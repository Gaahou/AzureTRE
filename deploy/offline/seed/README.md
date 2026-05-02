# Cosmos DB Seed Scripts

This directory contains scripts for initializing and seeding the Cosmos DB emulator for local TRE development.

## Scripts

### cosmos-init.sh
Initializes the Cosmos DB emulator with the AzureTRE database and all required containers.

**Usage:**
```bash
# From the deploy/offline directory
docker-compose exec tre-api /bin/bash
cd /app/../deploy/offline/seed
./cosmos-init.sh
```

**Or run directly:**
```bash
docker-compose exec tre-api bash -c "cd /deploy/offline/seed && ./cosmos-init.sh"
```

**What it does:**
1. Waits for Cosmos DB emulator to be ready (up to 5 minutes)
2. Creates the `AzureTRE` database
3. Creates the following containers with `/id` partition key:
   - Resources
   - ResourceTemplates
   - ResourceHistory
   - Operations
   - Requests
   - AirlockRequests
   - AirlockRequestsHistory

**Environment Variables:**
- `STATE_STORE_ENDPOINT` - Cosmos DB endpoint (default: https://cosmosdb:8081)
- `STATE_STORE_KEY` - Cosmos DB master key (default: emulator key)
- `STATE_STORE_DATABASE` - Database name (default: AzureTRE)

### seed-templates.sh
Seeds the database with base workspace and service templates.

**Usage:**
```bash
# From the deploy/offline directory
docker-compose exec tre-api bash -c "cd /deploy/offline/seed && ./seed-templates.sh"
```

**What it does:**
1. Checks Cosmos DB connectivity
2. Loads templates from `templates.json`
3. Inserts the following templates into the ResourceTemplates container:
   - Base workspace template
   - Guacamole workspace service template
   - Linux VM user resource template
   - Windows VM user resource template
   - Firewall shared service template

**Prerequisites:**
- Run `cosmos-init.sh` first to create the database and containers
- Requires `jq` for JSON parsing (included in tre-api container)

**Environment Variables:**
- Same as `cosmos-init.sh`
- `STATE_STORE_RESOURCE_TEMPLATES_CONTAINER` - Container name (default: ResourceTemplates)

## Quick Start - Complete Setup

To set up a fresh local TRE environment:

```bash
# 1. Start services
cd deploy/offline
docker-compose up -d

# 2. Wait for services to be ready (check health)
docker-compose ps

# 3. Initialize Cosmos DB
docker-compose exec tre-api bash -c "cd /deploy/offline/seed && ./cosmos-init.sh"

# 4. Seed templates
docker-compose exec tre-api bash -c "cd /deploy/offline/seed && ./seed-templates.sh"

# 5. Verify
# Access TRE API: http://localhost:8000/api/docs
# Access Cosmos Explorer: https://localhost:8081/_explorer/index.html
```

## Templates

The seed includes the following templates:

**Workspace Templates:**
- `tre-workspace-base` - Base workspace with VNet configuration

**Workspace Service Templates:**
- `tre-service-guacamole` - Apache Guacamole remote desktop gateway

**User Resource Templates:**
- `tre-service-guacamole-linuxvm` - Ubuntu Linux VM (20.04/22.04)
- `tre-service-guacamole-windowsvm` - Windows VM (10/11/Server 2022)

**Shared Service Templates:**
- `tre-shared-service-firewall` - Azure Firewall for network security

## Containers

| Container | Partition Key | Purpose |
|-----------|---------------|---------|
| Resources | /id | Workspace, workspace service, and user resource instances |
| ResourceTemplates | /id | Template definitions for resources |
| ResourceHistory | /id | Historical changes to resources |
| Operations | /id | Deployment operations and their status |
| Requests | /id | API requests and their lifecycle |
| AirlockRequests | /id | Airlock import/export requests |
| AirlockRequestsHistory | /id | Historical airlock request changes |

## Troubleshooting

### Script fails with "Cosmos DB emulator failed to start"
- Check that the cosmosdb container is running: `docker-compose ps`
- Check cosmosdb logs: `docker-compose logs cosmosdb`
- Ensure Docker has sufficient memory (4GB+ recommended)
- Try increasing `MAX_RETRIES` in the script

### Database or container already exists
- This is normal and safe - the script handles existing resources
- To start fresh: `docker-compose down -v && docker-compose up -d`

### SSL/TLS certificate errors
- The emulator uses a self-signed certificate
- The script uses `curl -k` to bypass certificate validation
- This is safe for local development only

## Manual Verification

Access the Cosmos DB emulator web interface:
```
https://localhost:8081/_explorer/index.html
```

Or use Azure Cosmos DB Data Explorer in VS Code with:
- Endpoint: `https://localhost:8081`
- Key: `C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==`
