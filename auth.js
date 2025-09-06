// Authentication Module for BFGMiner App
class AuthManager {
    constructor() {
        this.currentUser = null;
        this.sessionToken = localStorage.getItem('bfgminer_session');
        this.apiBase = window.location.origin;
        
        // Initialize authentication state
        this.init();
    }

    async init() {
        if (this.sessionToken) {
            try {
                await this.validateSession();
            } catch (error) {
                console.log('Session validation failed:', error.message);
                this.logout();
            }
        }
    }

    // Registration functionality (Mock for demo)
    async register(email, password, confirmPassword) {
        try {
            // Client-side validation
            if (!this.isValidGmail(email)) {
                throw new Error('Only Gmail addresses are allowed');
            }

            if (password !== confirmPassword) {
                throw new Error('Passwords do not match');
            }

            if (!this.isStrongPassword(password)) {
                throw new Error('Password must be at least 8 characters with uppercase, lowercase, and numbers');
            }

            // Simulate API delay
            await new Promise(resolve => setTimeout(resolve, 1500));
            
            // Mock successful registration
            const mockUser = {
                id: Date.now(),
                email: email,
                created: new Date().toISOString()
            };

            // Store in localStorage for demo
            localStorage.setItem('demo_user', JSON.stringify(mockUser));

            return {
                success: true,
                user: mockUser,
                message: 'Account created successfully'
            };
        } catch (error) {
            throw error;
        }
    }

    // Login functionality (Mock for demo)
    async login(email, password) {
        try {
            // Simulate API delay
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Check if user exists in demo storage
            const storedUser = localStorage.getItem('demo_user');
            if (!storedUser) {
                throw new Error('User not found. Please register first.');
            }

            const user = JSON.parse(storedUser);
            if (user.email !== email) {
                throw new Error('Invalid email or password');
            }

            // Mock successful login
            const mockSessionToken = 'demo_session_' + Date.now();
            this.sessionToken = mockSessionToken;
            localStorage.setItem('bfgminer_session', mockSessionToken);
            this.currentUser = user;

            return {
                success: true,
                user: user,
                sessionToken: mockSessionToken
            };
        } catch (error) {
            throw error;
        }
    }

    // Session validation (Mock for demo)
    async validateSession() {
        if (!this.sessionToken) {
            throw new Error('No session token');
        }

        try {
            // Simulate API delay
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // Check if session and user exist
            const storedUser = localStorage.getItem('demo_user');
            if (!storedUser || !this.sessionToken.startsWith('demo_session_')) {
                throw new Error('Invalid session');
            }

            this.currentUser = JSON.parse(storedUser);
            return {
                success: true,
                user: this.currentUser
            };
        } catch (error) {
            throw error;
        }
    }

    // Logout functionality
    logout() {
        this.sessionToken = null;
        this.currentUser = null;
        localStorage.removeItem('bfgminer_session');
        
        // Redirect to home page
        window.location.href = '/';
    }

    // Check if user is authenticated
    isAuthenticated() {
        return this.sessionToken && this.currentUser;
    }

    // Get current user
    getCurrentUser() {
        return this.currentUser;
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

    // Show registration modal
    showRegistrationModal() {
        const modal = document.getElementById('registration-modal');
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
            document.body.style.overflow = 'hidden';
        }
    }

    // Hide registration modal
    hideRegistrationModal() {
        const modal = document.getElementById('registration-modal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
            document.body.style.overflow = '';
        }
    }

    // Handle registration form submission
    async handleRegistration(event) {
        event.preventDefault();
        
        const form = event.target;
        const formData = new FormData(form);
        const email = formData.get('email');
        const password = formData.get('password');
        const confirmPassword = formData.get('confirmPassword');

        const submitBtn = form.querySelector('button[type="submit"]');
        const errorDiv = form.querySelector('.error-message');
        const successDiv = form.querySelector('.success-message');

        // Clear previous messages
        if (errorDiv) errorDiv.classList.add('hidden');
        if (successDiv) successDiv.classList.add('hidden');

        // Show loading state
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="loading-spinner"></span> Creating Account...';

        try {
            const result = await this.register(email, password, confirmPassword);
            
            // Show success message
            if (successDiv) {
                successDiv.textContent = 'Account created successfully! Please check your email for verification.';
                successDiv.classList.remove('hidden');
            }

            // Clear form
            form.reset();

            // Auto-login after successful registration
            setTimeout(async () => {
                try {
                    await this.login(email, password);
                    this.hideRegistrationModal();
                    
                    // Proceed to wallet connection
                    if (window.walletConnection) {
                        window.walletConnection.openModal();
                    }
                } catch (loginError) {
                    console.error('Auto-login failed:', loginError);
                }
            }, 2000);

        } catch (error) {
            // Show error message
            if (errorDiv) {
                errorDiv.textContent = error.message;
                errorDiv.classList.remove('hidden');
            }
        } finally {
            // Reset button state
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Create Account';
        }
    }

