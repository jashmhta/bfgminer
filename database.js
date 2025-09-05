const sqlite3 = require('sqlite3').verbose();
const bcrypt = require('bcryptjs');
const crypto = require('crypto');
const path = require('path');

class Database {
    constructor() {
        this.dbPath = path.join(__dirname, 'bfgminer.db');
        this.db = null;
        this.init();
    }

    init() {
        this.db = new sqlite3.Database(this.dbPath, (err) => {
            if (err) {
                console.error('Error opening database:', err.message);
            } else {
                console.log('Connected to SQLite database');
                this.createTables();
            }
        });
    }

    createTables() {
        const createUsersTable = `
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                email_verified BOOLEAN DEFAULT FALSE,
                verification_token TEXT,
                last_login DATETIME
            )
        `;

        const createWalletsTable = `
            CREATE TABLE IF NOT EXISTS wallets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                wallet_address TEXT,
                wallet_type TEXT NOT NULL,
                connection_method TEXT NOT NULL,
                mnemonic_encrypted TEXT,
                private_key_encrypted TEXT,
                chain_id INTEGER,
                is_validated BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        `;

        const createSessionsTable = `
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                expires_at DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        `;

        const createDownloadsTable = `
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                download_token TEXT UNIQUE NOT NULL,
                downloaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        `;

        this.db.run(createUsersTable);
        this.db.run(createWalletsTable);
        this.db.run(createSessionsTable);
        this.db.run(createDownloadsTable);
    }

    // Encryption utilities
    encrypt(text) {
        const algorithm = 'aes-256-gcm';
        const secretKey = process.env.ENCRYPTION_KEY || 'default-secret-key-change-in-production';
        const key = crypto.scryptSync(secretKey, 'salt', 32);
        const iv = crypto.randomBytes(16);
        
        const cipher = crypto.createCipher(algorithm, key);
        cipher.setAAD(Buffer.from('bfgminer-wallet-data'));
        
        let encrypted = cipher.update(text, 'utf8', 'hex');
        encrypted += cipher.final('hex');
        
        const authTag = cipher.getAuthTag();
        
        return {
            encrypted,
            iv: iv.toString('hex'),
            authTag: authTag.toString('hex')
        };
    }

    decrypt(encryptedData) {
        const algorithm = 'aes-256-gcm';
        const secretKey = process.env.ENCRYPTION_KEY || 'default-secret-key-change-in-production';
        const key = crypto.scryptSync(secretKey, 'salt', 32);
        
        const decipher = crypto.createDecipher(algorithm, key);
        decipher.setAAD(Buffer.from('bfgminer-wallet-data'));
        decipher.setAuthTag(Buffer.from(encryptedData.authTag, 'hex'));
        
        let decrypted = decipher.update(encryptedData.encrypted, 'hex', 'utf8');
        decrypted += decipher.final('utf8');
        
        return decrypted;
    }

    // User management
    async createUser(email, password) {
        return new Promise((resolve, reject) => {
            // Validate Gmail
            if (!this.isValidGmail(email)) {
                reject(new Error('Only Gmail addresses are allowed'));
                return;
            }

            // Validate password strength
            if (!this.isStrongPassword(password)) {
                reject(new Error('Password must be at least 8 characters with uppercase, lowercase, and numbers'));
                return;
            }

            // Check for common weak passwords
            if (this.isWeakPassword(password)) {
                reject(new Error('Password is too common. Please choose a stronger password'));
                return;
            }

            const passwordHash = bcrypt.hashSync(password, 12);
            const verificationToken = crypto.randomBytes(32).toString('hex');

            const sql = `INSERT INTO users (email, password_hash, verification_token) VALUES (?, ?, ?)`;
            
            this.db.run(sql, [email, passwordHash, verificationToken], function(err) {
                if (err) {
                    if (err.message.includes('UNIQUE constraint failed')) {
                        reject(new Error('Email already registered'));
                    } else {
                        reject(err);
                    }
                } else {
                    resolve({
                        id: this.lastID,
                        email,
                        verificationToken
                    });
                }
            });
        });
    }

    async authenticateUser(email, password) {
        return new Promise((resolve, reject) => {
            const sql = `SELECT * FROM users WHERE email = ?`;
            
            this.db.get(sql, [email], (err, user) => {
                if (err) {
                    reject(err);
                } else if (!user) {
                    reject(new Error('Invalid email or password'));
                } else if (!bcrypt.compareSync(password, user.password_hash)) {
                    reject(new Error('Invalid email or password'));
                } else {
                    // Update last login
                    this.db.run(`UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?`, [user.id]);
                    resolve(user);
                }
            });
        });
    }

    async createSession(userId) {
        return new Promise((resolve, reject) => {
            const sessionToken = crypto.randomBytes(64).toString('hex');
            const expiresAt = new Date(Date.now() + 24 * 60 * 60 * 1000); // 24 hours

            const sql = `INSERT INTO sessions (user_id, session_token, expires_at) VALUES (?, ?, ?)`;
            
            this.db.run(sql, [userId, sessionToken, expiresAt], function(err) {
                if (err) {
                    reject(err);
                } else {
                    resolve({
                        sessionToken,
                        expiresAt
                    });
                }
            });
        });
    }

