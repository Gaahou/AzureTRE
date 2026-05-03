#!/bin/bash
# Uninstall Azure setup script dependencies
# Usage: ./scripts/uninstall_requirements.sh

echo "🗑️  Uninstalling Azure SDK packages..."

pip3 uninstall -y \
    azure-mgmt-cosmosdb \
    azure-identity \
    azure-mgmt-resource \
    azure-mgmt-subscription \
    azure-mgmt-core \
    azure-common \
    msrest \
    msal \
    msal-extensions \
    azure-core \
    requests-oauthlib \
    oauthlib \
    PyJWT \
    cryptography \
    cffi \
    pycparser \
    typing-extensions

echo ""
echo "✅ Azure SDK packages uninstalled"
echo ""
echo "Note: Some shared dependencies may remain if used by other packages."
echo "To see all installed packages: pip3 list"