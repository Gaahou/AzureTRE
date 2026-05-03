# Team Workflow Rules - Azure TRE Development

## Overview

This document outlines the agreed-upon workflow rules for the Azure TRE development team when working with Azure DevOps work items and git commits.

---

## Rule 1: Work Item State Management

### Never move tasks to "Closed" if they are not well tested. Move to "Resolved" when implementation is complete (no test cases left behind).

**Rationale:** Proper state management ensures work items move through appropriate stages - implementation complete, then thoroughly tested, then closed.

**Workflow:**
1. **Active** - Work item is being actively worked on
2. **Resolved** - Implementation is complete (no test cases left behind, ready for testing/review)
3. **Closed** - Work item has been well tested and verified

**Example:**
```bash
# ✅ CORRECT - Move to Resolved when implementation complete
git commit -m "Story 106: Add deployment_mode config flag"
# Implementation done, move to Resolved
./scripts/ado_helper.sh update 106 "Resolved"

# ❌ WRONG - Don't move to Closed without thorough testing
./scripts/ado_helper.sh update 106 "Closed"  # Not well tested yet!

# ✅ CORRECT - Move to Closed after thorough testing
# Run comprehensive tests
make test
make lint
# Manual testing
# Integration testing
# Then move to Closed
./scripts/ado_helper.sh update 106 "Closed"
```

**Implementation Complete Checklist (Before Moving to Resolved):**
- [ ] Code implementation finished
- [ ] Basic testing done (scripts run, syntax valid)
- [ ] Code compiles/runs without errors
- [ ] Committed and pushed
- [ ] Documentation updated
- [ ] Comment added to work item

**Well Tested Checklist (Before Moving to Closed):**
- [ ] Unit tests pass
- [ ] Integration tests pass (if applicable)
- [ ] Manual testing complete
- [ ] Edge cases tested
- [ ] Code reviewed (if required)

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

### Format 2: Comprehensive Comment for Closing Work Items (Resolved → Closed)

**When:** Use this comprehensive format when closing work items after testing is complete.

**Structure Order (MANDATORY):**
1. **Title** with ✅: `<strong>Story/Feature #XXX Complete</strong> ✅<br><br>`
2. **Commit(s):** `<strong>Commit:</strong> <code>hash</code>: message<br>` (use "Commits:" if multiple)
3. **Branch:** `<strong>Branch:</strong> branch-name<br>`
4. **GitHub:** `<strong>GitHub:</strong> <a href="url">url</a><br><br>`
5. **Status:** `<strong>Status:</strong> Complete ✅<br><br>`
6. **Files Created/Modified:** `<strong>Files Created:</strong><ul><li>file</li></ul>`
7. **Implementation:** `<strong>Implementation:</strong><br>- full details<br><br>`
8. **Testing/Features:** `<strong>Testing:</strong><br>✅ test results<br>`
9. **Documentation:** `<strong>Documentation:</strong><ul><li>docs</li></ul>` (if applicable)

**Template:**
```html
<strong>Story #123 Complete</strong> ✅<br><br>

<strong>Commit:</strong> <code>abc123</code>: Story 123: Description<br>
<strong>Branch:</strong> feature/branch-name<br>
<strong>GitHub:</strong> <a href="https://github.com/org/repo/commit/abc123">https://github.com/org/repo/commit/abc123</a><br><br>

<strong>Status:</strong> Complete ✅<br><br>

<strong>Files Created:</strong>
<ul>
<li>path/to/file.py</li>
<li>path/to/another.js</li>
</ul>

<strong>Implementation:</strong><br>
- Created X functionality<br>
- Added Y feature<br>
- Configured Z settings<br><br>

<strong>Testing:</strong><br>
✅ Unit tests pass (22/22)<br>
✅ Integration tests pass<br>
✅ Manual testing complete<br><br>

<strong>Documentation:</strong>
<ul>
<li>docs/feature-guide.md</li>
<li>scripts/README.md</li>
</ul>
```

**Usage:**
- **Format 1 (above)**: Use after commits during implementation (Active → Resolved)
- **Format 2 (this section)**: Use when closing work items after testing (Resolved → Closed)

---

## Rule 3: Feature Completion and Next Feature Activation

### When the last story in a feature is Resolved, mark the feature as Resolved and prompt for moving to the next feature with all its stories to Active

**Rationale:** Ensures systematic progression through features and maintains clear visibility of feature completion status. Prevents orphaned stories and ensures the team stays aligned on which feature is being worked on.

