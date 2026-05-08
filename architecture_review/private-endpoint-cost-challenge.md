# Challenge: Private Endpoint Network Costs

## Executive Summary

**Current Assessment:** The cost optimization plan accepts that most Private Endpoints are necessary, reducing only the 5 airlock-related Private Endpoints per workspace (~$10K/mo savings at 500 workspaces).

**This Challenge:** The TRE architecture uses **10 Private Endpoints per workspace** (when airlock is enabled) costing ~$72/mo each = **$720/mo per workspace** or **$360K/year at 500 workspaces**. This analysis challenges whether ALL of these are truly required and proposes alternative architectures to significantly reduce or eliminate per-workspace Private Endpoint costs.

## Current Private Endpoint Inventory

### Per Workspace (Base Template)
From `templates/workspaces/base/terraform/`:

1. **Key Vault** (`kvpe`) - [keyvault.tf:3](../templates/workspaces/base/terraform/keyvault.tf#L3)
2. **Storage Blob** (`stgblobpe`) - [storage.tf:85](../templates/workspaces/base/terraform/storage.tf#L85)
3. **Storage File** (`stgfilepe`) - [storage.tf:64](../templates/workspaces/base/terraform/storage.tf#L64)
4. **Storage DFS** (`stgdfspe`) - [storage.tf:106](../templates/workspaces/base/terraform/storage.tf#L106)
5. **Azure Monitor** (`azure_monitor_private_endpoint`) - [azure-monitor/azure-monitor.tf](../templates/workspaces/base/terraform/azure-monitor/azure-monitor.tf)

### Per Workspace with Airlock (5 additional)
From `templates/workspaces/base/terraform/airlock/storage_accounts.tf`:

6. **Import Approved Storage** (`import_approved_pe`) - line 53
7. **Export Internal Storage** (`export_internal_pe`) - line 129
8. **Export In-Progress Storage** (`export_inprogress_pe`) - line 210
9. **Export Rejected Storage** (`export_rejected_pe`) - line 310
10. **Export Blocked Storage** (`export_blocked_pe`) - line 385

### Core TRE Private Endpoints (Shared/Fixed Cost)
From `core/terraform/`:
- API App Service
- Key Vault
- Storage (Blob + File)
- Container Registry (ACR)
- Service Bus
- Cosmos DB (MongoDB)

**Total per workspace:** 10 PEs (with airlock) or 5 PEs (without airlock)
**Cost:** $7.20/PE/mo × 10 = $72/mo/workspace = **$36K/mo at 500 workspaces**

---

## Challenge #1: Do We Need 3 Private Endpoints for ONE Storage Account?

### Current Architecture
Each workspace storage account has **3 separate Private Endpoints**:
- `stgblobpe` - for Blob service
- `stgfilepe` - for File service  
- `stgdfspe` - for Data Lake Storage Gen2 (DFS/ADLS)

### Question: Why?
Azure Storage supports multiple subresources on a single Private Endpoint. The Terraform code explicitly creates separate endpoints:

```hcl
# storage.tf
resource "azurerm_private_endpoint" "stgfilepe" {
  subresource_names = ["File"]
}

resource "azurerm_private_endpoint" "stgblobpe" {
  subresource_names = ["Blob"]
}

resource "azurerm_private_endpoint" "stgdfspe" {
  subresource_names = ["dfs"]
}
```

### Alternative: Multi-Subresource Private Endpoint

**Proposal:** Use a single Private Endpoint with multiple subresource connections:

```hcl
resource "azurerm_private_endpoint" "workspace_storage_pe" {
  name                = "stgpe-${local.workspace_resource_name_suffix}"
  location            = azurerm_resource_group.ws.location
  resource_group_name = azurerm_resource_group.ws.name
  subnet_id           = module.network.services_subnet_id
  
  # Multiple subresources on ONE endpoint
  private_service_connection {
    name                           = "psc-storage-blob"
    private_connection_resource_id = azurerm_storage_account.stg.id
    is_manual_connection           = false
    subresource_names              = ["blob"]
  }
  
  private_service_connection {
    name                           = "psc-storage-file"
    private_connection_resource_id = azurerm_storage_account.stg.id
    is_manual_connection           = false
    subresource_names              = ["file"]
  }
  
  private_service_connection {
    name                           = "psc-storage-dfs"
    private_connection_resource_id = azurerm_storage_account.stg.id
    is_manual_connection           = false
    subresource_names              = ["dfs"]
  }
  
  private_dns_zone_group {
    name = "storage-dns-group"
    private_dns_zone_ids = [
      data.azurerm_private_dns_zone.blobcore.id,
      data.azurerm_private_dns_zone.filecore.id,
      data.azurerm_private_dns_zone.dfscore.id
    ]
  }
}
```

**Savings:** 2 Private Endpoints per workspace = **$14.40/mo/workspace** = **$7,200/mo at 500 workspaces**

**Validation Needed:**
- [ ] Test if Azure Private Endpoint supports multiple private_service_connection blocks to same resource
- [ ] Verify DNS resolution works correctly with private_dns_zone_group containing multiple zones
- [ ] Confirm no performance impact vs separate endpoints

---

## Challenge #2: Do Workspaces Need Dedicated Azure Monitor Private Endpoints?

### Current Architecture
Each workspace deploys its own:
- Log Analytics Workspace
- Private Endpoint to Azure Monitor Private Link Scope (AMPLS)

### Question: Why Not Use Core AMPLS?

The **Core TRE** already has:
- Shared AMPLS resource (`ampls-{TRE_ID}`)
- Private Endpoint in SharedSubnet
- Private DNS zones configured

**Proposal:** Have workspace Log Analytics Workspaces associate with the **core AMPLS** instead of creating per-workspace Private Endpoints.

```hcl
# In workspace template - REMOVE the private endpoint
# resource "azurerm_private_endpoint" "azure_monitor_private_endpoint" { ... }

# Instead, just associate with core AMPLS
resource "azurerm_monitor_private_link_scoped_service" "workspace_logs" {
  name                = "svc-logs-${local.workspace_resource_name_suffix}"
  resource_group_name = var.core_resource_group_name # Core RG
  scope_name          = var.core_ampls_name          # Core AMPLS
  linked_resource_id  = azurerm_log_analytics_workspace.workspace.id
}
```

**Rationale:**
- AMPLS is designed to support multiple Log Analytics Workspaces
- Workspaces are already on peered VNETs with route to Core SharedSubnet
- Azure Monitor ingestion traffic already flows through Azure backbone
- No additional security benefit from per-workspace AMPLS PE

**Savings:** 1 Private Endpoint per workspace = **$7.20/mo/workspace** = **$3,600/mo at 500 workspaces**

**Validation Needed:**
- [ ] Confirm workspace VMs can reach Core AMPLS endpoint over peered VNET
- [ ] Test Log Analytics ingestion from workspace resources via Core PE
- [ ] Verify no compliance/isolation requirement for separate AMPLS endpoints
- [ ] Check if NSG rules between Workspace VNET and Core SharedSubnet allow required traffic

---

## Challenge #3: Consolidate Airlock Storage Under Shared Private Endpoints

### Current Architecture
Each workspace with airlock creates **5 separate storage accounts** with **5 Private Endpoints**:
1. Import Approved
2. Export Internal
3. Export In-Progress
4. Export Rejected
5. Export Blocked

**Cost:** $36/mo (5 × $7.20) + $15/mo storage = **$51/mo per airlock-enabled workspace**

### Alternative 1: Shared Airlock Storage Infrastructure

**Proposal:** Move airlock storage to **Shared Services** (like Gitea/Nexus storage):

```
Core TRE → Shared Subnet
  ├─ Shared Storage Account: sa-airlock-core-{TRE_ID}
  │   ├─ Container: import-approved-ws-{WORKSPACE_ID}
  │   ├─ Container: export-internal-ws-{WORKSPACE_ID}
  │   ├─ Container: export-inprogress-ws-{WORKSPACE_ID}
  │   ├─ Container: export-rejected-ws-{WORKSPACE_ID}
  │   └─ Container: export-blocked-ws-{WORKSPACE_ID}
  └─ Private Endpoint (1) → workspace VNETs access via peering
```

**Access Control:** Use container-level SAS tokens or RBAC for workspace isolation

**Savings:** 
- Eliminates 5 PEs per workspace = **$36/mo per workspace**
- Eliminates 5 storage accounts per workspace = **$15/mo per workspace**
- **Total: $51/mo per workspace = $25,500/mo at 500 workspaces**

**Tradeoffs:**
- ⚠️ Slightly more complex RBAC/access management (container-level instead of account-level)
- ⚠️ Single storage account has scale limits (~500 TPS)
- ⚠️ Requires architectural change to airlock processor to support multi-workspace storage pattern
- ✅ Better centralized monitoring/auditing of all airlock activity
- ✅ Easier to implement organization-wide airlock policies

### Alternative 2: Single Airlock Storage Account per Workspace

If shared storage is too complex, at least consolidate the 5 accounts into 1:

```hcl
resource "azurerm_storage_account" "workspace_airlock" {
  name = "stgairlock${var.short_workspace_id}"
  # ... standard config
}

resource "azurerm_storage_container" "import_approved" {
  name                  = "import-approved"
  storage_account_name  = azurerm_storage_account.workspace_airlock.name
}

resource "azurerm_storage_container" "export_internal" {
  name                  = "export-internal"
  storage_account_name  = azurerm_storage_account.workspace_airlock.name
}
# ... etc for other 3 containers

resource "azurerm_private_endpoint" "airlock_pe" {
  # Single PE with blob subresource
  private_service_connection {
    subresource_names = ["blob"]
  }
}
```

**Savings:** 4 Private Endpoints per workspace = **$28.80/mo per workspace** = **$14,400/mo at 500 workspaces**

**Validation Needed:**
- [ ] Review airlock event processor - does it depend on separate storage accounts?
- [ ] Check if container-level access control provides sufficient isolation
- [ ] Verify EventGrid subscriptions can filter by container

---

## Challenge #4: Do Workspaces Need Dedicated Key Vaults?

### Current Architecture
Each workspace gets its own Key Vault + Private Endpoint

### Question: What Secrets Are Workspace-Specific?

Looking at [keyvault.tf](../templates/workspaces/base/terraform/keyvault.tf):
- `auth-tenant-id` - could be shared (same across all workspaces)
- Workspace-specific secrets (API keys, connection strings for workspace services)

### Alternative 1: Shared Key Vault with RBAC

**Proposal:** Use Core Key Vault with namespace-prefix secrets:

```
Core Key Vault kv-{TRE_ID}:
  ├─ ws-{WORKSPACE_ID}-connection-string
  ├─ ws-{WORKSPACE_ID}-api-key
  └─ ... (RBAC restricts access to workspace-specific secrets)
```

**Savings:** 1 Private Endpoint per workspace = **$7.20/mo/workspace** = **$3,600/mo at 500 workspaces**

**Tradeoffs:**
- ⚠️ Single Key Vault has soft limits (secrets, operations/sec)
- ⚠️ More complex RBAC management
- ⚠️ Requires workspace resource principal to have RBAC on Core Key Vault
- ⚠️ Less isolation (all workspace secrets in one vault)

### Alternative 2: Keep Workspace Key Vaults, Remove Private Endpoints

**Proposal:** Use Key Vault [Service Endpoints](https://learn.microsoft.com/en-us/azure/key-vault/general/overview-vnet-service-endpoints) instead of Private Endpoints:

```hcl
# On workspace services subnet
resource "azurerm_subnet" "services" {
  service_endpoints = ["Microsoft.KeyVault"]
}

# On Key Vault
resource "azurerm_key_vault" "workspace_kv" {
  network_acls {
    default_action             = "Deny"
    bypass                     = "AzureServices"
    virtual_network_subnet_ids = [module.network.services_subnet_id]
  }
}
```

**Savings:** 1 Private Endpoint per workspace = **$7.20/mo/workspace** = **$3,600/mo at 500 workspaces**

**Tradeoffs:**
- ⚠️ Traffic goes over Azure backbone (not private VNET), but still encrypted
- ⚠️ May not meet strict compliance requirements that mandate Private Link
- ✅ Simpler infrastructure
- ✅ Faster access (no Private DNS resolution overhead)

**Validation Needed:**
- [ ] Check TRE compliance/security requirements for Key Vault access
- [ ] Verify if Service Endpoints meet security posture
- [ ] Test Key Vault access from workspace VMs via Service Endpoint

---

## Challenge #5: Question the Security Architecture Assumption

### Current Assumption
**Every PaaS resource in every workspace needs a Private Endpoint to prevent data exfiltration**

### Counter-Argument: Defense in Depth Already Exists

The TRE architecture ALREADY has multiple layers preventing unauthorized access:

1. **Network Isolation:**
   - All workspace subnets have default route to Azure Firewall
   - Firewall explicitly denies all egress except approved destinations
   - Workspace VNETs cannot reach Internet directly

2. **Service-Level Security:**
   - Storage accounts have `network_rules { default_action = "Deny" }`
   - Key Vaults have network ACLs restricting access
   - NSGs control inter-subnet traffic

3. **Identity & Access:**
   - Managed identities with RBAC
   - No shared access keys enabled on storage
   - Service principals with least privilege

### Question: What Attack Vector Do Private Endpoints Actually Block?

Scenario: A compromised workspace VM tries to exfiltrate data

**Without Private Endpoints:**
- VM tries to reach `stgworkspace123.blob.core.windows.net`
- DNS resolves to public IP (e.g., 52.x.x.x)
- Traffic hits Azure Firewall egress rules
- Firewall **denies** connection (not in allowlist)
- VM **cannot reach storage account public endpoint** from Internet

**With Private Endpoints:**
- VM resolves `stgworkspace123.blob.core.windows.net` to private IP (10.x.x.x)
- Traffic stays in VNET
- Reaches storage account via Private Link

**The Question:** If the Firewall already blocks public endpoint access, what additional security does the Private Endpoint provide?

### Potential Answer: Prevent Insider Bypass

An attacker with Azure portal/CLI access could:
1. Temporarily modify Firewall rules to allow storage public IP
2. Exfiltrate data
3. Revert Firewall rules

**Counter:** This requires:
- Attacker has Contributor/Owner on Firewall resource
- If they have this, they could also:
  - Modify Private Endpoint NSG rules
  - Create peering to external VNET
  - Deploy malicious VM as "jump box"

**Conclusion:** Private Endpoints provide defense-in-depth but may not justify **$360K/year** in a Firewall-controlled environment.

### Validation Needed:
- [ ] Test if workspace VM can reach storage public endpoint when Firewall denies it
- [ ] Review TRE security documentation for explicit Private Link requirements
- [ ] Consult with security/compliance team on acceptable risk tradeoffs
- [ ] Check if audit/compliance frameworks (HIPAA, ISO 27001) mandate Private Link

---

## Summary of Savings Opportunities

| Challenge | Change | Savings per WS | Savings at 500 WS | Difficulty | Risk |
|-----------|--------|----------------|-------------------|------------|------|
| #1 | Consolidate 3 storage PEs to 1 | $14.40/mo | $7,200/mo | Low | Low |
| #2 | Use Core AMPLS instead of per-workspace | $7.20/mo | $3,600/mo | Medium | Medium |
| #3a | Shared airlock storage infrastructure | $51.00/mo | $25,500/mo | High | High |
| #3b | Single storage account for airlock | $28.80/mo | $14,400/mo | Medium | Medium |
| #4 | Remove Key Vault PE (use Service Endpoint) | $7.20/mo | $3,600/mo | Low | Medium |
| #5 | Remove ALL workspace PEs (rely on Firewall) | $72.00/mo | $36,000/mo | High | High |

### Conservative Approach (Quick Wins)
Implement #1 + #2 + #3b (already planned airlock default-off):
- **Per workspace:** $14.40 + $7.20 = $21.60/mo (30% reduction)
- **At 500 workspaces:** $10,800/mo = **$129,600/year savings**
- **Difficulty:** Low-Medium
- **Risk:** Low

### Aggressive Approach (Architectural Change)
Implement #1 + #2 + #3a + #4:
- **Per workspace:** $14.40 + $7.20 + $51.00 + $7.20 = $79.80/mo (97% reduction)
- **At 500 workspaces:** $39,900/mo = **$478,800/year savings**
- **Difficulty:** Medium-High
- **Risk:** Medium

### Nuclear Option (Re-Architecture)
Implement #5 (remove all workspace PEs):
- **Per workspace:** $72.00/mo (100% reduction)
- **At 500 workspaces:** $36,000/mo = **$432,000/year savings**
- **Difficulty:** High (requires security posture review)
- **Risk:** High (may not meet compliance)

---

## Recommended Next Steps

### Immediate (Week 1)
1. ✅ **Validate Technical Feasibility**
   - Test multi-subresource Private Endpoint (Challenge #1)
   - Test Core AMPLS access from workspace VNET (Challenge #2)
   
### Short-term (Month 1)
2. ✅ **Security Review**
   - Document current threat model and how Private Endpoints mitigate risks
   - Identify which compliance frameworks require Private Link
   - Assess if Firewall + network ACLs provide sufficient isolation
   
3. ✅ **Implement Quick Wins**
   - Consolidate storage PEs (Challenge #1) - 1 week dev/test
   - Use Core AMPLS (Challenge #2) - 1 week dev/test
   - Deploy to dev/test environment and validate
   
### Medium-term (Quarter 1)
4. ✅ **Airlock Consolidation POC**
   - Prototype shared airlock storage (Challenge #3a)
   - Test EventGrid filtering and RBAC isolation
   - Compare with single-account approach (Challenge #3b)
   
5. ✅ **Cost-Benefit Analysis**
   - Project savings vs engineering effort
   - Quantify security posture changes
   - Present options to leadership
   
### Long-term (Quarter 2)
6. ⚠️ **Consider Architectural Pivot**
   - If compliance allows, pilot workspace without Private Endpoints
   - Run penetration tests to validate Firewall-only security model
   - Document new security architecture

---

## Questions for Stakeholders

1. **Security/Compliance Team:**
   - What are the actual regulatory requirements for Private Link?
   - Can we rely on Azure Firewall + network ACLs instead?
   - What is the risk tolerance for consolidated storage models?

2. **Architecture Team:**
   - What is the history of the "Private Endpoint everywhere" decision?
   - Are there known incidents that Private Endpoints prevented?
   - What happens if we exceed Azure subscription PE limits at scale?

3. **Finance/Leadership:**
   - What is the engineering budget to implement these changes?
   - At what scale does $432K/year in PE costs justify re-architecture?
   - Are there other cost centers we should prioritize instead?

---

## References

- [Azure Private Endpoint Pricing](https://azure.microsoft.com/en-us/pricing/details/private-link/)
- [Azure Storage Private Endpoints](https://learn.microsoft.com/en-us/azure/storage/common/storage-private-endpoints)
- [Azure Monitor Private Link Scope](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/private-link-security)
- [Service Endpoints vs Private Endpoints](https://learn.microsoft.com/en-us/azure/virtual-network/vnet-integration-for-azure-services)
- [Azure TRE Cost Optimization Plan](cost-optimization-plan.md)

---

# Private Endpoint Removal: Risk Matrix & Detailed Mitigation Strategies

## Summary Table

| Private Endpoint | Current State | Removal/Consolidation Approach | Savings per WS | Savings at 500 WS | Risk Level | Implementation Effort |
|------------------|---------------|--------------------------------|----------------|-------------------|------------|----------------------|
| Storage (Blob + File + DFS) | 3 separate PEs | Consolidate to 1 multi-subresource PE | $14.40/mo | $86,400/year | **LOW** | Low |
| Azure Monitor (AMPLS) | 1 PE per workspace | Use Core AMPLS (remove workspace PE) | $7.20/mo | $43,200/year | **MEDIUM** | Medium |
| Airlock Storage (5 accounts) | 5 PEs | Consolidate to 1 account/1 PE | $28.80/mo | $172,800/year | **MEDIUM** | Medium |
| Airlock Storage (shared) | 5 PEs | Move to Core shared storage | $51.00/mo | $306,000/year | **HIGH** | High |
| Key Vault | 1 PE | Use Service Endpoints | $7.20/mo | $43,200/year | **MEDIUM** | Low |
| Key Vault | 1 PE | Shared Core Key Vault | $7.20/mo | $43,200/year | **HIGH** | High |
| All Storage PEs | 3 PEs | Public endpoints + Firewall only | $21.60/mo | $129,600/year | **HIGH** | Medium |
| All Workspace PEs | 5-10 PEs | Public endpoints + Firewall only | $36-72/mo | $216K-432K/year | **VERY HIGH** | High |

---

## Detailed Risk & Mitigation Analysis

### Option 1: Consolidate Storage Private Endpoints (3 → 1)

**Current:** Each workspace storage account has 3 separate Private Endpoints:
- `stgblobpe` (Blob)
- `stgfilepe` (File)
- `stgdfspe` (DFS/ADLS)

**Proposed:** Single Private Endpoint with multiple private_service_connection blocks

| Risk | Severity | Probability | Mitigation |
|------|----------|-------------|------------|
| Azure doesn't support multiple subresources on one PE | Medium | Low | **Pre-validate:** Test in dev environment with single PE + multiple connections. Azure documentation confirms this is supported. |
| DNS resolution fails for some subresources | Medium | Low | **Verify:** Use `private_dns_zone_group` with all 3 DNS zones (blob.core, file.core, dfs.core). Test nslookup from workspace VM. |
| Existing workspaces break during migration | High | Medium | **Mitigation:** Use blue-green deployment. Create new PE before deleting old ones. Add `depends_on` to ensure ordering. Test rollback procedure. |
| Performance degradation (single NIC bottleneck) | Low | Very Low | **Monitor:** Compare latency/throughput before and after. Private Endpoints use 10Gbps NICs, unlikely to bottleneck. |
| Terraform state issues during migration | Medium | Medium | **Mitigation:** Use `terraform state mv` or `moved` blocks to avoid destroy/recreate. Document state migration procedure. |

**Implementation Steps:**
1. ✅ Test in isolated dev workspace
2. ✅ Validate DNS resolution for all 3 subresources
3. ✅ Create Terraform migration plan with `moved` blocks
4. ✅ Deploy to 1 pilot workspace, monitor for 1 week
5. ✅ Roll out to remaining workspaces in batches

**Rollback Plan:** Keep Terraform code for old 3-PE pattern. Can revert with `terraform apply` of previous version.

---

### Option 2: Remove Per-Workspace Azure Monitor Private Endpoints

**Current:** Each workspace deploys its own AMPLS + Private Endpoint

**Proposed:** Associate workspace Log Analytics with Core AMPLS (remove workspace PE)

| Risk | Severity | Probability | Mitigation |
|------|----------|-------------|------------|
| Network path blocked between workspace VNET and Core AMPLS | High | Medium | **Validate:** Check NSG rules on Workspace→Core peering. Ensure SharedSubnet allows ingress from workspace VNETs on HTTPS (443). Test with `curl` from workspace VM. |
| AMPLS ingestion limits exceeded | Medium | Low | **Check limits:** AMPLS supports 300 linked resources (workspaces) per AMPLS. For 500 workspaces, need 2 Core AMPLS resources or increase limit via support ticket. |
| Log ingestion fails due to DNS resolution | High | Medium | **Verify:** Workspace VMs must resolve `*.ods.opinsights.azure.com` to Core AMPLS private IP. Ensure workspace VNET has DNS link to Core private DNS zones. |
| Compliance violation (workspace isolation) | High | Low | **Audit:** Review compliance requirements. AMPLS provides log stream isolation even when sharing the PE. Each workspace's logs remain isolated in its own Log Analytics Workspace. |
| Cannot independently delete workspace without affecting Core | Low | Low | **Design:** Use `azurerm_monitor_private_link_scoped_service` to link workspace LA to Core AMPLS. Deleting workspace auto-removes the link, not the Core AMPLS. |

**Implementation Steps:**
1. ✅ Validate Core AMPLS has capacity (300 resources per AMPLS)
2. ✅ Test network connectivity: workspace VM → Core AMPLS endpoint
3. ✅ Deploy test workspace using Core AMPLS
4. ✅ Generate log traffic, verify ingestion succeeds
5. ✅ Monitor for 2 weeks, check for latency/drop issues
6. ✅ Update workspace template to remove PE, add AMPLS link
7. ✅ For existing workspaces: add link first, then remove PE (zero-downtime)

**Rollback Plan:** Keep per-workspace AMPLS PE template. Can deploy new AMPLS PE and unlink from Core.

---

### Option 3A: Consolidate Airlock Storage (5 accounts → 1 account)

**Current:** Each workspace with airlock creates 5 storage accounts, each with 1 PE

**Proposed:** Single storage account with 5 containers, 1 Private Endpoint

| Risk | Severity | Probability | Mitigation |
|------|----------|-------------|------------|
| EventGrid subscriptions break (rely on account-level events) | High | High | **Test:** Verify EventGrid can filter events by container path. Use `subject` filter: `subjectBeginsWith: "/blobServices/default/containers/import-approved/"`. Validate in dev environment. |
| Airlock processor cannot distinguish containers | High | Medium | **Code Review:** Check `core/terraform/airlock/airlock_processor.tf` and Python event handler. Update to parse container name from blob path. Add container-aware routing logic. |
| RBAC becomes too permissive (account-level) | Medium | Medium | **RBAC Design:** Use Managed Identity with `Storage Blob Data Contributor` scoped to specific containers, not account. Verify with `az role assignment list`. |
| Backup/Recovery Services Vault cannot back up containers independently | Low | Low | **Alternative:** Azure Backup supports container-level recovery even from account-level backup. Test restore procedure for single container. |
| Name collision between workspaces (container names) | Low | Very Low | **Convention:** Use `{container-type}-{workspace-id}` pattern (e.g., `import-approved-ws-1234`). Enforce via Terraform validation. |

**Implementation Steps:**
1. ✅ Audit airlock processor code for storage account assumptions
2. ✅ Test EventGrid subscriptions with container-level filtering
3. ✅ Create prototype single-account template
4. ✅ Test full airlock workflow (import → scan → approve → export)
5. ✅ Deploy to pilot workspace, run airlock operations for 1 month
6. ✅ Migrate existing workspaces (data copy + config update)

**Rollback Plan:** Keep old 5-account template. For migrated workspaces, can redeploy old template and copy data back.

**Migration Complexity:** HIGH - requires data migration for existing workspaces with airlock data.

---

### Option 3B: Shared Airlock Storage (Core Infrastructure)

**Current:** Each workspace with airlock creates 5 storage accounts

**Proposed:** Single Core storage account, all workspaces share via containers

| Risk | Severity | Probability | Mitigation |
|------|----------|-------------|------------|
| Cross-workspace data access (security violation) | **CRITICAL** | Medium | **RBAC Lockdown:** Use Managed Identity per workspace with RBAC scoped to only its containers. Implement Azure Policy to deny direct account key access. Add audit alerts for cross-workspace access attempts. |
| Storage account scale limits (500 TPS) | High | High | **Capacity Planning:** 500 workspaces × avg 1 req/sec = 500 TPS (at limit). Use multiple sharded storage accounts (e.g., 1 per 100 workspaces) or Premium tier (20K TPS). Monitor metrics. |
| Single point of failure for all airlock operations | High | Medium | **Redundancy:** Deploy GRS storage account. Use retry logic in airlock processor. Set up automated failover to secondary region. Monitor availability with alerts. |
| Complex RBAC management at scale | Medium | High | **Automation:** Use Terraform `for_each` to auto-create container-level RBAC assignments. Implement IaC validation tests. Document RBAC patterns in runbook. |
| EventGrid topic saturation (all workspaces → 1 topic) | Medium | Medium | **Scaling:** EventGrid supports 5K events/sec. Monitor throughput. If exceeded, shard by workspace ranges or use multiple storage accounts. |
| Workspace deletion leaves orphaned data | Low | Medium | **Lifecycle Policy:** Implement blob lifecycle management to auto-delete containers after workspace deletion. Add cleanup hook in workspace destroy operation. |
| Compliance violation (data co-mingling) | High | Low | **Audit:** Review regulatory requirements (HIPAA, GDPR). Some frameworks may prohibit shared storage infrastructure between tenants. Get compliance sign-off before proceeding. |

**Implementation Steps:**
1. ✅ **Security Review:** Get approval from security/compliance team for shared storage model
2. ✅ Create prototype Core airlock storage account
3. ✅ Implement container-level RBAC automation
4. ✅ Test workspace isolation (workspace A cannot read workspace B data)
5. ✅ Update airlock processor to handle container-based routing
6. ✅ Load test with simulated 500 workspace operations
7. ✅ Deploy to pilot workspace, run for 2 months
8. ✅ Document migration playbook for existing workspaces

**Rollback Plan:** Revert workspace template to deploy dedicated airlock storage. Copy data from Core storage to workspace storage.

**Migration Complexity:** VERY HIGH - requires airlock processor redesign and data migration.

---

### Option 4A: Replace Key Vault Private Endpoints with Service Endpoints

**Current:** Each workspace deploys Key Vault + Private Endpoint

**Proposed:** Use VNET Service Endpoints instead of Private Link

| Risk | Severity | Probability | Mitigation |
|------|----------|-------------|------------|
| Traffic goes over Azure backbone (not private VNET) | Low | 100% | **Accept Risk:** Traffic is still encrypted via TLS. Azure backbone is isolated from public internet. Document security architecture decision. |
| Compliance requirement for Private Link | High | Medium | **Validate:** Review compliance frameworks (HIPAA, FedRAMP, ISO 27001). Check if Private Link is explicitly required. Get sign-off from compliance team. If required, DO NOT PROCEED. |
| Service Endpoint not supported in workspace subnet | Medium | Low | **Verify:** Check if subnet already has service endpoints. Add `Microsoft.KeyVault` to `service_endpoints` list in Terraform. Test from workspace VM. |
| DNS resolution points to public endpoint | Medium | Medium | **Expected Behavior:** Service Endpoints use public DNS but traffic routes via Azure backbone. Verify with `nslookup {keyvault}.vault.azure.net` returns public IP, but `traceroute` shows private path. |
| Cannot enforce key vault firewall rules per workspace | Medium | Medium | **Network ACL:** Configure Key Vault firewall to allow workspace subnet via `virtual_network_subnet_ids`. Each workspace subnet added individually. |
| Performance difference (latency increase) | Low | Low | **Monitor:** Measure Key Vault API latency before/after. Service Endpoints typically have <5ms overhead vs Private Link. Set alert threshold at +10ms. |

**Implementation Steps:**
1. ✅ **Compliance Check:** Get explicit approval that Service Endpoints meet security requirements
2. ✅ Add `Microsoft.KeyVault` service endpoint to workspace services subnet
3. ✅ Deploy test workspace with Service Endpoint (no PE)
4. ✅ Test Key Vault access from workspace VM
5. ✅ Measure latency vs Private Endpoint baseline
6. ✅ Monitor for 2 weeks for any access issues
7. ✅ Update workspace template to remove PE, add network ACL

**Rollback Plan:** Re-add Private Endpoint to template. No data loss, only network path change.

**Migration Complexity:** LOW - network configuration only, no application changes.

---

### Option 4B: Shared Core Key Vault (Remove Workspace Key Vaults)

**Current:** Each workspace deploys dedicated Key Vault

**Proposed:** All workspaces use Core Key Vault with namespaced secrets

| Risk | Severity | Probability | Mitigation |
|------|----------|-------------|------------|
| Key Vault soft limits exceeded | High | High | **Limits:** 25K secrets per vault (adequate for 500 workspaces × 10 secrets = 5K). Transaction limit: 2K TPS (may be tight). Monitor metrics. Request limit increase via Azure support if needed. |
| Secret name collisions | Medium | Medium | **Naming Convention:** Enforce `ws-{WORKSPACE_ID}-{SECRET_NAME}` pattern. Use Terraform validation. Add uniqueness check in deployment pipeline. |
| RBAC management complexity | High | High | **Automation:** Use Terraform `for_each` + RBAC assignments. Each workspace identity gets Key Vault Secret User on secrets matching `ws-{WORKSPACE_ID}-*` pattern (requires custom role with scope to specific secrets - NOT supported by Azure). **BLOCKER:** Azure Key Vault RBAC cannot scope to secret name patterns. Would need vault-level access + app-level filtering = security risk. |
| Workspace deletion doesn't clean up secrets | Medium | High | **Lifecycle Management:** Add Terraform `destroy` provisioner to delete secrets with `ws-{WORKSPACE_ID}-*` prefix. Implement periodic cleanup job. Risk of orphaned secrets. |
| Less isolation (all secrets in one vault) | High | Medium | **Security Impact:** If Core Key Vault is compromised, all workspace secrets exposed. This reduces blast radius vs dedicated vaults. **Recommendation:** Keep dedicated vaults for high-security workspaces. |
| Cannot delete Core Key Vault without affecting all workspaces | **CRITICAL** | Low | **Design Flaw:** Makes Core Key Vault a permanent dependency. If vault needs recreation (e.g., region migration), must migrate all workspace secrets. High operational risk. |

**Assessment:** ❌ **NOT RECOMMENDED** due to RBAC limitation (cannot scope to secret name patterns) and blast radius concerns.

**Alternative:** Keep dedicated workspace Key Vaults but use Service Endpoints (Option 4A) to save on Private Endpoints.

---

### Option 5: Remove Storage Private Endpoints (Rely on Firewall + Network ACLs)

**Current:** Workspace storage uses Private Endpoints

**Proposed:** Remove Private Endpoints, rely on Azure Firewall + storage network ACLs

| Risk | Severity | Probability | Mitigation |
|------|----------|-------------|------------|
| Data exfiltration via public endpoint | **CRITICAL** | Medium | **Layered Defense:** <br>1. Storage network ACL: `default_action = "Deny"`, allow only workspace VNET <br>2. Azure Firewall: Deny outbound to storage public IPs (except workspace storage) <br>3. NSG: Deny workspace VM → Internet <br>4. Monitor: Alert on any storage access from non-workspace IPs |
| Insider with portal access modifies firewall rules | High | Medium | **RBAC + Audit:** <br>1. Separate Firewall admin role from workspace admin <br>2. Enable Azure Activity Log alerts on Firewall rule changes <br>3. Require approval workflow for Firewall changes (Azure Policy) <br>4. Regular audit of Firewall rule changes |
| DNS resolution still points to public IP | Medium | 100% (expected) | **Not a Risk:** Storage FQDN resolves to public IP, but traffic hits network ACL at Azure backbone. Firewall also blocks if VM tries to reach public IP. Traffic never leaves Azure network. |
| Compliance violation (HIPAA/FedRAMP require Private Link) | **CRITICAL** | High | **BLOCKER:** Check compliance requirements. Many frameworks explicitly require Private Link for PaaS services handling sensitive data. If required, DO NOT PROCEED. Get legal/compliance sign-off. |
| Storage account misconfiguration (network ACL removed) | High | Medium | **Azure Policy:** Implement policy to audit/deny storage accounts without network ACLs. Alert on any network ACL changes. Use Terraform to enforce ACL settings. |
| Increased attack surface (public endpoint exposed) | Medium | Medium | **Defense:** Even with public endpoint, access requires:<br>1. Pass network ACL (only workspace VNET allowed)<br>2. Valid authentication (Managed Identity or SAS token)<br>3. RBAC permissions<br>Still multiple layers, but Private Link removes one layer. |

**Implementation Steps:**
1. ✅ **Compliance Gate:** Get explicit approval from security/compliance team. If denied, STOP.
2. ✅ Document threat model: what attacks does Private Link prevent?
3. ✅ Test in isolated dev workspace:
   - Remove Private Endpoint
   - Configure storage network ACL to allow only workspace VNET
   - Test VM can access storage
   - Test VM from different VNET CANNOT access storage
4. ✅ Implement Azure Policies for network ACL enforcement
5. ✅ Set up monitoring/alerting for storage access anomalies
6. ✅ Run penetration test from external network
7. ✅ Deploy to pilot workspace, monitor for 3 months
8. ✅ If successful, roll out to low-security workspaces first

**Rollback Plan:** Re-add Private Endpoint to template. No data loss. Update DNS to point to private IP.

**Migration Complexity:** MEDIUM - Network configuration changes, requires extensive testing.

**Recommendation:** ⚠️ **ONLY for low-security workspaces**. Keep Private Endpoints for workspaces handling PHI/PII.

---

### Option 6: Remove ALL Workspace Private Endpoints

**Current:** Workspaces deploy 5-10 Private Endpoints

**Proposed:** Remove all workspace Private Endpoints, rely on Firewall + network ACLs

| Risk | Severity | Probability | Mitigation |
|------|----------|-------------|------------|
| Complete architecture change | **CRITICAL** | 100% | **Impact Analysis:** This is a fundamental security architecture change. Requires executive approval, security review, and compliance sign-off. NOT a simple optimization. |
| Fails compliance audit | **CRITICAL** | High | **BLOCKER:** Most compliance frameworks (HIPAA, FedRAMP, ISO 27001) require network isolation for PaaS services handling sensitive data. Private Link is often explicitly required. **Get legal/compliance approval before any testing.** |
| Multiple attack vectors opened | High | High | **Assessment:** Removing all PEs means:<br>- Storage: public endpoint (mitigated by network ACL + Firewall)<br>- Key Vault: public endpoint (mitigated by firewall + RBAC)<br>- Azure Monitor: public endpoint (mitigated by network ACL)<br>Each removal increases attack surface. Combined removal = compounding risk. |
| Insider threat can exfiltrate data | High | Medium | **Scenario:** Admin with Firewall + Storage permissions:<br>1. Add Firewall allow rule for storage public IP<br>2. Temporarily remove storage network ACL<br>3. Exfiltrate data from external system<br>4. Revert changes<br>**Mitigation:** Requires privileged access + covers tracks. Still possible with PE architecture by modifying NSGs/peering. |
| Increased cloud egress costs | Low | Low | **Cost:** Even without PEs, traffic from workspace to PaaS services stays within Azure region (no egress charges). Egress only charged for Internet/cross-region. |
| Operational complexity of managing network ACLs at scale | Medium | High | **Management:** 500 workspaces × 5 services = 2500 network ACL rules. Must be updated when workspace VNETs change. Automation required. Higher chance of misconfiguration vs Private Link auto-configuration. |

**Assessment:** ❌ **NOT RECOMMENDED** without:
1. Explicit compliance approval
2. Executive sign-off on security posture change
3. Independent security audit
4. Pilot program limited to non-sensitive data workspaces

**Alternative Recommendation:** Pursue Options 1-3 (consolidation) rather than complete removal. Reduces costs while maintaining security posture.

---

## Decision Matrix

### Low-Risk, High-Value (Implement Immediately)

| Option | Savings | Risk | Effort | Compliance Impact | Recommendation |
|--------|---------|------|--------|-------------------|----------------|
| **1. Consolidate Storage PEs (3→1)** | $86K/year | LOW | Low | None | ✅ **PROCEED** |

### Medium-Risk, High-Value (Pilot Required)

| Option | Savings | Risk | Effort | Compliance Impact | Recommendation |
|--------|---------|------|--------|-------------------|----------------|
| **2. Use Core AMPLS** | $43K/year | MEDIUM | Medium | Low | ✅ **PILOT** |
| **3A. Consolidate Airlock (5→1)** | $173K/year | MEDIUM | Medium | Low | ✅ **PILOT** |
| **4A. Key Vault Service Endpoints** | $43K/year | MEDIUM | Low | Medium | ⚠️ **COMPLIANCE CHECK FIRST** |

### High-Risk, High-Value (Requires Approval)

| Option | Savings | Risk | Effort | Compliance Impact | Recommendation |
|--------|---------|------|--------|-------------------|----------------|
| **3B. Shared Airlock Storage** | $306K/year | HIGH | High | High | ⚠️ **SECURITY REVIEW REQUIRED** |
| **5. Remove Storage PEs** | $130K/year | HIGH | Medium | High | ⚠️ **COMPLIANCE APPROVAL REQUIRED** |

### Not Recommended

| Option | Savings | Risk | Effort | Compliance Impact | Recommendation |
|--------|---------|------|--------|-------------------|----------------|
| **4B. Shared Core Key Vault** | $43K/year | HIGH | High | High | ❌ **NOT RECOMMENDED** (RBAC limitations) |
| **6. Remove All Workspace PEs** | $432K/year | VERY HIGH | High | Very High | ❌ **NOT RECOMMENDED** (compliance risk) |

---

## Recommended Implementation Roadmap

### Phase 1: Quick Wins (Month 1) - $86K/year
- ✅ Implement storage PE consolidation (3→1)
- ✅ Test in dev environment
- ✅ Deploy to 10% of workspaces
- ✅ Monitor for issues
- ✅ Roll out to remaining workspaces

**Expected Completion:** 4 weeks  
**Risk:** LOW  
**Savings:** $86,400/year

### Phase 2: Pilot Programs (Months 2-3) - +$216K/year
- ✅ Deploy test workspace using Core AMPLS
- ✅ Prototype consolidated airlock storage (5→1)
- ✅ Run pilot with 5 workspaces for 6 weeks
- ✅ Collect metrics on performance/reliability
- ✅ Get user feedback

**Expected Completion:** 8 weeks  
**Risk:** MEDIUM  
**Cumulative Savings:** $302,400/year

### Phase 3: Compliance Review (Month 4) - +$43K/year
- ⚠️ Assess Key Vault Service Endpoint option
- ⚠️ Review compliance requirements (HIPAA, ISO 27001, etc.)
- ⚠️ Get security team approval
- ⚠️ If approved, pilot with non-PHI workspaces

**Expected Completion:** 4-6 weeks  
**Risk:** MEDIUM  
**Cumulative Savings:** $345,600/year (if approved)

### Phase 4: Evaluate High-Risk Options (Month 5-6) - +$306K/year
- ⚠️ Security review for shared airlock storage
- ⚠️ Load testing and RBAC validation
- ⚠️ Decision: implement or defer based on findings

**Expected Completion:** 8 weeks  
**Risk:** HIGH  
**Potential Total Savings:** $651,600/year

---

## Success Metrics

### Technical Metrics
- ✅ Storage access latency < baseline + 10ms
- ✅ Zero failed storage/Key Vault operations post-migration
- ✅ Log Analytics ingestion success rate > 99.9%
- ✅ No increase in network errors/timeouts

### Security Metrics
- ✅ Zero unauthorized cross-workspace access attempts
- ✅ All network ACL changes logged and alerted
- ✅ Pass quarterly compliance audit
- ✅ No increase in security incidents

### Operational Metrics
- ✅ Deployment time unchanged or improved
- ✅ Zero rollbacks required
- ✅ Support ticket volume unchanged
- ✅ Documentation complete and validated

### Financial Metrics
- ✅ Achieve projected savings within 10%
- ✅ Implementation costs < 1 year of savings
- ✅ No unexpected cost increases from alternatives

---

## Approval Checklist

Before proceeding with each option:

**Option 1 (Storage Consolidation):**
- [ ] Terraform validation passed
- [ ] Dev environment test successful
- [ ] Architecture team sign-off

**Option 2 (Core AMPLS):**
- [ ] Network connectivity validated
- [ ] AMPLS capacity confirmed
- [ ] Pilot workspace successful (6+ weeks)
- [ ] Architecture team sign-off

**Option 3A (Consolidated Airlock):**
- [ ] EventGrid filtering tested
- [ ] Airlock processor code updated
- [ ] Pilot workspace successful (8+ weeks)
- [ ] Security team sign-off

**Option 3B (Shared Airlock):**
- [ ] Security review complete
- [ ] Compliance team approval
- [ ] Load testing passed
- [ ] Executive sign-off (high impact)

**Option 4A (Service Endpoints):**
- [ ] Compliance requirements reviewed
- [ ] Legal/compliance team approval
- [ ] Latency testing acceptable
- [ ] Security team sign-off

**Options 5-6 (Remove PEs):**
- [ ] ❌ NOT RECOMMENDED - Do not proceed without executive/legal approval

---

# Pre-Implementation Examination Checklist

## Conservative Approach: Options #1 + #2 + #3b

**Combined Savings:** $21.60/mo per workspace = $129,600/year at 500 workspaces  
**Risk Level:** LOW to MEDIUM  
**Implementation Timeline:** 8-10 weeks

This checklist covers all tasks to examine before implementing the conservative, high-value quick wins:
- **Option #1:** Consolidate Storage PEs (3 → 1)
- **Option #2:** Use Core AMPLS (remove workspace AMPLS PE)
- **Option #3b:** Consolidate Airlock Storage (5 accounts → 1 account)

---

## Phase 0: Initial Assessment (Week 0)

### 0.1 Current State Inventory

**Task:** Document current infrastructure and costs

- [ ] **Count Existing Workspaces**
  ```bash
  az group list --tag tre_id={TRE_ID} --query "[?contains(name, '-ws-')].name" -o table | wc -l
  ```
  - [ ] Total workspaces: _____
  - [ ] Workspaces with airlock enabled: _____
  - [ ] Projected annual savings: $_____

- [ ] **Document Current PE Count per Workspace**
  ```bash
  # For a sample workspace
  az network private-endpoint list \
    --resource-group rg-{TRE_ID}-ws-XXXX \
    --query "[].{Name:name, Service:privateLinkServiceConnections[0].privateLinkServiceId}" \
    --output table
  ```
  - [ ] Storage PEs (blob, file, dfs): 3 per workspace ✓
  - [ ] Azure Monitor PE: 1 per workspace ✓
  - [ ] Airlock PEs (if enabled): 5 per workspace ✓
  - [ ] Total baseline: _____ PEs per workspace

- [ ] **Review Current Monthly Costs**
  ```bash
  # Private Endpoint costs for last month
  az consumption usage list \
    --start-date $(date -d '30 days ago' +%Y-%m-%d) \
    --end-date $(date +%Y-%m-%d) \
    --query "[?contains(instanceId, 'Microsoft.Network/privateEndpoints')]" \
    --output table
  ```
  - [ ] Current monthly PE cost: $_____
  - [ ] Projected cost after changes: $_____
  - [ ] Monthly savings: $_____

**Exit Criteria:** Current state documented, savings potential confirmed

---

## Phase 1: Technical Validation (Week 1-2)

### 1.1 Option #1: Storage PE Consolidation - Feature Validation

**Task:** Verify Azure supports multi-subresource Private Endpoints

- [ ] **Check Azure Documentation**
  - [ ] Review: [Azure Storage Private Endpoints](https://learn.microsoft.com/en-us/azure/storage/common/storage-private-endpoints)
  - [ ] Confirm: Multiple `private_service_connection` blocks are supported
  - [ ] Verify: No regional or SKU limitations

- [ ] **Verify Terraform Provider Version**
  ```bash
  cd templates/workspaces/base/terraform
  grep "required_providers" versions.tf -A 10
  ```
  - [ ] Current `azurerm` version: _____
  - [ ] Required version: >= 3.0
  - [ ] Upgrade needed? YES / NO

- [ ] **Review Terraform Provider Docs**
  - [ ] Check: [azurerm_private_endpoint](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/private_endpoint)
  - [ ] Verify: Example with multiple connections exists
  - [ ] Note: Any recent breaking changes? _____

**Exit Criteria:** Multi-subresource PE feature confirmed as production-ready

---

### 1.2 Option #2: Core AMPLS - Network Path Validation

**Task:** Verify workspace VNETs can reach Core AMPLS

- [ ] **Identify Core AMPLS Resource**
  ```bash
  az monitor private-link-scope list \
    --resource-group rg-{TRE_ID} \
    --query "[].{Name:name, Id:id}" -o table
  ```
  - [ ] Core AMPLS name: `ampls-{TRE_ID}`
  - [ ] Core AMPLS resource ID: _____

- [ ] **Get Core AMPLS Private Endpoint**
  ```bash
  az network private-endpoint list \
    --resource-group rg-{TRE_ID} \
    --query "[?contains(name, 'ampls')].{Name:name, PrivateIP:privateLinkServiceConnections[0].privateIPAddress}" \
    --output table
  ```
  - [ ] Core AMPLS PE name: _____
  - [ ] Core AMPLS private IP: _____
  - [ ] PE subnet: SharedSubnet ✓

- [ ] **Check AMPLS Capacity**
  ```bash
  az monitor private-link-scope scoped-resource list \
    --resource-group rg-{TRE_ID} \
    --scope-name ampls-{TRE_ID} \
    --query "length([])"
  ```
  - [ ] Current linked resources: _____
  - [ ] AMPLS limit: 300 resources per AMPLS
  - [ ] Capacity for 500 workspaces: Need _____ AMPLS resources

- [ ] **Verify VNET Peering**
  ```bash
  # From sample workspace VNET
  az network vnet peering list \
    --resource-group rg-{TRE_ID}-ws-XXXX \
    --vnet-name vnet-{TRE_ID}-ws-XXXX \
    --query "[].{Name:name, PeeringState:peeringState, RemoteVnet:remoteVirtualNetwork.id}" \
    --output table
  ```
  - [ ] Peering to Core VNET exists ✓
  - [ ] Peering state: Connected ✓
  - [ ] Allow forwarded traffic: Enabled ✓

- [ ] **Check NSG Rules (Workspace → Core)**
  ```bash
  az network nsg show \
    --resource-group rg-{TRE_ID}-ws-XXXX \
    --name nsg-ws \
    --query "securityRules[?direction=='Outbound' && destinationAddressPrefix contains '10.']" \
    --output table
  ```
  - [ ] Outbound to Core VNET allowed ✓
  - [ ] Port 443 allowed ✓
  - [ ] SharedSubnet IP range allowed ✓

**Exit Criteria:** Network connectivity validated, AMPLS capacity confirmed

---

### 1.3 Option #3b: Airlock Consolidation - Code Review

**Task:** Analyze airlock processor for storage account dependencies

- [ ] **Locate Airlock Processor Code**
  ```bash
  find . -type f -name "*airlock*processor*" -o -name "*event*processor*"
  ```
  - [ ] Airlock processor location: _____
  - [ ] Language: Python / .NET / Other

- [ ] **Review Storage Account References**
  ```bash
  grep -r "storage_account\|StorageAccount" core/terraform/airlock/ -A 3
  ```
  - [ ] How many storage accounts referenced? 5 ✓
  - [ ] Hard-coded account names? YES / NO
  - [ ] Account names from environment variables? YES / NO

- [ ] **Review EventGrid Subscriptions**
  ```bash
  grep -r "eventgrid\|event_grid" templates/workspaces/base/terraform/airlock/ -A 10
  ```
  - [ ] EventGrid subscription location: _____
  - [ ] Filter by storage account? YES / NO
  - [ ] Filter by container path? YES / NO
  - [ ] Subject filter example: _____

- [ ] **Check Blob Path Parsing Logic**
  - [ ] Find event handler code: _____
  - [ ] Does it parse blob URL? YES / NO
  - [ ] Does it extract container name? YES / NO
  - [ ] Code change needed to support containers? YES / NO
  - [ ] Estimated effort: _____ hours

- [ ] **Review RBAC Assignments**
  ```bash
  grep -r "role_assignment\|RoleAssignment" templates/workspaces/base/terraform/airlock/ -A 5
  ```
  - [ ] RBAC scope: Account-level / Container-level?
  - [ ] Managed Identity used? YES / NO
  - [ ] Can scope to container? Need to verify ✓

**Exit Criteria:** Airlock code understood, consolidation feasibility confirmed

---

## Phase 2: Prototype Development (Week 2-3)

### 2.1 Option #1: Create Storage PE Prototype

**Task:** Draft Terraform configuration for consolidated PE

- [ ] **Create Feature Branch**
  ```bash
  git checkout -b feature/pe-consolidation-quick-wins
  ```

- [ ] **Draft Consolidated Storage PE**
  
  Create: `templates/workspaces/base/terraform/storage_pe_consolidated.tf`
  
  ```hcl
  # Consolidated Private Endpoint for Storage Account
  resource "azurerm_private_endpoint" "workspace_storage_pe" {
    name                = "stgpe-${local.workspace_resource_name_suffix}"
    location            = azurerm_resource_group.ws.location
    resource_group_name = azurerm_resource_group.ws.name
    subnet_id           = module.network.services_subnet_id
    tags                = local.tre_workspace_tags
  
    lifecycle { ignore_changes = [tags] }
  
    # Blob subresource
    private_service_connection {
      name                           = "psc-blob-${local.workspace_resource_name_suffix}"
      private_connection_resource_id = azurerm_storage_account.stg.id
      is_manual_connection           = false
      subresource_names              = ["blob"]
    }
  
    # File subresource
    private_service_connection {
      name                           = "psc-file-${local.workspace_resource_name_suffix}"
      private_connection_resource_id = azurerm_storage_account.stg.id
      is_manual_connection           = false
      subresource_names              = ["file"]
    }
  
    # DFS subresource
    private_service_connection {
      name                           = "psc-dfs-${local.workspace_resource_name_suffix}"
      private_connection_resource_id = azurerm_storage_account.stg.id
      is_manual_connection           = false
      subresource_names              = ["dfs"]
    }
  
    private_dns_zone_group {
      name = "storage-dns-group"
      private_dns_zone_ids = [
        data.azurerm_private_dns_zone.blobcore.id,
        data.azurerm_private_dns_zone.filecore.id,
        data.azurerm_private_dns_zone.dfscore.id
      ]
    }
  
    depends_on = [
      module.network,
      azurerm_storage_account.stg
    ]
  }
  ```

- [ ] **Validate Terraform Syntax**
  ```bash
  terraform fmt storage_pe_consolidated.tf
  terraform validate
  ```

**Exit Criteria:** Storage PE prototype created and validated

---

### 2.2 Option #2: Create Core AMPLS Integration

**Task:** Draft Terraform to link workspace LA to Core AMPLS

- [ ] **Add Core AMPLS Data Source**
  
  In `templates/workspaces/base/terraform/data.tf`:
  
  ```hcl
  data "azurerm_monitor_private_link_scope" "core_ampls" {
    name                = "ampls-${var.tre_id}"
    resource_group_name = var.core_resource_group_name
  }
  ```

- [ ] **Create AMPLS Link Resource**
  
  In `templates/workspaces/base/terraform/azure-monitor/azure-monitor.tf`:
  
  ```hcl
  # Link workspace Log Analytics to Core AMPLS
  resource "azurerm_monitor_private_link_scoped_service" "workspace_logs" {
    name                = "svc-logs-${local.workspace_resource_name_suffix}"
    resource_group_name = var.core_resource_group_name
    scope_name          = data.azurerm_monitor_private_link_scope.core_ampls.name
    linked_resource_id  = azurerm_log_analytics_workspace.workspace.id
  }
  ```

- [ ] **Comment Out Old AMPLS PE**
  ```hcl
  # DEPRECATED: Using Core AMPLS instead
  # resource "azurerm_private_endpoint" "azure_monitor_private_endpoint" {
  #   ...
  # }
  ```

- [ ] **Add Required Variables**
  
  In `templates/workspaces/base/terraform/variables.tf`:
  
  ```hcl
  variable "core_resource_group_name" {
    type        = string
    description = "Core TRE resource group name for shared resources"
  }
  ```

**Exit Criteria:** Core AMPLS integration code drafted

---

### 2.3 Option #3b: Create Consolidated Airlock Storage

**Task:** Draft Terraform for single airlock storage account

- [ ] **Design Container Naming Convention**
  ```
  Single storage account: stgairlock{workspace_suffix}
  
  Containers:
  - import-approved
  - export-internal
  - export-inprogress
  - export-rejected
  - export-blocked
  ```

- [ ] **Draft Consolidated Airlock Storage**
  
  In `templates/workspaces/base/terraform/airlock/storage_accounts.tf`:
  
  ```hcl
  # Consolidated airlock storage account
  resource "azurerm_storage_account" "airlock" {
    count = var.enable_airlock ? 1 : 0
    
    name                             = local.airlock_storage_name
    location                         = var.location
    resource_group_name              = var.ws_resource_group_name
    account_tier                     = "Standard"
    account_replication_type         = "LRS"
    allow_nested_items_to_be_public  = false
    shared_access_key_enabled        = false
    is_hns_enabled                   = false
    
    network_rules {
      default_action = var.enable_local_debugging ? "Allow" : "Deny"
      bypass         = ["AzureServices"]
    }
    
    tags = var.tre_workspace_tags
  }
  
  # Containers within single storage account
  resource "azurerm_storage_container" "import_approved" {
    count                = var.enable_airlock ? 1 : 0
    name                 = "import-approved"
    storage_account_name = azurerm_storage_account.airlock[0].name
  }
  
  resource "azurerm_storage_container" "export_internal" {
    count                = var.enable_airlock ? 1 : 0
    name                 = "export-internal"
    storage_account_name = azurerm_storage_account.airlock[0].name
  }
  
  resource "azurerm_storage_container" "export_inprogress" {
    count                = var.enable_airlock ? 1 : 0
    name                 = "export-inprogress"
    storage_account_name = azurerm_storage_account.airlock[0].name
  }
  
  resource "azurerm_storage_container" "export_rejected" {
    count                = var.enable_airlock ? 1 : 0
    name                 = "export-rejected"
    storage_account_name = azurerm_storage_account.airlock[0].name
  }
  
  resource "azurerm_storage_container" "export_blocked" {
    count                = var.enable_airlock ? 1 : 0
    name                 = "export-blocked"
    storage_account_name = azurerm_storage_account.airlock[0].name
  }
  
  # Single Private Endpoint for airlock storage
  resource "azurerm_private_endpoint" "airlock_pe" {
    count               = var.enable_airlock ? 1 : 0
    name                = "pe-airlock-${var.short_workspace_id}"
    location            = var.location
    resource_group_name = var.ws_resource_group_name
    subnet_id           = var.services_subnet_id
    tags                = var.tre_workspace_tags
  
    private_service_connection {
      name                           = "psc-airlock-${var.short_workspace_id}"
      private_connection_resource_id = azurerm_storage_account.airlock[0].id
      is_manual_connection           = false
      subresource_names              = ["blob"]
    }
  
    private_dns_zone_group {
      name                 = "airlock-dns-group"
      private_dns_zone_ids = [data.azurerm_private_dns_zone.blobcore.id]
    }
  }
  ```

- [ ] **Update EventGrid Subscriptions**
  ```hcl
  # Add subject filters for container-specific events
  resource "azurerm_eventgrid_event_subscription" "import_approved" {
    ...
    subject_filter {
      subject_begins_with = "/blobServices/default/containers/import-approved/"
    }
  }
  ```

**Exit Criteria:** Consolidated airlock storage prototype created

---

## Phase 3: Dev Environment Testing (Week 3-4)

### 3.1 Deploy Test Workspace

**Task:** Create test workspace with all three changes

- [ ] **Prepare Test Environment**
  - [ ] Test TRE environment: tre-id = _____
  - [ ] Backup current state:
  ```bash
  terraform state pull > backup-$(date +%Y%m%d).json
  ```

- [ ] **Deploy Test Workspace**
  ```bash
  # Via TRE API or Terraform
  # Enable all features: storage, monitoring, airlock
  ```
  - [ ] Workspace deployed successfully ✓
  - [ ] Workspace ID: ws-test-pe-consolidation
  - [ ] Resource group: _____

- [ ] **Verify PE Creation**
  ```bash
  az network private-endpoint list \
    --resource-group rg-{TRE_ID}-ws-test \
    --query "[].{Name:name, Connections:length(privateLinkServiceConnections)}" \
    --output table
  ```
  - [ ] Storage PE exists: 1 PE with 3 connections ✓
  - [ ] Airlock PE exists (if enabled): 1 PE ✓
  - [ ] Azure Monitor workspace PE: ABSENT (using Core) ✓
  - [ ] Total PEs: _____ (expected: 2 if airlock enabled, 1 if not)

**Exit Criteria:** Test workspace deployed with consolidated PEs

---

### 3.2 DNS Resolution Testing

**Task:** Verify DNS for all resources

- [ ] **Test Storage DNS (Option #1)**
  
  From workspace VM:
  ```bash
  # Blob
  nslookup stg{workspace-suffix}.blob.core.windows.net
  # Expected: Private IP of consolidated PE
  
  # File
  nslookup stg{workspace-suffix}.file.core.windows.net
  # Expected: SAME private IP
  
  # DFS
  nslookup stg{workspace-suffix}.dfs.core.windows.net
  # Expected: SAME private IP
  ```
  - [ ] All 3 resolve to same IP: _____._____._____._____ ✓

- [ ] **Test Azure Monitor DNS (Option #2)**
  
  From workspace VM:
  ```bash
  nslookup {workspace-id}.ods.opinsights.azure.com
  # Expected: Private IP of CORE AMPLS PE (not workspace-specific)
  ```
  - [ ] Resolves to Core AMPLS IP: _____._____._____._____ ✓
  - [ ] Confirm same IP as Core AMPLS PE ✓

- [ ] **Test Airlock Storage DNS (Option #3b)**
  
  From workspace VM:
  ```bash
  nslookup stgairlock{workspace-suffix}.blob.core.windows.net
  # Expected: Private IP of single airlock PE
  ```
  - [ ] Resolves to private IP: _____._____._____._____ ✓

**Exit Criteria:** All DNS resolution tests pass

---

### 3.3 Functionality Testing

**Task:** Verify all services work correctly

#### Option #1: Storage Access
- [ ] **Test Blob Access**
  ```bash
  az storage blob upload \
    --account-name stg{workspace-suffix} \
    --container-name test \
    --file ./test-file.txt \
    --name test-file.txt \
    --auth-mode login
  ```
  - [ ] Upload succeeds ✓
  - [ ] Download succeeds ✓
  - [ ] List blobs succeeds ✓

- [ ] **Test File Share Access**
  ```bash
  # Windows
  net use Z: \\stg{workspace-suffix}.file.core.windows.net\{share-name}
  echo "test" > Z:\test.txt
  
  # Linux
  sudo mount -t cifs //stg{workspace-suffix}.file.core.windows.net/{share-name} /mnt/test
  echo "test" > /mnt/test/test.txt
  ```
  - [ ] Mount succeeds ✓
  - [ ] Write file succeeds ✓
  - [ ] Read file succeeds ✓

- [ ] **Test DFS/ADLS Access**
  ```bash
  az storage fs directory create \
    --account-name stg{workspace-suffix} \
    --file-system test \
    --name testdir \
    --auth-mode login
  ```
  - [ ] Directory create succeeds ✓
  - [ ] File operations succeed ✓

#### Option #2: Azure Monitor Access
- [ ] **Test Log Analytics Ingestion**
  ```bash
  # Generate logs from workspace VM
  logger "Test log from workspace VM"
  
  # Wait 5 minutes for ingestion
  
  # Query logs
  az monitor log-analytics query \
    --workspace {workspace-id} \
    --analytics-query "Syslog | where TimeGenerated > ago(10m) | limit 10"
  ```
  - [ ] Logs are ingested ✓
  - [ ] Query returns results ✓
  - [ ] No ingestion errors ✓

- [ ] **Test Metrics Collection**
  ```bash
  az monitor metrics list \
    --resource /subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Compute/virtualMachines/{vm} \
    --metric "Percentage CPU" \
    --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
    --output table
  ```
  - [ ] Metrics available ✓
  - [ ] Data collection working ✓

#### Option #3b: Airlock Operations
- [ ] **Test Import Workflow**
  ```bash
  # Upload file to import-approved container
  az storage blob upload \
    --account-name stgairlock{workspace-suffix} \
    --container-name import-approved \
    --file ./test-import.txt \
    --name test-import.txt
  ```
  - [ ] Upload succeeds ✓
  - [ ] EventGrid event triggered ✓
  - [ ] Airlock processor handles event ✓

- [ ] **Test Export Workflow**
  ```bash
  # Upload to export-internal container
  az storage blob upload \
    --account-name stgairlock{workspace-suffix} \
    --container-name export-internal \
    --file ./test-export.txt \
    --name test-export.txt
  ```
  - [ ] Upload succeeds ✓
  - [ ] Export workflow triggered ✓
  - [ ] File moves through stages correctly ✓

- [ ] **Verify Container Isolation**
  - [ ] Workspace A cannot access workspace B's containers ✓
  - [ ] RBAC correctly scoped to account level ✓
  - [ ] No cross-workspace access possible ✓

**Exit Criteria:** All functionality tests pass

---

### 3.4 Performance Benchmarking

**Task:** Compare performance vs baseline

- [ ] **Create Baseline Workspace**
  - [ ] Deploy workspace with OLD configuration (3 storage PEs, dedicated AMPLS, 5 airlock accounts)
  - [ ] Workspace ID: ws-baseline-comparison

- [ ] **Storage Performance Test**
  ```bash
  # Upload 100MB file, measure time
  time az storage blob upload \
    --account-name stg{test-workspace} \
    --container-name perf-test \
    --file ./test-100mb.bin \
    --name test-100mb.bin
  
  # Repeat on baseline workspace
  time az storage blob upload \
    --account-name stg{baseline-workspace} \
    --container-name perf-test \
    --file ./test-100mb.bin \
    --name test-100mb.bin
  ```
  - [ ] Test workspace time: _____ seconds
  - [ ] Baseline workspace time: _____ seconds
  - [ ] Delta: _____% (must be < 10%)

- [ ] **Log Analytics Ingestion Latency**
  ```bash
  # Generate log and measure time to query
  logger "PERF_TEST_$(date +%s)"
  
  # Query until log appears
  start=$(date +%s)
  while ! az monitor log-analytics query ... | grep PERF_TEST; do sleep 5; done
  end=$(date +%s)
  echo "Ingestion latency: $((end-start)) seconds"
  ```
  - [ ] Test workspace latency: _____ seconds
  - [ ] Baseline workspace latency: _____ seconds
  - [ ] Delta: _____% (must be < 20%)

- [ ] **Concurrent Operation Test**
  ```bash
  # Run blob, file, and DFS operations concurrently
  (az storage blob upload ... &)
  (cp file-to-share ... &)
  (az storage fs directory create ... &)
  wait
  ```
  - [ ] All operations succeed ✓
  - [ ] No timeout errors ✓
  - [ ] Performance acceptable ✓

**Exit Criteria:** Performance within 10% of baseline

---

## Phase 4: Security & Compliance Review (Week 4-5)

### 4.1 Security Assessment

**Task:** Document security posture impact

- [ ] **Prepare Security Analysis Document**
  
  Include:
  - [ ] Change summary (technical details)
  - [ ] Network architecture diagrams (before/after)
  - [ ] Security posture comparison:
    - Option #1: No impact (still using Private Link, same isolation)
    - Option #2: No impact (Core AMPLS same security model)
    - Option #3b: Similar impact (container vs account isolation)
  - [ ] Attack surface analysis: UNCHANGED
  - [ ] Compliance framework alignment (HIPAA, etc.): MAINTAINED

- [ ] **Threat Model Review**
  - [ ] Data exfiltration: Still prevented by Private Link + Firewall ✓
  - [ ] Cross-workspace access: Still prevented by RBAC ✓
  - [ ] Network isolation: Maintained ✓
  - [ ] Audit logging: Unchanged ✓

- [ ] **Submit for Security Review**
  - [ ] Send to security team with test results
  - [ ] Include architecture diagrams
  - [ ] Highlight: Cost optimization, no security regression

- [ ] **Address Security Questions**
  - [ ] Question 1: _____ | Answer: _____
  - [ ] Question 2: _____ | Answer: _____
  - [ ] Question 3: _____ | Answer: _____

- [ ] **Get Security Approval**
  - [ ] Security team sign-off: ✅ [Date: _____]
  - [ ] Compliance team notification: ✅ [Date: _____]
  - [ ] Documented approval stored: ✅

**Exit Criteria:** Security team approves all three changes

---

### 4.2 Compliance Validation

**Task:** Confirm compliance requirements are met

- [ ] **Review Applicable Compliance Frameworks**
  - [ ] HIPAA: Requires Private Link? YES / NO
  - [ ] FedRAMP: Requires dedicated resources? YES / NO
  - [ ] ISO 27001: Requires network isolation? YES / NO
  - [ ] GDPR: Requires data segregation? YES / NO
  - [ ] Other: _____ | Requirement: _____

- [ ] **Validate Each Change Against Compliance**
  
  Option #1 (Storage PE consolidation):
  - [ ] Maintains Private Link: ✅
  - [ ] Maintains network isolation: ✅
  - [ ] No compliance impact: ✅
  
  Option #2 (Core AMPLS):
  - [ ] Logs remain isolated per workspace: ✅
  - [ ] Shared AMPLS PE permitted by framework: ✅
  - [ ] No compliance impact: ✅
  
  Option #3b (Consolidated airlock):
  - [ ] Container-level isolation acceptable: ✅ / ❌
  - [ ] RBAC enforcement adequate: ✅ / ❌
  - [ ] Audit trail maintained: ✅
  - [ ] Compliance impact: NONE / LOW / HIGH

- [ ] **Get Compliance Sign-Off**
  - [ ] Compliance officer review: ✅ [Date: _____]
  - [ ] Written approval received: ✅
  - [ ] Conditions/caveats: _____

**Exit Criteria:** Compliance team confirms no regulatory barriers

---

## Phase 5: Migration Planning (Week 5-6)

### 5.1 Update Terraform Configuration

**Task:** Finalize production-ready Terraform code

- [ ] **Integrate Prototypes into Main Code**
  
  In `templates/workspaces/base/terraform/storage.tf`:
  - [ ] Replace old 3 PEs with consolidated PE
  - [ ] Add `moved` blocks for state migration
  - [ ] Update `depends_on` references
  
  In `templates/workspaces/base/terraform/azure-monitor/azure-monitor.tf`:
  - [ ] Remove workspace AMPLS PE
  - [ ] Add Core AMPLS link
  
  In `templates/workspaces/base/terraform/airlock/storage_accounts.tf`:
  - [ ] Replace 5 storage accounts with 1
  - [ ] Replace 5 PEs with 1 PE
  - [ ] Update EventGrid subscriptions

- [ ] **Add Terraform State Migration Blocks**
  ```hcl
  # storage.tf
  moved {
    from = azurerm_private_endpoint.stgblobpe
    to   = azurerm_private_endpoint.workspace_storage_pe
  }
  
  # Note: stgfilepe and stgdfspe will be destroyed (expected)
  ```

- [ ] **Update Resource Dependencies**
  ```bash
  # Find all depends_on references
  grep -r "depends_on.*stgblobpe\|stgfilepe\|stgdfspe" .
  
  # Update to new PE name
  ```

- [ ] **Run Terraform Validation**
  ```bash
  terraform fmt -recursive
  terraform validate
  ```

**Exit Criteria:** Production Terraform code complete and validated

---

### 5.2 Terraform Plan Analysis

**Task:** Review migration plan for safety

- [ ] **Generate Terraform Plan**
  ```bash
  cd templates/workspaces/base/terraform
  terraform init
  terraform plan -out=pe-consolidation.tfplan | tee plan-output.txt
  ```

- [ ] **Analyze Plan Output**
  
  Expected changes per workspace:
  - [ ] Storage: Replace 3 PEs with 1 PE (destroy 2, modify 1)
  - [ ] AMPLS: Destroy workspace PE, create AMPLS link
  - [ ] Airlock (if enabled): Replace 5 accounts + 5 PEs with 1 account + 1 PE
  - [ ] **VERIFY:** No destruction of storage accounts, containers, or data
  - [ ] **VERIFY:** No unintended resource changes

- [ ] **Check for Warnings**
  ```bash
  grep -i "warn\|error" plan-output.txt
  ```
  - [ ] List warnings: _____
  - [ ] Resolution plan: _____

- [ ] **Estimate Downtime**
  - [ ] PE deletion: ~3 minutes × 6 PEs = ~18 minutes
  - [ ] PE creation: ~3 minutes × 2 PEs = ~6 minutes
  - [ ] DNS propagation: ~5 minutes
  - [ ] Total estimated: ~30 minutes per workspace
  - [ ] Acceptable? If not, plan blue-green approach

**Exit Criteria:** Terraform plan reviewed, no unexpected destructive changes

---

### 5.3 Rollback Procedure

**Task:** Document and test rollback

- [ ] **Create Rollback Git Branch**
  ```bash
  git checkout -b rollback/pe-original-config
  # Copy current production config
  git checkout main -- templates/workspaces/base/terraform/
  git commit -m "Rollback: Original PE configuration"
  ```

- [ ] **Document Rollback Steps**
  
  Create: `docs/runbooks/pe-consolidation-rollback.md`
  
  ```markdown
  # PE Consolidation Rollback Procedure
  
  ## When to rollback:
  - Storage access failures after migration
  - DNS resolution issues
  - Performance degradation > 20%
  - Security incident
  
  ## Steps:
  1. Checkout rollback branch: `git checkout rollback/pe-original-config`
  2. Apply old configuration: `terraform apply`
  3. Verify DNS resolution (may take 5-10 minutes)
  4. Test storage/monitoring/airlock access
  5. Notify stakeholders
  
  ## Data impact:
  - **NO DATA LOSS** (only network path changes)
  - Storage accounts unchanged
  - Log Analytics data intact
  - Airlock data intact
  
  ## Downtime:
  - Estimated 30 minutes per workspace
  ```

- [ ] **Test Rollback in Dev**
  - [ ] Apply consolidated PE config to test workspace
  - [ ] Verify functionality
  - [ ] Execute rollback procedure
  - [ ] Verify old config works
  - [ ] Confirm no data loss
  - [ ] Document time taken: _____ minutes

**Exit Criteria:** Rollback tested and documented

---

## Phase 6: Pilot Deployment (Week 6-8)

### 6.1 Select Pilot Workspaces

**Task:** Choose low-risk workspaces for pilot

- [ ] **Define Pilot Selection Criteria**
  - [ ] Non-production or dev/test workspaces
  - [ ] Active usage (can validate functionality)
  - [ ] Engaged workspace owners (will provide feedback)
  - [ ] Mix: some with airlock, some without
  - [ ] Representative of typical usage patterns

- [ ] **Select 5-10 Pilot Workspaces**
  
  | Workspace ID | Owner | Airlock Enabled | Usage Level | Notes |
  |--------------|-------|-----------------|-------------|-------|
  | ws-pilot-01  | _____  | YES / NO        | Low / Med / High | _____ |
  | ws-pilot-02  | _____  | YES / NO        | Low / Med / High | _____ |
  | ws-pilot-03  | _____  | YES / NO        | Low / Med / High | _____ |
  | ws-pilot-04  | _____  | YES / NO        | Low / Med / High | _____ |
  | ws-pilot-05  | _____  | YES / NO        | Low / Med / High | _____ |

- [ ] **Notify Pilot Workspace Owners**
  - [ ] Email sent: ✅ [Date: _____]
  - [ ] Explained change and benefits ✅
  - [ ] Provided maintenance window (~30 min) ✅
  - [ ] Requested feedback post-migration ✅

**Exit Criteria:** Pilot workspaces selected and owners notified

---

### 6.2 Execute Pilot Migration

**Task:** Migrate pilot workspaces

- [ ] **Pre-Migration Checklist**
  
  For each pilot workspace:
  - [ ] Backup Terraform state
  - [ ] Document current PE configuration
  - [ ] Take Azure Portal screenshots
  - [ ] Baseline storage access test
  - [ ] Record current private IPs
  - [ ] Notify workspace owner (1 hour before)

- [ ] **Execute Migration**
  ```bash
  # For each pilot workspace
  cd /path/to/workspace/terraform
  
  # Apply changes
  terraform apply pe-consolidation.tfplan
  
  # Monitor for errors
  terraform show
  ```

- [ ] **Track Migration Metrics**
  
  | Workspace | Start Time | End Time | Downtime | Issues | Resolution |
  |-----------|------------|----------|----------|--------|------------|
  | ws-pilot-01 | _____ | _____ | _____ min | YES / NO | _____ |
  | ws-pilot-02 | _____ | _____ | _____ min | YES / NO | _____ |
  | ws-pilot-03 | _____ | _____ | _____ min | YES / NO | _____ |
  | ws-pilot-04 | _____ | _____ | _____ min | YES / NO | _____ |
  | ws-pilot-05 | _____ | _____ | _____ min | YES / NO | _____ |

- [ ] **Post-Migration Validation**
  
  For each pilot workspace:
  - [ ] Verify PEs created (correct count)
  - [ ] Test DNS resolution (all FQDNs)
  - [ ] Test storage access (blob, file, dfs)
  - [ ] Test Log Analytics ingestion
  - [ ] Test airlock operations (if applicable)
  - [ ] Check Azure Monitor metrics
  - [ ] Review error logs
  - [ ] Notify workspace owner: migration complete

**Exit Criteria:** All pilot workspaces migrated successfully

---

### 6.3 Monitoring Period

**Task:** Monitor pilot workspaces for 2 weeks

- [ ] **Set Up Monitoring Dashboard**
  ```bash
  # Create Azure Monitor dashboard for pilot workspaces
  # Include metrics:
  # - Private Endpoint health
  # - Storage access errors
  # - Log Analytics ingestion rate
  # - Network errors
  ```

- [ ] **Daily Monitoring Checklist**
  
  | Day | PE Health | Storage Errors | LA Ingestion | Network Errors | User Reports | Notes |
  |-----|-----------|----------------|--------------|----------------|--------------|-------|
  | Day 1 | ✅/⚠️/❌ | Count: _____ | ✅/⚠️/❌ | Count: _____ | Count: _____ | _____ |
  | Day 2 | ✅/⚠️/❌ | Count: _____ | ✅/⚠️/❌ | Count: _____ | Count: _____ | _____ |
  | Day 3 | ✅/⚠️/❌ | Count: _____ | ✅/⚠️/❌ | Count: _____ | Count: _____ | _____ |
  | Day 4 | ✅/⚠️/❌ | Count: _____ | ✅/⚠️/❌ | Count: _____ | Count: _____ | _____ |
  | Day 5 | ✅/⚠️/❌ | Count: _____ | ✅/⚠️/❌ | Count: _____ | Count: _____ | _____ |
  | ... | ... | ... | ... | ... | ... | ... |
  | Day 14 | ✅/⚠️/❌ | Count: _____ | ✅/⚠️/❌ | Count: _____ | Count: _____ | _____ |

- [ ] **Weekly User Feedback**
  - [ ] Week 1: Survey sent, responses: _____ / _____
  - [ ] Week 2: Survey sent, responses: _____ / _____
  - [ ] Issues reported: _____
  - [ ] Satisfaction score: _____ / 10

- [ ] **Performance Analysis**
  ```bash
  # Compare Week 1-2 (pilot) vs Week -2--1 (baseline)
  az monitor metrics list ... --start-time ... --end-time ...
  ```
  - [ ] Storage latency: _____ ms (before) vs _____ ms (after)
  - [ ] LA ingestion latency: _____ sec (before) vs _____ sec (after)
  - [ ] Error rate: _____% (before) vs _____% (after)
  - [ ] Variance: _____% (must be < 10%)

**Exit Criteria:** 2-week monitoring complete, metrics within acceptable range

---

## Phase 7: Production Rollout Planning (Week 8-9)

### 7.1 Pilot Review & Go/No-Go Decision

**Task:** Evaluate pilot results and decide on production rollout

- [ ] **Compile Pilot Results Report**
  
  Include:
  - [ ] Migration success rate: _____ / _____ workspaces
  - [ ] Average downtime: _____ minutes
  - [ ] Issues encountered: _____
  - [ ] Performance impact: _____% change
  - [ ] User satisfaction: _____ / 10
  - [ ] Cost savings realized: $_____ / month

- [ ] **Go/No-Go Criteria Evaluation**
  
  | Criterion | Target | Actual | Met? |
  |-----------|--------|--------|------|
  | Migration success rate | > 95% | _____% | ✅/❌ |
  | Critical issues | 0 | _____ | ✅/❌ |
  | Minor issues resolved | 100% | _____% | ✅/❌ |
  | Performance variance | < 10% | _____% | ✅/❌ |
  | User satisfaction | > 8/10 | _____ | ✅/❌ |
  | Security incidents | 0 | _____ | ✅/❌ |

- [ ] **Go/No-Go Decision Meeting**
  - [ ] Meeting date: _____
  - [ ] Attendees: Architecture, Security, Operations, Finance
  - [ ] Decision: **GO** / **NO-GO** / **GO WITH CONDITIONS**
  - [ ] Conditions (if any): _____
  - [ ] Documented approval: ✅

**Exit Criteria:** Production rollout approved

---

### 7.2 Production Rollout Strategy

**Task:** Plan batched production rollout

- [ ] **Choose Rollout Approach**
  
  Options:
  - [ ] Option A: Batch by percentage (10% → 25% → 50% → 100%)
  - [ ] Option B: Batch by workspace type (dev → test → prod)
  - [ ] Option C: Continuous (N workspaces per day)
  
  **Selected:** _____
  
  **Rationale:** _____

- [ ] **Create Rollout Schedule**
  
  Example (adjust based on total workspaces):
  
  | Batch | Workspaces | Schedule | Criteria to Proceed |
  |-------|------------|----------|---------------------|
  | Batch 1 (10%) | 1-50 | Week 9 | 0 critical issues, <5% minor issues |
  | Batch 2 (25%) | 51-125 | Week 10 | Same as Batch 1 |
  | Batch 3 (50%) | 126-250 | Week 11 | Same as Batch 1 |
  | Batch 4 (100%) | 251-500 | Week 12 | Same as Batch 1 |

- [ ] **Define Pause/Resume Criteria**
  
  **PAUSE rollout if:**
  - [ ] > 1 critical issue (data loss, security breach)
  - [ ] > 10% minor issues unresolved
  - [ ] Performance degradation > 20%
  - [ ] User satisfaction < 6/10
  
  **RESUME when:**
  - [ ] All issues resolved
  - [ ] Root cause analysis complete
  - [ ] Mitigation deployed
  - [ ] Architecture team approves

**Exit Criteria:** Rollout schedule defined and approved

---

### 7.3 Communication Plan

**Task:** Notify all stakeholders

- [ ] **Draft Communication Templates**
  
  **Template 1: General Announcement (1 week before)**
  ```
  Subject: Upcoming Infrastructure Optimization: Private Endpoint Consolidation
  
  Dear Workspace Owners,
  
  We will be performing a network optimization to reduce costs while 
  maintaining security. Your workspace will experience a brief 
  maintenance window (~30 minutes) on [DATE] at [TIME].
  
  What's changing:
  - Network infrastructure optimization
  - No user-facing changes expected
  - No data loss or migration
  
  Benefits:
  - Cost savings of $130K/year across all workspaces
  - Simplified architecture
  - Maintained security posture
  
  What to expect:
  - 30-minute maintenance window
  - Storage/monitoring may be briefly unavailable
  - No action required from you
  
  How to report issues:
  - Email: tre-support@...
  - Slack: #tre-support
  
  Thank you,
  TRE Operations Team
  ```
  
  **Template 2: 48-hour reminder**
  **Template 3: 1-hour notification**
  **Template 4: Completion notification**

- [ ] **Stakeholder Notification Schedule**
  
  | Audience | Notification | Timeline | Method |
  |----------|--------------|----------|--------|
  | All workspace owners | General announcement | 1 week before | Email |
  | Batch 1 owners | Specific notice | 48 hours before | Email |
  | Batch 1 owners | Reminder | 1 hour before | Email + Slack |
  | Support team | Briefing | 1 week before | Meeting |
  | Architecture team | Status update | Weekly | Email |
  | Finance team | Cost tracking | Monthly | Report |

- [ ] **Prepare Support Team**
  - [ ] Create troubleshooting runbook: ✅
  - [ ] Brief support team: ✅ [Date: _____]
  - [ ] Ensure escalation path clear: ✅
  - [ ] Rollback procedure accessible: ✅
  - [ ] On-call rotation assigned: ✅

**Exit Criteria:** Communication plan executed, stakeholders informed

---

## Phase 8: Production Rollout Execution (Week 9-12)

### 8.1 Batch Migration Execution

**Task:** Execute batched production rollout

**For Each Batch:**

- [ ] **Pre-Batch Checklist**
  - [ ] Review previous batch results
  - [ ] Confirm go/no-go criteria met
  - [ ] Send 48-hour notification
  - [ ] Prepare support team
  - [ ] Backup Terraform states

- [ ] **Execute Batch Migration**
  ```bash
  # For each workspace in batch
  for ws in $(cat batch-{N}-workspaces.txt); do
    echo "Migrating $ws..."
    cd /path/to/$ws/terraform
    terraform apply pe-consolidation.tfplan
    # Validate
    # Log results
  done
  ```

- [ ] **Post-Batch Validation**
  - [ ] All workspaces migrated successfully?
  - [ ] Any critical issues?
  - [ ] Performance metrics acceptable?
  - [ ] User reports reviewed?

- [ ] **Monitor for 72 Hours**
  - [ ] Day 1: Intensive monitoring (hourly checks)
  - [ ] Day 2: Regular monitoring (every 4 hours)
  - [ ] Day 3: Standard monitoring (daily checks)

- [ ] **Go/No-Go for Next Batch**
  - [ ] Criteria met? ✅ / ❌
  - [ ] Proceed to next batch? ✅ / ❌
  - [ ] If NO: pause, investigate, resolve

**Track Progress:**

| Batch | Workspaces | Start Date | End Date | Success Rate | Issues | Status |
|-------|------------|------------|----------|--------------|--------|--------|
| Batch 1 (10%) | 1-50 | _____ | _____ | _____% | _____ | ✅/⏸️/❌ |
| Batch 2 (25%) | 51-125 | _____ | _____ | _____% | _____ | ✅/⏸️/❌ |
| Batch 3 (50%) | 126-250 | _____ | _____ | _____% | _____ | ✅/⏸️/❌ |
| Batch 4 (100%) | 251-500 | _____ | _____ | _____% | _____ | ✅/⏸️/❌ |

**Exit Criteria:** All batches completed successfully

---

### 8.2 Final Validation

**Task:** Confirm all workspaces migrated correctly

- [ ] **Inventory Check**
  ```bash
  # Count PEs across all workspaces
  az network private-endpoint list \
    --query "length([?contains(resourceGroup, 'ws-')])" \
    --output tsv
  ```
  - [ ] Expected PE count: _____ (500 workspaces × 2 PEs = 1000, if all have airlock)
  - [ ] Actual PE count: _____
  - [ ] Match? ✅ / ❌

- [ ] **Cost Validation**
  ```bash
  # Get current month PE costs
  az consumption usage list \
    --start-date $(date +%Y-%m-01) \
    --query "[?contains(instanceId, 'privateEndpoints')]" \
    --output table
  ```
  - [ ] Baseline monthly cost: $_____
  - [ ] Current monthly cost: $_____
  - [ ] Savings realized: $_____ (~$10,800/month expected)

- [ ] **Random Sample Testing**
  - [ ] Select 20 random workspaces
  - [ ] Test DNS resolution
  - [ ] Test storage access
  - [ ] Test Log Analytics
  - [ ] Test airlock (if applicable)
  - [ ] All pass? ✅ / ❌

**Exit Criteria:** All workspaces validated, cost savings confirmed

---

## Phase 9: Documentation & Handover (Week 12-13)

### 9.1 Update Documentation

**Task:** Finalize all documentation

- [ ] **Update Architecture Documentation**
  - [ ] `docs/azure-tre-overview/networking.md`: PE counts updated ✅
  - [ ] `docs/azure-tre-overview/tre-resources-breakdown.md`: Updated ✅
  - [ ] Architecture diagrams regenerated ✅

- [ ] **Update Cost Documentation**
  - [ ] `architecture_review/cost-optimization-plan.md`: Mark complete ✅
  - [ ] Update projected vs actual savings ✅
  - [ ] Document lessons learned ✅

- [ ] **Create Operational Runbooks**
  - [ ] `docs/runbooks/pe-troubleshooting.md` ✅
  - [ ] `docs/runbooks/pe-consolidation-rollback.md` ✅
  - [ ] `docs/runbooks/new-workspace-deployment.md` (updated) ✅

- [ ] **Update Terraform Documentation**
  - [ ] README.md: New PE structure documented ✅
  - [ ] CHANGELOG.md: Changes logged ✅
  - [ ] Deprecation notices for old resources ✅

**Exit Criteria:** All documentation updated and published

---

### 9.2 Knowledge Transfer

**Task:** Train operations team

- [ ] **Conduct Training Session**
  - [ ] Date: _____
  - [ ] Attendees: Operations, Support, SRE teams
  - [ ] Topics covered:
    - [ ] New PE architecture
    - [ ] How to troubleshoot issues
    - [ ] Rollback procedure
    - [ ] Monitoring dashboards

- [ ] **Create Training Materials**
  - [ ] Slide deck: ✅
  - [ ] Demo video: ✅
  - [ ] FAQ document: ✅
  - [ ] Quick reference cards: ✅

- [ ] **Verify Knowledge Transfer**
  - [ ] Quiz/assessment completed: ✅
  - [ ] Operations team comfortable with changes: ✅
  - [ ] Support team ready to handle tickets: ✅

**Exit Criteria:** Operations team trained and confident

---

### 9.3 Post-Implementation Review

**Task:** Conduct retrospective

- [ ] **Compile Metrics**
  - [ ] Total workspaces migrated: _____
  - [ ] Total downtime: _____ hours
  - [ ] Success rate: _____%
  - [ ] Issues encountered: _____
  - [ ] Rollbacks required: _____
  - [ ] User satisfaction: _____ / 10
  - [ ] Cost savings (annual): $_____

- [ ] **Conduct Retrospective Meeting**
  - [ ] Date: _____
  - [ ] Attendees: Project team, stakeholders
  - [ ] What went well:
    - _____
    - _____
  - [ ] What could improve:
    - _____
    - _____
  - [ ] Action items:
    - _____
    - _____

- [ ] **Document Lessons Learned**
  - [ ] Create: `docs/postmortems/pe-consolidation-2026.md`
  - [ ] Include: Timeline, metrics, challenges, solutions
  - [ ] Share with organization ✅

**Exit Criteria:** Retrospective complete, lessons documented

---

## Success Criteria Summary

The implementation is considered successful when:

### ✅ Technical Success
- [ ] All workspaces migrated (target: 100%)
- [ ] No data loss incidents (target: 0)
- [ ] DNS resolution working (target: 100%)
- [ ] Storage/monitoring/airlock functional (target: 100%)
- [ ] Performance within baseline (target: < 10% variance)
- [ ] Error rate unchanged (target: < 5% increase)

### ✅ Operational Success
- [ ] Average downtime per workspace < 30 minutes
- [ ] Rollbacks < 5% of migrations
- [ ] Support ticket volume increase < 20%
- [ ] Operations team confident with new architecture
- [ ] Documentation complete and accurate

### ✅ Financial Success
- [ ] Annual cost savings: **$129,600** (at 500 workspaces)
- [ ] Monthly cost reduction: **$10,800**
- [ ] Per-workspace savings: **$21.60/month**
- [ ] Implementation costs < 1 year of savings
- [ ] No unexpected cost increases

### ✅ User Experience Success
- [ ] User satisfaction > 8/10
- [ ] No user-reported functionality loss
- [ ] Workspace services unaffected
- [ ] Minimal disruption to research activities

---

## Risk Mitigation Summary

| Risk | Probability | Impact | Mitigation | Status |
|------|-------------|--------|------------|--------|
| Azure feature unsupported | Low | High | ✅ Validated in Phase 1 | Mitigated |
| DNS resolution fails | Low | High | ✅ Tested in Phase 3 | Mitigated |
| Performance degradation | Low | Medium | ✅ Benchmarked in Phase 3 | Mitigated |
| Workspace service breakage | Medium | High | ✅ Pilot in Phase 6 | Mitigated |
| User disruption | Medium | Medium | ✅ Communication plan Phase 7 | Mitigated |
| Cost savings not realized | Low | Low | ✅ Track in Phase 8 | Mitigated |
| Compliance violation | Very Low | Critical | ✅ Reviewed in Phase 4 | Mitigated |
| Security incident | Very Low | Critical | ✅ Security review Phase 4 | Mitigated |

---

## Timeline Summary

| Phase | Duration | Key Deliverable |
|-------|----------|-----------------|
| 0. Initial Assessment | 2-3 days | Current state documented |
| 1. Technical Validation | 1 week | Features confirmed |
| 2. Prototype Development | 1 week | Terraform code drafted |
| 3. Dev Environment Testing | 1-2 weeks | Prototype validated |
| 4. Security & Compliance | 1-2 weeks | Approvals obtained |
| 5. Migration Planning | 1 week | Production code ready |
| 6. Pilot Deployment | 2 weeks | 5-10 workspaces migrated |
| 7. Production Planning | 1 week | Rollout strategy approved |
| 8. Production Rollout | 4 weeks | All workspaces migrated |
| 9. Documentation & Handover | 1 week | Knowledge transferred |
| **Total** | **12-14 weeks** | **$129,600/year savings** 🎉 |

---

## Next Steps

1. ✅ Complete Phase 0: Initial Assessment
2. ✅ Get stakeholder approval to proceed
3. ✅ Allocate resources (team, time, budget)
4. ✅ Begin Phase 1: Technical Validation
5. ✅ Follow this checklist step-by-step
6. ✅ Celebrate when done! 🚀

---

## Questions & Support

- **Technical questions:** [Architecture team contact]
- **Security questions:** [Security team contact]
- **Migration issues:** [DevOps/SRE team contact]
- **Cost questions:** [Finance team contact]
- **Rollback needed:** Follow `docs/runbooks/pe-consolidation-rollback.md`

---

**Document Version:** 1.0  
**Last Updated:** [Date]  
**Owner:** [Your name/team]  
**Status:** Ready for execution