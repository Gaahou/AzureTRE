# TRE Local Development - Quick Start

## Start Everything
```bash
cd /Users/andrew/Desktop/PoC/AzureTRE/deploy/offline
docker-compose up -d
```

## Check Status
```bash
docker-compose ps
curl http://localhost:8000/api/health | jq .
```

## Access UIs
- **API Docs**: http://localhost:8000/api/docs
- **Grafana**: http://localhost:3001 (admin/admin)
- **Jaeger**: http://localhost:16686
- **RabbitMQ**: http://localhost:15672 (tre_user/tre_password)
- **Keycloak**: http://localhost:8080/admin (admin/admin_password)
- **Vault**: http://localhost:8200 (token: root-token)

## Get Auth Token
```bash
TOKEN=$(curl -s -X POST http://localhost:8080/realms/AzureTRE/protocol/openid-connect/token \
  -d "client_id=tre-api-client" \
  -d "client_secret=tre-api-client-secret" \
  -d "grant_type=client_credentials" | jq -r '.access_token')

echo $TOKEN
```

## Test API with Auth
```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/workspaces | jq .
```

## View Logs
```bash
docker-compose logs -f tre-api
docker-compose logs -f tre-resource-processor
```

## Stop Everything
```bash
docker-compose down
```

## Full Details
See [LOCAL_TRE_STATUS.md](LOCAL_TRE_STATUS.md) for complete documentation.
