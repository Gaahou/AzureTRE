# Phase 0 & Phase 1: Private Endpoint Consolidation - ADO Work Items

## Structure

```
Epic: Private Endpoint Cost Optimization Initiative
  ├─ Feature: Phase 0 - Initial Assessment & Validation
  │    ├─ User Story 1: Current State Inventory
  │    ├─ User Story 2: Option #1 - Storage PE Consolidation Technical Validation
  │    ├─ User Story 3: Option #2 - Core AMPLS Network Path Assessment
  │    └─ User Story 4: Option #3b - Airlock Consolidation Code Review
  │
  └─ Feature: Phase 1 - Technical Validation
       ├─ User Story 1: Option #1 - Validate Azure Multi-Subresource PE Feature Support
       ├─ User Story 2: Option #2 - Validate Network Path from Workspaces to Core AMPLS
       └─ User Story 3: Option #3b - Deep Code Analysis of Airlock Processor Dependencies
```

---

## Epic

**Title:** Private Endpoint Cost Optimization Initiative

**Description:**
```html
<h3>Overview</h3>
<p>Reduce Azure TRE infrastructure costs by consolidating Private Endpoints across workspaces while maintaining security posture and compliance requirements.</p>

<h3>Business Value</h3>
<ul>
  <li><strong>Annual Savings:</strong> $129,600/year at 500 workspaces</li>
  <li><strong>Per Workspace Savings:</strong> $21.60/month</li>
  <li><strong>Security Impact:</strong> None - maintains Private Link and network isolation</li>
  <li><strong>Compliance Impact:</strong> None - meets all regulatory requirements</li>
</ul>

<h3>Scope</h3>
<p>This initiative covers three optimization approaches:</p>
<ol>
  <li><strong>Storage PE Consolidation:</strong> Reduce 3 PEs to 1 per workspace ($86K/year savings)</li>
  <li><strong>Core AMPLS:</strong> Use shared AMPLS instead of per-workspace ($43K/year savings)</li>
  <li><strong>Airlock Consolidation:</strong> Reduce 5 storage accounts to 1 ($173K/year savings)</li>
</ol>

<h3>Timeline</h3>
<p>12-14 weeks from initial assessment to full production rollout</p>

<h3>Success Criteria</h3>
<ul>
  <li>100% of workspaces migrated successfully</li>
  <li>Zero data loss incidents</li>
  <li>Performance within 10% of baseline</li>
  <li>Cost savings realized as projected</li>
  <li>Security and compliance requirements maintained</li>
</ul>
```

**Acceptance Criteria:**
- All phases completed successfully
- Cost savings validated
- Security posture maintained
- Documentation complete
- Operations team trained

---

## Feature

**Title:** Phase 0 - Initial Assessment & Validation

**Description:**
```html
<h3>Purpose</h3>
<p>Conduct initial technical assessment to validate feasibility and document current state before implementing Private Endpoint consolidation changes.</p>

<h3>Goals</h3>
<ul>
  <li>Document current Private Endpoint inventory and costs</li>
  <li>Validate Azure feature support for multi-subresource PEs</li>
  <li>Assess network connectivity for Core AMPLS approach</li>
  <li>Review airlock processor code for consolidation feasibility</li>
  <li>Confirm projected cost savings</li>
</ul>

<h3>Duration</h3>
<p>1 week (2-3 days)</p>

<h3>Dependencies</h3>
<ul>
  <li>Access to production TRE environment (read-only)</li>
  <li>Access to Azure Portal and CLI</li>
  <li>Access to Terraform codebase</li>
  <li>Access to cost reporting tools</li>
</ul>

<h3>Outputs</h3>
<ul>
  <li>Current state inventory document</li>
  <li>Technical feasibility assessment for each option</li>
  <li>Validated cost savings projections</li>
  <li>Go/No-Go recommendation for each option</li>
</ul>
```

**Acceptance Criteria:**
- [ ] Current state fully documented
- [ ] All three options technically validated
- [ ] Cost projections confirmed
- [ ] Risks identified and documented
- [ ] Stakeholder approval to proceed to Phase 1

---

## User Stories

### User Story 1: Current State Inventory

**Title:** Document Current Private Endpoint Configuration and Costs

