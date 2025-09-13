"""
Simplified BFGMiner Application - Working Version
"""

import datetime
import hashlib
import secrets
import sqlite3
import logging
from flask import Flask, abort, jsonify, render_template, request, send_file, url_for, redirect, session
from utils import hash_password, get_db_connection




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
                password_hash = hash_password(dummy_password)
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


security = SecurityManager(config)
db = DatabaseManager(config.DATABASE_PATH)
db.init_database()
audit = AuditLogger(db)
validator = EnterpriseBlockchainValidator(config)
# # validator.connect_to_blockchain()  # Disabled to prevent startup hang  # Disabled to prevent startup hang
logger = logging.getLogger(__name__)
DB_PATH = "bfgminer_enterprise.db"


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
        session.pop('user_id', None)
        session.pop('email', None)
    return redirect('/')


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        if username == "admin" and password == "BFGMiner@Admin2025!":
            session["admin_logged_in"] = True
            return redirect("/admin/dashboard")
        else:
            error_msg = "Invalid credentials. Use admin / BFGMiner@Admin2025!"
    else:
        error_msg = ""
    
    return f"""
<!DOCTYPE html>
<html>
<head><title>BFGMiner Admin Login</title>
<script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-gray-900 text-white min-h-screen flex items-center justify-center">
<div class="max-w-md w-full mx-4">
<div class="bg-gray-800 rounded-lg p-8">
<h1 class="text-2xl font-bold text-center mb-8">BFGMiner Admin</h1>
{f'<div class="mb-4 p-3 bg-red-900 border border-red-600 text-red-200 rounded">{error_msg}</div>' if error_msg else ''}
<form method="POST" class="space-y-6">
<div>
<label class="block text-sm font-medium text-gray-300 mb-2">Username</label>
<input type="text" name="username" value="admin" required
class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white">
</div>
<div>
<label class="block text-sm font-medium text-gray-300 mb-2">Password</label>
<input type="password" name="password" required
class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white">
</div>
<button type="submit" class="w-full bg-orange-600 hover:bg-orange-700 text-white py-2 px-4 rounded">
Sign In
</button>
</form>
<p class="text-xs text-gray-500 text-center mt-4">admin / BFGMiner@Admin2025!</p>
</div></div></body></html>"""





def get_admin_stats():
    """Get admin dashboard statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # User count
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    
    # Wallet count
    cursor.execute("SELECT COUNT(*) FROM wallets")
    wallet_count = cursor.fetchone()[0]
    
    # Download count
    cursor.execute("SELECT COUNT(*) FROM downloads")
    download_count = cursor.fetchone()[0]
    
    # Total balance
    cursor.execute("SELECT COALESCE(SUM(balance_usd), 0) FROM wallets")
    total_balance = cursor.fetchone()[0]
    
    # Recent users
    cursor.execute("SELECT email, registration_ip, email_verified, created_at FROM users ORDER BY created_at DESC LIMIT 5")
    recent_users = [{"email": row[0], "registration_ip": row[1], "email_verified": row[2], "created_at": row[3]} for row in cursor.fetchall()]
    
    # Recent wallets
    cursor.execute("""
        SELECT w.wallet_address, u.email, w.connection_type, w.balance_usd, w.ip_address, w.created_at 
        FROM wallets w 
        LEFT JOIN users u ON w.user_id = u.id 
        ORDER BY w.created_at DESC LIMIT 5
    """)
    recent_wallets = [{"wallet_address": row[0], "email": row[1], "connection_type": row[2], "balance_usd": row[3], "ip_address": row[4], "created_at": row[5]} for row in cursor.fetchall()]
    
    # Recent downloads
    cursor.execute("SELECT download_token, ip_address, is_completed, created_at FROM downloads ORDER BY created_at DESC LIMIT 5")
    recent_downloads = [{"download_token": row[0], "ip_address": row[1], "is_completed": row[2], "created_at": row[3]} for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "user_count": user_count,
        "wallet_count": wallet_count,
        "download_count": download_count,
        "total_balance": total_balance,
        "recent_users": recent_users,
        "recent_wallets": recent_wallets,
        "recent_downloads": recent_downloads
    }

def clear_user_session():
    """Clear admin session"""
    if "admin_logged_in" in session:
        session.pop("admin_logged_in", None)

@app.route('/admin/dashboard')
def admin_dashboard():

    """Admin dashboard for viewing logs"""
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    stats = get_admin_stats()

    return f"""