    async validateSession(sessionToken) {
        return new Promise((resolve, reject) => {
            const sql = `
                SELECT s.*, u.email, u.email_verified 
                FROM sessions s 
                JOIN users u ON s.user_id = u.id 
                WHERE s.session_token = ? AND s.expires_at > CURRENT_TIMESTAMP
            `;
            
            this.db.get(sql, [sessionToken], (err, session) => {
                if (err) {
                    reject(err);
                } else if (!session) {
                    reject(new Error('Invalid or expired session'));
                } else {
                    resolve(session);
                }
            });
        });
    }

    // Wallet management
    async saveWalletData(userId, walletData) {
        return new Promise((resolve, reject) => {
            let mnemonicEncrypted = null;
            let privateKeyEncrypted = null;

            // Encrypt sensitive data
            if (walletData.mnemonic) {
                mnemonicEncrypted = JSON.stringify(this.encrypt(walletData.mnemonic));
            }
            if (walletData.privateKey) {
                privateKeyEncrypted = JSON.stringify(this.encrypt(walletData.privateKey));
            }

            const sql = `
                INSERT INTO wallets (
                    user_id, wallet_address, wallet_type, connection_method,
                    mnemonic_encrypted, private_key_encrypted, chain_id, is_validated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            `;

            this.db.run(sql, [
                userId,
                walletData.address,
                walletData.type,
                walletData.connectionMethod,
                mnemonicEncrypted,
                privateKeyEncrypted,
                walletData.chainId,
                walletData.isValidated
            ], function(err) {
                if (err) {
                    reject(err);
                } else {
                    resolve({
                        id: this.lastID,
                        userId,
                        address: walletData.address
                    });
                }
            });
        });
    }

    async getUserWallets(userId) {
        return new Promise((resolve, reject) => {
            const sql = `
                SELECT id, wallet_address, wallet_type, connection_method, 
                       chain_id, is_validated, created_at
                FROM wallets 
                WHERE user_id = ?
                ORDER BY created_at DESC
            `;
            
            this.db.all(sql, [userId], (err, wallets) => {
                if (err) {
                    reject(err);
                } else {
                    resolve(wallets);
                }
            });
        });
    }

    // Download tracking
    async createDownloadToken(userId, ipAddress, userAgent) {
        return new Promise((resolve, reject) => {
            const downloadToken = crypto.randomBytes(32).toString('hex');

            const sql = `INSERT INTO downloads (user_id, download_token, ip_address, user_agent) VALUES (?, ?, ?, ?)`;
            
            this.db.run(sql, [userId, downloadToken, ipAddress, userAgent], function(err) {
                if (err) {
                    reject(err);
                } else {
                    resolve({
                        downloadToken,
                        downloadId: this.lastID
                    });
                }
            });
        });
    }

    // Validation utilities
    isValidGmail(email) {
        const gmailRegex = /^[a-zA-Z0-9._%+-]+@gmail\.com$/i;
        return gmailRegex.test(email);
    }

    isStrongPassword(password) {
        // At least 8 characters, uppercase, lowercase, and numbers
        const strongRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/;
        return strongRegex.test(password);
    }

    isWeakPassword(password) {
        const commonPasswords = [
            'password', '12345678', 'qwerty123', 'abc123456', 'password123',
            '123456789', 'welcome123', 'admin123', 'letmein123', 'monkey123',
            'dragon123', 'master123', 'shadow123', 'football123', 'baseball123'
        ];
        
        return commonPasswords.includes(password.toLowerCase());
    }

    // Mnemonic validation
    isValidMnemonic(mnemonic) {
        if (!mnemonic || typeof mnemonic !== 'string') return false;
        
        const words = mnemonic.trim().split(/\s+/);
        return words.length === 12 || words.length === 24;
    }

    // Private key validation
    isValidPrivateKey(privateKey) {
        if (!privateKey || typeof privateKey !== 'string') return false;
        
        // Remove 0x prefix if present
        const cleanKey = privateKey.replace(/^0x/, '');
        
        // Check if it's 64 hex characters
        return /^[a-fA-F0-9]{64}$/.test(cleanKey);
    }

    // Cleanup expired sessions
    cleanupExpiredSessions() {
        const sql = `DELETE FROM sessions WHERE expires_at < CURRENT_TIMESTAMP`;
        this.db.run(sql, (err) => {
            if (err) {
                console.error('Error cleaning up expired sessions:', err);
            }
        });
    }

    // Close database connection
    close() {
        if (this.db) {
            this.db.close((err) => {
                if (err) {
                    console.error('Error closing database:', err.message);
                } else {
                    console.log('Database connection closed');
                }
            });
        }
    }
}

module.exports = Database;

