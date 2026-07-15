// ArtiLogix Marketplace Page Controller

function init() {
    // 1. Authenticate Guard
    const auth = checkAuth(['logistics', 'marketplace']);
    if (!auth) return;

    // Display user profile info safely
    const avatarEl = document.getElementById('user-avatar');
    const nameEl = document.getElementById('user-display-name');
    if (avatarEl) avatarEl.textContent = auth.email.substring(0, 1).toUpperCase();
    if (nameEl) nameEl.textContent = auth.email.split('@')[0];

    // Set default shipping date to today + 3 days
    const today = new Date();
    today.setDate(today.getDate() + 3);
    const dateStr = today.toISOString().split('T')[0];
    const shippingDateEl = document.getElementById('shipping-date');
    if (shippingDateEl) shippingDateEl.value = dateStr;

    // 2. Initialize Marketplace features
    initEstimator();
    initLogsTable();
    initFloatingChat();

    // Sync button
    const refreshBtn = document.getElementById('refresh-marketplace');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            window.dispatchEvent(new CustomEvent('refresh-logs'));
        });
    }
}

// Robust execution wrapper to prevent DOMContentLoaded race conditions
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

// 1. Shipment Estimator Calculator
function initEstimator() {
    const form = document.getElementById('estimator-form');
    const resultPanel = document.getElementById('result-panel');
    const skeleton = document.getElementById('result-skeleton');
    const emptyState = document.getElementById('result-empty');
    const contentState = document.getElementById('result-content');
    
    // Result details
    const resVehicleIcon = document.getElementById('result-vehicle-icon');
    const resVehicleName = document.getElementById('result-vehicle-name');
    const resCostValue = document.getElementById('result-cost-value');
    const resRoute = document.getElementById('result-route');
    const resDistance = document.getElementById('result-distance');
    const resDelay = document.getElementById('result-delay');
    const resDesi = document.getElementById('result-desi');

    let currentEstimationData = null;

    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const dest = document.getElementById('destination').value;
        const weight = parseFloat(document.getElementById('weight').value);
        const volume = parseFloat(document.getElementById('volume').value);
        const deliveryType = document.getElementById('delivery-type').value;
        const priority = document.getElementById('delivery-priority').value;
        const waypoint = document.getElementById('route-waypoint').value;
        const isHoliday = document.getElementById('is-holiday').checked ? "true" : "false";
        const shipDate = document.getElementById('shipping-date').value;

        // Reset visual state
        emptyState.style.display = 'none';
        contentState.style.display = 'none';
        skeleton.style.display = 'flex';
        resultPanel.classList.remove('active');

        // Hide consolidation box initially
        const consolBox = document.getElementById('consolidation-box');
        if (consolBox) consolBox.style.display = 'none';

        try {
            // Build URL with query params matching FastAPI router
            const url = `${API_BASE}/predict/dispatch?region=${encodeURIComponent(dest)}` +
                `&date=${encodeURIComponent(shipDate)}` +
                `&cold_chain=${encodeURIComponent(priority === 'express' ? 'true' : 'false')}` +
                `&priority=${encodeURIComponent(priority)}` +
                `&waypoint=${encodeURIComponent(waypoint)}` +
                `&weight=${encodeURIComponent(weight)}` +
                `&volume=${encodeURIComponent(volume)}` +
                `&is_holiday=${encodeURIComponent(isHoliday)}`;

            const response = await fetch(url, { method: 'POST' });

            if (response.ok) {
                const data = await response.json();
                currentEstimationData = {
                    destination: dest,
                    weight: weight,
                    volume: volume,
                    deliveryType: deliveryType,
                    date: shipDate,
                    vehicle: data.vehicle_type,
                    cost: data.total_cost_azn,
                    distance: data.distance_km,
                    desi: data.estimated_desi
                };

                // Add delay for premium skeleton animation feel (600ms)
                setTimeout(async () => {
                    skeleton.style.display = 'none';
                    contentState.style.display = 'block';
                    resultPanel.classList.add('active');

                    // Map vehicle text representation
                    resVehicleName.textContent = data.vehicle_type.toUpperCase();
                    resCostValue.textContent = formatAZN(data.total_cost_azn);
                    
                    let routeString = `Absheron ➔ ${data.region}`;
                    if (waypoint && waypoint !== 'none') {
                        routeString = `Absheron ➔ ${waypoint} ➔ ${data.region}`;
                    }
                    resRoute.textContent = routeString;
                    
                    resDistance.textContent = `${data.distance_km} km`;
                    resDesi.textContent = `${data.estimated_desi} Desi`;
                    
                    // Delay Risk presentation
                    resDelay.textContent = `${data.delay_risk_pct}%`;
                    if (data.delay_risk_pct > 8.0) {
                        resDelay.style.color = 'var(--danger)';
                    } else if (data.delay_risk_pct > 4.5) {
                        resDelay.style.color = 'var(--warning)';
                    } else {
                        resDelay.style.color = 'var(--success)';
                    }

                    // Handle smart consolidation alert panel display
                    const consolContent = document.getElementById('consolidation-content');
                    if (consolBox && consolContent) {
                        if (data.consolidation_alert) {
                            consolBox.style.display = 'block';
                            consolContent.textContent = data.consolidation_alert;
                            if (window.lucide) {
                                lucide.createIcons({ node: consolBox });
                            }
                        } else {
                            consolBox.style.display = 'none';
                        }
                    }
                    
                    // Fetch dynamic AI Dispatch insights using Google Gemini
                    const insightsEl = document.getElementById('ai-insights-content');
                    if (insightsEl) {
                        insightsEl.innerHTML = '<span style="color:var(--text-muted); font-size:11px;">Generating AI route insights...</span>';
                        try {
                            const token = localStorage.getItem('access_token');
                            const prompt = `Analyze this B2B logistics dispatch request:
- Route Corridor: ${routeString}
- Target Date: ${shipDate}
- Delivery Priority: ${priority.toUpperCase()}
- Cargo Specs: ${weight} kg / ${volume} Desi (${deliveryType})
- AI Selected Vehicle: ${data.vehicle_type}
- Calculated Cost: ${formatAZN(data.total_cost_azn)}
- Predictive Route Delay Risk: ${data.delay_risk_pct}%
- Surcharge (Holiday/Peak) Applied: ${isHoliday === 'true' ? 'Yes (+30%)' : 'No'}

Provide a concise (3-4 bullet points) Azerbaijani routing analysis, noting any potential weather/terrain hazards for this route (e.g. Salyan/Lankaran humidity, Khachmaz seasonal traffic, Ganja mountain passes), vehicle suitability, and operational recommendations. Keep it professional, data-driven, and brief.`;

                            const aiRes = await fetch(`${API_BASE}/chat/message`, {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'Authorization': `Bearer ${token}`
                                },
                                body: JSON.stringify({
                                    message: prompt,
                                    session_id: `estimate-${Date.now()}`
                                })
                            });
                            if (aiRes.ok) {
                                const aiData = await aiRes.json();
                                insightsEl.innerHTML = renderMarkdown(aiData.response);
                            } else {
                                insightsEl.textContent = 'AI insights currently unavailable.';
                            }
                        } catch (e) {
                            console.error(e);
                            insightsEl.textContent = 'Failed to generate AI insights.';
                        }
                    }

                    showToast('Logistics routing solution generated!', 'success');
                }, 600);
            } else {
                showToast('Estimation failed. Please verify input data.', 'danger');
                skeleton.style.display = 'none';
                emptyState.style.display = 'block';
            }
        } catch (error) {
            console.error('Estimator error:', error);
            showToast('Unable to contact estimation service.', 'danger');
            skeleton.style.display = 'none';
            emptyState.style.display = 'block';
        }
    });

    // Book Dispatch Confirm action
    const bookBtn = document.getElementById('dispatch-book-btn');
    if (bookBtn) {
        bookBtn.addEventListener('click', async () => {
            if (!currentEstimationData) return;

            const newShipment = {
                shipment_id: `SL-${Math.floor(10000 + Math.random() * 90000)}`,
                destination: currentEstimationData.destination,
                date: currentEstimationData.date,
                vehicle: currentEstimationData.vehicle,
                cost: currentEstimationData.cost,
                delay: 0.0,
                status: 'pending'
            };

            try {
                const token = localStorage.getItem('access_token');
                const response = await fetch(`${API_BASE}/predict/shipments`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify(newShipment)
                });

                if (response.ok) {
                    showToast(`Shipment ${newShipment.shipment_id} booked successfully!`, 'success');
                    
                    // Reset Estimator
                    currentEstimationData = null;
                    contentState.style.display = 'none';
                    emptyState.style.display = 'block';
                    resultPanel.classList.remove('active');

                    // Refresh Table
                    window.dispatchEvent(new CustomEvent('refresh-logs'));
                } else {
                    showToast('Failed to save booking to database.', 'danger');
                }
            } catch (err) {
                console.error(err);
                showToast('Unable to connect to booking service.', 'danger');
            }
        });
    }
}

