#!/bin/bash

# BFGMiner Enterprise Deployment Script
# Comprehensive deployment with all enterprise features

set -e  # Exit on any error

echo "🚀 BFGMiner Enterprise Deployment Starting..."
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PYTHON_VERSION="3.8"
NODE_VERSION="16"
VENV_NAME="bfgminer_enterprise"
LOG_DIR="logs"
BACKUP_DIR="backups"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Check system requirements
check_requirements() {
    print_header "📋 Checking System Requirements..."
    
    # Check Python
    if command -v python3 &> /dev/null; then
        PYTHON_VER=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
        print_status "Python $PYTHON_VER found"
    else
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Check pip
    if command -v pip3 &> /dev/null; then
        print_status "pip3 found"
    else
        print_error "pip3 is required but not installed"
        exit 1
    fi
    
    # Check Node.js (optional for development)
    if command -v node &> /dev/null; then
        NODE_VER=$(node --version)
        print_status "Node.js $NODE_VER found"
    else
        print_warning "Node.js not found (optional for development)"
    fi
    
    # Check available disk space
    AVAILABLE_SPACE=$(df . | tail -1 | awk '{print $4}')
    if [ "$AVAILABLE_SPACE" -lt 1048576 ]; then  # 1GB in KB
        print_warning "Less than 1GB disk space available"
    else
        print_status "Sufficient disk space available"
    fi
    
    print_status "System requirements check completed"
}

# Setup directories
setup_directories() {
    print_header "📁 Setting up directories..."
    
    mkdir -p "$LOG_DIR"
    mkdir -p "$BACKUP_DIR"
    mkdir -p "temp"
    mkdir -p "uploads"
    mkdir -p "downloads"
    
    print_status "Directories created successfully"
}

# Setup Python virtual environment
setup_python_env() {
    print_header "🐍 Setting up Python environment..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "$VENV_NAME" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv "$VENV_NAME"
    else
        print_status "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source "$VENV_NAME/bin/activate"
    
    # Upgrade pip
    print_status "Upgrading pip..."
    pip install --upgrade pip
    
    # Install requirements
    print_status "Installing Python dependencies..."
    pip install -r requirements.txt
    
    # Install additional enterprise packages
    print_status "Installing enterprise packages..."
    pip install psutil gunicorn pytest pytest-cov
    
    print_status "Python environment setup completed"
}

# Setup database
setup_database() {
    print_header "🗄️ Setting up enterprise database..."
    
    # Backup existing database if it exists
    if [ -f "bfgminer.db" ]; then
        BACKUP_FILE="$BACKUP_DIR/bfgminer_$(date +%Y%m%d_%H%M%S).db"
        cp "bfgminer.db" "$BACKUP_FILE"
        print_status "Existing database backed up to $BACKUP_FILE"
    fi
    
    # Initialize enterprise database
    python3 -c "
from enterprise_improvements import DatabaseManager
from config import AppConfig
config = AppConfig()
db_manager = DatabaseManager(config.database.PATH)
print('Enterprise database initialized successfully')
"
    
    print_status "Database setup completed"
}

# Run tests
run_tests() {
    print_header "🧪 Running enterprise test suite..."
    
    # Activate virtual environment
    source "$VENV_NAME/bin/activate"
    
    # Run unit tests
    print_status "Running unit tests..."
    python -m pytest tests/ -v --tb=short
    
    # Run code quality checks
    print_status "Running code quality checks..."
    
    # Check Python syntax
    find . -name "*.py" -not -path "./venv/*" -not -path "./$VENV_NAME/*" -exec python3 -m py_compile {} \;
    
    # Check JavaScript syntax
    if command -v node &> /dev/null; then
        find . -name "*.js" -not -path "./node_modules/*" -exec node -c {} \;
    fi
    
    print_status "All tests passed successfully"
}

# Setup configuration
setup_configuration() {
    print_header "⚙️ Setting up enterprise configuration..."
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        print_status "Creating .env configuration file..."
        cat > .env << EOF
# BFGMiner Enterprise Configuration
FLASK_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
DATABASE_PATH=bfgminer_enterprise.db
DEBUG=False
HOST=0.0.0.0
PORT=5001
ADMIN_PORT=5002
LOG_LEVEL=INFO
LOG_FILE=logs/bfgminer_enterprise.log
BCRYPT_ROUNDS=12
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION=900
SESSION_TIMEOUT=3600
RATE_LIMIT=100 per hour
ADMIN_PASSWORD=BFGMiner@Admin2025!
EOF
        print_status ".env file created with secure defaults"
    else
        print_status ".env file already exists"
    fi
    
    # Set proper permissions
    chmod 600 .env
    print_status "Configuration file permissions set"
}

# Setup systemd services (Linux only)
setup_services() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        print_header "🔧 Setting up systemd services..."
        
        # Check if running as root or with sudo
        if [ "$EUID" -eq 0 ]; then
            print_status "Setting up systemd services..."
            
            # Main application service
            cat > /etc/systemd/system/bfgminer-app.service << EOF
[Unit]
Description=BFGMiner Enterprise Application
After=network.target

[Service]
Type=exec
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/$VENV_NAME/bin
ExecStart=$(pwd)/$VENV_NAME/bin/gunicorn -c gunicorn.conf.py app_enterprise:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

            # Admin dashboard service
            cat > /etc/systemd/system/bfgminer-admin.service << EOF
[Unit]
Description=BFGMiner Admin Dashboard
After=network.target

