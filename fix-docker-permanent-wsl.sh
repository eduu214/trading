#!/bin/bash

echo "=== Fixing Docker Permanent Access for Docker Desktop + WSL2 ==="
echo ""

# Remove the old service if it exists
if [ -f /etc/systemd/system/fix-docker-sock.service ]; then
    echo "Removing old service..."
    sudo systemctl disable fix-docker-sock.service 2>/dev/null
    sudo rm /etc/systemd/system/fix-docker-sock.service
fi

echo "Creating corrected systemd service for Docker Desktop..."
sudo tee /etc/systemd/system/fix-docker-sock.service > /dev/null << 'SERVICE'
[Unit]
Description=Fix Docker Socket Permissions for Docker Desktop
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'while [ ! -S /var/run/docker.sock ]; do sleep 1; done; /bin/chmod 666 /var/run/docker.sock'
RemainAfterExit=yes
StandardOutput=journal

[Install]
WantedBy=default.target
SERVICE

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable fix-docker-sock.service
sudo systemctl start fix-docker-sock.service

echo ""
echo "✓ Service created and enabled"
echo ""

# Also add to .bashrc as backup
echo "Adding backup fix to .bashrc..."
if ! grep -q "Fix Docker socket permissions" ~/.bashrc; then
    echo '' >> ~/.bashrc
    echo '# Fix Docker socket permissions in WSL (backup)' >> ~/.bashrc
    echo 'if [ -S /var/run/docker.sock ] && [ ! -w /var/run/docker.sock ]; then' >> ~/.bashrc
    echo '    sudo chmod 666 /var/run/docker.sock 2>/dev/null' >> ~/.bashrc
    echo 'fi' >> ~/.bashrc
    echo "✓ Added to ~/.bashrc"
else
    echo "✓ Already in ~/.bashrc"
fi

echo ""
echo "Testing Docker access..."
if [ -S /var/run/docker.sock ]; then
    sudo chmod 666 /var/run/docker.sock
    if docker ps > /dev/null 2>&1; then
        echo "✓ Docker is accessible!"
    else
        echo "⚠ Docker socket exists but docker command failed"
    fi
else
    echo "⚠ Docker socket not found. Make sure Docker Desktop is running."
fi

echo ""
echo "=== Setup Complete ==="
echo "The fix will now apply automatically on WSL startup."
echo "To apply the .bashrc changes now, run: source ~/.bashrc"
