#!/bin/bash

echo "=== Enabling Docker Access in WSL2 ==="
echo ""

# Try to fix Docker socket permissions temporarily
echo "Attempting to fix Docker socket permissions..."
echo "You will be prompted for your sudo password:"
echo ""

# Method 1: Change socket permissions (temporary fix)
sudo chmod 666 /var/run/docker.sock

echo ""
echo "Testing Docker access..."
if docker ps &>/dev/null; then
    echo "✓ Docker is now accessible!"
    echo ""
    echo "Running containers:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
else
    echo "✗ Docker is still not accessible"
    echo ""
    echo "Please try the following:"
    echo ""
    echo "1. Make sure Docker Desktop is running on Windows"
    echo "2. In Docker Desktop, go to Settings > Resources > WSL Integration"
    echo "3. Enable integration with your distro"
    echo "4. Apply & Restart Docker Desktop"
    echo "5. In PowerShell (as admin), run: wsl --shutdown"
    echo "6. Restart WSL and try again"
fi

echo ""
echo "Note: The chmod 666 fix is temporary and will reset when Docker restarts."
echo "For a permanent fix, ensure Docker Desktop WSL integration is properly configured."
