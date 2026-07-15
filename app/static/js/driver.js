// ArtiLogix Driver Portal Controller

let activeStepIdx = 2; // Step 2 (Refueling) is currently active

let mapPoints = [
    { name: "Absheron", x: 0.85, y: 0.5 },
    { name: "Yevlakh", x: 0.5, y: 0.5 },
    { name: "Ganja", x: 0.15, y: 0.5 }
];

document.addEventListener('DOMContentLoaded', () => {
    // 1. Authenticate Guard (Drivers only!)
    const auth = checkAuth('driver');
    if (!auth) return;

    // Initialize notch clock
    initNotchClock();
    
    // Initialize driver timeline checklist updates
    initTimelineController();
    
    // Initialize left drawer sidebar controls
    initMobileSidebar();
    initProfileEditor();
    
    // Load driver profile from server
    loadDriverProfile();
});

// 1. Notch Ticking Clock
function initNotchClock() {
    const timeEl = document.getElementById('phone-time');
    if (!timeEl) return;
    
    function tick() {
        const now = new Date();
        const hrs = String(now.getHours()).padStart(2, '0');
        const mins = String(now.getMinutes()).padStart(2, '0');
        timeEl.textContent = `${hrs}:${mins}`;
    }
    
    tick();
    setInterval(tick, 60000);
}

function markStepCompleted(stepId, timeStr) {
    const step = document.getElementById(stepId);
    if (!step) return;
    step.className = 'timeline-step completed';
    step.querySelector('.timeline-bullet').innerHTML = '<i data-lucide="check" style="width:12px; height:12px"></i>';
    const timeEl = step.querySelector('.timeline-time');
    if (timeEl) timeEl.textContent = timeStr;
    if (window.lucide) {
        lucide.createIcons({ node: step });
    }
}

// Set step active in checklist
function setStepActive(stepId, labelText = 'In-Transit') {
    const step = document.getElementById(stepId);
    if (!step) return;
    step.className = 'timeline-step active';
    const timeEl = step.querySelector('.timeline-time');
    if (timeEl) timeEl.textContent = labelText;
}

function disableUpdateBtn() {
    const updateBtn = document.getElementById('driver-update-status');
    if (updateBtn) {
        updateBtn.disabled = true;
        updateBtn.style.opacity = '0.5';
    }
}

// 2. Timeline Checklist Log Controller
function initTimelineController() {
    const updateBtn = document.getElementById('driver-update-status');
    if (!updateBtn) return;

    updateBtn.addEventListener('click', async () => {
        const token = localStorage.getItem('access_token');
        const now = new Date();
        const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const step2Title = document.getElementById('step-2-title').textContent.split(': ')[1] || 'Yevlakh';
        const step3Title = document.getElementById('step-3-title').textContent.replace('Arrive ', '');

        if (activeStepIdx === 2) {
            try {
                const response = await fetch(`${API_BASE}/api/drivers/me/progress`, {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        status: 'In-Transit',
                        current_checkpoint: step2Title,
                        last_checkpoint_time: timeStr
                    })
                });

                if (response.ok) {
                    markStepCompleted('step-2', timeStr);
                    setStepActive('step-3', 'Scheduled: 03:30 PM');
                    activeStepIdx = 3;
                    showToast(`Checkpoint logged: Refueled at ${step2Title}.`, 'success');
                } else {
                    showToast('Failed to update progress in DB.', 'danger');
                }
            } catch (err) {
                console.error(err);
                showToast('Network error.', 'danger');
            }
        } else if (activeStepIdx === 3) {
            try {
                const response = await fetch(`${API_BASE}/api/drivers/me/progress`, {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        status: 'Completed',
                        current_checkpoint: step3Title,
                        last_checkpoint_time: timeStr
                    })
                });

                if (response.ok) {
                    markStepCompleted('step-3', timeStr);
                    disableUpdateBtn();
                    showToast(`Trip Completed! Cargo delivered to ${step3Title}.`, 'success');
                } else {
                    showToast('Failed to complete trip in DB.', 'danger');
                }
            } catch (err) {
                console.error(err);
                showToast('Network error.', 'danger');
            }
        }
    });
}

