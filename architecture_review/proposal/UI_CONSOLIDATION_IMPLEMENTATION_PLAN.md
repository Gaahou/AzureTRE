# UI Consolidation Implementation Plan
**Project:** Consolidate Catalog, Workspaces, and Workflows into a Single GRIP UI Application  
**Date:** April 29, 2026  
**Status:** Pre-Implementation Planning (Updated for Multi-Repo Architecture)

---

## Executive Summary

**Current State (REVISED):**
- **3 separate repositories:**
  - Catalog repo (c:\Catalog) → Contains Catalog UI + Workflows (embedded)
  - Workspaces_UI repo (separate) → Contains Workspaces app
- **3 separate React applications** with independent builds:
  - Catalog: React app (webpack/Nx)
  - Workspaces: React app (CRA with craco)
  - Workflows: Embedded in Catalog (React component in iframe)
- **3 separate Keycloak bootstraps** (separate auth contexts)
- **3 separate Redux stores** (no shared state)
- **3 separate API configurations** (different endpoints)
- **2 separate CI/CD pipelines** (Catalog pipeline + Workspaces pipeline)
- **Complex local development:** Requires running 2 separate things (Catalog + Workspaces_UI)

**Target State:**
- 1 unified React application (or monorepo structure)
- Single build pipeline
- Single react-router instance
- Unified authentication (single Keycloak bootstrap)
- Unified Redux store (shared state)
- Single API client configuration
- End-to-end telemetry tracing
- Simple `pnpm start` (single development setup)

**Estimated Timeline:** 20 weeks with parallel workspaces feature development (22-24 weeks with contingency)  
**Team Size:** 4-5 developers total (2-3 consolidation + 1-2 workspaces features + 0.5 merge manager)  
**Risk Level:** 🟠 Moderate (multi-repo consolidation + build system migration + concurrent development)

---

## Parallel Development Strategy

### Current Challenge: Active Feature Development During Consolidation

**Reality Check:**
- Consolidation timeline: 20-24 weeks
- Workspaces team: Actively developing vendor features during this period
- Problem: Without coordination, features added to Workspaces_UI repo won't be in consolidated codebase
- Result: Lost features, duplicate work, merge conflicts, vendor dissatisfaction

### Solution: Two Parallel Work Streams with Weekly Synchronization

#### **Stream 1: Consolidation Team (2-3 developers)**
```
Timeline: Week 1-20
├─ Week 1-2: Phase 0 analysis
├─ Week 3-6: CRA→Nx migration (Phase 1)
├─ Week 7-20: Feature consolidation, testing, deployment (Phase 2-5)
└─ Responsibility: Build unified app infrastructure
```

#### **Stream 2: Workspaces Feature Team (existing 1-2 developers)**
```
Timeline: Week 1-20+ (continuous)
├─ Week 1-20: Continue normal feature development for vendors
├─ Branch: features/* (separate development branches)
└─ Responsibility: Add vendor features while consolidation proceeds
```

### Git & Branch Strategy

**Repository Setup:**
```
Workspaces_UI repo (original):
├─ main (frozen after Phase 1, used as reference)
├─ features/vendor-a-2026-q2 (current development)
├─ features/vendor-b-2026-q2 (current development)
└─ features/vendor-c-2026-q2 (current development)

Catalog repo (consolidation target):
├─ main (stable, production)
└─ feature/ui-consolidation (long-running consolidation branch)
   ├─ Week 1-2: Phase 0 analysis
   ├─ Week 3-6: CRA→Nx migration
   ├─ Week 7-20: Feature consolidation
   ├─ WEEKLY: Merge latest Workspaces_UI features/* into this branch
   └─ Week 21: Fast-forward merge to main (big cutover)

AFTER Consolidation Complete (Week 21+):
├─ Workspaces_UI repo: ARCHIVED (reference only, no new work)
├─ Catalog/ui/apps/workspaces: NEW home for all workspaces development
└─ All feature work now happens in Catalog repo
```

### Weekly Synchronization Protocol

**Thursday Sync Meeting (30 minutes):**

```
Participants: 1 dev from consolidation team + 1 dev from workspaces team

1. Consolidation team pulls latest workspaces features
   git pull origin features/vendor-*

2. Cherry-pick or merge new features into consolidation branch
   git cherry-pick <commit> or git merge --no-ff features/vendor-a-2026-q2

3. Run tests on consolidated codebase
   pnpm test
   nx run-many --target=test

4. Identify conflicts
   - TypeScript import mismatches?
   - Component name collisions?
   - Redux state conflicts?
   - Route path conflicts?

5. Resolve conflicts immediately or schedule deeper dive
   - Simple: Fix and commit
   - Complex: Schedule 1 hour follow-up with both teams

6. Document sync results
   - Features merged: ✓
   - Conflicts found: [list]
   - Blockers: [list]
   - Next week's focus: [areas at risk]
```

**Daily Automated Checks (CI Job):**
```yaml
# Daily at 6am, auto-test compatibility
schedule:
  - cron: '0 6 * * *'
  
steps:
  - name: Fetch latest Workspaces features
    run: git fetch origin features/*
    
  - name: Merge to consolidation branch (dry-run)
    run: git merge --no-commit --no-ff features/vendor-a-2026-q2
    
  - name: Run full test suite
    run: pnpm test
    
  - name: Report conflicts to Slack
    if: failure()
    run: |
      echo "⚠️ Consolidation branch conflicts detected"
      "Check the details: [CI link]"
```

### Vendor Feature Management: Two Options

#### **Option A: Allow New Features (Recommended for Multi-Vendor)**

**What happens:**
- Workspaces team adds features normally
- Features are merged into consolidation branch weekly
- Features available to vendors on staggered schedule:
  ```
  Week 8:  Vendor A gets features + Phase 1 (CRA→Nx) consolidated
  Week 15: Vendor B gets features + Phase 1-3 consolidated
  Week 22: Vendor C gets all features + fully consolidated app
  ```

**Requirements:**
- Consolidation team must keep pace with feature merges
- All features must pass tests in consolidated context
- Workspaces team must fix any consolidation-breaking changes immediately

**Timeline Impact:** Same (20-24 weeks), but with feature delivery momentum

**Risk:** HIGH - Complex merge management, potential feature loss

---

#### **Option B: Feature Freeze (Safest but Expensive)**

**What happens:**
- Workspaces team: Bug fixes and support only (no new features)
- Freeze period: Week 1-20
- Resume development: Week 21 (in consolidated codebase)

**Requirements:**
- Strict feature freeze enforcement
- Vendor communication: "No new features during consolidation"
- Workspaces team retrained on consolidated codebase before resuming

**Timeline impact:** Slightly faster (18-19 weeks possible), but 2-3 months of lost feature velocity

**Risk:** LOW - Clean consolidation, but vendor dissatisfaction

---

**RECOMMENDATION:** Start with **Option A (Allow Features)** because:
- Vendors continue getting features (happy customers)
- Workspaces team stays productive
- Could merge to Option B mid-consolidation if conflicts become unmanageable

### Risk Mitigation: Managing Concurrent Development

**Risk 1: Feature Gets Lost in Consolidation**
```
Symptom: Feature works in Workspaces_UI but missing in consolidated app
Cause: Merge conflict resolved incorrectly, or file wasn't migrated

Mitigation:
- [ ] Feature inventory document (list of every feature added in week 1-20)
- [ ] Weekly checklist: "All features in list appear in consolidated build?"
- [ ] Test in both places: Verify feature works in Workspaces_UI AND consolidated
- [ ] Designated "feature shepherd" to track compliance
```

