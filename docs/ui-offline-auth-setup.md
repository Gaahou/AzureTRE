# UI Offline Authentication Setup

This document describes how the Azure TRE UI handles authentication in offline deployment mode using Keycloak instead of Azure AD.

## Overview

The UI supports two authentication modes based on the `deploymentMode` configuration:

- **Online Mode** (`deploymentMode: "online"`): Uses Azure AD with MSAL (Microsoft Authentication Library)
- **Offline Mode** (`deploymentMode: "offline"`): Uses Keycloak with OIDC (OpenID Connect)

## Architecture

### File Structure

```
ui/app/src/
├── authConfig.ts          # Auth configuration based on deployment mode
├── keycloakAuth.ts        # Keycloak OIDC helper functions
└── config.source.json     # UI configuration template
```

### Configuration Files

#### config.source.json

```json
{
  "deploymentMode": "online",
  "rootClientId": "",
  "rootTenantId": "",
  "activeDirectoryUri": "",
  "keycloakUrl": "http://localhost:8080",
  "keycloakRealm": "AzureTRE",
  "keycloakClientId": "tre-ui-client",
  ...
}
```

**Key Fields:**
- `deploymentMode`: `"online"` or `"offline"` - determines auth provider
- `keycloakUrl`: Keycloak server URL (offline mode)
- `keycloakRealm`: Keycloak realm name (offline mode)
- `keycloakClientId`: OAuth client ID for UI (offline mode)

#### authConfig.ts

Exports different auth configurations based on deployment mode:

```typescript
export const authMode = isOfflineMode ? "keycloak" : "azuread";
export const pca = !isOfflineMode ? new PublicClientApplication(msalConfiguration) : null;
export const keycloakConfig = isOfflineMode ? keycloakConfiguration : null;
export const keycloakEndpoints = isOfflineMode ? {...} : null;
```

## Keycloak Configuration

### Realm Setup

The Keycloak realm (`AzureTRE`) is configured with:

**Client:** `tre-ui-client`
- **Type:** Public client (no client secret required)
- **Protocol:** OpenID Connect
- **Flow:** Authorization Code with PKCE
- **Redirect URIs:**
  - `http://localhost:3000/*`
  - `http://localhost:3000/oauth2/callback`
- **Web Origins:** `http://localhost:3000`

**Roles:**
- `WorkspaceOwner`: Full workspace control
- `WorkspaceResearcher`: Workspace resource access
- `AirlockManager`: Airlock request management

### PKCE Flow

The Keycloak authentication uses OAuth 2.0 Authorization Code flow with PKCE (Proof Key for Code Exchange) for enhanced security:

1. **Generate PKCE Parameters:**
   ```typescript
   const codeVerifier = generateCodeVerifier();  // Random string
   const codeChallenge = await generateCodeChallenge(verifier);  // SHA-256 hash
   ```

2. **Initiate Authorization:**
   ```typescript
   loginWithKeycloak() -> Redirects to Keycloak login page
   ```

3. **Handle Callback:**
   ```typescript
   handleKeycloakCallback() -> Exchanges code for tokens
   ```

4. **Store Tokens:**
   - Access token
   - Refresh token
   - Token expiry timestamp

## Authentication Flow

### Login Flow (Offline Mode)

```
User clicks "Login"
  ↓
loginWithKeycloak()
  ↓
Generate PKCE code_verifier and code_challenge
  ↓
Store verifier and state in sessionStorage
  ↓
Redirect to Keycloak: /realms/AzureTRE/protocol/openid-connect/auth
  ↓
User authenticates in Keycloak
  ↓
Keycloak redirects back with authorization code
  ↓
handleKeycloakCallback()
  ↓
Exchange code for tokens using code_verifier
  ↓
Store tokens in sessionStorage
  ↓
User authenticated
```

### Token Management

**Access Token:**
- Stored in `sessionStorage.getItem('access_token')`
- Used in API requests: `Authorization: Bearer {token}`
- Valid for 1 hour (configurable in Keycloak)

**Refresh Token:**
- Stored in `sessionStorage.getItem('refresh_token')`
- Used to obtain new access tokens
- Valid for longer period (10 hours default)

**Auto-Refresh:**
```typescript
if (isTokenExpired()) {
  await refreshKeycloakToken();
}
```

Tokens are considered expired 5 minutes before actual expiry for proactive refresh.

### Logout Flow

```
User clicks "Logout"
  ↓
logoutFromKeycloak()
  ↓
Clear sessionStorage tokens
  ↓
Redirect to Keycloak: /realms/AzureTRE/protocol/openid-connect/logout
  ↓
Keycloak logs out user
  ↓
Redirect back to UI
```

## API Integration

### Calling TRE API from UI

```typescript
const token = getAccessToken();

fetch('http://localhost:8000/api/workspaces', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  },
});
```

