#!/bin/bash

echo "=== Setting up permanent Docker fix for WSL2 ==="
echo ""
echo "Choose your preferred method:"
echo "1. Add to .bashrc (simplest, requires sudo password each session)"
echo "2. Create systemd service (automatic, no password needed after setup)"
echo "3. Just show me the options"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo "Adding Docker fix to .bashrc..."
        echo '# Fix Docker socket permissions in WSL' >> ~/.bashrc
        echo 'if [ -S /var/run/docker.sock ]; then' >> ~/.bashrc
        echo '    sudo chmod 666 /var/run/docker.sock 2>/dev/null' >> ~/.bashrc
        echo 'fi' >> ~/.bashrc
        echo ""
        echo "✓ Added to ~/.bashrc"
        echo "The fix will apply on your next login."
        echo "To apply now, run: source ~/.bashrc"
        ;;
    2)
        echo "Creating systemd service..."
        echo "You'll need to enter your sudo password:"
        
        sudo tee /etc/systemd/system/fix-docker-sock.service > /dev/null << 'SERVICE'
[Unit]
Description=Fix Docker Socket Permissions
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
ExecStart=/bin/chmod 666 /var/run/docker.sock
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
SERVICE
        
        sudo systemctl daemon-reload
        sudo systemctl enable fix-docker-sock.service
        sudo systemctl start fix-docker-sock.service
        
        echo ""
        echo "✓ Systemd service created and enabled"
        echo "Docker permissions will be fixed automatically on boot"
        ;;
    3)
        echo "See fix-docker-permanent.md for all options"
        ;;
    *)
        echo "Invalid choice"
        ;;
esac

echo ""
echo "Testing Docker access..."
if docker ps > /dev/null 2>&1; then
    echo "✓ Docker is accessible!"
else
    echo "✗ Docker test failed. You may need to restart WSL."
fi
