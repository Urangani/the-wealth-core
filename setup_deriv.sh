#!/bin/bash

# Deriv API Setup Script
# This script helps you configure your Deriv API credentials

echo "=== Deriv API Setup ==="
echo ""
echo "To connect to Deriv's live API, you need your own App ID and API Token."
echo "The demo App ID (1089) is rate-limited and may not work reliably."
echo ""
echo "Steps to get your credentials:"
echo "1. Go to https://deriv.com and create an account (if you don't have one)"
echo "2. Visit https://app.deriv.com/account/api-token"
echo "3. Register a new app to get your App ID"
echo "4. Create an API token with 'read' scope for market data"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
fi

echo "Current Deriv configuration in .env:"
echo "====================================="
grep -E "^DERIV_" .env
echo ""
echo "If you do not yet have an API token, the service can still connect to public Deriv market data without auth."
echo "Set DERIV_WS_URL=wss://api.derivws.com/trading/v1/options/ws/public and leave DERIV_API_TOKEN empty."
echo ""
read -p "Do you have your Deriv App ID and API Token? (y/n): " has_credentials

if [ "$has_credentials" = "y" ] || [ "$has_credentials" = "Y" ]; then
    read -p "Enter your Deriv App ID: " app_id
    read -p "Enter your Deriv API Token: " api_token

    # Update .env file
    sed -i "s/DERIV_APP_ID=.*/DERIV_APP_ID=$app_id/" .env
    sed -i "s/DERIV_WS_URL=.*/DERIV_WS_URL=wss:\/\/ws.derivws.com\/websockets\/v3?app_id=$app_id/" .env
    sed -i "s/DERIV_API_TOKEN=.*/DERIV_API_TOKEN=$api_token/" .env

    echo ""
    echo "✅ Credentials updated in .env file"
    echo ""
    echo "Testing connection..."
    echo "======================"

    # Restart services to pick up new config
    docker compose down
    docker compose up -d --build

    # Wait for services to start
    echo "Waiting for services to start..."
    sleep 10

    # Check status
    echo "Market service status:"
    curl -s http://localhost:8001/market/status | python3 -m json.tool

else
    echo ""
    echo "Please get your credentials from https://app.deriv.com/account/api-token"
    echo "Then run this script again or manually update the .env file."
    echo ""
    echo "For now, the system will use the demo App ID (1089) which may be rate-limited."
fi

echo ""
echo "To check the connection later, run:"
echo "curl http://localhost:8001/market/status"