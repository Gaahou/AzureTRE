# TRE Scripts

This directory contains setup and testing scripts for the Azure TRE project.

## Azure Setup Scripts

### setup_azure_simple.py

**Purpose:** Provision Azure Cosmos DB Free Tier for Phase 1 testing

**Prerequisites:**
```bash
# Install Python dependencies
pip3 install -r scripts/requirements.txt
```

**Usage:**
```bash
python3 scripts/setup_azure_simple.py
```

**What it does:**
1. Authenticates to Azure (opens browser)
2. Creates resource group (default: `tre-poc-rg`)
3. Creates Cosmos DB account with free tier (default: `tre-poc-cosmos`)
4. Creates database `AzureTRE`
5. Creates 6 containers (Resources, ResourceTemplates, ResourceHistory, Operations, Requests, Migrations)
6. Generates `deploy/offline/.env` file with connection details

**Time:** ~5-7 minutes (mostly Cosmos DB provisioning)

**Cost:** $0 with free tier (1000 RU/s included)

---

## Testing Scripts

### test_phase1_docker.sh

**Purpose:** Automated Phase 1 testing with Docker

**Usage:**
```bash
# After Azure setup is complete
./scripts/test_phase1_docker.sh
```

**What it tests:**
- Docker services start correctly
- API connects to Azure Cosmos DB
- Health endpoints respond
- Swagger UI accessible
- Offline mode configuration

---

## Requirements

| Script | Dependencies | Install Command |
|--------|--------------|-----------------|
| `setup_azure_simple.py` | Azure Python SDKs | `pip3 install -r scripts/requirements.txt` |
| `test_phase1_docker.sh` | Docker Desktop | N/A (system dependency) |

---

## Quick Start

```bash
# 1. Install dependencies
pip3 install -r scripts/requirements.txt

# 2. Set up Azure Cosmos DB
python3 scripts/setup_azure_simple.py

# 3. Run tests
./scripts/test_phase1_docker.sh
```

---

## Cleanup

### cleanup_phase1.sh

**Purpose:** Clean up Phase 1 Azure resources and/or local Docker environment

**Usage:**
```bash
# Clean up both Azure and local (default)
./scripts/cleanup_phase1.sh

# Only delete Azure resources
./scripts/cleanup_phase1.sh --azure-only

# Only clean up Docker containers
./scripts/cleanup_phase1.sh --local-only
```

**What it cleans:**
- Azure resource group (tre-poc-rg)
- Cosmos DB account and containers
- Docker containers (tre-api, tre-azurite)
- Docker volumes and networks

**Safety:**
- Prompts for confirmation before deletion
- Shows what will be deleted
- Cannot be undone (destructive operation)

**Note:** Preserves .env file and all documentation for reference.

### Uninstall Dependencies

After testing is complete, you can uninstall the Azure SDK packages:

```bash
./scripts/uninstall_requirements.sh
```

This removes all packages from `requirements.txt` and their dependencies.

### Manual Cleanup

Alternatively, delete Azure resources manually:

```bash
# Using Azure CLI
az group delete --name tre-poc-rg --yes

# Or via Azure Portal
# Navigate to resource group → Delete resource group
```

**Cost Impact:** Deleting resources immediately stops any charges (~$0.05/day saved).

---

## Troubleshooting

### "Missing packages" error
```bash
pip3 install -r scripts/requirements.txt
```

### "Authentication failed" error
- Ensure you're logged into Azure in your browser
- Check your subscription is active
- Try: `az login` if you have Azure CLI installed

### "Free tier already used" warning
- Azure allows one free tier Cosmos DB per subscription
- Script will automatically create standard tier (small cost: ~$0.01-0.05/day)
- Or use existing free tier account by changing the account name

---

## Documentation

- **Azure Free Tier Setup Guide:** [docs/azure-free-tier-setup.md](../docs/azure-free-tier-setup.md)
- **Cosmos DB Workarounds:** [docs/phase1-cosmos-emulator-workarounds.md](../docs/phase1-cosmos-emulator-workarounds.md)
- **Phase 1 Final Status:** [docs/phase1-final-status.md](../docs/phase1-final-status.md)

---

**Last Updated:** 2026-05-02  
**Phase:** 1 (Local API with Emulators)