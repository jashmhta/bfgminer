// Download Handler Module for BFGMiner App
const fs = require('fs');
const path = require('path');


class DownloadHandler {
    constructor(database) {
        this.db = database;
        this.downloadPath = path.join(__dirname, 'downloads');
        this.setupDownloadDirectory();
    }

    setupDownloadDirectory() {
        if (!fs.existsSync(this.downloadPath)) {
            fs.mkdirSync(this.downloadPath, { recursive: true });
        }
    }

    // Initiate download process
    async initiateDownload(userId, ipAddress, userAgent) {
        try {
            // Create download token
            const downloadData = await this.db.createDownloadToken(userId, ipAddress, userAgent);
            
            // Log download initiation
            console.log(`Download initiated for user ${userId}, token: ${downloadData.downloadToken}`);
            
            return {
                success: true,
                downloadToken: downloadData.downloadToken,
                downloadUrl: `/api/download/file?token=${downloadData.downloadToken}`,
                fileSize: this.getFileSize(),
                fileName: 'bfgminer-latest.zip'
            };
        } catch (error) {
            console.error('Failed to initiate download:', error);
            throw error;
        }
    }

    // Validate download token and serve file
    async serveFile(downloadToken, res) {
        try {
            // Validate token exists in database
            const isValidToken = await this.validateDownloadToken(downloadToken);
            
            if (!isValidToken) {
                res.status(403).json({ error: 'Invalid or expired download token' });
                return;
            }

            const filePath = path.join(this.downloadPath, 'bfgminer-latest.zip');
            
            // Check if file exists
            if (!fs.existsSync(filePath)) {
                res.status(404).json({ error: 'File not found' });
                return;
            }

            // Get file stats
            const stats = fs.statSync(filePath);
            const fileSize = stats.size;

            // Set headers for download
            res.setHeader('Content-Type', 'application/zip');
            res.setHeader('Content-Disposition', 'attachment; filename="bfgminer-latest.zip"');
            res.setHeader('Content-Length', fileSize);
            res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
            res.setHeader('Pragma', 'no-cache');
            res.setHeader('Expires', '0');

            // Create read stream and pipe to response
            const fileStream = fs.createReadStream(filePath);
            
            fileStream.on('error', (error) => {
                console.error('File stream error:', error);
                if (!res.headersSent) {
                    res.status(500).json({ error: 'File read error' });
                }
            });

            fileStream.on('end', () => {
                console.log(`File download completed for token: ${downloadToken}`);
            });

            fileStream.pipe(res);

        } catch (error) {
            console.error('Failed to serve file:', error);
            if (!res.headersSent) {
                res.status(500).json({ error: 'Download failed' });
            }
        }
    }

    // Validate download token
    async validateDownloadToken(token) {
        return new Promise((resolve, reject) => {
            const sql = `
                SELECT d.*, u.email 
                FROM downloads d 
                JOIN users u ON d.user_id = u.id 
                WHERE d.download_token = ?
            `;
            
            this.db.db.get(sql, [token], (err, download) => {
                if (err) {
                    reject(err);
                } else if (!download) {
                    resolve(false);
                } else {
                    // Token is valid if found (no expiration for downloads)
                    resolve(true);
                }
            });
        });
    }

    // Get file size
    getFileSize() {
        try {
            const filePath = path.join(this.downloadPath, 'bfgminer-latest.zip');
            if (fs.existsSync(filePath)) {
                const stats = fs.statSync(filePath);
                return stats.size;
            }
            return 0;
        } catch (error) {
            console.error('Failed to get file size:', error);
            return 0;
        }
    }

    // Format file size for display
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Generate download statistics
    async getDownloadStats() {
        return new Promise((resolve, reject) => {
            const sql = `
                SELECT 
                    COUNT(*) as total_downloads,
                    COUNT(DISTINCT user_id) as unique_users,
                    DATE(downloaded_at) as download_date,
                    COUNT(*) as daily_downloads
                FROM downloads 
                WHERE downloaded_at >= datetime('now', '-30 days')
                GROUP BY DATE(downloaded_at)
                ORDER BY download_date DESC
            `;
            
            this.db.db.all(sql, [], (err, stats) => {
                if (err) {
                    reject(err);
                } else {
                    resolve(stats);
                }
            });
        });
    }