The TRE API validates the Keycloak token using the LocalCredentialProvider (Story #128).

### Token Validation

**API Side (api_app/providers/local/credentials.py):**
```python
def validate_token(self, token: str, require_audience: bool = False) -> dict:
    jwks_client = self._get_jwks_client()
    signing_key = jwks_client.get_signing_key_from_jwt(token)
    decoded = jwt.decode(token, signing_key.key, algorithms=["RS256"])
    return decoded
```

**Role Extraction:**
```python
def extract_roles(self, token_claims: dict) -> list[str]:
    realm_roles = token_claims.get("realm_access", {}).get("roles", [])
    tre_roles = [role for role in realm_roles
                 if role in ["WorkspaceOwner", "WorkspaceResearcher", "AirlockManager"]]
    return tre_roles
```

## Development Setup

### Local Development (Offline Mode)

1. **Start Keycloak:**
   ```bash
   cd deploy/offline
   docker-compose up -d keycloak
   ```

2. **Configure UI:**
   Create `ui/app/src/config.json` from template:
   ```bash
   cp ui/app/src/config.source.json ui/app/src/config.json
   ```

   Edit `config.json`:
   ```json
   {
     "deploymentMode": "offline",
     "keycloakUrl": "http://localhost:8080",
     "keycloakRealm": "AzureTRE",
     "keycloakClientId": "tre-ui-client",
     "treUrl": "http://localhost:8000/api"
   }
   ```

3. **Start UI:**
   ```bash
   cd ui/app
   npm install
   npm start
   ```

   UI runs at: http://localhost:3000

4. **Test Login:**
   - Click "Login" button
   - Redirected to Keycloak (http://localhost:8080)
   - Use credentials:
     - Username: `admin` / Password: `admin_password`
     - Username: `researcher` / Password: `researcher_password`
   - Redirected back to UI with tokens

### Online Development (Azure AD Mode)

1. **Configure UI:**
   Edit `config.json`:
   ```json
   {
     "deploymentMode": "online",
     "rootClientId": "{Azure AD App ID}",
     "rootTenantId": "{Azure AD Tenant ID}",
     "activeDirectoryUri": "https://login.microsoftonline.com",
     "treUrl": "https://my-tre.azure.com/api"
   }
   ```

2. **Start UI:**
   ```bash
   npm start
   ```

   Uses MSAL for Azure AD authentication.

## Testing

### Manual Testing Checklist

- [ ] Login redirects to Keycloak
- [ ] Successful authentication redirects back with tokens
- [ ] Access token stored in sessionStorage
- [ ] API calls include Bearer token
- [ ] Token auto-refreshes before expiry
- [ ] Logout clears tokens and redirects
- [ ] Role-based access control works
- [ ] PKCE parameters generated correctly

### Browser Console Testing

```javascript
// Check auth mode
import { authMode } from './authConfig';
console.log('Auth mode:', authMode);  // Should be "keycloak" in offline mode

// Check token
import { getAccessToken, isAuthenticated } from './keycloakAuth';
console.log('Is authenticated:', isAuthenticated());
console.log('Access token:', getAccessToken());

// Check user info
import { getKeycloakUser } from './keycloakAuth';
const user = await getKeycloakUser();
console.log('User:', user);
console.log('Roles:', user.realm_access?.roles);
```

## Troubleshooting

### Issue: "Keycloak not configured" Error

**Cause:** UI running in offline mode but config missing Keycloak settings.

**Fix:** Ensure `config.json` has:
```json
{
  "deploymentMode": "offline",
  "keycloakUrl": "http://localhost:8080",
  "keycloakRealm": "AzureTRE",
  "keycloakClientId": "tre-ui-client"
}
```

### Issue: Redirect Loop After Login

**Cause:** Redirect URI mismatch between UI and Keycloak client configuration.

**Fix:** Verify Keycloak client `tre-ui-client` has:
- Redirect URI: `http://localhost:3000/*`
- Web Origins: `http://localhost:3000`

### Issue: Token Validation Fails

**Cause:** API not configured for offline mode or Keycloak not accessible.

**Fix:**
1. Verify API has `DEPLOYMENT_MODE=offline`
2. Check Keycloak is running: `docker ps | grep keycloak`
3. Test Keycloak endpoint: `curl http://localhost:8080/realms/AzureTRE/.well-known/openid-configuration`

### Issue: CORS Errors

**Cause:** Keycloak not allowing requests from UI origin.

**Fix:** Check Keycloak client `tre-ui-client` has correct Web Origins set to `http://localhost:3000`.

## Security Considerations

### PKCE (Proof Key for Code Exchange)

PKCE prevents authorization code interception attacks:
- Code verifier: Random string, never sent to server
- Code challenge: SHA-256 hash of verifier, sent during authorization
- Code exchange: Verifier proven during token exchange

### Token Storage

Tokens stored in `sessionStorage` (not `localStorage`):
- Cleared when browser tab/window closed
- Not shared across tabs
- Reduces XSS attack surface

### State Parameter

Random state parameter prevents CSRF attacks:
- Generated during authorization request
- Stored in sessionStorage
- Validated on callback

## References

- **Keycloak Documentation:** https://www.keycloak.org/docs/latest/securing_apps/
- **OAuth 2.0 PKCE:** https://oauth.net/2/pkce/
- **OIDC Specification:** https://openid.net/specs/openid-connect-core-1_0.html
- **Story #128:** LocalCredentialProvider implementation
- **Story #129:** API authentication middleware abstraction
- **Story #131:** UI offline auth flow (this document)

## Related Files

- `api_app/providers/local/credentials.py` - Keycloak token validation
- `api_app/services/aad_authentication.py` - Auth middleware
- `deploy/offline/seed/AzureTRE-realm.json` - Keycloak realm configuration
- `ui/app/src/authConfig.ts` - Auth configuration
- `ui/app/src/keycloakAuth.ts` - Keycloak OIDC helper