const API_URL = '/api';

// Theme Toggle
const toggleTheme = () => {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
};

// Initialize Theme
const initTheme = () => {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
};

// Toast Notification
const showToast = (message) => {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
};

// Authentication state
const checkAuth = () => {
    const token = localStorage.getItem('token');
    const user = JSON.parse(localStorage.getItem('user'));
    return { token, user };
};

// Update Navbar based on Auth
const updateNavbar = () => {
    const { token, user } = checkAuth();
    const navLinks = document.getElementById('nav-links');
    if (!navLinks) return;

    if (token && user) {
        navLinks.innerHTML = `
            <a href="/">Home</a>
            <a href="/dashboard">Dashboard</a>
            ${user.role === 'admin' ? '<a href="/admin">Admin</a>' : ''}
            <span style="font-weight: bold; margin-left:1rem;">Hi, ${user.name}</span>
            <button onclick="logout()" class="btn" style="margin-left: 1rem; padding: 0.5rem 1rem;">Logout</button>
            <button class="theme-toggle" onclick="toggleTheme()">🌓</button>
        `;
    } else {
        navLinks.innerHTML = `
            <a href="/">Home</a>
            <a href="/login">Login</a>
            <a href="/signup" class="btn" style="color:white; padding: 0.5rem 1rem;">Sign Up</a>
            <button class="theme-toggle" onclick="toggleTheme()">🌓</button>
        `;
    }
};

const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
};

// Captcha Helper
const generateCaptcha = () => {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%';
    let captcha = '';
    for (let i = 0; i < 6; i++) {
        captcha += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return captcha;
};

// Init
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    updateNavbar();
});
