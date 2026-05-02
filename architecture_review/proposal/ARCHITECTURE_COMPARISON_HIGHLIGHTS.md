# Architecture Comparison: Module Federation vs. Unified Single App

**Date:** April 29, 2026  
**Status:** For Discussion and Alignment

---

## 🎯 Executive Summary

Two architectural approaches have been documented for the GRIP UI consolidation:

| Approach | Document | Status | Complexity | Timeline |
|----------|----------|--------|-----------|----------|
| **Module Federation** | [ui-shell-architecture.drawio](ui-shell-architecture.drawio) | ❌ Appears to be earlier proposal | **High** | ~12+ weeks |
| **Unified Single App** | [ui-shell-unified-architecture.drawio](ui-shell-unified-architecture.drawio) + Implementation/Branding docs | ✅ **Chosen approach** | **Low** | 20 weeks + 6 weeks |

**Recommendation:** Archive the Module Federation diagram as an alternative approach and proceed with the Unified Single App architecture.

---

## 📊 Side-by-Side Comparison

### Architecture Pattern

| Aspect | Module Federation | Unified Single App |
|--------|-------------------|-------------------|
| **Pattern** | Micro-frontends (webpack federation) | Monolithic single-page app |
| **Entity Separation** | Separate MFE per entity (GRIP, ADDI, Future) | Runtime theme switching |
| **Code Organization** | Multiple independent apps | Single codebase with feature modules |
| **Dynamic Loading** | Remote modules loaded at runtime | Standard code splitting / lazy loading |

### Build & Deployment

| Aspect | Module Federation | Unified Single App |
|--------|-------------------|-------------------|
| **Build Process** | Multiple builds (shell + each MFE) | Single unified build |
| **Build Time** | Higher (multiple webpack configs) | 10-15 minutes |
| **CI/CD** | Multiple pipelines | Single pipeline |
| **Deployment** | Independent per MFE | Single deployment for all orgs |
| **Artifacts** | Multiple bundles | One optimized bundle (~900KB) |

### Developer Experience

| Aspect | Module Federation | Unified Single App |
|--------|-------------------|-------------------|
| **Local Dev** | Multiple dev servers | Single `pnpm start` |
| **Code Sharing** | Via federation config + shared deps | Direct imports with TypeScript |
| **Hot Reload** | Complex (cross-MFE changes) | Simple (standard HMR) |
| **Debugging** | Cross-boundary debugging needed | Standard debugging |
| **Onboarding** | Learn Module Federation concepts | Standard React development |

### Branding & Multi-Tenancy

| Aspect | Module Federation | Unified Single App |
|--------|-------------------|-------------------|
| **Entity Branding** | Separate MFE per entity | Runtime theme injection (JSON + CSS) |
| **New Organization** | Build + deploy new MFE | Add JSON config (~1 hour) |
| **Theme Updates** | Rebuild + redeploy MFE | Update config (instant) |
| **Org Limit** | Complex beyond ~20 entities | Scales to 100+ easily |

### Authentication & State

| Aspect | Module Federation | Unified Single App |
|--------|-------------------|-------------------|
| **Auth Context** | Shared via shell + per-MFE | Single Keycloak bootstrap |
| **State Management** | Shared state + per-MFE state | Single Redux store |
| **Routing** | Shell router + MFE sub-routers | Single React Router instance |
| **Telemetry** | Cross-boundary tracing needed | Native end-to-end tracing |

---

## 🔍 Key Architectural Highlights

### ✅ Unified Single App (Chosen Approach)

**Core Principle:** One codebase → One build → Runtime customization

```
┌─────────────────────────────────────────────────┐
│         Single Unified Application              │
│                                                 │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐      │
│  │ Catalog │  │Workspaces│  │Workflows │      │
│  │ Feature │  │ Feature  │  │ Feature  │      │
│  └─────────┘  └──────────┘  └──────────┘      │
│                                                 │
│  • Single Router                               │
│  • Single Auth Context                         │
│  • Single Redux Store                          │
│  • Runtime Theme Engine                        │
└─────────────────────────────────────────────────┘
         ↓ (10-15 min build)
┌─────────────────────────────────────────────────┐
│      Single Deployment (All 14+ Orgs)          │
└─────────────────────────────────────────────────┘
```