**Risk 2: Merge Conflicts Explode**
```
Estimate: Workspaces team adds ~20 features × 10 files/feature = 200 files
          Consolidation refactors ~100 files
          Overlap: ~15-20 files with conflicts per feature
          Total conflicts: 300-400 over 20 weeks (15-20 per week)

Mitigation:
- [ ] Automated conflict detection (daily CI job reports conflicts)
- [ ] Git hooks to prevent conflicting imports/route definitions
- [ ] Dedicated merge manager (1 senior dev, 20% time)
- [ ] Cherry-pick strategy (small, daily merges vs big weekly merges)
- [ ] Clear file ownership (Workspaces team owns src/modules/*, consolidation owns imports)
```

**Risk 3: Workspaces Team Breaks Consolidation Build**
```
Scenario: Workspaces team adds feature that breaks consolidation tests

Mitigation:
- [ ] Consolidation branch must always be buildable
- [ ] If feature breaks build, Workspaces team fixes it within 1 day
- [ ] Blocking issue: If not fixed, feature branch reverted from merge
- [ ] Clear SLA: "If you break the consolidation build, you fix it in 4 hours"
```

**Risk 4: Duplicate Work (Feature Coded Twice)**
```
Scenario: Both teams implement same feature independently

Mitigation:
- [ ] Weekly sync discusses upcoming vendor requests
- [ ] "No surprises" rule: Features discussed before coding starts
- [ ] Consolidation team gets advance notice of planned features
- [ ] If overlap detected mid-week, immediate deep-dive to resolve
```

### Communication & Discipline Requirements

**Team Rules During Consolidation:**

```
FOR WORKSPACES TEAM:
✓ Do: Add vendor features on feature branches
✓ Do: Notify consolidation team of new branches
✓ Do: Participate in weekly sync
✓ Do: Have feature ready for merge at determined cutoff day (e.g., Tuesday)
✗ Don't: Commit directly to main (consolidation team needs clean history)
✗ Don't: Make breaking changes to API contracts
✗ Don't: Refactor existing code (only add new features)

FOR CONSOLIDATION TEAM:
✓ Do: Merge workspaces features weekly
✓ Do: Run full test suite after each merge
✓ Do: Immediately report merge issues to workspaces team
✓ Do: Keep consolidation branch ahead of main (has latest features)
✗ Don't: Leave major conflicts unresolved
✗ Don't: Remove or modify workspaces code without discussing

FOR BOTH TEAMS:
✓ Do: Communicate synchronously in Slack #consolidation channel
✓ Do: Document decisions in shared document
✓ Do: Escalate blockers immediately (don't wait for Thursday sync)
✓ Do: Have quick "conflict resolution" meeting slots available (2 per week)
```

### Updated Team Allocation

**Total Team: 4-5 developers**

```
Consolidation Stream:
├─ Lead Dev (1, with Nx/webpack expertise)
├─ Mid-level Dev (1, general frontend)
├─ Merge Manager (0.5, dedicated conflict resolution)
└─ Tech Lead (0.2, guidance & architecture decisions)

Workspaces Feature Stream:
├─ Senior Dev (1, feature owner)
└─ Mid-level Dev (1, implementation)
   
Total sustained effort: 3.7 FTE over 20 weeks
Budget: ~3.7 × 20 = 74 developer-weeks
```

### Timeline with Parallel Development

| Week | Consolidation Team | Workspaces Team | Sync Activity |
|------|---|---|---|
| 1-2 | Phase 0 analysis | Vendor work continues | Gather feature list |
| 3-6 | Phase 1 CRA→Nx | Vendor: Features A, B, C | Weekly merges |
| 7-10 | Phase 2 workflows | Vendor: Features D, E, F | Weekly merges + conflicts |
| 11-14 | Phase 2 workspaces | Vendor: Features G, H, I | Weekly merges |
| 15-16 | Phase 3 build system | Vendor: Features J, K | Weekly merges |
| 17-19 | Phase 4 testing | Vendor: Bug fixes | Smaller merges |
| 20 | Phase 5 deploy | Workspaces team tests | Final validation |
| 21+ | Production support | Development in consolidated repo | Unified workflow |

**Key: All weekly merges and syncs happen even during testing/deployment phases.**

### Decision Point: Make Now

**Before starting, choose:**
- [ ] **Option A (Allow Features)**: Features continue flowing, weekly merge overhead
- [ ] **Option B (Freeze)**: No new features, faster consolidation, vendor pushback

**If choosing Option A, also decide:**
- Staggered vendor rollout (Wave 1, 2, 3)? or all at once on Week 21?
- Who is the "merge manager"? (must have strong Git + conflict resolution skills)
- What's the escalation path for merge conflicts? (Who makes final call?)

---

## CRITICAL DISCOVERY: Multi-Repository Architecture

### Repository Structure Overview

```
Project GRIP Repositories:
├─ Catalog (main, where you are now)
│  ├─ ui/apps/shell/          (Catalog app - React/Nx/Webpack)
│  ├─ ui/apps/workflows/      (Workflows app - embedded in Catalog)
│  ├─ ui/libs/shared/         (Shared components/theme)
│  ├─ backend/ (services)
│  ├─ tools/ci/ (CI/CD)
│  └─ BUILD_THEME per org → 14 separate builds
│
├─ Workspaces_UI (SEPARATE REPO)
│  ├─ src/
│  │  ├─ modules/             (Feature modules)
│  │  ├─ routes/              (React Router routes)
│  │  ├─ redux/               (Redux store - SEPARATE from Catalog)
│  │  ├─ keycloak-config.js   (SEPARATE Keycloak bootstrap)
│  │  └─ ...
│  ├─ package.json            (CRA + craco, NOT Nx)
│  ├─ webpack config          (Different from Catalog)
│  └─ Multiple CI/CD files    (cd_pipeline.yaml, cicd-pipeline.yaml, ci_pipeline.yaml)
│
└─ Other repos (backend services, not UI)
   ├─ Workspaces-Core
   ├─ Workspaces-Automation
   ├─ Catalog-AMS
   └─ etc.
```

### Key Findings from Workspaces_UI Analysis

**Build System:**
- Catalog uses: **Nx workspace + webpack**
- Workspaces_UI uses: **Create React App (CRA) + craco** (different tool entirely!)
- These are incompatible build systems

