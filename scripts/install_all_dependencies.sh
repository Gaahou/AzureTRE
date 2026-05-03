#!/bin/bash
# Master Install Script - Install All Python Dependencies
# Installs all project dependencies in one go

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "╔════════════════════════════════════════════════════╗"
echo "║     Master Python Dependencies Installer           ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""

# Check for virtual environment
if [[ -z "${VIRTUAL_ENV}" ]]; then
    echo "⚠️  WARNING: No virtual environment detected!"
    echo "It's recommended to use a virtual environment."
    read -p "Continue anyway? (y/N): " -r
    echo
    [[ ! $REPLY =~ ^[Yy]$ ]] && echo "Aborted." && exit 1
fi

echo "🔍 Current Python environment: ${VIRTUAL_ENV:-system}"
echo "🐍 Python version: $(python --version)"
echo ""

# Display current packages
echo "📦 Currently installed packages:"
pip list
echo ""

# Check if requirements files exist
echo "🔍 Checking requirements files..."
echo ""

REQUIREMENTS_FILES=(
    "api_app/requirements.txt"
    "api_app/requirements-dev.txt"
    "resource_processor/local_runner/requirements.txt"
)

MISSING_FILES=()
for req_file in "${REQUIREMENTS_FILES[@]}"; do
    if [[ -f "$PROJECT_ROOT/$req_file" ]]; then
        echo "  ✅ Found: $req_file"
    else
        echo "  ❌ Missing: $req_file"
        MISSING_FILES+=("$req_file")
    fi
done

echo ""

if [[ ${#MISSING_FILES[@]} -gt 0 ]]; then
    echo "⚠️  Some requirements files are missing!"
    read -p "Continue with available files? (y/N): " -r
    echo
    [[ ! $REPLY =~ ^[Yy]$ ]] && echo "Aborted." && exit 1
fi

echo "╔════════════════════════════════════════════════════╗"
echo "║          Installation Options                      ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""
echo "What would you like to install?"
echo ""
echo "  1) All dependencies (API + Dev/Test + Resource Processor)"
echo "  2) API dependencies only (production)"
echo "  3) API + Dev/Test dependencies"
echo "  4) Resource Processor dependencies only"
echo "  5) Custom selection"
echo ""
read -p "Enter choice [1-5] (default: 1): " choice
choice=${choice:-1}

echo ""

install_api=false
install_dev=false
install_processor=false

case $choice in
    1)
        echo "📦 Installing ALL dependencies..."
        install_api=true
        install_dev=true
        install_processor=true
        ;;
    2)
        echo "📦 Installing API dependencies only..."
        install_api=true
        ;;
    3)
        echo "📦 Installing API + Dev/Test dependencies..."
        install_api=true
        install_dev=true
        ;;
    4)
        echo "📦 Installing Resource Processor dependencies only..."
        install_processor=true
        ;;
    5)
        echo "Custom selection:"
        read -p "  Install API dependencies? (y/N): " -r
        [[ $REPLY =~ ^[Yy]$ ]] && install_api=true

        read -p "  Install Dev/Test dependencies? (y/N): " -r
        [[ $REPLY =~ ^[Yy]$ ]] && install_dev=true

        read -p "  Install Resource Processor dependencies? (y/N): " -r
        [[ $REPLY =~ ^[Yy]$ ]] && install_processor=true
        ;;
    *)
        echo "❌ Invalid choice. Aborted."
        exit 1
        ;;
esac

echo ""
echo "╔════════════════════════════════════════════════════╗"
echo "║          Starting Installation                     ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""

# Install API dependencies
if $install_api && [[ -f "$PROJECT_ROOT/api_app/requirements.txt" ]]; then
    echo "📦 Installing API dependencies..."
    pip install -r "$PROJECT_ROOT/api_app/requirements.txt"
    echo "✅ API dependencies installed"
    echo ""
fi

# Install Dev/Test dependencies
if $install_dev && [[ -f "$PROJECT_ROOT/api_app/requirements-dev.txt" ]]; then
    echo "📦 Installing Dev/Test dependencies..."
    pip install -r "$PROJECT_ROOT/api_app/requirements-dev.txt"
    echo "✅ Dev/Test dependencies installed"
    echo ""
fi

# Install Resource Processor dependencies
if $install_processor && [[ -f "$PROJECT_ROOT/resource_processor/local_runner/requirements.txt" ]]; then
    echo "📦 Installing Resource Processor dependencies..."
    pip install -r "$PROJECT_ROOT/resource_processor/local_runner/requirements.txt"
    echo "✅ Resource Processor dependencies installed"
    echo ""
fi

echo "╔════════════════════════════════════════════════════╗"
echo "║          Installation Complete ✅                   ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""

# Display final package list
echo "📦 Final installed packages:"
pip list
echo ""

# Summary
echo "📊 Installation Summary:"
echo ""
if $install_api; then
    echo "  ✅ API dependencies installed"
fi
if $install_dev; then
    echo "  ✅ Dev/Test dependencies installed"
fi
if $install_processor; then
    echo "  ✅ Resource Processor dependencies installed"
fi
echo ""

# Verification tests
echo "🧪 Running verification tests..."
echo ""

if $install_api; then
    echo "  Testing API imports..."
    if python -c "from core.config import DEPLOYMENT_MODE; print(f'  ✅ DEPLOYMENT_MODE={DEPLOYMENT_MODE}')" 2>/dev/null; then
        true
    else
        echo "  ⚠️  API import test failed"
    fi

    if python -c "from azure.cosmos import CosmosClient; print('  ✅ Azure Cosmos SDK loaded')" 2>/dev/null; then
        true
    else
        echo "  ⚠️  Azure Cosmos SDK import failed"
    fi
fi

if $install_dev; then
    echo "  Testing Dev/Test tools..."
    if python -c "import pytest; print(f'  ✅ pytest {pytest.__version__} loaded')" 2>/dev/null; then
        true
    else
        echo "  ⚠️  pytest import failed"
    fi
fi

if $install_processor; then
    echo "  Testing Resource Processor imports..."
    if python -c "import aio_pika; print('  ✅ aio-pika loaded')" 2>/dev/null; then
        true
    else
        echo "  ⚠️  aio-pika import failed"
    fi
fi

echo ""
echo "╔════════════════════════════════════════════════════╗"
echo "║              Ready to Use ✅                        ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""
echo "Your Python environment is now ready for development."
echo ""
echo "Next steps:"
echo "  • Start services: cd deploy/offline && docker-compose up -d"
echo "  • Run tests: pytest api_app/tests_ma/"
echo "  • Check API: curl http://localhost:8000/api/health"
echo ""