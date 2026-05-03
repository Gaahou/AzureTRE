# User Story: Add Azure AD B2C Authentication Provider

## Story Information

**Title**: Implement Azure AD B2C credential provider for consumer identity scenarios

**Type**: User Story

**Epic**: Authentication & Identity Management

**Priority**: Medium

**Effort Estimate**: 3-4 days

**Dependencies**: 
- Story #128: Implement local credential provider (completed)
- Story #129: Abstract auth middleware to use provider (in progress)

---

## Description

Add support for Azure AD B2C (Business to Consumer) as an authentication provider, enabling TRE to authenticate consumer users with social identity providers and custom user flows. This complements the existing Azure AD (Enterprise) and Keycloak (Offline) providers.

Azure AD B2C is designed for consumer-facing applications and provides:
- Social identity provider integration (Microsoft, Google, Facebook, etc.)
- Custom user flows (sign-up, sign-in, profile editing, password reset)
- Custom attributes and claims
- Multi-tenant consumer scenarios

---

## Acceptance Criteria

- [ ] Users can authenticate via Azure AD B2C user flows
- [ ] Social identity providers work (Microsoft Account, Google, etc.)
- [ ] B2C custom attributes are mapped to TRE user properties
- [ ] B2C tokens are validated against B2C OIDC discovery endpoint
- [ ] App roles from B2C custom claims are extracted correctly
- [ ] B2C user flows (sign-up, sign-in, profile edit) are supported
- [ ] Online mode can be configured to use B2C instead of Enterprise AD
- [ ] Existing Azure AD and Keycloak providers continue to work
- [ ] No regression in offline mode or Enterprise AD mode

---

## Technical Implementation

### Files to Create/Modify

1. **api_app/providers/azure/b2c_credentials.py** (new)
   - Implement `AzureADB2CCredentialProvider` class
   - Validate JWT tokens against B2C OIDC discovery
   - Handle B2C-specific claims structure
   - Map B2C custom attributes to TRE roles
   - Support B2C user flows (susi, profile_edit, password_reset)

2. **api_app/providers/factory.py** (modify)
   - Add B2C provider option
   - Check `AUTH_TYPE` env var (aad, b2c, keycloak)
   - Return appropriate provider based on configuration

3. **api_app/core/config.py** (modify)
   - Add B2C-specific environment variables:
     - `B2C_TENANT_NAME` - B2C tenant name (e.g., "contosob2c")
     - `B2C_POLICY_SUSI` - Sign-up/Sign-in user flow name
     - `B2C_POLICY_PROFILE_EDIT` - Profile edit user flow name
     - `B2C_POLICY_PASSWORD_RESET` - Password reset user flow name
     - `B2C_CLIENT_ID` - B2C application client ID
     - `B2C_CLIENT_SECRET` - B2C application client secret (if required)

4. **api_app/services/authentication.py** (modify)
   - Update `get_access_service()` to support B2C
   - Add B2C-specific auth helper functions

5. **api_app/models/schemas/workspace.py** (modify)
   - Add `B2C` to `AuthProvider` enum

6. **deploy/azure/b2c-setup.md** (new)
   - Document B2C tenant setup
   - User flow configuration instructions
   - Custom attribute definitions
   - App registration steps

---

## Implementation Details

### B2C Token Structure Differences

**Azure AD Enterprise Token:**
```json
{
  "oid": "user-object-id",
  "name": "John Doe",
  "email": "john@contoso.com",
  "roles": ["WorkspaceOwner", "TREUser"]
}
```

**Azure AD B2C Token:**
```json
{
  "oid": "user-object-id",
  "name": "John Doe",
  "emails": ["john@outlook.com"],
  "extension_Role": "WorkspaceOwner",
  "extension_TRERole": "TREUser",
  "tfp": "B2C_1_susi",
  "idp": "google.com"
}
```

### Key Differences to Handle

1. **Claims Naming**: B2C uses different claim names
   - `emails` (array) instead of `email` (string)
   - Custom attributes with `extension_` prefix
   
2. **User Flows**: B2C includes user flow identifier (`tfp` claim)
   - Must validate token against correct user flow policy

3. **Identity Providers**: B2C tracks which IDP was used (`idp` claim)
   - Can implement IDP-specific logic if needed

4. **Role Mapping**: B2C custom attributes need mapping
   - `extension_Role` → TRE workspace roles
   - `extension_TRERole` → TRE core roles
   - Configurable mapping via environment variables

