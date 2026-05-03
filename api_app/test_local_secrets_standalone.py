"""
Standalone test suite for LocalSecretProvider (HashiCorp Vault).

This test suite verifies the Vault-based secrets management for offline mode,
testing CRUD operations on the HashiCorp Vault KV v2 secrets engine.

Requirements:
- Vault running at http://localhost:8200 (or VAULT_ADDR)
- Root token configured (or VAULT_TOKEN)
- KV v2 secrets engine enabled at 'secret/' mount point

Usage:
    python3 test_local_secrets_standalone.py
"""

import os
import asyncio
import httpx


# Configuration
VAULT_ADDR = os.getenv("VAULT_ADDR", "http://localhost:8200")
VAULT_TOKEN = os.getenv("VAULT_TOKEN", "root-token")
VAULT_MOUNT_POINT = os.getenv("VAULT_MOUNT_POINT", "secret")


class LocalSecretProvider:
    """Simplified LocalSecretProvider for standalone testing."""

    def __init__(self):
        self.vault_addr = VAULT_ADDR
        self.vault_token = VAULT_TOKEN
        self.mount_point = VAULT_MOUNT_POINT
        self.api_base = f"{self.vault_addr}/v1/{self.mount_point}"

    def _get_headers(self) -> dict:
        return {
            "X-Vault-Token": self.vault_token,
            "Content-Type": "application/json"
        }

    def _get_secret_path(self, secret_name: str) -> str:
        return f"{self.api_base}/data/{secret_name}"

    def _get_metadata_path(self, secret_name: str) -> str:
        return f"{self.api_base}/metadata/{secret_name}"

    async def get_secret(self, secret_name: str) -> str:
        try:
            secret_path = self._get_secret_path(secret_name)
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    secret_path,
                    headers=self._get_headers(),
                    timeout=10.0
                )

                if response.status_code == 404:
                    raise Exception(f"Secret '{secret_name}' not found in Vault")

                response.raise_for_status()
                data = response.json()
                secret_value = data.get("data", {}).get("data", {}).get("value")

                if secret_value is None:
                    raise Exception(f"Secret '{secret_name}' has no value")

                return secret_value

        except httpx.HTTPError as e:
            raise Exception(f"Failed to retrieve secret '{secret_name}': {str(e)}")

    async def set_secret(self, secret_name: str, secret_value: str) -> None:
        try:
            secret_path = self._get_secret_path(secret_name)
            payload = {"data": {"value": secret_value}}

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    secret_path,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=10.0
                )
                response.raise_for_status()

        except httpx.HTTPError as e:
            raise Exception(f"Failed to set secret '{secret_name}': {str(e)}")

    async def delete_secret(self, secret_name: str) -> None:
        try:
            metadata_path = self._get_metadata_path(secret_name)
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    metadata_path,
                    headers=self._get_headers(),
                    timeout=10.0
                )

                if response.status_code == 404:
                    return

                response.raise_for_status()

        except httpx.HTTPError as e:
            raise Exception(f"Failed to delete secret '{secret_name}': {str(e)}")

    async def list_secrets(self) -> list[str]:
        try:
            list_path = f"{self.api_base}/metadata"
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    "LIST",
                    list_path,
                    headers=self._get_headers(),
                    params={"list": "true"},
                    timeout=10.0
                )

                if response.status_code == 404:
                    return []

                response.raise_for_status()
                data = response.json()
                keys = data.get("data", {}).get("keys", [])
                return keys

        except httpx.HTTPError as e:
            raise Exception(f"Failed to list secrets: {str(e)}")


