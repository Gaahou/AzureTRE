# Online Deployment (Azure Cloud)

This directory contains scripts and configurations for deploying Azure TRE to Azure cloud services.

## Purpose

When `deployment_mode: online` is set in `config.yaml`, Azure TRE uses:
- **Azure Cosmos DB** for state storage
- **Azure Service Bus** for message queuing
- **Azure Event Grid** for event publishing
- **Azure AD** for authentication
- **Azure App Service** for API hosting
- **Azure Container Registry** for Docker images
- All other Azure services as defined in `core/terraform/`

## Status

⚠️ **Coming Soon**: Online deployment-specific scripts will be added here in future phases.

For now, online deployment continues to use the existing deployment process:
- `make tre-deploy` (from project root)
- `make tre-start`
- `make tre-stop`

## Future Contents

This directory will eventually contain:
- `deploy.sh` - Azure-specific deployment orchestration
- `docker-compose.yml` - For building and pushing images to ACR
- `.env.sample` - Azure-specific environment variables template
- `Makefile` - Azure deployment targets

## See Also

- [../shared/](../shared/) - Mode-agnostic scripts (env.sh, healthcheck.sh)
- [../../docs/quick-start-phase0.md](../../docs/quick-start-phase0.md) - Phase 0 implementation guide