from flask import Blueprint, render_template, session, redirect, url_for, request, flash
import sqlite3

admin_dashboard_bp = Blueprint('admin_dashboard', __name__, template_folder='templates')

DB_PATH = 'bfgminer.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@admin_dashboard_bp.route('/admin/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'Admin123!':
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard.dashboard'))
        else:
            flash('Invalid credentials')
    return render_template('admin_login.html')

@admin_dashboard_bp.route('/admin/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_dashboard.login'))

@admin_dashboard_bp.route('/admin/dashboard')
def dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard.login'))
    
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    wallets = conn.execute('SELECT * FROM wallets').fetchall()
    downloads = conn.execute('SELECT * FROM downloads').fetchall()
    conn.close()
    
    return render_template('admin_dashboard.html', users=users, wallets=wallets, downloads=downloads)
