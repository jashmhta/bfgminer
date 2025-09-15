#!/bin/bash

# BFGMiner Enterprise Deployment Script
# This script sets up the BFGMiner application with Gunicorn and Nginx

set -e  # Exit on error

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root or with sudo"
  exit 1
fi

# Configuration
APP_DIR="/opt/bfgminer"
USER="www-data"
GROUP="www-data"
PYTHON_VERSION="3.11"

echo "=== BFGMiner Enterprise Deployment ==="
echo "Installing to: $APP_DIR"

# Install dependencies
echo "Installing dependencies..."
apt-get update
apt-get install -y python3 python3-pip python3-venv nginx supervisor

# Create app directory if it doesn't exist
if [ ! -d "$APP_DIR" ]; then
  mkdir -p "$APP_DIR"
fi

# Copy application files
echo "Copying application files..."
cp -r . "$APP_DIR"

# Set permissions
echo "Setting permissions..."
chown -R "$USER:$GROUP" "$APP_DIR"
chmod -R 755 "$APP_DIR"

# Create virtual environment
echo "Creating virtual environment..."
cd "$APP_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# Configure Nginx
echo "Configuring Nginx..."
cp "$APP_DIR/deployment/nginx.conf" /etc/nginx/sites-available/bfgminer
ln -sf /etc/nginx/sites-available/bfgminer /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default  # Remove default site

# Update Nginx configuration paths
sed -i "s|/path/to/bfgminer|$APP_DIR|g" /etc/nginx/sites-available/bfgminer

# Configure systemd services
echo "Configuring systemd services..."
cp "$APP_DIR/systemd/bfgminer-main.service" /etc/systemd/system/
cp "$APP_DIR/systemd/bfgminer-admin.service" /etc/systemd/system/

# Update systemd service paths
sed -i "s|%h/bfgminer|$APP_DIR|g" /etc/systemd/system/bfgminer-main.service
sed -i "s|%h/bfgminer|$APP_DIR|g" /etc/systemd/system/bfgminer-admin.service

# Reload systemd
systemctl daemon-reload

# Start services
echo "Starting services..."
systemctl enable bfgminer-main
systemctl enable bfgminer-admin
systemctl restart bfgminer-main
systemctl restart bfgminer-admin
systemctl restart nginx

# Open firewall port 80
echo "Configuring firewall..."
if command -v ufw &> /dev/null; then
    ufw allow 80/tcp
    echo "UFW: Port 80 opened"
elif command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-port=80/tcp
    firewall-cmd --reload
    echo "FirewallD: Port 80 opened"
else
    echo "No firewall detected, please manually open port 80 if needed"
fi

echo "=== Deployment Complete ==="
echo "Main application: http://your-server-ip/"
echo "Admin dashboard: http://your-server-ip/admin/"
echo ""
echo "Check status with:"
echo "  systemctl status bfgminer-main"
echo "  systemctl status bfgminer-admin"
echo "  systemctl status nginx"
echo ""
echo "View logs with:"
echo "  journalctl -u bfgminer-main"
echo "  journalctl -u bfgminer-admin"