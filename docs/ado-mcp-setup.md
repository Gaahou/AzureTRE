# Azure DevOps MCP Server Setup

## Overview

This project uses a local Azure DevOps MCP (Model Context Protocol) server to enable Claude Code to directly interact with Azure DevOps work items.

## Configuration

### MCP Server Configuration

The MCP server is configured in [.mcp.json](../.mcp.json):

```json
{
  "mcpServers": {
    "azure-devops": {
      "type": "url",
      "url": "http://localhost:3000/mcp"
    }
  }
}
```

### Prerequisites

1. **MCP Server Running**: Ensure the Azure DevOps MCP server is running at `http://localhost:3000/mcp`
2. **Environment Variables**: The MCP server typically requires:
   - `ADO_ORG`: Azure DevOps organization URL
   - `ADO_PROJECT`: Default project name
   - `ADO_PAT`: Personal Access Token with work item read/write permissions

## Available Tools

The MCP server exposes the following tools:

| Tool | Description |
|------|-------------|
| `list_work_items` | Execute WIQL queries to retrieve work items |
| `get_work_item` | Get complete details for a single work item by ID |
| `create_work_item` | Create new work items (Bug, Task, User Story, Epic, Feature) |
| `update_work_item` | Update existing work items (state, assignee, fields) |
| `delete_work_item` | Delete work items |
| `add_comment` | Add comments to work items |
| `link_work_items` | Create relationships between work items |
| `query_work_items` | Simplified work item filtering |
| `search_work_items` | Full-text search across work items |

## Helper Script

Use the provided helper script for command-line access:

```bash
# Test connection
./scripts/ado_helper.sh test

# Update work item state
./scripts/ado_helper.sh update 106 Active

# Get work item details
./scripts/ado_helper.sh get 106

# Activate multiple stories
./scripts/ado_helper.sh activate 106 107 108 109 110 111 112

# Query work items
./scripts/ado_helper.sh query "SELECT [System.Id] FROM WorkItems WHERE [System.WorkItemType] = 'User Story'"
```

## Using in Claude Code

### Direct curl invocation (always works)

```bash
curl -s http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "update_work_item",
      "arguments": {
        "id": 106,
        "state": "Active"
      }
    }
  }' | jq '.'
```

### Via helper script (recommended)

```bash
./scripts/ado_helper.sh update 106 Active
```

### MCP Tool Discovery (when available)

Once MCP tools are properly discovered by Claude Code, they should be directly callable as native tools. This is the preferred method but requires proper tool registration.

## Troubleshooting

### MCP Server Not Responding

```bash
# Test if server is running
curl -s http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}' \
  | jq '.result.tools[] | .name'
```

### Work Item Updates Failing

Check that:
1. Your PAT has `Work Items (Read & write)` permission
2. The project name is correct
3. The state you're transitioning to is valid for the work item type

### Authentication Issues

Verify environment variables are set:
```bash
echo $ADO_ORG
echo $ADO_PROJECT
echo $ADO_PAT  # Should show masked value
```

## Project Structure

```
AzureTRE/
├── .mcp.json                      # MCP server configuration
├── scripts/
│   └── ado_helper.sh             # CLI helper for ADO operations
└── docs/
    └── ado-mcp-setup.md          # This file
```

## Common Workflows

### Moving Stories to Active

```bash
# Phase 0 stories (106-112)
./scripts/ado_helper.sh activate 106 107 108 109 110 111 112
```

### Querying Work Items by Epic

```bash
./scripts/ado_helper.sh query \
  "SELECT [System.Id], [System.Title], [System.State] 
   FROM WorkItems 
   WHERE [System.Parent] = 104"
```

### Checking Story Status

```bash
./scripts/ado_helper.sh get 106 | jq '{id, title, state, assignedTo}'
```

## References

- [MCP Specification](https://modelcontextprotocol.io/)
- [Azure DevOps REST API](https://learn.microsoft.com/en-us/rest/api/azure/devops/)
- [WIQL Syntax](https://learn.microsoft.com/en-us/azure/devops/boards/queries/wiql-syntax)
