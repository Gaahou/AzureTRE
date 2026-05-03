# Phase 3 Test Plan: Local Authentication & Secrets

**Testing User Story:** TBD  
**Feature:** TBD - F4: Local Authentication & Secrets (Phase 3)  
**Stories:** 126-131  
**Branch:** feature/phase3-auth-secrets  
**Last Commit:** a20bb026a59c6f7e7d1c16d3d8f7a2f8e5e5e5e5  
**Test Date:** 2026-05-03

---

## Test Environment

### Docker-Based Testing (Rule #7)
All tests executed in Docker containers to ensure reproducible results.

**Test Script:** `scripts/test_phase3_docker.sh`

**Test Image:** `azuretre-api-test:phase3` (built from `api_app/Dockerfile`)

---

## Test Scope

Phase 3 introduces local authentication and secrets management for offline mode:

### Stories Under Test

| ID | Story | Description |
|----|-------|-------------|
| 126 | Add Keycloak to offline docker-compose | Keycloak container for OIDC authentication |
| 127 | Create Keycloak realm configuration | AzureTRE realm with clients and roles |
| 128 | Implement local credential provider | `KeycloakCredentialProvider` implementing `CredentialProvider` interface |
| 129 | Abstract auth middleware to use provider | Auth middleware uses factory pattern for credentials |
| 130 | Add HashiCorp Vault for secrets management | Vault container with KV v2 secrets engine |
| 131 | Update UI for offline auth flow | UI redirects to Keycloak for login |

---

## Test Categories

### 1. Infrastructure Tests

#### 1.1 Keycloak Container Startup
**Story:** 126  
**Objective:** Verify Keycloak starts successfully in offline mode

**Test Steps:**
```bash
cd deploy/offline
docker-compose up -d keycloak
docker-compose ps keycloak
```

**Expected Results:**
- [ ] Keycloak container starts successfully
- [ ] Container status is "running"
- [ ] Keycloak UI accessible at http://localhost:8080
- [ ] Admin credentials work (admin/admin_password)
- [ ] AzureTRE realm imported automatically

**Acceptance Criteria:**
- Container starts within 60 seconds
- Admin console accessible
- No error logs in container

---

#### 1.2 Vault Container Startup
**Story:** 130  
**Objective:** Verify HashiCorp Vault starts successfully in offline mode

**Test Steps:**
```bash
cd deploy/offline
docker-compose up -d vault
docker-compose ps vault
docker-compose logs vault
```

**Expected Results:**
- [ ] Vault container starts successfully
- [ ] Container status is "running"
- [ ] Vault UI accessible at http://localhost:8200
- [ ] Dev mode root token works (root-token)
- [ ] KV v2 secrets engine enabled at /secret
- [ ] Logs show "Development mode" initialized

**Acceptance Criteria:**
- Container starts within 15 seconds
- Vault API responsive
- KV v2 engine ready

---

#### 1.3 Keycloak Realm Configuration
**Story:** 127  
**Objective:** Verify AzureTRE realm is properly configured

**Test Steps:**
```bash
# Check realm file exists
ls -la deploy/offline/seed/AzureTRE-realm.json

# Verify realm imported
curl -s http://localhost:8080/realms/AzureTRE/.well-known/openid-configuration | jq .
```

**Expected Results:**
- [ ] Realm configuration file exists
- [ ] Realm imported into Keycloak
- [ ] OIDC discovery endpoint returns valid configuration
- [ ] Client `tre-api-client` exists
- [ ] Realm roles include: TREAdmin, TREUser, WorkspaceOwner, WorkspaceResearcher
- [ ] JWKS URI accessible

**Acceptance Criteria:**
- OIDC discovery returns 200 OK
- All required roles present
- Client configured with secret

---

### 2. Credential Provider Tests

#### 2.1 Keycloak Credential Provider - Initialization
**Story:** 128  
**Objective:** Verify `KeycloakCredentialProvider` initializes correctly

