# Team Workflow Rules - Azure TRE Development

## Overview

This document outlines the agreed-upon workflow rules for the Azure TRE development team when working with Azure DevOps work items and git commits.

---

## Rule 1: Work Item State Management

### Never move tasks to "Resolved" or "Closed" if they are not tested

**Rationale:** Moving work items to final states prematurely can lead to incomplete or untested features being considered done, which can cause issues in production.

**Workflow:**
1. **Active** - Work item is being actively worked on
2. **Resolved** - Implementation is complete AND tested (ready for review)
3. **Closed** - Work item has been reviewed and accepted

**Example:**
```bash
# ❌ WRONG - Don't do this after just committing
./scripts/ado_helper.sh update 106 "Resolved"  # No testing done yet!

# ✅ CORRECT - Keep in Active until tested
git commit -m "Story 106: Add deployment_mode config flag"
# Run tests first
make test
# Then move to Resolved
./scripts/ado_helper.sh update 106 "Resolved"
```

**Testing Checklist Before Moving to Resolved:**
- [ ] Unit tests pass
- [ ] Integration tests pass (if applicable)
- [ ] Manual testing complete
- [ ] Code compiles/runs without errors
- [ ] Documentation updated

---

## Rule 2: Add Comments to Work Items After Commits

### Make comments to the according cards right after we commit changes

**Rationale:** Keeping work item discussions synchronized with git commits creates a clear audit trail and helps team members understand the implementation progress without having to search through git logs.

**Required Information in Comments:**
- Commit hash
- Branch name
- GitHub link to commit
- Summary of changes
- Files modified
- Current status

**Template:**
```html
<strong>Implementation Complete</strong> ✅<br/><br/>
<strong>Commit:</strong> {commit_hash}<br/>
<strong>Branch:</strong> {branch_name}<br/>
<strong>GitHub:</strong> <a href="{github_url}">{github_url}</a><br/><br/>
<strong>Changes:</strong>
<ul>
  <li>Change description 1</li>
  <li>Change description 2</li>
</ul>
<strong>Status:</strong> {current_status}<br/><br/>
<strong>Files Modified:</strong>
<ul>
  <li>file1.py</li>
  <li>file2.yaml</li>
</ul>
```

**Example:**
```bash
# After committing
git commit -m "Story 106: Add deployment_mode config flag"
git push

# Immediately add comment to work item
curl -s http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "add_work_item_comment",
      "arguments": {
        "id": 106,
        "text": "<strong>Implementation Complete</strong> ✅<br/>..."
      }
    }
  }'
```

**Helper Script Usage:**
```bash
# The team should use the helper script (coming soon)
./scripts/ado_comment.sh 106 "$(git log -1 --format='%H')" "feature/phase0-provider-abstraction"
```

---

## Workflow Checklist

### Starting a Story
- [ ] Move story to **Active** in Azure DevOps
- [ ] Create feature branch from main
- [ ] Ensure you understand acceptance criteria

### During Implementation
- [ ] Make frequent, atomic commits
- [ ] Keep commits focused on single concerns
- [ ] Write clear commit messages referencing work item ID

### After Each Commit
- [ ] Push commit to GitHub
- [ ] ✅ **RULE 2:** Add comment to work item with commit details
- [ ] Keep work item in **Active** state

### Before Moving to Resolved
- [ ] ✅ **RULE 1:** Run all relevant tests
- [ ] Manual testing complete
- [ ] Code review ready (if required)
- [ ] Documentation updated
- [ ] Then and only then, move to **Resolved**

### Code Review
- [ ] Create Pull Request
- [ ] Link PR to work item
- [ ] Address review comments
- [ ] Get approval

### After Merge
- [ ] Move work item to **Closed**
- [ ] Add final comment with merge details
- [ ] Delete feature branch (if workflow allows)

---

## Tools

### ADO Helper Script
```bash
# Update work item state
./scripts/ado_helper.sh update <id> <state>

# Get work item details
./scripts/ado_helper.sh get <id>

# Test MCP connection
./scripts/ado_helper.sh test
```

### Adding Comments Programmatically
```bash
# Via MCP server
curl -s http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "add_work_item_comment",
      "arguments": {
        "id": <work_item_id>,
        "text": "<HTML formatted comment>"
      }
    }
  }'
```

---

## Enforcement

These rules are enforced through:
1. **Peer Review** - Team members review PRs for adherence
2. **Claude Code** - Automated reminders in development workflow
3. **ADO Helper Scripts** - Built-in prompts and checks
4. **Team Retrospectives** - Regular review of adherence

---

## Example: Complete Workflow

```bash
# 1. Start Story 107
./scripts/ado_helper.sh update 107 "Active"
git checkout -b feature/story-107

# 2. Implement changes
# ... make code changes ...

# 3. Commit
git add deploy/
git commit -m "Story 107: Create deploy/ folder structure

- Create deploy/online/, deploy/offline/, deploy/shared/ directories
- Add env.sh and healthcheck.sh scripts

Related Work Item: #107"

# 4. Push
git push origin feature/story-107

# 5. ✅ RULE 2: Add comment immediately
curl -s http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "add_work_item_comment",
      "arguments": {
        "id": 107,
        "text": "<strong>Implementation Complete</strong> ✅<br/>..."
      }
    }
  }'

# 6. Test
./deploy/shared/env.sh
./deploy/shared/healthcheck.sh

# 7. ✅ RULE 1: Only move to Resolved after testing
./scripts/ado_helper.sh update 107 "Resolved"

# 8. Add final comment
# ... add comment about testing results ...
```

---

## Questions?

For questions about these workflow rules, contact:
- Team Lead
- Scrum Master
- See also: [docs/ado-mcp-setup.md](./ado-mcp-setup.md)

## Updates

This document should be reviewed and updated during sprint retrospectives or when workflow improvements are identified.

**Last Updated:** 2026-05-02
**Version:** 1.0