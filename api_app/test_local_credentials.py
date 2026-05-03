#!/usr/bin/env python3
"""
Test script for LocalCredentialProvider.

Tests Keycloak token validation and service token acquisition.
"""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from providers.local.credentials import LocalCredentialProvider


async def test_service_token():
    """Test service-to-service token acquisition."""
    print("🧪 Testing service token acquisition...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    try:
        provider = LocalCredentialProvider()

        # Get service token
        print("\n📝 Acquiring service token via client credentials flow...")
        token = await provider.get_service_token()

        print(f"✅ Service token acquired (length: {len(token)})")
        print(f"   Token preview: {token[:50]}...")

        # Validate the token we just got
        print("\n🔍 Validating service token...")
        claims = provider.validate_token(token)

        print(f"✅ Token validated successfully")
        print(f"   Subject: {claims.get('sub')}")
        print(f"   Client ID: {claims.get('azp', claims.get('client_id'))}")
        print(f"   Issued at: {claims.get('iat')}")
        print(f"   Expires at: {claims.get('exp')}")
        print(f"   Token type: {claims.get('typ')}")

        # Extract roles
        print("\n🎭 Extracting roles...")
        roles = provider.extract_roles(claims)
        if roles:
            print(f"   Roles: {', '.join(roles)}")
        else:
            print("   No TRE roles found (service account)")

        print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("✅ All tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_credential_objects():
    """Test credential object creation."""
    print("\n🧪 Testing credential object creation...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    try:
        provider = LocalCredentialProvider()

        # Test async credential
        print("\n📝 Getting async credential...")
        cred_async = await provider.get_credential_async()
        print(f"✅ Async credential created: {type(cred_async).__name__}")

        # Test async context manager
        print("\n📝 Testing async context manager...")
        async with provider.get_credential_async_context() as cred:
            token = cred.get_token("https://management.azure.com/.default")
            print(f"✅ Context credential working, token length: {len(token.token)}")

        # Test sync credential (uses event loop)
        print("\n📝 Getting sync credential...")
        cred_sync = provider.get_credential()
        print(f"✅ Sync credential created: {type(cred_sync).__name__}")

        print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("✅ Credential object tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("╔══════════════════════════════════════════════════╗")
    print("║   LocalCredentialProvider Test Suite            ║")
    print("╚══════════════════════════════════════════════════╝")
    print()

    # Check environment
    print("📋 Environment:")
    print(f"   KEYCLOAK_URL: {os.getenv('KEYCLOAK_URL', 'http://keycloak:8080')}")
    print(f"   KEYCLOAK_REALM: {os.getenv('KEYCLOAK_REALM', 'AzureTRE')}")
    print(f"   KEYCLOAK_CLIENT_ID: {os.getenv('KEYCLOAK_CLIENT_ID', 'tre-api-client')}")
    print()

    # Run tests
    test1 = await test_service_token()
    test2 = await test_credential_objects()

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