**Test Steps:**
```python
# In Docker container
from providers.local.credentials import KeycloakCredentialProvider
import asyncio

async def test_init():
    provider = KeycloakCredentialProvider()
    print(f"Keycloak URL: {provider.keycloak_url}")
    print(f"Realm: {provider.realm}")
    print(f"Client ID: {provider.client_id}")
    assert provider.realm == "AzureTRE"
    print("✓ Provider initialized")

asyncio.run(test_init())
```

**Expected Results:**
- [ ] Provider initializes without errors
- [ ] Keycloak URL set correctly
- [ ] Realm name is "AzureTRE"
- [ ] Client ID configured

**Acceptance Criteria:**
- No initialization errors
- All configuration loaded from environment

---

#### 2.2 Keycloak Token Validation
**Story:** 128  
**Objective:** Verify provider can validate Keycloak JWT tokens

**Test Steps:**
```python
# In Docker container (with Keycloak running)
from providers.local.credentials import KeycloakCredentialProvider
import httpx
import asyncio

async def test_token_validation():
    # 1. Get token from Keycloak
    token_url = "http://keycloak:8080/realms/AzureTRE/protocol/openid-connect/token"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": "tre-api-client",
                "client_secret": "tre-api-client-secret"
            }
        )
        token = response.json()["access_token"]
    
    # 2. Validate token
    provider = KeycloakCredentialProvider()
    credential = await provider.get_credential_from_token(token)
    
    assert credential is not None
    print("✓ Token validated successfully")

asyncio.run(test_token_validation())
```

**Expected Results:**
- [ ] Token obtained from Keycloak
- [ ] Token validated successfully
- [ ] Credential object returned
- [ ] No validation errors

**Acceptance Criteria:**
- Valid tokens accepted
- Invalid tokens rejected
- Expired tokens rejected

---

#### 2.3 Credential Provider Factory
**Story:** 128, 129  
**Objective:** Verify factory returns correct credential provider based on `DEPLOYMENT_MODE`

**Test Steps:**
```python
import os
from providers.factory import get_credential_provider

# Test 1: Offline mode
os.environ["DEPLOYMENT_MODE"] = "offline"
provider = get_credential_provider()
assert provider.__class__.__name__ == "KeycloakCredentialProvider"

# Test 2: Online mode
os.environ["DEPLOYMENT_MODE"] = "online"
provider = get_credential_provider()
assert provider.__class__.__name__ == "AzureMSICredentialProvider"
```

**Expected Results:**
- [ ] Offline mode returns `KeycloakCredentialProvider`
- [ ] Online mode returns `AzureMSICredentialProvider`
- [ ] No import errors
- [ ] Factory pattern working correctly

**Acceptance Criteria:**
- Correct implementation returned based on mode
- Both implementations follow `CredentialProvider` interface

---

### 3. Secrets Management Tests

#### 3.1 Vault Secret Provider - Basic Operations
**Story:** 130  
**Objective:** Verify `LocalSecretProvider` can store and retrieve secrets from Vault

**Test Steps:**
```python
# In Docker container (with Vault running)
from providers.local.secrets import LocalSecretProvider
import asyncio

async def test_secrets():
    provider = LocalSecretProvider()
    
    # Test 1: Set secret
    await provider.set_secret("test-secret", "test-value-123")
    print("✓ Secret stored")
    
    # Test 2: Get secret
    value = await provider.get_secret("test-secret")
    assert value == "test-value-123"
    print("✓ Secret retrieved")
    
    # Test 3: Delete secret
    await provider.delete_secret("test-secret")
    print("✓ Secret deleted")
    
    # Test 4: Get deleted secret (should return None)
    value = await provider.get_secret("test-secret")
    assert value is None
    print("✓ Deleted secret returns None")

asyncio.run(test_secrets())
```

**Expected Results:**
- [ ] Secrets stored successfully in Vault
- [ ] Secrets retrieved with correct values
- [ ] Secrets deleted successfully
- [ ] Deleted secrets return None
- [ ] No connection errors to Vault

**Acceptance Criteria:**
- All CRUD operations work
- Values preserved correctly
- Vault API responds within 1 second

