# Phase 4 Test Plan: Workspace Lifecycle & Observability

**Testing User Story:** TBD  
**Feature:** F4 - Workspace Lifecycle & Observability (Phase 4)  
**Stories:** 133-138  
**Branch:** feature/phase4-workspace-lifecycle  
**Last Commit:** 916c604b9b42866bbb05fdf49f89a6f1340ce2d9  
**Test Date:** 2026-05-03

---

## Test Environment

### Docker-Based Testing (Rule #7)
All tests executed in Docker containers to ensure reproducible results.

**Test Script:** `scripts/test_phase4_docker.sh`

**Test Environment:** Full offline stack with all Phase 4 services

---

## Test Scope

Phase 4 introduces Docker-based workspace lifecycle management and observability infrastructure:

### Stories Under Test

| ID | Story | Description |
|----|-------|-------------|
| 133 | Create Docker-based workspace template | Base workspace template for offline Docker deployments |
| 134 | Create Docker-based Linux VM resource | Linux VM workspace service running in Docker |
| 135 | Extend local resource processor for Docker deployments | Resource processor can deploy Docker-based workspaces |
| 136 | Add container registry to offline stack | Private Docker registry for workspace images |
| 137 | Add Traefik for workspace routing | Reverse proxy for routing to workspace services |
| 138 | Add observability stack | Jaeger, Loki, Grafana for tracing, logging, and monitoring |

---

## Test Categories

### 1. Infrastructure Tests

#### 1.1 Container Registry Startup
**Story:** 136  
**Objective:** Verify private Docker registry starts and is accessible

**Test Steps:**
```bash
cd deploy/offline
docker-compose up -d registry
docker-compose ps registry
curl -s http://localhost:5000/v2/_catalog
```

**Expected Results:**
- [ ] Registry container starts successfully
- [ ] Container status is "healthy"
- [ ] Registry API accessible at http://localhost:5000
- [ ] Authentication working (if configured)
- [ ] Can list repositories via API

**Acceptance Criteria:**
- Container starts within 30 seconds
- Registry API responsive
- No error logs in container

---

#### 1.2 Traefik Startup and Configuration
**Story:** 137  
**Objective:** Verify Traefik reverse proxy starts and routes correctly

**Test Steps:**
```bash
cd deploy/offline
docker-compose up -d traefik
docker-compose ps traefik
curl -s http://localhost:8080/api/overview
docker-compose logs traefik | grep -i "Configuration loaded"
```

**Expected Results:**
- [ ] Traefik container starts successfully
- [ ] Dashboard accessible at http://localhost:8080
- [ ] Configuration loaded without errors
- [ ] Network connections established
- [ ] HTTP and HTTPS entrypoints configured

**Acceptance Criteria:**
- Container starts within 15 seconds
- Dashboard shows active services
- No configuration errors in logs

---

#### 1.3 Observability Stack Startup
**Story:** 138  
**Objective:** Verify Jaeger, Loki, and Grafana start and integrate correctly

**Test Steps:**
```bash
cd deploy/offline
docker-compose up -d jaeger loki grafana
docker-compose ps jaeger loki grafana

# Test Jaeger
curl -s http://localhost:16686/api/services

# Test Loki
curl -s http://localhost:3100/ready

# Test Grafana
curl -s http://localhost:3001/api/health
```

**Expected Results:**
- [ ] Jaeger UI accessible at http://localhost:16686
- [ ] Loki API accessible at http://localhost:3100
- [ ] Grafana UI accessible at http://localhost:3001
- [ ] All services report healthy status
- [ ] Services can communicate with each other

**Acceptance Criteria:**
- All containers start within 60 seconds
- All health endpoints return 200 OK
- No startup errors in logs

---

### 2. Workspace Template Tests

#### 2.1 Base Workspace Template Validation
**Story:** 133  
**Objective:** Verify base workspace template is valid and deployable

**Test Steps:**
```bash
# Validate template schema
cat templates/workspaces/base/template_schema.json | jq .

# Check required fields
jq '.name, .version, .description, .resourceType' templates/workspaces/base/template_schema.json

# Validate parameters
cat templates/workspaces/base/parameters.json | jq .
```

**Expected Results:**
- [ ] Template schema is valid JSON
- [ ] All required fields present (name, version, description, resourceType)
- [ ] resourceType is "workspace"
- [ ] Parameters file exists and is valid
- [ ] Template follows TRE schema conventions

