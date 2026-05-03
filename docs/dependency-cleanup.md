# Python Dependencies Cleanup Guide

## Quick Commands

### Cleanup (Remove All Dependencies)

Remove all Python dependencies and restore to clean base state:

```bash
./scripts/cleanup_all_dependencies.sh
```

This will:
1. Remove ALL installed packages (except pip, setuptools, wheel)
2. Restore base packages to exact versions:
   - pip 21.2.4
   - setuptools 58.0.4
   - wheel 0.37.0

### Install (Reinstall All Dependencies)

Install all project dependencies in one go:

```bash
./scripts/install_all_dependencies.sh
```

This provides interactive options:
1. **All dependencies** (API + Dev/Test + Resource Processor)
2. **API dependencies only** (production)
3. **API + Dev/Test dependencies**
4. **Resource Processor dependencies only**
5. **Custom selection**

Features:
- ✅ Virtual environment check
- ✅ Requirements file validation
- ✅ Interactive installation options
- ✅ Verification tests after installation
- ✅ Final package summary

## Safety Features

- **Virtual Environment Check**: Warns if not in a virtual environment
- **Confirmation Prompts**: Requires explicit "yes" to proceed
- **Package List Display**: Shows what will be removed before proceeding
- **Verification**: Displays final package list to confirm cleanup

## Reinstalling Dependencies

### Option 1: Interactive Installer (Recommended)

```bash
./scripts/install_all_dependencies.sh
```

Choose from menu what to install.

### Option 2: Manual Installation

Install specific components as needed:

```bash
# API dependencies
pip install -r api_app/requirements.txt

# Resource Processor dependencies
pip install -r resource_processor/local_runner/requirements.txt

# Development/Testing dependencies
pip install -r api_app/requirements-dev.txt
```

## Component-Specific Cleanup

### API Dependencies Only
```bash
./api_app/cleanup_dependencies.sh
```

Removes:
- `aio-pika` (RabbitMQ client)
- `aiormq` (dependency)
- `pamqp` (dependency)

### Resource Processor (Docker-based)
```bash
docker stop tre-resource-processor
docker rm tre-resource-processor
docker rmi tre-resource-processor:local
```

All Python dependencies are removed with the container.

### Phase-Specific Cleanup

```bash
# Phase 2: Message Queue
./scripts/cleanup_phase2.sh

# Phase 3: Auth & Secrets
./scripts/cleanup_phase3.sh

# Phase 4: Workspace Lifecycle
./scripts/cleanup_phase4.sh
```

## Best Practices

### Use Virtual Environments

Always work in a virtual environment:

```bash
# Create virtual environment
python3 -m venv .venv

# Activate (Linux/Mac)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate

# Verify
which python
# Should show: .venv/bin/python
```

### Before Cleanup

1. **Deactivate any running services**:
   ```bash
   cd deploy/offline
   docker-compose down
   ```

2. **Save your work**:
   ```bash
   git status
   git add .
   git commit -m "Save work before cleanup"
   ```

3. **Document installed packages** (optional):
   ```bash
   pip list > packages_before_cleanup.txt
   pip freeze > requirements_before_cleanup.txt
   ```

### After Cleanup

1. **Verify base packages**:
   ```bash
   pip list
   # Should show only:
   # Package    Version
   # ---------- -------
   # pip        21.2.4
   # setuptools 58.0.4
   # wheel      0.37.0
   ```

2. **Reinstall dependencies**:
   ```bash
   pip install -r api_app/requirements.txt
   ```

3. **Test installation**:
   ```bash
   python -c "from core.config import DEPLOYMENT_MODE; print(f'DEPLOYMENT_MODE={DEPLOYMENT_MODE}')"
   ```

## Troubleshooting

### "Permission denied" error
```bash
chmod +x scripts/cleanup_all_dependencies.sh
```

### "No module named 'pip'" after cleanup
```bash
python -m ensurepip --upgrade
python -m pip install --upgrade pip==21.2.4
```

### Packages not removing cleanly
```bash
# Force removal
pip freeze | xargs pip uninstall -y

# Then restore base packages
pip install pip==21.2.4 setuptools==58.0.4 wheel==0.37.0
```

### Docker containers still running
```bash
cd deploy/offline
docker-compose down -v  # Remove volumes too
docker system prune -a  # Remove all unused containers/images
```

## Dependency Management Rules

Following **Rule #8** from team workflow:

1. ✅ **Pin versions** in requirements.txt (e.g., `aio-pika==9.4.3`)
2. ✅ **Provide cleanup scripts** when adding dependencies
3. ✅ **Document changes** in commit messages
4. ✅ **Test cleanup scripts** before committing
5. ✅ **Commit requirements and cleanup together**

## File Structure

```
AzureTRE/
├── scripts/
│   ├── cleanup_all_dependencies.sh       # Master cleanup script
│   ├── install_all_dependencies.sh       # Master install script
│   ├── cleanup_phase2.sh                 # Phase 2 specific
│   ├── cleanup_phase3.sh                 # Phase 3 specific
│   └── cleanup_phase4.sh                 # Phase 4 specific
├── api_app/
│   ├── requirements.txt                  # API dependencies
│   ├── requirements-dev.txt              # Dev/test dependencies
│   └── cleanup_dependencies.sh           # API cleanup
└── resource_processor/
    └── local_runner/
        ├── requirements.txt              # Processor dependencies
        └── cleanup.sh                    # Processor cleanup (Docker)
```

## Related Documentation

- [Team Workflow Rules](./team-workflow-rules.md) - Rule #8: Dependency Management
- [Quick Start Guide](../QUICK_START.md) - Setup and installation
- [Local TRE Status](../LOCAL_TRE_STATUS.md) - Service overview

---

**Last Updated:** 2026-05-03  
**Version:** 1.0
