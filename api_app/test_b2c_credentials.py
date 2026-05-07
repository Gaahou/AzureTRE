#!/usr/bin/env python3
"""
Test script for Azure AD B2C Credential Provider.

Tests B2C token validation and role extraction against a real B2C tenant.
"""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from providers.azure.b2c_credentials import AzureADB2CCredentialProvider
from core import config


async def test_b2c_provider_initialization():
    """Test that B2C credential provider initializes correctly."""
    print("🧪 Testing B2C provider initialization...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()

    try:
        provider = AzureADB2CCredentialProvider()

        print(f"✅ B2C Provider initialized")
        print(f"   Tenant: {provider.tenant_name}")
        print(f"   Policy: {provider.policy_susi}")
        print(f"   Client ID: {provider.client_id[:8]}...{provider.client_id[-4:]}")
        print()

        # Display OIDC endpoints
        print(f"📍 B2C OIDC Endpoints:")
        print(f"   Discovery: {provider._get_discovery_url()}")
        print(f"   JWKS: {provider._get_jwks_uri()}")
        print()

        return True

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_oidc_discovery():
    """Test fetching OIDC discovery configuration."""
    print("🧪 Testing OIDC discovery endpoint...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()

    try:
        provider = AzureADB2CCredentialProvider()

        print("📝 Fetching OIDC configuration...")
        oidc_config = await provider._get_oidc_config()

        print(f"✅ OIDC configuration retrieved")
        print(f"   Issuer: {oidc_config.get('issuer')}")
        print(f"   Authorization endpoint: {oidc_config.get('authorization_endpoint')}")
        print(f"   Token endpoint: {oidc_config.get('token_endpoint')}")
        print(f"   JWKS URI: {oidc_config.get('jwks_uri')}")
        print()

        return True

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_token_validation():
    """
    Test token validation with a B2C token.

    Note: This requires a valid B2C token. You can obtain one via:
    1. Password flow (ROPC - if enabled in B2C)
    2. Device code flow
    3. Manual login via browser and copy token
    """
    print("🧪 Testing B2C token validation...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()

    # Check if test token is provided via environment
    test_token = os.getenv("B2C_TEST_TOKEN")

    if not test_token:
        print("⚠️  Skipping token validation test")
        print("   To test with a real token, set B2C_TEST_TOKEN environment variable")
        print()
        print("   How to get a B2C token:")
        print("   1. Use Postman/curl to authenticate via B2C user flow")
        print("   2. Copy the access_token from the response")
        print("   3. Set: export B2C_TEST_TOKEN='<your-token>'")
        print()
        return True  # Not a failure, just skipped

    try:
        provider = AzureADB2CCredentialProvider()

        print("🔍 Validating B2C token...")
        claims = provider.validate_token(test_token, require_audience=False)

        print(f"✅ Token validated successfully")
        print()
        print(f"📋 Token Claims:")
        print(f"   Subject (oid): {claims.get('oid')}")
        print(f"   Name: {claims.get('name')}")
        print(f"   Emails: {claims.get('emails', [])}")
        print(f"   User Flow (tfp): {claims.get('tfp')}")
        print(f"   Identity Provider (idp): {claims.get('idp', 'local')}")
        print(f"   Issued at (iat): {claims.get('iat')}")
        print(f"   Expires at (exp): {claims.get('exp')}")
        print()

        # Extract roles
        print("🎭 Extracting roles...")
        roles = provider.extract_roles(claims)
        print(f"   Roles: {roles if roles else '(none - no role claims)'}")
        print()

        # Show custom attributes
        print("🔧 Custom Attributes:")
        for key, value in claims.items():
            if key.startswith("extension_"):
                print(f"   {key}: {value}")
        print()

        # Test user extraction
        print("👤 Testing user extraction...")
        from services.aad_authentication import AzureADAuthorization
        user = AzureADAuthorization._get_user_from_provider_token(claims, provider)
        print(f"   User ID: {user.id}")
        print(f"   Name: {user.name}")
        print(f"   Email: {user.email}")
        print(f"   Roles: {user.roles}")
        print()

        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("✅ Token validation test passed!")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_role_extraction():
    """Test role extraction from B2C custom attributes."""
    print("🧪 Testing B2C role extraction...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()

    try:
        provider = AzureADB2CCredentialProvider()

        # Test various role claim formats
        test_cases = [
            {
                "name": "Single WorkspaceRole",
                "claims": {"extension_WorkspaceRole": "WorkspaceOwner"},
                "expected": ["WorkspaceOwner"]
            },
            {
                "name": "Multiple roles (comma-separated)",
                "claims": {"extension_WorkspaceRole": "WorkspaceOwner,WorkspaceResearcher"},
                "expected": ["WorkspaceOwner", "WorkspaceResearcher"]
            },
            {
                "name": "TRE roles",
                "claims": {"extension_TRERole": "TREUser"},
                "expected": ["TREUser"]
            },
            {
                "name": "Airlock role",
                "claims": {"extension_AirlockRole": "AirlockManager"},
                "expected": ["AirlockManager"]
            },
            {
                "name": "Multiple role types",
                "claims": {
                    "extension_WorkspaceRole": "WorkspaceOwner",
                    "extension_TRERole": "TREUser",
                    "extension_AirlockRole": "AirlockManager"
                },
                "expected": ["WorkspaceOwner", "TREUser", "AirlockManager"]
            },
            {
                "name": "No roles",
                "claims": {},
                "expected": []
            }
        ]

        all_passed = True
        for i, test_case in enumerate(test_cases, 1):
            roles = provider.extract_roles(test_case["claims"])
            expected = test_case["expected"]

            if set(roles) == set(expected):
                print(f"✅ Test {i}: {test_case['name']}")
                print(f"   Claims: {test_case['claims']}")
                print(f"   Extracted: {roles}")
            else:
                print(f"❌ Test {i}: {test_case['name']}")
                print(f"   Claims: {test_case['claims']}")
                print(f"   Expected: {expected}")
                print(f"   Got: {roles}")
                all_passed = False
            print()

        if all_passed:
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print("✅ All role extraction tests passed!")

        return all_passed

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all B2C provider tests."""
    print("╔══════════════════════════════════════════════════╗")
    print("║   Azure AD B2C Credential Provider Tests        ║")
    print("╚══════════════════════════════════════════════════╝")
    print()

    # Check environment
    print("📋 Environment:")
    print(f"   AUTH_TYPE: {config.AUTH_TYPE}")
    print(f"   B2C_TENANT_NAME: {config.B2C_TENANT_NAME}")
    print(f"   B2C_POLICY_SUSI: {config.B2C_POLICY_SUSI}")
    print(f"   B2C_CLIENT_ID: {config.B2C_CLIENT_ID[:8] if config.B2C_CLIENT_ID else '(not set)'}...")
    print()

    # Run tests
    test1 = await test_b2c_provider_initialization()
    test2 = await test_oidc_discovery()
    test3 = await test_role_extraction()
    test4 = await test_token_validation()

    # Summary
    print()
    print("╔══════════════════════════════════════════════════╗")
    if test1 and test2 and test3 and test4:
        print("║           ✅ ALL TESTS PASSED                    ║")
    else:
        print("║           ❌ SOME TESTS FAILED                   ║")
        failed_tests = []
        if not test1:
            failed_tests.append("Provider initialization")
        if not test2:
            failed_tests.append("OIDC discovery")
        if not test3:
            failed_tests.append("Role extraction")
        if not test4:
            failed_tests.append("Token validation")
        print("║                                                  ║")
        for test in failed_tests:
            print(f"║   ❌ {test:<43}║")
    print("╚══════════════════════════════════════════════════╝")

    return test1 and test2 and test3 and test4


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