**Description:**
```html
<h3>As a</h3>
<p>TRE Architect</p>

<h3>I want to</h3>
<p>Document the current Private Endpoint inventory across all workspaces and calculate actual costs</p>

<h3>So that</h3>
<p>I can establish a baseline for comparison and validate projected cost savings</p>

<h3>Background</h3>
<p>Before implementing any changes, we need a clear understanding of:</p>
<ul>
  <li>How many workspaces exist and their configurations</li>
  <li>How many Private Endpoints are deployed per workspace</li>
  <li>Current monthly costs for Private Endpoints</li>
  <li>Which workspaces have airlock enabled</li>
</ul>

<h3>Tasks</h3>
<ol>
  <li><strong>Count Existing Workspaces</strong>
    <ul>
      <li>Query Azure to get total workspace count</li>
      <li>Identify workspaces with airlock enabled</li>
      <li>Document workspace types (dev, test, prod)</li>
    </ul>
  </li>
  <li><strong>Inventory Private Endpoints</strong>
    <ul>
      <li>For 5 sample workspaces, list all Private Endpoints</li>
      <li>Categorize by type (storage blob, file, dfs, AMPLS, airlock)</li>
      <li>Validate against expected counts from architecture docs</li>
    </ul>
  </li>
  <li><strong>Analyze Current Costs</strong>
    <ul>
      <li>Pull Private Endpoint costs from last 30 days</li>
      <li>Calculate average monthly cost</li>
      <li>Project annual cost at current scale</li>
    </ul>
  </li>
  <li><strong>Calculate Projected Savings</strong>
    <ul>
      <li>Option #1: 2 PEs removed per workspace × $7.20/mo</li>
      <li>Option #2: 1 PE removed per workspace × $7.20/mo</li>
      <li>Option #3b: 4 PEs removed per airlock workspace × $7.20/mo</li>
      <li>Total projected annual savings</li>
    </ul>
  </li>
</ol>
```

**Acceptance Criteria:**
```html
<ul>
  <li>Total workspace count documented</li>
  <li>Workspaces with airlock identified (count and list)</li>
  <li>Current PE inventory complete for sample workspaces</li>
  <li>Average PEs per workspace calculated: ____ (expected: 5-10)</li>
  <li>Current monthly PE cost documented: $____</li>
  <li>Projected monthly savings calculated: $____ (expected: ~$10,800)</li>
  <li>Projected annual savings calculated: $____ (expected: ~$129,600)</li>
  <li>Findings documented in: <code>architecture_review/phase0-current-state.md</code></li>
</ul>
```

**Effort:** 4 hours  
**Priority:** High  
**Tags:** Phase0, Assessment, Documentation

---

### User Story 2: Option #1 - Storage PE Consolidation Technical Validation

**Title:** Validate Azure Multi-Subresource Private Endpoint Support

**Description:**
```html
<h3>As a</h3>
<p>TRE Platform Engineer</p>

<h3>I want to</h3>
<p>Verify that Azure supports multiple subresources (blob, file, dfs) on a single Private Endpoint</p>

<h3>So that</h3>
<p>I can confidently proceed with consolidating 3 storage PEs into 1 PE per workspace</p>

<h3>Background</h3>
<p>Option #1 proposes consolidating the 3 separate Private Endpoints for workspace storage (blob, file, dfs) into a single PE with multiple <code>private_service_connection</code> blocks.</p>

<p><strong>Expected Savings:</strong> $14.40/mo per workspace = $86,400/year at 500 workspaces</p>

<h3>Tasks</h3>
<ol>
  <li><strong>Review Azure Documentation</strong>
    <ul>
      <li>Read: <a href="https://learn.microsoft.com/en-us/azure/storage/common/storage-private-endpoints">Azure Storage Private Endpoints</a></li>
      <li>Confirm: Multiple <code>private_service_connection</code> blocks supported</li>
      <li>Check: Any regional or SKU limitations</li>
      <li>Check: Any known issues or caveats</li>
    </ul>
  </li>
  <li><strong>Verify Terraform Provider Support</strong>
    <ul>
      <li>Check current <code>azurerm</code> provider version in workspace template</li>
      <li>Required version: >= 3.0</li>
      <li>Review provider changelog for any breaking changes</li>
      <li>Find example in Terraform registry showing multiple connections</li>
    </ul>
  </li>
  <li><strong>Review Current Implementation</strong>
    <ul>
      <li>Examine: <code>templates/workspaces/base/terraform/storage.tf</code></li>
      <li>Document current 3 separate PE resources</li>
      <li>Identify all dependencies on these PEs</li>
      <li>Check DNS zone configuration</li>
    </ul>
  </li>
  <li><strong>Create Feasibility Assessment</strong>
    <ul>
      <li>Document findings (supported/not supported)</li>
      <li>Identify any blockers</li>
      <li>Estimate implementation complexity: Low/Medium/High</li>
      <li>Provide Go/No-Go recommendation</li>
    </ul>
  </li>
</ol>
```

