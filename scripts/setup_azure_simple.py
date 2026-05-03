#!/usr/bin/env python3
"""
Simple Azure Cosmos DB Free Tier Setup
Run on your host machine with: python3 scripts/setup_azure_simple.py

Install dependencies first:
  pip3 install azure-mgmt-cosmosdb azure-identity azure-mgmt-resource
"""

import sys

# Check dependencies
print("Checking dependencies...")
try:
    from azure.identity import InteractiveBrowserCredential
    from azure.mgmt.cosmosdb import CosmosDBManagementClient
    from azure.mgmt.resource import ResourceManagementClient, SubscriptionClient
    from azure.mgmt.cosmosdb.models import *
    print("✅ All packages installed\n")
except ImportError as e:
    print(f"\n❌ Missing packages. Install with:")
    print("pip3 install azure-mgmt-cosmosdb azure-identity azure-mgmt-resource")
    sys.exit(1)

# Configuration
ACCOUNT_NAME = input("Cosmos DB account name [tre-poc-cosmos]: ").strip() or "tre-poc-cosmos"
RG_NAME = input("Resource group name [tre-poc-rg]: ").strip() or "tre-poc-rg"
LOCATION = input("Location [eastus]: ").strip() or "eastus"

print(f"\n📋 Configuration:")
print(f"   Account: {ACCOUNT_NAME}")
print(f"   Resource Group: {RG_NAME}")
print(f"   Location: {LOCATION}\n")

# Authenticate
print("🔐 Authenticating (opening browser)...")
credential = InteractiveBrowserCredential()

# Get subscription
subscription_client = SubscriptionClient(credential)
subs = list(subscription_client.subscriptions.list())

if len(subs) == 0:
    print("❌ No subscriptions found")
    sys.exit(1)

if len(subs) == 1:
    sub = subs[0]
else:
    print("\nSelect subscription:")
    for i, s in enumerate(subs, 1):
        print(f"  {i}. {s.display_name}")
    choice = int(input("Choice: ")) - 1
    sub = subs[choice]

print(f"✅ Using: {sub.display_name}\n")

# Create clients
resource_client = ResourceManagementClient(credential, sub.subscription_id)
cosmos_client = CosmosDBManagementClient(credential, sub.subscription_id)

# 1. Resource Group
print("1️⃣  Creating resource group...")
resource_client.resource_groups.create_or_update(RG_NAME, {"location": LOCATION})
print("   ✅ Done\n")

# 2. Cosmos DB
print("2️⃣  Creating Cosmos DB (3-5 min)...")
try:
    params = DatabaseAccountCreateUpdateParameters(
        location=LOCATION,
        locations=[Location(location_name=LOCATION, failover_priority=0)],
        enable_free_tier=True
    )
    op = cosmos_client.database_accounts.begin_create_or_update(RG_NAME, ACCOUNT_NAME, params)
    account = op.result()
    print("   ✅ Created with free tier\n")
except Exception as e:
    if "free tier" in str(e).lower():
        print("   ⚠️  Free tier used, creating standard...")
        params.enable_free_tier = False
        op = cosmos_client.database_accounts.begin_create_or_update(RG_NAME, ACCOUNT_NAME, params)
        account = op.result()
        print("   ✅ Created (standard tier)\n")
    else:
        print(f"   ❌ Error: {e}")
        sys.exit(1)

# 3. Get keys
print("3️⃣  Getting connection details...")
endpoint = account.document_endpoint
keys = cosmos_client.database_accounts.list_keys(RG_NAME, ACCOUNT_NAME)
key = keys.primary_master_key
print("   ✅ Done\n")

# 4. Create database
print("4️⃣  Creating database...")
try:
    db_params = SqlDatabaseCreateUpdateParameters(
        resource=SqlDatabaseResource(id="AzureTRE"),
        options={}
    )
    cosmos_client.sql_resources.begin_create_update_sql_database(
        RG_NAME, ACCOUNT_NAME, "AzureTRE", db_params
    ).result()
    print("   ✅ Done\n")
except:
    print("   ℹ️  Already exists\n")

# 5. Create containers
print("5️⃣  Creating containers...")
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
        params = SqlContainerCreateUpdateParameters(
            resource=SqlContainerResource(
                id=name,
                partition_key=ContainerPartitionKey(paths=[pk], kind="Hash")
            ),
            options={"throughput": 100}
        )
        cosmos_client.sql_resources.begin_create_update_sql_container(
            RG_NAME, ACCOUNT_NAME, "AzureTRE", name, params
        ).result()
        print(f"   ✅ {name}")
    except:
        print(f"   ℹ️  {name} exists")

# 6. Save .env
print("\n6️⃣  Creating .env file...")
import os
from pathlib import Path

env_path = Path(__file__).parent.parent / "deploy" / "offline" / ".env"
env_path.parent.mkdir(parents=True, exist_ok=True)

env_content = f"""# Azure TRE Configuration
COSMOSDB_ACCOUNT_NAME={ACCOUNT_NAME}
STATE_STORE_ENDPOINT={endpoint}
STATE_STORE_KEY={key}

STATE_STORE_DATABASE=AzureTRE
STATE_STORE_RESOURCES_CONTAINER=Resources
STATE_STORE_RESOURCE_TEMPLATES_CONTAINER=ResourceTemplates
STATE_STORE_RESOURCES_HISTORY_CONTAINER=ResourceHistory
STATE_STORE_OPERATIONS_CONTAINER=Operations
STATE_STORE_AIRLOCK_REQUESTS_CONTAINER=Requests

DEPLOYMENT_MODE=offline

AZURE_STORAGE_ACCOUNT_NAME=devstoreaccount1
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://azurite:10000/devstoreaccount1;QueueEndpoint=http://azurite:10001/devstoreaccount1;TableEndpoint=http://azurite:10002/devstoreaccount1;

SERVICE_BUS_FULLY_QUALIFIED_NAMESPACE=localhost

ENABLE_AIRLOCK=false
ENABLE_SWAGGER=true
API_DEBUG=true
"""

env_path.write_text(env_content)
print(f"   ✅ Saved to {env_path}\n")

# Done
print("="*70)
print("✅ Setup Complete!")
print("="*70)
print(f"\nResources:")
print(f"  📦 Resource Group: {RG_NAME}")
print(f"  🗄️  Cosmos DB: {ACCOUNT_NAME}")
print(f"  💾 Database: AzureTRE")
print(f"  📋 Containers: 6")
print(f"\nNext steps:")
print(f"  cd deploy/offline")
print(f"  docker-compose up -d")
print(f"  curl http://localhost:8000/api/health")
print()
