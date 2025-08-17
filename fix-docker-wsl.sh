#!/bin/bash

# Script to fix Docker access in WSL2

echo "=== Fixing Docker Access in WSL2 ==="
echo ""
echo "This script will help you fix Docker access issues in WSL."
echo ""

# Check if user is in docker group
if groups $USER | grep -q '\bdocker\b'; then
    echo "✓ User '$USER' is already in the docker group"
else
    echo "✗ User '$USER' is NOT in the docker group"
    echo ""
    echo "To fix this, run the following command:"
    echo ""
    echo "  sudo usermod -aG docker $USER"
    echo ""
    echo "Then, you need to either:"
    echo "  1. Log out and log back in, OR"
    echo "  2. Run: newgrp docker"
    echo ""
fi

# Check Docker socket
echo "Checking Docker socket..."
if [ -S /var/run/docker.sock ]; then
    echo "✓ Docker socket exists"
    ls -la /var/run/docker.sock
else
    echo "✗ Docker socket not found"
    echo ""
    echo "Make sure Docker Desktop is running and WSL integration is enabled:"
    echo "  1. Open Docker Desktop"
    echo "  2. Go to Settings > Resources > WSL Integration"
    echo "  3. Enable integration with your WSL distro"
    echo "  4. Click 'Apply & Restart'"
fi

echo ""
echo "Testing Docker access..."
if docker version &>/dev/null; then
    echo "✓ Docker is accessible!"
    echo ""
    docker version --format 'Docker version {{.Server.Version}}'
else
    echo "✗ Cannot access Docker"
    echo ""
    echo "If you just added yourself to the docker group, try:"
    echo "  newgrp docker"
    echo ""
    echo "Or restart your WSL session:"
    echo "  1. Exit WSL"
    echo "  2. In PowerShell run: wsl --shutdown"
    echo "  3. Start WSL again"
fi

echo ""
echo "=== Docker Access Check Complete ==="
