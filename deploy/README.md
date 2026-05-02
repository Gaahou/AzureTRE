# Deploy Directory

This directory contains deployment orchestration for Azure TRE, supporting both **online** (Azure cloud) and **offline** (local Docker) deployment modes.

## Structure

```
deploy/
├── online/              # Azure cloud deployment scripts and configurations
├── offline/             # Local Docker deployment (docker-compose, etc.)
└── shared/              # Mode-agnostic scripts used by both modes
    ├── env.sh          # Reads config.yaml and exports environment variables
    └── healthcheck.sh  # Health check for TRE API and infrastructure
```

## Usage

### Configure Environment

```bash
# Source environment variables based on deployment_mode in config.yaml
source deploy/shared/env.sh

# Verbose output
VERBOSE=1 source deploy/shared/env.sh
```

### Health Check

```bash
# Check TRE API and infrastructure health
./deploy/shared/healthcheck.sh
```

## Deployment Modes

### Online Mode (Azure Cloud)

- Uses Azure services: Cosmos DB, Service Bus, Azure AD, App Service, etc.
- Requires Azure subscription and credentials
- Scripts in `deploy/online/` directory

### Offline Mode (Local Docker)

- Uses local emulators: Cosmos DB Emulator, Azurite, RabbitMQ, Keycloak
- No Azure subscription required
- Scripts in `deploy/offline/` directory

## Configuration

The deployment mode is controlled by `deployment_mode` in `config.yaml`:

```yaml
developer_settings:
  deployment_mode: online  # or "offline"
```

See [docs/quick-start-phase0.md](../docs/quick-start-phase0.md) for implementation details.