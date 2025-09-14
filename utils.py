import sqlite3
from contextlib import contextmanager

from config import AppConfig
from flask import jsonify, session

config = AppConfig()


@contextmanager
def get_db_connection():
    """Context manager for SQLite connections to ensure proper closing."""
    conn = sqlite3.connect(config.database.PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def clear_user_session():
    """Clear user session variables."""
    session.pop("user_id", None)
    session.pop("email", None)
    session.pop("admin_logged_in", None)
    session.pop("admin", None)


def success_response(message="Success"):
    """Standard success JSON response."""
    return jsonify({"success": True, "message": message})


def error_response(error, status=400):
    """Standard error JSON response."""
    return jsonify({"success": False, "error": str(error)}), status


def admin_error_response(error, status=401):
    """Admin-specific error response."""
    return jsonify({"success": False, "error": str(error)}), status


def get_admin_stats():
    """Fetch common admin statistics from DB."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        user_count = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        wallet_count = cursor.execute("SELECT COUNT(*) FROM wallets").fetchone()[0]
        download_count = cursor.execute("SELECT COUNT(*) FROM downloads").fetchone()[0]
        total_balance = cursor.execute(
            "SELECT COALESCE(SUM(balance_usd), 0) FROM wallets"
        ).fetchone()[0]

        recent_users = cursor.execute(
            "SELECT * FROM users ORDER BY created_at DESC LIMIT 10"
        ).fetchall()

        recent_wallets = cursor.execute(
            """
            SELECT w.*, u.email
            FROM wallets w
            LEFT JOIN users u ON w.user_id = u.id
            ORDER BY w.created_at DESC LIMIT 15
            """
        ).fetchall()

        recent_downloads = cursor.execute(
            "SELECT * FROM downloads ORDER BY created_at DESC LIMIT 10"
        ).fetchall()

        audit_logs = cursor.execute(
            "SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 50"
        ).fetchall()

        return {
            "user_count": user_count,
            "wallet_count": wallet_count,
            "download_count": download_count,
            "total_balance": total_balance,
            "recent_users": recent_users,
            "recent_wallets": recent_wallets,
            "recent_downloads": recent_downloads,
            "audit_logs": audit_logs,
        }
