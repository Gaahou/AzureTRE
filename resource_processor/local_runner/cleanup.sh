#!/bin/bash
# Cleanup script for local resource processor
# This script stops and removes the resource processor container and cleans up Porter installations

set -e

echo "🧹 Cleaning up local resource processor..."

# Stop and remove the resource processor container if running
if docker ps -a --format '{{.Names}}' | grep -q '^tre-resource-processor$'; then
    echo "📦 Stopping and removing tre-resource-processor container..."
    docker stop tre-resource-processor || true
    docker rm tre-resource-processor || true
    echo "✅ Container removed"
else
    echo "ℹ️  No tre-resource-processor container found"
fi

# Remove the resource processor image if it exists
if docker images --format '{{.Repository}}:{{.Tag}}' | grep -q '^tre-resource-processor:local$'; then
    echo "🗑️  Removing tre-resource-processor:local image..."
    docker rmi tre-resource-processor:local || true
    echo "✅ Image removed"
else
    echo "ℹ️  No tre-resource-processor:local image found"
fi

# Clean up Porter bundles installed in the container
# Note: Porter bundles are installed inside the container, so removing the container cleans them up

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "To restart the resource processor, use docker-compose:"
echo "  cd deploy/offline && docker-compose up -d tre-resource-processor"