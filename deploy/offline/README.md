# Offline Deployment (Local Docker)

This directory contains scripts and configurations for running Azure TRE 100% locally using Docker and emulators.

## Purpose

When `deployment_mode: offline` is set in `config.yaml`, Azure TRE uses:
- **Cosmos DB Linux Emulator** for state storage
- **Azurite** for blob/queue/table storage
- **RabbitMQ** for message queuing (replaces Service Bus)
- **Keycloak** for authentication (replaces Azure AD)
- **HashiCorp Vault** for secrets (replaces Key Vault)
- **Docker Compose** for orchestration

## Status

⚠️ **Phase 1+**: Offline deployment infrastructure will be implemented in Phase 1 and beyond.

## Future Contents

This directory will contain (Phase 1-4):

### Phase 1 (Local API + Emulators)
- `docker-compose.yml` - Full local stack orchestration
- `.env.sample` - Local environment variables template
- `seed/` - Bootstrap scripts for local development
  - `cosmos-init.sh` - Initialize Cosmos DB Emulator
  - `templates.json` - Seed template data

### Phase 2 (Local Message Queue)
- RabbitMQ configuration
- Resource processor Docker setup

### Phase 3 (Local Authentication)
- Keycloak realm configuration
- Vault initialization scripts

### Phase 4 (Local Workspace Lifecycle)
- Docker-based workspace templates
- Traefik routing configuration
- Observability stack (Jaeger, Grafana, Loki)

## Quick Start (When Available)

```bash
# Configure for offline mode
# Edit config.yaml: deployment_mode: offline

# Start local TRE
make up

# Check health
./deploy/shared/healthcheck.sh

# Stop local TRE
make down
```

## See Also

- [../shared/](../shared/) - Mode-agnostic scripts (env.sh, healthcheck.sh)
- [../../docs/quick-start-phase0.md](../../docs/quick-start-phase0.md) - Phase 0 guide
- [../../architecture_review/epic-local-tre-deployment.md](../../architecture_review/epic-local-tre-deployment.md) - Full epic