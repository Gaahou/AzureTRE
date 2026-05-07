"""
Azure AD B2C implementation of CredentialProvider.

This module provides Azure AD B2C authentication for consumer identity scenarios,
validating JWT tokens against B2C OIDC discovery endpoints and mapping
B2C custom attributes to TRE application roles.
"""

import os
from contextlib import asynccontextmanager
from typing import Optional
import httpx
import jwt
from jwt import PyJWKClient
from azure.core.credentials import TokenCredential, AccessToken
from providers.interfaces import CredentialProvider
from core import config
from services.logging import logger


class B2CTokenCredential(TokenCredential):
    """
    Token credential that validates Azure AD B2C JWT tokens.

    This credential wrapper allows B2C tokens to be used with
    Azure SDK-compatible interfaces.
    """

    def __init__(self, token: str):
        """
        Initialize with an Azure AD B2C JWT token.

        Args:
            token: Azure AD B2C JWT access token
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
            scopes: OAuth2 scopes (informational for B2C tokens)

        Returns:
            AccessToken with token and expiry
        """
        return AccessToken(self._token, self._expires_on)

    async def close(self):
        """Close any resources (no-op for JWT tokens)."""
        pass


class AzureADB2CCredentialProvider(CredentialProvider):
    """
    Azure AD B2C credential provider for consumer identity scenarios.

    Validates JWT tokens against B2C OIDC discovery endpoint and provides
    B2C-specific token claim parsing for custom attributes and user flows.
    """

    def __init__(self):
        """Initialize the Azure AD B2C credential provider."""
        self.tenant_name = config.B2C_TENANT_NAME
        self.policy_susi = config.B2C_POLICY_SUSI
        self.client_id = config.B2C_CLIENT_ID
        self._jwks_client: Optional[PyJWKClient] = None
        self._oidc_config: Optional[dict] = None

        if not self.tenant_name:
            raise ValueError("B2C_TENANT_NAME must be configured when AUTH_TYPE=b2c")
        if not self.client_id:
            raise ValueError("B2C_CLIENT_ID must be configured when AUTH_TYPE=b2c")

        logger.info(f"Initialized AzureADB2CCredentialProvider for tenant: {self.tenant_name}")

    def _get_discovery_url(self) -> str:
        """
        Get B2C OIDC discovery URL.

        Returns:
            str: OIDC discovery endpoint URL for B2C user flow
        """
        return (
            f"https://{self.tenant_name}.b2clogin.com/"
            f"{self.tenant_name}.onmicrosoft.com/"
            f"{self.policy_susi}/v2.0/.well-known/openid-configuration"
        )

    def _get_jwks_uri(self) -> str:
        """
        Get B2C JWKS URI for token signature verification.

        Returns:
            str: JWKS endpoint URL for B2C user flow
        """
        return (
            f"https://{self.tenant_name}.b2clogin.com/"
            f"{self.tenant_name}.onmicrosoft.com/"
            f"discovery/v2.0/keys?p={self.policy_susi}"
        )

    def _get_jwks_client(self) -> PyJWKClient:
        """
        Get or create JWKS client for token verification.

        Returns:
            PyJWKClient: Client for fetching signing keys
        """
        if self._jwks_client is None:
            self._jwks_client = PyJWKClient(self._get_jwks_uri())
        return self._jwks_client

    async def _get_oidc_config(self) -> dict:
        """
        Fetch OIDC discovery configuration from B2C.

        Returns:
            dict: OIDC discovery configuration

        Raises:
            Exception: If discovery endpoint is unreachable
        """
        if self._oidc_config is None:
            discovery_url = self._get_discovery_url()
            async with httpx.AsyncClient() as client:
                response = await client.get(discovery_url)
                response.raise_for_status()
                self._oidc_config = response.json()
                logger.debug(f"Fetched B2C OIDC config from {discovery_url}")
        return self._oidc_config

    def validate_token(self, token: str, require_audience: bool = True) -> dict:
        """
        Validate a JWT token against B2C's OIDC endpoint.

        B2C tokens include:
        - tfp: User flow policy (e.g., B2C_1_susi)
        - idp: Identity provider used (google.com, microsoft.com, local)
        - emails: Array of email addresses (not singular 'email')
        - extension_*: Custom attributes for roles

        Args:
            token: JWT bearer token to validate
            require_audience: Whether to require audience validation

        Returns:
            dict: Decoded token claims including custom attributes

        Raises:
            jwt.InvalidTokenError: If token is invalid or expired
        """
        try:
            # Get signing key from JWKS
            jwks_client = self._get_jwks_client()
            signing_key = jwks_client.get_signing_key_from_jwt(token)

            # Verify and decode token
            decoded = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.client_id if require_audience else None,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_aud": require_audience,
                }
            )

            # Log token subject and user flow
            user_email = decoded.get('emails', ['unknown'])[0] if decoded.get('emails') else 'unknown'
            user_flow = decoded.get('tfp', 'unknown')
            idp = decoded.get('idp', 'local')
            logger.debug(f"B2C token validated for: {user_email} (flow: {user_flow}, idp: {idp})")

            return decoded

        except jwt.ExpiredSignatureError:
            logger.error("B2C token has expired")
            raise
        except jwt.InvalidAudienceError:
            logger.error(f"B2C token audience mismatch. Expected: {self.client_id}")
            raise
        except jwt.InvalidTokenError as e:
            logger.error(f"B2C token validation failed: {str(e)}")
            raise

    def extract_roles(self, token_claims: dict) -> list[str]:
        """
        Extract TRE application roles from B2C custom attributes.

        B2C custom attributes use extension_ prefix:
        - extension_WorkspaceRole -> WorkspaceOwner, WorkspaceResearcher
        - extension_AirlockRole -> AirlockManager
        - extension_TRERole -> TREAdmin, TREUser

        Args:
            token_claims: Decoded JWT token claims

        Returns:
            list[str]: List of TRE application role names
        """
        roles = []

        # Map B2C extension claims to TRE roles
        # WorkspaceRole can be a single role or comma-separated list
        workspace_role = token_claims.get("extension_WorkspaceRole")
        if workspace_role:
            # Handle both single role and comma-separated roles
            if isinstance(workspace_role, str):
                roles.extend([r.strip() for r in workspace_role.split(',')])
            else:
                roles.append(workspace_role)

        # AirlockManager role
        airlock_role = token_claims.get("extension_AirlockRole")
        if airlock_role:
            if isinstance(airlock_role, str):
                roles.extend([r.strip() for r in airlock_role.split(',')])
            else:
                roles.append(airlock_role)

        # TRE roles (TREAdmin, TREUser)
        tre_role = token_claims.get("extension_TRERole")
        if tre_role:
            if isinstance(tre_role, str):
                roles.extend([r.strip() for r in tre_role.split(',')])
            else:
                roles.append(tre_role)

        # Also support the configurable role claim name
        custom_role_claim = token_claims.get(config.B2C_ROLE_CLAIM_NAME)
        if custom_role_claim and config.B2C_ROLE_CLAIM_NAME not in ["extension_WorkspaceRole", "extension_AirlockRole", "extension_TRERole"]:
            if isinstance(custom_role_claim, str):
                roles.extend([r.strip() for r in custom_role_claim.split(',')])
            else:
                roles.append(custom_role_claim)

        # Remove duplicates while preserving order
        unique_roles = []
        for role in roles:
            if role and role not in unique_roles:
                unique_roles.append(role)

        logger.debug(f"Extracted TRE roles from B2C token: {unique_roles}")
        return unique_roles

    async def get_service_token(self) -> str:
        """
        Get a service-to-service token.

        Note: B2C is primarily for user authentication. Service-to-service
        authentication should use Azure AD Managed Identity instead.

        Raises:
            NotImplementedError: B2C doesn't support service-to-service auth
        """
        raise NotImplementedError(
            "Azure AD B2C is for user authentication only. "
            "For service-to-service authentication, use Azure AD Managed Identity "
            "by setting AUTH_TYPE=aad."
        )

    def get_credential(self) -> TokenCredential:
        """
        Get a credential object for synchronous operations.

        Note: B2C is for user authentication. For service accounts,
        use Azure AD Managed Identity (AUTH_TYPE=aad).

        Returns:
            TokenCredential: B2C credential for sync operations
        """
        raise NotImplementedError(
            "Azure AD B2C credentials are obtained from user tokens, not service principals. "
            "Use AUTH_TYPE=aad for service-to-service authentication."
        )

    async def get_credential_async(self) -> TokenCredential:
        """
        Get a credential object for asynchronous operations.

        Note: B2C is for user authentication. For service accounts,
        use Azure AD Managed Identity (AUTH_TYPE=aad).

        Returns:
            TokenCredential: B2C credential for async operations
        """
        raise NotImplementedError(
            "Azure AD B2C credentials are obtained from user tokens, not service principals. "
            "Use AUTH_TYPE=aad for service-to-service authentication."
        )

    @asynccontextmanager
    async def get_credential_async_context(self) -> TokenCredential:
        """
        Get a credential object as an async context manager.

        Note: B2C is for user authentication. For service accounts,
        use Azure AD Managed Identity (AUTH_TYPE=aad).

        Yields:
            TokenCredential: B2C credential
        """
        raise NotImplementedError(
            "Azure AD B2C credentials are obtained from user tokens, not service principals. "
            "Use AUTH_TYPE=aad for service-to-service authentication."
        )

    async def get_token(self, scopes: list[str]) -> str:
        """
        Get an access token for the specified scopes.

        Note: B2C is for user authentication. For service accounts,
        use Azure AD Managed Identity (AUTH_TYPE=aad).

        Args:
            scopes: List of OAuth2 scopes

        Returns:
            str: Access token
        """
        raise NotImplementedError(
            "Azure AD B2C credentials are obtained from user tokens, not service principals. "
            "Use AUTH_TYPE=aad for service-to-service authentication."
        )
