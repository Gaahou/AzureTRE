# Runtime Branding Solution for Unified GRIP Application
**Version:** 2.0 (Post-Consolidation Strategy)  
**Date:** April 29, 2026  
**Prerequisite:** UI Consolidation completed (single unified app)

---

## Executive Summary

After consolidating the 3 UI apps into 1 unified application, implementing runtime branding becomes **significantly simpler and faster**.

**Current State (Post-Consolidation):**
- Single React application with 3 feature areas (catalog, workspaces, workflows)
- Single build process
- 14+ organizations currently need separate deployments

**Target State (Runtime Branding):**
- Single codebase → 1 build
- 14+ organizations share same deployed instance
- Runtime switches theme based on organization context
- Instant branding updates (no rebuild required)
- New organization onboarding in minutes (not days)

**Timeline:** 6 weeks (vs 12 weeks in original federated architecture)  
**Team:** 1-2 developers  
**Complexity:** 🟢 Low (simplified by consolidation)

---

## Why This Is Simpler Than The Original Proposal

### Original Proposal (Federated Architecture)
```
Complexity sources:
├─ Module Federation remotes to theme individually
├─ Component registry across multiple apps
├─ Remote health checks and failovers
├─ Complex asset loading per remote
├─ Multiple webpack configs to manage
└─ Estimated 12 weeks, high complexity
```

### Simplified Approach (Unified App)
```
What changed:
├─ ❌ No remotes (all code in one app)
├─ ❌ No component registry needed
├─ ❌ No remote health checks
├─ ✅ Simple CSS variable injection
├─ ✅ Single webpack config (already consolidated)
└─ Estimated 6 weeks, low complexity
```

**Removed 70% of the original complexity by consolidating first.**

---

## Part 1: Current State Analysis

### Build-Time Theming (What We're Replacing)

Current pipeline:
```yaml
Build jobs per organization:
├─ BUILD_THEME=actc → dist/actc/
├─ BUILD_THEME=epnd → dist/epnd/
├─ BUILD_THEME=adwb → dist/adwb/
└─ ... 14+ separate builds

Result: 14 artifacts, 14 deployments
Problem: Changes require rebuilding all 14
```

### Where Themes Currently Live

```
ui/libs/shared/theme/src/lib/themes/
├─ actc/
│  ├─ theme.ts (hardcoded logo, colors)
│  ├─ assets/ (logos, images)
│  ├─ footer/footer.tsx (custom component)
│  └─ ...
├─ epnd/
├─ adwb/
├─ emory/
└─ ... (14 total)

src/core/services/keycloak-grip/themes/
└─ Same structure for login screens
```

### Problems With Current Approach

1. **Long Build Times**
   - 14 builds × 10-15 min each = 2-3 hours per release
   - New organization requires full build cycle

2. **Fragile Deployments**
   - 14 places to deploy
   - Easy to miss one
   - Hard to verify all deployed correctly

3. **Limited Scalability**
   - Cannot add organizations quickly
   - Cannot support dynamic customization
   - 25+ organizations practical limit

4. **Cost Inefficiency**
   - 14 separate container instances
   - 14× infrastructure costs
   - 14× monitoring/logging overhead

---

## Part 2: Target Architecture

### Runtime Theme Loading

After consolidation, theme loading is simple:

```typescript
// 1. User lands on app
// 2. App detects organization (from URL, auth token, or query param)
// 3. Load theme at runtime
// 4. Apply to entire app

// src/App.tsx (unified app root)
import { useTheme } from './theme/useTheme';

export function App() {
  const { theme, isLoading } = useTheme();

  if (isLoading) return <LoadingScreen />;

  return (
    <ThemeProvider theme={theme}>
      <KeycloakProvider>
        <BrowserRouter>
          <RootRouter />
        </BrowserRouter>
      </KeycloakProvider>
    </ThemeProvider>
  );
}
```

### System Architecture

```
┌─────────────────────────────────────────────────┐
│      Single Unified GRIP Application            │
│  (Already consolidated from 3 apps)             │
└──────────────┬──────────────────────────────────┘
               │ On startup:
               ├─→ Detect organization
               ├─→ Load theme configuration
               └─→ Apply theme to entire app
                    │
                    ├─→ CSS Variables (colors, fonts)
                    ├─→ Logo/branding assets (from CDN)
                    ├─→ Localization strings
                    └─→ Feature flags per org

┌─────────────────────────────────────┐
│   Theme Configuration Service       │
│   (New API - simple CRUD)           │
├─────────────────────────────────────┤
│ GET  /api/v1/orgs/{orgId}/theme     │
│ PUT  /api/v1/orgs/{orgId}/theme     │
│ POST /api/v1/orgs/{orgId}/assets    │
└─────────────────────────────────────┘
          │
          ├─→ Database (theme configs)
          └─→ Blob Storage (assets)
               └─→ CDN (fast delivery)
```

