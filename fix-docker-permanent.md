# Permanent Docker Permission Fix for WSL2

## Option 1: Add to .bashrc or .zshrc (Easiest)
Add this line to your shell startup file to fix permissions on each login:

```bash
# Add to ~/.bashrc or ~/.zshrc
echo 'sudo chmod 666 /var/run/docker.sock 2>/dev/null' >> ~/.bashrc
```

Note: You'll be prompted for sudo password once per session.

## Option 2: Create a systemd service (Most Reliable)
Since WSL2 supports systemd, create a service to fix permissions on boot:

1. Create the service file:
```bash
sudo tee /etc/systemd/system/fix-docker-sock.service << 'EOF'
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
EOF
```

2. Enable the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable fix-docker-sock.service
sudo systemctl start fix-docker-sock.service
```

## Option 3: Configure Docker daemon (Cleanest)
Create a Docker daemon configuration to set proper group permissions:

1. Create Docker daemon config:
```bash
sudo tee /etc/docker/daemon.json << 'EOF'
{
  "hosts": ["unix:///var/run/docker.sock"],
  "group": "docker"
}
EOF
```

2. Ensure your user is in the docker group:
```bash
sudo usermod -aG docker $USER
```

3. Restart Docker and WSL:
```bash
# In WSL:
sudo service docker restart

# In PowerShell (as admin):
wsl --shutdown
# Then restart WSL
```

## Option 4: Use Docker Desktop WSL Integration (Recommended)
This is the official method:

1. Open Docker Desktop
2. Go to Settings → Resources → WSL Integration
3. Enable integration with your distro
4. Apply & Restart

Then in WSL:
```bash
# Add this to ~/.bashrc to ensure proper group membership
if ! groups | grep -q docker; then
    newgrp docker
fi
```

## Quick Test
After applying any method, test with:
```bash
docker ps
```

## Current Status
Currently using temporary fix: `sudo chmod 666 /var/run/docker.sock`
This resets when Docker restarts.