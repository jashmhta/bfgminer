
"""
Admin Dashboard Server for BFGMiner - Runs on Port 5002
"""
import os
import sqlite3
from flask import Flask, request, render_template, abort, session
from dotenv import load_dotenv
from enterprise_improvements import AppConfig, DatabaseManager, AuditLogger

load_dotenv()

app = Flask(__name__, template_folder="templates")
app.secret_key = AppConfig().SECRET_KEY  # Reuse config
DB_PATH = AppConfig().DATABASE_PATH
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "BFGMiner@Admin2025!")

db = DatabaseManager(DB_PATH)
db.init_database()
audit = AuditLogger(db)

@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    """Admin dashboard for viewing logs"""
    if request.method == 'POST':
        password = request.form.get('password')
        if password != ADMIN_PASSWORD:
            abort(401, "Unauthorized")
        session['admin'] = True

    if 'admin' not in session:
        # Simple password prompt (render a login form if needed, but for now, assume POST handles it)
        return '''
        <form method="post">
            <label>Admin Password:</label>
            <input type="password" name="password">
            <button type="submit">Login</button>
        </form>
        '''

    # Basic auth check (simplified; in prod use proper auth)
    session['admin'] = True

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get users
    cursor.execute("SELECT id, email, created_at, last_login FROM users")
    users = cursor.fetchall()

    # Get wallets
    cursor.execute("""
        SELECT w.id, u.email, w.wallet_address, w.connection_type, w.balance_usd, w.created_at
        FROM wallets w JOIN users u ON w.user_id = u.id
    """)
    wallets = cursor.fetchall()

    # Get audit logs (assuming audit_logs table exists from AuditLogger)
    try:
        cursor.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 50")
        audit_logs = cursor.fetchall()
    except sqlite3.OperationalError:
        audit_logs = []  # Table may not exist yet

    conn.close()

    return render_template('admin.html', users=users, wallets=wallets, audit_logs=audit_logs)

@app.route('/admin/logout')
def admin_logout():
   session.pop('admin', None)
   return redirect('/admin')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=False)