### No More Build Per Organization

```
BEFORE (Current - 14 builds):
New release:
├─ Trigger 14 separate builds
├─ 2-3 hours of build time
├─ Deploy 14 artifacts
└─ Verify 14 deployments

AFTER (Runtime theming - 1 build):
New release:
├─ Trigger 1 build
├─ 10-15 minutes
├─ Deploy 1 artifact to all orgs
└─ All organizations instantly get new features
   (themes still customize via config)
```

---

## Part 3: Implementation Plan

### Phase 1: Theme Configuration Design (Week 1)

**Task:** Define what aspects of app are themeable

```typescript
// theme.config.ts - NEW
export interface OrganizationTheme {
  // Organization identity
  organizationId: string;
  organizationName: string; // e.g., "EPND", "ACTC"

  // Branding
  branding: {
    // Logos
    logoUrl: string;        // Main logo (CDN URL)
    faviconUrl: string;     // Browser tab icon
    
    // Colors
    primaryColor: string;   // CSS color value
    secondaryColor: string;
    accentColor: string;
    
    // Typography
    fontFamily: string;     // CSS font-family
    fontSize: 'small' | 'medium' | 'large';
  };

  // Content
  content: {
    catalogueName: string;  // "EPND Catalog", etc.
    footerText: string;
    contactEmail: string;
  };

  // Features
  features: {
    enableStatistics: boolean;
    enableSharing: boolean;
    enableWorkflows: boolean;
    customBehaviors: Record<string, any>;
  };

  // Keycloak realm (for login UI)
  keycloakRealm?: string;
}
```

**Deliverable:** Theme schema document  
**Estimate:** 2-3 days

### Phase 2: Backend Theme Service (Week 1-2)

**Task:** Create simple API to store/retrieve themes

```typescript
// Java/C# implementation (pseudocode)

// Theme Controller
@RestController
@RequestMapping("/api/v1/orgs")
public class ThemeController {
  
  @GetMapping("/{orgId}/theme")
  public ResponseEntity<OrganizationTheme> getTheme(
    @PathVariable String orgId
  ) {
    // Fetch from database
    // Cache in Redis (TTL: 5 minutes)
    // Return to frontend
  }

  @PutMapping("/{orgId}/theme")
  public ResponseEntity<OrganizationTheme> updateTheme(
    @PathVariable String orgId,
    @RequestBody OrganizationTheme theme
  ) {
    // Validate theme
    // Update database
    // Invalidate cache
    // Return updated theme
  }

  @PostMapping("/{orgId}/assets")
  public ResponseEntity<String> uploadAsset(
    @PathVariable String orgId,
    @RequestParam MultipartFile file
  ) {
    // Validate file (image type, size limit)
    // Upload to blob storage
    // Return CDN URL
  }
}
```

**Database Schema:**
```sql
CREATE TABLE organization_themes (
  organization_id VARCHAR(255) PRIMARY KEY,
  theme_config JSONB NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_org_themes ON organization_themes(organization_id);
```

**Estimate:** 3-4 days (1 developer)

### Phase 3: Frontend Theme Engine (Week 2-3)

**Task:** Load and apply themes in React app

