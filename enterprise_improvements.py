"""
Enterprise-Grade Improvements for BFGMiner Application
"""
import os
import logging
import sqlite3
import json
import datetime
import uuid
import re
import zipfile
import tempfile
import hashlib
import secrets
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from contextlib import contextmanager

import bcrypt
import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, send_file, abort, session
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from web3 import Web3
import bip39
from blockchain_validator import BlockchainValidator

# Configure enterprise logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bfgminer_enterprise.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

@dataclass
class AppConfig:
    """Enterprise configuration management"""
    SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", secrets.token_hex(32))
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "bfgminer_enterprise.db")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "5001"))
    RATE_LIMIT: str = os.getenv("RATE_LIMIT", "100 per hour")
    SESSION_TIMEOUT: int = int(os.getenv("SESSION_TIMEOUT", "3600"))  # 1 hour
    MAX_CONTENT_LENGTH: int = int(os.getenv("MAX_CONTENT_LENGTH", "16777216"))  # 16MB
    
    # Blockchain configuration
    ETHEREUM_RPC_URLS: List[str] = [
        "https://cloudflare-eth.com",
        "https://rpc.ankr.com/eth",
        "https://eth-mainnet.public.blastapi.io",
        "https://ethereum.publicnode.com"
    ]
    
    # Security configuration
    BCRYPT_ROUNDS: int = 12
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION: int = 900  # 15 minutes

class SecurityManager:
    """Enterprise security management"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.failed_attempts = {}
    
    def hash_password(self, password: str) -> str:
        """Securely hash password"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=self.config.BCRYPT_ROUNDS)).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def is_locked_out(self, identifier: str) -> bool:
        """Check if IP/user is locked out"""
        if identifier not in self.failed_attempts:
            return False
        
        attempts, last_attempt = self.failed_attempts[identifier]
        if attempts >= self.config.MAX_LOGIN_ATTEMPTS:
            if datetime.datetime.now() - last_attempt < datetime.timedelta(seconds=self.config.LOCKOUT_DURATION):
                return True
            else:
                # Reset after lockout period
                del self.failed_attempts[identifier]
        return False
    
    def record_failed_attempt(self, identifier: str):
        """Record failed login attempt"""
        now = datetime.datetime.now()
        if identifier in self.failed_attempts:
            attempts, _ = self.failed_attempts[identifier]
            self.failed_attempts[identifier] = (attempts + 1, now)
        else:
            self.failed_attempts[identifier] = (1, now)
    
    def clear_failed_attempts(self, identifier: str):
        """Clear failed attempts on successful login"""
        if identifier in self.failed_attempts:
            del self.failed_attempts[identifier]
    
    def generate_session_token(self) -> str:
        """Generate secure session token"""
        return secrets.token_urlsafe(32)
    
    def validate_input(self, data: str, input_type: str) -> bool:
        """Validate input data"""
        if input_type == "email":
            return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', data) is not None
        elif input_type == "private_key":
            return re.match(r'^(0x)?[0-9a-fA-F]{64}$', data) is not None
        elif input_type == "wallet_address":
            return re.match(r'^0x[0-9a-fA-F]{40}$', data) is not None
        return True

