// ArtiLogix Login Page Controller

document.addEventListener('DOMContentLoaded', () => {
    initCanvasAnimation();
    initPasswordToggle();
    initDemoHelpers();
    initAuthForm();
    initChangePasswordForm();
});

// 1. High-Tech Network Particle Canvas Animation
function initCanvasAnimation() {
    const canvas = document.getElementById('visual-canvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let width = canvas.width = canvas.offsetWidth;
    let height = canvas.height = canvas.offsetHeight;

    // Resize listener
    window.addEventListener('resize', () => {
        width = canvas.width = canvas.offsetWidth;
        height = canvas.height = canvas.offsetHeight;
    });

    const particles = [];
    const maxParticles = 65;
    
    // Mouse state
    const mouse = { x: null, y: null, radius: 150 };
    window.addEventListener('mousemove', (e) => {
        const rect = canvas.getBoundingClientRect();
        mouse.x = e.clientX - rect.left;
        mouse.y = e.clientY - rect.top;
    });

    window.addEventListener('mouseleave', () => {
        mouse.x = null;
        mouse.y = null;
    });

    class Particle {
        constructor() {
            this.x = Math.random() * width;
            this.y = Math.random() * height;
            this.vx = (Math.random() - 0.5) * 0.6;
            this.vy = (Math.random() - 0.5) * 0.6;
            this.radius = Math.random() * 2.5 + 1.5;
            this.color = Math.random() > 0.4 ? '#8B5CF6' : '#7C3AED'; // Purple theme
        }

        update() {
            this.x += this.vx;
            this.y += this.vy;

            // Bounce on boundaries
            if (this.x < 0 || this.x > width) this.vx = -this.vx;
            if (this.y < 0 || this.y > height) this.vy = -this.vy;

            // Mouse interaction
            if (mouse.x !== null && mouse.y !== null) {
                const dx = this.x - mouse.x;
                const dy = this.y - mouse.y;
                const dist = Math.hypot(dx, dy);
                if (dist < mouse.radius) {
                    const force = (mouse.radius - dist) / mouse.radius;
                    this.x += (dx / dist) * force * 1.5;
                    this.y += (dy / dist) * force * 1.5;
                }
            }
        }

        draw() {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
            ctx.fillStyle = this.color;
            ctx.shadowBlur = 10;
            ctx.shadowColor = this.color;
            ctx.fill();
            ctx.shadowBlur = 0; // reset
        }
    }

    // Populate particles
    for (let i = 0; i < maxParticles; i++) {
        particles.push(new Particle());
    }

    function animate() {
        ctx.clearRect(0, 0, width, height);

        // Draw network grid lines first
        ctx.strokeStyle = 'rgba(124, 58, 237, 0.05)';
        ctx.lineWidth = 0.5;
        for (let i = 0; i < width; i += 60) {
            ctx.beginPath();
            ctx.moveTo(i, 0);
            ctx.lineTo(i, height);
            ctx.stroke();
        }
        for (let j = 0; j < height; j += 60) {
            ctx.beginPath();
            ctx.moveTo(0, j);
            ctx.lineTo(width, j);
            ctx.stroke();
        }

        // Draw connections
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const dist = Math.hypot(dx, dy);

                if (dist < 100) {
                    const opacity = (100 - dist) / 100 * 0.18;
                    ctx.strokeStyle = `rgba(139, 92, 246, ${opacity})`;
                    ctx.lineWidth = 1;
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.stroke();
                }
            }
        }

        // Draw and update particles
        particles.forEach(p => {
            p.update();
            p.draw();
        });

        requestAnimationFrame(animate);
    }

    animate();
}

// 2. Password Visibility Toggle
function initPasswordToggle() {
    const toggleBtn = document.getElementById('password-toggle');
    const passwordInput = document.getElementById('password');
    if (!toggleBtn || !passwordInput) return;

    toggleBtn.addEventListener('click', () => {
        const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordInput.setAttribute('type', type);
        
        // Swap icon — Lucide replaces the original <i data-lucide="..."> with
        // a rendered <svg> on page load, so by the time this click fires
        // there is no <i> left to select; look for either.
        const icon = toggleBtn.querySelector('svg, i');
        if (!icon) return;

        if (type === 'text') {
            icon.setAttribute('data-lucide', 'eye-off');
        } else {
            icon.setAttribute('data-lucide', 'eye');
        }
        
        if (window.lucide) {
            lucide.createIcons({ node: toggleBtn });
        }
    });
}

