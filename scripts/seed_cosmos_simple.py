#!/usr/bin/env python3
"""Simple Cosmos DB seeder for offline mode - compatible with emulator"""

import sys
from azure.cosmos import CosmosClient, exceptions
import urllib3

# Disable SSL warnings for emulator
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Cosmos DB Emulator well-known endpoint and key
ENDPOINT = "https://cosmosdb:8081"
KEY = "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="
DATABASE_NAME = "AzureTRE"

CONTAINERS = {
    "Resources": "/id",
    "ResourceTemplates": "/id",
    "ResourceHistory": "/resourceId",
    "Operations": "/id",
    "Requests": "/id",
    "Migrations": "/id"
}

def main():
    print("🚀 Initializing Cosmos DB...")

    try:
        # Connect to Cosmos DB Emulator
        client = CosmosClient(ENDPOINT, KEY, connection_verify=False)

        # Create database
        try:
            database = client.create_database(DATABASE_NAME)
            print(f"✅ Created database: {DATABASE_NAME}")
        except exceptions.CosmosResourceExistsError:
            database = client.get_database_client(DATABASE_NAME)
            print(f"ℹ️  Database already exists: {DATABASE_NAME}")

        # Create containers
        for container_name, partition_key in CONTAINERS.items():
            try:
                database.create_container(
                    id=container_name,
                    partition_key={"paths": [partition_key], "kind": "Hash"}
                )
                print(f"✅ Created container: {container_name} (partition: {partition_key})")
            except exceptions.CosmosResourceExistsError:
                print(f"ℹ️  Container already exists: {container_name}")

        print("\n✅ Cosmos DB initialization complete!")
        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())