---

#### 3.2 Secret Provider Factory
**Story:** 130  
**Objective:** Verify factory returns correct secret provider based on `DEPLOYMENT_MODE`

**Test Steps:**
```python
import os
from providers.factory import get_secret_provider

# Test 1: Offline mode
os.environ["DEPLOYMENT_MODE"] = "offline"
provider = get_secret_provider()
assert provider.__class__.__name__ == "LocalSecretProvider"

# Test 2: Online mode
os.environ["DEPLOYMENT_MODE"] = "online"
provider = get_secret_provider()
assert provider.__class__.__name__ == "AzureKeyVaultSecretProvider"
```

**Expected Results:**
- [ ] Offline mode returns `LocalSecretProvider`
- [ ] Online mode returns `AzureKeyVaultSecretProvider`
- [ ] No import errors
- [ ] Factory pattern working correctly

**Acceptance Criteria:**
- Correct implementation returned based on mode
- Both implementations follow `SecretProvider` interface

---

### 4. Authentication Middleware Tests

#### 4.1 Auth Middleware Uses Provider
**Story:** 129  
**Objective:** Verify authentication middleware uses credential provider factory

**Test Steps:**
```python
# In Docker container
import inspect
from services import aad_authentication

# Check if middleware uses factory
source = inspect.getsource(aad_authentication.AzureADAuthorization)
assert "get_credential_provider()" in source or "CredentialProvider" in source
print("✓ Middleware uses credential provider")
```

**Expected Results:**
- [ ] Middleware calls `get_credential_provider()`
- [ ] No direct Azure AD SDK calls for credentials
- [ ] Provider abstraction used throughout
- [ ] Factory pattern implemented

**Acceptance Criteria:**
- Auth middleware abstracted
- Provider pattern used for credentials
- No breaking changes to existing auth flow

---

#### 4.2 Offline Auth Flow - JWT Validation
**Story:** 129, 131  
**Objective:** Verify API can validate Keycloak JWT tokens in offline mode

**Test Steps:**
```bash
# Start all services
cd deploy/offline
docker-compose up -d

# Get token from Keycloak
TOKEN=$(curl -s -X POST http://localhost:8080/realms/AzureTRE/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=tre-api-client" \
  -d "client_secret=tre-api-client-secret" | jq -r .access_token)

# Test API endpoint with Keycloak token
curl -s http://localhost:8000/api/health \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Results:**
- [ ] Token obtained from Keycloak
- [ ] API accepts Keycloak token
- [ ] JWT validated against Keycloak JWKS
- [ ] User roles extracted from token
- [ ] API returns successful response

**Acceptance Criteria:**
- End-to-end auth flow works
- Tokens validated correctly
- No Azure AD dependency in offline mode

---

### 5. Integration Tests

#### 5.1 Complete Offline Auth Flow
**Stories:** 126-131  
**Objective:** Verify complete authentication flow in offline mode

**Test Steps:**
```bash
# 1. Start all services
cd deploy/offline
docker-compose up -d

# 2. Verify Keycloak ready
curl -f http://localhost:8080/realms/AzureTRE/.well-known/openid-configuration

# 3. Obtain token
TOKEN=$(curl -s -X POST http://localhost:8080/realms/AzureTRE/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=tre-api-client" \
  -d "client_secret=tre-api-client-secret" | jq -r .access_token)

# 4. Call protected API endpoint
curl -i http://localhost:8000/api/workspaces \
  -H "Authorization: Bearer $TOKEN"

# 5. Verify secret storage
curl -X POST http://localhost:8200/v1/secret/data/test-integration \
  -H "X-Vault-Token: root-token" \
  -H "Content-Type: application/json" \
  -d '{"data": {"value": "test-123"}}'

curl -s http://localhost:8200/v1/secret/data/test-integration \
  -H "X-Vault-Token: root-token" | jq .data.data.value
