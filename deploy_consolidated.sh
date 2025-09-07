#!/bin/bash
echo "=== BFGMiner Consolidated Production Deployment ==="
echo "Current time: (date)"
cd /root/bfgminer_consolidation
# Install dependencies
pip install -r requirements.txt
# Create production .env from example
cp .env.example .env
# Create gunicorn.conf.py
cat > gunicorn.conf.py << "GUNI"
bind = "unix:/tmp/bfgminer.sock"
workers = 4
worker_class = "sync"
timeout = 120
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
sendfile = True
threads = 2
GUNI
# Start Gunicorn in background
gunicorn -c gunicorn.conf.py app:app > gunicorn.log 2>&1 &
GUNICORN_PID=$!
sleep 5
# Test endpoints
echo "Testing endpoints..."
curl -s -o /dev/null -w "Index: %{http_code}\n" http://localhost:5000/
curl -s -o /dev/null -w "Admin Login: %{http_code}\n" http://localhost:5000/admin/login
# Test database connectivity
sqlite3 bfgminer.db "SELECT COUNT(*) FROM users; SELECT COUNT(*) FROM admin_users;"
# Stop Gunicorn
kill $GUNICORN_PID
sleep 2
echo "Deployment test completed successfully"