**Acceptance Criteria:**
- Template passes JSON schema validation
- All mandatory fields populated
- Version follows semantic versioning

---

#### 2.2 Linux VM Workspace Service Template
**Story:** 134  
**Objective:** Verify Linux VM workspace service template is valid

**Test Steps:**
```bash
# Find Linux VM template
find templates/workspace_services -name "*linux*" -o -name "*docker*" | head -5

# Validate template structure
# Check for template_schema.json and parameters.json
ls -la templates/workspace_services/linux-vm/ 2>/dev/null || \
ls -la templates/workspace_services/docker-vm/ 2>/dev/null
```

**Expected Results:**
- [ ] Linux VM template exists in workspace_services
- [ ] Template schema is valid JSON
- [ ] resourceType is "workspace-service"
- [ ] Parent workspace reference configured
- [ ] Docker image specified or build context provided

**Acceptance Criteria:**
- Template validates against schema
- Can be linked to parent workspace
- Docker configuration is complete

---

### 3. Resource Processor Tests

#### 3.1 Docker Deployment Handler
**Story:** 135  
**Objective:** Verify resource processor can deploy Docker-based workspaces

**Test Steps:**
```bash
# Check resource processor has Docker deployment logic
cat resource_processor/local_runner/runner.py | grep -i docker

# Verify Docker client accessible in processor
docker-compose exec resource-processor python -c "
import docker
client = docker.from_env()
print(f'Docker version: {client.version()}')
"
```

**Expected Results:**
- [ ] Resource processor imports Docker SDK
- [ ] Can connect to Docker daemon
- [ ] Can list running containers
- [ ] Can create new containers
- [ ] Can manage container lifecycle (start, stop, remove)

**Acceptance Criteria:**
- Docker SDK integration working
- Can execute Docker operations
- Error handling for Docker failures

---

#### 3.2 Workspace Deployment Flow
**Story:** 135  
**Objective:** Verify complete workspace deployment workflow

**Test Steps:**
```bash
# Send workspace deployment message
python3 << EOF
import asyncio
from aio_pika import connect_robust, Message
import json

async def send_workspace_deploy():
    connection = await connect_robust("amqp://guest:guest@localhost:5672/")
    channel = await connection.channel()
    
    message = {
        "action": "deploy",
        "resourceType": "workspace",
        "resourceId": "ws-test-001",
        "templateName": "base-workspace",
        "parameters": {}
    }
    
    await channel.default_exchange.publish(
        Message(json.dumps(message).encode()),
        routing_key="tre.resource-request"
    )
    
    await connection.close()

asyncio.run(send_workspace_deploy())
EOF

# Check processor logs
docker-compose logs -f resource-processor | head -50
```

**Expected Results:**
- [ ] Message received by resource processor
- [ ] Template loaded successfully
- [ ] Docker container created for workspace
- [ ] Container starts successfully
- [ ] Status updated to "deployed"
- [ ] Deployment event published

**Acceptance Criteria:**
- Workspace deploys without errors
- Container running and healthy
- Database updated with workspace state

---

### 4. Container Registry Tests

#### 4.1 Push Image to Registry
**Story:** 136  
**Objective:** Verify can push Docker images to private registry

**Test Steps:**
```bash
# Build a test image
docker build -t test-workspace:v1 -<<EOF
FROM alpine:latest
CMD ["/bin/sh"]
EOF

# Tag for local registry
docker tag test-workspace:v1 localhost:5000/test-workspace:v1

# Push to registry
docker push localhost:5000/test-workspace:v1

# Verify in registry
curl -s http://localhost:5000/v2/_catalog
curl -s http://localhost:5000/v2/test-workspace/tags/list
```

**Expected Results:**
- [ ] Image builds successfully
- [ ] Can tag image for local registry
- [ ] Push completes without errors
- [ ] Image appears in registry catalog
- [ ] Tags are listed correctly

**Acceptance Criteria:**
- Push completes in < 30 seconds
- Image retrievable from registry
- No authentication errors

---

#### 4.2 Pull Image from Registry
**Story:** 136  
**Objective:** Verify can pull images from private registry

**Test Steps:**
```bash
# Remove local image
docker rmi localhost:5000/test-workspace:v1

# Pull from registry
docker pull localhost:5000/test-workspace:v1

# Verify pulled successfully
docker images | grep test-workspace

# Run container from pulled image
docker run --rm localhost:5000/test-workspace:v1 echo "Registry working"
```

