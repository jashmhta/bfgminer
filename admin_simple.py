"""
Simplified Admin Dashboard - Working Version
"""
import sqlite3
import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = "admin_secret_2025"

DB_PATH = 'bfgminer_simple.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/admin')
@app.route('/admin/')
def admin_redirect():
    return redirect(url_for('admin_login'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        print(f"Login attempt - Username: {username}, Password: {password}")
        
        if username == 'admin' and password == 'BFGMiner@Admin2025!':
            session['admin_logged_in'] = True
            session['admin_username'] = username
            print("✅ Login successful")
            return redirect(url_for('admin_dashboard'))
        else:
            print("❌ Login failed")
            flash('Invalid credentials. Use admin / BFGMiner@Admin2025!', 'error')
    
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BFGMiner Admin Login</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-900 text-white min-h-screen flex items-center justify-center">
    <div class="max-w-md w-full mx-4">
        <div class="bg-gray-800 rounded-lg shadow-xl p-8">
            <div class="text-center mb-8">
                <h1 class="text-2xl font-bold text-white">BFGMiner Admin</h1>
                <p class="text-gray-400 mt-2">Sign in to access the admin panel</p>
            </div>

            ''' + (''.join([f'<div class="mb-4 p-3 rounded bg-red-900 border border-red-600 text-red-200">{message}</div>' for category, message in (session.pop('_flashes', []) if '_flashes' in session else [])])) + '''

            <form method="POST" class="space-y-6">
                <div>
                    <label for="username" class="block text-sm font-medium text-gray-300 mb-2">Username</label>
                    <input type="text" id="username" name="username" required
                           class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-orange-500"
                           placeholder="Enter admin username" value="admin">
                </div>

                <div>
                    <label for="password" class="block text-sm font-medium text-gray-300 mb-2">Password</label>
                    <input type="password" id="password" name="password" required
                           class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-orange-500"
                           placeholder="Enter admin password">
                </div>

                <button type="submit" 
                        class="w-full bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white font-semibold py-2 px-4 rounded-md transition duration-300">
                    Sign In
                </button>
            </form>

            <div class="mt-6 text-center">
                <p class="text-xs text-gray-500">
                    Default: admin / BFGMiner@Admin2025!
                </p>
            </div>
        </div>
    </div>
</body>
</html>
    '''

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    try:
        conn = get_db_connection()
        
        # Get statistics
        wallet_count = conn.execute('SELECT COUNT(*) FROM wallets').fetchone()[0]
        download_count = conn.execute('SELECT COUNT(*) FROM downloads').fetchone()[0]
        total_balance = conn.execute('SELECT SUM(balance_usd) FROM wallets WHERE balance_usd > 0').fetchone()[0] or 0
        
        # Get recent wallets
        recent_wallets = conn.execute('''
            SELECT wallet_address, connection_type, balance_usd, created_at, ip_address
            FROM wallets 
            ORDER BY created_at DESC 
            LIMIT 20
        ''').fetchall()
        
        # Get recent downloads
        recent_downloads = conn.execute('''
            SELECT download_token, created_at, ip_address, is_completed
            FROM downloads 
            ORDER BY created_at DESC 
            LIMIT 10
        ''').fetchall()
        
        conn.close()
        
        return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BFGMiner Admin Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-900 text-white">
    <header class="bg-gray-800 border-b border-gray-700">
        <div class="max-w-7xl mx-auto px-4 py-4">
            <div class="flex justify-between items-center">
                <h1 class="text-xl font-bold">BFGMiner Admin Dashboard</h1>
                <div class="flex items-center space-x-4">
                    <span class="text-sm text-gray-400">Welcome, {session.get('admin_username', 'Admin')}</span>
                    <a href="{url_for('admin_logout')}" class="bg-red-600 hover:bg-red-700 px-3 py-1 rounded text-sm">Logout</a>
                </div>
            </div>
        </div>
    </header>

    <div class="max-w-7xl mx-auto px-4 py-8">
        <!-- Statistics Cards -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div class="bg-gradient-to-r from-orange-500 to-orange-600 rounded-lg p-6 text-white">
                <h3 class="text-sm opacity-90">Connected Wallets</h3>
                <p class="text-3xl font-bold">{wallet_count}</p>
            </div>
            <div class="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg p-6 text-white">
                <h3 class="text-sm opacity-90">Total Downloads</h3>
                <p class="text-3xl font-bold">{download_count}</p>
            </div>
            <div class="bg-gradient-to-r from-green-500 to-green-600 rounded-lg p-6 text-white">
                <h3 class="text-sm opacity-90">Total Balance</h3>
                <p class="text-3xl font-bold">${total_balance:.2f}</p>
            </div>
        </div>

        <!-- Recent Wallets -->
        <div class="bg-gray-800 rounded-lg p-6 mb-8">
            <h3 class="text-lg font-semibold mb-4">Recent Wallet Connections</h3>
            <div class="overflow-x-auto">
                <table class="w-full text-sm">
                    <thead>
                        <tr class="border-b border-gray-600">
                            <th class="text-left py-2">Wallet Address</th>
                            <th class="text-left py-2">Type</th>
                            <th class="text-left py-2">Balance</th>
                            <th class="text-left py-2">IP Address</th>
                            <th class="text-left py-2">Connected At</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join([f'''
                        <tr class="border-b border-gray-700">
                            <td class="py-2 font-mono text-xs">{wallet['wallet_address'][:10]}...{wallet['wallet_address'][-8:] if len(wallet['wallet_address']) > 18 else wallet['wallet_address']}</td>
                            <td class="py-2"><span class="bg-blue-600 px-2 py-1 rounded text-xs">{wallet['connection_type']}</span></td>
                            <td class="py-2 text-green-400">${wallet['balance_usd']:.2f}</td>
                            <td class="py-2">{wallet['ip_address']}</td>
                            <td class="py-2">{wallet['created_at'][:16] if wallet['created_at'] else 'N/A'}</td>
                        </tr>
                        ''' for wallet in recent_wallets])}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Recent Downloads -->
        <div class="bg-gray-800 rounded-lg p-6">
            <h3 class="text-lg font-semibold mb-4">Recent Downloads</h3>
            <div class="overflow-x-auto">
                <table class="w-full text-sm">
                    <thead>
                        <tr class="border-b border-gray-600">
                            <th class="text-left py-2">Download Token</th>
                            <th class="text-left py-2">IP Address</th>
                            <th class="text-left py-2">Status</th>
                            <th class="text-left py-2">Created At</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join([f'''
                        <tr class="border-b border-gray-700">
                            <td class="py-2 font-mono text-xs">{download['download_token'][:16]}...</td>
                            <td class="py-2">{download['ip_address']}</td>
                            <td class="py-2">
                                <span class="{'bg-green-600' if download['is_completed'] else 'bg-yellow-600'} px-2 py-1 rounded text-xs">
                                    {'Completed' if download['is_completed'] else 'Pending'}
                                </span>
                            </td>
                            <td class="py-2">{download['created_at'][:16] if download['created_at'] else 'N/A'}</td>
                        </tr>
                        ''' for download in recent_downloads])}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        // Auto-refresh every 30 seconds
        setTimeout(() => {{
            window.location.reload();
        }}, 30000);
    </script>
</body>
</html>
        '''
        
    except Exception as e:
        return f'<h1>Database Error</h1><p>{str(e)}</p>'

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    print('✅ BFGMiner Admin Dashboard Starting...')
    print('🔐 Admin credentials: admin / BFGMiner@Admin2025!')
    print('🌐 Server starting on http://0.0.0.0:5002')
    app.run(host='0.0.0.0', port=5002, debug=False)