**Acceptance Criteria:**
```html
<ul>
  <li>Azure documentation confirms multi-subresource PE support: ✅/❌</li>
  <li>Terraform provider version documented: v____</li>
  <li>Provider supports multiple <code>private_service_connection</code> blocks: ✅/❌</li>
  <li>Current implementation analyzed and documented</li>
  <li>No blockers identified OR blockers documented with mitigation plan</li>
  <li>Complexity assessment: ____ (Low/Medium/High)</li>
  <li>Recommendation: GO / NO-GO / GO-WITH-CONDITIONS</li>
  <li>Findings documented in: <code>architecture_review/phase0-option1-validation.md</code></li>
</ul>
```

**Effort:** 3 hours  
**Priority:** High  
**Tags:** Phase0, Option1, Storage, TechnicalValidation

---

### User Story 3: Option #2 - Core AMPLS Network Path Assessment

**Title:** Validate Network Connectivity from Workspaces to Core AMPLS

**Description:**
```html
<h3>As a</h3>
<p>TRE Network Engineer</p>

<h3>I want to</h3>
<p>Verify that workspace VNETs can reach the Core AMPLS Private Endpoint for Azure Monitor ingestion</p>

<h3>So that</h3>
<p>I can determine if we can remove per-workspace AMPLS Private Endpoints and use the shared Core AMPLS instead</p>

<h3>Background</h3>
<p>Option #2 proposes removing the per-workspace AMPLS Private Endpoint and having all workspace Log Analytics Workspaces link to the Core AMPLS instead.</p>

<p><strong>Expected Savings:</strong> $7.20/mo per workspace = $43,200/year at 500 workspaces</p>

<h3>Tasks</h3>
<ol>
  <li><strong>Identify Core AMPLS Resource</strong>
    <ul>
      <li>Find Core AMPLS resource: <code>ampls-{TRE_ID}</code></li>
      <li>Get resource ID and location</li>
      <li>Identify associated Private Endpoint</li>
      <li>Document private IP address</li>
    </ul>
  </li>
  <li><strong>Check AMPLS Capacity</strong>
    <ul>
      <li>Query current linked resources count</li>
      <li>AMPLS limit: 300 resources per AMPLS</li>
      <li>Calculate: How many AMPLS needed for 500 workspaces?</li>
      <li>Plan: Single AMPLS vs. multiple (e.g., 1 per 250 workspaces)</li>
    </ul>
  </li>
  <li><strong>Verify Network Connectivity</strong>
    <ul>
      <li>Check VNET peering: workspace VNET ↔ Core VNET</li>
      <li>Verify peering state: Connected</li>
      <li>Check peering settings: Allow forwarded traffic enabled</li>
      <li>Review NSG rules: workspace → Core SharedSubnet on port 443</li>
    </ul>
  </li>
  <li><strong>Validate DNS Configuration</strong>
    <ul>
      <li>Check if workspace VNETs have DNS link to Core private DNS zones</li>
      <li>Verify DNS zones for Azure Monitor: <code>privatelink.ods.opinsights.azure.com</code>, etc.</li>
      <li>Confirm workspace VMs can resolve Core AMPLS endpoints</li>
    </ul>
  </li>
  <li><strong>Test Connectivity (if possible in dev)</strong>
    <ul>
      <li>From workspace VM: <code>curl</code> Core AMPLS endpoint</li>
      <li>Verify route: workspace → Core VNET → AMPLS PE</li>
      <li>Check latency and connectivity</li>
    </ul>
  </li>
</ol>
```

**Acceptance Criteria:**
```html
<ul>
  <li>Core AMPLS identified: <code>ampls-{TRE_ID}</code> ✅</li>
  <li>Core AMPLS capacity checked: ____ current resources / 300 limit</li>
  <li>Capacity plan for 500 workspaces: ____ AMPLS resources needed</li>
  <li>VNET peering validated: Connected and configured correctly ✅/❌</li>
  <li>NSG rules allow traffic: workspace → Core SharedSubnet:443 ✅/❌</li>
  <li>DNS configuration validated: workspace can resolve Core AMPLS ✅/❌</li>
  <li>Test connectivity successful (if tested): ✅/❌/N/A</li>
  <li>No network blockers identified OR blockers documented with mitigation</li>
  <li>Recommendation: GO / NO-GO / GO-WITH-CONDITIONS</li>
  <li>Findings documented in: <code>architecture_review/phase0-option2-validation.md</code></li>
</ul>
```