### OIDC Discovery Endpoint

**Azure AD Enterprise:**
```
https://login.microsoftonline.com/{tenant-id}/v2.0/.well-known/openid-configuration
```

**Azure AD B2C:**
```
https://{tenant-name}.b2clogin.com/{tenant-name}.onmicrosoft.com/{policy-name}/v2.0/.well-known/openid-configuration
```

### Provider Implementation Pattern

```python
class AzureADB2CCredentialProvider(CredentialProvider):
    """
    Azure AD B2C credential provider for consumer identity scenarios.
    """
    
    def __init__(self):
        self.tenant_name = config.B2C_TENANT_NAME
        self.policy_susi = config.B2C_POLICY_SUSI
        self.client_id = config.B2C_CLIENT_ID
        self.discovery_url = self._get_discovery_url()
        
    def _get_discovery_url(self, policy: str = None) -> str:
        """Get B2C OIDC discovery URL for user flow."""
        policy = policy or self.policy_susi
        return (f"https://{self.tenant_name}.b2clogin.com/"
                f"{self.tenant_name}.onmicrosoft.com/"
                f"{policy}/v2.0/.well-known/openid-configuration")
    
    def validate_token(self, token: str) -> dict:
        """Validate B2C JWT token."""
        # Decode token to get user flow policy
        unverified = jwt.decode(token, options={"verify_signature": False})
        policy = unverified.get("tfp")
        
        # Get JWKS for specific policy
        jwks_client = PyJWKClient(self._get_jwks_uri(policy))
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        
        # Verify token
        decoded = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=self.client_id
        )
        
        return decoded
    
    def extract_roles(self, token_claims: dict) -> list[str]:
        """Extract TRE roles from B2C custom attributes."""
        roles = []
        
        # Extract from custom extension attributes
        workspace_role = token_claims.get("extension_WorkspaceRole")
        if workspace_role:
            roles.append(workspace_role)
            
        tre_role = token_claims.get("extension_TRERole")
        if tre_role:
            roles.append(tre_role)
        
        return roles
    
    def get_user_from_token(self, token_claims: dict) -> User:
        """Extract user information from B2C token claims."""
        # B2C uses 'emails' array instead of 'email' string
        emails = token_claims.get("emails", [])
        email = emails[0] if emails else ""
        
        return User(
            id=token_claims.get("oid"),
            name=token_claims.get("name", ""),
            email=email,
            roles=self.extract_roles(token_claims),
            idp=token_claims.get("idp", "local")  # Track identity provider
        )
```

---

## Configuration Example

### Environment Variables

```bash
# Authentication provider selection
AUTH_TYPE=b2c  # Options: aad, b2c, keycloak

# Azure AD B2C Configuration
B2C_TENANT_NAME=contosob2c
B2C_POLICY_SUSI=B2C_1_susi
B2C_POLICY_PROFILE_EDIT=B2C_1_profile_edit
B2C_POLICY_PASSWORD_RESET=B2C_1_password_reset
B2C_CLIENT_ID=12345678-1234-1234-1234-123456789abc
B2C_CLIENT_SECRET=your-client-secret

# Custom attribute mappings (optional)
B2C_ROLE_CLAIM_NAME=extension_WorkspaceRole
B2C_TRE_ROLE_CLAIM_NAME=extension_TRERole
```

### Factory Selection Logic

```python
def get_credential_provider() -> CredentialProvider:
    """Get credential provider based on configuration."""
    auth_type = os.getenv("AUTH_TYPE", "aad")
    
    if auth_type == "aad":
        from providers.azure.credentials import AzureCredentialProvider
        return AzureCredentialProvider()
    elif auth_type == "b2c":
        from providers.azure.b2c_credentials import AzureADB2CCredentialProvider
        return AzureADB2CCredentialProvider()
    elif auth_type == "keycloak":
        from providers.local.credentials import LocalCredentialProvider
        return LocalCredentialProvider()
    else:
        raise ValueError(f"Invalid AUTH_TYPE: {auth_type}")
```

---

## Testing Requirements

### Unit Tests

- [ ] Token validation with valid B2C token
- [ ] Token validation with expired B2C token
- [ ] Token validation with invalid signature
- [ ] Role extraction from B2C custom attributes
- [ ] User object creation from B2C claims
- [ ] Multiple user flow support (susi, profile_edit, etc.)
- [ ] Social identity provider claim handling

