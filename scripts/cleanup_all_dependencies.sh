#!/bin/bash
# Master Cleanup Script - Remove All Python Dependencies
# Restores Python environment to clean state with only base packages

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "╔════════════════════════════════════════════════════╗"
echo "║     Master Python Dependencies Cleanup             ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""

# Check for virtual environment
if [[ -z "${VIRTUAL_ENV}" ]]; then
    echo "⚠️  WARNING: No virtual environment detected!"
    echo "This will clean ALL packages in your system Python installation."
    read -p "Are you SURE you want to continue? (yes/NO): " -r
    echo
    [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]] && echo "Aborted." && exit 1
fi

echo "🔍 Current Python environment: ${VIRTUAL_ENV:-system}"
echo ""

# Display current packages
echo "📦 Current installed packages:"
pip list
echo ""

read -p "Remove ALL packages except pip/setuptools/wheel? (yes/NO): " -r
echo
[[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]] && echo "Aborted." && exit 1

echo ""
echo "🧹 Removing all packages..."
echo ""

# Get list of all installed packages except pip, setuptools, wheel
PACKAGES=$(pip list --format=freeze | grep -v "^pip==" | grep -v "^setuptools==" | grep -v "^wheel==" | cut -d'=' -f1)

if [[ -z "$PACKAGES" ]]; then
    echo "✅ No packages to remove (only base packages installed)"
else
    echo "Packages to remove:"
    echo "$PACKAGES"
    echo ""

    # Uninstall all packages
    echo "$PACKAGES" | xargs pip uninstall -y

    echo ""
    echo "✅ All packages removed"
fi

echo ""
echo "🔧 Restoring base packages to specific versions..."
echo ""

# Upgrade/downgrade to exact versions
pip install --upgrade pip==21.2.4
pip install --upgrade setuptools==58.0.4
pip install --upgrade wheel==0.37.0

echo ""
echo "✅ Base packages restored"
echo ""

# Display final state
echo "📦 Final package list:"
pip list
echo ""

# Verify exact versions
EXPECTED="pip==21.2.4 setuptools==58.0.4 wheel==0.37.0"
ACTUAL=$(pip list --format=freeze | grep -E "^(pip|setuptools|wheel)==")

echo "Expected packages:"
echo "  pip        21.2.4"
echo "  setuptools 58.0.4"
echo "  wheel      0.37.0"
echo ""

echo "Actual packages:"
pip list | grep -E "^(pip|setuptools|wheel)\s"
echo ""

echo "╔════════════════════════════════════════════════════╗"
echo "║              Cleanup Complete ✅                    ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""
echo "Your Python environment now has only base packages."
echo ""
echo "To reinstall project dependencies:"
echo "  API:                pip install -r api_app/requirements.txt"
echo "  Resource Processor: pip install -r resource_processor/local_runner/requirements.txt"
echo "  Dev/Test:           pip install -r api_app/requirements-dev.txt"
echo ""