**Effort:** 4 hours  
**Priority:** High  
**Tags:** Phase0, Option2, AMPLS, Networking, TechnicalValidation

---

### User Story 4: Option #3b - Airlock Consolidation Code Review

**Title:** Analyze Airlock Processor for Storage Account Consolidation Feasibility

**Description:**
```html
<h3>As a</h3>
<p>TRE Application Developer</p>

<h3>I want to</h3>
<p>Review the airlock processor code to understand dependencies on separate storage accounts</p>

<h3>So that</h3>
<p>I can determine the effort required to consolidate 5 airlock storage accounts into 1 account with 5 containers</p>

<h3>Background</h3>
<p>Option #3b proposes consolidating the 5 separate airlock storage accounts (import-approved, export-internal, export-inprogress, export-rejected, export-blocked) into a single storage account with 5 containers.</p>

<p><strong>Expected Savings:</strong> $28.80/mo per airlock workspace = $172,800/year at 500 workspaces (assuming 50% have airlock)</p>

<h3>Tasks</h3>
<ol>
  <li><strong>Locate Airlock Processor Code</strong>
    <ul>
      <li>Find processor implementation: Python/C#/.NET</li>
      <li>Identify event handlers for storage events</li>
      <li>Document code location and language</li>
    </ul>
  </li>
  <li><strong>Review Storage Account References</strong>
    <ul>
      <li>Search for storage account name references in code</li>
      <li>Are account names hard-coded or from config/env vars?</li>
      <li>How does processor distinguish between 5 accounts?</li>
      <li>Does logic rely on account-level properties?</li>
    </ul>
  </li>
  <li><strong>Review EventGrid Subscriptions</strong>
    <ul>
      <li>Examine: <code>templates/workspaces/base/terraform/airlock/storage_accounts.tf</code></li>
      <li>How are EventGrid subscriptions configured?</li>
      <li>Do they filter by storage account or could they filter by container?</li>
      <li>Check if <code>subjectBeginsWith</code> filter can target container path</li>
    </ul>
  </li>
  <li><strong>Analyze Blob Path Parsing</strong>
    <ul>
      <li>Find event handler that processes blob created events</li>
      <li>Does it parse blob URL to extract container name?</li>
      <li>Does it extract storage account name?</li>
      <li>Can logic be modified to route based on container instead of account?</li>
    </ul>
  </li>
  <li><strong>Review RBAC Configuration</strong>
    <ul>
      <li>How is RBAC currently assigned? (account-level or container-level)</li>
      <li>Does Azure support container-scoped RBAC?</li>
      <li>Can workspace Managed Identity be scoped to specific containers?</li>
    </ul>
  </li>
  <li><strong>Estimate Code Changes</strong>
    <ul>
      <li>List specific code files that need modification</li>
      <li>Estimate lines of code to change</li>
      <li>Identify test cases that need updating</li>
      <li>Estimate effort in hours/days</li>
    </ul>
  </li>
</ol>
```

**Acceptance Criteria:**
```html
<ul>
  <li>Airlock processor code located and documented: <code>____</code></li>
  <li>Storage account dependency analysis complete</li>
  <li>EventGrid filtering approach documented (account vs. container): ____</li>
  <li>Container-based filtering feasible: ✅/❌</li>
  <li>Code changes required identified and documented</li>
  <li>Estimated effort: ____ hours/days</li>
  <li>RBAC scoping to containers feasible: ✅/❌</li>
  <li>No blockers identified OR blockers documented with mitigation</li>
  <li>Complexity assessment: Low / Medium / High</li>
  <li>Recommendation: GO / NO-GO / GO-WITH-CONDITIONS</li>
  <li>Findings documented in: <code>architecture_review/phase0-option3b-validation.md</code></li>
</ul>
```

**Effort:** 6 hours  
**Priority:** High  
**Tags:** Phase0, Option3b, Airlock, CodeReview, TechnicalValidation

---

---

# Phase 1: Technical Validation - ADO Work Items

## Feature

**Title:** Phase 1 - Technical Validation

