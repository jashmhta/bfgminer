from flask import Flask, render_template, session, request, redirect, url_for, jsonify
from flask_session import Session
import sqlite3
from datetime import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash
from utils import get_db_connection

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-key-change-in-prod")
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

ADMIN_EMAIL = "admin@bfgminer.com"
ADMIN_PASSWORD_HASH = generate_password_hash("admin123")

def get_db_connection():
    conn = sqlite3.connect("bfgminer_enterprise.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        if email == ADMIN_EMAIL and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        return render_template("admin_login.html", error="Invalid credentials")
    return render_template("admin_login.html")

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users ORDER BY created_at DESC LIMIT 50")
        users = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute("""
            SELECT w.*, u.email, d.method as connection_method, d.balance 
            FROM wallets w 
            LEFT JOIN users u ON w.user_id = u.id 
            LEFT JOIN downloads d ON w.user_id = d.user_id 
            ORDER BY w.created_at DESC LIMIT 50
        """)
        wallets = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM downloads WHERE is_completed = 1")
        total_downloads = cursor.fetchone()[0]
        cursor.execute("SELECT SUM(balance) FROM downloads WHERE balance > 0")
        total_balance = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        slots_left = max(0, 1000 - user_count)
    
    return render_template("admin_dashboard.html", 
                         users=users, wallets=wallets, 
                         total_users=total_users, total_downloads=total_downloads, 
                         total_balance=total_balance, slots_left=slots_left)

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=False)