**Dependencies:**
- Catalog: typescript, @nx/*, webpack
- Workspaces_UI: react-scripts, craco (no Nx)
- Will need to reconcile or rewrite Workspaces_UI build

**React Router:**
- Catalog: v6.15.0 (or similar)
- Workspaces_UI: v6.28.0 (newer version)
- Minor version difference = potential breaking changes

**Keycloak:**
- Catalog: Bootstrap in shell app
- Workspaces_UI: Separate bootstrap in ModuleFedarateApp.tsx
- Two independent Keycloak instances = token issues

**State Management:**
- Catalog: Redux (or other)
- Workspaces_UI: Redux with separate store
- Two Redux stores = state sync issues

**Routing:**
- Catalog: Catalog routes
- Workspaces_UI: "/workspace/*" routes under separate Router
- Need unified routing hierarchy

**CI/CD:**
- Catalog: tools/ci/jobs/build_deliverables.yml
- Workspaces_UI: cd_pipeline.yaml, cicd-pipeline.yaml, ci_pipeline.yaml
- Need single unified pipeline

---

## Phase 0: Pre-Implementation (Week 1-2)

### Objective
Gather complete understanding of current architecture and create detailed consolidation roadmap.

### 0.1: Codebase Analysis (Including Workspaces_UI)

**Task:** Document the current state of BOTH repos in detail

```
Analysis Checklist:

CATALOG REPO:
├─ Catalog App Analysis
│  ├─ Entry point: ui/apps/shell/src/bootstrap.tsx
│  ├─ Build system: Nx workspace + webpack
│  ├─ Routes: Map all route definitions
│  ├─ State: Redux, Context API, Zustand?
│  ├─ React-router version: (e.g., v6.15.0)
│  ├─ Keycloak Bootstrap: Where? How?
│  ├─ Components: Shared vs app-specific
│  ├─ Dependencies: package.json analysis
│  └─ Telemetry setup: Application Insights configuration
│
├─ Workflows App Analysis
│  ├─ Location: Embedded in iframe in Catalog?
│  ├─ Entry point: Where?
│  ├─ Routes: All workflows routes
│  ├─ How does iframe ↔ parent communicate?
│  ├─ How auth tokens passed to iframe?
│  └─ Dependencies: versions vs Catalog
│
├─ Shared Libraries Analysis  
│  ├─ Location: ui/libs/shared/theme/
│  ├─ Other shared libs: ui/libs/shared/components?
│  ├─ What's currently shared?
│  └─ How are they imported/versioned?
│
└─ Current Build System
   ├─ Nx configuration: ui/nx.json
   ├─ Webpack config: Multiple files
   ├─ CI/CD: tools/ci/jobs/build_deliverables.yml
   ├─ Theme build process: How are 14 themes built?
   └─ Environment configs: Per environment?

WORKSPACES_UI REPO (SEPARATE):
├─ Workspaces App Analysis
│  ├─ Entry point: src/ModuleFedarateApp.tsx
│  ├─ Build system: Create React App (CRA) + craco (NOT Nx!)
│  ├─ Routes: src/routes/AppRoutes.tsx
│  ├─ State management: src/redux/Store.ts
│  │  ├─ Redux slices: What slices exist?
│  │  ├─ Does it share Redux with Catalog? (Probably NOT)
│  │  └─ What state is critical?
│  ├─ React-router version: Currently v6.28.0
│  ├─ Keycloak: src/keycloak-config.js (SEPARATE bootstrap!)
│  ├─ API endpoints: src/endpoints.js (separate config)
│  ├─ Dependencies: package.json (CRA dependencies, not Nx)
│  ├─ Modules: src/modules/ (feature modules)
│  ├─ Telemetry: src/telemetry/ (separate telemetry setup?)
│  └─ Webpack config: craco.config.js (if exists)
│
├─ Build System Analysis
│  ├─ Does it have Module Federation config? (Yes, ModuleFedarateApp)
│  ├─ Package.json scripts: start, build, test
│  ├─ Build output location: build/ folder
│  ├─ Docker config: Dockerfile present (separate deployment!)
│  ├─ Nginx config: nginx.conf (separate web server config)
│  └─ Environment setup: How are env vars configured?
│
├─ CI/CD Analysis
│  ├─ Pipeline files: cd_pipeline.yaml, cicd-pipeline.yaml, ci_pipeline.yaml
│  ├─ Which one is active?
│  ├─ Where does it deploy to?
│  └─ How does it relate to Catalog pipeline?
│
└─ Dependencies Analysis
   ├─ CRA-specific: react-scripts v5.0.1
   ├─ Build tool: craco (CRA customization)
   ├─ React version: 18.3.1 (matches Catalog ✓)
   ├─ React-router version: v6.28.0 (DIFFERS from Catalog v6.15?)
   ├─ Redux: @reduxjs/toolkit, react-redux
   ├─ Other key libs: Keycloak, axios, Application Insights
   └─ Compare versions with Catalog package.json

INTEGRATION ANALYSIS:
├─ How does Catalog load Workspaces_UI currently?
│  ├─ Via Module Federation? How configured?
│  └─ What's the remoteEntry URL?
├─ Do they share ANY code/dependencies?
│  └─ Probably NOT (completely separate repos)
├─ Auth token sharing: How does it happen?
│  ├─ Is it via postMessage (federation)?
│  ├─ Or separate auth per app?
│  └─ This is critical for understanding integration
└─ Telemetry: Are both sending to same Application Insights instance?
```

**Output:** Multi-Repo Analysis Document

### 0.2: Consolidation Architecture Decision

**Critical Question:** How should we consolidate 2 repos with different build systems?

**Option A: Move Workspaces_UI INTO Catalog Repo (RECOMMENDED)**
```
Result:
Catalog/
├─ ui/
│  ├─ apps/shell/        (Catalog)
│  ├─ apps/workspaces/   (MOVED from Workspaces_UI repo)
│  ├─ apps/workflows/    (already here)
│  ├─ libs/shared/
│  └─ nx.json            (unified Nx workspace)

Benefits:
✅ Single repository
✅ Single Nx workspace
✅ Single build system
✅ Shared code naturally lives in ui/libs/

Challenges:
⚠️ Must convert Workspaces_UI from CRA → Nx
⚠️ Update all imports to Nx style
⚠️ Reconcile build configs
⚠️ Migrate CI/CD files into main pipeline

Timeline Impact: +2-3 weeks (CRA → Nx migration)
```

**Option B: Use Monorepo Tools (Git Submodules or Nx Remote)**
```
Result:
Catalog/
├─ Workspaces_UI/ (submodule pointing to original repo)

Benefits:
✅ Keeps Workspaces_UI repo separate
✅ Can maintain separate CI/CD (initially)
✅ Easier incremental migration

Challenges:
⚠️ Still have 2 build systems (Nx + CRA)
⚠️ Local dev still complex (run both builds?)
⚠️ Shared code harder to manage
⚠️ Eventual consolidation still needed

Timeline Impact: Faster initially, but delays real consolidation
```

**Recommendation:** **Option A (Move into Catalog repo)**
- More work upfront, but achieves true consolidation
- Single source of truth
- Simpler long-term maintenance
- Proper Nx monorepo structure

This means:
1. Convert Workspaces_UI from CRA → Nx project
2. Move src/ into ui/apps/workspaces/
3. Update package.json references
4. Migrate CI/CD into main pipeline
5. Unify build/test/lint commands

### 0.3: Design Unified Architecture

**Task:** Create target architecture

```
Unified Application Structure (Post-Consolidation):

src/
├─ main.tsx                           (Single entry point)
├─ App.tsx                            (Root app with unified routing)
├─ auth/                              (Unified auth context)
│  ├─ KeycloakProvider.tsx
│  ├─ AuthContext.tsx
│  └─ useAuth.ts
├─ telemetry/                         (Unified telemetry)
│  ├─ TelemetryContext.tsx
│  └─ useTelemetry.ts
├─ router/                            (Single react-router)
│  ├─ rootRouter.tsx                  (Root router config)
│  ├─ catalogRoutes.tsx               (Catalog feature routes)
│  ├─ workspacesRoutes.tsx            (Workspaces feature routes)
│  └─ workflowsRoutes.tsx             (Workflows feature routes)
├─ features/
│  ├─ catalog/                        (Catalog feature module)
│  │  ├─ pages/
│  │  ├─ components/
│  │  ├─ hooks/
│  │  └─ index.ts
│  ├─ workspaces/                     (Workspaces feature module)
│  │  ├─ pages/
│  │  ├─ components/
│  │  ├─ hooks/
│  │  └─ index.ts
│  └─ workflows/                      (Workflows feature module)
│     ├─ pages/
│     ├─ components/
│     ├─ hooks/
│     └─ index.ts
├─ shared/                            (Shared components/hooks)
│  ├─ components/
│  ├─ hooks/
│  ├─ utils/
│  └─ types/
└─ config/                            (Configuration)
   ├─ environment.ts
   └─ constants.ts
```

**Key Design Decisions to Make:**
- [ ] Will features be in separate Nx libraries or within ui/apps/shell?
- [ ] How to handle feature-specific styling (Tailwind, CSS modules)?
- [ ] Shared state management (Redux, Context, Zustand)?
- [ ] How to lazy-load features (if at all)?
- [ ] Layout structure (shared header/footer, feature-specific)?

### 0.4: Kick-off Meeting with Team

**Attendees:** Your tech lead, Neptali, Andrew, 2-3 devs

**Agenda:**
- [ ] Review analysis findings
- [ ] Confirm target architecture
- [ ] Discuss phased approach (all-at-once vs. phased)
- [ ] Allocate team members to phases
- [ ] Establish communication plan
- [ ] Define success criteria

**Outputs:**
- [ ] Signed-off architecture diagram
- [ ] Phase breakdown agreed
- [ ] Team assignments
- [ ] Expected timeline

---

## Phase 1: Foundation & Setup (Week 3-4)

### Objective
Prepare the unified application structure and tooling without breaking existing functionality.

### 1.1: Create Unified App Shell

**Task:** Set up base structure for consolidated app in `ui/apps/shell`

```bash
# Create new directory structure
ui/apps/shell/src/
├─ main.tsx                    # NEW: Single entry point
├─ App.tsx                     # NEW: Root app component
├─ index.html                  # MODIFY: Update script tags
└─ environments/
   └─ config.local.json        # REMOVE: No more remotes
```

**What stays:** Current shell infrastructure (webpack, Nx config, tsconfig)  
**What changes:** Remove Module Federation configuration

**Key Work:**
```typescript
// src/main.tsx - NEW
import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

// src/App.tsx - NEW
import { BrowserRouter } from 'react-router-dom';
import { KeycloakProvider } from './auth/KeycloakProvider';
import { TelemetryProvider } from './telemetry/TelemetryProvider';
import { RootRouter } from './router/rootRouter';

export function App() {
  return (
    <KeycloakProvider>
      <TelemetryProvider>
        <BrowserRouter>
          <RootRouter />
        </BrowserRouter>
      </TelemetryProvider>
    </KeycloakProvider>
  );
}
```

**Estimate:** 2-3 days (1 developer)

### 1.2: Unify Keycloak Authentication

**Task:** Create single auth context that both old and new apps can use

**Current Problem:**
```
Catalog: Bootstraps Keycloak independently
Workspaces: Bootstraps Keycloak (remote)
Workflows: Bootstraps in iframe
Result: 3 separate Keycloak instances
```

**Solution:**
```typescript
// src/auth/KeycloakProvider.tsx - NEW
import { ReactNode, useEffect, useState } from 'react';
import Keycloak from 'keycloak-js';
import { AuthContext } from './AuthContext';

interface KeycloakConfig {
  url: string;
  realm: string;
  clientId: string;
}

export function KeycloakProvider({ children }: { children: ReactNode }) {
  const [keycloak, setKeycloak] = useState<Keycloak | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    const initKeycloak = async () => {
      const config = getKeycloakConfig(); // From env
      
      const keycloakInstance = new Keycloak({
        url: config.url,
        realm: config.realm,
        clientId: config.clientId,
      });

      try {
        const authenticated = await keycloakInstance.init({
          onLoad: 'login-required',
          silentCheckSsoRedirectUri: `${window.location.origin}/auth/silent-check-sso`,
        });

        setKeycloak(keycloakInstance);
        setIsInitialized(true);
      } catch (error) {
        console.error('Keycloak init failed:', error);
      }
    };

    initKeycloak();
  }, []);

  if (!isInitialized) {
    return <div>Initializing...</div>;
  }

  return (
    <AuthContext.Provider value={{ keycloak, isInitialized }}>
      {children}
    </AuthContext.Provider>
  );
}
```

**Estimate:** 2-3 days (1 developer)

### 1.3: Create Single React-Router Configuration

**Task:** Design unified routing that handles all 3 feature areas

**Before (3 routers):**
```
Catalog: /catalog/*, /workspaces (loads remote or iframe)
Workspaces: /app/* (within remote)
Workflows: iframe (separate routing inside iframe)
```

**After (1 router):**
```
/                      → Catalog dashboard/landing
/datasets/*            → Catalog features
/workspaces/*          → Workspaces features  
/workflows/*           → Workflows features
/admin/*               → Admin section (if needed)
```

**Implementation:**
```typescript
// src/router/rootRouter.tsx - NEW
import { Routes, Route, Navigate } from 'react-router-dom';
import { catalogRoutes } from './catalogRoutes';
import { workspacesRoutes } from './workspacesRoutes';
import { workflowsRoutes } from './workflowsRoutes';

export function RootRouter() {
  return (
    <Routes>
      {catalogRoutes()}
      {workspacesRoutes()}
      {workflowsRoutes()}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

// src/router/catalogRoutes.tsx - NEW
import { Route } from 'react-router-dom';
import { CatalogLayout } from '../features/catalog/CatalogLayout';
import { DatasetsPage } from '../features/catalog/pages/DatasetsPage';
// ... more catalog routes

export function catalogRoutes() {
  return (
    <Route element={<CatalogLayout />}>
      <Route path="/" element={<DatasetsPage />} />
      <Route path="/datasets" element={<DatasetsPage />} />
      {/* ... more routes */}
    </Route>
  );
}
```

**Key design questions:**
- Do features share a header/nav, or have separate layouts?
- What's the entry point? (/ → catalog? or separate pages?)
- How to handle feature permissions/visibility?

**Estimate:** 3-4 days (1 developer)

### 1.4: Verify Dependencies Don't Conflict

**Task:** Ensure shared packages have compatible versions

**Common conflicts:**
```
react-router
├─ Catalog: v6.15.0
├─ Workspaces: v6.14.0 ← Different minor version
└─ Workflows: v6.12.0 ← Much older