**Description:**
```html
<h3>Purpose</h3>
<p>Conduct detailed technical validation of Azure features, network paths, and code dependencies for all three Private Endpoint consolidation options.</p>

<h3>Goals</h3>
<ul>
  <li>Verify Azure supports multi-subresource Private Endpoints for storage</li>
  <li>Validate workspace VNETs can reach Core AMPLS over peered network</li>
  <li>Analyze airlock processor code dependencies on storage accounts</li>
  <li>Confirm no technical blockers exist for any option</li>
  <li>Provide Go/No-Go recommendation for each option</li>
</ul>

<h3>Duration</h3>
<p>1-2 weeks</p>

<h3>Dependencies</h3>
<ul>
  <li>Phase 0 complete (current state documented)</li>
  <li>Access to Azure documentation and Terraform provider docs</li>
  <li>Access to production TRE environment for validation</li>
  <li>Access to airlock processor source code</li>
</ul>

<h3>Outputs</h3>
<ul>
  <li>Azure feature support confirmation for each option</li>
  <li>Network connectivity validation results</li>
  <li>Code dependency analysis for airlock consolidation</li>
  <li>Technical feasibility report for each option</li>
  <li>Go/No-Go decision for proceeding to Phase 2</li>
</ul>
```

**Acceptance Criteria:**
- [ ] Azure feature validation complete for all options
- [ ] Network connectivity validated and documented
- [ ] Code dependencies fully analyzed
- [ ] Technical feasibility reports completed for each option
- [ ] Clear Go/No-Go recommendations provided
- [ ] Stakeholder approval to proceed to Phase 2 (Prototype Development)

---

## User Stories

### User Story 1: Option #1 - Validate Azure Multi-Subresource PE Feature Support

**Title:** Option #1: Validate Azure Multi-Subresource Private Endpoint Feature Support

**Description:**
```html
<h3>As a</h3>
<p>TRE Platform Engineer</p>

<h3>I want to</h3>
<p>Verify in detail that Azure supports multiple subresources on a single Private Endpoint and validate Terraform provider compatibility</p>

<h3>So that</h3>
<p>I can confirm Option #1 (Storage PE consolidation) is technically feasible before prototyping</p>

<h3>Background</h3>
<p>This is deeper validation than Phase 0. We need to verify specific Terraform syntax, check for any hidden limitations, and confirm the feature works in our region/subscription.</p>

<p><strong>Savings:</strong> $86,400/year at 500 workspaces</p>

<h3>Tasks</h3>
<ol>
  <li><strong>Review Azure Documentation in Detail</strong>
    <ul>
      <li>Read complete Azure Storage Private Endpoints documentation</li>
      <li>Check for any regional availability limitations</li>
      <li>Verify feature is GA (not preview)</li>
      <li>Check for any known issues or caveats in release notes</li>
      <li>Confirm pricing model (1 PE vs 3 PEs)</li>
    </ul>
  </li>
  <li><strong>Verify Terraform Provider Compatibility</strong>
    <ul>
      <li>Check current azurerm provider version in workspace template: <code>grep required_providers versions.tf</code></li>
      <li>Verify version >= 3.0 (required for multiple connections)</li>
      <li>Review Terraform provider changelog for relevant updates</li>
      <li>Find working example in Terraform registry with multiple private_service_connection blocks</li>
    </ul>
  </li>
  <li><strong>Review Current Terraform Implementation</strong>
    <ul>
      <li>Analyze templates/workspaces/base/terraform/storage.tf in detail</li>
      <li>Document all 3 current PE resources and their configurations</li>
      <li>Map all resources that have depends_on referencing storage PEs</li>
      <li>Identify all outputs that reference PE IDs or private IPs</li>
      <li>Check if any workspace services hard-code PE names</li>
    </ul>
  </li>
  <li><strong>Validate DNS Zone Configuration</strong>
    <ul>
      <li>Verify 3 private DNS zones exist: privatelink.blob.core.windows.net, privatelink.file.core.windows.net, privatelink.dfs.core.windows.net</li>
      <li>Confirm DNS zones are linked to workspace VNETs</li>
      <li>Check if private_dns_zone_group can reference multiple zones</li>
      <li>Verify no conflicts with existing DNS records</li>
    </ul>
  </li>
  <li><strong>Create Feasibility Report</strong>
    <ul>
      <li>Document all findings in architecture_review/phase1-option1-detailed-validation.md</li>
      <li>List any blockers or limitations discovered</li>
      <li>Assess complexity: Low/Medium/High</li>
      <li>Provide clear Go/No-Go recommendation with justification</li>
    </ul>
  </li>
</ol>
```