// 2. Shipment Logs History Table
function initLogsTable() {
    const tbody = document.getElementById('logs-tbody');
    const logSearch = document.getElementById('log-search');
    const filterStatus = document.getElementById('filter-status');
    const filterVehicle = document.getElementById('filter-vehicle');
    
    const btnPrev = document.getElementById('btn-prev');
    const btnNext = document.getElementById('btn-next');
    const pageIndicator = document.getElementById('page-indicator');

    if (!tbody || !logSearch) return;

    let logs = [];
    let currentPage = 1;
    const itemsPerPage = 5;

    async function renderTable() {
        try {
            const token = localStorage.getItem('access_token');
            const response = await fetch(`${API_BASE}/predict/shipments`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            if (response.ok) {
                logs = await response.json();
            }
        } catch (err) {
            console.error('Failed to load shipments:', err);
        }

        // Apply filter constraints
        const searchVal = logSearch.value.toLowerCase().trim();
        const statusVal = filterStatus.value;
        const vehicleVal = filterVehicle.value;

        const filtered = logs.filter(item => {
            const matchDest = item.destination.toLowerCase().includes(searchVal) || item.id.toLowerCase().includes(searchVal);
            const matchStatus = statusVal === 'all' || item.status === statusVal;
            
            let matchVehicle = true;
            if (vehicleVal !== 'all') {
                if (vehicleVal === 'Isuzu') {
                    matchVehicle = item.vehicle.includes('Isuzu') || item.vehicle.includes('Gazelle');
                } else {
                    matchVehicle = item.vehicle === vehicleVal;
                }
            }

            return matchDest && matchStatus && matchVehicle;
        });

        // Paginate filtered results
        const totalItems = filtered.length;
        const totalPages = Math.ceil(totalItems / itemsPerPage) || 1;
        
        if (currentPage > totalPages) currentPage = totalPages;
        
        const startIdx = (currentPage - 1) * itemsPerPage;
        const endIdx = Math.min(startIdx + itemsPerPage, totalItems);
        const paginated = filtered.slice(startIdx, endIdx);

        // Update indicators
        if (pageIndicator) pageIndicator.textContent = totalItems === 0 ? "Showing 0 shipments" : `Showing ${startIdx + 1}-${endIdx} of ${totalItems} shipments`;
        if (btnPrev) btnPrev.disabled = currentPage === 1;
        if (btnNext) btnNext.disabled = currentPage === totalPages || totalItems === 0;

        tbody.innerHTML = '';

        if (paginated.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; color:var(--text-muted);">No matching shipments logged in this period.</td></tr>`;
            return;
        }

        paginated.forEach(row => {
            let badgeClass = 'badge-info';
            if (row.status === 'delivered') badgeClass = 'badge-success';
            else if (row.status === 'pending') badgeClass = 'badge-warning';
            else if (row.status === 'delayed') badgeClass = 'badge-danger';
            else if (row.status === 'in-transit') badgeClass = 'badge-primary';

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td style="font-family:var(--font-mono); font-weight:600; color:var(--primary-lighter);">${row.id}</td>
                <td><b>${row.destination}</b></td>
                <td>${row.date}</td>
                <td><span style="font-size:13px;">${row.vehicle}</span></td>
                <td style="font-family:var(--font-mono);">${formatAZN(row.cost)}</td>
                <td style="color:${row.delay > 8 ? 'var(--warning)' : 'var(--success)'}; font-family:var(--font-mono);">${row.delay}%</td>
                <td><span class="badge ${badgeClass}">${row.status}</span></td>
                <td>
                    <button class="btn btn-ghost delete-log-btn" data-id="${row.id}" style="padding:6px;" title="Cancel Shipment">
                        <i data-lucide="trash-2" style="width:16px; height:16px; color:var(--danger);"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });

        // Re-inject icons
        if (window.lucide) {
            lucide.createIcons({
                attrs: { class: 'lucide' },
                nameAttr: 'data-lucide',
                node: tbody
            });
        }

        // Delete handlers
        document.querySelectorAll('.delete-log-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const id = btn.getAttribute('data-id');
                try {
                    const token = localStorage.getItem('access_token');
                    const response = await fetch(`${API_BASE}/predict/shipments/${encodeURIComponent(id)}`, {
                        method: 'DELETE',
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    });
                    if (response.ok) {
                        showToast(`Shipment ${id} has been cancelled.`, 'warning');
                        renderTable();
                    } else {
                        showToast('Failed to cancel shipment.', 'danger');
                    }
                } catch (err) {
                    console.error(err);
                    showToast('Connection error.', 'danger');
                }
            });
        });
    }

    renderTable();

    // Event hooks
    if (logSearch) logSearch.addEventListener('input', () => { currentPage = 1; renderTable(); });
    if (filterStatus) filterStatus.addEventListener('change', () => { currentPage = 1; renderTable(); });
    if (filterVehicle) filterVehicle.addEventListener('change', () => { currentPage = 1; renderTable(); });

    if (btnPrev) btnPrev.addEventListener('click', () => { if (currentPage > 1) { currentPage--; renderTable(); } });
    if (btnNext) btnNext.addEventListener('click', () => { currentPage++; renderTable(); });

    window.addEventListener('refresh-logs', () => {
        currentPage = 1;
        renderTable();
    });
}

