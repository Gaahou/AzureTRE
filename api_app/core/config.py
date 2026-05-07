from typing import List
import warnings
from starlette.config import Config
from _version import __version__

warnings.filterwarnings("ignore", message="Config file '.env' not found.")

config = Config('.env')

# API settings
API_PREFIX = "/api"
PROJECT_NAME: str = config("PROJECT_NAME", default="Azure TRE API")
LOGGING_LEVEL: str = config("LOGGING_LEVEL", default="INFO")

# Deployment mode configuration
_DEPLOYMENT_MODE: str = config("DEPLOYMENT_MODE", default="online")
VALID_DEPLOYMENT_MODES = ["online", "offline"]

# Validate deployment mode
if _DEPLOYMENT_MODE not in VALID_DEPLOYMENT_MODES:
    raise ValueError(
        f"Invalid DEPLOYMENT_MODE '{_DEPLOYMENT_MODE}'. "
        f"Must be one of: {', '.join(VALID_DEPLOYMENT_MODES)}"
    )

DEPLOYMENT_MODE: str = _DEPLOYMENT_MODE
ENABLE_LOCAL_DEBUGGING: bool = config("ENABLE_LOCAL_DEBUGGING", cast=bool, default=False)
ENABLE_SWAGGER: bool = config("ENABLE_SWAGGER", cast=bool, default=False)
VERSION = __version__
API_DESCRIPTION = "Welcome to the Azure TRE API - for more information about templates and workspaces see the [Azure TRE documentation](https://microsoft.github.io/AzureTRE)"

# Resource Info
RESOURCE_LOCATION: str = config("RESOURCE_LOCATION", default="")
TRE_ID: str = config("TRE_ID", default="")
CORE_ADDRESS_SPACE: str = config("CORE_ADDRESS_SPACE", default="")
TRE_ADDRESS_SPACE: str = config("TRE_ADDRESS_SPACE", default="")

# State store configuration
STATE_STORE_ENDPOINT: str = config("STATE_STORE_ENDPOINT", default="")      # Cosmos DB endpoint
STATE_STORE_SSL_VERIFY: bool = config("STATE_STORE_SSL_VERIFY", cast=bool, default=True)
STATE_STORE_KEY: str = config("STATE_STORE_KEY", default="")                # Cosmos DB access key
COSMOSDB_ACCOUNT_NAME: str = config("COSMOSDB_ACCOUNT_NAME", default="")                # Cosmos DB account name
STATE_STORE_DATABASE = "AzureTRE"
STATE_STORE_RESOURCES_CONTAINER = "Resources"
STATE_STORE_RESOURCE_TEMPLATES_CONTAINER = "ResourceTemplates"
STATE_STORE_RESOURCES_HISTORY_CONTAINER = "ResourceHistory"
STATE_STORE_OPERATIONS_CONTAINER = "Operations"
STATE_STORE_AIRLOCK_REQUESTS_CONTAINER = "Requests"
SUBSCRIPTION_ID: str = config("SUBSCRIPTION_ID", default="")
RESOURCE_GROUP_NAME: str = config("RESOURCE_GROUP_NAME", default="")

# Service bus configuration (online mode - Azure Service Bus)
SERVICE_BUS_FULLY_QUALIFIED_NAMESPACE: str = config("SERVICE_BUS_FULLY_QUALIFIED_NAMESPACE", default="")
SERVICE_BUS_RESOURCE_REQUEST_QUEUE: str = config("SERVICE_BUS_RESOURCE_REQUEST_QUEUE", default="")
SERVICE_BUS_DEPLOYMENT_STATUS_UPDATE_QUEUE: str = config("SERVICE_BUS_DEPLOYMENT_STATUS_UPDATE_QUEUE", default="")
SERVICE_BUS_STEP_RESULT_QUEUE: str = config("SERVICE_BUS_STEP_RESULT_QUEUE", default="")