**Expected Results:**
- [ ] Image pulls successfully
- [ ] Pull completes in reasonable time
- [ ] Can run container from pulled image
- [ ] No layer verification errors

**Acceptance Criteria:**
- Pull completes without errors
- Image functional after pull

---

### 5. Traefik Routing Tests

#### 5.1 Dynamic Service Discovery
**Story:** 137  
**Objective:** Verify Traefik discovers and routes to workspace services

**Test Steps:**
```bash
# Start workspace with labels for Traefik
docker run -d \
  --name test-workspace-svc \
  --network tre-local \
  --label "traefik.enable=true" \
  --label "traefik.http.routers.test-ws.rule=Host(\`test-ws.tre.local\`)" \
  --label "traefik.http.services.test-ws.loadbalancer.server.port=80" \
  nginx:alpine

# Wait for Traefik to discover service
sleep 5

# Test routing
curl -H "Host: test-ws.tre.local" http://localhost:80

# Check Traefik dashboard for service
curl -s http://localhost:8080/api/http/routers | jq '.[] | select(.name | contains("test-ws"))'
```

**Expected Results:**
- [ ] Traefik discovers workspace service
- [ ] Router created automatically
- [ ] HTTP request routed correctly
- [ ] Response received from workspace service
- [ ] Service appears in Traefik dashboard

**Acceptance Criteria:**
- Service discovered within 10 seconds
- Routing works correctly
- No 404 or 502 errors

---

#### 5.2 Workspace Isolation via Routing
**Story:** 137  
**Objective:** Verify each workspace gets unique route

**Test Steps:**
```bash
# Create two workspace services
for i in 1 2; do
  docker run -d \
    --name test-workspace-$i \
    --network tre-local \
    --label "traefik.enable=true" \
    --label "traefik.http.routers.ws$i.rule=Host(\`ws$i.tre.local\`)" \
    --label "traefik.http.services.ws$i.loadbalancer.server.port=80" \
    nginx:alpine
done

# Test routing to each workspace
curl -H "Host: ws1.tre.local" http://localhost:80 | grep -i nginx
curl -H "Host: ws2.tre.local" http://localhost:80 | grep -i nginx

# Verify isolation (wrong host should fail)
curl -H "Host: ws3.tre.local" http://localhost:80
```

**Expected Results:**
- [ ] Both workspaces accessible via different hosts
- [ ] Each workspace receives its own requests
- [ ] Invalid host returns 404
- [ ] No cross-workspace routing

**Acceptance Criteria:**
- Workspaces are isolated
- Routing is workspace-specific
- No accidental cross-workspace access

---

### 6. Observability Tests

#### 6.1 Jaeger Tracing Integration
**Story:** 138  
**Objective:** Verify distributed tracing captures workspace operations

**Test Steps:**
```bash
# Deploy workspace with tracing enabled
# Check if API sends traces to Jaeger
docker-compose logs api | grep -i jaeger

# Query Jaeger for traces
curl -s "http://localhost:16686/api/traces?service=tre-api&limit=10" | jq '.data[0].traceID'

# Verify trace spans
curl -s "http://localhost:16686/api/services" | jq '.data[]'
```

**Expected Results:**
- [ ] API configured to send traces to Jaeger
- [ ] Traces appear in Jaeger UI
- [ ] Spans show workspace deployment steps
- [ ] Service dependencies visible
- [ ] Timing information captured

**Acceptance Criteria:**
- Traces captured for workspace operations
- All major operations traced
- UI displays traces correctly

---

#### 6.2 Loki Log Aggregation
**Story:** 138  
**Objective:** Verify logs from all services aggregated in Loki

**Test Steps:**
```bash
# Check Loki receiving logs
curl -s 'http://localhost:3100/loki/api/v1/label' | jq .

# Query logs for specific service
curl -s 'http://localhost:3100/loki/api/v1/query?query={job="api"}' | jq '.data.result[0]'

# Query logs for resource processor
curl -s 'http://localhost:3100/loki/api/v1/query?query={job="resource-processor"}' | jq '.data.result[0]'
```

**Expected Results:**
- [ ] Loki receives logs from API
- [ ] Loki receives logs from resource processor
- [ ] Loki receives logs from workspaces
- [ ] Logs queryable via LogQL
- [ ] Log labels configured correctly

**Acceptance Criteria:**
- All services send logs to Loki
- Logs are queryable
- Retention policy working

---