**Workflow:**
1. When moving the **last story** in a feature to **Resolved**, also move the parent **Feature** to **Resolved**
2. Prompt the user to activate the next feature and all its stories
3. Wait for user confirmation before activating the next feature
4. When confirmed, move the next feature and all its stories to **Active**

**Example:**
```bash
# Story 112 is the last story in Feature 1.0 (Phase 0: Provider Abstraction)
./scripts/ado_helper.sh update 112 "Resolved"

# Automatically move Feature 1.0 to Resolved
./scripts/ado_helper.sh update <feature-id> "Resolved"

# Prompt user:
# "Feature 1.0 (Phase 0) is complete! Move to Feature 1.1 (Phase 1) with Stories 113-118? (y/n)"

# If user confirms:
./scripts/ado_helper.sh update <next-feature-id> "Active"
./scripts/ado_helper.sh activate 113 114 115 116 117 118
```

**Feature Completion Checklist:**
- [ ] All stories in the feature are Resolved
- [ ] Feature integration testing complete
- [ ] Feature documentation updated
- [ ] Feature moved to Resolved
- [ ] User prompted for next feature activation

**Next Feature Activation Checklist:**
- [ ] User confirms readiness to start next feature
- [ ] Next feature moved to Active
- [ ] All stories in next feature moved to Active
- [ ] Team notified of feature transition

---

## Rule 4: Feature Branch Strategy

### Branch out a new feature branch based on the previous feature for ease of testing later on

**Rationale:** Creating feature branches that build on top of each other maintains a clear dependency chain and enables incremental testing. Each feature can be tested independently while still having access to all previous features' code. This makes it easier to merge features sequentially and isolate issues.

**Workflow:**
1. When starting a new feature, create a new branch from the **previous feature's branch** (not from main)
2. Name the branch using a consistent pattern: `feature/phase{N}-{description}`
3. This creates a branch chain: main → phase0 → phase1 → phase2 → etc.
4. Each phase can be tested independently and merged to main in order

**Example:**
```bash
# Feature 105 (Phase 0) - Start from main
git checkout main
git checkout -b feature/phase0-provider-abstraction
# ... work on Phase 0 stories 106-112 ...
git push origin feature/phase0-provider-abstraction

# Feature 113 (Phase 1) - Start from Phase 0 branch
git checkout feature/phase0-provider-abstraction
git checkout -b feature/phase1-local-api
# ... work on Phase 1 stories 113-117 ...
git push origin feature/phase1-local-api

# Feature 118 (Phase 2) - Start from Phase 1 branch
git checkout feature/phase1-local-api
git checkout -b feature/phase2-message-queue
# ... work on Phase 2 stories ...
git push origin feature/phase2-message-queue
```

**Benefits:**
- **Incremental Testing**: Each feature branch contains all previous features, enabling full integration testing
- **Clear Dependencies**: Branch hierarchy reflects feature dependencies
- **Easier Debugging**: Issues can be traced back through the branch chain
- **Flexible Merging**: Features can be merged to main in sequence after testing
- **Isolation**: If a feature needs rework, it doesn't block subsequent features from being developed

**Branch Naming Convention:**
- `feature/phase{N}-{short-description}` for phase-based features
- Example: `feature/phase0-provider-abstraction`, `feature/phase1-local-api`, `feature/phase2-message-queue`

**Merging Strategy:**
When all features are tested and ready:
1. Merge Phase 0 → main
2. Rebase Phase 1 onto main, test, merge → main
3. Rebase Phase 2 onto main, test, merge → main
4. Continue in sequence

Alternatively, if features are tightly coupled and tested together:
1. Merge final phase branch → main (contains all previous phases)
2. Close intermediate feature branches

---

## Rule 5: Feature Testing Workflow

### For every feature test: create a User Story to capture the testing plan, link to the feature, test against the last commit, and properly close work items upon success

**Rationale:** Formalizing the testing process ensures thorough validation before closing features. Creating a dedicated testing user story provides a clear audit trail, captures test results, and ensures all team members know when features are ready for production.

**Workflow:**

1. **Create Testing User Story**
   - Create a new User Story in Azure DevOps for testing the completed feature
   - Title format: `Test {Feature Name} (Phase {N})`
   - Description: Include testing plan, test cases, and acceptance criteria
   - Link to the feature being tested (Add Link → Parent → Feature ID)
   
2. **Test Against Last Commit**
   - Ensure testing is performed against the last commit from the last User Story of the feature branch
   - Document the commit hash in the testing story
   - Verify all feature acceptance criteria are met
   