react
├─ Catalog: v18.3.1
├─ Workspaces: v18.3.1 ✓
└─ Workflows: v18.2.0 ← Older patch
```

**Solution:**
```bash
# Run dependency audit
npm ls react react-router-dom react-query

# Create consolidated package.json strategy
# - Keep highest compatible version
# - Check for breaking changes in minor versions
# - Test each upgrade incrementally
```

**Estimate:** 1-2 days (1 developer)

### 1.5: Parallel: Create Telemetry Context

**Task:** Design unified telemetry that traces across all features

```typescript
// src/telemetry/TelemetryContext.tsx - NEW
import { ReactNode, useCallback } from 'react';
import { TelemetryContext } from './TelemetryContext';

export function TelemetryProvider({ children }: { children: ReactNode }) {
  const trackEvent = useCallback((
    eventName: string,
    properties?: Record<string, any>
  ) => {
    // Send to Application Insights with unified context
    appInsights.trackEvent(eventName, {
      ...properties,
      feature: getCurrentFeature(), // Which feature?
      user: getCurrentUser(),
      timestamp: new Date().toISOString(),
    });
  }, []);

  return (
    <TelemetryContext.Provider value={{ trackEvent }}>
      {children}
    </TelemetryContext.Provider>
  );
}
```

**Estimate:** 2 days (1 developer)

## Phase 1: CRA → Nx Migration (Week 3-6)

### Objective
Migrate Workspaces_UI from Create React App (CRA) to Nx workspace, then merge into Catalog repo unified structure.

**Why This Phase?** Workspaces_UI uses incompatible build system (CRA + craco). Must convert to Nx for single unified build system.

### 1.1: Move Workspaces_UI Code Into Catalog Repository

**Task:** Physically move code from separate Workspaces_UI repo into Catalog repo structure

```bash
# Create new Nx app for workspaces
cd Catalog/ui/apps
nx generate @nx/react:app workspaces --directory=apps

