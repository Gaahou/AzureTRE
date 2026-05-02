#!/bin/bash
# Azure DevOps Work Item Comment Helper
# Adds formatted comments to work items after commits

MCP_URL="${MCP_URL:-http://localhost:3000/mcp}"

# Show usage
if [[ $# -lt 2 ]]; then
    cat <<EOF
Usage: $0 <work_item_id> <commit_hash> [branch_name] [status]

Adds a formatted comment to a work item with commit details.

Arguments:
  work_item_id  Work item ID number
  commit_hash   Git commit hash (short or full)
  branch_name   Git branch name (optional, auto-detected if omitted)
  status        Current status text (optional, default: "Implementation in progress")

Examples:
  # Basic usage (auto-detect branch)
  $0 106 02c85a39

  # With branch name
  $0 106 02c85a39 feature/phase0-provider-abstraction

  # With custom status
  $0 106 02c85a39 feature/phase0 "Implementation complete, awaiting testing"

  # Quick: Use current commit and branch
  $0 106 "\$(git log -1 --format='%H')"

Environment:
  MCP_URL: $MCP_URL
  GITHUB_REPO: GitHub repository (default: Gaahou/AzureTRE)

EOF
    exit 1
fi

WORK_ITEM_ID="$1"
COMMIT_HASH="$2"
BRANCH_NAME="${3:-$(git rev-parse --abbrev-ref HEAD 2>/dev/null)}"
STATUS="${4:-Implementation in progress}"
GITHUB_REPO="${GITHUB_REPO:-Gaahou/AzureTRE}"

# Get commit details
if git rev-parse --verify "$COMMIT_HASH" >/dev/null 2>&1; then
    COMMIT_SHORT=$(git rev-parse --short "$COMMIT_HASH")
    COMMIT_FULL=$(git rev-parse "$COMMIT_HASH")
    COMMIT_MSG=$(git log -1 --format='%s' "$COMMIT_HASH")
    COMMIT_FILES=$(git diff-tree --no-commit-id --name-only -r "$COMMIT_HASH" | head -10)
else
    echo "❌ Error: Invalid commit hash: $COMMIT_HASH"
    exit 1
fi

# Build GitHub URL
GITHUB_URL="https://github.com/${GITHUB_REPO}/commit/${COMMIT_FULL}"

# Build file list HTML
FILES_HTML=""
while IFS= read -r file; do
    FILES_HTML="${FILES_HTML}<li>${file}</li>"
done <<< "$COMMIT_FILES"

# Build comment HTML
COMMENT_HTML="<strong>Commit Added</strong> 💾<br/><br/>\
<strong>Commit:</strong> ${COMMIT_SHORT} (${COMMIT_MSG})<br/>\
<strong>Branch:</strong> ${BRANCH_NAME}<br/>\
<strong>GitHub:</strong> <a href=\"${GITHUB_URL}\">${GITHUB_URL}</a><br/><br/>\
<strong>Status:</strong> ${STATUS}<br/><br/>\
<strong>Files Modified:</strong>\
<ul>${FILES_HTML}</ul>"

# Add comment via MCP
echo "Adding comment to work item #${WORK_ITEM_ID}..."
result=$(curl -s "$MCP_URL" \
    -H "Content-Type: application/json" \
    -d "{
        \"jsonrpc\": \"2.0\",
        \"id\": 1,
        \"method\": \"tools/call\",
        \"params\": {
            \"name\": \"add_work_item_comment\",
            \"arguments\": {
                \"id\": ${WORK_ITEM_ID},
                \"text\": $(echo "$COMMENT_HTML" | jq -Rs .)
            }
        }
    }")

# Check result
if echo "$result" | jq -e '.result.content[0].text' >/dev/null 2>&1; then
    COMMENT_ID=$(echo "$result" | jq -r '.result.content[0].text | fromjson | .id')
    echo "✓ Comment added successfully (ID: ${COMMENT_ID})"
    echo "  Commit: ${COMMIT_SHORT}"
    echo "  Branch: ${BRANCH_NAME}"
    echo "  View: https://dev.azure.com/${GITHUB_REPO%/*}/_workitems/edit/${WORK_ITEM_ID}"
else
    echo "❌ Error adding comment:"
    echo "$result" | jq -r '.result.content[0].text // .error // .'
    exit 1
fi