// 3. Mobile left profile drawer toggle
function initMobileSidebar() {
    const trigger = document.getElementById('mobile-sidebar-trigger');
    const closeBtn = document.getElementById('mobile-drawer-close');
    const overlay = document.getElementById('mobile-drawer-overlay');
    const drawer = document.getElementById('mobile-left-drawer');

    if (!trigger || !drawer) return;

    trigger.addEventListener('click', () => {
        drawer.classList.add('open');
        overlay.classList.add('active');
        
        if (window.lucide) {
            lucide.createIcons({ node: drawer });
        }
    });

    closeBtn.addEventListener('click', closeDrawer);
    overlay.addEventListener('click', closeDrawer);

    function closeDrawer() {
        drawer.classList.remove('open');
        overlay.classList.remove('active');
    }
}

// 4. Drawer Interactive Profile Editor & Password Update
function initProfileEditor() {
    const saveProfileBtn = document.getElementById('btn-save-profile');

    if (saveProfileBtn) {
        saveProfileBtn.addEventListener('click', async () => {
            const token = localStorage.getItem('access_token');
            const name = document.getElementById('drv-input-name').value.trim();
            const phone = document.getElementById('drv-input-phone').value.trim();
            const vehicle = document.getElementById('drv-input-vehicle').value.trim();
            const plate = document.getElementById('drv-input-plate').value.trim();
            const newPassword = document.getElementById('drv-input-password').value.trim();

            saveProfileBtn.disabled = true;
            saveProfileBtn.textContent = 'Saving...';

            try {
                // 1. Update Profile Fields
                const response = await fetch(`${API_BASE}/api/drivers/me`, {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        name: name,
                        phone: phone,
                        vehicle_type: vehicle,
                        vehicle_number: plate
                    })
                });

                if (!response.ok) {
                    const err = await response.json();
                    showToast(err.detail || 'Could not update profile.', 'danger');
                    return;
                }

                // 2. If password is provided, update Password too!
                if (newPassword) {
                    if (newPassword.length < 4) {
                        showToast('Password must be at least 4 characters.', 'warning');
                        return;
                    }
                    const passRes = await fetch(`${API_BASE}/auth/change-password`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${token}`
                        },
                        body: JSON.stringify({ new_password: newPassword })
                    });

                    if (!passRes.ok) {
                        const err = await passRes.json();
                        showToast(err.detail || 'Could not update password.', 'danger');
                        return;
                    }
                    document.getElementById('drv-input-password').value = '';
                }

                showToast('Profile changes saved successfully!', 'success');
                loadDriverProfile();
            } catch (e) {
                console.error(e);
                showToast('Network error while saving profile.', 'danger');
            } finally {
                saveProfileBtn.disabled = false;
                saveProfileBtn.textContent = 'Save Changes';
            }
        });
    }
}

async function loadDriverProfile() {
    const token = localStorage.getItem('access_token');
    try {
        const response = await fetch(`${API_BASE}/api/drivers/me`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (response.ok) {
            const data = await response.json();
            
            // Populate display elements
            const idEl = document.getElementById('drv-display-id');
            if (idEl) idEl.textContent = data.driver_id;
            
            // Populate input form fields
            const nameIn = document.getElementById('drv-input-name');
            const phoneIn = document.getElementById('drv-input-phone');
            const vehicleIn = document.getElementById('drv-input-vehicle');
            const plateIn = document.getElementById('drv-input-plate');

            if (nameIn) nameIn.value = data.name || '';
            if (phoneIn) phoneIn.value = data.phone || '';
            if (vehicleIn) vehicleIn.value = data.vehicle_type || '';
            if (plateIn) plateIn.value = data.vehicle_number || '';

            const ship = data.active_shipment;
            const updateBtn = document.getElementById('driver-update-status');

            if (ship) {
                // Populate Active Shipment Card
                document.getElementById('shipment-id-badge').textContent = `DISPATCH: ${ship.shipment_id}`;
                document.getElementById('shipment-route-header').textContent = `Absheron ➔ ${ship.destination}`;
                document.getElementById('shipment-vehicle-desc').innerHTML = `Assigned Vehicle: <b>${ship.vehicle}</b>`;
                document.getElementById('shipment-cost-val').textContent = formatAZN(ship.cost);

                // Dynamically update checkpoint titles based on route destination
                const step3Title = document.getElementById('step-3-title');
                const step2Title = document.getElementById('step-2-title');
                
                step3Title.textContent = `Arrive ${ship.destination} Hub`;
                
                let midPoint = 'Yevlakh';
                if (ship.destination === 'Lankaran') {
                    midPoint = 'Salyan';
                } else if (ship.destination === 'Khachmaz') {
                    midPoint = 'Gobustan';
                }
                step2Title.textContent = `Refueling & Break: ${midPoint}`;

                // Dynamically update GPS map points
                if (ship.destination === 'Lankaran') {
                    mapPoints = [
                        { name: "Absheron", x: 0.85, y: 0.2 },
                        { name: "Salyan", x: 0.65, y: 0.5 },
                        { name: "Lankaran", x: 0.55, y: 0.8 }
                    ];
                } else if (ship.destination === 'Khachmaz') {
                    mapPoints = [
                        { name: "Absheron", x: 0.85, y: 0.8 },
                        { name: "Gobustan", x: 0.75, y: 0.5 },
                        { name: "Khachmaz", x: 0.65, y: 0.2 }
                    ];
                } else {
                    mapPoints = [
                        { name: "Absheron", x: 0.85, y: 0.5 },
                        { name: "Yevlakh", x: 0.5, y: 0.5 },
                        { name: ship.destination, x: 0.15, y: 0.5 }
                    ];
                }

                if (updateBtn) {
                    updateBtn.disabled = false;
                    updateBtn.style.opacity = '1.0';
                }

                // Restore checklist state based on database values!
                if (data.status === 'Completed' || data.current_checkpoint === ship.destination) {
                    markStepCompleted('step-2', data.last_checkpoint_time || '12:30 PM');
                    markStepCompleted('step-3', data.last_checkpoint_time || '03:45 PM');
                    disableUpdateBtn();
                } else if (data.status === 'In-Transit' && data.current_checkpoint === midPoint) {
                    markStepCompleted('step-2', data.last_checkpoint_time || '12:30 PM');
                    setStepActive('step-3', 'Scheduled: 03:30 PM');
                    activeStepIdx = 3;
                } else {
                    setStepActive('step-2', 'Scheduled: 12:30 PM');
                    activeStepIdx = 2;
                }
            } else {
                // No active shipment booked yet
                document.getElementById('shipment-id-badge').textContent = `DISPATCH: NO ACTIVE TRIP`;
                document.getElementById('shipment-route-header').textContent = `No cargo assigned`;
                document.getElementById('shipment-vehicle-desc').innerHTML = `Assigned Vehicle: <b>None</b>`;
                document.getElementById('shipment-cost-val').textContent = `₼ 0.00`;

                if (updateBtn) {
                    updateBtn.disabled = true;
                    updateBtn.style.opacity = '0.5';
                }

                // Default empty map points
                mapPoints = [
                    { name: "Absheron", x: 0.85, y: 0.5 },
                    { name: "Yevlakh", x: 0.5, y: 0.5 },
                    { name: "Ganja", x: 0.15, y: 0.5 }
                ];
            }
        }
    } catch (e) {
        console.error("Failed to load driver profile", e);
    }
}