```typescript
// src/theme/useTheme.ts - NEW
import { useEffect, useState } from 'react';
import { useAuth } from '../auth/useAuth';
import { OrganizationTheme } from './types';

export function useTheme() {
  const { keycloak } = useAuth();
  const [theme, setTheme] = useState<OrganizationTheme | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadTheme = async () => {
      try {
        // Get organization ID from auth token or URL
        const orgId = getOrganizationId(keycloak);
        
        // Fetch theme from API
        const response = await fetch(`/api/v1/orgs/${orgId}/theme`);
        const themeConfig = await response.json();
        
        // Apply theme to document
        applyTheme(themeConfig);
        
        setTheme(themeConfig);
      } catch (error) {
        console.error('Failed to load theme:', error);
        // Fall back to default theme
      } finally {
        setIsLoading(false);
      }
    };

    if (keycloak?.token) {
      loadTheme();
    }
  }, [keycloak?.token]);

  return { theme, isLoading };
}

// Apply theme colors/fonts to document
function applyTheme(theme: OrganizationTheme) {
  const root = document.documentElement;
  
  // Set CSS custom properties (CSS variables)
  root.style.setProperty('--primary-color', theme.branding.primaryColor);
  root.style.setProperty('--secondary-color', theme.branding.secondaryColor);
  root.style.setProperty('--accent-color', theme.branding.accentColor);
  root.style.setProperty('--font-family', theme.branding.fontFamily);
  
  // Update favicon
  updateFavicon(theme.branding.faviconUrl);
  
  // Update page title
  document.title = `${theme.branding.catalogueName} - GRIP`;
  
  // Store in localStorage for quick access
  localStorage.setItem('currentTheme', JSON.stringify(theme));
}

// To detect organization:
function getOrganizationId(keycloak: Keycloak): string {
  // Option 1: From URL query param
  const params = new URLSearchParams(window.location.search);
  if (params.has('org')) return params.get('org')!;
  
  // Option 2: From auth token (if org is in token claims)
  if (keycloak?.tokenParsed?.organization) {
    return keycloak.tokenParsed.organization;
  }
  
  // Option 3: From URL path
  const path = window.location.href;
  if (path.includes('/epnd')) return 'epnd';
  if (path.includes('/actc')) return 'actc';
  
  // Default
  return 'grip'; // default theme
}
```

**CSS Setup:**
```css
/* src/index.css */
:root {
  /* Default theme (applied before runtime theme loads) */
  --primary-color: #0066cc;
  --secondary-color: #f0f0f0;
  --accent-color: #ff6600;
  --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto;
}

/* Components use CSS variables */
body {
  font-family: var(--font-family);
}

.button-primary {
  background-color: var(--primary-color);
  color: white;
}

.header {
  background-color: var(--secondary-color);
  border-bottom: 2px solid var(--primary-color);
}

/* Logo changes dynamically */
.logo {
  background-image: var(--logo-url);
}
```

**Estimate:** 4-5 days (1-2 developers)

### Phase 4: Migrate Existing Themes (Week 3-4)

**Task:** Convert 14 build-time themes → runtime configs

**Process:**
```typescript
// For each existing theme (actc, epnd, adwb, etc.)

// 1. Read current build-time theme
import { ACTCTheme } from './themes/actc/theme';

// 2. Extract values
const themeConfig: OrganizationTheme = {
  organizationId: 'actc',
  organizationName: ACTCTheme.catalogue,
  branding: {
    logoUrl: uploadLogoToCDN(ACTCTheme.logoUrl),
    faviconUrl: uploadFaviconToCDN(ACTCTheme.faviconUrl),
    primaryColor: ACTCTheme.colors.primary,
    secondaryColor: ACTCTheme.colors.secondary,
    accentColor: ACTCTheme.colors.accent,
    fontFamily: ACTCTheme.typography.fontFamily,
  },
  content: {
    catalogueName: ACTCTheme.catalogue,
    footerText: ACTCTheme.footer?.text || '',
    contactEmail: ACTCTheme.contactEmail,
  },
  features: {
    enableStatistics: !ACTCTheme.hideStatistics,
    enableSharing: true,
    enableWorkflows: true,
  },
};

// 3. Store in database via API
await fetch('/api/v1/orgs/actc/theme', {
  method: 'PUT',
  body: JSON.stringify(themeConfig),
});

// 4. Upload assets to CDN
// - Logos
// - Images
// - Custom fonts
```

**Migration checklist:**
```
For each of 14 themes:
├─ Extract logo URLs
├─ Extract color palette
├─ Extract typography settings
├─ Extract footer content
├─ Upload logos to blob storage/CDN
├─ Create theme config JSON
├─ Store in database
└─ Verify it loads in app
```

**Estimate:** 4-5 days (1-2 developers)

### Phase 5: Keycloak Login Theme (Week 4)

**Task:** Apply branding to Keycloak login screens

**Current State:**
```
src/core/services/keycloak-grip/themes/
├─ actc/ (login theme)
├─ epnd/
└─ ... (per-org Keycloak themes)
```

**New Approach:**
```
Option A: Dynamic Keycloak Theme (if supported)
├─ Single base Keycloak theme
├─ Load org-specific CSS at runtime
├─ Update theme config in Keycloak database

Option B: Keep Per-Theme Keycloak Themes
├─ Still deploy per-organization theme
├─ But single app theme (no more app-level per-org builds)
└─ This is acceptable (Keycloak has separate deployment)

Option C: Hybrid (Recommended)
├─ Keycloak URL routing by org
├─ https://keycloak.epnd.example.com (EPND realm)
├─ https://keycloak.actc.example.com (ACTC realm)
└─ Each has its own Keycloak instance (separate from app theming)
```