#### 6.3 Grafana Dashboards
**Story:** 138  
**Objective:** Verify Grafana displays metrics and logs

**Test Steps:**
```bash
# Login to Grafana (default admin/admin)
curl -s -X POST http://localhost:3001/api/auth/keys \
  -H "Content-Type: application/json" \
  -u admin:admin \
  -d '{"name":"test-key","role":"Admin"}'

# Check data sources configured
curl -s http://localhost:3001/api/datasources -u admin:admin | jq '.[] | {name: .name, type: .type}'

# Verify Loki data source
curl -s http://localhost:3001/api/datasources -u admin:admin | jq '.[] | select(.type == "loki")'

# Verify Jaeger data source
curl -s http://localhost:3001/api/datasources -u admin:admin | jq '.[] | select(.type == "jaeger")'
```

**Expected Results:**
- [ ] Grafana UI accessible
- [ ] Loki configured as data source
- [ ] Jaeger configured as data source
- [ ] Can query logs from Grafana
- [ ] Can view traces from Grafana
- [ ] Dashboards pre-configured (if applicable)

**Acceptance Criteria:**
- All data sources connected
- Queries return data
- UI functional

---

### 7. Integration Tests

#### 7.1 End-to-End Workspace Deployment
**Stories:** 133-138  
**Objective:** Verify complete workspace lifecycle from API request to running workspace

**Test Steps:**
```bash
# 1. Start all services
cd deploy/offline
docker-compose up -d

# 2. Wait for services to be healthy
sleep 30

# 3. Deploy workspace via API
curl -X POST http://localhost:8000/api/workspaces \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "template_name": "base-workspace",
    "workspace_owner": "test-user@example.com",
    "properties": {}
  }'

# 4. Check workspace status
WORKSPACE_ID=$(curl -s http://localhost:8000/api/workspaces | jq -r '.[0].id')
curl -s http://localhost:8000/api/workspaces/$WORKSPACE_ID | jq '.status'

# 5. Verify workspace container running
docker ps | grep workspace

# 6. Check Traefik routing
curl -H "Host: $WORKSPACE_ID.tre.local" http://localhost:80

# 7. Verify logs in Loki
curl -s "http://localhost:3100/loki/api/v1/query?query={workspace_id=\"$WORKSPACE_ID\"}" | jq .

# 8. Verify traces in Jaeger
curl -s "http://localhost:16686/api/traces?service=workspace-$WORKSPACE_ID" | jq .
```

**Expected Results:**
- [ ] API accepts workspace deployment request
- [ ] Request queued to RabbitMQ
- [ ] Resource processor receives message
- [ ] Workspace Docker container created
- [ ] Container registered with Traefik
- [ ] Workspace accessible via HTTP
- [ ] Workspace logs appear in Loki
- [ ] Deployment traced in Jaeger
- [ ] Database updated with workspace state
- [ ] Status changed event published

**Acceptance Criteria:**
- Complete flow completes within 60 seconds
- No errors in any component
- Workspace fully functional
- All observability data captured

---

#### 7.2 Workspace Service Deployment
**Story:** 134, 135  
**Objective:** Verify deploying a workspace service (Linux VM) into a workspace

**Test Steps:**
```bash
# 1. Deploy workspace first (from 7.1)
WORKSPACE_ID="ws-test-001"

# 2. Deploy Linux VM service into workspace
curl -X POST http://localhost:8000/api/workspaces/$WORKSPACE_ID/workspace-services \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "template_name": "linux-vm",
    "properties": {
      "display_name": "Test VM",
      "description": "Test Linux VM"
    }
  }'

# 3. Check service status
SERVICE_ID=$(curl -s http://localhost:8000/api/workspaces/$WORKSPACE_ID/workspace-services | jq -r '.[0].id')
curl -s http://localhost:8000/api/workspaces/$WORKSPACE_ID/workspace-services/$SERVICE_ID | jq '.status'

# 4. Verify service container running
docker ps | grep $SERVICE_ID

# 5. Verify service route in Traefik
curl -s http://localhost:8080/api/http/routers | jq ".[] | select(.name | contains(\"$SERVICE_ID\"))"
```

**Expected Results:**
- [ ] API accepts service deployment request
- [ ] Service queued to RabbitMQ
- [ ] Resource processor deploys service container
- [ ] Service container running
- [ ] Service accessible via Traefik
- [ ] Service logs in Loki
- [ ] Parent workspace reference maintained

