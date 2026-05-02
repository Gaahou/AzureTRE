# TRE Offline Deployment

This directory contains Docker Compose configuration for running Azure TRE locally with emulators instead of Azure cloud services.

## Services

### Cosmos DB Emulator
- **Image:** `mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:latest`
- **Ports:** 8081 (HTTPS endpoint), 10250-10255 (data plane)
- **Connection String:** Uses default emulator key
- **Data Persistence:** Enabled via volume mount

### Azurite (Storage Emulator)
- **Image:** `mcr.microsoft.com/azure-storage/azurite:latest`
- **Ports:** 10000 (Blob), 10001 (Queue), 10002 (Table)
- **Connection String:** Uses default development storage account

### TRE API
- **Build:** From `../../api_app/Dockerfile`
- **Port:** 8000
- **Mode:** `DEPLOYMENT_MODE=offline`
- **Dependencies:** Waits for Cosmos DB and Azurite to be healthy

## Quick Start

```bash
# From project root
cd deploy/offline

# Start all services
docker-compose up -d

# Check service health
docker-compose ps

# View logs
docker-compose logs -f tre-api

# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

## Healthchecks

All services have healthchecks configured:
- **CosmosDB:** Polls `https://localhost:8081/_explorer/index.html`
- **Azurite:** Checks port 10000 availability
- **TRE API:** Polls `/api/health` endpoint

## Environment Variables

See `.env.sample` for full configuration options.

Key variables:
- `DEPLOYMENT_MODE=offline` - Enables local emulator mode
- `STATE_STORE_ENDPOINT=https://cosmosdb:8081` - Cosmos DB emulator endpoint
- `AZURE_STORAGE_CONNECTION_STRING=...` - Azurite connection string

## Volumes

Persistent data is stored in named volumes:
- `tre-cosmosdb-data` - Cosmos DB data
- `tre-azurite-data` - Azurite blob/queue/table data

## Network

All services are on the `tre-local` bridge network for inter-service communication.

## Troubleshooting

### Cosmos DB Emulator not starting
- Ensure Docker has at least 4GB RAM allocated
- Check platform is set to `linux/amd64` (required for emulator)
- Wait for full startup (can take 60+ seconds)

### API cannot connect to Cosmos DB
- Check the emulator healthcheck: `docker-compose ps`
- Verify SSL certificate: Emulator uses self-signed cert
- Check logs: `docker-compose logs cosmosdb`

### Azurite connection errors
- Ensure connection string uses `http://` not `https://`
- Check ports 10000-10002 are not in use on host

## Next Steps (Future Phases)

- **Phase 2:** Add RabbitMQ for message queue
- **Phase 3:** Add Keycloak for authentication
- **Phase 4:** Add resource processor for workspace provisioning