# OR manually:
# Copy Workspaces_UI/src/* → Catalog/ui/apps/workspaces/src/
# Copy Workspaces_UI/public/* → Catalog/ui/apps/workspaces/public/
```

**File Structure After:**
```
Catalog/
├─ ui/apps/
│  ├─ shell/          (Catalog app - already Nx)
│  ├─ workspaces/     (MOVED from Workspaces_UI repo) ⭐
│  ├─ workflows/      (already here)
│  └─ nx.json         (single workspace config)
└─ (rest of Catalog)
```

**Estimate:** 1-2 days

### 1.2: Convert CRA Build Config to Nx

**Task:** Remove CRA-specific configs and replace with Nx equivalents

**What to Remove:**
```
❌ Workspaces_UI/craco.config.js     (CRA customization - DELETE)
❌ react-scripts (from package.json) (DELETE - Nx uses webpack directly)
❌ Multiple CI/CD files             (DELETE - consolidate into main pipeline)
```

**What to Update:**
```
✅ Create project.json for workspaces app (Nx configuration)
✅ Update tsconfig.json to use shared Nx tsconfig.base.json
✅ Update jest configuration to use Nx/shared jest config
✅ Add workspaces targets: build, serve, test, lint
```

**New Workspaces project.json:**
```json
{
  "name": "workspaces",
  "projectType": "application",
  "targets": {
    "build": {
      "executor": "@nx/webpack:webpack",
      "options": {
        "outputPath": "dist/apps/workspaces"
      }
    },
    "serve": {
      "executor": "@nx/webpack:dev-server",
      "options": {
        "buildTarget": "workspaces:build",
        "port": 4201
      }
    },
    "test": {
      "executor": "@nx/jest:jest",
      "options": {
        "jestConfig": "ui/apps/workspaces/jest.config.ts"
      }
    }
  }
}
```

**Estimate:** 3 days

### 1.3: Consolidate Dependencies

**Task:** Merge Workspaces_UI dependencies into Catalog root package.json, resolve conflicts

**Current Versions:**
```
Workspaces_UI has:
├─ react: 18.3.1 ✓ (matches Catalog)
├─ react-router-dom: v6.28.0
├─ @reduxjs/toolkit: 2.4.0
├─ keycloak-js: 26.0.6
└─ ... 30+ other packages

Catalog has:
├─ react: 18.3.1 ✓
├─ react-router-dom: v6.15.0 ❌ (NEED TO UPGRADE)
├─ Redux: (version TBD)
└─ ... other packages
```

**Process:**
```bash
# 1. Add all Workspaces_UI dependencies to root package.json
pnpm add <package_name>

# 2. For conflicts, choose higher version (safer)
# 3. Run tests to verify no conflicts

# 4. Update package-lock/pnpm-lock.yaml
pnpm install

# 5. Check for peer dependency warnings
pnpm list --peer-only
```

**Upgrade React-Router:**
```
Catalog: v6.15.0 → v6.28.0
Rationale: Match Workspaces_UI version
Check: Breaking changes between v6.15 and v6.28
```

**Estimate:** 2-3 days

### 1.4: Update Imports to Nx Style

**Task:** Update all imports to use Nx path aliases from tsconfig.base.json

**Before (CRA style):**
```typescript
import { Button } from '../components/Button';
import { api } from '../../services/api';
```

**After (Nx style):**
```typescript
import { Button } from '@ui/shared/components';
import { api } from '@workspaces/services';
```

**Configuration in tsconfig.base.json:**
```json
{
  "compilerOptions": {
    "paths": {
      "@ui/shared/*": ["libs/shared/*"],
      "@workspaces/*": ["apps/workspaces/src/*"],
      "@catalog/*": ["apps/shell/src/*"],
      "@workflows/*": ["apps/workflows/src/*"]
    }
  }
}
```

**Tools:**
- VSCode find/replace with regex
- TypeScript compiler can help identify import issues
- Nx may have migration helpers

**Estimate:** 3-4 days (tedious but mechanical)

### 1.5: Update Build and Lint Commands

**Task:** Remove CRA-specific scripts, use Nx commands instead

**Before (CRA in Workspaces_UI):**
```json
{
  "scripts": {
    "start": "craco start",
    "build": "craco build",
    "test": "react-scripts test"
  }
}
```

**After (Nx in root):**
```json
{
  "scripts": {
    "start": "nx serve shell",        // Catalog
    "start:workspaces": "nx serve workspaces",
    "build:shell": "nx build shell",
    "build:workspaces": "nx build workspaces",
    "test:workspaces": "nx test workspaces",
    "test": "nx run-many --target=test"
  }
}
```

**Update Nx config (nx.json):**
```json
{
  "tasksRunnerOptions": {
    "default": {
      "runner": "@nx/workspace:native",
      "options": {
        "cacheableOperations": ["build", "test", "lint"]
      }
    }
  }
}
```

**Estimate:** 1-2 days

### 1.6: Verify All Builds Work

**Task:** Test that workspaces app builds and serves correctly under Nx

```bash
# Build workspaces app
nx build workspaces

# Serve workspaces app
nx serve workspaces

# Run workspaces tests
nx test workspaces

# Run all tests
nx run-many --target=test
```

**Checklist:**
- [ ] `nx build workspaces` succeeds
- [ ] `nx serve workspaces` runs on correct port
- [ ] No TypeScript errors
- [ ] No webpack build warnings
- [ ] Tests pass
- [ ] All imports resolve correctly

**Estimate:** 2-3 days (troubleshooting any build issues)

**Phase 1 Total:** 4 weeks (2-3 developers, with Nx expertise leading)

---

## Phase 2: Feature Integration & Consolidation (Week 7-14)

### Objective
Extract Workflows from iframe, consolidate code, and integrate all three features into unified app.

### 2.1: Extract Workflows from iframe

**Task:** Convert iframe-embedded Workflows app into native React component

**Current State:**
```html
<!-- Workflows embedded in iframe in Workspaces -->
<iframe src="/workflows.html" />

<!-- Separate webpack config, separate build -->
```

**Target State:**
```typescript
// Workflows is now a feature module
import { WorkflowsFeature } from './features/workflows';

// Loaded as a React component, not iframe
<Routes>
  <Route path="/workflows/*" element={<WorkflowsFeature />} />
</Routes>
```

**Detailed Steps:**

#### Step A: Extract Workflows App
```bash
# 1. Locate workflows app (separate from ui/apps/shell)
find . -name "*workflows*" -type d

# Likely locations:
# - ui/apps/workflows/
# - Or embedded within ui/apps/shell?

# 2. Extract source files
# - Entry point (index.tsx, bootstrap.tsx)
# - All components
# - All hooks
# - All utilities
```

#### Step B: Remove iframe Communication
```typescript
// OLD (Workflows in iframe):
// Parent sends messages to iframe
window.frames[0].postMessage({ action: 'navigate', path: '/workflow/1' });

// Child (iframe) listens:
window.addEventListener('message', (event) => {
  if (event.data.action === 'navigate') {
    navigate(event.data.path);
  }
});

// NEW (Native component):
// Direct function call
<WorkflowsFeature onNavigate={handleNavigate} />
```

#### Step C: Unify Authentication
```typescript
// OLD (Iframe):
// Iframe had its own Keycloak bootstrap
// Parent passed auth token via postMessage

// NEW (Native):
// Share auth context from parent
import { useAuth } from '../../auth/useAuth';

export function WorkflowsFeature() {
  const { keycloak } = useAuth();
  // Use keycloak directly, no postMessage
}
```

#### Step D: Consolidate Routes
```typescript
// OLD routes (separate within iframe)
/workflows/list
/workflows/detail/:id
/workflows/create

// NEW routes (within unified app)
/workflows/list
/workflows/detail/:id
/workflows/create

