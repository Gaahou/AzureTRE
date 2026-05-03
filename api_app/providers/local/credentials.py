"""
Keycloak OIDC implementation of CredentialProvider.

This module provides Keycloak-based authentication for offline mode,
validating JWT tokens against Keycloak's OIDC discovery endpoint and
mapping realm roles to TRE application roles.
"""

import os
from contextlib import asynccontextmanager
from typing import Optional
import httpx
import jwt
from jwt import PyJWKClient
from azure.core.credentials import TokenCredential, AccessToken
from providers.interfaces import CredentialProvider
from services.logging import logger


# Keycloak configuration from environment
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://keycloak:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "AzureTRE")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "tre-api-client")
KEYCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET", "tre-api-client-secret")

# OIDC endpoints
OIDC_DISCOVERY_URL = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/.well-known/openid-configuration"
TOKEN_ENDPOINT = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token"
JWKS_URI = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs"


class KeycloakTokenCredential(TokenCredential):
    """
    Token credential that validates Keycloak JWT tokens.

    This credential wrapper allows Keycloak tokens to be used with
    Azure SDK-compatible interfaces.
    """

    def __init__(self, token: str):
        """
        Initialize with a Keycloak JWT token.

        Args:
            token: Keycloak JWT access token
        """
        self._token = token
        # Decode to get expiry (without verification for now)
        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
            self._expires_on = decoded.get("exp", 0)
        except Exception:
            self._expires_on = 0

    def get_token(self, *scopes, **kwargs) -> AccessToken:
        """
        Get the access token.

        Args:
            scopes: OAuth2 scopes (ignored for Keycloak tokens)

        Returns:
            AccessToken with token and expiry
        """
        return AccessToken(self._token, self._expires_on)

    async def close(self):
        """Close any resources (no-op for JWT tokens)."""
        pass


class LocalCredentialProvider(CredentialProvider):
    """
    Keycloak OIDC credential provider for offline mode.

    Validates JWT tokens against Keycloak OIDC discovery endpoint and
    provides client credential flow for service-to-service authentication.
    """

    def __init__(self):
        """Initialize the Keycloak credential provider."""
        self._jwks_client: Optional[PyJWKClient] = None
        self._oidc_config: Optional[dict] = None
        logger.info(f"Initialized LocalCredentialProvider for Keycloak realm: {KEYCLOAK_REALM}")

    def _get_jwks_client(self) -> PyJWKClient:
        """
        Get or create JWKS client for token verification.

        Returns:
            PyJWKClient: Client for fetching signing keys
        """
        if self._jwks_client is None:
            self._jwks_client = PyJWKClient(JWKS_URI)
        return self._jwks_client

    async def _get_oidc_config(self) -> dict:
        """
        Fetch OIDC discovery configuration from Keycloak.

        Returns:
            dict: OIDC discovery configuration

        Raises:
            Exception: If discovery endpoint is unreachable
        """
        if self._oidc_config is None:
            async with httpx.AsyncClient() as client:
                response = await client.get(OIDC_DISCOVERY_URL)
                response.raise_for_status()
                self._oidc_config = response.json()
                logger.debug(f"Fetched OIDC config from {OIDC_DISCOVERY_URL}")
        return self._oidc_config

    def validate_token(self, token: str, require_audience: bool = False) -> dict:
        """
        Validate a JWT token against Keycloak's OIDC endpoint.

        Args:
            token: JWT bearer token to validate
            require_audience: Whether to require audience validation (service tokens don't have audience)

        Returns:
            dict: Decoded token claims including roles

        Raises:
            jwt.InvalidTokenError: If token is invalid or expired
        """
        try:
            # Get signing key from JWKS
            jwks_client = self._get_jwks_client()
            signing_key = jwks_client.get_signing_key_from_jwt(token)

            # Verify and decode token
            # Service account tokens (client credentials) don't have audience claim
            decoded = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_aud": require_audience,
                }
            )

            # Log token subject (user or service account)
            subject_type = decoded.get('preferred_username') or decoded.get('azp') or decoded.get('client_id', 'unknown')
            logger.debug(f"Token validated for: {subject_type}")
            return decoded

        except jwt.ExpiredSignatureError:
            logger.error("Token has expired")
            raise
        except jwt.InvalidAudienceError:
            logger.error(f"Token audience mismatch. Expected: {KEYCLOAK_CLIENT_ID}")
            raise
        except jwt.InvalidTokenError as e:
            logger.error(f"Token validation failed: {str(e)}")
            raise

    def extract_roles(self, token_claims: dict) -> list[str]:
        """
        Extract TRE application roles from Keycloak token claims.

        Keycloak stores roles in realm_access.roles. We map these to TRE roles:
        - WorkspaceOwner
        - WorkspaceResearcher
        - AirlockManager

        Args:
            token_claims: Decoded JWT token claims

        Returns:
            list[str]: List of TRE application role names
        """
        realm_roles = token_claims.get("realm_access", {}).get("roles", [])

        # Filter to only TRE-specific roles
        tre_roles = [
            role for role in realm_roles
            if role in ["WorkspaceOwner", "WorkspaceResearcher", "AirlockManager"]
        ]

        logger.debug(f"Extracted TRE roles: {tre_roles}")
        return tre_roles

    async def get_service_token(self) -> str:
        """
        Get a service-to-service token using client credentials flow.

        This is used for backend service authentication (e.g., Resource Processor).

        Returns:
            str: Access token for service account

        Raises:
            Exception: If token acquisition fails
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    TOKEN_ENDPOINT,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": KEYCLOAK_CLIENT_ID,
                        "client_secret": KEYCLOAK_CLIENT_SECRET,
                    }
                )
                response.raise_for_status()
                token_data = response.json()

                logger.debug("Service token acquired via client credentials flow")
                return token_data["access_token"]

        except httpx.HTTPError as e:
            logger.error(f"Failed to acquire service token: {str(e)}")
            raise Exception(f"Token acquisition failed: {str(e)}")

    def get_credential(self) -> TokenCredential:
        """
        Get a credential object for synchronous operations.

        Note: In offline mode with Keycloak, this returns a credential that
        uses client credentials flow for service-to-service auth.

        Returns:
            TokenCredential: Keycloak credential for sync operations
        """
        # For sync operations, we need to get a token synchronously
        # This is primarily used for service-to-service calls
        import asyncio
        import nest_asyncio

        try:
            # Allow nested event loops (for sync calls from async context)
            nest_asyncio.apply()
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Get service token
        token = loop.run_until_complete(self.get_service_token())
        return KeycloakTokenCredential(token)

    async def get_credential_async(self) -> TokenCredential:
        """
        Get a credential object for asynchronous operations.

        Returns:
            TokenCredential: Keycloak credential for async operations
        """
        token = await self.get_service_token()
        return KeycloakTokenCredential(token)

    @asynccontextmanager
    async def get_credential_async_context(self) -> TokenCredential:
        """
        Get a credential object as an async context manager.

        Yields:
            TokenCredential: Keycloak credential that is properly cleaned up
        """
        credential = await self.get_credential_async()
        try:
            yield credential
        finally:
            await credential.close()

    async def get_token(self, scopes: list[str]) -> str:
        """
        Get an access token for the specified scopes.

        Note: Keycloak doesn't use Azure-style scopes in the same way.
        This method returns a service account token.

        Args:
            scopes: List of OAuth2 scopes (informational only)

        Returns:
            str: Access token

        Raises:
            Exception: If token acquisition fails
        """
        logger.debug(f"Requesting token for scopes: {scopes}")
        return await self.get_service_token()