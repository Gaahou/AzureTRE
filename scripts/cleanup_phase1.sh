#!/bin/bash
# Phase 1 Cleanup Script
# Removes Azure resources and optionally cleans up local environment
#
# Usage:
#   ./scripts/cleanup_phase1.sh [--all|--azure-only|--local-only]
#
# Options:
#   --all         Clean up both Azure resources and local environment (default)
#   --azure-only  Only delete Azure resources (keep Docker containers)
#   --local-only  Only clean up local environment (keep Azure resources)

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Default: clean up both
CLEANUP_AZURE=true
CLEANUP_LOCAL=true

# Parse arguments
if [ "$1" = "--azure-only" ]; then
    CLEANUP_LOCAL=false
elif [ "$1" = "--local-only" ]; then
    CLEANUP_AZURE=false
elif [ "$1" = "--all" ]; then
    CLEANUP_AZURE=true
    CLEANUP_LOCAL=true
elif [ -n "$1" ]; then
    echo -e "${RED}Invalid option: $1${NC}"
    echo "Usage: $0 [--all|--azure-only|--local-only]"
    exit 1
fi

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Phase 1 Cleanup Script${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Show what will be cleaned up
if [ "$CLEANUP_AZURE" = true ]; then
    echo -e "${YELLOW}Will clean up:${NC}"
    echo "  • Azure Resource Group: tre-poc-rg"
    echo "  • Cosmos DB Account: tre-poc-cosmos"
    echo "  • Database and Containers"
fi

if [ "$CLEANUP_LOCAL" = true ]; then
    if [ "$CLEANUP_AZURE" = true ]; then
        echo "  • Docker containers (tre-api, tre-azurite)"
        echo "  • Docker volumes"
        echo "  • Docker network"
    else
        echo -e "${YELLOW}Will clean up:${NC}"
        echo "  • Docker containers (tre-api, tre-azurite)"
        echo "  • Docker volumes"
        echo "  • Docker network"
    fi
fi

echo ""
echo -e "${RED}⚠️  WARNING: This action cannot be undone!${NC}"
echo ""

# Confirmation prompt
read -p "Are you sure you want to continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo -e "${YELLOW}Cleanup cancelled.${NC}"
    exit 0
fi

echo ""

# Clean up Azure resources
if [ "$CLEANUP_AZURE" = true ]; then
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Cleaning up Azure Resources${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    # Check if Azure CLI or Python SDK is available
    if command -v az &> /dev/null; then
        echo "Using Azure CLI to delete resources..."

        # Check if resource group exists
        if az group show --name tre-poc-rg &> /dev/null; then
            echo "Deleting resource group 'tre-poc-rg'..."
            az group delete --name tre-poc-rg --yes --no-wait
            echo -e "${GREEN}✅ Resource group deletion initiated (running in background)${NC}"
            echo -e "${YELLOW}ℹ️  Note: Deletion may take 5-10 minutes to complete${NC}"
        else
            echo -e "${YELLOW}ℹ️  Resource group 'tre-poc-rg' not found (may already be deleted)${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Azure CLI not found${NC}"
        echo "To delete Azure resources manually:"
        echo "  1. Install Azure CLI: pip3 install azure-cli"
        echo "  2. Run: az login"
        echo "  3. Run: az group delete --name tre-poc-rg --yes"
        echo ""
        echo "Or delete via Azure Portal:"
        echo "  https://portal.azure.com → Resource Groups → tre-poc-rg → Delete"
    fi
    echo ""
fi

# Clean up local environment
if [ "$CLEANUP_LOCAL" = true ]; then
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Cleaning up Local Environment${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    # Stop and remove Docker containers
    cd "$PROJECT_ROOT/deploy/offline"

    if [ -f "docker-compose.yml" ]; then
        echo "Stopping Docker containers..."
        docker-compose down -v 2>&1 | grep -E "Stopping|Stopped|Removing|Removed|Volume" || echo "No containers to stop"
        echo -e "${GREEN}✅ Docker containers and volumes removed${NC}"
    else
        echo -e "${YELLOW}ℹ️  docker-compose.yml not found${NC}"
    fi

    # Remove orphaned containers
    if docker ps -a | grep -q "tre-cosmosdb-emulator"; then
        echo "Removing orphaned emulator container..."
        docker stop tre-cosmosdb-emulator 2>/dev/null || true
        docker rm tre-cosmosdb-emulator 2>/dev/null || true
        echo -e "${GREEN}✅ Orphaned emulator container removed${NC}"
    fi

    # Remove network if it exists
    if docker network ls | grep -q "tre-local"; then
        echo "Removing Docker network..."
        docker network rm tre-local 2>/dev/null || echo -e "${YELLOW}ℹ️  Network still in use or already removed${NC}"
    fi

    echo ""
fi

# Summary
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Cleanup Summary${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ "$CLEANUP_AZURE" = true ]; then
    echo -e "${GREEN}✅ Azure Resources:${NC}"
    echo "   - Resource group deletion initiated"
    echo "   - This will delete:"
    echo "     • Cosmos DB account (tre-poc-cosmos)"
    echo "     • Database (AzureTRE)"
    echo "     • All containers"
    echo ""
    echo -e "${YELLOW}   Note: Deletion runs in background (5-10 minutes)${NC}"
    echo ""
fi

if [ "$CLEANUP_LOCAL" = true ]; then
    echo -e "${GREEN}✅ Local Environment:${NC}"
    echo "   - Docker containers removed"
    echo "   - Docker volumes removed"
    echo "   - Docker network cleaned up"
    echo ""
fi

echo -e "${YELLOW}Files Preserved (for reference):${NC}"
echo "   - deploy/offline/.env (connection details)"
echo "   - All documentation in docs/"
echo "   - All scripts in scripts/"
echo ""
echo "To recreate the environment:"
echo "   1. Run: pip3 install -r scripts/requirements.txt"
echo "   2. Run: python3 scripts/setup_azure_simple.py"
echo "   3. Run: cd deploy/offline && docker-compose up -d"
echo ""

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Cleanup Complete${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""