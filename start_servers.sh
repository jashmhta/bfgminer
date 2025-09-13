
#!/bin/bash
cd /home/azureuser/bfgminer
source venv/bin/activate
rm -f main_server.log admin_server.log
nohup python app_main.py > main_server.log 2>&1 &
MAIN_PID=$!
sleep 2
nohup python app_admin.py > admin_server.log 2>&1 &
ADMIN_PID=$!
echo "Main server PID: $MAIN_PID"
echo "Admin server PID: $ADMIN_PID"
