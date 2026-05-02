"""
Azure AD / Managed Identity implementation of CredentialProvider.

This module provides Azure-specific authentication using Azure AD and
Managed Identity credentials.
"""

from contextlib import asynccontextmanager
from urllib.parse import urlparse
from azure.core.credentials import TokenCredential
from azure.identity import (
    DefaultAzureCredential,
    ManagedIdentityCredential,
    ChainedTokenCredential,
)
from azure.identity.aio import (
    DefaultAzureCredential as DefaultAzureCredentialAsync,
    ManagedIdentityCredential as ManagedIdentityCredentialAsync,
    ChainedTokenCredential as ChainedTokenCredentialAsync,
)
from core.config import MANAGED_IDENTITY_CLIENT_ID, AAD_AUTHORITY_URL
from providers.interfaces import CredentialProvider


class AzureCredentialProvider(CredentialProvider):
    """
    Azure AD / Managed Identity credential provider.

    Uses Azure Managed Identity when available, falls back to DefaultAzureCredential
    for local development (Azure CLI, VS Code, etc.).
    """

    def get_credential(self) -> TokenCredential:
        """
        Get a credential object for synchronous operations.

        Returns:
            TokenCredential: Azure credential for sync operations
        """
        if MANAGED_IDENTITY_CLIENT_ID:
            return ChainedTokenCredential(
                ManagedIdentityCredential(client_id=MANAGED_IDENTITY_CLIENT_ID)
            )
        else:
            return DefaultAzureCredential(
                authority=urlparse(AAD_AUTHORITY_URL).netloc,
                exclude_shared_token_cache_credential=True,
                exclude_workload_identity_credential=True,
                exclude_developer_cli_credential=True,
                exclude_managed_identity_credential=True,
                exclude_powershell_credential=True
            )

    async def get_credential_async(self) -> TokenCredential:
        """
        Get a credential object for asynchronous operations.

        Returns:
            TokenCredential: Azure credential for async operations
        """
        if MANAGED_IDENTITY_CLIENT_ID:
            return ChainedTokenCredentialAsync(
                ManagedIdentityCredentialAsync(client_id=MANAGED_IDENTITY_CLIENT_ID)
            )
        else:
            return DefaultAzureCredentialAsync(
                authority=urlparse(AAD_AUTHORITY_URL).netloc,
                exclude_shared_token_cache_credential=True,
                exclude_workload_identity_credential=True,
                exclude_developer_cli_credential=True,
                exclude_managed_identity_credential=True,
                exclude_powershell_credential=True
            )

    @asynccontextmanager
    async def get_credential_async_context(self) -> TokenCredential:
        """
        Get a credential object as an async context manager.

        Yields:
            TokenCredential: Azure credential that is properly cleaned up
        """
        credential = await self.get_credential_async()
        try:
            yield credential
        finally:
            await credential.close()

    async def get_token(self, scopes: list[str]) -> str:
        """
        Get an access token for the specified scopes.

        Args:
            scopes: List of OAuth2 scopes to request

        Returns:
            str: Access token

        Raises:
            Exception: If token acquisition fails
        """
        credential = await self.get_credential_async()
        try:
            token = await credential.get_token(*scopes)
            return token.token
        finally:
            await credential.close()