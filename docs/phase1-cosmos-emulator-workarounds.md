# Phase 1: Cosmos DB Emulator Workarounds

## Problem Summary

The Azure Cosmos DB Linux Emulator has known issues when running in Docker with custom hostname configurations. The emulator requires specific IP address settings for inter-container communication, but these settings conflict with Docker's hostname-based service discovery.

### Symptoms

- Cosmos DB container status: `Up (health: starting)` indefinitely
- Healthcheck never succeeds
- API logs show: `Connection refused` or `Name or service not known` errors
- Database 'AzureTRE' not found errors even after seeding attempts

### Root Causes

1. **IP Address Override Conflict:** Setting `AZURE_COSMOS_EMULATOR_IP_ADDRESS_OVERRIDE` to hostname causes healthcheck failures
2. **SDK Endpoint Resolution:** Azure Cosmos SDK resolves endpoints and rewrites them to IP addresses
3. **Network Timing:** Emulator takes 60-90 seconds to fully start and become responsive
4. **Bash Compatibility:** Seed scripts use bash 4+ features (associative arrays) not available in macOS bash 3.2

---

## Workaround Options

### Option 1: Windows Cosmos DB Emulator (Recommended for Development)

**Status:** ✅ Most stable option  
**Effort:** 30 minutes  
**Use Case:** Local development on Windows

The Windows version of Cosmos DB Emulator is more stable and has better Docker support.

#### Prerequisites
- Windows 10/11 or Windows Server 2016+
- Docker Desktop for Windows
- 4GB+ RAM allocated to Docker

#### Steps

1. **Pull Windows Cosmos DB Emulator Image**
   ```powershell
   docker pull mcr.microsoft.com/cosmosdb/windows/azure-cosmos-emulator:latest
   ```

2. **Update docker-compose.yml**
   ```yaml
   # deploy/offline/docker-compose.yml
   services:
     cosmosdb:
       image: mcr.microsoft.com/cosmosdb/windows/azure-cosmos-emulator:latest
       platform: windows/amd64
       # Remove IP_ADDRESS_OVERRIDE - not needed on Windows
       environment:
         - AZURE_COSMOS_EMULATOR_PARTITION_COUNT=10
         - AZURE_COSMOS_EMULATOR_ENABLE_DATA_PERSISTENCE=true
       # Keep rest of config the same
   ```

3. **Start Services**
   ```bash
   docker-compose up -d
   ```

4. **Run Seed Scripts**
   ```bash
   # Windows has newer bash in Git Bash or WSL
   bash seed/cosmos-init.sh
   bash seed/seed-templates.sh
   ```

**Pros:**
- ✅ More stable than Linux emulator
- ✅ Better documented
- ✅ Fewer networking issues

**Cons:**
- ❌ Requires Windows host
- ❌ Larger image size (~2GB)
- ❌ Cannot run on macOS/Linux hosts

---

### Option 2: Azure Cosmos DB Free Tier (Recommended for Testing)

**Status:** ✅ Most reliable option  
**Effort:** 20 minutes  
**Use Case:** Integration testing, CI/CD, team environments

Use real Azure Cosmos DB with free tier (no cost for development/testing).

#### Prerequisites
- Azure subscription (free tier available)
- Azure CLI installed

#### Steps

1. **Create Free Tier Cosmos DB Account**
   ```bash
   # Login to Azure
   az login

   # Create resource group
   az group create --name tre-dev-rg --location eastus

   # Create Cosmos DB account (free tier)
   az cosmosdb create \
     --name tre-dev-cosmos \
     --resource-group tre-dev-rg \
     --enable-free-tier true \
     --locations regionName=eastus failoverPriority=0

   # Get connection details
   az cosmosdb keys list \
     --name tre-dev-cosmos \
     --resource-group tre-dev-rg \
     --type connection-strings
   ```

2. **Update .env File**
   ```bash
   # deploy/offline/.env
   DEPLOYMENT_MODE=offline
   STATE_STORE_ENDPOINT=https://tre-dev-cosmos.documents.azure.com:443/
   STATE_STORE_KEY=<primary-key-from-above>
   STATE_STORE_DATABASE=AzureTRE
   # ... rest of config
   ```

3. **Remove Cosmos DB from docker-compose.yml**
   ```yaml
   # Comment out or remove cosmosdb service
   # services:
   #   cosmosdb:
   #     ...

   # Update API dependencies
   services:
     tre-api:
       depends_on:
         azurite:
           condition: service_started
       # Remove cosmosdb dependency
   ```