class DatabaseManager:
    """Enterprise database management with connection pooling"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def init_database(self):
        """Initialize database with enterprise schema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Enhanced users table
            cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                email_verified BOOLEAN DEFAULT FALSE,
                verification_token TEXT,
                last_login DATETIME,
                login_count INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE,
                failed_login_attempts INTEGER DEFAULT 0,
                locked_until DATETIME,
                registration_ip TEXT,
                last_login_ip TEXT,
                user_agent TEXT,
                CONSTRAINT email_format CHECK (email LIKE '%@%.%')
            )''')
            
            # Enhanced sessions table
            cursor.execute('''CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME NOT NULL,
                last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_session_token (session_token),
                INDEX idx_expires_at (expires_at)
            )''')
            
            # Enhanced wallets table
            cursor.execute('''CREATE TABLE IF NOT EXISTS wallets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                wallet_address TEXT NOT NULL,
                connection_type TEXT NOT NULL,
                connection_method TEXT,
                credentials_hash TEXT,  -- Hashed credentials for security
                balance_wei TEXT DEFAULT '0',
                balance_eth REAL DEFAULT 0,
                balance_usd REAL DEFAULT 0,
                chain_id INTEGER DEFAULT 1,
                is_validated BOOLEAN DEFAULT FALSE,
                validation_timestamp DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                risk_score INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
                INDEX idx_wallet_address (wallet_address),
                INDEX idx_connection_type (connection_type),
                INDEX idx_created_at (created_at)
            )''')
            
            # Enhanced downloads table
            cursor.execute('''CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                wallet_id INTEGER,
                download_token TEXT UNIQUE NOT NULL,
                filename TEXT DEFAULT 'bfgminer-repository.zip',
                file_size INTEGER,
                file_hash TEXT,
                download_started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                download_completed_at DATETIME,
                ip_address TEXT,
                user_agent TEXT,
                referrer TEXT,
                download_count INTEGER DEFAULT 0,
                is_completed BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
                FOREIGN KEY (wallet_id) REFERENCES wallets(id) ON DELETE SET NULL,
                INDEX idx_download_token (download_token),
                INDEX idx_download_started (download_started_at)
            )''')
            
            # Audit log table
            cursor.execute('''CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                resource_type TEXT,
                resource_id TEXT,
                details TEXT,  -- JSON string
                ip_address TEXT,
                user_agent TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                session_id TEXT,
                risk_level TEXT DEFAULT 'LOW',
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
                INDEX idx_action (action),
                INDEX idx_timestamp (timestamp),
                INDEX idx_user_id (user_id)
            )''')
            
            # Security events table
            cursor.execute('''CREATE TABLE IF NOT EXISTS security_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                source_ip TEXT,
                user_id INTEGER,
                details TEXT,  -- JSON string
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                resolved BOOLEAN DEFAULT FALSE,
                resolved_at DATETIME,
                resolved_by INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
                FOREIGN KEY (resolved_by) REFERENCES users(id) ON DELETE SET NULL,
                INDEX idx_event_type (event_type),
                INDEX idx_severity (severity),
                INDEX idx_timestamp (timestamp)
            )''')
            
            conn.commit()
            logger.info("Database initialized successfully")

class AuditLogger:
    """Enterprise audit logging"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def log_action(self, user_id: Optional[int], action: str, resource_type: str = None, 
                   resource_id: str = None, details: Dict[str, Any] = None, 
                   ip_address: str = None, user_agent: str = None, 
                   session_id: str = None, risk_level: str = "LOW"):
        """Log user action for audit trail"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''INSERT INTO audit_logs 
                                 (user_id, action, resource_type, resource_id, details, 
                                  ip_address, user_agent, session_id, risk_level)
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                              (user_id, action, resource_type, resource_id, 
                               json.dumps(details) if details else None,
                               ip_address, user_agent, session_id, risk_level))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to log audit action: {e}")
    
    def log_security_event(self, event_type: str, severity: str, source_ip: str = None,
                          user_id: int = None, details: Dict[str, Any] = None):
        """Log security event"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''INSERT INTO security_events 
                                 (event_type, severity, source_ip, user_id, details)
                                 VALUES (?, ?, ?, ?, ?)''',
                              (event_type, severity, source_ip, user_id,
                               json.dumps(details) if details else None))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")

class EnterpriseBlockchainValidator(BlockchainValidator):
    """Enhanced blockchain validator with enterprise features"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.rpc_endpoints = config.ETHEREUM_RPC_URLS
        self.web3 = None
        self.current_endpoint_index = 0
        self.connect_to_blockchain()
    
    def connect_to_blockchain(self) -> bool:
        """Connect with failover support"""
        for i, endpoint in enumerate(self.rpc_endpoints):
            try:
                w3 = Web3(Web3.HTTPProvider(endpoint, request_kwargs={'timeout': 10}))
                if w3.is_connected():
                    self.web3 = w3
                    self.current_endpoint_index = i
                    logger.info(f"Connected to blockchain via {endpoint}")
                    return True
            except Exception as e:
                logger.warning(f"Failed to connect to {endpoint}: {e}")
        
        logger.error("Failed to connect to any blockchain endpoint")
        return False
    
    def validate_with_retry(self, validation_func, *args, **kwargs):
        """Retry validation with different endpoints"""
        max_retries = len(self.rpc_endpoints)
        for attempt in range(max_retries):
            try:
                return validation_func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Validation attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    # Try next endpoint
                    self.current_endpoint_index = (self.current_endpoint_index + 1) % len(self.rpc_endpoints)
                    self.connect_to_blockchain()
        
        raise Exception("All validation attempts failed")

# Initialize enterprise components
config = AppConfig()
security_manager = SecurityManager(config)
db_manager = DatabaseManager(config.DATABASE_PATH)
audit_logger = AuditLogger(db_manager)
validator = EnterpriseBlockchainValidator(config)

# Create Flask app with enterprise configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH
app.config['SESSION_COOKIE_SECURE'] = not config.DEBUG
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

CORS(app, origins=["http://localhost:3000", "http://localhost:5001"] if config.DEBUG else [])

# Rate limiting
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=[config.RATE_LIMIT]
)

@app.before_request
def before_request():
    """Enterprise security checks before each request"""
    # Check for suspicious activity
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    
    # Basic security checks
    if len(request.url) > 2048:  # Prevent long URL attacks
        audit_logger.log_security_event("LONG_URL_ATTACK", "HIGH", ip_address)
        abort(400, "URL too long")
    
    # Check for common attack patterns
    suspicious_patterns = [
        r'<script',
        r'javascript:',
        r'eval\(',
        r'union.*select',
        r'drop.*table'
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, request.url, re.IGNORECASE):
            audit_logger.log_security_event("SUSPICIOUS_REQUEST", "HIGH", ip_address, 
                                           details={"url": request.url, "pattern": pattern})
            abort(400, "Suspicious request detected")

@app.after_request
def after_request(response):
    """Add security headers"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://unpkg.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:;"
    return response

if __name__ == '__main__':
    logger.info("Starting BFGMiner Enterprise Application...")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)