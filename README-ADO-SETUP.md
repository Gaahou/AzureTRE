# Azure DevOps MCP Setup Complete ✓

## What's Configured

Your Azure TRE project now has a persistent connection to Azure DevOps via the MCP (Model Context Protocol) server running at `http://localhost:3000/mcp`.

## Files Created

1. **[.mcp.json](./.mcp.json)** - MCP server configuration (persists across Claude sessions)
2. **[scripts/ado_helper.sh](./scripts/ado_helper.sh)** - CLI helper for ADO operations
3. **[docs/ado-mcp-setup.md](./docs/ado-mcp-setup.md)** - Complete MCP setup documentation
4. **[docs/quick-start-phase0.md](./docs/quick-start-phase0.md)** - Phase 0 implementation guide

## Quick Reference

### Test Connection
```bash
./scripts/ado_helper.sh test
```

### Update Work Item State
```bash
# Move story 106 to "In Progress"
./scripts/ado_helper.sh update 106 "In Progress"

# Move story 106 to "Done"
./scripts/ado_helper.sh update 106 "Done"
```

### Get Work Item Details
```bash
./scripts/ado_helper.sh get 106
```

### Query Work Items
```bash
./scripts/ado_helper.sh query "SELECT [System.Id], [System.Title] FROM WorkItems WHERE [System.Parent] = 105"
```

### Bulk Activate Stories
```bash
./scripts/ado_helper.sh activate 106 107 108 109
```

## Current Status

### Phase 0 Stories - ALL ACTIVE ✓

| ID | Story | Status |
|----|-------|--------|
| 106 | 1.1 - Add deployment_mode config flag | ✓ **Active** |
| 107 | 1.2 - Create deploy/ folder structure | ✓ **Active** |
| 108 | 1.3 - Create provider interfaces | ✓ **Active** |
| 109 | 1.4 - Extract Azure implementations | ✓ **Active** |
| 110 | 1.5 - Create provider factory | ✓ **Active** |
| 111 | 1.6 - Refactor service_bus/helpers.py | ✓ **Active** |
| 112 | 1.7 - Add mode-aware Makefile targets | ✓ **Active** |

## Using in Future Claude Sessions

The `.mcp.json` configuration file ensures that the Azure DevOps MCP server connection persists across Claude Code sessions. However, Claude Code's current MCP tool discovery has limitations, so the most reliable approach is:

### Option 1: Via Helper Script (Recommended)
```bash
./scripts/ado_helper.sh update 106 "In Progress"
```

### Option 2: Direct curl (Always Works)
```bash
curl -s http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "update_work_item",
      "arguments": {"id": 106, "state": "In Progress"}
    }
  }' | jq '.'
```

### Option 3: Ask Claude to Use MCP Tools
Simply ask Claude Code to:
- "Update work item 106 to In Progress using the MCP server"
- "Get details for story 107 from Azure DevOps"
- "Move Phase 0 stories to Done"

Claude will use the helper script or direct curl commands as needed.

## Available MCP Tools

- `list_work_items` - Execute WIQL queries
- `get_work_item` - Get complete work item details
- `create_work_item` - Create new work items
- `update_work_item` - Update work item fields/state
- `delete_work_item` - Delete work items
- `add_comment` - Add comments to work items
- `link_work_items` - Create work item relationships
- `query_work_items` - Simplified filtering
- `search_work_items` - Full-text search

## Prerequisites

Ensure the MCP server is running:
```bash
curl -s http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}' \
  | jq -r '.result.tools[] | .name' | head -5
```

Expected output:
```
list_work_items
get_work_item
create_work_item
update_work_item
delete_work_item
```

## Next Steps

1. **Start Phase 0 Implementation**: See [docs/quick-start-phase0.md](./docs/quick-start-phase0.md)
2. **Review Epic Plan**: See [architecture_review/epic-local-tre-deployment.md](./architecture_review/epic-local-tre-deployment.md)
3. **Review Design Doc**: See [architecture_review/local-deployment.md](./architecture_review/local-deployment.md)

## Troubleshooting

### MCP Server Not Responding
```bash
# Check if server is running
curl http://localhost:3000/health

# Restart the server (method depends on your setup)
```

### Authentication Issues
Verify the MCP server has valid Azure DevOps credentials:
- `ADO_ORG` - Organization URL
- `ADO_PROJECT` - Project name
- `ADO_PAT` - Personal Access Token with work item permissions

## Documentation

- [ADO MCP Setup](./docs/ado-mcp-setup.md) - Complete MCP configuration guide
- [Phase 0 Quick Start](./docs/quick-start-phase0.md) - Implementation guide
- [Epic Document](./architecture_review/epic-local-tre-deployment.md) - Full epic breakdown
- [Design Document](./architecture_review/local-deployment.md) - Technical design