3. **On Test Success**
   - Commit test results and any test scripts to the same feature branch
   - Add comments to all related work items (feature + all stories) with test results
   - Update work item states:
     - Stories: Move from **Resolved** → **Closed**
     - Feature: Move from **Resolved** → **Closed**
     - Testing Story: Move from **Active** → **Closed**

4. **On Test Failure**
   - Document failures in the testing story
   - Reopen affected user stories (move back to **Active**)
   - Link bug work items to the testing story
   - Feature remains in **Resolved** until issues are fixed

**Example:**

```bash
# 1. Create testing story via ADO MCP
curl -s http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "create_work_item",
      "arguments": {
        "project": "TRE playground",
        "work_item_type": "User Story",
        "title": "Test Phase 0: Provider Abstraction & Mode Switching",
        "description": "Comprehensive testing of Phase 0...",
        "assigned_to": "andrew@example.com"
      }
    }
  }'

# 2. Link testing story to feature
curl -s http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "add_work_item_link",
      "arguments": {
        "id": <testing-story-id>,
        "link_type": "System.LinkTypes.Hierarchy-Reverse",
        "target_id": 105,
        "comment": "Testing story for Phase 0 feature"
      }
    }
  }'

# 3. Test against last commit
git checkout feature/phase0-provider-abstraction
LAST_COMMIT=$(git log -1 --format='%H')
echo "Testing against commit: $LAST_COMMIT"

# Run test suite
./scripts/test_phase0.sh

# 4a. If tests pass - commit test artifacts
git add docs/phase0-test-plan.md scripts/test_phase0.sh
git commit -m "Test Phase 0: All acceptance criteria met

- Created comprehensive test plan
- All unit tests passing
- All integration tests passing
- No regressions detected

Tested against commit: $LAST_COMMIT

Related Work Items: #<testing-story-id>, #105, #106-112"

git push

# 4b. Comment all related work items
# Feature 105
./scripts/ado_comment.sh 105 "Testing Complete" "All Phase 0 tests passed. Ready to close."

# Stories 106-112
for story_id in 106 107 108 109 110 111 112; do
  ./scripts/ado_comment.sh $story_id "Testing Complete" "Phase 0 testing passed. Moving to Closed."
done

# Testing story
./scripts/ado_comment.sh <testing-story-id> "Testing Complete" "All tests passed, see commit $LAST_COMMIT"

# 4c. Close all work items
# Stories: Resolved → Closed
for story_id in 106 107 108 109 110 111 112; do
  ./scripts/ado_helper.sh update $story_id "Closed"
done

# Feature: Resolved → Closed
./scripts/ado_helper.sh update 105 "Closed"

# Testing story: Active → Closed
./scripts/ado_helper.sh update <testing-story-id> "Closed"
```

**Testing Story Template:**

```markdown
Title: Test Phase {N}: {Feature Name}

Description:
## Testing Scope
- Feature ID: {feature-id}
- Stories: {story-ids}
- Branch: feature/phase{N}-{name}
- Last Commit: {commit-hash}

## Test Plan
See: docs/phase{N}-test-plan.md

## Acceptance Criteria
- [ ] All feature acceptance criteria met
- [ ] All story acceptance criteria met
- [ ] Unit tests pass (100%)
- [ ] Integration tests pass
- [ ] No regressions detected
- [ ] Linting passes
- [ ] Documentation updated

## Test Execution
{Results will be documented here}

## Sign-off
- [ ] All tests passed
- [ ] All work items commented
- [ ] All work items closed
- [ ] Ready for next feature
```

**Testing Story Acceptance Criteria:**
- [ ] Testing story created and linked to feature
- [ ] Test plan documented with clear steps
- [ ] Tests executed against specific commit hash
- [ ] Test results documented in testing story
- [ ] All related work items commented with results
- [ ] Work items moved to appropriate states (Closed or Active)

**Benefits:**
- **Audit Trail**: Clear record of when and how features were tested
- **Traceability**: Easy to see which commit was tested
- **Quality Gate**: Formal testing step before closing features
- **Team Visibility**: Everyone can see testing status and results
- **Historical Context**: Future reference for what was tested and how

---

## Rule 6: Rules Management and Synchronization

### All new rules must be committed to both the current feature branch and synchronized back to all active feature branches

**Rationale:** Rules define the team's workflow and must be consistently applied across all feature branches. When a new rule is added on any branch, it should be immediately synchronized to ensure all team members follow the same process regardless of which feature they're working on.

**Workflow:**

1. **Add new rule** to `docs/team-workflow-rules.md` on current branch
2. **Commit the rule** to current branch with clear commit message
3. **Cherry-pick to all active feature branches** to synchronize the rule
4. **Update version number** at bottom of document
5. **Notify team** of new rule via ADO comment on Epic