**Benefits:**
- ✅ **70% less complexity** than federation
- ✅ **88% faster builds** (15 min vs 2-3 hours)
- ✅ **Instant branding updates** (no rebuild)
- ✅ **Simpler maintenance** (one version to support)
- ✅ **Better performance** (optimized single bundle)
- ✅ **Standard React patterns** (easier to hire/onboard)

**Trade-offs:**
- ⚠️ All features deploy together (can't deploy independently)
- ⚠️ Larger initial bundle (mitigated by lazy loading)
- ⚠️ Must coordinate feature releases across teams

---

### ❌ Module Federation (Earlier Proposal)

**Core Principle:** Shell host → Loads remote MFEs dynamically

```
┌─────────────────────────────────────────────────┐
│         Shell Application (Host)                │
│                                                 │
│  Runtime loads:                                │
│  ↓ GRIP MFE (remote)                           │
│  ↓ ADDI MFE (remote)                           │
│  ↓ Future Entity MFEs (remotes)                │
└─────────────────────────────────────────────────┘
         ↓ (multiple builds)
┌─────────────────────────────────────────────────┐
│   Multiple Independent Deployments              │
│   (Shell + Each MFE separately)                 │
└─────────────────────────────────────────────────┘
```

**Benefits:**
- ✅ Independent deployment per MFE
- ✅ Teams can work in complete isolation
- ✅ Can version MFEs independently

**Trade-offs:**
- ⚠️ **High complexity** (webpack federation config)
- ⚠️ **Complex debugging** (cross-boundary issues)
- ⚠️ **Slower builds** (multiple webpack processes)
- ⚠️ **Runtime errors** (remote loading failures)
- ⚠️ **Difficult state sharing** (cross-MFE communication)
- ⚠️ **Hard to test** (integration testing across remotes)

---

## 🎨 Runtime Theming (Unified App Solution)

Instead of separate MFEs per entity, the unified app uses **runtime theme injection**:

### How It Works

```typescript
// 1. User authenticates → Org detected
const orgId = detectOrganization(); // from URL, token, or path

// 2. Fetch org theme
const theme = await fetch(`/api/v1/orgs/${orgId}/theme`);
// Returns: { primaryColor: '#0066cc', logoUrl: 'https://cdn.../logo.svg', ... }

// 3. Apply theme dynamically
document.documentElement.style.setProperty('--primary-color', theme.primaryColor);
document.getElementById('logo').src = theme.logoUrl;
localStorage.setItem('currentTheme', JSON.stringify(theme));

// 4. Theme persists across navigation
// All features (catalog, workspaces, workflows) see same theme
```

### Comparison: Build-Time vs Runtime Theming

| Aspect | Build-Time (Current) | Runtime (Target) |
|--------|---------------------|------------------|
| **Builds per release** | 14 separate builds | 1 build |
| **Build time** | 2-3 hours | 10-15 minutes |
| **Theme update** | Code change → Rebuild → Deploy | API call → Instant |
| **New organization** | 3-5 days | <1 hour |
| **Infrastructure** | 14 containers | 1 shared container |

---

## 📋 Implementation Status

### Phase 1: CRA → Nx Migration ✓ (Weeks 3-6)
- Move Workspaces_UI from separate repo into Catalog monorepo
- Convert from Create React App to Nx workspace
- Consolidate dependencies (React, React-Router, Redux)

### Phase 2: Feature Integration (Weeks 7-14)
- Extract Workflows from iframe → native React component
- Merge Workspaces feature into unified router
- Consolidate auth context (single Keycloak)
- Merge shared components

### Phase 3: Build System Simplification (Weeks 15-16)
- **Remove Module Federation config entirely**
- Single CI/CD pipeline
- Single deployment model

### Phase 4: Testing (Weeks 17-19)
- Unit, integration, E2E tests
- Performance validation
- Feature parity verification

### Phase 5: Deployment (Week 20)
- Blue-green deployment
- Documentation
- Team training

### Then: Runtime Branding (6 additional weeks)
- Theme API backend
- Frontend theme engine
- Migrate existing 14 themes to JSON configs
- Admin portal for self-service branding

**Total: 26 weeks (20 consolidation + 6 branding)**

---

## 🚨 Critical Decision Points

### 1. Archive Module Federation Diagram?

**Recommendation:** Yes
- It represents an earlier architectural proposal
- The team has chosen the simpler unified approach
- Keeping it causes confusion about the target architecture

**Suggested Action:**
```
Rename: ui-shell-architecture.drawio → ui-shell-architecture-REJECTED-federation-approach.drawio
Add note: "This was an earlier proposal. See ui-shell-unified-architecture.drawio for chosen approach"
```

### 2. Update High-Level Architecture Diagram?

**Current:** [to-be-architecture.drawio](to-be-architecture.drawio) is somewhat ambiguous  
**Issue:** "Multi-Entity Shell Application" could mean either approach

**Recommendation:** Add clarification note
- "Shell Application = Single unified React app (not Module Federation)"
- Link to detailed unified architecture diagram

### 3. Align Team Communication

**Problem:** Different documents showing different architectures causes confusion

**Action Items:**
- [ ] Team meeting: Present both diagrams side-by-side
- [ ] Explain why federation was considered but rejected
- [ ] Confirm unified approach is the target
- [ ] Archive federation diagram with clear "REJECTED" label
- [ ] Update any presentation decks or wikis

---

## 💡 Recommendations for Discussion

### For Stakeholders (Neptali, Andrew, Tech Lead)

**Question 1:** Are we aligned that the unified single app (not Module Federation) is the target?
- If yes → Archive federation diagram, proceed with implementation plan
- If no → Need to revisit architectural decision

**Question 2:** Should we communicate this architectural choice to vendors?
- They may have expectations about independent deployments
- Unified approach means all features deploy together

**Question 3:** What's our risk tolerance for the 20-week consolidation timeline?
- Option A: Allow vendor features during consolidation (weekly merges, higher risk)
- Option B: Feature freeze during consolidation (simpler, but vendor pushback)

### For Development Team

**Question 1:** Does everyone understand why Module Federation was rejected?
- Complexity vs. benefit analysis
- Runtime theming achieves same multi-tenancy goals

**Question 2:** Are we comfortable with the Nx monorepo approach?
- Need Nx expertise on team
- Training for developers unfamiliar with Nx

**Question 3:** How will we handle the CRA → Nx migration for Workspaces_UI?
- This is a prerequisite for consolidation
- 4 weeks of work with some risk

---

## 📚 Related Documents

| Document | Purpose | Status |
|----------|---------|--------|
| [to-be-architecture.drawio](to-be-architecture.drawio) | High-level target architecture | Needs clarification |
| [ui-shell-architecture.drawio](ui-shell-architecture.drawio) | Module Federation approach | ❌ Should be archived |
| [ui-shell-unified-architecture.drawio](ui-shell-unified-architecture.drawio) | ✅ Chosen unified approach | Current target |
| [UI_CONSOLIDATION_IMPLEMENTATION_PLAN.md](temp/UI_CONSOLIDATION_IMPLEMENTATION_PLAN.md) | 20-week consolidation plan | Active |
| [BRANDING_SOLUTION_SIMPLIFIED_POSTCONSOLIDATION.md](temp/BRANDING_SOLUTION_SIMPLIFIED_POSTCONSOLIDATION.md) | Runtime theming (6 weeks) | After consolidation |

---

## 🎬 Next Steps

### Immediate (This Week)
1. **Review this comparison** with tech lead and stakeholders
2. **Confirm architectural choice** (unified app, not federation)
3. **Archive federation diagram** with clear label
4. **Update presentations/docs** to reference unified architecture only

### Short Term (Next 2 Weeks)
5. **Begin Phase 0 analysis** from consolidation plan
6. **Create branch strategy** for parallel feature development
7. **Allocate team** (2-3 consolidation + 1-2 vendor features)
8. **Set up weekly sync** between consolidation and vendor teams

### Long Term (Weeks 3-26)
9. **Execute consolidation plan** (20 weeks)
10. **Implement runtime branding** (6 weeks)
11. **Deploy to production** with blue-green strategy
12. **Celebrate** 🎉 (70% complexity reduction achieved!)

---

## ✅ Success Criteria

The unified single app architecture is successfully implemented when:

- [ ] Single codebase in Catalog monorepo
- [ ] Single `pnpm start` command for local development
- [ ] Single build output (~900KB, optimized)
- [ ] Single CI/CD pipeline (10-15 min builds)
- [ ] Single deployment for all 14+ organizations
- [ ] Runtime theme switching working (instant updates)
- [ ] Zero Module Federation artifacts remaining
- [ ] All catalog, workspaces, workflows features working
- [ ] End-to-end telemetry tracing across all features
- [ ] Documentation updated and team trained

---

**Questions? Concerns? Suggestions?**  
This is the moment to surface them before we commit to the 26-week implementation journey.