### Integration Tests

- [ ] End-to-end authentication flow with B2C
- [ ] Social login (Microsoft Account, Google)
- [ ] Custom user flow (sign-up with email validation)
- [ ] Profile editing flow
- [ ] Password reset flow
- [ ] API access with B2C token
- [ ] Role-based authorization with B2C roles

### Manual Testing

- [ ] Sign up with email and password
- [ ] Sign in with Microsoft Account
- [ ] Sign in with Google Account
- [ ] Edit user profile
- [ ] Reset password
- [ ] Access API endpoints with B2C token
- [ ] Verify role-based access control

---

## Documentation Requirements

1. **B2C Setup Guide** (`docs/b2c-setup.md`)
   - Create B2C tenant
   - Configure user flows
   - Define custom attributes
   - Register API application
   - Configure identity providers

2. **Configuration Guide** (`docs/b2c-configuration.md`)
   - Environment variable reference
   - User flow policy naming
   - Custom attribute mapping
   - Role configuration

3. **Migration Guide** (`docs/migrate-to-b2c.md`)
   - Migrating from Azure AD Enterprise to B2C
   - User migration strategies
   - Role mapping migration
   - Testing migration

4. **API Documentation** (update existing)
   - Add B2C authentication examples
   - Update token format examples
   - Document B2C-specific claims

---

## Benefits

### For Consumer Applications

- **Social Identity Providers**: Users can sign in with existing accounts (Microsoft, Google, Facebook)
- **Self-Service**: Built-in user flows for sign-up, password reset, profile editing
- **Custom Branding**: B2C UI can be customized to match application branding
- **Scalability**: B2C handles millions of consumer identities

### For Development

- **Separation of Concerns**: Consumer identities separate from enterprise identities
- **Flexible User Flows**: Customize authentication experience without code changes
- **Multi-Tenant**: Support multiple consumer tenant scenarios
- **Provider Pattern**: Leverages existing provider abstraction

---

## Risks & Considerations

### Technical Risks

- **Token Format Differences**: B2C tokens have different structure than Enterprise AD
  - *Mitigation*: Comprehensive unit tests for token parsing
  
- **User Flow Complexity**: Multiple user flows need different handling
  - *Mitigation*: Abstract user flow logic, document clearly

- **Custom Attribute Management**: B2C custom attributes need careful mapping
  - *Mitigation*: Configurable mapping, clear documentation

### Migration Risks

- **User Migration**: Moving from Enterprise AD to B2C requires user migration
  - *Mitigation*: Provide migration guide and scripts

- **Role Mapping**: B2C roles structure different from Enterprise AD
  - *Mitigation*: Role mapping configuration, validation tools

---

## Related Stories

- **Story #128**: Implement local credential provider (completed)
  - Established provider pattern
  - Set precedent for multi-provider support

- **Story #129**: Abstract auth middleware to use provider
  - Creates abstraction layer B2C will use
  - Defines provider interface

- **Future Enhancement**: Social IDP-specific features
  - Track which IDP user authenticated with
  - IDP-specific authorization rules
  - IDP-based analytics

---

## Success Criteria

- [ ] B2C provider passes all unit tests
- [ ] Integration tests with B2C succeed
- [ ] Can authenticate with social identity providers
- [ ] User flows (sign-up, sign-in, profile edit) work end-to-end
- [ ] Roles extracted correctly from B2C custom attributes
- [ ] Documentation complete and validated
- [ ] No regression in existing Azure AD or Keycloak modes
- [ ] Performance meets requirements (token validation < 100ms)

---

## Effort Breakdown

| Task | Estimate |
|------|----------|
| B2C credential provider implementation | 1 day |
| Factory and configuration updates | 0.5 days |
| Token validation and role extraction | 1 day |
| Unit tests | 0.5 days |
| Integration tests | 0.5 days |
| Documentation | 0.5 days |
| **Total** | **4 days** |

---

## Notes

- This story should be implemented **after** Story #129 is complete
- Requires access to Azure AD B2C tenant for testing
- B2C tenant setup time not included in estimate (requires Azure subscription)
- Consider B2C pricing when planning (free tier: 50,000 MAU)

---

**Created**: 2026-05-03  
**Status**: Backlog  
**Blocked By**: Story #129