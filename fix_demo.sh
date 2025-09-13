#!/bin/bash
cd /home/azureuser/bfgminer
# Add onclick to buttons
sed -i 's/class="demo-trigger"/class="demo-trigger" onclick="showDemo()"/g' templates/index.html
# Remove old script tags
sed -i '/<script src="demo_animation.js">/d' templates/index.html
sed -i '/src="demo_animation.js"/d' templates/index.html
# Add correct script tag before </body>
sed -i '/<\/body>/i <script src="/static/js/demo_animation.js"><\/script>' templates/index.html
# Restart server
pkill -f "python app_main.py" || true
sleep 2
source venv/bin/activate
nohup python app_main.py > main_server.log 2>&1 &
sleep 2
echo "Demo fixed: buttons wired, script loaded correctly. Server restarted."
grep -n "demo-trigger.*onclick" templates/index.html
grep -n "src.*demo_animation" templates/index.html
tail -n 5 main_server.log