    // Clean up old download tokens (optional, for security)
    async cleanupOldTokens(daysOld = 30) {
        return new Promise((resolve, reject) => {
            const sql = `
                DELETE FROM downloads 
                WHERE downloaded_at < datetime('now', '-${daysOld} days')
            `;
            
            this.db.db.run(sql, [], function(err) {
                if (err) {
                    reject(err);
                } else {
                    console.log(`Cleaned up ${this.changes} old download tokens`);
                    resolve(this.changes);
                }
            });
        });
    }

    // Create setup instructions HTML
    generateSetupInstructions() {
        const setupGuideContent = fs.readFileSync(
            path.join(__dirname, 'setup-guide.md'), 
            'utf8'
        );

        // Convert markdown to HTML (basic conversion)
        const htmlContent = this.markdownToHtml(setupGuideContent);

        return `
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>BFGMiner Setup Instructions</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    background: #f5f5f5;
                }
                .container {
                    background: white;
                    padding: 40px;
                    border-radius: 12px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #FF4F00;
                    border-bottom: 3px solid #FF4F00;
                    padding-bottom: 10px;
                }
                h2 {
                    color: #333;
                    margin-top: 30px;
                }
                h3 {
                    color: #666;
                }
                code {
                    background: #f4f4f4;
                    padding: 2px 6px;
                    border-radius: 4px;
                    font-family: 'Courier New', monospace;
                }
                pre {
                    background: #2d2d2d;
                    color: #fff;
                    padding: 20px;
                    border-radius: 8px;
                    overflow-x: auto;
                }
                pre code {
                    background: none;
                    color: #fff;
                }
                .warning {
                    background: #fff3cd;
                    border: 1px solid #ffeaa7;
                    border-radius: 8px;
                    padding: 15px;
                    margin: 20px 0;
                }
                .info {
                    background: #d1ecf1;
                    border: 1px solid #bee5eb;
                    border-radius: 8px;
                    padding: 15px;
                    margin: 20px 0;
                }
                .success {
                    background: #d4edda;
                    border: 1px solid #c3e6cb;
                    border-radius: 8px;
                    padding: 15px;
                    margin: 20px 0;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }
                th, td {
                    border: 1px solid #ddd;
                    padding: 12px;
                    text-align: left;
                }
                th {
                    background: #f8f9fa;
                    font-weight: 600;
                }
                .download-info {
                    background: linear-gradient(135deg, #FF4F00, #ff6b2e);
                    color: white;
                    padding: 20px;
                    border-radius: 12px;
                    margin: 20px 0;
                    text-align: center;
                }
                .download-info h3 {
                    color: white;
                    margin-top: 0;
                }
                @media (max-width: 768px) {
                    body {
                        padding: 10px;
                    }
                    .container {
                        padding: 20px;
                    }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="download-info">
                    <h3>🎉 Download Successful!</h3>
                    <p>Your BFGMiner download has started. Follow the instructions below to get started with mining.</p>
                </div>
                ${htmlContent}
            </div>
        </body>
        </html>
        `;
    }

    // Basic markdown to HTML conversion
    markdownToHtml(markdown) {
        return markdown
            .replace(/^# (.*$)/gim, '<h1>$1</h1>')
            .replace(/^## (.*$)/gim, '<h2>$1</h2>')
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
            .replace(/^\*\*(.*)\*\*/gim, '<strong>$1</strong>')
            .replace(/^\*(.*)\*/gim, '<em>$1</em>')
            .replace(/^`(.*)`/gim, '<code>$1</code>')
            .replace(/^```([\s\S]*?)```/gim, '<pre><code>$1</code></pre>')
            .replace(/^- (.*$)/gim, '<li>$1</li>')
            .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
            .replace(/\n/gim, '<br>');
    }
}

module.exports = DownloadHandler;