[Service]
Type=exec
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/$VENV_NAME/bin
ExecStart=$(pwd)/$VENV_NAME/bin/python admin_app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

            systemctl daemon-reload
            systemctl enable bfgminer-app.service
            systemctl enable bfgminer-admin.service
            
            print_status "Systemd services configured"
        else
            print_warning "Systemd services require root privileges. Run with sudo for service setup."
        fi
    else
        print_warning "Systemd services only available on Linux"
    fi
}

# Start services
start_services() {
    print_header "🚀 Starting BFGMiner Enterprise Services..."
    
    # Activate virtual environment
    source "$VENV_NAME/bin/activate"
    
    # Start main application
    print_status "Starting main application on port 5001..."
    nohup python3 app_enterprise.py > "$LOG_DIR/app.log" 2>&1 &
    APP_PID=$!
    echo $APP_PID > "$LOG_DIR/app.pid"
    
    # Wait a moment
    sleep 3
    
    # Start admin dashboard
    print_status "Starting admin dashboard on port 5002..."
    nohup python3 admin_app.py > "$LOG_DIR/admin.log" 2>&1 &
    ADMIN_PID=$!
    echo $ADMIN_PID > "$LOG_DIR/admin.pid"
    
    # Wait for services to start
    sleep 5
    
    # Check if services are running
    if kill -0 $APP_PID 2>/dev/null; then
        print_status "Main application started successfully (PID: $APP_PID)"
    else
        print_error "Failed to start main application"
        exit 1
    fi
    
    if kill -0 $ADMIN_PID 2>/dev/null; then
        print_status "Admin dashboard started successfully (PID: $ADMIN_PID)"
    else
        print_error "Failed to start admin dashboard"
        exit 1
    fi
}

# Health check
health_check() {
    print_header "🏥 Performing health checks..."
    
    # Check main application
    if curl -f -s http://localhost:5001/health > /dev/null; then
        print_status "Main application health check passed"
    else
        print_warning "Main application health check failed"
    fi
    
    # Check admin dashboard
    if curl -f -s http://localhost:5002/admin > /dev/null; then
        print_status "Admin dashboard health check passed"
    else
        print_warning "Admin dashboard health check failed"
    fi
}

# Display deployment summary
show_summary() {
    print_header "📋 Deployment Summary"
    echo "================================================"
    echo ""
    echo "🎉 BFGMiner Enterprise deployed successfully!"
    echo ""
    echo "🔗 Access Points:"
    echo "   Main Application: http://localhost:5001"
    echo "   Admin Dashboard:  http://localhost:5002/admin"
    echo ""
    echo "🔐 Admin Credentials:"
    echo "   Username: admin"
    echo "   Password: BFGMiner@Admin2025!"
    echo ""
    echo "📊 Enterprise Features:"
    echo "   ✅ Enhanced terminal-style animation"
    echo "   ✅ Real wallet logos and blockchain validation"
    echo "   ✅ Comprehensive admin dashboard"
    echo "   ✅ Enterprise security and monitoring"
    echo "   ✅ Automatic download of real BFGMiner repository"
    echo "   ✅ Complete audit logging and analytics"
    echo ""
    echo "📁 Important Files:"
    echo "   Configuration: .env"
    echo "   Database: bfgminer_enterprise.db"
    echo "   Logs: $LOG_DIR/"
    echo "   Backups: $BACKUP_DIR/"
    echo ""
    echo "🛑 To stop services:"
    echo "   kill \$(cat $LOG_DIR/app.pid)"
    echo "   kill \$(cat $LOG_DIR/admin.pid)"
    echo ""
    echo "📖 For more information, see ENTERPRISE_ANALYSIS.md"
    echo ""
}

# Cleanup function
cleanup() {
    if [ -f "$LOG_DIR/app.pid" ]; then
        APP_PID=$(cat "$LOG_DIR/app.pid")
        if kill -0 $APP_PID 2>/dev/null; then
            kill $APP_PID
            print_status "Stopped main application"
        fi
    fi
    
    if [ -f "$LOG_DIR/admin.pid" ]; then
        ADMIN_PID=$(cat "$LOG_DIR/admin.pid")
        if kill -0 $ADMIN_PID 2>/dev/null; then
            kill $ADMIN_PID
            print_status "Stopped admin dashboard"
        fi
    fi
}

# Trap cleanup on script exit (disabled for persistent deployment)
# trap cleanup EXIT

# Main deployment flow
main() {
    print_header "🏢 BFGMiner Enterprise Deployment"
    echo "Starting comprehensive enterprise deployment..."
    echo ""
    
    check_requirements
    setup_directories
    setup_python_env
    setup_configuration
    setup_database
    run_tests
    setup_services
    start_services
    
    # Wait a moment for services to fully start
    sleep 5
    
    health_check
    show_summary
    
    print_status "Enterprise deployment completed successfully!"
}

# Handle command line arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "test")
        setup_python_env
        run_tests
        ;;
    "start")
        start_services
        ;;
    "stop")
        cleanup
        ;;
    "health")
        health_check
        ;;
    *)
        echo "Usage: $0 {deploy|test|start|stop|health}"
        echo ""
        echo "Commands:"
        echo "  deploy  - Full enterprise deployment (default)"
        echo "  test    - Run test suite only"
        echo "  start   - Start services only"
        echo "  stop    - Stop all services"
        echo "  health  - Run health checks"
        exit 1
        ;;
esac