**Estimate:** 2-3 days (1 developer)

### Phase 6: Testing & Validation (Week 5)

**Task:** Test all 14 organizations with new runtime theming

**Test Cases:**
```
For each organization (actc, epnd, adwb, emory, mjff, etc.):
├─ Logo displays correctly
├─ Colors match expected palette
├─ Typography renders correctly
├─ Footer content appears
├─ Navigation works
├─ Workspace features work
├─ Workflow features work
└─ Telemetry tracks correctly (includes org_id)

Test environments:
├─ Local dev (manual test)
├─ Staging (automated tests)
└─ Production (canary deployment - 10% of users)
```

**Automated Tests:**
```typescript
describe('Organization Themes', () => {
  const organizations = ['actc', 'epnd', 'adwb', 'emory', 'mjff' /*, ... */];

  organizations.forEach((orgId) => {
    test(`Theme loads correctly for ${orgId}`, async () => {
      // Load app with org context
      render(<App orgId={orgId} />);
      
      // Wait for theme to load
      await waitFor(() => {
        expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
      });
      
      // Verify theme applied
      const primaryColor = getComputedStyle(document.documentElement)
        .getPropertyValue('--primary-color');
      expect(primaryColor).toBeTruthy();
      
      // Verify logo loaded
      const logo = screen.getByAltText('Organization Logo');
      expect(logo).toBeInTheDocument();
    });
  });
});
```

**Estimate:** 3-4 days (1 developer)

### Phase 7: Documentation & Training (Week 5-6)

**Task:** Document how to manage themes going forward

**Create:**
```
├─ Admin Portal Guide
│  └─ How to update organization branding
├─ Developer Guide
│  └─ How to add a new organization
├─ API Documentation
│  └─ Theme configuration endpoints
├─ Troubleshooting Guide
│  └─ Common issues & fixes
└─ Deployment Guide
   └─ How to deploy updates
```

**Admin Portal (for customer self-service):**
```
Example workflow:
1. Admin logs in
2. Navigates to "Organization Settings"
3. Updates:
   ├─ Organization name
   ├─ Primary color (color picker)
   ├─ Logo (upload new image)
   ├─ Footer text
   └─ Feature toggles
4. Clicks "Save"
5. Updates appear instantly in app (no rebuild needed!)
```

**Estimate:** 2-3 days (1 developer + technical writer)

**Phase Total:** 6 weeks

---

## Part 4: Deployment Strategy

### Blue-Green Deployment

```
Step 1: Prepare New Deployment
├─ Build unified app with runtime theming
├─ Run all tests
└─ Create Blue deployment

Step 2: Validate Blue
├─ Deploy to staging "Blue"
├─ Run acceptance tests on all 14 orgs
├─ Performance testing
├─ Smoke tests

Step 3: Switch Traffic
├─ Currently running: Green (old build-per-org system)
├─ Switch: Blue (new runtime theming)
├─ Monitor metrics closely (errors, latency, hits)

Step 4: Verify & Commit
├─ All 14 organizations working as expected
├─ Telemetry showing correct org_id
├─ No error rate spike
└─ Keep Green as rollback
```

### Rollback Plan

If issues occur:
```
Immediate Rollback:
├─ Route traffic back to Green (old system)
├─ Takes <5 minutes
├─ Zero data loss

Post-Mortem:
├─ Identify root cause
├─ Fix in development
├─ Re-test thoroughly
└─ Try again
```

---

## Part 5: Benefits After Implementation

### Operational Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|------------|
| Build time per release | 2-3 hours | 15 minutes | **88% faster** |
| New org setup | 3-5 days | <1 hour | **95% faster** |
| Hotfix deployment | 2-3 hours | 20 minutes | **90% faster** |
| Branding update | Requires rebuild | Real-time | **Instant** |

### Infrastructure Efficiency

| Resource | Before | After | Improvement |
|----------|--------|-------|------------|
| Container instances | 14+ separate | 1 shared | **93% reduction** |
| Storage | 14× duplicated | Shared | **Eliminates duplication** |
| CDN configs | 14 separate | 1 unified | **Simplified** |
| Monitoring | 14 systems | 1 system | **Single pane of glass** |

### Developer Experience