4. **Initialize Database**
   ```bash
   # Use Azure CLI or Portal to create database and containers
   az cosmosdb sql database create \
     --account-name tre-dev-cosmos \
     --resource-group tre-dev-rg \
     --name AzureTRE

   # Create containers
   for container in Resources ResourceTemplates ResourceHistory Operations Requests Migrations; do
     az cosmosdb sql container create \
       --account-name tre-dev-cosmos \
       --resource-group tre-dev-rg \
       --database-name AzureTRE \
       --name $container \
       --partition-key-path "/id"
   done
   ```

**Pros:**
- ✅ Most reliable - production-grade service
- ✅ Free tier: 1000 RU/s, 25GB storage (plenty for dev/test)
- ✅ Works from any platform
- ✅ Same API as emulator
- ✅ Better performance
- ✅ Data persistence between sessions

**Cons:**
- ❌ Requires Azure subscription
- ❌ Internet connection required
- ❌ Not fully "offline"

---

### Option 3: Manual Database Seeding with Python

**Status:** ✅ Works with current setup  
**Effort:** 5 minutes per restart  
**Use Case:** Quick testing, troubleshooting

Manually seed the database after containers start.

#### Prerequisites
- Cosmos DB emulator running (even if unhealthy)
- Python 3.12+ available

#### Steps

1. **Start Services Without Volume Cleanup**
   ```bash
   cd deploy/offline
   docker-compose up -d
   ```

2. **Wait for Cosmos DB to Start**
   ```bash
   # Wait 120 seconds for emulator to initialize
   sleep 120
   
   # Check logs
   docker-compose logs cosmosdb | grep "Started"
   ```

3. **Run Python Seeding Script**
   ```bash
   # From project root
   docker exec -i tre-api python3 << 'EOF'
   from azure.cosmos import CosmosClient, exceptions
   import sys

   ENDPOINT = "https://cosmosdb:8081"
   KEY = "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="
   
   print("🚀 Seeding Cosmos DB...")
   
   try:
       client = CosmosClient(ENDPOINT, KEY, connection_verify=False)
       
       # Create database
       try:
           database = client.create_database("AzureTRE")
           print("✅ Created database: AzureTRE")
       except exceptions.CosmosResourceExistsError:
           print("ℹ️  Database already exists")
           database = client.get_database_client("AzureTRE")
       
       # Create containers
       containers = {
           "Resources": "/id",
           "ResourceTemplates": "/id",
           "ResourceHistory": "/resourceId",
           "Operations": "/id",
           "Requests": "/id",
           "Migrations": "/id"
       }
       
       for name, pk in containers.items():
           try:
               database.create_container(
                   id=name,
                   partition_key={"paths": [pk], "kind": "Hash"}
               )
               print(f"✅ Created container: {name}")
           except exceptions.CosmosResourceExistsError:
               print(f"ℹ️  Container exists: {name}")
       
       print("\n✅ Database seeding complete!")
       sys.exit(0)
       
   except Exception as e:
       print(f"\n❌ Error: {e}")
       import traceback
       traceback.print_exc()
       sys.exit(1)
   EOF
   ```

4. **Restart API**
   ```bash
   docker-compose restart tre-api
   
   # Wait for API to start
   sleep 30
   
   # Test
   curl http://localhost:8000/api/health
   ```

**Pros:**
- ✅ Works with current docker-compose setup
- ✅ No changes to configuration needed
- ✅ Can be scripted
- ✅ Uses existing API container (has all dependencies)

**Cons:**
- ❌ Manual step required after each restart
- ❌ Must wait for emulator to be partially ready
- ❌ Not automated

---

### Option 4: Use Bash 4+ for Seed Scripts

**Status:** ✅ Fixes seed script errors  
**Effort:** 10 minutes  
**Use Case:** macOS development

Install modern bash and run seed scripts properly.

#### Prerequisites
- macOS with Homebrew
- Or Docker container with bash 4+

#### Steps

**Option A: Install Bash 5 on macOS**

```bash
# Install bash via Homebrew
brew install bash

# Add to shells
sudo bash -c 'echo /opt/homebrew/bin/bash >> /etc/shells'

# Run seed scripts with modern bash
/opt/homebrew/bin/bash deploy/offline/seed/cosmos-init.sh
/opt/homebrew/bin/bash deploy/offline/seed/seed-templates.sh
```

**Option B: Run Seed Scripts in Docker Container**

