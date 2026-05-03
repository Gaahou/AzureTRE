# Local Resource Processor

Docker-based resource processor for Azure TRE offline mode. Consumes deployment messages from RabbitMQ and executes Porter bundles.

## Overview

The local resource processor replaces the Azure VMSS-based resource processor for offline deployments:

- **Online Mode**: Uses Azure Service Bus + VMSS with Porter
- **Offline Mode**: Uses RabbitMQ + Docker container with Porter (this implementation)

## Architecture

```
┌─────────────────┐      ┌──────────────┐      ┌─────────────────────┐
│   TRE API       │─────▶│  RabbitMQ    │─────▶│ Resource Processor  │
│   (offline)     │      │              │      │  (local_runner)     │
└─────────────────┘      │ Queue:       │      │                     │
                         │ workspacequeue│      │ ┌─────────────────┐ │
                         │              │      │ │  Porter Runner  │ │
                         │ Queue:       │◀─────│ │  (executes      │ │
                         │deploymentstatus│     │ │   bundles)      │ │
                         └──────────────┘      │ └─────────────────┘ │
                                               └─────────────────────┘
                                                         │
                                                         ▼
                                                 Docker Socket
                                                 (Docker-in-Docker)
```

## Components

### 1. Dockerfile
- Base: Python 3.12 slim
- Installs: Porter, Docker CLI
- Mounts: Docker socket for Porter bundle execution

### 2. runner.py
- Consumes messages from `workspacequeue`
- Executes Porter actions (install/upgrade/uninstall)
- Publishes status updates to `deploymentstatus`

### 3. cleanup.sh
- Stops and removes resource processor container
- Cleans up Docker images

## Message Format

### Deployment Request (workspacequeue)
```json
{
  "id": "resource-uuid",
  "resourceId": "resource-uuid",
  "action": "install",
  "templateName": "tre-workspace-base",
  "parameters": {
    "workspace_id": "ws1",
    "address_space": "10.1.0.0/24"
  }
}
```

### Status Update (deploymentstatus)
```json
{
  "operationId": "operation-uuid",
  "resourceId": "resource-uuid",
  "status": "deployed",
  "message": "Successfully executed install",
  "timestamp": "2026-05-03T05:40:00Z",
  "outputs": {}
}
```

## Status Values

- `deploying` - Porter action started
- `deployed` - Install succeeded
- `updated` - Upgrade succeeded
- `failed` - Action failed

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RABBITMQ_HOST` | `rabbitmq` | RabbitMQ hostname |
| `RABBITMQ_PORT` | `5672` | RabbitMQ port |
| `RABBITMQ_USER` | `tre_user` | RabbitMQ username |
| `RABBITMQ_PASSWORD` | `tre_password` | RabbitMQ password |
| `RABBITMQ_VHOST` | `/` | RabbitMQ virtual host |

## Usage

### Build Image
```bash
cd resource_processor/local_runner
docker build -t tre-resource-processor:local .
```

### Run Container
```bash
docker run -d \
  --name tre-resource-processor \
  --network tre-local \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e RABBITMQ_HOST=rabbitmq \
  -e RABBITMQ_USER=tre_user \
  -e RABBITMQ_PASSWORD=tre_password \
  tre-resource-processor:local
```

### View Logs
```bash
docker logs -f tre-resource-processor
```

### Cleanup
```bash
./cleanup.sh
```

## Integration with docker-compose

The resource processor is added to `deploy/offline/docker-compose.yml`:

```yaml
tre-resource-processor:
  build:
    context: ../../resource_processor/local_runner
    dockerfile: Dockerfile
  container_name: tre-resource-processor
  depends_on:
    rabbitmq:
      condition: service_healthy
  environment:
    - RABBITMQ_HOST=rabbitmq
    - RABBITMQ_USER=tre_user
    - RABBITMQ_PASSWORD=tre_password
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock
  networks:
    - tre-local
```

## Porter Bundle Execution

The resource processor uses Porter to execute deployment bundles:

```bash
porter install <bundle-name> \
  --installation <resource-id> \
  --reference <bundle-name> \
  --param key=value \
  --allow-docker-host-access \
  --debug
```

## Testing

Send a test message to RabbitMQ:

```bash
# Install rabbitmq-management plugin (included in rabbitmq:3-management)
# Access management UI: http://localhost:15672

# Or use CLI
docker exec -it tre-rabbitmq rabbitmqadmin publish \
  exchange=amq.default \
  routing_key=workspacequeue \
  payload='{"id":"test-resource","action":"install","templateName":"test-bundle"}'
```

## Troubleshooting

### Resource processor not receiving messages
- Check RabbitMQ connection: `docker logs tre-resource-processor`
- Verify queue exists: http://localhost:15672 → Queues
- Check network connectivity: `docker network inspect tre-local`

### Porter execution fails
- Verify Docker socket is mounted: `docker inspect tre-resource-processor | grep Mounts`
- Check Porter installation: `docker exec tre-resource-processor porter version`
- Review Porter logs in container output

### Docker-in-Docker issues
- Ensure Docker socket has correct permissions
- On macOS: Docker Desktop must allow bind mounts to `/var/run/docker.sock`

## Future Enhancements (Phase 3+)

- [ ] Add Porter credential sets for authentication
- [ ] Implement output parsing from Porter execution
- [ ] Add retry logic for failed deployments
- [ ] Implement operation cancellation
- [ ] Add metrics and monitoring
- [ ] Support for session-based message processing