// Same routes, but now part of single router
```

**Estimate:** 3-4 weeks (1-2 developers)  
**Risk:** 🟠 Medium - Need to systematically remove iframe dependencies

**Testing Strategy:**
- Unit tests for extracted components
- End-to-end tests for workflows feature
- Verify no auth token passing issues
- Check telemetry integration

### 2.2: Merge Workspaces into Unified App

**Task:** Integrate Workspaces feature into unified routing

**Current State:**
```
Workspaces loaded via Module Federation
├─ Separate webpack config
├─ Separate entry point
└─ Separate build process
```

**Target State:**
```
Workspaces as feature module
├─ Lives in src/features/workspaces/
├─ Exports routes and components
└─ Part of unified build
```

**Steps:**

#### Step A: Move Workspaces Source
```bash
# Copy workspaces app into unified structure
cp -r apps/workspaces/src/app/* apps/shell/src/features/workspaces/
```

#### Step B: Resolve Module Federation
```typescript
// OLD (uses Module Federation):
const WorkspacesApp = lazy(() => import('workspaces/App'));

// NEW (direct import):
import { WorkspacesApp } from './features/workspaces/App';
```

#### Step C: Consolidate Dependencies
```
Before:
├─ Catalog has: react-router v6.15, react-query v5.0
└─ Workspaces has: react-router v6.14, react-query v4.8

After:
└─ Both use: react-router v6.15, react-query v5.0
```

#### Step D: Integrate Routes
```typescript
// src/router/workspacesRoutes.tsx - NEW
export function workspacesRoutes() {
  return (
    <Route path="/workspaces" element={<WorkspacesLayout />}>
      <Route index element={<WorkspacesListPage />} />
      <Route path=":id" element={<WorkspaceDetailPage />} />
      {/* ... more routes */}
    </Route>
  );
}
```

**Estimate:** 2 weeks (1-2 developers)  
**Risk:** 🟢 Low - No complex iframe extraction

### 2.3: Consolidate Catalog (Already in Place)

**Task:** Ensure existing Catalog routes continue working

**What to do:**
- Verify existing routes mapped to new routing system
- Ensure all imports updated to use new structure
- Test existing functionality

**Estimate:** 1 week (1 developer)

### 2.4: Consolidate Shared Components

**Task:** Identify and consolidate duplicate components/utilities across 3 apps

**Analysis:**
```bash
# Find potential duplicates
grep -r "export function.*" */src/components | sort

# Likely duplicates:
├─ Header/Navigation (each app had their own)
├─ Layout components (Sidebar, etc.)
├─ Shared UI components (Button, Card, etc.)
├─ Hooks (useAuth, useNavigation, etc.)
└─ Utils (date formatting, API calls, etc.)
```

**Consolidation:**
```typescript
// BEFORE (duplicated):
ui/apps/shell/src/components/Header.tsx
ui/apps/workspaces/src/components/Header.tsx
ui/apps/workflows/src/components/Header.tsx
// ... 3 versions, slightly different

// AFTER (consolidated in shared):
ui/libs/shared/components/Header.tsx
// Used by all features

// Or within unified app:
ui/apps/shell/src/shared/components/Header.tsx
// Used by all features
```

**Estimate:** 1-2 weeks (1 developer)

**Phase 2 Total:** ~7-8 weeks (can use 2-3 developers in parallel on different features)

---

## Phase 3: Build System & Pipeline Consolidation (Week 15-16)

### Objective
Unify build process and CI/CD pipeline for single application.

### 3.1: Remove Module Federation Config

**Task:** Simplify webpack configuration

```typescript
// OLD webpack.config.ts (has Module Federation):
withModuleFederation(loadModuleFederationRemotesFromConfig(), { dts: false })

// NEW webpack.config.ts:
// Just standard React + Webpack, no federation
withReact()
```

**Changes:**
- Remove `withModuleFederation` plugin
- Remove remote loading logic
- Remove shared dependencies config
- Simplify to standard React webpack

**Estimate:** 1-2 days (1 developer)

### 3.2: Consolidate Build Pipelines

**Task:** Update CI/CD to single build

**Before (`tools/ci/jobs/build_deliverables.yml`):**
```yaml
- template: ./ui_theme_build.yml
  parameters:
    theme: actc

- template: ./ui_unit_tests.yml

- template: ./ui_theme_build.yml   # Multiple builds!
  parameters:
    theme: epnd

- template: ./ui_theme_build.yml
  parameters:
    theme: adwb
```

**After:**
```yaml
- template: ./ui_unit_tests.yml
  
- template: ./ui_build.yml         # Single build
  parameters:
    theme: actc                     # Still build per-theme for branding
    
# ... if still doing per-theme builds for branding
```

**Key Decision:** How many builds per pipeline?
- Option 1: Single build output, deploy to all themes (simpler)
- Option 2: Build per-theme for branding (current model), but from single codebase

**Likely approach:** Keep per-theme for branding, but single codebase consolidation.

**Changes:**
```yaml
# OLD:
shell_build.yml
workspaces_build.yml
workflows_build.yml

# NEW:
ui_build.yml         # Builds all features into single app
```

**Estimate:** 2-3 days (1 developer)

### 3.3: Update Nx Configuration

**Task:** Update project.json and nx.json

```json
// ui/apps/shell/project.json - MODIFY

OLD:
"targets": {
  "build": { "command": "nx build shell" },
  "serve": { "command": "nx serve shell" }
}

NEW:
"targets": {
  "build": { 
    "command": "nx build shell",
    // No module federation
    // Single output
  },
  "serve": { 
    "command": "nx serve shell"
    // Single local dev server
  }
}
```

**Estimate:** 1 day (1 developer)

### 3.4: Single Local Dev Server

**Task:** Simplify `pnpm start` to run single server

**Before:**
```bash
# Terminal 1
pnpm start                 # Catalog app

# Terminal 2  
cd apps/workspaces
npm start                  # Workspaces remote

# Terminal 3
cd apps/workflows
npm start                  # Workflows app
```

**After:**
```bash
# Single terminal
pnpm start                 # All features in one app
```

**What to do:**
- Update package.json scripts
- Remove separate dev servers
- Single webpack dev server serves everything

**Estimate:** 1 day (1 developer)

**Phase 3 Total:** ~2 weeks (1-2 developers)

---

## Phase 4: Testing & Validation (Week 17-19)

### Objective
Comprehensive testing to ensure nothing broke and all features work correctly.

### 4.1: Unit & Component Tests

**Task:** Verify all extracted/moved components work correctly

```bash
# Run all tests
pnpm test

# Check coverage
pnpm test:coverage

# Expected coverage: >80%
```

**Focus areas:**
- Catalog features
- Workspaces features
- Workflows features (newly integrated)
- Shared components/utilities

**Estimate:** 3-4 days

### 4.2: Integration Tests

**Task:** Test feature interactions across consolidated app

**Test scenarios:**
```typescript
// Catalog → Workspaces navigation
test('Can navigate from catalog to workspace', () => {
  // User in catalog
  // Clicks workspace link
  // Workspaces feature loads
  // Routes correctly to workspace detail
});

// Workspaces → Workflows navigation
test('Can navigate from workspace to workflow', () => {
  // User in workspaces
  // Opens workflow
  // Workflows feature loads (previously in iframe)
  // Workflow displays correctly
});

// End-to-end telemetry
test('Telemetry traces across all features', () => {
  // User actions in catalog
  // Actions in workspaces
  // Actions in workflows
  // All appear in single trace in Application Insights
});

// Auth context sharing
test('Auth context shared across all features', () => {
  // User token valid in catalog
  // Token still valid in workspaces
  // Token still valid in workflows
});
```

**Tools:**
- Jest + React Testing Library (unit/component)
- Cypress or Playwright (E2E)

**Estimate:** 4-5 days

### 4.3: Performance Testing

**Task:** Ensure consolidated app performs well

**Metrics:**
```
Before (3 separate apps):
├─ Catalog: 500KB bundle
├─ Workspaces: 400KB bundle
├─ Workflows: 300KB bundle
└─ Total (separate): 1.2MB
   (But only one loads at a time)

