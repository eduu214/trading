#!/bin/bash

echo "🐳 AlphaStrat Docker Setup for macOS"
echo "===================================="
echo ""

# Check if Docker is already installed
if command -v docker &> /dev/null; then
    echo "✅ Docker is already installed!"
    docker --version
else
    echo "📦 Installing Docker Desktop..."
    
    # Try to install via Homebrew
    if command -v brew &> /dev/null; then
        echo "Using Homebrew to install Docker Desktop..."
        brew install --cask docker
        
        if [ $? -eq 0 ]; then
            echo "✅ Docker Desktop installed successfully!"
        else
            echo "⚠️  Homebrew installation failed. Please try manual installation:"
            echo "1. Download Docker Desktop from: https://www.docker.com/products/docker-desktop/"
            echo "2. Open the downloaded .dmg file"
            echo "3. Drag Docker to Applications folder"
            echo "4. Launch Docker from Applications"
            exit 1
        fi
    else
        echo "⚠️  Homebrew not found. Please install Docker Desktop manually:"
        echo "1. Download from: https://www.docker.com/products/docker-desktop/"
        echo "2. Open the downloaded .dmg file"
        echo "3. Drag Docker to Applications folder"
        echo "4. Launch Docker from Applications"
        exit 1
    fi
fi

# Open Docker Desktop
echo ""
echo "🚀 Opening Docker Desktop..."
open -a Docker

echo ""
echo "⏳ Waiting for Docker to start (this may take a minute)..."
echo "   Docker Desktop needs to be running before we can continue."
echo ""

# Wait for Docker to be ready
max_attempts=30
attempt=0
while ! docker system info &>/dev/null; do
    attempt=$((attempt+1))
    if [ $attempt -eq $max_attempts ]; then
        echo "❌ Docker Desktop is taking too long to start."
        echo "   Please ensure Docker Desktop is running and try again."
        exit 1
    fi
    echo -n "."
    sleep 2
done

echo ""
echo "✅ Docker is running!"
echo ""

# Verify Docker Compose
if docker compose version &>/dev/null; then
    echo "✅ Docker Compose is available!"
    docker compose version
else
    echo "❌ Docker Compose not found. It should be included with Docker Desktop."
    exit 1
fi

echo ""
echo "🎉 Docker setup complete!"
echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env and add your API keys"
echo "2. Run: docker compose up"
echo ""