// 3. Slide-over AI Advisor (Glassmorphism Sidebar Drawer)
function initFloatingChat() {
    const toggleBtn = document.getElementById('chat-toggle');
    const panel = document.getElementById('ai-panel');
    const overlay = document.getElementById('ai-overlay');
    const closeBtn = document.getElementById('ai-panel-close');

    const sendBtn = document.getElementById('ai-chat-send');
    const chatInput = document.getElementById('ai-chat-input');
    const messagesBox = document.getElementById('ai-messages');

    if (!toggleBtn || !panel) return;

    function openPanel() {
        panel.classList.add('open');
        if (overlay) overlay.classList.add('active');
    }

    function closePanel() {
        panel.classList.remove('open');
        if (overlay) overlay.classList.remove('active');
    }

    toggleBtn.addEventListener('click', openPanel);
    if (closeBtn) closeBtn.addEventListener('click', closePanel);
    if (overlay) overlay.addEventListener('click', closePanel);

    // Suggested prompts
    const suggestedBtns = document.querySelectorAll('.suggested-prompt-btn');
    suggestedBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const prompt = btn.getAttribute('data-prompt');
            if (chatInput) {
                chatInput.value = prompt;
                sendMessage();
            }
        });
    });

    if (sendBtn) sendBtn.addEventListener('click', sendMessage);
    if (chatInput) {
        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    }

    async function sendMessage() {
        const text = chatInput.value.trim();
        if (!text) return;

        chatInput.value = '';

        // Add user msg bubble
        const userMsg = document.createElement('div');
        userMsg.className = 'chat-msg user';
        userMsg.textContent = text;
        messagesBox.appendChild(userMsg);
        messagesBox.scrollTop = messagesBox.scrollHeight;

        // Add assistant thinking placeholder
        const assistantMsg = document.createElement('div');
        assistantMsg.className = 'chat-msg assistant';
        
        const loader = document.createElement('div');
        loader.className = 'chat-msg-thinking';
        loader.innerHTML = `
            <span>Thinking</span>
            <div class="thinking-dot"></div>
            <div class="thinking-dot"></div>
            <div class="thinking-dot"></div>
        `;
        assistantMsg.appendChild(loader);
        messagesBox.appendChild(assistantMsg);
        messagesBox.scrollTop = messagesBox.scrollHeight;

        // Stream via EventSource
        try {
            const token = localStorage.getItem('access_token');
            const url = `${API_BASE}/chat/stream?message=${encodeURIComponent(text)}&token=${encodeURIComponent(token)}`;
            const eventSource = new EventSource(url);
            let buffer = '';

            eventSource.onmessage = (event) => {
                const data = JSON.parse(event.data);

                if (data.reset) {
                    assistantMsg.innerHTML = '';
                } else if (data.content !== undefined) {
                    buffer += data.content;
                    // Format response markup
                    assistantMsg.innerHTML = renderMarkdown(buffer);
                    messagesBox.scrollTop = messagesBox.scrollHeight;
                }

                if (data.done) {
                    eventSource.close();
                }
            };

            eventSource.onerror = () => {
                eventSource.close();
                
                // Fallback POST
                fetch(`${API_BASE}/chat/message`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({ message: text })
                }).then(res => res.json()).then(data => {
                    assistantMsg.innerHTML = renderMarkdown(data.response || 'Session ended.');
                    messagesBox.scrollTop = messagesBox.scrollHeight;
                }).catch(() => {
                    loader.innerHTML = '<span style="color:var(--danger)">Connection failed.</span>';
                });
            };

        } catch (err) {
            console.error(err);
            loader.innerHTML = '<span style="color:var(--danger)">Connection failed.</span>';
        }
    }
}

