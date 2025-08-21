#!/bin/bash
# Quick script to install missing dependencies in running container

echo "🔧 Installing missing dependencies in running container..."

# Install yfinance (lightweight, quick install)
echo "📦 Installing yfinance..."
docker-compose exec -T backend pip install yfinance==0.2.28

# Try to install vectorbt (may take time)
echo "📦 Installing vectorbt..."
docker-compose exec -T backend pip install vectorbt==0.26.2

# Try to install ta-lib (may fail without system dependencies)
echo "📦 Installing ta-lib..."
docker-compose exec -T backend pip install TA-Lib==0.4.28 || echo "⚠️ TA-Lib installation failed (need system deps)"

echo "✅ Dependencies installation complete!"