| Task | Before | After |
|------|--------|-------|
| Deploy new feature | Build all 14 → Deploy 14 | Build 1 → Deploy 1 |
| Update branding | Code change → Rebuild → Deploy | Admin portal → Instant |
| Add new org | Create theme folder → Add CI job → Manual steps | API call → Done |
| Debug issues | Check 14 deployments | Check 1 deployment |

### Business Benefits

- ✅ **Faster go-to-market** for new organizations
- ✅ **Lower infrastructure costs** (consolidated instance)
- ✅ **Better customer experience** (instant branding updates)
- ✅ **Easier support** (single version to maintain)
- ✅ **Foundation for SaaS scaling** (multi-tenant ready)

---

## Part 6: Risk Mitigation

### Risk 1: Theme Configuration Issues
**Risk:** Theme config corrupted or missing during migration  
**Mitigation:**
- [ ] Validate all 14 themes migrate correctly
- [ ] Test each theme in isolation before go-live
- [ ] Fallback to default theme if config missing
- [ ] Backup of old build-time themes kept

### Risk 2: Performance Degradation
**Risk:** Loading theme at runtime adds latency  
**Mitigation:**
- [ ] Cache theme in localStorage (persist across sessions)
- [ ] Cache in Redis on backend (5-minute TTL)
- [ ] Pre-fetch theme before rendering app
- [ ] Monitor page load performance metrics

### Risk 3: CDN Asset Delivery
**Risk:** Logo images fail to load from CDN  
**Mitigation:**
- [ ] Fallback to default placeholder if asset fails
- [ ] Use multiple CDN endpoints (geographic redundancy)
- [ ] Set reasonable timeout (fall back if >3s)
- [ ] Monitor CDN health

### Risk 4: Org Detection Issues
**Risk:** Organization context not detected correctly  
**Mitigation:**
- [ ] Multiple org detection methods (URL, token, query param)
- [ ] Default to safe fallback org if detection fails
- [ ] Log org_id in telemetry for auditing
- [ ] Test each org routing path thoroughly

### Risk 5: Auth Token Issues (Iframe Removed)
**Risk:** Token no longer passes through iframe boundaries  
**Mitigation:**
- [ ] Auth context now shared directly (simpler than before)
- [ ] No cross-origin token passing needed
- [ ] Consolidation already solved this problem
- [ ] Test auth against all keycloak realms

---

## Part 7: Success Criteria

### Functional ✅
- [ ] Single build works for all 14 organizations
- [ ] Each org displays correct branding
- [ ] All features work across all orgs
- [ ] Theme can be updated without rebuild
- [ ] New org can be added in <1 hour

### Performance ✅
- [ ] App loads in <3 seconds (with theme)
- [ ] Theme switch between orgs: <500ms
- [ ] No performance regression vs. old system
- [ ] Bundle size increase <10%

### Operational ✅
- [ ] Single CI/CD pipeline (no more 14 builds)
- [ ] Single deployment process
- [ ] Rollback capability <5 minutes
- [ ] Admin portal for theme management

### Quality ✅
- [ ] All 14 existing themes migrated correctly
- [ ] Zero visual regressions
- [ ] All features tested on all orgs
- [ ] Accessibility audit passes

---

## Comparison: Original vs. Simplified Approach

### Original Approach (With Federation)
```
Complexity:
├─ Component registry across remotes
├─ Theme engine for each remote
├─ Federation health checks
├─ Complex asset management
├─ Module federation refactoring
└─ Estimated: 12 weeks, high risk

Architecture:
├─ Shell app + 2 remotes
├─ Theme applied per-remote
├─ Federation config per theme
└─ Complex deployment
```

### Simplified Approach (Post-Consolidation)
```
Simplicity:
├─ Load theme JSON from API
├─ Inject CSS variables
├─ Apply to entire app
├─ No federation complexity
└─ Estimated: 6 weeks, low risk

Architecture:
├─ Single unified app
├─ Theme applied to root
├─ Simple API endpoints
└─ Single deployment
```

**Difference: 6 weeks faster, 70% less complexity, better results**

---

## Implementation Checklist

### Phase 1: Design
- [ ] Theme schema finalized
- [ ] Architecture reviewed with tech lead
- [ ] Database schema approved
- [ ] API endpoints documented

### Phase 2: Backend
- [ ] Theme API endpoints created
- [ ] Database tables created
- [ ] Theme service tested
- [ ] Asset upload working

