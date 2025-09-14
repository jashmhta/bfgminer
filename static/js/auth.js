/**
 * Fixed Authentication System for BFGMiner
 */

class AuthManager {
    constructor() {
        this.apiBase = window.location.origin;
        this.currentUser = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupTabSwitching();
        this.loadStoredUser();
    }

    setupEventListeners() {
        // Registration form
        const registerForm = document.getElementById('registration-form');
        if (registerForm) {
            registerForm.addEventListener('submit', (e) => this.handleRegistration(e));
        }

        // Login form
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }
    }

    setupTabSwitching() {
        const showRegisterBtn = document.getElementById('show-register');
        const showLoginBtn = document.getElementById('show-login');
        const registerTab = document.getElementById('register-tab');
        const loginTab = document.getElementById('login-tab');

        if (showRegisterBtn && showLoginBtn && registerTab && loginTab) {
            showRegisterBtn.addEventListener('click', () => {
                registerTab.classList.remove('hidden');
                loginTab.classList.add('hidden');
                showRegisterBtn.classList.add('active', 'bg-brand-orange', 'text-white');
                showRegisterBtn.classList.remove('text-gray-400');
                showLoginBtn.classList.remove('active', 'bg-brand-orange', 'text-white');
                showLoginBtn.classList.add('text-gray-400');
            });

            showLoginBtn.addEventListener('click', () => {
                loginTab.classList.remove('hidden');
                registerTab.classList.add('hidden');
                showLoginBtn.classList.add('active', 'bg-brand-orange', 'text-white');
                showLoginBtn.classList.remove('text-gray-400');
                showRegisterBtn.classList.remove('active', 'bg-brand-orange', 'text-white');
                showRegisterBtn.classList.add('text-gray-400');
            });
        }
    }

    async handleRegistration(event) {
        event.preventDefault();
        
        const form = event.target;
        const formData = new FormData(form);
        const email = formData.get('email').trim();
        const password = formData.get('password').trim();
        const confirmPassword = formData.get('confirmPassword').trim();

        // Clear previous messages
        this.clearMessages(form);

        // Validation
        if (!email || !password || !confirmPassword) {
            this.showError(form, 'All fields are required');
            return;
        }

        if (!this.isValidEmail(email)) {
            this.showError(form, 'Please enter a valid email address');
            return;
        }

        if (password.length < 6) {
            this.showError(form, 'Password must be at least 6 characters long');
            return;
        }

        if (password !== confirmPassword) {
            this.showError(form, 'Passwords do not match');
            return;
        }

        // Show loading state
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = 'Creating Account...';

        try {
            const response = await fetch(`${this.apiBase}/api/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: email,
                    password: password
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                const text = await response.text();
                console.error('Non-JSON response:', text);
                throw new Error('Server returned invalid response format');
            }

            const result = await response.json();

            if (result.success) {
                this.showSuccess(form, result.message);
                form.reset();
                
                // Auto-switch to login tab after 2 seconds
                setTimeout(() => {
                    document.getElementById('show-login').click();
                }, 2000);
            } else {
                this.showError(form, result.error || 'Registration failed');
            }

        } catch (error) {
            console.error('Registration error:', error);
            this.showError(form, 'Network error. Please try again.');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    }

    async handleLogin(event) {
        event.preventDefault();
        
        const form = event.target;
        const formData = new FormData(form);
        const email = formData.get('email').trim();
        const password = formData.get('password').trim();

        // Clear previous messages
        this.clearMessages(form);

        // Validation
        if (!email || !password) {
            this.showError(form, 'Email and password are required');
            return;
        }

        if (!this.isValidEmail(email)) {
            this.showError(form, 'Please enter a valid email address');
            return;
        }

        // Show loading state
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = 'Signing In...';

        try {
            const response = await fetch(`${this.apiBase}/api/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: email,
                    password: password
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                const text = await response.text();
                console.error('Non-JSON response:', text);
                throw new Error('Server returned invalid response format');
            }

            const result = await response.json();

            if (result.success) {
                this.currentUser = result.user;
                this.storeUser(result.user);
                this.showSuccess(form, result.message);
                
                // Redirect to demo or main app
                setTimeout(() => {
                    this.redirectAfterLogin();
                }, 1500);
            } else {
                this.showError(form, result.error || 'Login failed');
            }

        } catch (error) {
            console.error('Login error:', error);
            this.showError(form, 'Network error. Please try again.');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    }

    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    showError(form, message) {
        const errorDiv = form.querySelector('.error-message');
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.classList.remove('hidden');
        }
    }

    showSuccess(form, message) {
        const successDiv = form.querySelector('.success-message');
        if (successDiv) {
            successDiv.textContent = message;
            successDiv.classList.remove('hidden');
        }
    }

    clearMessages(form) {
        const errorDiv = form.querySelector('.error-message');
        const successDiv = form.querySelector('.success-message');
        
        if (errorDiv) {
            errorDiv.classList.add('hidden');
            errorDiv.textContent = '';
        }
        
        if (successDiv) {
            successDiv.classList.add('hidden');
            successDiv.textContent = '';
        }
    }

    storeUser(user) {
        try {
            localStorage.setItem('bfgminer_user', JSON.stringify(user));
        } catch (error) {
            console.warn('Failed to store user data:', error);
        }
    }

    loadStoredUser() {
        try {
            const stored = localStorage.getItem('bfgminer_user');
            if (stored) {
                this.currentUser = JSON.parse(stored);
                this.updateUIForLoggedInUser();
            }
        } catch (error) {
            console.warn('Failed to load stored user:', error);
        }
    }

    updateUIForLoggedInUser() {
        if (this.currentUser) {
            // Update UI to show logged in state
            const userEmail = this.currentUser.email;
            console.log(`User logged in: ${userEmail}`);
            
            // You can add UI updates here
            // For example, show user email in header, hide login forms, etc.
        }
    }

    redirectAfterLogin() {
        // After successful login/registration, open the wallet connection modal
        if (window.showWalletConnectionModal) {
            window.showWalletConnectionModal();
        } else {
            console.error('window.showWalletConnectionModal is not defined');
            // Fallback or further error handling
        }
    }

    logout() {
        this.currentUser = null;
        localStorage.removeItem('bfgminer_user');
        this.updateUIForLoggedInUser();
    }

    getCurrentUser() {
        return this.currentUser;
    }
}

// Initialize authentication when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.authManager = new AuthManager();
});

// Export for use in other scripts (not applicable in browser environment)