**Acceptance Criteria:**
- Service deploys successfully
- Service accessible
- Workspace-service relationship maintained

---

#### 7.3 Workspace Deletion Flow
**Story:** 135  
**Objective:** Verify workspace and all services deleted cleanly

**Test Steps:**
```bash
# 1. Delete workspace (should cascade to services)
curl -X DELETE http://localhost:8000/api/workspaces/$WORKSPACE_ID \
  -H "Authorization: Bearer $TOKEN"

# 2. Verify workspace container removed
docker ps -a | grep $WORKSPACE_ID

# 3. Verify service containers removed
docker ps -a | grep $SERVICE_ID

# 4. Verify Traefik routes removed
curl -s http://localhost:8080/api/http/routers | jq ".[] | select(.name | contains(\"$WORKSPACE_ID\"))"

# 5. Verify database cleanup
curl -s http://localhost:8000/api/workspaces/$WORKSPACE_ID
# Should return 404

# 6. Verify deletion event published
docker-compose logs rabbitmq | grep -i "delete.*$WORKSPACE_ID"
```

**Expected Results:**
- [ ] API accepts deletion request
- [ ] Deletion message sent to resource processor
- [ ] All workspace service containers stopped and removed
- [ ] Workspace container stopped and removed
- [ ] Traefik routes removed
- [ ] Database records removed
- [ ] Deletion event published
- [ ] No orphaned containers

**Acceptance Criteria:**
- Complete cleanup within 30 seconds
- No orphaned resources
- Database consistent

---

### 8. Registry Integration Tests

#### 8.1 Workspace Image from Registry
**Story:** 136  
**Objective:** Verify workspaces can be deployed from images in private registry

**Test Steps:**
```bash
# 1. Build custom workspace image
docker build -t workspace-custom:v1 -<<EOF
FROM nginx:alpine
COPY index.html /usr/share/nginx/html/
EOF

# 2. Push to local registry
docker tag workspace-custom:v1 localhost:5000/workspace-custom:v1
docker push localhost:5000/workspace-custom:v1

# 3. Deploy workspace using registry image
curl -X POST http://localhost:8000/api/workspaces \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "template_name": "custom-workspace",
    "properties": {
      "image": "localhost:5000/workspace-custom:v1"
    }
  }'

# 4. Verify workspace pulled from registry
docker-compose logs resource-processor | grep -i "pulling.*workspace-custom"

# 5. Verify workspace running
docker ps | grep workspace-custom
```

**Expected Results:**
- [ ] Custom image pushes to registry
- [ ] Resource processor pulls from registry
- [ ] Workspace container starts from registry image
- [ ] No image pull errors

**Acceptance Criteria:**
- Registry integration working
- Custom images deployable
- No authentication issues

---

### 9. Regression Tests

#### 9.1 Phase 3 Features Still Working
**Stories:** 133-138  
**Objective:** Verify Phase 3 (Auth & Secrets) not broken by Phase 4

**Test Steps:**
```bash
# Test Keycloak still running
curl -s http://localhost:8080/realms/tre/.well-known/openid-configuration | jq .

# Test Vault still running
docker-compose exec vault vault status

# Test API authentication still working
# Get token
TOKEN=$(curl -s -X POST http://localhost:8080/realms/tre/protocol/openid-connect/token \
  -d "client_id=tre-api" \
  -d "client_secret=secret" \
  -d "grant_type=client_credentials" | jq -r '.access_token')

# Use token to access API
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/workspaces
```

**Expected Results:**
- [ ] Keycloak accessible
- [ ] Vault accessible
- [ ] Authentication flow works
- [ ] Secrets retrieval works
- [ ] No regression in Phase 3 features

**Acceptance Criteria:**
- All Phase 3 features functional
- No breaking changes

---

#### 9.2 Phase 2 Message Queue Still Working
**Stories:** 133-138  
**Objective:** Verify RabbitMQ message flow not broken

**Test Steps:**
```bash
# Check RabbitMQ still running
docker-compose ps rabbitmq

# Check management UI
curl -s http://localhost:15672/ | grep -i rabbitmq

# Send test message
python3 << EOF
import asyncio
from aio_pika import connect_robust, Message

async def test_rabbit():
    connection = await connect_robust("amqp://guest:guest@localhost:5672/")
    channel = await connection.channel()
    await channel.default_exchange.publish(
        Message(b'{"test": "phase4-regression"}'),
        routing_key="tre.resource-request"
    )
    await connection.close()

asyncio.run(test_rabbit())
EOF

# Check resource processor received it
docker-compose logs resource-processor | tail -5
```