**Example:**

```bash
# 1. Add Rule #5 on feature/phase1-local-api
git checkout feature/phase1-local-api
# ... edit docs/team-workflow-rules.md ...
git add docs/team-workflow-rules.md
git commit -m "Add Rule #5: Feature testing workflow

- Create User Story for each feature test
- Link testing story to feature being tested
- Test against last commit from last user story
- Commit test results to same branch
- Comment all related work items with results

Related Work Item: Epic #104

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# 2. Get the commit hash
RULE_COMMIT=$(git log -1 --format='%H')

# 3. Cherry-pick to phase0 branch
git checkout feature/phase0-provider-abstraction
git cherry-pick $RULE_COMMIT

# 4. Cherry-pick to any other active branches
git checkout feature/phase2-message-queue
git cherry-pick $RULE_COMMIT

# 5. Return to original branch
git checkout feature/phase1-local-api
```

**Active Feature Branches:**
Maintain a list of currently active feature branches that need rule synchronization:
- `feature/phase0-provider-abstraction` (Phase 0)
- `feature/phase1-local-api` (Phase 1)
- `feature/phase2-message-queue` (Phase 2) [when created]
- `feature/phase3-auth-secrets` (Phase 3) [when created]
- `feature/phase4-workspace-lifecycle` (Phase 4) [when created]

**Rule Addition Checklist:**
- [ ] New rule added to team-workflow-rules.md
- [ ] Rule includes rationale, workflow, example, and benefits
- [ ] Rule committed to current branch
- [ ] Rule cherry-picked to all active feature branches
- [ ] Version number updated in document
- [ ] Team notified via ADO comment

**Version Control:**
Update the version number at the bottom of the document:
- **Major version** (X.0): Fundamental workflow changes
- **Minor version** (1.X): New rules or significant modifications
- **Patch version** (1.1.X): Clarifications or minor edits

**Conflict Resolution:**
If cherry-pick causes conflicts:
1. Review the conflict in team-workflow-rules.md
2. Keep both changes (merge sections)
3. Ensure rule numbering is sequential
4. Complete the cherry-pick: `git cherry-pick --continue`

**Benefits:**
- **Consistency**: All branches follow the same rules
- **No Confusion**: Team members see same workflow regardless of branch
- **Single Source of Truth**: Rules document stays synchronized
- **Easy Rollback**: Can revert rules across all branches if needed
- **Clear History**: Rule additions tracked in git history

---

## Rule 7: Docker-Based Testing for Features

### All feature testing must be executed in Docker containers to ensure consistent, reproducible test environments with all dependencies

**Rationale:** Local development environments vary widely (missing dependencies, version mismatches, OS differences). Docker containers provide a clean, reproducible environment that matches production, ensuring tests pass consistently across all machines and CI/CD pipelines.

**Workflow:**

1. **Create test script** that uses Docker to run tests
2. **Build test image** from existing Dockerfile (use test stage)
3. **Run tests in container** with mounted volumes for access to test results
4. **Clean up container and image** after tests complete
5. **Save test output** for documentation and troubleshooting

**Docker Test Script Pattern:**

```bash
#!/bin/bash
# Test Phase N in Docker

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "🐳 Phase N Testing in Docker"
echo ""

# 1. Build test image
echo "📦 Building test image..."
cd "$PROJECT_ROOT/api_app"
docker build --target test -t azuretre-api-test:phaseN . --quiet

# 2. Run tests in container
echo "🧪 Running tests..."
docker run --rm \
    -v "$PROJECT_ROOT:/workspace" \
    -w /api \
    azuretre-api-test:phaseN \
    bash -c "
        # Phase-specific tests here
        pytest tests_ma/ -v --tb=short
    " 2>&1 | tee /tmp/phaseN_test_output.txt

TEST_EXIT_CODE=${PIPESTATUS[0]}

# 3. Cleanup
echo "🧹 Cleaning up..."
docker rmi azuretre-api-test:phaseN --force > /dev/null 2>&1

# 4. Report results
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ Phase N tests PASSED"
    exit 0
else
    echo "❌ Phase N tests FAILED"
    exit 1
fi
```

**Example (Phase 0):**