After (1 unified app):
├─ Single app: 900KB bundle
│  (Smaller total, but all loaded)
├─ Tree shaking should reduce unused code
└─ Target: <900KB
```

**Performance checklist:**
- [ ] Bundle size <1MB
- [ ] Initial page load <3s
- [ ] Feature routes lazy-load? (if yes, check lazy load perf)
- [ ] No memory leaks (auth context, telemetry context)
- [ ] No duplicate Keycloak initializations

**Tools:**
- Webpack Bundle Analyzer
- Lighthouse
- Chrome DevTools

**Estimate:** 2-3 days

### 4.4: Feature Verification

**Task:** Manual testing of all 3 features

**Test matrix:**
```
┌─────────────────┬──────────┬─────────────┬──────────────┐
│ Feature         │ Catalog  │ Workspaces  │ Workflows    │
├─────────────────┼──────────┼─────────────┼──────────────┤
│ Landing         │   ✓      │    ✓        │    ✓         │
│ Navigation      │   ✓      │    ✓        │    ✓         │
│ CRUD operations │   ✓      │    ✓        │    ✓         │
│ Authentication  │   ✓      │    ✓        │    ✓         │
│ Search/Filter   │   ✓      │    ✓        │    ✓         │
│ Telemetry       │   ✓      │    ✓        │    ✓         │
└─────────────────┴──────────┴─────────────┴──────────────┘
```

**Environments to test:**
- Local development
- Staging environment
- Production (after blue-green deploy)

**Estimate:** 3-4 days

### 4.5: Security & Auth Testing

**Task:** Verify auth consolidation is secure

**Checklist:**
- [ ] Keycloak session shared correctly
- [ ] No auth token leakage between features
- [ ] CSRF protection intact
- [ ] No mixed content (http/https)
- [ ] API endpoints all secure

**Estimate:** 1-2 days

**Phase 4 Total:** ~2-3 weeks (2-3 developers in parallel)

---

## Phase 5: Documentation & Deployment (Week 20)

### Objective
Document changes and deploy consolidated app.

### 5.1: Update Documentation

**Create/Update:**
- [ ] Architecture documentation (consolidated app design)
- [ ] Local development guide (single `pnpm start`)
- [ ] Feature module documentation (Catalog, Workspaces, Workflows)
- [ ] Routing guide (unified routing structure)
- [ ] Build/deployment guide (single pipeline)
- [ ] Migration guide (for team members understanding changes)

**Estimate:** 2-3 days

### 5.2: Deployment Strategy

**Option A: Blue-Green Deployment** (Safer)
```
1. Build new consolidated app
2. Deploy to "green" environment
3. Run full test suite on green
4. Switch traffic from "blue" to "green"
5. Keep blue as rollback
```

**Option B: Canary Deployment** (Gradual)
```
1. Build consolidated app
2. Deploy to 10% of users
3. Monitor metrics (errors, latency, telemetry)
4. If good: increase to 100%
5. If bad: rollback to 0%
```

**Recommendation:** Use blue-green for safety, then monitor heavily.

**Estimate:** 1-2 days

### 5.3: Rollback Plan

**If consolidated app has critical issues:**
```
1. Immediate rollback command
   az deployment group create --template-uri [old-deployment-template]

2. Rollback criteria
   - >1% error rate increase
   - >500ms latency increase
   - Complete feature unavailability
   - Authentication failures

3. Communication plan
   - Notify stakeholders immediately
   - Document root cause
   - Plan fix
```

**Estimate:** 1 day

**Phase 5 Total:** ~1 week (1-2 developers)

---

## Complete Timeline Summary

| Phase | Duration | Team Size | Focus |
|-------|----------|-----------|-------|
| Phase 0: Pre-Impl | Week 1-2 | 1-2 | Planning, analysis of both repos |
| **Phase 1: CRA→Nx Migration** | **Week 3-6** | **2-3** | **Convert Workspaces_UI from CRA to Nx** ⭐ |
| Phase 2: Feature Integration | Week 7-14 | 2-3 | Redux, Auth, React-Router consolidation |
| Phase 3: Build System | Week 15-16 | 1-2 | CI/CD pipeline unification |
| Phase 4: Testing | Week 17-19 | 2-3 | Comprehensive testing |
| Phase 5: Deploy | Week 20 | 1-2 | Documentation, launch |
| **TOTAL** | **20 weeks** | **3 devs** | **Single unified app + multi-repo consolidation** |

### Recommended Team Allocation

**Consolidation Stream (Primary):**
- 1 lead developer with Nx/webpack expertise
- 1-2 general frontend developers
- 0.5 FTE merge manager (conflict resolution & git orchestration)
- Tech lead for guidance & architecture decisions

**Workspaces Feature Stream (Parallel):**
- 1 senior developer (feature ownership & vendor liaison)
- 1 mid-level developer (implementation)

**Cross-Stream Responsibilities:**
- Weekly sync: 1 person from each stream (30 min)
- Conflict resolution: Merge manager + both stream leads
- Escalation: Tech lead resolves blocking architectural decisions

**Phase-Specific Allocation:**

Phase 0-1 (Week 1-6):
- Consolidation: 2-3 developers (heavy work)
- Workspaces: 2 developers (business as usual)
- Merge manager: 20% time (light merges, planning)

Phase 2-3 (Week 7-16):
- Consolidation: 2-3 developers (feature migration, build system)
- Workspaces: 2 developers (continue features)
- Merge manager: 50% time (heavy merge volume expected)

Phase 4-5 (Week 17-20):
- Consolidation: 2-3 developers (testing, documentation, deploy)
- Workspaces: 1 developer (smaller team, focus on supporting consolidation)
- Merge manager: 30% time (declining merge volume as feature freeze begins)

---

## Risk Mitigation

### Risk 1: Breaking Changes Between App Versions
**Status Indicator:** 🟠 Moderate

**Mitigation:**
- [ ] Comprehensive version audit in Phase 0
- [ ] Incremental upgrade testing
- [ ] Feature flags to disable problematic features
- [ ] Extensive E2E testing

### Risk 2: Complex Dependency Conflicts
**Status Indicator:** 🟠 Moderate

**Mitigation:**
- [ ] Dependency tree analysis tools
- [ ] Try merging in isolated branch first
- [ ] Detailed conflict resolution strategy
- [ ] New dependency lockfile

### Risk 3: Auth Context Issues (Workflows extraction)
**Status Indicator:** 🟠 Moderate

**Mitigation:**
- [ ] Mock auth in tests early
- [ ] POC iframe extraction on shallow component first
- [ ] Extensive auth flow testing
- [ ] Keycloak configuration review

### Risk 4: Performance Degradation (1 large app vs 3 small)
**Status Indicator:** 🟡 Low-Moderate

**Mitigation:**
- [ ] Bundle analysis tools configured
- [ ] Lazy loading for feature routes
- [ ] Code splitting strategy
- [ ] Performance baselines established
- [ ] Performance testing before deployment

### Risk 5: Incomplete Feature Coverage
**Status Indicator:** 🟡 Low-Moderate

**Mitigation:**
- [ ] Complete feature inventory in Phase 0
- [ ] Feature checklist for migration
- [ ] Manual testing matrix
- [ ] Compare old vs new feature parity

---

## Success Criteria

### Functional Requirements ✅
- [ ] Single application runs with `pnpm start`
- [ ] All catalog features work as before
- [ ] All workspaces features work as before
- [ ] All workflows features work (extracted from iframe)
- [ ] Navigation between all features works correctly
- [ ] User canroute to any feature from any other feature

### Technical Requirements ✅
- [ ] Single react-router v6 instance (unified routing)
- [ ] Single Keycloak auth context (shared token)
- [ ] Unified telemetry (can trace events across features)
- [ ] Single webpack build
- [ ] Single CI/CD pipeline
- [ ] Zero Module Federation artifacts

### Performance Requirements ✅
- [ ] Bundle size <1MB (or <previous total)
- [ ] Initial page load <3s
- [ ] Feature routes load <500ms
- [ ] No performance regression on main features

### Quality Requirements ✅
- [ ] Unit test coverage >80%
- [ ] Integration tests for cross-feature flows
- [ ] E2E test coverage of critical paths
- [ ] No console errors or warnings
- [ ] Accessibility audit passes (WCAG 2.1 AA)

### DevOps Requirements ✅
- [ ] Local development setup: `pnpm install && pnpm start`
- [ ] Build pipeline runs in <15 minutes
- [ ] Deployment <10 minutes
- [ ] Rollback capability in <5 minutes
- [ ] Monitoring/alerting in place

### Business Requirements ✅
- [ ] Zero downtime deployment
- [ ] All features available to users
- [ ] Improved performance for end users
- [ ] Better maintenance experience for developers

---

## Appendix: Phase 0 Analysis Document Template

### Section A: Consolidation Analysis

**TO COMPLETE IN PHASE 0 - Include these details:**

#### A.1: Current Architecture Overview

```
Repository Structure:
ui/
├─ apps/
│  ├─ shell/                    # Catalog (host)
│  ├─ workspaces/               # Workspaces remote?
│  └─ workflows/                # Workflows app?
├─ libs/                         # Shared libraries
└─ ...

