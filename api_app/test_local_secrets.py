"""
Test suite for LocalSecretProvider (HashiCorp Vault).

This test suite verifies the Vault-based secrets management for offline mode,
testing CRUD operations on the HashiCorp Vault KV v2 secrets engine.

Requirements:
- Vault running at http://localhost:8200 (or VAULT_ADDR)
- Root token configured (or VAULT_TOKEN)
- KV v2 secrets engine enabled at 'secret/' mount point

Usage:
    pytest test_local_secrets.py -v
"""

import pytest
import os
import asyncio
from providers.local.secrets import LocalSecretProvider


@pytest.fixture
def secret_provider():
    """Create a LocalSecretProvider instance for testing."""
    return LocalSecretProvider()


@pytest.mark.asyncio
async def test_set_and_get_secret(secret_provider):
    """Test setting and retrieving a secret."""
    secret_name = "test-secret-1"
    secret_value = "my-secret-value-123"

    # Set the secret
    await secret_provider.set_secret(secret_name, secret_value)

    # Get the secret
    retrieved_value = await secret_provider.get_secret(secret_name)

    assert retrieved_value == secret_value
    print(f"✓ Set and retrieved secret: {secret_name}")


@pytest.mark.asyncio
async def test_get_nonexistent_secret(secret_provider):
    """Test retrieving a secret that doesn't exist."""
    secret_name = "nonexistent-secret"

    with pytest.raises(Exception) as exc_info:
        await secret_provider.get_secret(secret_name)

    assert "not found" in str(exc_info.value).lower()
    print(f"✓ Correctly raised exception for nonexistent secret")


@pytest.mark.asyncio
async def test_update_secret(secret_provider):
    """Test updating an existing secret."""
    secret_name = "test-secret-2"
    original_value = "original-value"
    updated_value = "updated-value"

    # Set original
    await secret_provider.set_secret(secret_name, original_value)
    retrieved = await secret_provider.get_secret(secret_name)
    assert retrieved == original_value

    # Update
    await secret_provider.set_secret(secret_name, updated_value)
    retrieved = await secret_provider.get_secret(secret_name)
    assert retrieved == updated_value

    print(f"✓ Updated secret: {secret_name}")


@pytest.mark.asyncio
async def test_list_secrets(secret_provider):
    """Test listing all secrets."""
    # Set a few test secrets
    test_secrets = {
        "test-list-1": "value1",
        "test-list-2": "value2",
        "test-list-3": "value3",
    }

    for name, value in test_secrets.items():
        await secret_provider.set_secret(name, value)

    # List all secrets
    secret_names = await secret_provider.list_secrets()

    # Verify our test secrets are in the list
    for name in test_secrets.keys():
        assert name in secret_names, f"Secret {name} not found in list"

    print(f"✓ Listed {len(secret_names)} secrets in Vault")


@pytest.mark.asyncio
async def test_delete_secret(secret_provider):
    """Test deleting a secret."""
    secret_name = "test-secret-delete"
    secret_value = "to-be-deleted"

    # Set the secret
    await secret_provider.set_secret(secret_name, secret_value)

    # Verify it exists
    retrieved = await secret_provider.get_secret(secret_name)
    assert retrieved == secret_value

    # Delete it
    await secret_provider.delete_secret(secret_name)

    # Verify it's gone
    with pytest.raises(Exception) as exc_info:
        await secret_provider.get_secret(secret_name)

    assert "not found" in str(exc_info.value).lower()
    print(f"✓ Deleted secret: {secret_name}")


@pytest.mark.asyncio
async def test_delete_nonexistent_secret(secret_provider):
    """Test deleting a secret that doesn't exist (should not raise error)."""
    secret_name = "nonexistent-delete"

    # Should not raise an error
    await secret_provider.delete_secret(secret_name)

    print(f"✓ Gracefully handled deletion of nonexistent secret")


@pytest.mark.asyncio
async def test_seeded_secrets_exist(secret_provider):
    """Test that vault-init.sh seeded secrets are accessible."""
    expected_secrets = [
        "cosmosdb-connection-string",
        "storage-account-key",
        "api-client-secret",
        "servicebus-connection-string",
        "workspace-secret",
    ]

    for secret_name in expected_secrets:
        value = await secret_provider.get_secret(secret_name)
        assert value is not None
        assert len(value) > 0
        print(f"✓ Seeded secret exists: {secret_name}")


@pytest.mark.asyncio
async def test_secret_with_special_characters(secret_provider):
    """Test storing secrets with special characters."""
    secret_name = "test-special-chars"
    secret_value = 'P@ssw0rd!#$%^&*()_+-={}[]|:";\'<>?,./~`'

    await secret_provider.set_secret(secret_name, secret_value)
    retrieved = await secret_provider.get_secret(secret_name)

    assert retrieved == secret_value
    print(f"✓ Stored and retrieved secret with special characters")


@pytest.mark.asyncio
async def test_secret_with_json_value(secret_provider):
    """Test storing a JSON string as a secret."""
    secret_name = "test-json-secret"
    secret_value = '{"username": "admin", "password": "secret123", "roles": ["admin", "user"]}'

    await secret_provider.set_secret(secret_name, secret_value)
    retrieved = await secret_provider.get_secret(secret_name)

    assert retrieved == secret_value
    print(f"✓ Stored and retrieved JSON secret")


@pytest.mark.asyncio
async def test_concurrent_operations(secret_provider):
    """Test concurrent secret operations."""
    secret_names = [f"concurrent-secret-{i}" for i in range(5)]

    # Set multiple secrets concurrently
    set_tasks = [
        secret_provider.set_secret(name, f"value-{i}")
        for i, name in enumerate(secret_names)
    ]
    await asyncio.gather(*set_tasks)

    # Get multiple secrets concurrently
    get_tasks = [secret_provider.get_secret(name) for name in secret_names]
    values = await asyncio.gather(*get_tasks)

    # Verify all values
    for i, value in enumerate(values):
        assert value == f"value-{i}"

    print(f"✓ Concurrent operations completed successfully")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("HashiCorp Vault Secret Provider Test Suite")
    print("="*60 + "\n")

    print(f"Vault Address: {os.getenv('VAULT_ADDR', 'http://vault:8200')}")
    print(f"Vault Token: {os.getenv('VAULT_TOKEN', 'root-token')[:10]}...")
    print(f"Mount Point: {os.getenv('VAULT_MOUNT_POINT', 'secret')}\n")

    pytest.main([__file__, "-v", "--tb=short"])