**Acceptance Criteria:**
```html
<ul>
  <li>Azure documentation confirms multi-subresource PE support (GA, not preview)</li>
  <li>No regional or subscription limitations found</li>
  <li>Terraform provider version documented and compatible (>= 3.0)</li>
  <li>Working Terraform example found in registry with multiple connections</li>
  <li>Current implementation fully analyzed (3 PEs, dependencies, outputs)</li>
  <li>All dependency chains documented</li>
  <li>DNS zone configuration validated (3 zones, VNET links confirmed)</li>
  <li>private_dns_zone_group supports multiple zones: YES/NO</li>
  <li>No technical blockers identified OR blockers documented with mitigation plan</li>
  <li>Complexity assessment: Low/Medium/High</li>
  <li>Clear recommendation: GO / NO-GO / GO-WITH-CONDITIONS</li>
  <li>Detailed findings documented in: <code>architecture_review/phase1-option1-detailed-validation.md</code></li>
</ul>
```

**Effort:** 5 Story Points  
**Priority:** High  
**Tags:** Phase1, Option1, Storage, TechnicalValidation

---

### User Story 2: Option #2 - Validate Network Path from Workspaces to Core AMPLS

**Title:** Option #2: Validate Network Path from Workspaces to Core AMPLS

**Description:**
```html
<h3>As a</h3>
<p>TRE Network Engineer</p>

<h3>I want to</h3>
<p>Thoroughly validate network connectivity from workspace VNETs to Core AMPLS and test actual Log Analytics ingestion</p>

<h3>So that</h3>
<p>I can confirm Option #2 (Core AMPLS) is technically feasible and will work in production</p>

<h3>Background</h3>
<p>This is deeper validation than Phase 0. We need to verify actual network paths, test real connectivity, check AMPLS capacity limits, and ensure NSG/routing rules allow the traffic.</p>

<p><strong>Savings:</strong> $43,200/year at 500 workspaces</p>

<h3>Tasks</h3>
<ol>
  <li><strong>Identify and Document Core AMPLS Infrastructure</strong>
    <ul>
      <li>Find Core AMPLS resource: <code>az monitor private-link-scope list --resource-group rg-{TRE_ID}</code></li>
      <li>Document AMPLS resource ID, name, location</li>
      <li>Get Core AMPLS Private Endpoint details and private IP</li>
      <li>Identify which subnet the PE is in (should be SharedSubnet)</li>
      <li>Document all currently linked resources</li>
    </ul>
  </li>
  <li><strong>Validate AMPLS Capacity and Scaling</strong>
    <ul>
      <li>Query current linked resource count: <code>az monitor private-link-scope scoped-resource list</code></li>
      <li>AMPLS limit is 300 resources per AMPLS instance</li>
      <li>Calculate: 500 workspaces need how many AMPLS? (500/300 = 2 AMPLS minimum)</li>
      <li>Plan architecture: Single AMPLS or multiple (shard by workspace ranges)</li>
      <li>Document capacity planning strategy</li>
    </ul>
  </li>
  <li><strong>Test Network Connectivity End-to-End</strong>
    <ul>
      <li>Verify VNET peering exists: workspace VNET ↔ Core VNET</li>
      <li>Check peering state is Connected and allow forwarded traffic enabled</li>
      <li>Review NSG rules: workspace → Core SharedSubnet on port 443</li>
      <li>Test from workspace VM: <code>curl -v https://[AMPLS-PE-IP]:443</code> or <code>Test-NetConnection</code></li>
      <li>Verify route table: workspace traffic routes to Core VNET</li>
      <li>Check if any firewall rules block the path</li>
    </ul>
  </li>
  <li><strong>Validate DNS Configuration</strong>
    <ul>
      <li>Verify workspace VNETs have DNS links to Core private DNS zones</li>
      <li>Check DNS zones: privatelink.ods.opinsights.azure.com, privatelink.oms.opinsights.azure.com, privatelink.agentsvc.azure-automation.net</li>
      <li>Test DNS resolution from workspace VM: <code>nslookup *.ods.opinsights.azure.com</code></li>
      <li>Confirm resolves to Core AMPLS private IP (not public IP)</li>
    </ul>
  </li>
  <li><strong>Test Log Analytics Ingestion (if possible)</strong>
    <ul>
      <li>If dev environment available: create test workspace using Core AMPLS</li>
      <li>Generate sample logs from workspace VM</li>
      <li>Verify logs appear in Log Analytics workspace</li>
      <li>Measure ingestion latency</li>
      <li>Check for any errors in Azure Monitor diagnostics</li>
    </ul>
  </li>
  <li><strong>Create Feasibility Report</strong>
    <ul>
      <li>Document all findings in architecture_review/phase1-option2-detailed-validation.md</li>
      <li>Include network diagrams showing the path</li>
      <li>List any blockers or performance concerns</li>
      <li>Provide capacity plan for 500 workspaces</li>
      <li>Clear Go/No-Go recommendation</li>
    </ul>
  </li>
</ol>
```

