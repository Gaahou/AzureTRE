# Phase 1 Testing Plan: Local API with Emulators

## Test Scope

**Feature ID:** 113 (Feature 113: Local API with Emulators - Phase 1)  
**Stories:** 114, 115, 116, 117  
**Branch:** `feature/phase1-local-api`  
**Last Commit:** TBD (to be filled during execution)

## Overview

Phase 1 enables the TRE API to run locally against Cosmos DB Emulator and Azurite storage emulator, eliminating Azure cloud dependencies for the data layer. This test plan validates all acceptance criteria from the epic documentation.

## Acceptance Criteria (from Epic)

- [x] `make up` (offline mode) starts Cosmos Emulator, Azurite, and the API
- [x] `http://localhost:8000/api/docs` loads Swagger UI
- [x] Can create/read/update/delete templates and resources in the state store
- [x] Cosmos Data Explorer accessible at `https://localhost:10250`

## Test Environment

**Testing Method:** Docker-based (per Rule #7)  
**Test Runner:** `scripts/test_phase1_docker.sh`  
**Docker Image:** `azuretre-api-test:phase1` (built from `api_app/Dockerfile` test stage)

## Test Categories

### 1. Infrastructure Tests (Docker Compose)

**Test 1.1: Service Startup**
- **Objective:** Verify all services start successfully
- **Steps:**
  1. Run `docker-compose up -d` from `deploy/offline/`
  2. Wait for all healthchecks to pass
  3. Check container status with `docker-compose ps`
- **Expected:**
  - `tre-cosmosdb-emulator` status: Up (healthy)
  - `tre-azurite` status: Up (healthy)
  - `tre-api` status: Up (healthy)
- **Pass Criteria:** All services show "Up (healthy)" status within 120 seconds

**Test 1.2: Service Dependencies**
- **Objective:** Verify startup ordering and dependencies
- **Steps:**
  1. Stop all services: `docker-compose down`
  2. Start only TRE API: `docker-compose up tre-api` (should wait for dependencies)
  3. Observe startup order in logs
- **Expected:**
  - cosmosdb starts first and becomes healthy
  - azurite starts and becomes healthy
  - tre-api starts only after both dependencies are healthy
- **Pass Criteria:** API does not start until dependencies are healthy

**Test 1.3: Port Accessibility**
- **Objective:** Verify all exposed ports are accessible from host
- **Steps:**
  1. Test Cosmos DB: `curl -k https://localhost:8081/_explorer/index.html`
  2. Test Azurite Blob: `curl http://localhost:10000/devstoreaccount1?comp=list`
  3. Test TRE API: `curl http://localhost:8000/api/health`
- **Expected:** All endpoints return successful responses (200/302)
- **Pass Criteria:** No connection refused errors

**Test 1.4: Data Persistence**
- **Objective:** Verify volumes persist data across restarts
- **Steps:**
  1. Create a test document in Cosmos via API
  2. Stop services: `docker-compose down`
  3. Start services: `docker-compose up -d`
  4. Query for the test document
- **Expected:** Document still exists after restart
- **Pass Criteria:** Data survives container restart

### 2. Environment Configuration Tests

**Test 2.1: Deployment Mode Flag**
- **Objective:** Verify `DEPLOYMENT_MODE=offline` is set
- **Steps:**
  1. Exec into tre-api container: `docker exec tre-api env | grep DEPLOYMENT_MODE`
- **Expected:** Output shows `DEPLOYMENT_MODE=offline`
- **Pass Criteria:** Environment variable is correctly set

**Test 2.2: Cosmos DB Connection**
- **Objective:** Verify API connects to Cosmos DB emulator
- **Steps:**
  1. Check tre-api logs for Cosmos connection success
  2. Verify `STATE_STORE_ENDPOINT` points to `https://cosmosdb:8081`
- **Expected:** No connection errors in logs
- **Pass Criteria:** API successfully connects to Cosmos emulator

**Test 2.3: Azurite Connection**
- **Objective:** Verify API connects to Azurite storage emulator
- **Steps:**
  1. Check tre-api logs for Storage connection success
  2. Verify `AZURE_STORAGE_CONNECTION_STRING` uses `devstoreaccount1`
- **Expected:** No storage connection errors in logs
- **Pass Criteria:** API successfully connects to Azurite

**Test 2.4: .env.sample Completeness**
- **Objective:** Verify .env.sample documents all required variables
- **Steps:**
  1. Read `deploy/offline/.env.sample`
  2. Compare variables with docker-compose.yml environment section
- **Expected:** All variables in docker-compose are documented in .env.sample
- **Pass Criteria:** No undocumented environment variables

### 3. Database Initialization Tests

**Test 3.1: Cosmos Database Creation**
- **Objective:** Verify `cosmos-init.sh` creates AzureTRE database
- **Steps:**
  1. Run seed script: `bash deploy/offline/seed/cosmos-init.sh`
  2. Query databases via REST API
- **Expected:** `AzureTRE` database exists
- **Pass Criteria:** Database creation succeeds without errors

**Test 3.2: Cosmos Containers Creation**
- **Objective:** Verify all required containers are created
- **Steps:**
  1. Run seed script: `bash deploy/offline/seed/cosmos-init.sh`
  2. List containers in AzureTRE database
- **Expected:** 7 containers exist:
  - Resources
  - ResourceTemplates
  - ResourceHistory
  - Operations
  - Requests
  - Migrations
  - Airlock (if enabled)
- **Pass Criteria:** All 7 containers created with `/id` partition key

**Test 3.3: Idempotent Initialization**
- **Objective:** Verify init script is idempotent (can run multiple times)
- **Steps:**
  1. Run `cosmos-init.sh` twice
  2. Check for errors on second run
- **Expected:** Second run completes without errors (detects existing resources)
- **Pass Criteria:** No "already exists" errors, graceful handling

**Test 3.4: Template Seeding**
- **Objective:** Verify `seed-templates.sh` loads template data
- **Steps:**
  1. Run template seed script: `bash deploy/offline/seed/seed-templates.sh`
  2. Query ResourceTemplates container
- **Expected:** Templates exist:
  - Base workspace template
  - Guacamole service template
  - Linux VM user resource templates
  - Windows VM user resource templates
  - Azure Firewall shared service template
- **Pass Criteria:** All 5+ templates successfully inserted

### 4. API Functionality Tests

**Test 4.1: Swagger UI Access**
- **Objective:** Verify Swagger UI loads successfully
- **Steps:**
  1. Navigate to `http://localhost:8000/api/docs` in browser or curl
  2. Verify HTML response
- **Expected:** Swagger UI HTML page loads with API documentation
- **Pass Criteria:** 200 OK response with swagger-ui content

**Test 4.2: Health Endpoint**
- **Objective:** Verify API health check endpoint works
- **Steps:**
  1. GET `http://localhost:8000/api/health`
- **Expected:** JSON response: `{"status": "healthy"}` or similar
- **Pass Criteria:** 200 OK with healthy status

**Test 4.3: List Templates (GET)**
- **Objective:** Verify can retrieve seeded templates
- **Steps:**
  1. GET `/api/workspace-templates` (or appropriate endpoint)
  2. Parse JSON response
- **Expected:** List of templates including base workspace
- **Pass Criteria:** 200 OK with array of template objects

**Test 4.4: Get Template by ID (GET)**
- **Objective:** Verify can retrieve single template
- **Steps:**
  1. GET `/api/workspace-templates/{id}` with known template ID from seed data
- **Expected:** Single template object with all fields
- **Pass Criteria:** 200 OK with template details

**Test 4.5: Create Template (POST)**
- **Objective:** Verify can create new template
- **Steps:**
  1. POST `/api/workspace-templates` with valid template JSON
  2. Verify template is created in Cosmos
- **Expected:** 201 Created with new template ID
- **Pass Criteria:** Template persists and can be retrieved

**Test 4.6: Update Template (PUT/PATCH)**
- **Objective:** Verify can update existing template
- **Steps:**
  1. PATCH `/api/workspace-templates/{id}` with modified fields
  2. GET the template to verify changes
- **Expected:** 200 OK, changes persisted
- **Pass Criteria:** Updated fields reflected in subsequent GET

**Test 4.7: Delete Template (DELETE)**
- **Objective:** Verify can delete template
- **Steps:**
  1. DELETE `/api/workspace-templates/{id}`
  2. GET the template (should return 404)
- **Expected:** 204 No Content, template removed
- **Pass Criteria:** Template no longer exists in state store

**Test 4.8: Create Resource**
- **Objective:** Verify can create resource records
- **Steps:**
  1. POST `/api/workspaces` with valid workspace definition
  2. Verify resource appears in Resources container
- **Expected:** 201 Created with resource ID
- **Pass Criteria:** Resource persists in Cosmos

**Test 4.9: List Resources (GET)**
- **Objective:** Verify can retrieve created resources
- **Steps:**
  1. GET `/api/workspaces`
- **Expected:** List of workspace resources
- **Pass Criteria:** 200 OK with array of resources

**Test 4.10: Get Resource by ID (GET)**
- **Objective:** Verify can retrieve single resource
- **Steps:**
  1. GET `/api/workspaces/{id}`
- **Expected:** Single resource object
- **Pass Criteria:** 200 OK with resource details

### 5. Cosmos DB Emulator Tests

**Test 5.1: Data Explorer Access**
- **Objective:** Verify Cosmos Data Explorer is accessible
- **Steps:**
  1. Navigate to `https://localhost:10250/_explorer/index.html`
  2. Accept self-signed certificate warning
- **Expected:** Cosmos Data Explorer UI loads
- **Pass Criteria:** Can view AzureTRE database and containers in UI

**Test 5.2: REST API Access**
- **Objective:** Verify can query Cosmos via REST API directly
- **Steps:**
  1. Use curl with emulator key to query databases
  2. List containers in AzureTRE database
- **Expected:** JSON responses from Cosmos REST API
- **Pass Criteria:** Direct REST queries work with emulator key

**Test 5.3: Partition Key Validation**
- **Objective:** Verify all containers use `/id` partition key
- **Steps:**
  1. Query container metadata via REST API
  2. Check partitionKey field
- **Expected:** `"partitionKey": {"paths": ["/id"]}`
- **Pass Criteria:** All containers have correct partition key

### 6. Azurite Storage Tests

**Test 6.1: Blob Service**
- **Objective:** Verify Azurite blob service works
- **Steps:**
  1. Use Azure Storage SDK to create container
  2. Upload test blob
  3. Download blob and verify content
- **Expected:** Blob operations succeed
- **Pass Criteria:** Upload/download works via Azurite

**Test 6.2: Queue Service**
- **Objective:** Verify Azurite queue service works
- **Steps:**
  1. Create queue via SDK
  2. Send message to queue
  3. Retrieve message
- **Expected:** Queue operations succeed
- **Pass Criteria:** Message can be sent and retrieved

**Test 6.3: Table Service**
- **Objective:** Verify Azurite table service works
- **Steps:**
  1. Create table via SDK
  2. Insert entity
  3. Query entity
- **Expected:** Table operations succeed
- **Pass Criteria:** Entity can be inserted and queried

### 7. Negative Tests

**Test 7.1: Invalid Connection String**
- **Objective:** Verify API fails gracefully with invalid connection
- **Steps:**
  1. Modify STATE_STORE_KEY to invalid value
  2. Restart API
- **Expected:** API logs authentication error, does not crash
- **Pass Criteria:** Graceful error handling

**Test 7.2: Missing Database**
- **Objective:** Verify API handles missing database
- **Steps:**
  1. Start API before running cosmos-init.sh
  2. Attempt API operation
- **Expected:** API returns 503 Service Unavailable or similar
- **Pass Criteria:** Error indicates database not ready

**Test 7.3: Service Unavailable**
- **Objective:** Verify API handles emulator downtime
- **Steps:**
  1. Stop cosmosdb container
  2. Attempt API operation
- **Expected:** API returns error indicating downstream service unavailable
- **Pass Criteria:** Does not crash, returns appropriate error

### 8. Documentation Tests

**Test 8.1: README Accuracy**
- **Objective:** Verify deploy/offline/README.md instructions work
- **Steps:**
  1. Follow README quick start from clean state
  2. Verify all commands work as documented
- **Expected:** All commands execute without errors
- **Pass Criteria:** README is accurate and complete

**Test 8.2: Seed Scripts README**
- **Objective:** Verify deploy/offline/seed/README.md is accurate
- **Steps:**
  1. Follow seed script instructions
  2. Verify scripts work as documented
- **Expected:** Database and templates initialize correctly
- **Pass Criteria:** README accurately describes seed process

## Test Execution

### Prerequisites
- Docker Desktop installed and running
- Docker Compose v3.8+
- 4GB+ RAM allocated to Docker
- Ports 8000, 8081, 10000-10002, 10250-10255 available

### Manual Test Execution

```bash
# 1. Clean slate
cd deploy/offline
docker-compose down -v

# 2. Start services
docker-compose up -d

# 3. Wait for health
docker-compose ps
# Wait until all show "Up (healthy)"

# 4. Initialize database
bash seed/cosmos-init.sh

# 5. Seed templates
bash seed/seed-templates.sh

# 6. Run API tests
curl http://localhost:8000/api/health
curl http://localhost:8000/api/docs
curl http://localhost:8000/api/workspace-templates

# 7. Access Cosmos Data Explorer
open https://localhost:10250/_explorer/index.html

# 8. Cleanup
docker-compose down -v
```

### Automated Test Execution (Rule #7)

```bash
# Run comprehensive Phase 1 tests in Docker
./scripts/test_phase1_docker.sh

# Test output saved to:
# - /tmp/phase1_test_output.txt
```

## Test Deliverables

1. **Test Script:** `scripts/test_phase1_docker.sh` (Docker-based per Rule #7)
2. **Test Results:** Document in Testing User Story comments
3. **Test Output:** Commit test logs to repo under `docs/test-results/phase1/`
4. **Screenshots:** Capture Swagger UI, Cosmos Data Explorer, working API calls
5. **Updated Documentation:** Any corrections to READMEs based on testing

## Pass/Fail Criteria

### Phase 1 passes if:
- ✅ All 8 test categories have 0 failures
- ✅ All acceptance criteria from epic are met
- ✅ No critical bugs discovered
- ✅ Documentation is accurate

### Phase 1 fails if:
- ❌ Any service fails to start
- ❌ API cannot connect to emulators
- ❌ State store CRUD operations fail
- ❌ Seed scripts fail to initialize data
- ❌ Critical bugs block basic functionality

## Sign-off

**Tester:** ________________  
**Date:** ________________  
**Result:** ☐ PASS  ☐ FAIL

**Comments:**

---

**Related Work Items:**
- Feature #113: Local API with Emulators (Phase 1)
- Story #114: Create offline docker-compose with emulators
- Story #115: Create offline .env.sample  
- Story #116: Create Cosmos DB seed script
- Story #117: Create template seed data

**Testing User Story:** TBD (to be created per Rule #5)