// 4. Quick fill demo badges
function initDemoHelpers() {
    const badges = document.querySelectorAll('.demo-badge');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');

    badges.forEach(badge => {
        badge.addEventListener('click', () => {
            const user = badge.getAttribute('data-user');
            const pass = badge.getAttribute('data-pass');
            
            emailInput.value = user;
            passwordInput.value = pass;
            
            showToast(`Auto-filled: ${user}`, 'info');
            
            // Highlight filled state
            badge.style.transform = 'scale(0.98)';
            setTimeout(() => {
                badge.style.transform = 'none';
            }, 100);
            
            // Auto submit
            document.getElementById('auth-form').dispatchEvent(new Event('submit'));
        });
    });
}

function redirectForRole(role) {
    if (role === 'logistics') {
        window.location.href = 'dashboard.html';
    } else if (role === 'marketplace') {
        window.location.href = 'marketplace.html';
    } else if (role === 'driver') {
        window.location.href = 'driver.html';
    } else if (role === 'admin') {
        window.location.href = 'admin.html';
    } else {
        window.location.href = 'marketplace.html';
    }
}

// 5. Submit Auth Form
function initAuthForm() {
    const form = document.getElementById('auth-form');
    const submitBtn = document.getElementById('submit-btn');
    const btnText = document.getElementById('btn-text');

    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value.trim();

        if (!email || !password) {
            showToast('Please fill in all fields.', 'warning');
            return;
        }

        // Disable button & show loader
        submitBtn.disabled = true;
        btnText.textContent = 'Authenticating...';

        try {
            // Prepare OAuth2 password form payload
            const formData = new URLSearchParams();
            formData.append('username', email);
            formData.append('password', password);

            const response = await fetch(`${API_BASE}/auth/token`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                // Save token & user details
                localStorage.setItem('access_token', data.access_token);
                localStorage.setItem('user_role', data.role);
                localStorage.setItem('user_email', email);

                if (data.must_change_password) {
                    // Temporary password — force a password change before
                    // letting the person into their dashboard.
                    document.getElementById('auth-form').style.display = 'none';
                    document.getElementById('change-password-form').style.display = 'block';
                    showToast('Please set a new password to continue.', 'info');
                    submitBtn.disabled = false;
                    btnText.textContent = 'Sign In';
                    return;
                }

                showToast('Authentication Successful!', 'success');
                setTimeout(() => redirectForRole(data.role), 800);
            } else {
                showToast(data.detail || 'Incorrect email or password.', 'danger');
                submitBtn.disabled = false;
                btnText.textContent = 'Sign In';
            }
        } catch (error) {
            console.error('Auth Error:', error);
            showToast('Network error, failed to reach authentication server.', 'danger');
            submitBtn.disabled = false;
            btnText.textContent = 'Sign In';
        }
    });
}

// 6. Submit Change-Password Form (first login with a temporary password)
function initChangePasswordForm() {
    const form = document.getElementById('change-password-form');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const newPassword = document.getElementById('new-password').value.trim();
        const token = localStorage.getItem('access_token');
        const role = localStorage.getItem('user_role');

        const submitBtn = form.querySelector('button[type="submit"]');
        submitBtn.disabled = true;

        try {
            const response = await fetch(`${API_BASE}/auth/change-password`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ new_password: newPassword })
            });

            if (response.ok) {
                showToast('Password set. Redirecting...', 'success');
                setTimeout(() => redirectForRole(role), 800);
            } else {
                const err = await response.json();
                showToast(err.detail || 'Could not set password.', 'danger');
                submitBtn.disabled = false;
            }
        } catch (error) {
            showToast('Network error while setting password.', 'danger');
            submitBtn.disabled = false;
        }
    });
}