**Acceptance Criteria:**
```html
<ul>
  <li>Core AMPLS identified and documented (resource ID, PE details, private IP)</li>
  <li>Current AMPLS capacity checked: ____ resources / 300 limit</li>
  <li>Capacity plan for 500 workspaces documented (need ____ AMPLS instances)</li>
  <li>VNET peering validated: Connected, forwarded traffic enabled</li>
  <li>NSG rules validated: workspace → Core SharedSubnet:443 allowed</li>
  <li>Network connectivity tested: workspace VM can reach Core AMPLS PE</li>
  <li>DNS resolution validated: workspace VMs resolve Azure Monitor endpoints to Core AMPLS private IP</li>
  <li>All required private DNS zones identified and linked</li>
  <li>Log Analytics ingestion tested (if dev environment available): YES/NO</li>
  <li>Ingestion latency measured: ____ seconds (if tested)</li>
  <li>No network blockers identified OR blockers documented with mitigation</li>
  <li>Network path diagram created</li>
  <li>Recommendation: GO / NO-GO / GO-WITH-CONDITIONS</li>
  <li>Detailed findings documented in: <code>architecture_review/phase1-option2-detailed-validation.md</code></li>
</ul>
```

**Effort:** 8 Story Points  
**Priority:** High  
**Tags:** Phase1, Option2, AMPLS, Networking, TechnicalValidation

---

### User Story 3: Option #3b - Deep Code Analysis of Airlock Processor Dependencies

**Title:** Option #3b: Deep Code Analysis of Airlock Processor Dependencies

**Description:**
```html
<h3>As a</h3>
<p>TRE Application Developer</p>

<h3>I want to</h3>
<p>Perform comprehensive code analysis of the airlock processor to understand all storage account dependencies and estimate refactoring effort</p>

<h3>So that</h3>
<p>I can confirm Option #3b (Airlock consolidation) is feasible and provide accurate effort estimates</p>

<h3>Background</h3>
<p>This is deeper analysis than Phase 0. We need to trace through the entire airlock codebase, understand event handling logic, identify all storage account references, and estimate the full scope of code changes required.</p>

<p><strong>Savings:</strong> $172,800/year at 500 workspaces (50% with airlock)</p>

<h3>Tasks</h3>
<ol>
  <li><strong>Locate and Map Airlock Processor Architecture</strong>
    <ul>
      <li>Find all airlock processor code files: <code>find . -type f -name "*airlock*" -o -name "*processor*"</code></li>
      <li>Identify language/framework (Python/C#/.NET/other)</li>
      <li>Map component architecture (event handlers, storage clients, routing logic)</li>
      <li>Document dependencies (SDKs, libraries, frameworks)</li>
      <li>Create architecture diagram showing data flow</li>
    </ul>
  </li>
  <li><strong>Analyze Storage Account References</strong>
    <ul>
      <li>Search for storage account name references: <code>grep -r "storage.*account" core/terraform/airlock/</code></li>
      <li>Identify how account names are configured (hardcoded/env vars/config file)</li>
      <li>Trace how 5 account names are currently used in code</li>
      <li>Check if code logic depends on account names or just connection strings</li>
      <li>Document all places where account names appear</li>
    </ul>
  </li>
  <li><strong>Deep Dive into EventGrid Integration</strong>
    <ul>
      <li>Examine EventGrid subscription configuration in templates/workspaces/base/terraform/airlock/storage_accounts.tf</li>
      <li>Document current filtering approach (by storage account)</li>
      <li>Analyze event payload structure and what fields are available</li>
      <li>Verify EventGrid supports subjectBeginsWith filter for container paths</li>
      <li>Test filter syntax: <code>/blobServices/default/containers/[container-name]/</code></li>
      <li>Check if existing event handler code extracts blob URL correctly</li>
    </ul>
  </li>
  <li><strong>Analyze Blob Path Parsing Logic</strong>
    <ul>
      <li>Find event handler that processes Microsoft.Storage.BlobCreated events</li>
      <li>Trace code that parses blob URL/path from event payload</li>
      <li>Check if container name is currently extracted</li>
      <li>Document blob URL format: https://[account].blob.core.windows.net/[container]/[path]</li>
      <li>Verify code can be modified to route based on container vs account</li>
      <li>Identify any assumptions that would break with container-based approach</li>
    </ul>
  </li>
  <li><strong>Review RBAC and Access Control</strong>
    <ul>
      <li>Document current RBAC assignments in Terraform (account-level vs container-level)</li>
      <li>Research: Does Azure support container-scoped RBAC for Managed Identity? Check Azure documentation</li>
      <li>Test RBAC scope in dev if possible: assign role to container only</li>
      <li>Identify if current code uses account keys (bad) or Managed Identity (good)</li>
      <li>Document access control changes needed</li>
    </ul>
  </li>
  <li><strong>Estimate Code Changes and Test Impact</strong>
    <ul>
      <li>List all files that need modification (with line numbers)</li>
      <li>Estimate lines of code to add/modify/delete</li>
      <li>Identify all unit tests that need updating</li>
      <li>Estimate integration test changes needed</li>
      <li>Calculate effort in hours: [files × complexity × risk factor]</li>
      <li>Create change impact matrix: Low/Medium/High risk per file</li>
    </ul>
  </li>
  <li><strong>Create Detailed Feasibility Report</strong>
    <ul>
      <li>Document findings in architecture_review/phase1-option3b-detailed-validation.md</li>
      <li>Include code snippets showing key dependencies</li>
      <li>Provide detailed refactoring plan with estimated effort</li>
      <li>List all risks and mitigation strategies</li>
      <li>Assess complexity: Low/Medium/High with justification</li>
      <li>Clear Go/No-Go recommendation</li>
    </ul>
  </li>
</ol>
```

