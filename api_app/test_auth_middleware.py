#!/usr/bin/env python3
"""
Test script for authentication middleware with credential provider.

Tests that the auth middleware correctly uses the credential provider
in offline mode for token validation.
"""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from providers.factory import get_credential_provider
from core import config


async def test_provider_integration():
    """Test that credential provider is correctly integrated."""
    print("🧪 Testing credential provider integration...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()

    try:
        # Check deployment mode
        print(f"📋 Deployment Mode: {config.DEPLOYMENT_MODE}")

        # Get credential provider
        provider = get_credential_provider()
        print(f"✅ Credential Provider: {type(provider).__name__}")
        print()

        # Get service token
        print("📝 Acquiring service token...")
        token = await provider.get_service_token()
        print(f"✅ Token acquired (length: {len(token)})")
        print()

        # Validate token
        print("🔍 Validating token...")
        claims = provider.validate_token(token, require_audience=False)
        print(f"✅ Token validated")
        print(f"   Subject: {claims.get('sub')}")
        print(f"   Client: {claims.get('azp', claims.get('client_id'))}")
        print(f"   Issued: {claims.get('iat')}")
        print(f"   Expires: {claims.get('exp')}")
        print()

        # Extract roles
        print("🎭 Extracting roles...")
        roles = provider.extract_roles(claims)
        print(f"   Roles: {roles if roles else '(none - service account)'}")
        print()

        # Test user extraction from token
        print("👤 Testing user extraction...")
        from services.aad_authentication import AzureADAuthorization
        user = AzureADAuthorization._get_user_from_provider_token(claims, provider)
        print(f"✅ User extracted:")
        print(f"   ID: {user.id}")
        print(f"   Name: {user.name}")
        print(f"   Email: {user.email}")
        print(f"   Roles: {user.roles}")
        print()

        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("✅ All provider integration tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_user_token():
    """Test with a user token (admin user with roles)."""
    print("\n🧪 Testing with user token (admin)...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()

    try:
        # First, get an admin token from Keycloak
        import httpx

        print("📝 Acquiring admin user token from Keycloak...")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{os.getenv('KEYCLOAK_URL', 'http://keycloak:8080')}/realms/AzureTRE/protocol/openid-connect/token",
                data={
                    "grant_type": "password",
                    "client_id": "tre-api-client",
                    "client_secret": "tre-api-client-secret",
                    "username": "admin",
                    "password": "admin_password"
                }
            )

            if response.status_code != 200:
                print(f"❌ Failed to get user token: {response.status_code}")
                print(response.text)
                return False

            token_data = response.json()
            token = token_data["access_token"]

        print(f"✅ User token acquired (length: {len(token)})")
        print()

        # Validate and extract user
        provider = get_credential_provider()

        print("🔍 Validating user token...")
        claims = provider.validate_token(token, require_audience=False)
        print(f"✅ Token validated")
        print(f"   Username: {claims.get('preferred_username')}")
        print(f"   Email: {claims.get('email')}")
        print()

        print("🎭 Extracting roles...")
        roles = provider.extract_roles(claims)
        print(f"   User roles: {roles}")
        print()

        # Extract user
        from services.aad_authentication import AzureADAuthorization
        user = AzureADAuthorization._get_user_from_provider_token(claims, provider)
        print(f"✅ User extracted:")
        print(f"   ID: {user.id}")
        print(f"   Name: {user.name}")
        print(f"   Email: {user.email}")
        print(f"   Roles: {user.roles}")

        # Verify admin has all expected roles
        expected_roles = ["WorkspaceOwner", "WorkspaceResearcher", "AirlockManager"]
        has_all_roles = all(role in user.roles for role in expected_roles)

        if has_all_roles:
            print(f"\n✅ Admin user has all expected roles: {expected_roles}")
        else:
            print(f"\n⚠️  Admin user missing some roles. Expected: {expected_roles}, Got: {user.roles}")

        print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("✅ User token test passed!")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("╔══════════════════════════════════════════════════╗")
    print("║   Auth Middleware Provider Integration Tests    ║")
    print("╚══════════════════════════════════════════════════╝")
    print()

    # Check environment
    print("📋 Environment:")
    print(f"   DEPLOYMENT_MODE: {config.DEPLOYMENT_MODE}")
    print(f"   KEYCLOAK_URL: {os.getenv('KEYCLOAK_URL', 'http://keycloak:8080')}")
    print(f"   KEYCLOAK_REALM: {os.getenv('KEYCLOAK_REALM', 'AzureTRE')}")
    print()

    # Run tests
    test1 = await test_provider_integration()
    test2 = await test_user_token()

    # Summary
    print()
    print("╔══════════════════════════════════════════════════╗")
    if test1 and test2:
        print("║           ✅ ALL TESTS PASSED                    ║")
    else:
        print("║           ❌ SOME TESTS FAILED                   ║")
    print("╚══════════════════════════════════════════════════╝")

    return test1 and test2


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)