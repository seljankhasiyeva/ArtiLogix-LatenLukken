// ArtiLogix Admin Console Controller

let allUsers = [];

document.addEventListener('DOMContentLoaded', () => {
    const auth = checkAuth('admin');
    if (!auth) return;

    // Display user profile info safely
    const avatarEl = document.getElementById('user-avatar');
    const nameEl = document.getElementById('user-display-name');
    if (avatarEl) avatarEl.textContent = auth.email.substring(0, 1).toUpperCase();
    if (nameEl) nameEl.textContent = auth.email.split('@')[0];

    loadUsersList();
    initUserModal();
});

async function loadUsersList() {
    const marketplaceBody = document.getElementById('marketplace-table-body');
    const logisticsBody = document.getElementById('logistics-table-body');
    if (!marketplaceBody || !logisticsBody) return;

    marketplaceBody.innerHTML = `<tr><td colspan="3" style="padding: 20px; text-align: center; color: var(--text-muted);">Loading accounts...</td></tr>`;
    logisticsBody.innerHTML = `<tr><td colspan="3" style="padding: 20px; text-align: center; color: var(--text-muted);">Loading accounts...</td></tr>`;

    const token = localStorage.getItem('access_token');
    try {
        const response = await fetch(`${API_BASE}/api/admin/users`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            allUsers = await response.json();
            
            // Filter out 'admin' accounts completely so they don't show up in editable client lists
            const filteredUsers = allUsers.filter(u => u.role !== 'admin');
            renderUsers(filteredUsers);
        } else {
            marketplaceBody.innerHTML = `<tr><td colspan="3" style="padding: 20px; text-align: center; color: var(--danger);">Failed to load accounts.</td></tr>`;
            logisticsBody.innerHTML = `<tr><td colspan="3" style="padding: 20px; text-align: center; color: var(--danger);">Failed to load accounts.</td></tr>`;
        }
    } catch (error) {
        console.error(error);
        marketplaceBody.innerHTML = `<tr><td colspan="3" style="padding: 20px; text-align: center; color: var(--danger);">Network error while loading accounts.</td></tr>`;
        logisticsBody.innerHTML = `<tr><td colspan="3" style="padding: 20px; text-align: center; color: var(--danger);">Network error while loading accounts.</td></tr>`;
    }
}

function renderUsers(users) {
    const marketplaceBody = document.getElementById('marketplace-table-body');
    const logisticsBody = document.getElementById('logistics-table-body');
    const marketplaceCount = document.getElementById('marketplace-count');
    const logisticsCount = document.getElementById('logistics-count');

    if (!marketplaceBody || !logisticsBody) return;

    const marketplaceUsers = users.filter(u => u.role === 'marketplace');
    const logisticsUsers = users.filter(u => u.role === 'logistics');

    if (marketplaceCount) marketplaceCount.textContent = `${marketplaceUsers.length} account${marketplaceUsers.length === 1 ? '' : 's'}`;
    if (logisticsCount) logisticsCount.textContent = `${logisticsUsers.length} account${logisticsUsers.length === 1 ? '' : 's'}`;

    const generateRowsHTML = (userList) => {
        if (userList.length === 0) {
            return `<tr><td colspan="3" style="padding: 24px; text-align: center; color: var(--text-muted); font-size: 13px;">No accounts created under this role.</td></tr>`;
        }

        return userList.map(u => {
            const pwStatus = u.must_change_password
                ? `<span class="badge badge-secondary" style="display:inline-flex; align-items:center; gap:6px;"><i data-lucide="clock" style="width:12px; height:12px;"></i> Temp password pending</span>`
                : `<span class="badge badge-success" style="display:inline-flex; align-items:center; gap:6px;"><i data-lucide="check" style="width:12px; height:12px;"></i> Password set</span>`;

            return `
                <tr style="border-bottom: 1px solid var(--border);">
                    <td style="padding: 16px; font-size: 14px; font-weight: 500; color: var(--text-main);">${u.email}</td>
                    <td style="padding: 16px; font-size: 12px;">${pwStatus}</td>
                    <td style="padding: 16px; text-align: right; padding-right: 24px;">
                        <button type="button" class="btn btn-secondary" style="padding: 4px 10px; font-size: 12px; background: rgba(239,68,68,0.15); color: var(--danger, #EF4444); border: 1px solid rgba(239,68,68,0.3); border-radius: 6px;" onclick="deleteUser('${u.email}')">Delete</button>
                    </td>
                </tr>
            `;
        }).join('');
    };

    marketplaceBody.innerHTML = generateRowsHTML(marketplaceUsers);
    logisticsBody.innerHTML = generateRowsHTML(logisticsUsers);

    if (window.lucide) {
        lucide.createIcons({ node: marketplaceBody });
        lucide.createIcons({ node: logisticsBody });
    }
}

function initUserModal() {
    const modal = document.getElementById('register-user-modal');
    const overlay = document.getElementById('user-modal-overlay');
    const btnOpen = document.getElementById('btn-open-register-user');
    const btnClose = document.getElementById('btn-close-user-modal');
    const form = document.getElementById('register-user-form');

    const openModal = () => {
        form.reset();
        modal.style.display = 'block';
        overlay.style.display = 'block';
    };
    const closeModal = () => {
        modal.style.display = 'none';
        overlay.style.display = 'none';
    };

    if (btnOpen) btnOpen.addEventListener('click', openModal);
    if (btnClose) btnClose.addEventListener('click', closeModal);
    if (overlay) overlay.addEventListener('click', closeModal);

    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('user-email-input').value.trim();
            const role = document.getElementById('user-role-input').value;
            const token = localStorage.getItem('access_token');

            try {
                const response = await fetch(`${API_BASE}/api/admin/users`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({ email, role })
                });

                if (response.ok) {
                    const data = await response.json();
                    closeModal();
                    showTempPassword(data.password);
                    loadUsersList();
                } else {
                    const err = await response.json();
                    showToast(err.detail || 'Failed to create account.', 'danger');
                }
            } catch (error) {
                showToast('Network error while creating account.', 'danger');
            }
        });
    }

    // Temp password reveal modal
    const pwOverlay = document.getElementById('temp-password-overlay');
    const pwModal = document.getElementById('temp-password-modal');
    const pwCloseBtn = document.getElementById('btn-close-temp-password');
    const closePwModal = () => {
        pwModal.style.display = 'none';
        pwOverlay.style.display = 'none';
    };
    if (pwCloseBtn) pwCloseBtn.addEventListener('click', closePwModal);
    if (pwOverlay) pwOverlay.addEventListener('click', closePwModal);
}

function showTempPassword(password) {
    document.getElementById('temp-password-value').textContent = password;
    document.getElementById('temp-password-modal').style.display = 'block';
    document.getElementById('temp-password-overlay').style.display = 'block';
}

async function deleteUser(email) {
    if (!confirm(`Delete account ${email}? This cannot be undone.`)) return;

    const token = localStorage.getItem('access_token');
    try {
        const response = await fetch(`${API_BASE}/api/admin/users/${encodeURIComponent(email)}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (response.ok || response.status === 204) {
            showToast(`Account ${email} deleted.`, 'success');
            loadUsersList();
        } else {
            const err = await response.json();
            showToast(err.detail || 'Failed to delete account.', 'danger');
        }
    } catch (error) {
        showToast('Network error while deleting account.', 'danger');
    }
}