async def run_tests():
    """Run all test cases."""
    provider = LocalSecretProvider()
    passed = 0
    failed = 0

    print("\n" + "="*60)
    print("HashiCorp Vault Secret Provider Test Suite")
    print("="*60)
    print(f"\nVault Address: {VAULT_ADDR}")
    print(f"Vault Token: {VAULT_TOKEN[:10]}...")
    print(f"Mount Point: {VAULT_MOUNT_POINT}\n")

    # Test 1: Set and get secret
    try:
        print("Test 1: Set and get secret...")
        await provider.set_secret("test-secret-1", "my-secret-value-123")
        value = await provider.get_secret("test-secret-1")
        assert value == "my-secret-value-123"
        print("  ✓ PASSED\n")
        passed += 1
    except Exception as e:
        print(f"  ✗ FAILED: {e}\n")
        failed += 1

    # Test 2: Get nonexistent secret
    try:
        print("Test 2: Get nonexistent secret...")
        try:
            await provider.get_secret("nonexistent-secret-xyz")
            print("  ✗ FAILED: Should have raised exception\n")
            failed += 1
        except Exception as e:
            if "not found" in str(e).lower():
                print("  ✓ PASSED\n")
                passed += 1
            else:
                print(f"  ✗ FAILED: Wrong exception: {e}\n")
                failed += 1
    except Exception as e:
        print(f"  ✗ FAILED: {e}\n")
        failed += 1

    # Test 3: Update secret
    try:
        print("Test 3: Update secret...")
        await provider.set_secret("test-secret-2", "original-value")
        value1 = await provider.get_secret("test-secret-2")
        assert value1 == "original-value"
        await provider.set_secret("test-secret-2", "updated-value")
        value2 = await provider.get_secret("test-secret-2")
        assert value2 == "updated-value"
        print("  ✓ PASSED\n")
        passed += 1
    except Exception as e:
        print(f"  ✗ FAILED: {e}\n")
        failed += 1

    # Test 4: List secrets
    try:
        print("Test 4: List secrets...")
        await provider.set_secret("test-list-1", "value1")
        await provider.set_secret("test-list-2", "value2")
        await provider.set_secret("test-list-3", "value3")
        secret_names = await provider.list_secrets()
        assert "test-list-1" in secret_names
        assert "test-list-2" in secret_names
        assert "test-list-3" in secret_names
        print(f"  ✓ PASSED (found {len(secret_names)} secrets)\n")
        passed += 1
    except Exception as e:
        print(f"  ✗ FAILED: {e}\n")
        failed += 1

    # Test 5: Delete secret
    try:
        print("Test 5: Delete secret...")
        await provider.set_secret("test-secret-delete", "to-be-deleted")
        value = await provider.get_secret("test-secret-delete")
        assert value == "to-be-deleted"
        await provider.delete_secret("test-secret-delete")
        try:
            await provider.get_secret("test-secret-delete")
            print("  ✗ FAILED: Secret still exists after deletion\n")
            failed += 1
        except Exception as e:
            if "not found" in str(e).lower():
                print("  ✓ PASSED\n")
                passed += 1
            else:
                print(f"  ✗ FAILED: Wrong exception: {e}\n")
                failed += 1
    except Exception as e:
        print(f"  ✗ FAILED: {e}\n")
        failed += 1

    # Test 6: Delete nonexistent secret
    try:
        print("Test 6: Delete nonexistent secret...")
        await provider.delete_secret("nonexistent-delete-xyz")
        print("  ✓ PASSED\n")
        passed += 1
    except Exception as e:
        print(f"  ✗ FAILED: {e}\n")
        failed += 1

    # Test 7: Verify seeded secrets
    try:
        print("Test 7: Verify seeded secrets exist...")
        expected_secrets = [
            "cosmosdb-connection-string",
            "storage-account-key",
            "api-client-secret",
            "servicebus-connection-string",
            "workspace-secret",
        ]
        for secret_name in expected_secrets:
            value = await provider.get_secret(secret_name)
            assert value is not None
            assert len(value) > 0
        print(f"  ✓ PASSED (all {len(expected_secrets)} seeded secrets exist)\n")
        passed += 1
    except Exception as e:
        print(f"  ✗ FAILED: {e}\n")
        failed += 1

    # Test 8: Special characters in secret value
    try:
        print("Test 8: Secret with special characters...")
        special_value = 'P@ssw0rd!#$%^&*()_+-={}[]|:";\'<>?,./~`'
        await provider.set_secret("test-special-chars", special_value)
        value = await provider.get_secret("test-special-chars")
        assert value == special_value
        print("  ✓ PASSED\n")
        passed += 1
    except Exception as e:
        print(f"  ✗ FAILED: {e}\n")
        failed += 1

    # Test 9: JSON value in secret
    try:
        print("Test 9: JSON value in secret...")
        json_value = '{"username": "admin", "password": "secret123", "roles": ["admin", "user"]}'
        await provider.set_secret("test-json-secret", json_value)
        value = await provider.get_secret("test-json-secret")
        assert value == json_value
        print("  ✓ PASSED\n")
        passed += 1
    except Exception as e:
        print(f"  ✗ FAILED: {e}\n")
        failed += 1

    # Test 10: Concurrent operations
    try:
        print("Test 10: Concurrent operations...")
        secret_names = [f"concurrent-secret-{i}" for i in range(5)]

        # Set multiple secrets concurrently
        set_tasks = [
            provider.set_secret(name, f"value-{i}")
            for i, name in enumerate(secret_names)
        ]
        await asyncio.gather(*set_tasks)

        # Get multiple secrets concurrently
        get_tasks = [provider.get_secret(name) for name in secret_names]
        values = await asyncio.gather(*get_tasks)

        # Verify all values
        for i, value in enumerate(values):
            assert value == f"value-{i}"

        print("  ✓ PASSED\n")
        passed += 1
    except Exception as e:
        print(f"  ✗ FAILED: {e}\n")
        failed += 1

    # Summary
    print("="*60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_tests())
    exit(0 if success else 1)