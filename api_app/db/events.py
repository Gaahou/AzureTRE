import asyncio
from azure.mgmt.cosmosdb import CosmosDBManagementClient
from azure.cosmos.aio import CosmosClient

from core.config import (
    SUBSCRIPTION_ID, RESOURCE_GROUP_NAME, RESOURCE_LOCATION, COSMOSDB_ACCOUNT_NAME,
    STATE_STORE_DATABASE, STATE_STORE_RESOURCES_CONTAINER, STATE_STORE_RESOURCE_TEMPLATES_CONTAINER,
    STATE_STORE_RESOURCES_HISTORY_CONTAINER, STATE_STORE_OPERATIONS_CONTAINER,
    STATE_STORE_AIRLOCK_REQUESTS_CONTAINER, DEPLOYMENT_MODE, STATE_STORE_ENDPOINT, STATE_STORE_KEY
)
from core.credentials import get_credential
from services.logging import logger


async def bootstrap_database() -> bool:
    """
    Bootstrap database and containers.

    In online mode: Uses Azure Cosmos Management SDK to create containers.
    In offline mode: Verifies containers exist (pre-created by seed scripts).
    """
    try:
        if DEPLOYMENT_MODE == "offline":
            logger.info("Offline mode: Verifying containers exist (pre-created by seed scripts)")
            return await verify_containers_exist_offline()
        else:
            logger.info("Online mode: Creating containers via Azure Cosmos Management SDK")
            credential = get_credential()
            db_mgmt_client = CosmosDBManagementClient(credential=credential, subscription_id=SUBSCRIPTION_ID)

            await asyncio.gather(
                create_container_if_not_exists(db_mgmt_client, STATE_STORE_RESOURCES_CONTAINER, "/id"),
                create_container_if_not_exists(db_mgmt_client, STATE_STORE_RESOURCE_TEMPLATES_CONTAINER, "/id"),
                create_container_if_not_exists(db_mgmt_client, STATE_STORE_RESOURCES_HISTORY_CONTAINER, "/resourceId"),
                create_container_if_not_exists(db_mgmt_client, STATE_STORE_OPERATIONS_CONTAINER, "/id"),
                create_container_if_not_exists(db_mgmt_client, STATE_STORE_AIRLOCK_REQUESTS_CONTAINER, "/id")
            )

            return True

    except Exception as e:
        logger.exception("Could not bootstrap database")
        logger.debug(e)
        return False


async def verify_containers_exist_offline() -> bool:
    """
    Verify that required containers exist in offline mode.
    Containers should be pre-created by seed scripts (cosmos-init.sh).
    """
    required_containers = [
        STATE_STORE_RESOURCES_CONTAINER,
        STATE_STORE_RESOURCE_TEMPLATES_CONTAINER,
        STATE_STORE_RESOURCES_HISTORY_CONTAINER,
        STATE_STORE_OPERATIONS_CONTAINER,
        STATE_STORE_AIRLOCK_REQUESTS_CONTAINER
    ]

    try:
        # Use data plane SDK to verify containers exist
        async with CosmosClient(STATE_STORE_ENDPOINT, STATE_STORE_KEY) as client:
            database = client.get_database_client(STATE_STORE_DATABASE)

            # Check if database exists
            try:
                await database.read()
                logger.info(f"Database '{STATE_STORE_DATABASE}' found")
            except Exception as e:
                logger.error(f"Database '{STATE_STORE_DATABASE}' not found. Run seed scripts first: deploy/offline/seed/cosmos-init.sh")
                return False

            # Verify each container exists
            for container_name in required_containers:
                try:
                    container = database.get_container_client(container_name)
                    await container.read()
                    logger.info(f"Container '{container_name}' verified")
                except Exception:
                    logger.error(f"Container '{container_name}' not found. Run seed scripts first: deploy/offline/seed/cosmos-init.sh")
                    return False

            logger.info("All required containers verified successfully")
            return True

    except Exception as e:
        logger.exception("Failed to verify containers in offline mode")
        logger.error("Make sure to run seed scripts: deploy/offline/seed/cosmos-init.sh")
        return False


async def create_container_if_not_exists(db_mgmt_client, container, partition_key):

    db_mgmt_client.sql_resources.begin_create_update_sql_container(
        resource_group_name=RESOURCE_GROUP_NAME,
        account_name=COSMOSDB_ACCOUNT_NAME,
        database_name=STATE_STORE_DATABASE,
        container_name=container,
        create_update_sql_container_parameters={
            "location": RESOURCE_LOCATION,
            "resource": {
                "id": container,
                "partition_key": {
                    "paths": [
                        partition_key
                    ],
                    "kind": "Hash"
                }
            }
        }
    )
