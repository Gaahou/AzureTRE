"""
HashiCorp Vault implementation of SecretProvider.

This module provides HashiCorp Vault-based secrets management for offline mode,
storing and retrieving secrets from a local Vault instance.
"""

import os
import httpx
from providers.interfaces import SecretProvider
from services.logging import logger


# Vault configuration from environment
VAULT_ADDR = os.getenv("VAULT_ADDR", "http://vault:8200")
VAULT_TOKEN = os.getenv("VAULT_TOKEN", "root-token")
VAULT_MOUNT_POINT = os.getenv("VAULT_MOUNT_POINT", "secret")  # KV v2 mount point


class LocalSecretProvider(SecretProvider):
    """
    HashiCorp Vault secret provider for offline mode.

    Uses Vault's KV v2 secrets engine to store and retrieve secrets.
    In dev mode, Vault runs in-memory with a root token.
    """

    def __init__(self):
        """Initialize the Vault secret provider."""
        self.vault_addr = VAULT_ADDR
        self.vault_token = VAULT_TOKEN
        self.mount_point = VAULT_MOUNT_POINT
        self.api_base = f"{self.vault_addr}/v1/{self.mount_point}"
        logger.info(f"Initialized LocalSecretProvider for Vault at: {self.vault_addr}")

    def _get_headers(self) -> dict:
        """
        Get HTTP headers for Vault API requests.

        Returns:
            dict: Headers including Vault token
        """
        return {
            "X-Vault-Token": self.vault_token,
            "Content-Type": "application/json"
        }

    def _get_secret_path(self, secret_name: str) -> str:
        """
        Get the full KV v2 API path for a secret.

        KV v2 uses /data/ in the path for secret values.

        Args:
            secret_name: Name of the secret

        Returns:
            str: Full API path
        """
        return f"{self.api_base}/data/{secret_name}"

    def _get_metadata_path(self, secret_name: str) -> str:
        """
        Get the full KV v2 API path for secret metadata.

        Args:
            secret_name: Name of the secret

        Returns:
            str: Full metadata API path
        """
        return f"{self.api_base}/metadata/{secret_name}"

    async def get_secret(self, secret_name: str) -> str:
        """
        Get a secret value from Vault.

        Args:
            secret_name: Name of the secret to retrieve

        Returns:
            str: Secret value

        Raises:
            Exception: If secret retrieval fails or secret not found
        """
        try:
            secret_path = self._get_secret_path(secret_name)
            logger.debug(f"Retrieving secret: {secret_name} from {secret_path}")

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    secret_path,
                    headers=self._get_headers(),
                    timeout=10.0
                )

                if response.status_code == 404:
                    logger.error(f"Secret not found: {secret_name}")
                    raise Exception(f"Secret '{secret_name}' not found in Vault")

                response.raise_for_status()
                data = response.json()

                # KV v2 response format: {"data": {"data": {"value": "..."}}}
                secret_value = data.get("data", {}).get("data", {}).get("value")

                if secret_value is None:
                    logger.error(f"Secret value is null: {secret_name}")
                    raise Exception(f"Secret '{secret_name}' has no value")

                logger.debug(f"Successfully retrieved secret: {secret_name}")
                return secret_value

        except httpx.HTTPError as e:
            logger.error(f"HTTP error retrieving secret {secret_name}: {str(e)}")
            raise Exception(f"Failed to retrieve secret '{secret_name}': {str(e)}")
        except Exception as e:
            logger.error(f"Error retrieving secret {secret_name}: {str(e)}")
            raise

    async def set_secret(self, secret_name: str, secret_value: str) -> None:
        """
        Set a secret value in Vault.

        Args:
            secret_name: Name of the secret
            secret_value: Value to store

        Raises:
            Exception: If secret storage fails
        """
        try:
            secret_path = self._get_secret_path(secret_name)
            logger.debug(f"Setting secret: {secret_name} at {secret_path}")

            # KV v2 request format: {"data": {"value": "..."}}
            payload = {
                "data": {
                    "value": secret_value
                }
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    secret_path,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=10.0
                )

                response.raise_for_status()
                logger.info(f"Successfully set secret: {secret_name}")

        except httpx.HTTPError as e:
            logger.error(f"HTTP error setting secret {secret_name}: {str(e)}")
            raise Exception(f"Failed to set secret '{secret_name}': {str(e)}")
        except Exception as e:
            logger.error(f"Error setting secret {secret_name}: {str(e)}")
            raise

    async def delete_secret(self, secret_name: str) -> None:
        """
        Delete a secret from Vault.

        This performs a soft delete in KV v2 (versions are retained).

        Args:
            secret_name: Name of the secret to delete

        Raises:
            Exception: If secret deletion fails
        """
        try:
            metadata_path = self._get_metadata_path(secret_name)
            logger.debug(f"Deleting secret: {secret_name} at {metadata_path}")

            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    metadata_path,
                    headers=self._get_headers(),
                    timeout=10.0
                )

                if response.status_code == 404:
                    logger.warning(f"Secret not found (already deleted?): {secret_name}")
                    return

                response.raise_for_status()
                logger.info(f"Successfully deleted secret: {secret_name}")

        except httpx.HTTPError as e:
            logger.error(f"HTTP error deleting secret {secret_name}: {str(e)}")
            raise Exception(f"Failed to delete secret '{secret_name}': {str(e)}")
        except Exception as e:
            logger.error(f"Error deleting secret {secret_name}: {str(e)}")
            raise

    async def list_secrets(self) -> list[str]:
        """
        List all secret names in Vault.

        Returns:
            list[str]: List of secret names

        Raises:
            Exception: If listing fails
        """
        try:
            list_path = f"{self.api_base}/metadata"
            logger.debug(f"Listing secrets at: {list_path}")

            async with httpx.AsyncClient() as client:
                response = await client.request(
                    "LIST",
                    list_path,
                    headers=self._get_headers(),
                    params={"list": "true"},
                    timeout=10.0
                )

                if response.status_code == 404:
                    # No secrets yet
                    logger.debug("No secrets found in Vault (404)")
                    return []

                response.raise_for_status()
                data = response.json()

                # Response format: {"data": {"keys": ["secret1", "secret2"]}}
                keys = data.get("data", {}).get("keys", [])
                logger.debug(f"Found {len(keys)} secrets in Vault")
                return keys

        except httpx.HTTPError as e:
            logger.error(f"HTTP error listing secrets: {str(e)}")
            raise Exception(f"Failed to list secrets: {str(e)}")
        except Exception as e:
            logger.error(f"Error listing secrets: {str(e)}")
            raise