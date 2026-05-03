#!/bin/bash
# Phase 2 Cleanup Script
# Removes all Phase 2 components (RabbitMQ message queue infrastructure)

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         Phase 2 Cleanup: Local Message Queue              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Function to prompt for confirmation
confirm() {
    local prompt="$1"
    read -p "$prompt (y/N): " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]]
}

echo "This script will remove:"
echo "  • RabbitMQ container and volumes"
echo "  • Resource processor container and image"
echo "  • Python dependencies (aio-pika)"
echo ""

if ! confirm "Continue with cleanup?"; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "─────────────────────────────────────────────────────────────"
echo "1. Stopping Docker Compose services..."
echo "─────────────────────────────────────────────────────────────"

cd "$PROJECT_ROOT/deploy/offline"

# Stop all services
if docker-compose ps | grep -q "Up"; then
    docker-compose down || echo "  ⚠️  Failed to stop services (may already be stopped)"
else
    echo "  ℹ️  Services already stopped"
fi

echo ""
echo "─────────────────────────────────────────────────────────────"
echo "2. Removing RabbitMQ volume..."
echo "─────────────────────────────────────────────────────────────"

if docker volume ls | grep -q "tre-rabbitmq-data"; then
    docker volume rm tre-rabbitmq-data || echo "  ⚠️  Volume in use or already removed"
    echo "  ✅ RabbitMQ volume removed"
else
    echo "  ℹ️  RabbitMQ volume not found"
fi

echo ""
echo "─────────────────────────────────────────────────────────────"
echo "3. Removing resource processor..."
echo "─────────────────────────────────────────────────────────────"

# Run resource processor cleanup script
if [ -f "$PROJECT_ROOT/resource_processor/local_runner/cleanup.sh" ]; then
    bash "$PROJECT_ROOT/resource_processor/local_runner/cleanup.sh"
else
    echo "  ℹ️  Resource processor cleanup script not found"
fi

echo ""
echo "─────────────────────────────────────────────────────────────"
echo "4. Removing RabbitMQ images..."
echo "─────────────────────────────────────────────────────────────"

if docker images | grep -q "rabbitmq.*3-management"; then
    docker images | grep "rabbitmq.*3-management" | awk '{print $3}' | xargs docker rmi -f || echo "  ⚠️  Some images could not be removed"
    echo "  ✅ RabbitMQ images removed"
else
    echo "  ℹ️  No RabbitMQ images found"
fi

echo ""
echo "─────────────────────────────────────────────────────────────"
echo "5. Python dependencies (optional)..."
echo "─────────────────────────────────────────────────────────────"

if confirm "Remove Python dependencies (aio-pika)?"; then
    if [ -f "$PROJECT_ROOT/api_app/cleanup_dependencies.sh" ]; then
        bash "$PROJECT_ROOT/api_app/cleanup_dependencies.sh"
    else
        echo "  ⚠️  API cleanup script not found"
    fi
else
    echo "  ℹ️  Skipped Python dependencies cleanup"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                   Cleanup Complete! ✅                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Phase 2 components have been removed."
echo ""
echo "To restore Phase 2:"
echo "  1. Ensure docker-compose.yml includes RabbitMQ and resource processor"
echo "  2. cd deploy/offline && docker-compose up -d"
echo "  3. pip install -r api_app/requirements.txt (if dependencies removed)"
echo ""