# Azure Free Tier Setup Guide (Option 2)

**Purpose:** Set up Azure Cosmos DB Free Tier for Phase 1 testing  
**Time Required:** 10-15 minutes  
**Cost:** $0 (Free Tier: 1000 RU/s, 25GB storage)

---

## Prerequisites

- Azure subscription (free tier available at https://azure.microsoft.com/free/)
- Azure CLI installed (`brew install azure-cli` on macOS)
- Docker Desktop running

---

## Step 1: Login to Azure

```bash
# Login to your Azure account
az login

# Set your subscription (if you have multiple)
az account list --output table
az account set --subscription "YOUR_SUBSCRIPTION_NAME_OR_ID"

# Verify current subscription
az account show --output table
```

---

## Step 2: Create Resource Group

```bash
# Create resource group for TRE PoC resources
az group create \
  --name tre-poc-rg \
  --location eastus

# Verify resource group created
az group show --name tre-poc-rg --output table
```

**Note:** You can use an existing resource group if preferred. Just replace `tre-poc-rg` with your resource group name.

---

## Step 3: Create Cosmos DB Account (Free Tier)

```bash
# Create Cosmos DB account with free tier enabled
az cosmosdb create \
  --name tre-poc-cosmos \
  --resource-group tre-poc-rg \
  --enable-free-tier true \
  --locations regionName=eastus failoverPriority=0 \
  --default-consistency-level Session

# This takes 3-5 minutes to provision
# Wait for "provisioningState": "Succeeded"
```

**Important:** 
- Account name must be globally unique (3-44 characters, lowercase, alphanumeric, hyphens)
- If `tre-poc-cosmos` is taken, use `tre-poc-cosmos-YOURNAME` or similar
- Free tier limited to **one account per subscription**
- If you get "free tier already used" error, you can create without `--enable-free-tier true` flag (small cost, ~$0.01/day for dev workload)

**Check provisioning status:**
```bash
az cosmosdb show \
  --name tre-poc-cosmos \
  --resource-group tre-poc-rg \
  --query "{name:name, status:provisioningState}" \
  --output table
```

---

## Step 4: Get Connection Details

```bash
# Get the endpoint URL
az cosmosdb show \
  --name tre-poc-cosmos \
  --resource-group tre-poc-rg \
  --query "documentEndpoint" \
  --output tsv

# Get the primary key
az cosmosdb keys list \
  --name tre-poc-cosmos \
  --resource-group tre-poc-rg \
  --query "primaryMasterKey" \
  --output tsv
```

**Save these values** - you'll need them in the next step.

---

## Step 5: Create .env File

Create `deploy/offline/.env` with your connection details:

```bash
# Navigate to deploy/offline directory
cd deploy/offline

# Copy example file
cp .env.example .env

# Edit .env file with your values
# Replace the following placeholders:
#   - your-cosmos-account-name (e.g., tre-poc-cosmos)
#   - your-primary-key-here (from Step 4)
```

**Example .env file:**
```bash
# Cosmos DB Configuration (Azure Free Tier)
COSMOSDB_ACCOUNT_NAME=tre-poc-cosmos
STATE_STORE_ENDPOINT=https://tre-poc-cosmos.documents.azure.com:443/
STATE_STORE_KEY=abc123YourActualPrimaryKeyHere456def==

# Database Configuration
STATE_STORE_DATABASE=AzureTRE
STATE_STORE_RESOURCES_CONTAINER=Resources
STATE_STORE_RESOURCE_TEMPLATES_CONTAINER=ResourceTemplates
STATE_STORE_RESOURCES_HISTORY_CONTAINER=ResourceHistory
STATE_STORE_OPERATIONS_CONTAINER=Operations
STATE_STORE_AIRLOCK_REQUESTS_CONTAINER=Requests

# Deployment Mode
DEPLOYMENT_MODE=offline

# Storage (Azurite - already configured)
AZURE_STORAGE_ACCOUNT_NAME=devstoreaccount1
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://azurite:10000/devstoreaccount1;QueueEndpoint=http://azurite:10001/devstoreaccount1;TableEndpoint=http://azurite:10002/devstoreaccount1;

# Service Bus
SERVICE_BUS_FULLY_QUALIFIED_NAMESPACE=localhost

# Feature Flags
ENABLE_AIRLOCK=false
ENABLE_SWAGGER=true
API_DEBUG=true
```

**Security Note:** Add `.env` to your `.gitignore` (should already be there). Never commit credentials to git.

---

## Step 6: Initialize Cosmos DB Database and Containers

```bash
# Create database
az cosmosdb sql database create \
  --account-name tre-poc-cosmos \
  --resource-group tre-poc-rg \
  --name AzureTRE

# Create containers (one by one)
az cosmosdb sql container create \
  --account-name tre-poc-cosmos \
  --resource-group tre-poc-rg \
  --database-name AzureTRE \
  --name Resources \
  --partition-key-path "/id" \
  --throughput 400

az cosmosdb sql container create \
  --account-name tre-poc-cosmos \
  --resource-group tre-poc-rg \
  --database-name AzureTRE \
  --name ResourceTemplates \
  --partition-key-path "/id" \
  --throughput 400

az cosmosdb sql container create \
  --account-name tre-poc-cosmos \
  --resource-group tre-poc-rg \
  --database-name AzureTRE \
  --name ResourceHistory \
  --partition-key-path "/resourceId" \
  --throughput 400

az cosmosdb sql container create \
  --account-name tre-poc-cosmos \
  --resource-group tre-poc-rg \
  --database-name AzureTRE \
  --name Operations \
  --partition-key-path "/id" \
  --throughput 400

az cosmosdb sql container create \
  --account-name tre-poc-cosmos \
  --resource-group tre-poc-rg \
  --database-name AzureTRE \
  --name Requests \
  --partition-key-path "/id" \
  --throughput 400

# Optional: Create Migrations container for future use
az cosmosdb sql container create \
  --account-name tre-poc-cosmos \
  --resource-group tre-poc-rg \
  --database-name AzureTRE \
  --name Migrations \
  --partition-key-path "/id" \
  --throughput 400
```

**Note:** Free tier includes 1000 RU/s shared across all containers. We allocate 400 RU/s per container (6 containers = 2400 RU/s total), which exceeds free tier. Azure will charge ~$0.05/day for the additional 1400 RU/s. For testing purposes, you can reduce throughput to 100 RU/s per container.

**Cost-optimized version (stays within free tier):**
```bash
# Use --throughput 100 for each container instead of 400
# Total: 600 RU/s across 6 containers (within 1000 RU/s free tier)
```

---

## Step 7: Verify Azure Setup

```bash
# List all containers
az cosmosdb sql container list \
  --account-name tre-poc-cosmos \
  --resource-group tre-poc-rg \
  --database-name AzureTRE \
  --query "[].name" \
  --output table

# Should show:
# Resources
# ResourceTemplates
# ResourceHistory
# Operations
# Requests
# Migrations
```

---

## Step 8: Start TRE Services

```bash
# Navigate to deploy/offline directory (if not already there)
cd /Users/andrew/Desktop/PoC/AzureTRE/deploy/offline

# Ensure .env file exists and is populated
cat .env | grep STATE_STORE_ENDPOINT

# Clean any old containers
docker-compose down -v

# Start services (only Azurite and TRE API now)
docker-compose up -d

# Check container status
docker-compose ps

# Expected output:
# tre-api       Up (healthy)
# tre-azurite   Up
# (No cosmosdb container - using Azure Free Tier)
```

---

## Step 9: Verify API Connection

```bash
# Wait for API to start (30 seconds)
sleep 30

# Check API logs - should show successful Cosmos DB connection
docker-compose logs tre-api | tail -30

# Expected log messages:
# - "Starting Azure TRE API in OFFLINE mode"
# - "Service Bus disabled (offline mode)"
# - "Database 'AzureTRE' found"
# - "Container 'Resources' verified"
# - "Container 'ResourceTemplates' verified"
# - etc.

# Test health endpoint
curl http://localhost:8000/api/health

# Expected response: {"message": "OK"} or similar
```

---

## Step 10: Access Services

Once the API is healthy, you can access:

### Swagger UI (API Documentation)
```
http://localhost:8000/api/docs
```

### Health Check
```
http://localhost:8000/api/health
```

### Azure Portal (Cosmos DB Data Explorer)
```
https://portal.azure.com
→ Search for "tre-poc-cosmos"
→ Data Explorer
→ View AzureTRE database and containers
```

---

## Troubleshooting

### Issue: "Free tier already used"

**Solution:** Either:
1. Use existing free tier Cosmos DB account
2. Create without free tier (small cost: ~$0.01-0.05/day)
   ```bash
   az cosmosdb create \
     --name tre-poc-cosmos \
     --resource-group tre-poc-rg \
     --locations regionName=eastus failoverPriority=0
   ```

### Issue: "Account name already exists"

**Solution:** Choose a different account name
```bash
# Try with your name or timestamp
az cosmosdb create \
  --name tre-poc-cosmos-yourname \
  --resource-group tre-poc-rg \
  --enable-free-tier true
```

### Issue: API logs show "Database 'AzureTRE' not found"

**Solution:** Database not created yet
```bash
# Create database
az cosmosdb sql database create \
  --account-name tre-poc-cosmos \
  --resource-group tre-poc-rg \
  --name AzureTRE
```

### Issue: API logs show "Container 'Resources' not found"

**Solution:** Containers not created yet - run Step 6 commands

### Issue: API logs show connection errors to Cosmos DB

**Solution:** Check .env file configuration
```bash
# Verify .env file exists
cat deploy/offline/.env

# Verify endpoint and key are correct
az cosmosdb show \
  --name tre-poc-cosmos \
  --resource-group tre-poc-rg \
  --query "documentEndpoint"

az cosmosdb keys list \
  --name tre-poc-cosmos \
  --resource-group tre-poc-rg \
  --query "primaryMasterKey"
```

### Issue: Docker-compose fails to load .env file

**Solution:** Make sure .env is in deploy/offline directory
```bash
ls -la /Users/andrew/Desktop/PoC/AzureTRE/deploy/offline/.env

# If missing, create it from .env.example
cp .env.example .env
# Then edit with your values
```

---

## Running Tests

Once everything is up and running:

```bash
# Run Phase 1 test suite (from project root)
cd /Users/andrew/Desktop/PoC/AzureTRE
./scripts/test_phase1_docker.sh

# Or manually test key endpoints
curl http://localhost:8000/api/health
curl http://localhost:8000/api/docs
```

---

## Cleanup (When Done Testing)

```bash
# Stop Docker containers
cd deploy/offline
docker-compose down

# Delete Azure resources (to avoid any charges)
az group delete --name tre-poc-rg --yes --no-wait

# Or keep for future testing (free tier = $0)
```

**Note:** Free tier Cosmos DB has no ongoing cost if you stay within 1000 RU/s and 25GB storage limits.

---

## Cost Summary

| Resource | Cost |
|----------|------|
| **Cosmos DB Free Tier** | $0 (up to 1000 RU/s) |
| **Cosmos DB exceeding free tier** | ~$0.05/day ($1.50/month) for 2400 RU/s |
| **Storage (<25GB)** | $0 |
| **Azurite (local)** | $0 |
| **TRE API (local)** | $0 |

**Recommendation:** Use 100 RU/s per container (600 RU/s total) to stay within free tier during testing.

---

## Next Steps

After successful setup:

1. ✅ Verify all containers are healthy
2. ✅ Test API endpoints via Swagger UI
3. ✅ Run automated test suite
4. ✅ Close Story #348 and Feature #113
5. ⏭️ Move to Phase 2: Resource Processor Integration

---

## Support

- **Azure Free Tier Docs:** https://docs.microsoft.com/azure/cosmos-db/free-tier
- **Cosmos DB CLI Docs:** https://docs.microsoft.com/cli/azure/cosmosdb
- **Workaround Guide:** [docs/phase1-cosmos-emulator-workarounds.md](phase1-cosmos-emulator-workarounds.md)

---

**Created:** 2026-05-02  
**For:** Phase 1 Testing (Story #348, Feature #113)  
**Author:** Claude Sonnet 4.5