"""
Separate Admin Dashboard Application for BFGMiner
"""
import os
import sqlite3
import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_cors import CORS
import bcrypt

app = Flask(__name__)
app.secret_key = os.getenv("ADMIN_SECRET_KEY", "admin_bfgminer_2025")
CORS(app)

DB_PATH = 'bfgminer.db'

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Simple admin authentication (in production, use proper password hashing)
        if username == 'admin' and password == 'BFGMiner@Admin2025!':
            session['admin_logged_in'] = True
            session['admin_username'] = username
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
@app.route('/admin/dashboard')
def admin_dashboard():
    """Main admin dashboard"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    try:
        conn = get_db_connection()
        
        # Get statistics
        stats = {}
        stats['total_users'] = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        stats['total_wallets'] = conn.execute('SELECT COUNT(*) FROM wallets').fetchone()[0]
        stats['total_downloads'] = conn.execute('SELECT COUNT(*) FROM downloads').fetchone()[0]
        stats['total_balance'] = conn.execute('SELECT SUM(balance_usd) FROM wallets WHERE balance_usd > 0').fetchone()[0] or 0
        
        # Get recent wallet connections
        recent_wallets = conn.execute('''
            SELECT w.*, u.email, u.created_at as user_created
            FROM wallets w
            LEFT JOIN users u ON w.user_id = u.id
            ORDER BY w.created_at DESC
            LIMIT 50
        ''').fetchall()
        
        # Get recent downloads
        recent_downloads = conn.execute('''
            SELECT d.*, u.email
            FROM downloads d
            LEFT JOIN users u ON d.user_id = u.id
            ORDER BY d.created_at DESC
            LIMIT 20
        ''').fetchall()
        
        # Get wallet connection methods breakdown
        connection_methods = conn.execute('''
            SELECT connection_type, COUNT(*) as count
            FROM wallets
            GROUP BY connection_type
        ''').fetchall()
        
        conn.close()
        
        return render_template('admin_dashboard.html', 
                             stats=stats,
                             recent_wallets=recent_wallets,
                             recent_downloads=recent_downloads,
                             connection_methods=connection_methods)
        
    except Exception as e:
        flash(f'Database error: {str(e)}', 'error')
        return render_template('admin_dashboard.html', 
                             stats={}, recent_wallets=[], recent_downloads=[], connection_methods=[])

@app.route('/admin/api/wallets')
def api_wallets():
    """API endpoint for wallet data"""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        conn = get_db_connection()
        
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 25))
        offset = (page - 1) * per_page
        
        # Get search parameters
        search = request.args.get('search', '')
        connection_type = request.args.get('connection_type', '')
        
        # Build query
        where_conditions = []
        params = []
        
        if search:
            where_conditions.append('(w.wallet_address LIKE ? OR u.email LIKE ?)')
            params.extend([f'%{search}%', f'%{search}%'])
        
        if connection_type:
            where_conditions.append('w.connection_type = ?')
            params.append(connection_type)
        
        where_clause = 'WHERE ' + ' AND '.join(where_conditions) if where_conditions else ''
        
        # Get total count
        count_query = f'''
            SELECT COUNT(*)
            FROM wallets w
            LEFT JOIN users u ON w.user_id = u.id
            {where_clause}
        '''
        total = conn.execute(count_query, params).fetchone()[0]
        
        # Get wallets
        wallets_query = f'''
            SELECT w.*, u.email, u.created_at as user_created
            FROM wallets w
            LEFT JOIN users u ON w.user_id = u.id
            {where_clause}
            ORDER BY w.created_at DESC
            LIMIT ? OFFSET ?
        '''
        params.extend([per_page, offset])
        wallets = conn.execute(wallets_query, params).fetchall()
        
        conn.close()
        
        return jsonify({
            'wallets': [dict(wallet) for wallet in wallets],
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/stats')
def api_stats():
    """API endpoint for dashboard statistics"""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        conn = get_db_connection()
        
        # Daily statistics for the last 30 days
        daily_stats = conn.execute('''
            SELECT DATE(created_at) as date,
                   COUNT(*) as wallet_connections
            FROM wallets
            WHERE created_at >= date('now', '-30 days')
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        ''').fetchall()
        
        # Connection type breakdown
        connection_breakdown = conn.execute('''
            SELECT connection_type,
                   COUNT(*) as count,
                   SUM(balance_usd) as total_balance
            FROM wallets
            GROUP BY connection_type
        ''').fetchall()
        
        # Top wallet balances
        top_wallets = conn.execute('''
            SELECT wallet_address, balance_usd, connection_type, created_at
            FROM wallets
            WHERE balance_usd > 0
            ORDER BY balance_usd DESC
            LIMIT 10
        ''').fetchall()
        
        conn.close()
        
        return jsonify({
            'daily_stats': [dict(row) for row in daily_stats],
            'connection_breakdown': [dict(row) for row in connection_breakdown],
            'top_wallets': [dict(row) for row in top_wallets]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print('Starting BFGMiner Admin Dashboard...')
    app.run(host='0.0.0.0', port=5002, debug=True)