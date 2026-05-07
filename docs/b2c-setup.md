# Azure AD B2C Setup Guide

This guide explains how to set up Azure AD B2C (Business-to-Consumer) authentication for Azure TRE, enabling consumer identity scenarios with social identity providers and custom user flows.

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Create Azure AD B2C Tenant](#create-azure-ad-b2c-tenant)
4. [Configure Custom Attributes](#configure-custom-attributes)
5. [Configure User Flows](#configure-user-flows)
6. [Register TRE API Application](#register-tre-api-application)
7. [Configure Social Identity Providers](#configure-social-identity-providers-optional)
8. [TRE Configuration](#tre-configuration)
9. [Testing](#testing)
10. [Troubleshooting](#troubleshooting)

---

## Overview

Azure AD B2C provides:
- **Consumer Identity Management**: Authenticate millions of consumer users
- **Social Identity Providers**: Microsoft Account, Google, Facebook, etc.
- **Custom User Flows**: Sign-up, sign-in, profile editing, password reset
- **Custom Attributes**: Map B2C user attributes to TRE roles
- **Self-Service**: Users manage their own accounts

**Use B2C when:**
- Building consumer-facing TRE deployments
- Requiring social identity provider integration
- Needing self-service user management
- Supporting multi-tenant consumer scenarios

**Use Azure AD Enterprise when:**
- Building internal enterprise TRE deployments
- Using corporate Azure AD for authentication
- Requiring Azure AD groups and enterprise app roles

---

## Prerequisites

- Azure subscription with permissions to create B2C tenants
- Azure AD B2C pricing tier: Free tier (50,000 MAU) or Premium P1/P2
- Understanding of OAuth2 and OIDC
- TRE instance with AUTH_TYPE configuration support

---

## Create Azure AD B2C Tenant

### 1. Create B2C Tenant

1. Navigate to [Azure Portal](https://portal.azure.com)
2. Click **Create a resource** → Search for **Azure Active Directory B2C**
3. Click **Create**
4. Select **Create a new Azure AD B2C Tenant**
5. Fill in details:
   - **Organization name**: e.g., "Contoso TRE B2C"
   - **Initial domain name**: e.g., "contosotreb2c" (this becomes `contosotreb2c.onmicrosoft.com`)
   - **Country/Region**: Select your location
   - **Subscription**: Select subscription
   - **Resource group**: Create new or select existing
6. Click **Create**

> **Note**: Creating a B2C tenant can take several minutes.

### 2. Link B2C Tenant to Subscription

1. In the B2C tenant, navigate to **Subscriptions**
2. Click **Link a subscription** if not already linked
3. Select your Azure subscription
4. Ensure billing is enabled for B2C

### 3. Get Tenant Information

After creation, note:
- **Tenant Name**: `contosotreb2c` (from domain `contosotreb2c.onmicrosoft.com`)
- **Tenant ID**: Found in **Azure AD B2C → Overview**
- **Domain**: `contosotreb2c.b2clogin.com`

---

## Configure Custom Attributes

TRE requires custom attributes to map B2C users to TRE roles.

### 1. Navigate to User Attributes

1. In B2C tenant, go to **User attributes**
2. Click **+ Add**

### 2. Create Custom Attributes

Create the following custom attributes:

| Attribute Name | Data Type | Description |
|----------------|-----------|-------------|
| `WorkspaceRole` | String | Workspace role: WorkspaceOwner, WorkspaceResearcher |
| `TRERole` | String | TRE core role: TREAdmin, TREUser |
| `AirlockRole` | String | Airlock role: AirlockManager |

**Steps for each attribute:**
1. **Name**: e.g., `WorkspaceRole`
2. **Data type**: String
3. **Description**: e.g., "TRE workspace role"
4. Click **Create**

> **Note**: B2C prefixes custom attributes with `extension_` in JWT tokens. For example, `WorkspaceRole` becomes `extension_WorkspaceRole`.

---

## Configure User Flows

User flows define the authentication experience (sign-up, sign-in, etc.).

### 1. Create Sign-up and Sign-in User Flow

1. Navigate to **User flows** in B2C tenant
2. Click **+ New user flow**
3. Select **Sign up and sign in** → **Recommended**
4. Configure:
   - **Name**: `susi` (full name will be `B2C_1_susi`)
   - **Identity providers**: 
     - ✅ Email signup
     - ✅ Local accounts (username/email/phone)
   - **Multifactor authentication**: Configure as needed
   - **User attributes and token claims**:

#### Select User Attributes (Collected during sign-up):
- ✅ Email Address
- ✅ Display Name
- ✅ WorkspaceRole (custom attribute)
- ✅ TRERole (custom attribute)
- ✅ AirlockRole (custom attribute) - optional

#### Select Application Claims (Returned in token):
- ✅ Email Addresses
- ✅ Display Name
- ✅ User's Object ID
- ✅ Identity Provider
- ✅ WorkspaceRole (custom attribute)
- ✅ TRERole (custom attribute)
- ✅ AirlockRole (custom attribute)

5. Click **Create**

### 2. Test User Flow (Optional)

1. Click on the created user flow (`B2C_1_susi`)
2. Click **Run user flow**
3. Select application: `https://jwt.ms` (for testing)
4. Click **Run user flow**
5. Complete sign-up/sign-in process
6. View the decoded JWT token at jwt.ms

---

## Register TRE API Application

### 1. Create App Registration

1. In B2C tenant, navigate to **App registrations**
2. Click **+ New registration**
3. Configure:
   - **Name**: `TRE API`
   - **Supported account types**: Accounts in this organizational directory only
   - **Redirect URI**: 
     - Platform: **Web**
     - URI: `https://your-tre-domain.com/api/oauth2/callback` (or `http://localhost:8000/api/oauth2/callback` for local dev)
4. Click **Register**

### 2. Get Application (Client) ID

1. In the app registration, go to **Overview**
2. Copy **Application (client) ID** → This is `B2C_CLIENT_ID`

### 3. Create Client Secret (if needed)

1. Go to **Certificates & secrets**
2. Click **+ New client secret**
3. Description: `TRE API Secret`
4. Expires: Select appropriate duration
5. Click **Add**
6. **Copy the secret value immediately** → This is `B2C_CLIENT_SECRET`

> **Important**: Secret value is only shown once. Store it securely.

### 4. Expose an API (Optional for API scopes)

1. Go to **Expose an API**
2. Click **+ Add a scope**
3. Accept default Application ID URI or customize
4. Configure scope:
   - **Scope name**: `user_impersonation`
   - **Admin consent display name**: Access TRE API
   - **Admin consent description**: Allow app to access TRE API on behalf of signed-in user
   - **State**: Enabled
5. Click **Add scope**

### 5. Configure Token Claims

1. Go to **Token configuration**
2. Click **+ Add optional claim**
3. Token type: **ID** and **Access**
4. Add claims:
   - ✅ email
   - ✅ family_name
   - ✅ given_name
5. Click **Add**

---

## Configure Social Identity Providers (Optional)

### Microsoft Account

1. In B2C tenant, go to **Identity providers**
2. Click **+ New OpenID Connect provider**
3. Select **Microsoft Account**
4. Follow wizard to configure
5. Add to user flow: Edit `B2C_1_susi` → Identity providers → Add Microsoft

### Google

1. Create OAuth 2.0 credentials in [Google Cloud Console](https://console.cloud.google.com/)
2. In B2C tenant, go to **Identity providers**
3. Click **+ Google**
4. Enter:
   - **Client ID**: From Google
   - **Client secret**: From Google
5. Save
6. Add to user flow: Edit `B2C_1_susi` → Identity providers → Add Google

### Facebook

1. Create Facebook app at [Facebook for Developers](https://developers.facebook.com/)
2. In B2C tenant, go to **Identity providers**
3. Click **+ Facebook**
4. Enter:
   - **Client ID**: From Facebook (App ID)
   - **Client secret**: From Facebook (App Secret)
5. Save
6. Add to user flow: Edit `B2C_1_susi` → Identity providers → Add Facebook

---

## TRE Configuration

### Environment Variables

Add to your TRE `.env` file or environment configuration:

```bash
# Authentication Type
AUTH_TYPE=b2c

# Azure AD B2C Configuration
B2C_TENANT_NAME=contosotreb2c                    # Your B2C tenant name (without .onmicrosoft.com)
B2C_POLICY_SUSI=B2C_1_susi                       # Your sign-up/sign-in user flow name
B2C_CLIENT_ID=12345678-1234-1234-1234-1234567890 # Application (client) ID from app registration
B2C_CLIENT_SECRET=your-client-secret-value       # Client secret (if needed)

# Optional Configuration
B2C_ROLE_CLAIM_NAME=extension_WorkspaceRole      # Custom role claim name (default: extension_WorkspaceRole)
```

### Configuration Validation

Verify B2C configuration:

```bash
# Check environment variables
echo $AUTH_TYPE          # Should be: b2c
echo $B2C_TENANT_NAME    # Should be: your-tenant-name
echo $B2C_CLIENT_ID      # Should be: your-client-id

# Start TRE and check logs
docker-compose up -d
docker logs api-server | grep "B2C"

# Expected log output:
# INFO: Initialized AzureADB2CCredentialProvider for tenant: contosotreb2c
# DEBUG: Using Azure AD B2C for credentials
```

### OIDC Endpoints

B2C uses different OIDC endpoints than Azure AD Enterprise:

**Discovery URL:**
```
https://{tenant}.b2clogin.com/{tenant}.onmicrosoft.com/{policy}/v2.0/.well-known/openid-configuration
```

Example:
```
https://contosotreb2c.b2clogin.com/contosotreb2c.onmicrosoft.com/B2C_1_susi/v2.0/.well-known/openid-configuration
```

**JWKS URI:**
```
https://{tenant}.b2clogin.com/{tenant}.onmicrosoft.com/discovery/v2.0/keys?p={policy}
```

---

## Testing

### 1. Test B2C Credential Provider

Run the B2C test script:

```bash
cd api_app

# Set environment for B2C
export AUTH_TYPE=b2c
export B2C_TENANT_NAME=contosotreb2c
export B2C_POLICY_SUSI=B2C_1_susi
export B2C_CLIENT_ID=your-client-id

# Run tests
python test_b2c_credentials.py
```

### 2. Get B2C Token (Manual Testing)

#### Option A: Using Postman

1. Create new request in Postman
2. Authorization tab:
   - Type: OAuth 2.0
   - Grant Type: Authorization Code (with PKCE)
3. Configure OAuth 2.0:
   - **Auth URL**: `https://{tenant}.b2clogin.com/{tenant}.onmicrosoft.com/{policy}/oauth2/v2.0/authorize`
   - **Access Token URL**: `https://{tenant}.b2clogin.com/{tenant}.onmicrosoft.com/{policy}/oauth2/v2.0/token`
   - **Client ID**: Your B2C client ID
   - **Scope**: `openid profile email`
   - **State**: (random string)
4. Click **Get New Access Token**
5. Complete B2C sign-in
6. Copy access token

#### Option B: Using curl (Password Grant - if enabled)

```bash
curl -X POST \
  "https://contosotreb2c.b2clogin.com/contosotreb2c.onmicrosoft.com/B2C_1_susi/oauth2/v2.0/token" \
  -d "grant_type=password" \
  -d "client_id=$B2C_CLIENT_ID" \
  -d "username=testuser@example.com" \
  -d "password=YourPassword123!" \
  -d "scope=openid"
```

> **Note**: Password grant (ROPC) must be explicitly enabled in B2C user flow settings.

### 3. Test TRE API with B2C Token

```bash
# Get token (from Postman or curl)
TOKEN="your-b2c-access-token"

# Test API endpoint
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/workspaces

# Expected: 200 OK with workspace list (if user has WorkspaceOwner role)
```

### 4. Validate Token Claims

Decode the B2C token to verify claims:

```bash
# Decode JWT (payload is base64-encoded)
echo $TOKEN | cut -d'.' -f2 | base64 -d | jq .
```

**Expected claims:**
```json
{
  "oid": "a1b2c3d4-...",
  "name": "Jane Doe",
  "emails": ["jane@outlook.com"],
  "tfp": "B2C_1_susi",
  "idp": "google.com",
  "extension_WorkspaceRole": "WorkspaceOwner",
  "extension_TRERole": "TREUser",
  "iat": 1714665600,
  "exp": 1714669200,
  "aud": "your-client-id"
}
```

### 5. Test Role-Based Access

```bash
# User with WorkspaceOwner role should access workspace endpoints
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/workspaces

# User without required role should get 403 Forbidden
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/admin/users
# Expected: 403 Forbidden (if user doesn't have TREAdmin role)
```

---

## Troubleshooting

### Issue: Token validation fails with "Invalid signature"

**Cause**: JWKS URI may be incorrect or B2C keys have rotated.

**Solution:**
1. Verify JWKS URI is correct:
   ```bash
   curl "https://{tenant}.b2clogin.com/{tenant}.onmicrosoft.com/discovery/v2.0/keys?p={policy}"
   ```
2. Check TRE logs for JWKS errors:
   ```bash
   docker logs api-server | grep -i jwks
   ```
3. Restart TRE to refresh JWKS cache

### Issue: Token validation fails with "Audience mismatch"

**Cause**: B2C token `aud` claim doesn't match `B2C_CLIENT_ID`.

**Solution:**
1. Check token audience:
   ```bash
   echo $TOKEN | cut -d'.' -f2 | base64 -d | jq .aud
   ```
2. Verify `B2C_CLIENT_ID` matches app registration client ID
3. Ensure token was issued for the correct application

### Issue: Custom attributes not in token

**Cause**: User flow not configured to return custom attributes.

**Solution:**
1. Edit user flow (`B2C_1_susi`)
2. Go to **Application claims**
3. Ensure custom attributes are checked:
   - ✅ WorkspaceRole
   - ✅ TRERole
   - ✅ AirlockManager
4. Save user flow
5. Get new token (existing tokens won't have new claims)

### Issue: User has no roles extracted

**Cause**: Custom attributes not set for user or claim names don't match.

**Solution:**
1. Check token claims:
   ```bash
   echo $TOKEN | cut -d'.' -f2 | base64 -d | jq . | grep extension
   ```
2. Verify custom attribute names match:
   - Token claim: `extension_WorkspaceRole`
   - Config: `B2C_ROLE_CLAIM_NAME=extension_WorkspaceRole`
3. Set user attributes in B2C:
   - Azure Portal → B2C → Users
   - Select user → Edit
   - Set custom attributes

### Issue: "B2C_TENANT_NAME must be configured" error

**Cause**: Environment variable not set or TRE not configured for B2C.

**Solution:**
1. Verify environment variables:
   ```bash
   echo $AUTH_TYPE         # Must be: b2c
   echo $B2C_TENANT_NAME   # Must be set
   ```
2. Restart TRE after setting variables:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

### Issue: Social identity provider not working

**Cause**: IDP not configured in user flow or credentials incorrect.

**Solution:**
1. Verify IDP added to user flow:
   - Edit `B2C_1_susi`
   - Check Identity providers section
2. Test IDP configuration:
   - Click **Run user flow**
   - Select social IDP
   - Complete authentication
3. Check IDP credentials in B2C:
   - Go to Identity providers
   - Verify client ID/secret

---

## Token Structure Reference

### B2C Token vs Azure AD Enterprise

| Claim | Azure AD Enterprise | Azure AD B2C |
|-------|---------------------|--------------|
| Email | `email` (string) | `emails` (array) |
| Roles | `roles` (array) | `extension_*` (custom attributes) |
| User Flow | N/A | `tfp` (policy name) |
| Identity Provider | N/A | `idp` (provider identifier) |
| User ID | `oid` | `oid` |
| Name | `name` | `name` |

### Example B2C Token

```json
{
  "oid": "a1b2c3d4-e5f6-4789-a012-3456789abcde",
  "sub": "a1b2c3d4-e5f6-4789-a012-3456789abcde",
  "name": "Jane Consumer",
  "given_name": "Jane",
  "family_name": "Consumer",
  "emails": ["jane@outlook.com"],
  "tfp": "B2C_1_susi",
  "idp": "google.com",
  "extension_WorkspaceRole": "WorkspaceOwner",
  "extension_TRERole": "TREUser",
  "extension_AirlockRole": "AirlockManager",
  "iat": 1714665600,
  "exp": 1714669200,
  "nbf": 1714665600,
  "aud": "12345678-1234-1234-1234-123456789abc",
  "iss": "https://contosotreb2c.b2clogin.com/12345678-1234-1234-1234-123456789abc/v2.0/",
  "ver": "2.0"
}
```

---

## Best Practices

### Security

1. **Use HTTPS**: Always use HTTPS in production for redirect URIs
2. **Rotate Secrets**: Rotate client secrets regularly
3. **Limit Token Lifetime**: Configure appropriate token expiration (default: 1 hour)
4. **Validate Audience**: Always validate `aud` claim matches your client ID
5. **Monitor Sign-ins**: Use B2C audit logs to monitor authentication activity

### User Management

1. **Default Roles**: Assign default roles during sign-up (e.g., TREUser)
2. **Role Elevation**: Require admin approval for elevated roles (WorkspaceOwner, TREAdmin)
3. **Self-Service**: Enable profile editing and password reset user flows
4. **Account Linking**: Consider account linking for users with multiple IDPs

### Performance

1. **Cache JWKS**: B2C provider caches signing keys (PyJWKClient)
2. **Token Reuse**: Clients should cache tokens until expiry
3. **Connection Pooling**: Use HTTP connection pooling for OIDC requests

### Monitoring

1. **Log Token Validation**: Enable debug logging for auth middleware
2. **Track IDPs**: Monitor which identity providers users prefer (`idp` claim)
3. **User Flow Analytics**: Use B2C reports to analyze user flow completion rates

---

## Additional Resources

- [Azure AD B2C Documentation](https://learn.microsoft.com/en-us/azure/active-directory-b2c/)
- [B2C User Flow Best Practices](https://learn.microsoft.com/en-us/azure/active-directory-b2c/user-flow-best-practices)
- [B2C Custom Policies](https://learn.microsoft.com/en-us/azure/active-directory-b2c/custom-policy-overview)
- [B2C Pricing](https://azure.microsoft.com/en-us/pricing/details/active-directory-b2c/)

---

**Created**: 2026-05-05  
**User Story**: #361  
**Version**: 1.0