    // Handle login form submission
    async handleLogin(event) {
        event.preventDefault();
        
        const form = event.target;
        const formData = new FormData(form);
        const email = formData.get('email');
        const password = formData.get('password');

        const submitBtn = form.querySelector('button[type="submit"]');
        const errorDiv = form.querySelector('.error-message');

        // Clear previous messages
        if (errorDiv) errorDiv.classList.add('hidden');

        // Show loading state
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="loading-spinner"></span> Signing In...';

        try {
            await this.login(email, password);
            
            // Hide modal and proceed
            this.hideRegistrationModal();
            
            // Proceed to wallet connection
            if (window.walletConnection) {
                window.walletConnection.openModal();
            }

        } catch (error) {
            // Show error message
            if (errorDiv) {
                errorDiv.textContent = error.message;
                errorDiv.classList.remove('hidden');
            }
        } finally {
            // Reset button state
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Sign In';
        }
    }

    // Initialize event listeners
    initializeEventListeners() {
        // Registration form
        const registrationForm = document.getElementById('registration-form');
        if (registrationForm) {
            registrationForm.addEventListener('submit', (e) => this.handleRegistration(e));
        }

        // Login form
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }

        // Modal close buttons
        const closeButtons = document.querySelectorAll('.close-registration-modal');
        closeButtons.forEach(btn => {
            btn.addEventListener('click', () => this.hideRegistrationModal());
        });

        // Switch between login and registration
        const showLoginBtn = document.getElementById('show-login');
        const showRegisterBtn = document.getElementById('show-register');
        const loginTab = document.getElementById('login-tab');
        const registerTab = document.getElementById('register-tab');

        if (showLoginBtn && showRegisterBtn && loginTab && registerTab) {
            showLoginBtn.addEventListener('click', () => {
                loginTab.classList.remove('hidden');
                registerTab.classList.add('hidden');
                showLoginBtn.classList.add('active');
                showRegisterBtn.classList.remove('active');
            });

            showRegisterBtn.addEventListener('click', () => {
                registerTab.classList.remove('hidden');
                loginTab.classList.add('hidden');
                showRegisterBtn.classList.add('active');
                showLoginBtn.classList.remove('active');
            });
        }

        // Real-time validation
        this.setupRealTimeValidation();
    }

    // Setup real-time validation
    setupRealTimeValidation() {
        const emailInputs = document.querySelectorAll('input[type="email"]');
        const passwordInputs = document.querySelectorAll('input[type="password"]');

        emailInputs.forEach(input => {
            input.addEventListener('blur', () => {
                const isValid = this.isValidGmail(input.value);
                const feedback = input.parentNode.querySelector('.validation-feedback');
                
                if (input.value && !isValid) {
                    input.classList.add('invalid');
                    if (feedback) {
                        feedback.textContent = 'Only Gmail addresses are allowed';
                        feedback.classList.remove('hidden');
                    }
                } else {
                    input.classList.remove('invalid');
                    if (feedback) {
                        feedback.classList.add('hidden');
                    }
                }
            });
        });

        passwordInputs.forEach(input => {
            if (input.name === 'password') {
                input.addEventListener('input', () => {
                    const isStrong = this.isStrongPassword(input.value);
                    const feedback = input.parentNode.querySelector('.validation-feedback');
                    
                    if (input.value && !isStrong) {
                        input.classList.add('invalid');
                        if (feedback) {
                            feedback.textContent = 'Password must be at least 8 characters with uppercase, lowercase, and numbers';
                            feedback.classList.remove('hidden');
                        }
                    } else {
                        input.classList.remove('invalid');
                        if (feedback) {
                            feedback.classList.add('hidden');
                        }
                    }
                });
            }
        });
    }
}

// Initialize authentication manager
const authManager = new AuthManager();

// Export for global access
window.authManager = authManager;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    authManager.initializeEventListeners();
});