```

**Expected Results:**
- [ ] All services start successfully
- [ ] Keycloak authentication working
- [ ] API accepts Keycloak tokens
- [ ] Vault stores and retrieves secrets
- [ ] No Azure dependencies in offline mode
- [ ] Complete flow works end-to-end

**Acceptance Criteria:**
- Complete flow completes within 10 seconds
- No errors in any component
- Auth and secrets working together

---

#### 5.2 Secret Storage Integration
**Story:** 130  
**Objective:** Verify API can store/retrieve secrets via Vault provider

**Test Steps:**
```python
# In API runtime with Vault provider
from providers.factory import get_secret_provider
import asyncio

async def test_api_secrets():
    provider = get_secret_provider()
    
    # Simulate API storing workspace secret
    await provider.set_secret("workspace-ws001-key", "secret-value-123")
    
    # Simulate API retrieving workspace secret
    value = await provider.get_secret("workspace-ws001-key")
    assert value == "secret-value-123"
    
    print("✓ API secret storage working")

asyncio.run(test_api_secrets())
```

**Expected Results:**
- [ ] API stores secrets in Vault
- [ ] API retrieves secrets from Vault
- [ ] No Azure Key Vault calls in offline mode
- [ ] Secrets isolated per workspace/resource

**Acceptance Criteria:**
- API uses provider abstraction
- Vault backend working
- No breaking changes

---

### 6. Regression Tests

#### 6.1 Online Mode - No Regressions
**Stories:** 126-131  
**Objective:** Verify online mode (Azure AD / Key Vault) still works

**Test Steps:**
```bash
# Set online mode
export DEPLOYMENT_MODE=online

# Run API in Docker
cd api_app
docker build --target test -t azuretre-api-test:phase3 .
docker run --rm \
  -e DEPLOYMENT_MODE=online \
  azuretre-api-test:phase3 \
  python -c "
from providers.factory import get_credential_provider, get_secret_provider

cp = get_credential_provider()
print(f'Credential Provider: {cp.__class__.__name__}')
assert cp.__class__.__name__ == 'AzureMSICredentialProvider'

sp = get_secret_provider()
print(f'Secret Provider: {sp.__class__.__name__}')
assert sp.__class__.__name__ == 'AzureKeyVaultSecretProvider'

print('✅ Online mode working correctly')
"
```

**Expected Results:**
- [ ] Online mode uses `AzureMSICredentialProvider`
- [ ] Online mode uses `AzureKeyVaultSecretProvider`
- [ ] No import errors
- [ ] No breaking changes to Azure implementations

**Acceptance Criteria:**
- Online mode unchanged
- Azure SDK still imported correctly
- No regressions

---

### 7. Unit Tests

#### 7.1 Keycloak Credential Provider Tests
**Story:** 128  
**Objective:** Run standalone tests for Keycloak provider

**Test Steps:**
```bash
cd api_app
docker run --rm \
  --network deploy_offline_tre-local \
  -v "$PWD:/api" \
  -w /api \
  azuretre-api-test:phase3 \
  python test_local_credentials.py
```

**Expected Results:**
- [ ] All credential tests pass
- [ ] Token validation works
- [ ] Role mapping works
- [ ] No errors

**Acceptance Criteria:**
- Zero test failures

---

#### 7.2 Vault Secret Provider Tests
**Story:** 130  
**Objective:** Run standalone tests for Vault provider

**Test Steps:**
```bash
cd api_app
docker run --rm \
  --network deploy_offline_tre-local \
  -v "$PWD:/api" \
  -w /api \
  azuretre-api-test:phase3 \
  python test_local_secrets.py
```

**Expected Results:**
- [ ] All secret tests pass
- [ ] CRUD operations work
- [ ] Error handling works
- [ ] No errors

**Acceptance Criteria:**
- Zero test failures

---

#### 7.3 Auth Middleware Tests
**Story:** 129  
**Objective:** Run tests for abstracted auth middleware

**Test Steps:**
```bash
cd api_app
docker run --rm \
  --network deploy_offline_tre-local \
  -v "$PWD:/api" \
  -w /api \
  azuretre-api-test:phase3 \
  python test_auth_middleware.py
