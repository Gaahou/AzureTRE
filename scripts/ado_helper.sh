#!/bin/bash
# Azure DevOps MCP Helper Script
# This script provides easy access to Azure DevOps work item operations via the local MCP server

MCP_URL="${MCP_URL:-http://localhost:3000/mcp}"

# Function to call MCP tool
call_mcp_tool() {
    local tool_name="$1"
    local arguments="$2"

    curl -s "$MCP_URL" \
        -H "Content-Type: application/json" \
        -d "{
            \"jsonrpc\": \"2.0\",
            \"id\": 1,
            \"method\": \"tools/call\",
            \"params\": {
                \"name\": \"$tool_name\",
                \"arguments\": $arguments
            }
        }"
}

# Update work item state
update_work_item_state() {
    local id="$1"
    local state="$2"

    echo "Updating work item $id to $state..."
    result=$(call_mcp_tool "update_work_item" "{\"id\": $id, \"state\": \"$state\"}" \
        | jq -r '.result.content[0].text | fromjson | "\(.id): \(.title) → \(.state)"')
    echo "  ✓ $result"
}

# Get work item details
get_work_item() {
    local id="$1"

    call_mcp_tool "get_work_item" "{\"id\": $id}" \
        | jq -r '.result.content[0].text | fromjson'
}

# Query work items by WIQL
query_work_items() {
    local query="$1"

    call_mcp_tool "list_work_items" "{\"query\": \"$query\"}" \
        | jq -r '.result.content[0].text | fromjson'
}

# Bulk update stories to Active
activate_stories() {
    local ids=("$@")

    for id in "${ids[@]}"; do
        update_work_item_state "$id" "Active"
    done
}

# Main command dispatcher
case "$1" in
    update)
        shift
        update_work_item_state "$@"
        ;;
    get)
        shift
        get_work_item "$@"
        ;;
    query)
        shift
        query_work_items "$@"
        ;;
    activate)
        shift
        activate_stories "$@"
        ;;
    test)
        echo "Testing MCP connection to $MCP_URL..."
        curl -s "$MCP_URL" \
            -H "Content-Type: application/json" \
            -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}' \
            | jq -r '.result.tools[] | .name' | head -5
        echo "✓ MCP server is responding"
        ;;
    *)
        cat <<EOF
Azure DevOps MCP Helper

Usage:
  $0 update <id> <state>        Update work item state
  $0 get <id>                   Get work item details
  $0 query "<WIQL>"             Query work items
  $0 activate <id1> [id2...]    Activate multiple stories
  $0 test                       Test MCP connection

Examples:
  $0 update 106 Active
  $0 get 106
  $0 query "SELECT [System.Id] FROM WorkItems WHERE [System.WorkItemType] = 'User Story'"
  $0 activate 106 107 108 109 110 111 112
  $0 test

Environment:
  MCP_URL: $MCP_URL
EOF
        ;;
esac