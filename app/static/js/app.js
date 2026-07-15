// ArtiLogix Shared App JS - Auth Guard, Toast & Layout System

// Backend base URL. During local dev the frontend and backend run on
// different ports/servers (no reverse proxy yet), so every fetch()/
// EventSource call needs this prefix or it silently resolves against the
// frontend's own origin instead of the API. Once nginx serves both from
// the same origin (see nginx.conf), set this to '' (empty string).
window.API_BASE = 'http://localhost:8001';

// Initialize Theme immediately on script load to avoid page flash
(function() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
})();

document.addEventListener('DOMContentLoaded', () => {
    // Inject lucide icons if library is loaded
    if (window.lucide) {
        lucide.createIcons();
    }
    initThemeToggle();
});

// Toast System
function showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    // Choose icon based on type
    let icon = 'info';
    if (type === 'success') icon = 'check-circle';
    if (type === 'warning') icon = 'alert-triangle';
    if (type === 'danger') icon = 'x-circle';

    toast.innerHTML = `
        <i data-lucide="${icon}" class="toast-icon"></i>
        <div class="toast-message">${message}</div>
    `;

    container.appendChild(toast);
    
    if (window.lucide) {
        lucide.createIcons({
            attrs: { class: 'lucide' },
            nameAttr: 'data-lucide',
            node: toast
        });
    }

    // Slide out and remove
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(20px) scale(0.95)';
        toast.style.transition = 'all 300ms cubic-bezier(0.16, 1, 0.3, 1)';
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 4000);
}

// Authentication Check Guard
function checkAuth(allowedRoles = null) {
    const token = localStorage.getItem('access_token');
    const role = localStorage.getItem('user_role');
    const email = localStorage.getItem('user_email');

    // If no token, redirect to login
    if (!token || !role) {
        localStorage.clear();
        if (!window.location.pathname.endsWith('/login.html')) {
            window.location.href = 'login.html';
        }
        return false;
    }

    // Role specific route check
    if (allowedRoles) {
        const rolesArray = Array.isArray(allowedRoles) ? allowedRoles : [allowedRoles];
        if (!rolesArray.includes(role)) {
            // Redirect to correct dashboard based on actual role
            if (role === 'logistics') {
                window.location.href = 'dashboard.html';
            } else if (role === 'marketplace') {
                window.location.href = 'marketplace.html';
            } else if (role === 'driver') {
                window.location.href = 'driver.html';
            } else if (role === 'admin') {
                window.location.href = 'admin.html';
            }
            return false;
        }
    }
    
    return { token, role, email };
}

// Theme Handler
function initThemeToggle() {
    const toggleBtn = document.getElementById('theme-toggle');
    if (!toggleBtn) return;

    toggleBtn.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        
        // Update Lucide icon
        updateThemeIcon(newTheme);
        
        // Dispatch custom event for charts to redraw if needed
        window.dispatchEvent(new CustomEvent('themechanged', { detail: { theme: newTheme } }));
    });

    // Match initial icon
    const theme = document.documentElement.getAttribute('data-theme') || 'dark';
    updateThemeIcon(theme);
}

function updateThemeIcon(theme) {
    const toggleBtn = document.getElementById('theme-toggle');
    if (!toggleBtn) return;
    
    if (theme === 'light') {
        toggleBtn.innerHTML = '<i data-lucide="moon"></i>';
    } else {
        toggleBtn.innerHTML = '<i data-lucide="sun"></i>';
    }
    
    if (window.lucide) {
        lucide.createIcons({ node: toggleBtn });
    }
}

// Logout handler
function logout() {
    localStorage.clear();
    showToast('Logged out successfully', 'success');
    setTimeout(() => {
        window.location.href = 'login.html';
    }, 500);
}

// Format currency
function formatAZN(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'AZN',
        minimumFractionDigits: 2
    }).format(amount).replace('AZN', '₼');
}

// Format numbers
function formatNumber(number) {
    return new Intl.NumberFormat('en-US').format(number);
}