```

**Expected Results:**
- [ ] All auth tests pass
- [ ] Provider abstraction works
- [ ] Role extraction works
- [ ] No errors

**Acceptance Criteria:**
- Zero test failures

---

#### 7.4 Run Full Test Suite
**All Stories**  
**Objective:** Verify all existing unit tests pass

**Test Steps:**
```bash
# In Docker container
cd /api
pytest tests_ma/ -v --tb=short
```

**Expected Results:**
- [ ] All tests pass (100%)
- [ ] No new test failures
- [ ] No skipped tests
- [ ] Test coverage maintained or improved

**Acceptance Criteria:**
- Zero test failures
- Test suite completes within 3 minutes

---

### 8. Code Quality Tests

#### 8.1 Linting
**All Stories**  
**Objective:** Verify code follows style guidelines

**Test Steps:**
```bash
cd api_app
flake8 providers/ services/aad_authentication.py --count --max-line-length=127
```

**Expected Results:**
- [ ] No linting errors
- [ ] Code follows PEP 8 guidelines
- [ ] No unused imports

**Acceptance Criteria:**
- Zero linting errors

---

### 9. Security Tests

#### 9.1 Vault Token Security
**Story:** 130  
**Objective:** Verify Vault tokens not exposed in logs or errors

**Test Steps:**
```bash
# Check API logs for exposed tokens
docker-compose logs api | grep -i "root-token" | grep -v "X-Vault-Token: [REDACTED]"
```

**Expected Results:**
- [ ] No tokens in plain text logs
- [ ] Tokens redacted in error messages
- [ ] Secrets not leaked in responses

**Acceptance Criteria:**
- No token exposure

---

#### 9.2 JWT Token Validation
**Story:** 128  
**Objective:** Verify invalid tokens are rejected

**Test Steps:**
```bash
# Test with invalid token
curl -i http://localhost:8000/api/workspaces \
  -H "Authorization: Bearer invalid-token-here"
```

**Expected Results:**
- [ ] Invalid tokens rejected
- [ ] 401 Unauthorized returned
- [ ] No information leakage in error
- [ ] Expired tokens rejected

**Acceptance Criteria:**
- All invalid tokens rejected
- Proper HTTP status codes

---

## Test Execution Checklist

- [ ] All infrastructure tests passed
- [ ] All credential provider tests passed
- [ ] All secrets management tests passed
- [ ] All auth middleware tests passed
- [ ] All integration tests passed
- [ ] All regression tests passed (online mode)
- [ ] All unit tests passed
- [ ] Code quality checks passed
- [ ] Security tests passed

---

## Test Results Summary

**Executed By:** [Name]  
**Execution Date:** [Date]  
**Environment:** Docker (local)  
**Commit:** a20bb026a59c6f7e7d1c16d3d8f7a2f8e5e5e5e5

### Results

| Category | Tests | Passed | Failed | Status |
|----------|-------|--------|--------|--------|
| Infrastructure | TBD | TBD | TBD | ⏳ Pending |
| Credential Provider | TBD | TBD | TBD | ⏳ Pending |
| Secrets Management | TBD | TBD | TBD | ⏳ Pending |
| Auth Middleware | TBD | TBD | TBD | ⏳ Pending |
| Integration | TBD | TBD | TBD | ⏳ Pending |
| Regression | TBD | TBD | TBD | ⏳ Pending |
| Unit Tests | TBD | TBD | TBD | ⏳ Pending |
| Code Quality | TBD | TBD | TBD | ⏳ Pending |
| Security | TBD | TBD | TBD | ⏳ Pending |

### Issues Found

[Document any issues discovered during testing]

### Recommendations

[Document any recommendations for improvements]

---

## Sign-off

- [ ] All acceptance criteria met
- [ ] All test categories completed
- [ ] Test results documented
- [ ] Issues logged (if any)
- [ ] Ready to close Phase 3 stories

**Tester Signature:** _______________  
**Date:** _______________