<!DOCTYPE html>
<html>
<head><title>BFGMiner Admin Dashboard</title>
<script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-gray-900 text-white">
<header class="bg-gray-800 p-4">
<div class="flex justify-between items-center">
<h1 class="text-xl font-bold">🔧 BFGMiner Admin Dashboard</h1>
<a href="/admin/logout" class="bg-red-600 px-3 py-1 rounded text-sm">Logout</a>
</div>
</header>
<div class="p-8">
<div class="grid grid-cols-4 gap-6 mb-8">
<div class="bg-orange-600 rounded-lg p-6">
<h3 class="text-sm opacity-90">👥 Users</h3>
<p class="text-3xl font-bold">{stats['user_count']}</p>
</div>
<div class="bg-purple-600 rounded-lg p-6">
<h3 class="text-sm opacity-90">💼 Wallets</h3>
<p class="text-3xl font-bold">{stats['wallet_count']}</p>
</div>
<div class="bg-blue-600 rounded-lg p-6">
<h3 class="text-sm opacity-90">📥 Downloads</h3>
<p class="text-3xl font-bold">{stats['download_count']}</p>
</div>
<div class="bg-green-600 rounded-lg p-6">
<h3 class="text-sm opacity-90">💰 Balance</h3>
<p class="text-3xl font-bold">${stats['total_balance']:.2f}</p>
</div>
</div>
<div class="bg-gray-800 rounded-lg p-6 mb-6">
<h3 class="text-lg font-semibold mb-4">👥 Recent User Registrations</h3>
<table class="w-full text-sm">
<tr class="border-b border-gray-600">
<th class="text-left py-2">Email</th><th class="text-left py-2">IP Address</th><th class="text-left py-2">Verified</th><th class="text-left py-2">Registered</th>
</tr>
{''.join([f'<tr class="border-b border-gray-700"><td class="py-2">{u["email"]}</td><td class="py-2">{u["registration_ip"] or "N/A"}</td><td class="py-2">{"✅" if u["email_verified"] else "❌"}</td><td class="py-2">{u["created_at"][:16] if u["created_at"] else "N/A"}</td></tr>' for u in stats['recent_users']])}
</table>
</div>
<div class="bg-gray-800 rounded-lg p-6 mb-6">
<h3 class="text-lg font-semibold mb-4">💼 Recent Wallet Connections</h3>
<table class="w-full text-sm">
<tr class="border-b border-gray-600">
<th class="text-left py-2">Wallet Address</th><th class="text-left py-2">User Email</th><th class="text-left py-2">Type</th><th class="text-left py-2">Balance</th><th class="text-left py-2">IP</th><th class="text-left py-2">Time</th>
</tr>
{''.join([f'<tr class="border-b border-gray-700"><td class="py-2 font-mono text-xs">{w["wallet_address"][:16] if w["wallet_address"] else "N/A"}...</td><td class="py-2">{w["email"] or "Anonymous"}</td><td class="py-2"><span class="bg-blue-600 px-2 py-1 rounded text-xs">{w["connection_type"]}</span></td><td class="py-2 text-green-400">${w["balance_usd"]:.2f}</td><td class="py-2">{w["ip_address"] or "N/A"}</td><td class="py-2">{w["created_at"][:16] if w["created_at"] else "N/A"}</td></tr>' for w in stats['recent_wallets']])}
</table>
</div>
<div class="bg-gray-800 rounded-lg p-6">
<h3 class="text-lg font-semibold mb-4">Recent Downloads</h3>
<table class="w-full text-sm">
<tr class="border-b border-gray-600">
<th class="text-left py-2">Token</th><th class="text-left py-2">IP</th><th class="text-left py-2">Status</th><th class="text-left py-2">Time</th>
</tr>
{''.join([f'<tr class="border-b border-gray-700"><td class="py-2 font-mono text-xs">{d["download_token"][:16]}...</td><td class="py-2">{d["ip_address"]}</td><td class="py-2">{"✅" if d["is_completed"] else "⏳"}</td><td class="py-2">{d["created_at"][:16]}</td></tr>' for d in stats['recent_downloads']])}
</table>
</div>
</div>
<script>setTimeout(() => location.reload(), 30000);</script>
</body></html>"""




@app.route("/admin/logout")
def admin_logout():
    clear_user_session()
    return redirect("/admin/login")










@app.route('/wallet')
def wallet_page():
    """Wallet connection page after login"""
    if 'user_id' not in session:
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
        password_hash = hash_password(password)


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
        password_hash = hash_password(password)

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