### Phase 3: Frontend
- [ ] useTheme hook implemented
- [ ] CSS variables configured
- [ ] Theme applied on app startup
- [ ] Fallback theme working

### Phase 4: Migration
- [ ] All 14 themes extracted to JSON
- [ ] All logos uploaded to CDN
- [ ] All configs stored in database
- [ ] Each theme tested in app

### Phase 5: Keycloak
- [ ] Keycloak realm theming (decision made)
- [ ] Login pages branded correctly
- [ ] Theme sync between app and Keycloak

### Phase 6: Testing
- [ ] Unit tests passing
- [ ] All 14 orgs tested
- [ ] Performance benchmarks met
- [ ] Security review passed

### Phase 7: Documentation
- [ ] Admin guide written
- [ ] Developer guide written
- [ ] API docs complete
- [ ] Troubleshooting guide done

### Deployment
- [ ] Blue environment prepared
- [ ] Tests passing on Blue
- [ ] Traffic switched to Blue
- [ ] Metrics monitored
- [ ] Team trained on new process

---

## FAQ

**Q: Will we still build per-organization for theming?**
A: No. Single build for all orgs. Theme is applied at runtime based on organization context.

**Q: How do we detect which organization the user is for?**
A: Multiple methods: URL parameter, token claim, URL path. Falls back gracefully.

**Q: What if a theme config is missing?**
A: Fallback to default "GRIP" theme. Can update config without rebuild.

**Q: How fast is theme switching between organizations?**
A: <500ms (loads from cache if available, or API if not).

**Q: Can customers update their own branding?**
A: Yes! Admin portal allows self-service theme updates (future phase, not in this implementation).

**Q: Is this true multi-tenancy?**
A: In terms of branding/UI customization: Yes. In terms of data: Depends on your data model. This solution is for UI multi-tenancy.

**Q: What about Keycloak realms?**
A: That's separate. Can stay per-organization or be consolidated (separate decision).

**Q: How do we handle white-labeling?**
A: This solution enables it. Customer branding can be fully customized per organization.

---

## Next Steps

1. **Before Implementation:**
   - [ ] Review architecture with tech lead
   - [ ] Get approval from Neptali/Andrew
   - [ ] Confirm timeline with team

2. **During UI Consolidation (Weeks 1-16):**
   - [ ] Prepare theme migration scripts
   - [ ] Design admin portal (future phase)
   - [ ] Set up CDN for asset storage

3. **After Consolidation (Weeks 17-22):**
   - [ ] Implement phases 1-7 of branding solution
   - [ ] Deploy to staging first
   - [ ] Monitor carefully on production

4. **Post-Launch:**
   - [ ] Train team on new theme management
   - [ ] Gather feedback from organizations
   - [ ] Plan Phase 2 (admin self-service portal)

---

## Appendix: File Structure After Implementation

```
ui/apps/shell/
├─ src/
│  ├─ theme/                    # NEW: Theme management
│  │  ├─ useTheme.ts           # Hook to load theme
│  │  ├─ applyTheme.ts         # Apply theme to DOM
│  │  ├─ types.ts              # Theme types
│  │  └─ defaultTheme.ts       # Fallback theme
│  │
│  ├─ features/                # Already consolidated
│  │  ├─ catalog/
│  │  ├─ workspaces/
│  │  └─ workflows/
│  │
│  ├─ shared/
│  ├─ router/
│  ├─ auth/
│  ├─ App.tsx                  # Root (applies theme)
│  └─ main.tsx
│
├─ public/
│  └─ default-logo.svg         # Fallback if CDN fails
│
├─ webpack.config.ts           # Simplified (no federation)
├─ package.json                # Single app dependencies
└─ tsconfig.json

Database:
├─ organization_themes (stores all 14 orgs' configs)
└─ assets (references to CDN URLs)

CDN:
/orgs/
├─ actc/
│  ├─ logo.svg
│  └─ favicon.ico
├─ epnd/
│  ├─ logo.svg
│  └─ favicon.ico
└─ ... (14 total)
```

---

## Conclusion

By consolidating the UI first, the branding solution **becomes dramatically simpler**:

- ✅ **6 weeks instead of 12** (50% faster)
- ✅ **1 app instead of 3+** (no federation complexity)
- ✅ **1 build instead of 14** (88% faster builds)
- ✅ **Single deployment** (simpler operations)
- ✅ **Instant branding updates** (no rebuild needed)
- ✅ **True multi-tenant ready** (scales to 100+ orgs)

This is the **recommended implementation sequence** for GRIP's evolution to a true SaaS platform.

