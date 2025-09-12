#!/bin/bash

# BFGMiner Complete Application Startup Script

echo "🚀 Starting BFGMiner Complete Application Suite..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip3."
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

# Initialize database
echo "🗄️ Initializing database..."
python3 -c "from app import init_db; init_db()"

# Start main application (port 5001)
echo "🌐 Starting main BFGMiner application on port 5001..."
python3 app.py &
MAIN_PID=$!

# Wait a moment for main app to start
sleep 3

# Start admin dashboard (port 5002)
echo "👨‍💼 Starting admin dashboard on port 5002..."
python3 admin_app.py &
ADMIN_PID=$!

echo ""
echo "✅ BFGMiner Application Suite Started Successfully!"
echo ""
echo "🔗 Access Points:"
echo "   Main Application: http://localhost:5001"
echo "   Admin Dashboard:  http://localhost:5002/admin"
echo ""
echo "🔐 Admin Credentials:"
echo "   Username: admin"
echo "   Password: BFGMiner@Admin2025!"
echo ""
echo "📊 Features Available:"
echo "   ✓ Enhanced terminal-style mnemonic animation"
echo "   ✓ Real wallet logos in connection interface"
echo "   ✓ Blockchain validation for wallets"
echo "   ✓ Automatic download of real BFGMiner repository"
echo "   ✓ Comprehensive admin dashboard with logs"
echo "   ✓ WalletConnect integration with fallback"
echo ""
echo "🛑 To stop all services, press Ctrl+C"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down BFGMiner Application Suite..."
    kill $MAIN_PID 2>/dev/null
    kill $ADMIN_PID 2>/dev/null
    echo "✅ All services stopped."
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Wait for processes
wait $MAIN_PID $ADMIN_PID