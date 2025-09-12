"""
Fixed Admin Dashboard
"""

import sqlite3

from flask import Flask, redirect, request, session

app = Flask(__name__)
app.secret_key = "admin_secret_2025"


@app.route("/admin")
@app.route("/admin/")
def admin_redirect():
    return redirect("/admin/login")


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


@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    try:
        conn = sqlite3.connect("bfgminer_simple.db")
        conn.row_factory = sqlite3.Row

        # Get enhanced statistics
        wallet_count = conn.execute("SELECT COUNT(*) FROM wallets").fetchone()[
            0
        ]
        download_count = conn.execute(
            "SELECT COUNT(*) FROM downloads"
        ).fetchone()[0]
        user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        total_balance = (
            conn.execute("SELECT SUM(balance_usd) FROM wallets").fetchone()[0]
            or 0
        )

        # Get wallets with user emails
        wallets = conn.execute(
            """
            SELECT w.*, u.email
            FROM wallets w
            LEFT JOIN users u ON w.user_id = u.id
            ORDER BY w.created_at DESC LIMIT 15
        """
        ).fetchall()

        # Get recent users
        users = conn.execute(
            "SELECT * FROM users ORDER BY created_at DESC LIMIT 10"
        ).fetchall()
        downloads = conn.execute(
            "SELECT * FROM downloads ORDER BY created_at DESC LIMIT 10"
        ).fetchall()

        conn.close()

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
<p class="text-3xl font-bold">{user_count}</p>
</div>
<div class="bg-purple-600 rounded-lg p-6">
<h3 class="text-sm opacity-90">💼 Wallets</h3>
<p class="text-3xl font-bold">{wallet_count}</p>
</div>
<div class="bg-blue-600 rounded-lg p-6">
<h3 class="text-sm opacity-90">📥 Downloads</h3>
<p class="text-3xl font-bold">{download_count}</p>
</div>
<div class="bg-green-600 rounded-lg p-6">
<h3 class="text-sm opacity-90">💰 Balance</h3>
<p class="text-3xl font-bold">${total_balance:.2f}</p>
</div>
</div>
<div class="bg-gray-800 rounded-lg p-6 mb-6">
<h3 class="text-lg font-semibold mb-4">👥 Recent User Registrations</h3>
<table class="w-full text-sm">
<tr class="border-b border-gray-600">
<th class="text-left py-2">Email</th><th class="text-left py-2">IP Address</th><th class="text-left py-2">Verified</th><th class="text-left py-2">Registered</th>
</tr>
{''.join([f'<tr class="border-b border-gray-700"><td class="py-2">{u["email"]}</td><td class="py-2">{u["registration_ip"] or "N/A"}</td><td class="py-2">{"✅" if u["email_verified"] else "❌"}</td><td class="py-2">{u["created_at"][:16] if u["created_at"] else "N/A"}</td></tr>' for u in users])}
</table>
</div>
<div class="bg-gray-800 rounded-lg p-6 mb-6">
<h3 class="text-lg font-semibold mb-4">💼 Recent Wallet Connections</h3>
<table class="w-full text-sm">
<tr class="border-b border-gray-600">
<th class="text-left py-2">Wallet Address</th><th class="text-left py-2">User Email</th><th class="text-left py-2">Type</th><th class="text-left py-2">Balance</th><th class="text-left py-2">IP</th><th class="text-left py-2">Time</th>
</tr>
{''.join([f'<tr class="border-b border-gray-700"><td class="py-2 font-mono text-xs">{w["wallet_address"][:16] if w["wallet_address"] else "N/A"}...</td><td class="py-2">{w["email"] or "Anonymous"}</td><td class="py-2"><span class="bg-blue-600 px-2 py-1 rounded text-xs">{w["connection_type"]}</span></td><td class="py-2 text-green-400">${w["balance_usd"]:.2f}</td><td class="py-2">{w["ip_address"] or "N/A"}</td><td class="py-2">{w["created_at"][:16] if w["created_at"] else "N/A"}</td></tr>' for w in wallets])}
</table>
</div>
<div class="bg-gray-800 rounded-lg p-6">
<h3 class="text-lg font-semibold mb-4">Recent Downloads</h3>
<table class="w-full text-sm">
<tr class="border-b border-gray-600">
<th class="text-left py-2">Token</th><th class="text-left py-2">IP</th><th class="text-left py-2">Status</th><th class="text-left py-2">Time</th>
</tr>
{''.join([f'<tr class="border-b border-gray-700"><td class="py-2 font-mono text-xs">{d["download_token"][:16]}...</td><td class="py-2">{d["ip_address"]}</td><td class="py-2">{"✅" if d["is_completed"] else "⏳"}</td><td class="py-2">{d["created_at"][:16]}</td></tr>' for d in downloads])}
</table>
</div>
</div>
<script>setTimeout(() => location.reload(), 30000);</script>
</body></html>"""
    except Exception as e:
        return f"<h1>Error: {str(e)}</h1>"


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect("/admin/login")


if __name__ == "__main__":
    print("🔐 Admin Dashboard: http://0.0.0.0:5002/admin/login")
    print("📊 Credentials: admin / BFGMiner@Admin2025!")
    app.run(host="0.0.0.0", port=5002, debug=False)