# RabbitMQ configuration (offline mode)
RABBITMQ_HOST: str = config("RABBITMQ_HOST", default="localhost")
RABBITMQ_PORT: int = config("RABBITMQ_PORT", cast=int, default=5672)
RABBITMQ_USER: str = config("RABBITMQ_USER", default="guest")
RABBITMQ_PASSWORD: str = config("RABBITMQ_PASSWORD", default="guest")
RABBITMQ_VHOST: str = config("RABBITMQ_VHOST", default="/")

# Event grid configuration
EVENT_GRID_STATUS_CHANGED_TOPIC_ENDPOINT: str = config("EVENT_GRID_STATUS_CHANGED_TOPIC_ENDPOINT", default="")
EVENT_GRID_AIRLOCK_NOTIFICATION_TOPIC_ENDPOINT: str = config("EVENT_GRID_AIRLOCK_NOTIFICATION_TOPIC_ENDPOINT", default="")

# Managed identity configuration
MANAGED_IDENTITY_CLIENT_ID: str = config("MANAGED_IDENTITY_CLIENT_ID", default="")

# Cloud configuration
AAD_AUTHORITY_URL: str = config("AAD_AUTHORITY_URL", default="https://login.microsoftonline.com")
RESOURCE_MANAGER_ENDPOINT: str = config("RESOURCE_MANAGER_ENDPOINT", default="https://management.azure.com")
CREDENTIAL_SCOPES: List[str] = [f"{RESOURCE_MANAGER_ENDPOINT}/.default"]
MICROSOFT_GRAPH_URL: str = config("MICROSOFT_GRAPH_URL", default="https://graph.microsoft.com")
STORAGE_ENDPOINT_SUFFIX: str = config("STORAGE_ENDPOINT_SUFFIX", default="core.windows.net")

# Monitoring
APPLICATIONINSIGHTS_CONNECTION_STRING: str = config("APPLICATIONINSIGHTS_CONNECTION_STRING", default=None)

# Authentication
API_CLIENT_ID: str = config("API_CLIENT_ID", default="")
API_CLIENT_SECRET: str = config("API_CLIENT_SECRET", default="")
SWAGGER_UI_CLIENT_ID: str = config("SWAGGER_UI_CLIENT_ID", default="")
AAD_TENANT_ID: str = config("AAD_TENANT_ID", default="")

API_AUDIENCE: str = config("API_AUDIENCE", default=API_CLIENT_ID)

# Authentication Type (for online mode - which Azure AD to use)
_AUTH_TYPE: str = config("AUTH_TYPE", default="aad")
VALID_AUTH_TYPES = ["aad", "b2c", "keycloak"]

# Validate auth type
if _AUTH_TYPE not in VALID_AUTH_TYPES:
    raise ValueError(
        f"Invalid AUTH_TYPE '{_AUTH_TYPE}'. "
        f"Must be one of: {', '.join(VALID_AUTH_TYPES)}"
    )

AUTH_TYPE: str = _AUTH_TYPE

# Azure AD B2C Configuration (when AUTH_TYPE=b2c)
B2C_TENANT_NAME: str = config("B2C_TENANT_NAME", default="")
B2C_POLICY_SUSI: str = config("B2C_POLICY_SUSI", default="B2C_1_susi")
B2C_CLIENT_ID: str = config("B2C_CLIENT_ID", default="")
B2C_CLIENT_SECRET: str = config("B2C_CLIENT_SECRET", default="")
B2C_ROLE_CLAIM_NAME: str = config("B2C_ROLE_CLAIM_NAME", default="extension_WorkspaceRole")

AIRLOCK_SAS_TOKEN_EXPIRY_PERIOD_IN_HOURS: int = config("AIRLOCK_SAS_TOKEN_EXPIRY_PERIOD_IN_HOURS", default=1)
ENABLE_AIRLOCK_EMAIL_CHECK: bool = config("ENABLE_AIRLOCK_EMAIL_CHECK", cast=bool, default=False)

API_ROOT_SCOPE: str = f"api://{API_CLIENT_ID}/user_impersonation"

# User Management
USER_MANAGEMENT_ENABLED: bool = config("USER_MANAGEMENT_ENABLED", cast=bool, default=False)