Current app relationships:
┌─────────────────────────────────┐
│   Catalog (ui/apps/shell)       │
│   - Port 4200                   │
│   - Module Federation host      │
└──────┬──────────────────────────┘
       │ ModuleFederation.loadRemote
       ├─→ Workspaces
       └─→ (Workflows in iframe)

Entry Points:
├─ Catalog: ui/apps/shell/src/bootstrap.tsx
├─ Workspaces: ui/apps/workspaces/src/bootstrap.tsx (?)
└─ Workflows: (Embedded within Workspaces)
```

#### A.2: React-Router Versions

```
Discovery Tool:
cat ui/apps/shell/package.json | grep "react-router"
cat ui/apps/workspaces/package.json | grep "react-router"
cat ui/apps/workflows/package.json | grep "react-router"

Current Status:
Catalog: react-router-dom: "^6.15.0"
Workspaces: react-router-dom: "^6.14.0"
Workflows: react-router-dom: "^6.12.0"

Conflicts: YES - need migration plan per version jump
Breaking changes: [List any v6.12→6.14→6.15 breaking changes]
```

#### A.3: Authentication Flow

```
CURRENT:
Catalog:
├─ Keycloak bootstrap in bootstrap.tsx
├─ Token stored in sessionStorage
└─ Used for API calls

Workspaces (remote):
├─ Separate Keycloak bootstrap
├─ Separate token (?)
└─ Issues: [note any cross-origin issues]

Workflows (iframe):
├─ Iframe has separate origin (?)
├─ Token passing mechanism: [how?]
└─ Issues: [note any CORS issues]

TARGET:
Single Keycloak bootstrap
├─ Token in Context
├─ Shared across all features
└─ No iframe = simpler
```

#### A.4: Telemetry Setup

```
CURRENT:
Application Insights initialized in:
├─ Catalog: [which file?]
├─ Workspaces: [separate initialization?]
└─ Workflows: [separate initialization?]

Issues:
- Can events be traced across apps? [Yes / No]
- Can events be traced through iframe? [Yes / No]
- Are user sessions unified? [Yes / No]

TARGET:
Single Application Insights context
├─ Initialized once in root app
├─ Shared via React Context
└─ All features use same context
```

#### A.5: Shared Dependencies

```
CURRENT:
Catalog package.json:
├─ react: "^18.3.1"
├─ react-dom: "^18.3.1"
├─ react-query: "^5.0.0"
└─ [...list others]

Workspaces package.json:
├─ react: "^18.3.1"
├─ react-dom: "^18.3.1"
├─ react-query: "^4.8.0" ← Different!
└─ [...]

Workflows package.json:
├─ react: "^18.2.0" ← Different!
├─ react-dom: "^18.2.0"
└─ [...]

Conflicts to Resolve:
[List which packages have conflicting versions]
```

#### A.6: Route Inventory

```
CATALOG ROUTES:
GET / (landing)
GET /datasets (list)
GET /datasets/:id (detail)
GET /search?q=...
... [complete list]

WORKSPACES ROUTES:
GET /workspaces (list)
GET /workspaces/:id (detail)
PUT /workspaces/:id (edit modal)
... [complete list]

WORKFLOWS ROUTES:
GET /workflows (list)
GET /workflows/:id (detail)
POST /workflows (create)
... [complete list]

TARGET UNIFIED ROUTES:
GET / (catalog landing)
GET /datasets/*
GET /workspaces/*
GET /workflows/*
```

#### A.7: Shared Component Inventory

```
CATALOG COMPONENTS:
src/components/
├─ Header.tsx (1200 lines)
├─ Sidebar.tsx (800 lines)
├─ DataTable.tsx (reusable?)
└─ ...

WORKSPACES COMPONENTS:
src/components/
├─ Header.tsx (1100 lines) ← Similar to Catalog?
├─ Navigation.tsx
└─ ...

WORKFLOWS COMPONENTS:
src/components/
├─ Header.tsx (900 lines) ← Similar?
└─ ...

CONSOLIDATION PLAN:
Components to consolidate:
├─ Header (use Catalog version, adapt for others)
├─ Sidebar (consolidate)
└─ [List others]

New shared component location:
ui/apps/shell/src/shared/components/
or
ui/libs/shared/component/
```

---

## Next Steps (Immediate Actions)

**This week:**
1. [ ] Review this plan with tech lead
2. [ ] Confirm team allocation (2-3 devs)
3. [ ] Start Phase 0 analysis (use Section A template)
4. [ ] Schedule kick-off meeting

**Next week:**
5. [ ] Complete Phase 0 analysis
6. [ ] Get architecture sign-off
7. [ ] Establish success criteria with team
8. [ ] Branch planning: Create feature branch for consolidation
9. [ ] Begin Phase 1 foundation work

---

## Questions to Resolve Before Starting

1. **Vendor Feature Strategy During Consolidation:** 
   - Option A: Allow new features (weekly merge overhead, feature momentum)
   - Option B: Feature freeze (faster consolidation, vendor acceptance risk)
   
2. **Merge Manager Role:** 
   - Who will manage weekly feature merges and conflict resolution?
   - Does this person need Nx/TypeScript expertise or just Git + soft skills?

3. **Framework versions to target:** Are we upgrading to latest react-router, react, etc.?

4. **Lazy loading strategy:** Do we lazy-load feature routes or eagerly load everything?

5. **Shared vs. feature styling:** Tailwind configuration - single or per-component?

6. **State management:** Redux, Context, Zustand? Any existing setup to consolidate?

7. **Testing approach:** Jest + RTL? Cypress? Playwright for E2E?

8. **Deployment windows:** Can we deploy during maintenance window or need blue-green?

9. **Rollback criteria:** What metrics trigger automatic rollback?

10. **Vendor communication plan:** 
    - How will you notify vendors of the consolidation?
    - If Option A, how will you handle staggered feature rollout?
    - What's the SLA for critical bug fixes during consolidation?

---

