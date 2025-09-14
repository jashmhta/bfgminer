document.addEventListener('DOMContentLoaded', () => {
    lucide.createIcons();
    
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
        }
    };

    // Update slot counter initially and every 10 seconds
    updateSlotCounter();
    setInterval(updateSlotCounter, 10000);

    const walletModal = document.getElementById('wallet-modal');
    const setupInstructionsModal = document.getElementById('setup-instructions-modal');
    const registrationModal = document.getElementById('registration-modal');
    const demoAnim = new DemoAnimation();






    // Demo trigger handlers
    const downloadTriggers = document.querySelectorAll(".demo-trigger");
    downloadTriggers.forEach(trigger => {
        trigger.addEventListener("click", async (e) => {
            e.preventDefault();
            try {
                const response = await fetch("/api/download/initiate", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ user_id: 1 })
                });
                const data = await response.json();
                if (data.success) {
                    demoAnim.startDemo();
                } else {
                    alert("Download initiation failed: " + (data.error || "Unknown error"));
                }
            } catch (error) {
                alert("Network error: " + error.message);
                registrationModal.classList.remove("hidden");
                registrationModal.classList.add("flex");
            }
        });
    });

    // Modal close handlers
    const closeRegistrationModalBtns = document.querySelectorAll(".close-registration-modal");
    const closeWalletModalBtns = document.querySelectorAll(".close-wallet-modal");
    const closeInstructionsModalBtns = document.querySelectorAll(".close-instructions-modal");

    closeRegistrationModalBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            registrationModal.classList.add("hidden");
            registrationModal.classList.remove("flex");
        });
    });

    closeWalletModalBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            walletModal.classList.add("hidden");
            walletModal.classList.remove("flex");
        });
    });

    closeInstructionsModalBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            setupInstructionsModal.classList.add("hidden");
            setupInstructionsModal.classList.remove("flex");
        });
    });
});
}