```bash
# Create Docker test script
cat > scripts/test_phase0_docker.sh << 'EOF'
#!/bin/bash
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Build test image
cd "$PROJECT_ROOT/api_app"
docker build --target test -t azuretre-api-test:phase0 .

# Run Phase 0 specific tests
docker run --rm azuretre-api-test:phase0 bash -c "
    python -c 'from core.config import DEPLOYMENT_MODE; print(f\"✓ DEPLOYMENT_MODE={DEPLOYMENT_MODE}\")'
    python -c 'from providers.factory import get_message_bus; print(\"✓ Factory working\")'
    pytest tests_ma/ -v --tb=short
"

# Cleanup
docker rmi azuretre-api-test:phase0 --force
EOF

chmod +x scripts/test_phase0_docker.sh

# Execute tests
./scripts/test_phase0_docker.sh
```

**Benefits:**
- **Reproducibility**: Same test results on any machine
- **Clean Environment**: No dependency conflicts with local setup
- **CI/CD Ready**: Same Docker image used in automated pipelines
- **Isolation**: Tests don't affect local environment
- **Documentation**: Dockerfile documents exact dependencies needed
- **Version Control**: Test environment versioned with code

**Required Files:**
- `api_app/Dockerfile` - Must have a `test` stage
- `api_app/requirements.txt` - Production dependencies
- `api_app/requirements-dev.txt` - Test dependencies (pytest, etc.)
- `scripts/test_phase{N}_docker.sh` - Docker test runner script

**Dockerfile Test Stage Pattern:**

```dockerfile
FROM python:3.12-slim-bookworm AS base
COPY requirements.txt /.
RUN pip3 install --no-cache-dir -r requirements.txt

FROM base AS test
COPY requirements-dev.txt /.
RUN pip3 install --no-cache-dir -r requirements-dev.txt
COPY . /api
WORKDIR /api
# Test stage ready - tests run via docker run command
```

**Testing Checklist (Following Rule #5 + Rule #7):**
- [ ] Create Docker test script: `scripts/test_phase{N}_docker.sh`
- [ ] Make script executable: `chmod +x scripts/test_phase{N}_docker.sh`
- [ ] Build Docker test image from Dockerfile test stage
- [ ] Run phase-specific validation tests in container
- [ ] Run full unit test suite: `pytest tests_ma/`
- [ ] Verify all acceptance criteria met
- [ ] Save test output to file for documentation
- [ ] Clean up Docker images after testing
- [ ] Commit test scripts with test results
- [ ] Document test results in Testing User Story

**When NOT to Use Docker:**
- Quick syntax checks (use `python -m py_compile`)
- Simple file structure validation (use bash `test -f`)
- Configuration file checks (use `yq`, `jq`)
- Git operations

Use Docker only for **runtime testing** that requires dependencies, not for static validation.

**Troubleshooting:**

```bash
# If Docker build fails
docker build --target test -t azuretre-api-test:debug . --progress=plain

# If tests fail in container but pass locally
docker run -it --rm azuretre-api-test:phase0 bash
# Then debug interactively inside container

# Check container logs
docker logs <container-id>

# Clean up all test images
docker images | grep azuretre-api-test | awk '{print $3}' | xargs docker rmi -f
```

**CI/CD Integration:**
The same Docker test approach should be used in CI/CD pipelines (GitHub Actions, Azure DevOps Pipelines) to ensure test consistency:

```yaml
# Example GitHub Actions
- name: Run Phase 0 Tests
  run: ./scripts/test_phase0_docker.sh
```

---

## Workflow Checklist

### Starting a Feature
- [ ] ✅ **RULE 4:** Create new feature branch from previous feature branch
- [ ] Move feature to **Active** in Azure DevOps
- [ ] Move all stories in feature to **Active**

### Starting a Story
- [ ] Move story to **Active** in Azure DevOps
- [ ] Ensure you're on the correct feature branch
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

### After Last Story in Feature Resolved
- [ ] ✅ **RULE 3:** Move parent Feature to Resolved
- [ ] ✅ **RULE 5:** Create Testing User Story for the feature
- [ ] ✅ **RULE 5:** Link Testing Story to Feature
- [ ] ✅ **RULE 7:** Execute tests in Docker container
- [ ] ✅ **RULE 5:** If tests pass: commit results, comment all work items
- [ ] ✅ **RULE 5:** Close all Stories (Resolved → Closed)
- [ ] ✅ **RULE 5:** Close Feature (Resolved → Closed)
- [ ] ✅ **RULE 3:** Prompt user for next feature activation
- [ ] Wait for user confirmation
- [ ] ✅ **RULE 4:** Create new feature branch from current feature branch
- [ ] Activate next feature and all its stories when confirmed

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
**Version:** 1.5 - Added Rule #7 for Docker-based testing to ensure reproducible test environments