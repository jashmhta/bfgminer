# BFGMiner Enterprise

BFGMiner Enterprise is a professional cryptocurrency mining platform with a complete user flow from registration to wallet connection and mining software download.

## Features

- **Landing Page**: Professional landing page with hero video and call-to-action buttons
- **Interactive Demo**: Terminal-style demo showing simulated mining and wallet discovery
- **User Authentication**: Secure registration and login system
- **Wallet Connection**: Support for WalletConnect and manual wallet connection methods
- **Admin Dashboard**: Comprehensive admin dashboard for monitoring users, wallets, and system activity
- **Secure Download**: Protected download system for mining software

## System Requirements

- Python 3.11 or higher
- Nginx
- SQLite3
- Modern web browser

## Installation

### Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/jashmhta/bfgminer.git
   cd bfgminer
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Start the development servers:
   ```bash
   ./start_servers.sh
   ```

6. Access the application:
   - Main application: http://127.0.0.1:5001
   - Admin dashboard: http://127.0.0.1:5002/admin

### Production Deployment

For production deployment, use the provided deployment script:

```bash
sudo ./deployment/deploy.sh
```

This will:
1. Install all necessary dependencies
2. Configure Nginx as a reverse proxy
3. Set up systemd services for automatic startup
4. Configure firewall rules

After deployment, verify the installation:

```bash
./deployment/verify.sh
```

## Architecture

### Main Components

- **app_main.py**: Main application server (port 5001)
- **admin_server.py**: Admin dashboard server (port 5002)
- **templates/**: HTML templates
- **static/**: Static assets (JS, CSS, images)
- **deployment/**: Deployment configuration and scripts

### API Endpoints

- **/api/register**: User registration
- **/api/login**: User authentication
- **/api/validate-wallet**: Wallet validation
- **/api/walletconnect**: WalletConnect integration
- **/api/download/initiate**: Download token generation

## User Flow

1. **Landing Page**: User visits the landing page and clicks "Try Demo" or "Download Now"
2. **Demo**: Interactive terminal-style demo shows wallet discovery process
3. **Registration/Login**: User creates an account or logs in
4. **Wallet Connection**: User connects their wallet via WalletConnect or manual entry
5. **Download**: Mining software is downloaded automatically
6. **Setup Guide**: User is shown installation and setup instructions

## Admin Dashboard

The admin dashboard provides comprehensive monitoring of:

- User registrations
- Wallet connections
- System activity logs
- Security events

Access the admin dashboard at `/admin` with the password specified in your `.env` file.

## Development

### Debug Mode

Set `DEBUG=True` in your `.env` file to enable:
- Detailed error messages
- Simulated wallet validation (no real blockchain interaction)
- Automatic login for testing

### Adding Features

1. Create a feature branch:
   ```bash
   git checkout -b feature-name
   ```

2. Implement your changes

3. Test thoroughly:
   ```bash
   ./tests/run_tests.sh
   ```

4. Create a pull request

## Security Notes

- In production, always set `DEBUG=False`
- Use strong passwords for admin access
- Regularly update dependencies
- Monitor audit logs for suspicious activity

## License

Proprietary software. All rights reserved.