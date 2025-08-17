#!/bin/bash

echo "Uninstalling Docker from WSL2/Ubuntu..."

# Stop Docker service if running
sudo service docker stop 2>/dev/null || true

# Remove Docker packages
sudo apt-get purge -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin docker-ce-rootless-extras

# Remove Docker GPG key and repository
sudo rm -f /etc/apt/keyrings/docker.gpg
sudo rm -f /etc/apt/sources.list.d/docker.list

# Remove Docker data and config
sudo rm -rf /var/lib/docker
sudo rm -rf /var/lib/containerd
sudo rm -rf /etc/docker

# Remove Docker group
sudo groupdel docker 2>/dev/null || true

# Clean up apt
sudo apt-get autoremove -y
sudo apt-get autoclean

echo ""
echo "Docker has been uninstalled from WSL2/Ubuntu."
echo ""
echo "Next steps:"
echo "1. Install Docker Desktop for Windows from: https://www.docker.com/products/docker-desktop/"
echo "2. Docker Desktop will automatically integrate with WSL2"
echo "3. After installation, restart your WSL terminal"
echo "4. Test with: docker --version"