**Acceptance Criteria:**
```html
<ul>
  <li>Airlock processor architecture mapped and documented</li>
  <li>All code files identified with language/framework noted</li>
  <li>Architecture diagram created showing event flow</li>
  <li>Storage account references catalogued (all occurrences documented)</li>
  <li>Configuration approach documented (env vars/config files/hardcoded)</li>
  <li>EventGrid integration fully analyzed</li>
  <li>EventGrid subject filter syntax validated for container paths</li>
  <li>Blob path parsing logic traced and documented</li>
  <li>Container name extraction feasibility confirmed: YES/NO</li>
  <li>RBAC research complete: Container-scoped RBAC supported: YES/NO</li>
  <li>Current access control approach documented (keys vs Managed Identity)</li>
  <li>All code files requiring changes listed with estimated LOC changes</li>
  <li>Unit test impact assessed</li>
  <li>Integration test impact assessed</li>
  <li>Total effort estimated: ____ hours/days</li>
  <li>Change impact matrix created (Low/Medium/High risk per file)</li>
  <li>Detailed refactoring plan documented</li>
  <li>Complexity assessment: Low / Medium / High (with justification)</li>
  <li>All risks identified with mitigation strategies</li>
  <li>Recommendation: GO / NO-GO / GO-WITH-CONDITIONS</li>
  <li>Comprehensive report in: <code>architecture_review/phase1-option3b-detailed-validation.md</code></li>
</ul>
```

**Effort:** 13 Story Points  
**Priority:** High  
**Tags:** Phase1, Option3b, Airlock, CodeAnalysis, TechnicalValidation

---

## Summary

**Phase 0 Work Items:**
- 1 Epic
- 1 Feature (Phase 0)
- 4 User Stories
- **Total Effort:** ~17 hours (~2-3 days)
- **Expected Outcome:** Initial feasibility assessment and Go/No-Go decision for each option

**Phase 1 Work Items:**
- 1 Feature (Phase 1)
- 3 User Stories
- **Total Story Points:** 26 SP (~1-2 weeks)
- **Expected Outcome:** Detailed technical validation and final Go/No-Go decision before prototyping

**Combined Summary:**
- 1 Epic
- 2 Features (Phase 0 + Phase 1)
- 7 User Stories total
- **Expected Savings:** $302,400/year combined for all 3 options
- **Timeline:** 2-3 weeks for both phases

**Next Steps:**
1. ✅ Work items created in Azure DevOps TRE playground board
2. Execute Phase 0 assessment (2-3 days)
3. Review Phase 0 findings
4. Execute Phase 1 deep technical validation (1-2 weeks)
5. Review Phase 1 findings and make final Go/No-Go decision
6. If approved, proceed to Phase 2: Prototype Development