// Minimal markdown table/formatting renderer (shared code block)
function renderMarkdown(md) {
    let html = md;
    html = html.replace(/```yaml([\s\S]*?)```/g, '<pre style="padding:6px; font-size:11px; margin:6px 0;"><code class="language-yaml">$1</code></pre>');
    html = html.replace(/```([\s\S]*?)```/g, '<pre style="padding:6px; font-size:11px; margin:6px 0;"><code>$1</code></pre>');
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/(?<!\*)\*([^*\n]+)\*(?!\*)/g, '<em>$1</em>');
    html = html.replace(/^\s*\|?[\s:|-]*-[\s:|-]*\|[\s:|-]*\s*$/gm, '');
    html = html.replace(/^\*\s+(.*)$/gm, '<li>$1</li>');
    html = html.replace(/^- (.*)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/s, '<ul style="margin-left:14px; margin-top:4px;">$1</ul>');
    html = html.replace(/^### (.*)$/gm, '<h5 style="margin: 6px 0 4px 0; font-weight:600;">$1</h5>');
    html = html.replace(/\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|/g, (match, p1, p2, p3, p4) => {
        return `<tr><td>${p1.trim()}</td><td>${p2.trim()}</td><td>${p3.trim()}</td><td>${p4.trim()}</td></tr>`;
    });
    html = html.replace(/\|([^|]+)\|([^|]+)\|([^|]+)\|/g, (match, p1, p2, p3) => {
        return `<tr><td>${p1.trim()}</td><td>${p2.trim()}</td><td>${p3.trim()}</td></tr>`;
    });
    html = html.replace(/((?:<tr>(?:<td>[^<]*<\/td>)+<\/tr>\s*)+)/g, '<table style="margin:6px 0; width:100%; border-collapse:collapse; font-size:10px;">$1</table>');
    html = html.replace(/\n/g, '<br>');
    return html;
}
