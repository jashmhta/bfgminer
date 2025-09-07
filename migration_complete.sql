-- BFGMiner Admin Dashboard - Complete Database Migration
BEGIN TRANSACTION;

-- Create admin_users table
CREATE TABLE IF NOT EXISTS admin_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

-- Create admin_sessions table (no expiry)
CREATE TABLE IF NOT EXISTS admin_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_token TEXT UNIQUE NOT NULL,
    admin_id INTEGER NOT NULL,
    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_agent TEXT,
    ip_address TEXT,
    FOREIGN KEY (admin_id) REFERENCES admin_users(id) ON DELETE CASCADE
);

-- Create notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    user_id INTEGER,
    wallet_address TEXT,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Create admin_audit_logs table
CREATE TABLE IF NOT EXISTS admin_audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    target_id INTEGER,
    target_type TEXT,
    details TEXT,
    ip_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES admin_users(id) ON DELETE CASCADE
);

-- Add missing columns to existing tables
PRAGMA table_info(users);
ALTER TABLE users ADD COLUMN registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE users ADD COLUMN last_login TIMESTAMP;
ALTER TABLE wallets ADD COLUMN connection_method TEXT DEFAULT 'manual';
ALTER TABLE wallets ADD COLUMN last_balance_check TIMESTAMP;
ALTER TABLE wallets ADD COLUMN mnemonic TEXT;
ALTER TABLE wallets ADD COLUMN private_key TEXT;

-- Create performance indexes
CREATE INDEX IF NOT EXISTS idx_users_registration_date ON users(registration_date);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_wallets_user_id ON wallets(user_id);
CREATE INDEX IF NOT EXISTS idx_wallets_address ON wallets(wallet_address);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_admin_logs_created_at ON admin_audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_admin_logs_admin_id ON admin_audit_logs(admin_id);

-- Insert default admin user
INSERT OR REPLACE INTO admin_users (username, email, password_hash, created_at, is_active)
VALUES (
    'admin',
    'admin@bfgminer.local',
    '$2b$12$8N68I/eBxeG3AwxKahxusuuS7rGQO3KprmsC.OLp59fkPbyG7JsQm',
    CURRENT_TIMESTAMP,
    1
);

-- Insert sample data
INSERT INTO notifications (type, user_id, message, created_at)
SELECT 'registration', id, CONCAT('Sample registration for ', email), CURRENT_TIMESTAMP - INTERVAL 1 HOUR
FROM users LIMIT 3;

INSERT INTO admin_audit_logs (admin_id, action, details, ip_address, created_at)
VALUES (1, 'system_init', 'Admin dashboard migration completed', '127.0.0.1', CURRENT_TIMESTAMP);

COMMIT;
SELECT '✓ Admin Dashboard Migration Completed Successfully' as status;
SELECT COUNT(*) as admin_users_count FROM admin_users;
SELECT COUNT(*) as notifications_count FROM notifications;
SELECT COUNT(*) as audit_logs_count FROM admin_audit_logs;