```bash
# Use Azure CLI container which has bash 5
docker run --rm --network tre-local \
  -v "$PWD/deploy/offline/seed:/seed" \
  -e STATE_STORE_ENDPOINT=https://cosmosdb:8081 \
  mcr.microsoft.com/azure-cli:latest \
  bash /seed/cosmos-init.sh

docker run --rm --network tre-local \
  -v "$PWD/deploy/offline/seed:/seed" \
  -e STATE_STORE_ENDPOINT=https://cosmosdb:8081 \
  mcr.microsoft.com/azure-cli:latest \
  bash /seed/seed-templates.sh
```

**Pros:**
- ✅ Makes existing seed scripts work
- ✅ Proper solution for bash compatibility
- ✅ Scripts work as designed

**Cons:**
- ❌ Requires Homebrew on macOS
- ❌ Adds dependency
- ❌ Still requires emulator to be healthy

---

### Option 5: Simplified Docker Compose (127.0.0.1 Override)

**Status:** ⚠️ Partial workaround  
**Effort:** 5 minutes  
**Use Case:** Single-machine testing only

Revert to `127.0.0.1` IP override and use host networking.

#### Steps

1. **Update docker-compose.yml**
   ```yaml
   # deploy/offline/docker-compose.yml
   services:
     cosmosdb:
       image: mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:latest
       container_name: tre-cosmosdb-emulator
       platform: linux/amd64
       network_mode: host  # Use host networking
       environment:
         - AZURE_COSMOS_EMULATOR_PARTITION_COUNT=10
         - AZURE_COSMOS_EMULATOR_ENABLE_DATA_PERSISTENCE=true
         - AZURE_COSMOS_EMULATOR_IP_ADDRESS_OVERRIDE=127.0.0.1
       volumes:
         - cosmosdb-data:/data/db
   ```

2. **Update API Configuration**
   ```yaml
   tre-api:
     environment:
       - STATE_STORE_ENDPOINT=https://localhost:8081
       # Change from https://cosmosdb:8081
   ```

3. **Start and Seed**
   ```bash
   docker-compose up -d
   sleep 120
   
   # Seed from host machine
   python3 scripts/seed_cosmos_simple.py
   ```

**Pros:**
- ✅ Simpler networking
- ✅ Emulator healthcheck works
- ✅ Can access from host easily

**Cons:**
- ❌ Only works on single machine
- ❌ Containers must use host network
- ❌ Port conflicts possible
- ❌ Not suitable for team environments

---

## Automated Setup Scripts

### Complete Test Script (Option 3 - Manual Seeding)

Create `scripts/test_phase1_with_seeding.sh`:

```bash
#!/bin/bash
# Complete Phase 1 test with manual database seeding

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT/deploy/offline"

echo "🚀 Phase 1 Complete Test"
echo "========================"

# Step 1: Clean start
echo "1️⃣  Cleaning up old containers..."
docker-compose down -v

# Step 2: Start services
echo "2️⃣  Starting services..."
docker-compose up -d

# Step 3: Wait for Cosmos DB
echo "3️⃣  Waiting for Cosmos DB (120s)..."
sleep 120

# Check if cosmosdb started
if docker-compose logs cosmosdb | grep -q "Started"; then
    echo "   ✅ Cosmos DB started"
else
    echo "   ⚠️  Cosmos DB may not be fully ready, continuing anyway..."
fi

# Step 4: Seed database
echo "4️⃣  Seeding database..."
docker exec -i tre-api python3 << 'EOF'
from azure.cosmos import CosmosClient, exceptions
ENDPOINT = "https://cosmosdb:8081"
KEY = "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="
client = CosmosClient(ENDPOINT, KEY, connection_verify=False)
try:
    database = client.create_database("AzureTRE")
    print("✅ Created database")
except exceptions.CosmosResourceExistsError:
    database = client.get_database_client("AzureTRE")
    print("ℹ️  Database exists")
for name, pk in {
    "Resources": "/id",
    "ResourceTemplates": "/id",
    "ResourceHistory": "/resourceId",
    "Operations": "/id",
    "Requests": "/id",
    "Migrations": "/id"
}.items():
    try:
        database.create_container(id=name, partition_key={"paths": [pk], "kind": "Hash"})
        print(f"✅ {name}")
    except exceptions.CosmosResourceExistsError:
        print(f"ℹ️  {name} exists")
EOF

if [ $? -eq 0 ]; then
    echo "   ✅ Database seeded"
else
    echo "   ❌ Seeding failed"
    exit 1
fi

# Step 5: Restart API
echo "5️⃣  Restarting API..."
docker-compose restart tre-api
sleep 30

# Step 6: Test endpoints
echo "6️⃣  Testing API..."
HEALTH=$(curl -s -m 10 http://localhost:8000/api/health || echo "TIMEOUT")

if echo "$HEALTH" | grep -qE "ok|healthy|success"; then
    echo "   ✅ API is healthy"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ Phase 1 Test PASSED!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Services:"
    echo "  - API:       http://localhost:8000/api/docs"
    echo "  - Health:    http://localhost:8000/api/health"
    echo "  - Cosmos DB: https://localhost:10250/_explorer/index.html"
    echo ""
else
    echo "   ❌ API health check failed"
    echo "   Response: $HEALTH"
    exit 1
fi
```