**Expected Results:**
- [ ] RabbitMQ running
- [ ] Can publish messages
- [ ] Resource processor receives messages
- [ ] No message loss

**Acceptance Criteria:**
- RabbitMQ fully functional
- Message flow intact

---

### 10. Unit Tests

#### 10.1 Run Full Test Suite
**All Stories**  
**Objective:** Verify all unit tests pass

**Test Steps:**
```bash
# Run in Docker container (Rule #7)
cd api_app
docker build --target test -t azuretre-api-test:phase4 .
docker run --rm azuretre-api-test:phase4 pytest tests_ma/ -v --tb=short
```

**Expected Results:**
- [ ] All tests pass (100%)
- [ ] No new test failures
- [ ] No skipped tests
- [ ] Test coverage maintained or improved

**Acceptance Criteria:**
- Zero test failures
- Test suite completes within 3 minutes

---

### 11. Performance Tests

#### 11.1 Concurrent Workspace Deployments
**Story:** 135, 137  
**Objective:** Verify system handles multiple concurrent workspace deployments

**Test Steps:**
```bash
# Deploy 5 workspaces concurrently
for i in {1..5}; do
  curl -X POST http://localhost:8000/api/workspaces \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "{\"template_name\": \"base-workspace\", \"properties\": {}}" &
done
wait

# Check all deployed successfully
curl -s http://localhost:8000/api/workspaces | jq 'length'

# Verify all containers running
docker ps | grep workspace | wc -l
```

**Expected Results:**
- [ ] All 5 workspaces deploy successfully
- [ ] No race conditions
- [ ] All containers running
- [ ] No resource conflicts
- [ ] All routes configured correctly

**Acceptance Criteria:**
- All deployments complete within 2 minutes
- No failures
- System remains stable

---

### 12. Code Quality Tests

#### 12.1 Linting
**All Stories**  
**Objective:** Verify code follows style guidelines

**Test Steps:**
```bash
cd api_app
flake8 api/ providers/ event_grid/ --count --max-line-length=127

cd ../resource_processor/local_runner
flake8 . --count --max-line-length=127
```

**Expected Results:**
- [ ] No linting errors
- [ ] Code follows PEP 8 guidelines
- [ ] No unused imports

**Acceptance Criteria:**
- Zero linting errors

---

## Test Execution Checklist

- [ ] All infrastructure tests passed
- [ ] All workspace template tests passed
- [ ] All resource processor tests passed
- [ ] All container registry tests passed
- [ ] All Traefik routing tests passed
- [ ] All observability tests passed
- [ ] All integration tests passed
- [ ] All regression tests passed (Phases 2-3)
- [ ] All unit tests passed
- [ ] All performance tests passed
- [ ] Code quality checks passed

---

## Test Results Summary

**Executed By:** [Name]  
**Execution Date:** [Date]  
**Environment:** Docker (local)  
**Commit:** 916c604b9b42866bbb05fdf49f89a6f1340ce2d9

### Results

| Category | Tests | Passed | Failed | Status |
|----------|-------|--------|--------|--------|
| Infrastructure | 3 | TBD | TBD | ⏳ Pending |
| Workspace Templates | 2 | TBD | TBD | ⏳ Pending |
| Resource Processor | 2 | TBD | TBD | ⏳ Pending |
| Container Registry | 2 | TBD | TBD | ⏳ Pending |
| Traefik Routing | 2 | TBD | TBD | ⏳ Pending |
| Observability | 3 | TBD | TBD | ⏳ Pending |
| Integration | 3 | TBD | TBD | ⏳ Pending |
| Registry Integration | 1 | TBD | TBD | ⏳ Pending |
| Regression | 2 | TBD | TBD | ⏳ Pending |
| Unit Tests | 1 | TBD | TBD | ⏳ Pending |
| Performance | 1 | TBD | TBD | ⏳ Pending |
| Code Quality | 1 | TBD | TBD | ⏳ Pending |

### Issues Found

[Document any issues discovered during testing]

### Recommendations

[Document any recommendations for improvements]

---

## Sign-off

- [ ] All acceptance criteria met
- [ ] All test categories completed
- [ ] Test results documented
- [ ] Issues logged (if any)
- [ ] Ready to close Phase 4 stories

**Tester Signature:** _______________  
**Date:** _______________