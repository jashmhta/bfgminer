"""BFGMiner Admin Dashboard - Complete Flask Blueprint Implementation

Production-ready admin functionality with:
- Persistent admin authentication (no session expiry)
- Comprehensive user/wallet/notification/audit log management
- Mainnet balance validation with Infura RPC and CoinGecko pricing
- Real-time notifications via SSE
- Rate limiting and caching for performance
- Complete audit logging for security
- Unmasked wallet data display (no encryption)
"""

import os
import sqlite3
import bcrypt
import requests
import json
import datetime
import uuid
import functools
import threading
import time
from flask import Blueprint, render_template, request, jsonify, session, abort, Response, current_app, send_file
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create admin blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Global cache for balance results
data_cache = {}
BALANCE_CACHE_TTL = 300  # 5 minutes

# Rate limiting storage
rate_limits = {}
RATE_LIMIT_WINDOW = 60  # 1 minute
MAX_REQUESTS = 10

# Database connection helper
def get_db_connection():
    conn = sqlite3.connect('bfgminer.db')
    conn.row_factory = sqlite3.Row
    return conn

# Audit logging function
def log_admin_action(admin_id, action, target_id=None, target_type=None, details=None, ip_address=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO admin_audit_logs (admin_id, action, target_id, target_type, details, ip_address, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (admin_id, action, target_id, target_type, details, ip_address, datetime.datetime.now()))
    conn.commit()
    conn.close()

# Admin authentication middleware
def require_admin(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        session_token = request.headers.get('Authorization', '').replace('Bearer ', '') or request.cookies.get('admin_token')
        if not session_token:
            abort(401, 'Admin authentication required')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT s.admin_id, a.username FROM admin_sessions s JOIN admin_users a ON s.admin_id = a.id WHERE s.session_token = ?', (session_token,))
        admin = cursor.fetchone()
        conn.close()
        
        if not admin:
            abort(401, 'Invalid admin session')
        
        # Log access attempt
        ip_address = request.remote_addr or '127.0.0.1'
        log_admin_action(admin['admin_id'], 'route_access', details=f'{request.path}', ip_address=ip_address)
        
        # Add admin info to request for use in route
        request.admin = {'id': admin['admin_id'], 'username': admin['username']}
        return f(*args, **kwargs)
    return decorated_function

# Rate limiting decorator for balance checks
def rate_limit_balance_check(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.remote_addr or '127.0.0.1'
        now = time.time()
        
        if client_ip not in rate_limits:
            rate_limits[client_ip] = []
        
        # Remove old requests
        rate_limits[client_ip] = [req_time for req_time in rate_limits[client_ip] if now - req_time < RATE_LIMIT_WINDOW]
        
        if len(rate_limits[client_ip]) >= MAX_REQUESTS:
            abort(429, 'Rate limit exceeded. Too many balance validation requests.')
        
        rate_limits[client_ip].append(now)
        return f(*args, **kwargs)
    return decorated_function

# Admin Login Route
@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'error': 'Username and password required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, password_hash FROM admin_users WHERE username = ? AND is_active = 1', (username,))
        admin = cursor.fetchone()
        conn.close()
        
        if not admin or not bcrypt.checkpw(password.encode(), admin['password_hash'].encode()):
            ip_address = request.remote_addr or '127.0.0.1'
            log_admin_action(1, 'login_failed', details=f'Invalid credentials for {username}', ip_address=ip_address)
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        
        # Generate persistent session token (no expiry)
        session_token = str(uuid.uuid4())
        ip_address = request.remote_addr or '127.0.0.1'
        user_agent = request.headers.get('User-Agent', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO admin_sessions (session_token, admin_id, login_time, user_agent, ip_address)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_token, admin['id'], datetime.datetime.now(), user_agent, ip_address))
        conn.commit()
        conn.close()
        
        # Log successful login
        log_admin_action(admin['id'], 'login_success', ip_address=ip_address, details=f'Admin {username} logged in')
        
        response = jsonify({'success': True, 'message': 'Admin login successful', 'sessionToken': session_token})
        response.set_cookie('admin_token', session_token, httponly=True, secure=True, samesite='Strict')
        return response
    
    return render_template('admin_login.html')

# Admin Logout Route
@admin_bp.route('/logout', methods=['POST'])
@require_admin
def admin_logout():
    session_token = request.headers.get('Authorization', '').replace('Bearer ', '') or request.cookies.get('admin_token')
    if session_token:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM admin_sessions WHERE session_token = ?', (session_token,))
        conn.commit()
        conn.close()
        log_admin_action(request.admin['id'], 'logout', ip_address=request.remote_addr, details='Admin session terminated')
    
    response = jsonify({'success': True, 'message': 'Logged out successfully'})
    response.delete_cookie('admin_token')
    return response

# Admin Dashboard Route
@admin_bp.route('/dashboard')
@require_admin
def admin_dashboard():
    return render_template('admin_dashboard.html')

# API: Get Users (Paginated with Wallet/Download Counts)
@admin_bp.route('/api/users')
@require_admin
def get_users():
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    search = request.args.get('search', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = '''
        SELECT u.id, u.email, u.registration_date, u.email_verified as verification_status, u.last_login,
               COUNT(w.id) as total_wallets, COUNT(d.id) as downloads_count
        FROM users u
        LEFT JOIN wallets w ON u.id = w.user_id
        LEFT JOIN downloads d ON u.id = d.user_id
    '''
    params = []
    
    if search:
        query += 'WHERE u.email LIKE ? '
        params.append(f'%{search}%')
    
    query += 'GROUP BY u.id, u.email, u.registration_date, u.email_verified, u.last_login '
    query += 'ORDER BY u.registration_date DESC LIMIT ? OFFSET ?'
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    users = [dict(row) for row in cursor.fetchall()]
    
    # Get total count for pagination
    count_query = 'SELECT COUNT(DISTINCT u.id) FROM users u'
    if search:
        count_query += ' WHERE u.email LIKE ?'
        cursor.execute(count_query, (f'%{search}%',))
    else:
        cursor.execute(count_query)
    total = cursor.fetchone()[0]
    
    conn.close()
    log_admin_action(request.admin['id'], 'user_view', details=f'Viewed {len(users)} users, search: {search}')
    return jsonify({'users': users, 'total': total, 'limit': limit, 'offset': offset})

# API: Get All Wallets (Unmasked Data)
@admin_bp.route('/api/wallets')
@require_admin
def get_wallets():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT w.*, u.email as user_email, u.id as user_id
        FROM wallets w
        JOIN users u ON w.user_id = u.id
        ORDER BY w.created_at DESC
    ''')
    wallets = [dict(row) for row in cursor.fetchall()]
    conn.close()
    log_admin_action(request.admin['id'], 'wallet_view', details=f'Viewed {len(wallets)} wallets')
    return jsonify({'wallets': wallets})

# API: Validate Wallet Balance (Mainnet + CoinGecko)
@admin_bp.route('/api/wallets/validate-balance', methods=['POST'])
@require_admin
@rate_limit_balance_check
def validate_wallet_balance():
    data = request.json
    wallet_address = data.get('wallet_address')
    
    if not wallet_address:
        return jsonify({'success': False, 'error': 'Wallet address required'}), 400
    
    # Get Infura project ID from environment
    infura_project_id = os.getenv('INFURA_PROJECT_ID')
    if not infura_project_id or infura_project_id == 'your_infura_project_id_here':
        return jsonify({'success': False, 'error': 'Infura configuration required'}), 500
    
    cache_key = f'balance_{wallet_address.lower()}'
    current_time = time.time()
    
    # Check cache
    if cache_key in data_cache and current_time - data_cache[cache_key]['timestamp'] < BALANCE_CACHE_TTL:
        return jsonify(data_cache[cache_key]['data'])
    
    try:
        # Mainnet balance check using Infura JSON-RPC
        infura_url = f'https://mainnet.infura.io/v3/{infura_project_id}'
        payload = {
            'jsonrpc': '2.0',
            'method': 'eth_getBalance',
            'params': [wallet_address, 'latest'],
            'id': 1
        }
        response = requests.post(infura_url, json=payload, timeout=10)
        response.raise_for_status()
        
        balance_wei = int(response.json()['result'], 16)
        balance_eth = balance_wei / 1e18
        
        # Get current ETH price from CoinGecko
        price_response = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd', timeout=10)
        price_response.raise_for_status()
        eth_price = price_response.json()['ethereum']['usd']
        balance_usd = balance_eth * eth_price
        
        result = {
            'success': True,
            'wallet_address': wallet_address,
            'balance_eth': round(balance_eth, 6),
            'balance_usd': round(balance_usd, 2),
            'eth_price': eth_price,
            'timestamp': datetime.datetime.now().isoformat(),
            'cached': False
        }
        
        # Cache result for 5 minutes
        data_cache[cache_key] = {'data': result, 'timestamp': current_time}
        
        # Log balance validation
        log_admin_action(request.admin['id'], 'balance_check', target_id=wallet_address, target_type='wallet', details=f'Balance: {balance_eth} ETH (${balance_usd} USD)')
        
        return jsonify(result)
    
    except requests.exceptions.RequestException as e:
        error_msg = f'RPC/Price API error: {str(e)}'
        log_admin_action(request.admin['id'], 'balance_check_failed', target_id=wallet_address, target_type='wallet', details=error_msg)
        return jsonify({'success': False, 'error': error_msg}), 500
    
    except Exception as e:
        error_msg = f'Unexpected error: {str(e)}'
        log_admin_action(request.admin['id'], 'balance_check_failed', target_id=wallet_address, target_type='wallet', details=error_msg)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

# API: Get Notifications
@admin_bp.route('/api/notifications')
@require_admin
def get_notifications():
    unread_only = request.args.get('unread', 'false').lower() == 'true'
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if unread_only:
        query = 'SELECT * FROM notifications WHERE is_read = 0 ORDER BY created_at DESC LIMIT ? OFFSET ?'
    else:
        query = 'SELECT * FROM notifications ORDER BY created_at DESC LIMIT ? OFFSET ?'
    
    cursor.execute(query, (limit, offset))
    notifications = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    log_admin_action(request.admin['id'], 'notification_view', details=f'Viewed {len(notifications)} notifications, unread_only: {unread_only}')
    return jsonify({'notifications': notifications})

# API: Get Audit Logs
@admin_bp.route('/api/logs')
@require_admin
def get_audit_logs():
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT al.*, au.username
        FROM admin_audit_logs al
        JOIN admin_users au ON al.admin_id = au.id
        ORDER BY al.created_at DESC LIMIT ? OFFSET ?
    ''', (limit, offset))
    logs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    log_admin_action(request.admin['id'], 'audit_log_view', details=f'Viewed {len(logs)} audit logs')
    return jsonify({'logs': logs})

# API: Delete User (with Cascade)
@admin_bp.route('/api/users/<int:user_id>', methods=['DELETE'])
@require_admin
def delete_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    
    if affected > 0:
        log_admin_action(request.admin['id'], 'user_delete', target_id=user_id, target_type='user', details=f'User {user_id} deleted (cascade to wallets/downloads/sessions)')
        return jsonify({'success': True, 'message': 'User deleted successfully with cascade'})
    else:
        return jsonify({'success': False, 'error': 'User not found'}), 404

# API: Delete Wallet
@admin_bp.route('/api/wallets/<int:wallet_id>', methods=['DELETE'])
@require_admin
def delete_wallet(wallet_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM wallets WHERE id = ?', (wallet_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    
    if affected > 0:
        log_admin_action(request.admin['id'], 'wallet_delete', target_id=wallet_id, target_type='wallet', details=f'Wallet {wallet_id} deleted (unmasked data removed)')
        return jsonify({'success': True, 'message': 'Wallet deleted successfully'})
    else:
        return jsonify({'success': False, 'error': 'Wallet not found'}), 404

# Server-Sent Events for Real-time Notifications
@admin_bp.route('/events')
@require_admin
def admin_events():
    def event_stream():
        last_notification_id = 0
        while True:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM notifications WHERE id > ? AND is_read = 0 ORDER BY created_at DESC LIMIT 1', (last_notification_id,))
            notification = cursor.fetchone()
            conn.close()
            
            if notification:
                last_notification_id = notification['id']
                yield f'data: {json.dumps(dict(notification))}\n\n'
                # Mark as read
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('UPDATE notifications SET is_read = 1 WHERE id = ?', (notification['id'],))
                conn.commit()
                conn.close()
            
            time.sleep(30)  # Poll every 30 seconds
    
    return Response(event_stream(), mimetype='text/event-stream',
                   headers={'Cache-Control': 'no-cache',
                           'Connection': 'keep-alive',
                           'Access-Control-Allow-Origin': '*' })

# Notification Trigger Function (Call from user routes)
def trigger_notification(notification_type, user_id=None, wallet_address=None, message=None):
    """Trigger admin notification and email alert for user actions"""
    if not message:
        messages = {
            'registration': 'New user registration detected',
            'wallet_connect': f'New wallet connection: {wallet_address}',
            'download': 'New download initiated by user',
            'balance_update': 'Wallet balance updated successfully'
        }
        message = messages.get(notification_type, 'New platform notification')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO notifications (type, user_id, wallet_address, message, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (notification_type, user_id, wallet_address, message, datetime.datetime.now()))
    conn.commit()
    conn.close()
    
    # Send async email notification to admin
    def send_admin_email():
        try:
            import smtplib
            from email.mime.text import MIMEText
            smtp_server = 'smtp.gmail.com'
            smtp_port = 587
            sender_email = os.getenv('GMAIL_SENDER', 'noreply@bfgminer.local')
            receiver_email = os.getenv('ADMIN_EMAIL', 'admin@bfgminer.local')
            smtp_password = os.getenv('SMTP_PASSWORD')
            
            msg = MIMEText(f'BFGMiner Admin Alert: {notification_type.upper()}\n\n{message}')
            msg['Subject'] = f'URGENT: BFGMiner {notification_type.upper()} Alert'
            msg['From'] = sender_email
            msg['To'] = receiver_email
            
            if smtp_password and smtp_password != 'your_gmail_app_password_16_chars':
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
                server.login(sender_email, smtp_password)
                server.send_message(msg)
                server.quit()
                print(f'[ADMIN EMAIL] Sent notification: {notification_type} - {message}')
            else:
                print(f'[ADMIN EMAIL] SMTP credentials not configured - skipping email for {notification_type}')
                
        except Exception as e:
            print(f'[ADMIN EMAIL ERROR] Failed to send email for {notification_type}: {e}')
    
    # Run email sending in background thread
    threading.Thread(target=send_admin_email, daemon=True).start()

# Blueprint registration function
def register_admin_blueprint(app):
    """Register admin blueprint with CORS support"""
    CORS(admin_bp)
    app.register_blueprint(admin_bp)
    print('✓ Admin blueprint registered successfully')

if __name__ == '__main__':
    from flask import Flask
    app = Flask(__name__)
    app.secret_key = os.getenv('FLASK_SECRET_KEY', 'bfgminer_admin_secret_2025')
    register_admin_blueprint(app)
    app.run(debug=True, port=5001)