Make it executable:
```bash
chmod +x scripts/test_phase1_with_seeding.sh
```

Run it:
```bash
./scripts/test_phase1_with_seeding.sh
```

---

## Comparison Matrix

| Workaround | Effort | Reliability | Platform | Internet | Automation | Recommendation |
|-----------|--------|-------------|----------|----------|------------|----------------|
| Windows Emulator | Medium | ⭐⭐⭐⭐⭐ | Windows only | No | Yes | ✅ Best for Windows devs |
| Azure Free Tier | Low | ⭐⭐⭐⭐⭐ | Any | Yes | Yes | ✅ Best for teams |
| Manual Seeding | Low | ⭐⭐⭐ | Any | No | Partial | ✅ Quick testing |
| Bash 4+ | Low | ⭐⭐⭐ | Any | No | Yes | ✅ Script compatibility |
| Host Networking | Low | ⭐⭐ | Single machine | No | Yes | ⚠️ Limited use |

---

## Recommendations by Use Case

### For Individual Developers (macOS/Linux)
1. **Primary:** Manual Seeding (Option 3) - works now with existing setup
2. **Alternative:** Azure Free Tier (Option 2) - most reliable

### For Individual Developers (Windows)
1. **Primary:** Windows Emulator (Option 1) - most stable
2. **Alternative:** Azure Free Tier (Option 2)

### For Team Environments
1. **Primary:** Azure Free Tier (Option 2) - shared, reliable
2. **Alternative:** CI/CD with Azure Cosmos (same as Option 2)

### For CI/CD Pipelines
1. **Primary:** Azure Free Tier (Option 2) - consistent, fast
2. **Alternative:** Windows build agents with Windows Emulator

### For Demonstrations
1. **Primary:** Azure Free Tier (Option 2) - most reliable
2. **Alternative:** Manual Seeding (Option 3) - truly offline

---

## Troubleshooting Common Issues

### Issue: "Database 'AzureTRE' not found"

**Cause:** Database not seeded yet

**Solution:**
```bash
# Run manual seeding script (Option 3)
docker exec -i tre-api python3 << 'EOF'
from azure.cosmos import CosmosClient, exceptions
client = CosmosClient("https://cosmosdb:8081", "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==", connection_verify=False)
database = client.create_database("AzureTRE")
EOF
```

### Issue: "Connection refused" to 127.0.0.1:8081

**Cause:** SDK resolving cosmosdb hostname to 127.0.0.1

**Solution:** Use Azure Free Tier (Option 2) or Windows Emulator (Option 1)

### Issue: Cosmos DB healthcheck never succeeds

**Cause:** IP address override conflicts with healthcheck

**Solution:** 
- Use Windows Emulator (Option 1)
- Or use Azure Free Tier (Option 2)
- Or accept unhealthy status and manually seed (Option 3)

### Issue: Bash script errors on macOS

**Cause:** macOS ships with bash 3.2, scripts need bash 4+

**Solution:**
```bash
# Install bash 5
brew install bash

# Run scripts with new bash
/opt/homebrew/bin/bash deploy/offline/seed/cosmos-init.sh
```

---

## Next Steps

1. **Choose your workaround** based on your environment and use case
2. **Test the chosen approach** with the provided scripts
3. **Document team choice** in project README
4. **Update CI/CD** if using Azure Free Tier
5. **Continue to Phase 2** - the application code is ready

---

## Support & References

- **Cosmos DB Emulator Docs:** https://docs.microsoft.com/azure/cosmos-db/local-emulator
- **Docker Networking:** https://docs.docker.com/network/
- **Azure Cosmos DB Free Tier:** https://docs.microsoft.com/azure/cosmos-db/free-tier
- **Issue Tracker:** File issues at project repo

**Related Work Items:** #348, #113, #357

**Last Updated:** 2026-05-02  
**Author:** Claude Sonnet 4.5