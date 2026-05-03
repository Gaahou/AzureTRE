#!/bin/bash
# Cleanup script for API dependencies
# This script uninstalls Python packages added for Phase 2 (RabbitMQ support)

set -e

echo "🧹 Cleaning up Phase 2 API dependencies..."
echo ""

# Check if we're in a virtual environment
if [[ -z "${VIRTUAL_ENV}" ]]; then
    echo "⚠️  WARNING: No virtual environment detected!"
    echo "It's recommended to run this in a virtual environment to avoid affecting system Python."
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

echo "📦 Uninstalling aio-pika and dependencies..."

# Uninstall aio-pika (added in Story 120)
pip uninstall -y aio-pika || echo "  aio-pika not installed"

# Uninstall aio-pika dependencies (if not used by other packages)
echo ""
echo "Checking for orphaned dependencies..."
pip uninstall -y aiormq || echo "  aiormq not installed or used by other packages"
pip uninstall -y pamqp || echo "  pamqp not installed or used by other packages"

echo ""
echo "✅ Phase 2 dependencies removed"
echo ""
echo "To reinstall, run:"
echo "  pip install -r requirements.txt"
echo ""
echo "To rebuild API container:"
echo "  cd deploy/offline && docker-compose build tre-api"