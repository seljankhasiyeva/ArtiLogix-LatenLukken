// ArtiLogix Logistics Dashboard Controller

document.addEventListener('DOMContentLoaded', () => {
    // 1. Authenticate Guard
    const auth = checkAuth('logistics');
    if (!auth) return;

    // Display user profile info
    document.getElementById('user-avatar').textContent = auth.email.substring(0, 1).toUpperCase();
    document.getElementById('user-display-name').textContent = auth.email.split('@')[0];

    // 2. Initialize Dashboard Widgets
    initKPIs();
    initAnalyticsCharts();
    initAIAssistant();
    initDriverManagement();
    initDriverPasswordToggle();

    // Refresh synchronization
    document.getElementById('refresh-dashboard').addEventListener('click', () => {
        initKPIs();
        window.dispatchEvent(new CustomEvent('refresh-charts'));
        window.dispatchEvent(new CustomEvent('refresh-map'));
    });
});

// 1. KPI & Sparklines Drawer
async function initKPIs() {
    try {
        const response = await fetch(`${API_BASE}/analytics/kpis`);
        if (response.ok) {
            const data = await response.json();
            
            // Animate KPI numbers using live values from database
            animateNumber('kpi-load-val', data.load, 0, ' Desi');
            animateNumber('kpi-routes-val', data.routes, 0, '');
            animateNumber('kpi-delays-val', data.delay_rate, 1, '%');
            animateNumber('kpi-cost-val', data.cost, 0, ' ₼');

            // Draw sparklines dynamically incorporating the latest live values
            drawSparkline('sparkline-load', [30, 45, 35, 60, 40, 75, Math.min(100, data.load / 60)], '#7C3AED');
            drawSparkline('sparkline-routes', [5, 6, 6, 7, 7, 7, data.routes], '#22C55E');
            drawSparkline('sparkline-delays', [8.2, 7.5, 6.1, 5.5, 4.9, 4.5, data.delay_rate], '#EF4444');
            drawSparkline('sparkline-cost', [10200, 11400, 10800, 12100, 11900, 12500, data.cost], '#7C3AED');
            return;
        }
    } catch (e) {
        console.error("Failed to load live KPIs:", e);
    }

    // Fallback to baseline design if API is down
    animateNumber('kpi-load-val', 4820, 0, ' Desi');
    animateNumber('kpi-routes-val', 8, 0, '');
    animateNumber('kpi-delays-val', 4.2, 1, '%');
    animateNumber('kpi-cost-val', 12850, 0, ' ₼');
    drawSparkline('sparkline-load', [30, 45, 35, 60, 40, 75, 90], '#7C3AED');
    drawSparkline('sparkline-routes', [5, 6, 6, 7, 7, 7, 8], '#22C55E');
    drawSparkline('sparkline-delays', [8.2, 7.5, 6.1, 5.5, 4.9, 4.5, 4.2], '#EF4444');
    drawSparkline('sparkline-cost', [10200, 11400, 10800, 12100, 11900, 12500, 12850], '#7C3AED');
}

function animateNumber(id, endValue, decimals = 0, suffix = '') {
    const el = document.getElementById(id);
    if (!el) return;
    
    let start = 0;
    const duration = 1000;
    const startTime = performance.now();

    function update(now) {
        const progress = Math.min((now - startTime) / duration, 1);
        // Easing function (cubic-bezier easeOut)
        const val = progress * (2 - progress); 
        const current = start + val * endValue;
        
        if (id.includes('cost')) {
            el.innerHTML = formatAZN(current);
        } else {
            el.textContent = current.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ",") + suffix;
        }

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    requestAnimationFrame(update);
}

function drawSparkline(canvasId, dataPoints, color) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    
    // Set layout size
    canvas.width = 100;
    canvas.height = 36;
    
    ctx.clearRect(0, 0, 100, 36);
    ctx.beginPath();
    ctx.lineWidth = 2.0;
    ctx.strokeStyle = color;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    
    const max = Math.max(...dataPoints);
    const min = Math.min(...dataPoints);
    const range = max - min || 1;
    
    dataPoints.forEach((val, i) => {
        const x = (i / (dataPoints.length - 1)) * 90 + 5;
        const y = 36 - (((val - min) / range) * 26 + 5);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    
    ctx.stroke();
    
    // Fill Gradient
    ctx.lineTo(95, 36);
    ctx.lineTo(5, 36);
    ctx.closePath();
    const grad = ctx.createLinearGradient(0, 0, 0, 36);
    grad.addColorStop(0, color + '22');
    grad.addColorStop(1, color + '00');
    ctx.fillStyle = grad;
    ctx.fill();
}

// 2. Chart.js Configurations
function initAnalyticsCharts() {
    let demandChart, delayChart, usageChart, routesChart;
    
    function getThemeColors() {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        return {
            text: isDark ? '#A1A1AA' : '#71717A',
            grid: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)',
            cardBg: isDark ? '#111113' : '#FFFFFF'
        };
    }

    async function loadChartData() {
        const colors = getThemeColors();
        
        try {
            // Fetch Regional Demand
            const rDemand = await fetch(`${API_BASE}/analytics/regional-demand`).then(res => res.json());
            const demandMap = {};
            rDemand.data.forEach(item => {
                if (!demandMap[item.region]) demandMap[item.region] = [];
                demandMap[item.region].push(item.order_count);
            });
            const regions = Object.keys(demandMap).slice(0, 6);
            const demandDataset = regions.map((region, idx) => ({
                label: region,
                data: demandMap[region].slice(-6),
                backgroundColor: `hsla(${(idx * 60) % 360}, 75%, 60%, 0.75)`,
                borderRadius: 4
            }));

            // Fetch Delay Rate
            const rDelay = await fetch(`${API_BASE}/analytics/delay-rate`).then(res => res.json());
            const delayData = rDelay.data.slice(0, 5);
            const delayLabels = delayData.map(d => `${d.origin}➔${d.destination}`);
            const delayRates = delayData.map(d => d.delay_rate_pct);

            // Fetch Vehicle Usage
            const rUsage = await fetch(`${API_BASE}/analytics/vehicle-usage`).then(res => res.json());
            const usageData = rUsage.data;
            const usageLabels = usageData.map(u => u.capacity_range);
            const usageRates = usageData.map(u => u.avg_utilization_pct);

            // Fetch Top Routes
            const rRoutes = await fetch(`${API_BASE}/analytics/top-routes`).then(res => res.json());
            const topRoutes = rRoutes.data.slice(0, 5);
            const routeNames = topRoutes.map(r => `${r.origin}➔${r.destination}`);
            const routeCosts = topRoutes.map(r => r.avg_cost_azn);
            const routeShipments = topRoutes.map(r => r.shipment_count);

            // 1. Demand Chart
            if (demandChart) demandChart.destroy();
            demandChart = new Chart(document.getElementById('chart-demand'), {
                type: 'bar',
                data: {
                    labels: ['Wk 23', 'Wk 24', 'Wk 25', 'Wk 26', 'Wk 27', 'Wk 28'],
                    datasets: demandDataset
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { labels: { color: colors.text, font: { family: 'Inter' } } }
                    },
                    scales: {
                        x: { grid: { color: colors.grid }, ticks: { color: colors.text } },
                        y: { grid: { color: colors.grid }, ticks: { color: colors.text } }
                    }
                }
            });

            // 2. Delay Chart
            if (delayChart) delayChart.destroy();
            delayChart = new Chart(document.getElementById('chart-delays'), {
                type: 'bar',
                data: {
                    labels: delayLabels,
                    datasets: [{
                        label: 'Delay %',
                        data: delayRates,
                        backgroundColor: '#EF444488',
                        borderColor: '#EF4444',
                        borderWidth: 1.5,
                        borderRadius: 4
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        x: { max: 100, grid: { color: colors.grid }, ticks: { color: colors.text } },
                        y: { grid: { color: colors.grid }, ticks: { color: colors.text } }
                    }
                }
            });

            // 3. Usage Chart
            if (usageChart) usageChart.destroy();
            usageChart = new Chart(document.getElementById('chart-usage'), {
                type: 'doughnut',
                data: {
                    labels: usageLabels,
                    datasets: [{
                        data: usageRates,
                        backgroundColor: ['#7C3AEDcc', '#8B5CF6cc', '#A78BFAcc', '#C4B5FDcc'],
                        borderColor: colors.cardBg,
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'right', labels: { color: colors.text } }
                    }
                }
            });

            // 4. Routes Cost Chart
            if (routesChart) routesChart.destroy();
            routesChart = new Chart(document.getElementById('chart-routes'), {
                type: 'line',
                data: {
                    labels: routeNames,
                    datasets: [
                        {
                            label: 'Avg Cost (₼)',
                            data: routeCosts,
                            borderColor: '#7C3AED',
                            backgroundColor: '#7C3AED22',
                            fill: true,
                            yAxisID: 'y',
                            tension: 0.3
                        },
                        {
                            label: 'Shipment Volume',
                            data: routeShipments,
                            type: 'bar',
                            backgroundColor: '#3B82F655',
                            borderColor: '#3B82F6',
                            borderWidth: 1.5,
                            yAxisID: 'y1'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { labels: { color: colors.text } }
                    },
                    scales: {
                        x: { grid: { color: colors.grid }, ticks: { color: colors.text } },
                        y: { position: 'left', grid: { color: colors.grid }, ticks: { color: colors.text } },
                        y1: { position: 'right', grid: { drawOnChartArea: false }, ticks: { color: colors.text } }
                    }
                }
            });

        } catch (error) {
            console.error('Failed to load chart metrics:', error);
            showToast('Unable to synchronize live metrics from database.', 'danger');
        }
    }

    loadChartData();
    window.addEventListener('themechanged', loadChartData);
    window.addEventListener('refresh-charts', loadChartData);
}

// 3. Interactive Vector Canvas Live TIR Map
function initLiveTIRMap() {
    const canvas = document.getElementById('tir-map-canvas');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const tooltip = document.getElementById('map-tooltip');
    
    // Map bounds
    let width = canvas.width = canvas.offsetWidth;
    let height = canvas.height = canvas.offsetHeight;

    window.addEventListener('resize', () => {
        width = canvas.width = canvas.offsetWidth;
        height = canvas.height = canvas.offsetHeight;
    });

    // Azerbaijan Hub locations relative coordinate positions (0 to 1)
    const azBorder = [
        {x: 0.0791, y: 0.1918},
        {x: 0.1283, y: 0.1482},
        {x: 0.1444, y: 0.1555},
        {x: 0.1593, y: 0.1636},
        {x: 0.1961, y: 0.1813},
        {x: 0.1905, y: 0.1979},
        {x: 0.2314, y: 0.2248},
        {x: 0.2500, y: 0.2206},
        {x: 0.2722, y: 0.2175},
        {x: 0.2918, y: 0.2415},
        {x: 0.3110, y: 0.2583},
        {x: 0.3185, y: 0.2468},
        {x: 0.3310, y: 0.2449},
        {x: 0.3362, y: 0.2213},
        {x: 0.3417, y: 0.2081},
        {x: 0.3438, y: 0.1974},
        {x: 0.3397, y: 0.1836},
        {x: 0.3343, y: 0.1758},
        {x: 0.3063, y: 0.1551},
        {x: 0.2857, y: 0.1368},
        {x: 0.2801, y: 0.1139},
        {x: 0.2730, y: 0.1060},
        {x: 0.2646, y: 0.0932},
        {x: 0.2725, y: 0.0656},
        {x: 0.2879, y: 0.0631},
        {x: 0.3075, y: 0.0308},
        {x: 0.3227, y: 0.0391},
        {x: 0.3286, y: 0.0576},
        {x: 0.3461, y: 0.0464},
        {x: 0.3529, y: 0.0402},
        {x: 0.3573, y: 0.0606},
        {x: 0.3765, y: 0.0765},
        {x: 0.3805, y: 0.0862},
        {x: 0.3957, y: 0.1147},
        {x: 0.4076, y: 0.1170},
        {x: 0.4171, y: 0.1257},
        {x: 0.4219, y: 0.1374},
        {x: 0.4253, y: 0.1468},
        {x: 0.4316, y: 0.1787},
        {x: 0.4515, y: 0.1995},
        {x: 0.4770, y: 0.2117},
        {x: 0.4917, y: 0.2084},
        {x: 0.5108, y: 0.2182},
        {x: 0.5346, y: 0.2110},
        {x: 0.5342, y: 0.1937},
        {x: 0.5414, y: 0.1806},
        {x: 0.5514, y: 0.1724},
        {x: 0.5830, y: 0.1369},
        {x: 0.6131, y: 0.1084},
        {x: 0.6347, y: 0.0575},
        {x: 0.6544, y: 0.0539},
        {x: 0.6768, y: 0.0965},
        {x: 0.6994, y: 0.1339},
        {x: 0.7070, y: 0.1501},
        {x: 0.7154, y: 0.1583},
        {x: 0.7301, y: 0.1960},
        {x: 0.7357, y: 0.2323},
        {x: 0.7658, y: 0.2989},
        {x: 0.7793, y: 0.3159},
        {x: 0.7918, y: 0.3249},
        {x: 0.7891, y: 0.3488},
        {x: 0.7919, y: 0.3598},
        {x: 0.7963, y: 0.3672},
        {x: 0.8114, y: 0.3732},
        {x: 0.8305, y: 0.3850},
        {x: 0.8526, y: 0.3826},
        {x: 0.8763, y: 0.3862},
        {x: 0.8834, y: 0.3981},
        {x: 0.9053, y: 0.4105},
        {x: 0.9161, y: 0.4267},
        {x: 0.9245, y: 0.4642},
        {x: 0.9272, y: 0.4808},
        {x: 0.9092, y: 0.4521},
        {x: 0.8894, y: 0.4441},
        {x: 0.8809, y: 0.4455},
        {x: 0.8636, y: 0.4529},
        {x: 0.8575, y: 0.4447},
        {x: 0.8410, y: 0.4492},
        {x: 0.8208, y: 0.4691},
        {x: 0.7907, y: 0.4935},
        {x: 0.7867, y: 0.5121},
        {x: 0.7772, y: 0.5290},
        {x: 0.7842, y: 0.5408},
        {x: 0.7796, y: 0.5500},
        {x: 0.7754, y: 0.5580},
        {x: 0.7784, y: 0.5748},
        {x: 0.7743, y: 0.5828},
        {x: 0.7752, y: 0.5899},
        {x: 0.7708, y: 0.5993},
        {x: 0.7720, y: 0.6101},
        {x: 0.7691, y: 0.6243},
        {x: 0.7589, y: 0.6475},
        {x: 0.7535, y: 0.6697},
        {x: 0.7718, y: 0.7029},
        {x: 0.7712, y: 0.7175},
        {x: 0.7694, y: 0.7203},
        {x: 0.7670, y: 0.7200},
        {x: 0.7728, y: 0.7326},
        {x: 0.7569, y: 0.7172},
        {x: 0.7461, y: 0.7650},
        {x: 0.7419, y: 0.7863},
        {x: 0.7274, y: 0.8175},
        {x: 0.7172, y: 0.8106},
        {x: 0.7284, y: 0.8032},
        {x: 0.7301, y: 0.7832},
        {x: 0.7185, y: 0.7672},
        {x: 0.7054, y: 0.7602},
        {x: 0.7007, y: 0.7699},
        {x: 0.6996, y: 0.7769},
        {x: 0.6986, y: 0.7965},
        {x: 0.6958, y: 0.8300},
        {x: 0.6822, y: 0.8456},
        {x: 0.6871, y: 0.8766},
        {x: 0.6787, y: 0.9609},
        {x: 0.6630, y: 0.9711},
        {x: 0.6469, y: 0.9741},
        {x: 0.6316, y: 0.9476},
        {x: 0.6215, y: 0.9307},
        {x: 0.6129, y: 0.9140},
        {x: 0.5947, y: 0.9103},
        {x: 0.5867, y: 0.8883},
        {x: 0.5532, y: 0.8590},
        {x: 0.5594, y: 0.8303},
        {x: 0.5895, y: 0.8179},
        {x: 0.5974, y: 0.8096},
        {x: 0.5995, y: 0.7985},
        {x: 0.5825, y: 0.7735},
        {x: 0.5679, y: 0.7381},
        {x: 0.5905, y: 0.7183},
        {x: 0.6011, y: 0.6986},
        {x: 0.5497, y: 0.6232},
        {x: 0.5426, y: 0.6233},
        {x: 0.5233, y: 0.6269},
        {x: 0.4921, y: 0.6564},
        {x: 0.4754, y: 0.6721},
        {x: 0.4448, y: 0.7011},
        {x: 0.4330, y: 0.7132},
        {x: 0.4077, y: 0.7325},
        {x: 0.3969, y: 0.7595},
        {x: 0.3821, y: 0.7670},
        {x: 0.3726, y: 0.7661},
        {x: 0.3632, y: 0.7831},
        {x: 0.3562, y: 0.7917},
        {x: 0.3389, y: 0.8127},
        {x: 0.3284, y: 0.8358},
        {x: 0.3172, y: 0.8427},
        {x: 0.3111, y: 0.8174},
        {x: 0.3141, y: 0.8039},
        {x: 0.3079, y: 0.7757},
        {x: 0.3021, y: 0.7535},
        {x: 0.3264, y: 0.7536},
        {x: 0.3304, y: 0.7500},
        {x: 0.3177, y: 0.7354},
        {x: 0.3117, y: 0.7205},
        {x: 0.2951, y: 0.6930},
        {x: 0.3136, y: 0.6847},
        {x: 0.3137, y: 0.6729},
        {x: 0.3188, y: 0.6609},
        {x: 0.3018, y: 0.6557},
        {x: 0.2903, y: 0.6436},
        {x: 0.2652, y: 0.6505},
        {x: 0.2542, y: 0.6325},
        {x: 0.2330, y: 0.6031},
        {x: 0.2074, y: 0.5840},
        {x: 0.1914, y: 0.5538},
        {x: 0.1695, y: 0.5422},
        {x: 0.2185, y: 0.5356},
        {x: 0.2255, y: 0.5142},
        {x: 0.2333, y: 0.4833},
        {x: 0.2266, y: 0.4702},
        {x: 0.2176, y: 0.4702},
        {x: 0.1709, y: 0.4328},
        {x: 0.1519, y: 0.4012},
        {x: 0.1488, y: 0.3875},
        {x: 0.1376, y: 0.3695},
        {x: 0.1477, y: 0.3423},
        {x: 0.1734, y: 0.3134},
        {x: 0.1634, y: 0.3038},
        {x: 0.1485, y: 0.2842},
        {x: 0.1447, y: 0.2656},
        {x: 0.1280, y: 0.2712},
        {x: 0.1086, y: 0.2601},
        {x: 0.0972, y: 0.2537},
        {x: 0.0877, y: 0.2490},
        {x: 0.1102, y: 0.2317},
        {x: 0.0869, y: 0.2183},
        {x: 0.0791, y: 0.1918}
    ];

    const azNakhchivanBorder = [
        {x: 0.2576, y: 0.8476},
        {x: 0.2561, y: 0.8479},
        {x: 0.2469, y: 0.8448},
        {x: 0.2365, y: 0.8385},
        {x: 0.2033, y: 0.8292},
        {x: 0.1997, y: 0.8273},
        {x: 0.1916, y: 0.8230},
        {x: 0.1776, y: 0.8228},
        {x: 0.1686, y: 0.8199},
        {x: 0.1643, y: 0.8197},
        {x: 0.1631, y: 0.8193},
        {x: 0.1623, y: 0.8191},
        {x: 0.1591, y: 0.8166},
        {x: 0.1566, y: 0.8157},
        {x: 0.1547, y: 0.8150},
        {x: 0.1512, y: 0.8127},
        {x: 0.1478, y: 0.8097},
        {x: 0.1460, y: 0.8068},
        {x: 0.1457, y: 0.8039},
        {x: 0.1462, y: 0.8016},
        {x: 0.1468, y: 0.7993},
        {x: 0.1472, y: 0.7965},
        {x: 0.1464, y: 0.7947},
        {x: 0.1427, y: 0.7925},
        {x: 0.1412, y: 0.7910},
        {x: 0.1404, y: 0.7887},
        {x: 0.1391, y: 0.7829},
        {x: 0.1385, y: 0.7808},
        {x: 0.1370, y: 0.7787},
        {x: 0.1355, y: 0.7775},
        {x: 0.1342, y: 0.7761},
        {x: 0.1331, y: 0.7734},
        {x: 0.1345, y: 0.7694},
        {x: 0.1336, y: 0.7665},
        {x: 0.1315, y: 0.7647},
        {x: 0.1293, y: 0.7642},
        {x: 0.1277, y: 0.7632},
        {x: 0.1278, y: 0.7609},
        {x: 0.1282, y: 0.7583},
        {x: 0.1277, y: 0.7566},
        {x: 0.1263, y: 0.7564},
        {x: 0.1248, y: 0.7571},
        {x: 0.1237, y: 0.7581},
        {x: 0.1233, y: 0.7586},
        {x: 0.1069, y: 0.7514},
        {x: 0.1028, y: 0.7531},
        {x: 0.1018, y: 0.7490},
        {x: 0.1001, y: 0.7355},
        {x: 0.0990, y: 0.7326},
        {x: 0.0977, y: 0.7300},
        {x: 0.0967, y: 0.7272},
        {x: 0.0939, y: 0.7186},
        {x: 0.0926, y: 0.7160},
        {x: 0.0911, y: 0.7149},
        {x: 0.0896, y: 0.7124},
        {x: 0.0883, y: 0.7096},
        {x: 0.0877, y: 0.7076},
        {x: 0.0869, y: 0.7063},
        {x: 0.0812, y: 0.7011},
        {x: 0.0806, y: 0.7001},
        {x: 0.0803, y: 0.6989},
        {x: 0.0797, y: 0.6978},
        {x: 0.0785, y: 0.6974},
        {x: 0.0768, y: 0.6975},
        {x: 0.0760, y: 0.6972},
        {x: 0.0720, y: 0.6934},
        {x: 0.0714, y: 0.6915},
        {x: 0.0727, y: 0.6882},
        {x: 0.0694, y: 0.6843},
        {x: 0.0675, y: 0.6789},
        {x: 0.0627, y: 0.6529},
        {x: 0.0609, y: 0.6470},
        {x: 0.0575, y: 0.6439},
        {x: 0.0582, y: 0.6431},
        {x: 0.0586, y: 0.6419},
        {x: 0.0550, y: 0.6417},
        {x: 0.0516, y: 0.6409},
        {x: 0.0510, y: 0.6404},
        {x: 0.0488, y: 0.6387},
        {x: 0.0483, y: 0.6379},
        {x: 0.0466, y: 0.6345},
        {x: 0.0448, y: 0.6243},
        {x: 0.0432, y: 0.6209},
        {x: 0.0477, y: 0.6183},
        {x: 0.0550, y: 0.6165},
        {x: 0.0619, y: 0.6166},
        {x: 0.0673, y: 0.6149},
        {x: 0.0714, y: 0.6119},
        {x: 0.0723, y: 0.6112},
        {x: 0.0781, y: 0.6053},
        {x: 0.0840, y: 0.6026},
        {x: 0.0894, y: 0.6062},
        {x: 0.0906, y: 0.6082},
        {x: 0.1010, y: 0.6258},
        {x: 0.1026, y: 0.6303},
        {x: 0.1033, y: 0.6353},
        {x: 0.1030, y: 0.6417},
        {x: 0.1015, y: 0.6514},
        {x: 0.1021, y: 0.6553},
        {x: 0.1052, y: 0.6580},
        {x: 0.1110, y: 0.6561},
        {x: 0.1155, y: 0.6506},
        {x: 0.1197, y: 0.6487},
        {x: 0.1207, y: 0.6506},
        {x: 0.1246, y: 0.6579},
        {x: 0.1264, y: 0.6635},
        {x: 0.1280, y: 0.6665},
        {x: 0.1303, y: 0.6678},
        {x: 0.1378, y: 0.6687},
        {x: 0.1405, y: 0.6706},
        {x: 0.1455, y: 0.6773},
        {x: 0.1455, y: 0.6774},
        {x: 0.1472, y: 0.6787},
        {x: 0.1490, y: 0.6791},
        {x: 0.1508, y: 0.6786},
        {x: 0.1525, y: 0.6774},
        {x: 0.1542, y: 0.6764},
        {x: 0.1669, y: 0.6657},
        {x: 0.1711, y: 0.6634},
        {x: 0.1904, y: 0.6572},
        {x: 0.1913, y: 0.6569},
        {x: 0.1949, y: 0.6568},
        {x: 0.1993, y: 0.6590},
        {x: 0.2028, y: 0.6624},
        {x: 0.2043, y: 0.6659},
        {x: 0.2043, y: 0.6704},
        {x: 0.2038, y: 0.6773},
        {x: 0.2038, y: 0.6773},
        {x: 0.2052, y: 0.6897},
        {x: 0.2045, y: 0.6939},
        {x: 0.1992, y: 0.7055},
        {x: 0.1982, y: 0.7110},
        {x: 0.1991, y: 0.7137},
        {x: 0.1995, y: 0.7150},
        {x: 0.2085, y: 0.7181},
        {x: 0.2117, y: 0.7216},
        {x: 0.2147, y: 0.7259},
        {x: 0.2185, y: 0.7298},
        {x: 0.2208, y: 0.7313},
        {x: 0.2297, y: 0.7372},
        {x: 0.2330, y: 0.7413},
        {x: 0.2340, y: 0.7434},
        {x: 0.2343, y: 0.7454},
        {x: 0.2340, y: 0.7474},
        {x: 0.2330, y: 0.7492},
        {x: 0.2292, y: 0.7559},
        {x: 0.2282, y: 0.7628},
        {x: 0.2296, y: 0.7699},
        {x: 0.2330, y: 0.7772},
        {x: 0.2370, y: 0.7850},
        {x: 0.2402, y: 0.7936},
        {x: 0.2484, y: 0.8242},
        {x: 0.2576, y: 0.8476}
    ];

    const hubs = {
        "Absheron":  { name: "Absheron (Baku)", x: 0.8958, y: 0.5216, active: true, size: 9, orders: 480, delay: 3.4 },
        "Ganja":     { name: "Ganja Hub", x: 0.3345, y: 0.4598, active: true, size: 7, orders: 190, delay: 5.2 },
        "Lankaran":  { name: "Lankaran Hub", x: 0.7330, y: 0.8962, active: true, size: 6, orders: 120, delay: 4.8 },
        "Khachmaz":  { name: "Khachmaz Hub", x: 0.7250, y: 0.2840, active: true, size: 6, orders: 110, delay: 7.1 },
        "Sheki":     { name: "Sheki Hub", x: 0.4641, y: 0.3451, active: true, size: 5, orders: 85, delay: 4.1 },
        "Yevlakh":   { name: "Yevlakh Junction", x: 0.4609, y: 0.4762, active: true, size: 7, orders: 140, delay: 3.9 },
        "Nakhchivan":{ name: "Nakhchivan Exclave", x: 0.1825, y: 0.7930, active: true, size: 5, orders: 60, delay: 12.5 },
        "Qazakh":    { name: "Qazakh Border", x: 0.1759, y: 0.3677, active: false, size: 4, orders: 35, delay: 2.1 },
        "Kalbajar":  { name: "Kalbajar Outpost", x: 0.2816, y: 0.5893, active: false, size: 4, orders: 15, delay: 15.0 },
        "Khankendi": { name: "Khankendi Hub", x: 0.3968, y: 0.6571, active: true, size: 5, orders: 50, delay: 8.4 }
    };

    const routes = [
        { from: "Absheron", to: "Ganja", status: "normal", distance: 362, delay: 5.2 },
        { from: "Absheron", to: "Lankaran", status: "normal", distance: 268, delay: 4.8 },
        { from: "Absheron", to: "Khachmaz", status: "warning", distance: 157, delay: 7.1 },
        { from: "Absheron", to: "Sheki", status: "normal", distance: 298, delay: 4.1 },
        { from: "Absheron", to: "Yevlakh", status: "normal", distance: 285, delay: 3.9 },
        { from: "Yevlakh", to: "Ganja", status: "normal", distance: 77, delay: 2.5 },
        { from: "Ganja", to: "Qazakh", status: "normal", distance: 106, delay: 2.1 },
        { from: "Yevlakh", to: "Khankendi", status: "normal", distance: 93, delay: 8.4 },
        { from: "Yevlakh", to: "Kalbajar", status: "warning", distance: 110, delay: 15.0 },
        { from: "Yevlakh", to: "Nakhchivan", status: "normal", distance: 320, delay: 12.5 }
    ];

    // Truck Simulation (overridden by database active shipments)
    let trucks = [
        { id: "T-101", from: "Absheron", to: "Ganja", vehicle: "TIR", progress: 0.12, speed: 0.0012, status: "in-transit" },
        { id: "T-102", from: "Absheron", to: "Lankaran", vehicle: "Gazelle", progress: 0.45, speed: 0.0018, status: "in-transit" },
        { id: "T-103", from: "Absheron", to: "Khachmaz", vehicle: "Mercedes Atego", progress: 0.82, speed: 0.0015, status: "delayed" },
        { id: "T-104", from: "Yevlakh", to: "Nakhchivan", vehicle: "TIR", progress: 0.65, speed: 0.0010, status: "in-transit" },
        { id: "T-105", from: "Absheron", to: "Sheki", vehicle: "Isuzu", progress: 0.31, speed: 0.0016, status: "in-transit" },
        { id: "T-106", from: "Yevlakh", to: "Kalbajar", vehicle: "avtomobil", progress: 0.55, speed: 0.0014, status: "delayed" }
    ];

    async function loadActiveTrucks() {
        try {
            const res = await fetch(`${API_BASE}/predict/shipments`);
            if (res.ok) {
                const list = await res.json();
                // Filter shipments that are in-transit, delayed, or pending (treated as in-transit on map)
                const activeShipments = list.filter(s => s.status === 'in-transit' || s.status === 'delayed' || s.status === 'pending');
                if (activeShipments.length > 0) {
                    trucks = activeShipments.map((s, idx) => ({
                        id: s.id,
                        from: "Absheron",
                        to: s.destination,
                        vehicle: s.vehicle,
                        progress: 0.1 + (idx * 0.15) % 0.75,
                        speed: 0.001 + (idx * 0.0003) % 0.001,
                        status: s.status === 'pending' ? 'in-transit' : s.status
                    }));
                }
                const trucksCountEl = document.getElementById('telemetry-trucks');
                if (trucksCountEl) {
                    trucksCountEl.textContent = trucks.length;
                }
            }
        } catch (e) {
            console.error("Failed to load active trucks from DB:", e);
        }
    }
    loadActiveTrucks();

    // Reload trucks when map refresh is triggered
    window.addEventListener('refresh-map', loadActiveTrucks);

    // Pan & Zoom state
    let zoom = 1.0;
    let offsetX = 0;
    let offsetY = 0;
    let isDragging = false;
    let startX, startY;
    
    // Particles along trails
    const flowParticles = [];
    const maxParticles = 40;
    
    for (let i = 0; i < maxParticles; i++) {
        const route = routes[Math.floor(Math.random() * routes.length)];
        flowParticles.push({
            route: route,
            progress: Math.random(),
            speed: Math.random() * 0.004 + 0.002
        });
    }

    // Convert relative coordinates to screen coordinates
    function getScreenCoords(rx, ry) {
        // Center and scale map representation
        const scale = Math.min(width, height) * 0.85 * zoom;
        const originX = (width - scale) / 2 + offsetX;
        const originY = (height - scale) / 2 + offsetY;
        
        // Offset Nakhchivan exclave visual representation slightly for readability
        let px = rx;
        let py = ry;
        
        return {
            x: originX + px * scale,
            y: originY + py * scale
        };
    }

    // Reverse convert screen coordinates to relative map coordinates
    function getMapCoords(sx, sy) {
        const scale = Math.min(width, height) * 0.85 * zoom;
        const originX = (width - scale) / 2 + offsetX;
        const originY = (height - scale) / 2 + offsetY;
        return {
            rx: (sx - originX) / scale,
            ry: (sy - originY) / scale
        };
    }

    // Animation frames loop
    let pulseAngle = 0;
    
    function drawMap() {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        ctx.fillStyle = isDark ? '#09090b' : '#FAFAFA';
        ctx.fillRect(0, 0, width, height);

        // Draw high-tech grid background dot matrix (highly premium look)
        ctx.fillStyle = isDark ? 'rgba(255, 255, 255, 0.04)' : 'rgba(0, 0, 0, 0.05)';
        const gridSize = 40 * zoom;
        const startGridX = offsetX % gridSize;
        const startGridY = offsetY % gridSize;
        for (let x = startGridX; x < width; x += gridSize) {
            for (let y = startGridY; y < height; y += gridSize) {
                ctx.beginPath();
                ctx.arc(x, y, 1.0, 0, Math.PI * 2);
                ctx.fill();
            }
        }

        // Draw Azerbaijan Country Shading & Outline
        function drawCountryOutline(points, fillColor, strokeColor, lineWidth) {
            if (!points || points.length === 0) return;
            ctx.beginPath();
            const start = getScreenCoords(points[0].x, points[0].y);
            ctx.moveTo(start.x, start.y);
            for (let i = 1; i < points.length; i++) {
                const pt = getScreenCoords(points[i].x, points[i].y);
                ctx.lineTo(pt.x, pt.y);
            }
            ctx.closePath();
            
            if (fillColor) {
                ctx.fillStyle = fillColor;
                ctx.fill();
            }
            if (strokeColor) {
                ctx.strokeStyle = strokeColor;
                ctx.lineWidth = lineWidth;
                ctx.stroke();
            }
        }

        // Main body shading and border (with premium neon glow)
        ctx.shadowColor = isDark ? 'rgba(124, 58, 237, 0.45)' : 'rgba(124, 58, 237, 0.2)';
        ctx.shadowBlur = 15;
        drawCountryOutline(
            azBorder,
            isDark ? 'rgba(124, 58, 237, 0.018)' : 'rgba(124, 58, 237, 0.01)',
            isDark ? 'rgba(124, 58, 237, 0.28)' : 'rgba(124, 58, 237, 0.38)',
            1.8
        );
        // Neon contour overlay
        ctx.shadowBlur = 0; // reset glow for overlay
        drawCountryOutline(
            azBorder,
            null,
            isDark ? 'rgba(124, 58, 237, 0.15)' : 'rgba(124, 58, 237, 0.25)',
            0.8
        );

        // Nakhchivan shading and border (with premium neon glow)
        ctx.shadowColor = isDark ? 'rgba(124, 58, 237, 0.45)' : 'rgba(124, 58, 237, 0.2)';
        ctx.shadowBlur = 15;
        drawCountryOutline(
            azNakhchivanBorder,
            isDark ? 'rgba(124, 58, 237, 0.018)' : 'rgba(124, 58, 237, 0.01)',
            isDark ? 'rgba(124, 58, 237, 0.28)' : 'rgba(124, 58, 237, 0.38)',
            1.8
        );
        // Nakhchivan contour overlay
        ctx.shadowBlur = 0; // reset glow
        drawCountryOutline(
            azNakhchivanBorder,
            null,
            isDark ? 'rgba(124, 58, 237, 0.15)' : 'rgba(124, 58, 237, 0.25)',
            0.8
        );

        pulseAngle += 0.05;

        // 1. Draw Route Lines (glow and network paths)
        routes.forEach(route => {
            const startNode = hubs[route.from];
            const endNode = hubs[route.to];
            if (!startNode || !endNode) return;

            const p1 = getScreenCoords(startNode.x, startNode.y);
            const p2 = getScreenCoords(endNode.x, endNode.y);

            // Path background
            ctx.strokeStyle = 'rgba(124, 58, 237, 0.08)';
            ctx.lineWidth = 3.5;
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();

            // Main routing line
            ctx.lineWidth = 1.5;
            if (route.status === 'warning') {
                ctx.strokeStyle = 'rgba(245, 158, 11, 0.35)'; // warning amber
            } else {
                ctx.strokeStyle = 'rgba(34, 197, 94, 0.3)'; // success green
            }
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
        });

        // 2. Draw Moving Flow Particles (Light Trails)
        flowParticles.forEach(p => {
            const startNode = hubs[p.route.from];
            const endNode = hubs[p.route.to];
            if (!startNode || !endNode) return;

            const p1 = getScreenCoords(startNode.x, startNode.y);
            const p2 = getScreenCoords(endNode.x, endNode.y);

            // Interpolate position
            const x = p1.x + (p2.x - p1.x) * p.progress;
            const y = p1.y + (p2.y - p1.y) * p.progress;

            ctx.fillStyle = p.route.status === 'warning' ? '#F59E0B' : '#a78bfa';
            ctx.beginPath();
            ctx.arc(x, y, 1.5, 0, Math.PI * 2);
            ctx.shadowBlur = 6;
            ctx.shadowColor = ctx.fillStyle;
            ctx.fill();
            ctx.shadowBlur = 0; // reset

            // Update particle progress
            p.progress += p.speed;
            if (p.progress > 1) {
                p.progress = 0;
            }
        });

        // 3. Draw Moving Trucks
        trucks.forEach(t => {
            const startNode = hubs[t.from];
            const endNode = hubs[t.to];
            if (!startNode || !endNode) return;

            const p1 = getScreenCoords(startNode.x, startNode.y);
            const p2 = getScreenCoords(endNode.x, endNode.y);

            const x = p1.x + (p2.x - p1.x) * t.progress;
            const y = p1.y + (p2.y - p1.y) * t.progress;

            // Update truck progress
            t.progress += t.speed;
            if (t.progress > 1) {
                t.progress = 0;
                // Swap direction or keep loop
            }

            // Draw motion trails (3 particles trailing behind the truck)
            const trailCount = 3;
            for (let i = 1; i <= trailCount; i++) {
                const trailProgress = Math.max(0, t.progress - (i * 0.012));
                const tx = p1.x + (p2.x - p1.x) * trailProgress;
                const ty = p1.y + (p2.y - p1.y) * trailProgress;
                const alpha = 0.45 - (i * 0.12);
                ctx.fillStyle = t.status === 'delayed' ? `rgba(239, 68, 68, ${alpha})` : `rgba(34, 197, 94, ${alpha})`;
                ctx.beginPath();
                ctx.arc(tx, ty, 3.5 - (i * 0.6), 0, Math.PI * 2);
                ctx.fill();
            }

            // Draw truck dot indicator
            ctx.fillStyle = t.status === 'delayed' ? '#EF4444' : '#22C55E';
            ctx.beginPath();
            ctx.arc(x, y, 4.5, 0, Math.PI * 2);
            ctx.fill();
            
            // Draw dynamic pulsing radar ring
            ctx.strokeStyle = ctx.fillStyle;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.arc(x, y, 8 + Math.sin(pulseAngle * 1.5) * 2, 0, Math.PI * 2);
            ctx.stroke();

            // Label truck with subtle backdrop shadow
            ctx.fillStyle = isDark ? '#ffffff' : '#000000';
            ctx.font = 'bold 9px var(--font-mono)';
            ctx.fillText(t.id, x + 8, y + 3);
        });

        // 4. Draw Hub Nodes (Pulsing glowing circles and radar style rings)
        Object.entries(hubs).forEach(([id, hub]) => {
            const coords = getScreenCoords(hub.x, hub.y);

            // Glow Pulse Effect
            if (hub.active) {
                // Expanding glowing ripple for Absheron (Central Hub)
                if (id === 'Absheron') {
                    const rippleRadius1 = hub.size * 2.2 + ((pulseAngle * 12) % 24);
                    const rippleOpacity1 = Math.max(0, 0.4 - (rippleRadius1 - hub.size * 2.2) / 24);
                    ctx.strokeStyle = `rgba(124, 58, 237, ${rippleOpacity1})`;
                    ctx.lineWidth = 1.2;
                    ctx.beginPath();
                    ctx.arc(coords.x, coords.y, rippleRadius1, 0, Math.PI * 2);
                    ctx.stroke();

                    const rippleRadius2 = hub.size * 2.2 + (((pulseAngle * 12) + 12) % 24);
                    const rippleOpacity2 = Math.max(0, 0.4 - (rippleRadius2 - hub.size * 2.2) / 24);
                    ctx.strokeStyle = `rgba(124, 58, 237, ${rippleOpacity2})`;
                    ctx.lineWidth = 1.2;
                    ctx.beginPath();
                    ctx.arc(coords.x, coords.y, rippleRadius2, 0, Math.PI * 2);
                    ctx.stroke();
                }

                const pulseSize = hub.size * 1.6 + Math.sin(pulseAngle * 2.0) * 3;
                ctx.fillStyle = id === 'Absheron' ? 'rgba(124, 58, 237, 0.18)' : 'rgba(139, 92, 246, 0.08)';
                ctx.beginPath();
                ctx.arc(coords.x, coords.y, pulseSize, 0, Math.PI * 2);
                ctx.fill();

                // Thin elegant outer ring
                ctx.strokeStyle = id === 'Absheron' ? 'rgba(124, 58, 237, 0.5)' : (isDark ? 'rgba(255, 255, 255, 0.12)' : 'rgba(0, 0, 0, 0.15)');
                ctx.lineWidth = 0.8;
                ctx.beginPath();
                ctx.arc(coords.x, coords.y, hub.size + 4, 0, Math.PI * 2);
                ctx.stroke();
            }

            // Central core node
            ctx.fillStyle = id === 'Absheron' ? '#7C3AED' : (isDark ? '#FAFAFA' : '#18181B');
            ctx.beginPath();
            ctx.arc(coords.x, coords.y, hub.size, 0, Math.PI * 2);
            ctx.fill();
            ctx.strokeStyle = isDark ? 'rgba(0,0,0,0.6)' : 'rgba(255,255,255,0.9)';
            ctx.lineWidth = 1.8;
            ctx.stroke();

            // Label Node
            ctx.fillStyle = isDark ? '#E4E4E7' : '#27272A';
            ctx.font = '600 11px var(--font-sans)';
            ctx.textAlign = 'center';
            ctx.fillText(id, coords.x, coords.y - hub.size - 8);
        });
        
        requestAnimationFrame(drawMap);
    }

    drawMap();

    // Map Pan/Zoom interactions
    canvas.addEventListener('mousedown', (e) => {
        isDragging = true;
        startX = e.clientX - offsetX;
        startY = e.clientY - offsetY;
    });

    window.addEventListener('mouseup', () => {
        isDragging = false;
    });

    canvas.addEventListener('mousemove', (e) => {
        const rect = canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;
        
        if (isDragging) {
            offsetX = e.clientX - startX;
            offsetY = e.clientY - startY;
            return;
        }

        // Hover detection for hubs
        let foundHover = false;
        Object.entries(hubs).forEach(([id, hub]) => {
            const hC = getScreenCoords(hub.x, hub.y);
            const dist = Math.hypot(mouseX - hC.x, mouseY - hC.y);
            
            if (dist < 15) {
                foundHover = true;
                canvas.style.cursor = 'pointer';
                
                // Show tooltip
                tooltip.style.display = 'block';
                tooltip.style.left = `${mouseX + 15}px`;
                tooltip.style.top = `${mouseY + 15}px`;
                tooltip.innerHTML = `
                    <div style="font-weight:700; color:var(--primary-lighter); border-bottom:1px solid rgba(255,255,255,0.08); padding-bottom:4px; margin-bottom:6px;">${hub.name}</div>
                    <div style="display:flex; justify-content:space-between; margin-bottom:3px;"><span style="color:#a1a1aa">Active Orders:</span> <span style="font-family:var(--font-mono); font-weight:600;">${hub.orders}</span></div>
                    <div style="display:flex; justify-content:space-between; margin-bottom:3px;"><span style="color:#a1a1aa">Desi Volume:</span> <span style="font-family:var(--font-mono); font-weight:600;">${Math.round(hub.orders * 4.2)} Desi</span></div>
                    <div style="display:flex; justify-content:space-between;"><span style="color:#a1a1aa">Delay Risk:</span> <span style="font-family:var(--font-mono); font-weight:600; color:${hub.delay > 6 ? 'var(--warning)' : 'var(--success)'}">${hub.delay}%</span></div>
                `;
            }
        });

        // Hover detection for trucks
        if (!foundHover) {
            trucks.forEach(t => {
                const sN = hubs[t.from];
                const eN = hubs[t.to];
                if (!sN || !eN) return;
                
                const p1 = getScreenCoords(sN.x, sN.y);
                const p2 = getScreenCoords(eN.x, eN.y);
                
                const tx = p1.x + (p2.x - p1.x) * t.progress;
                const ty = p1.y + (p2.y - p1.y) * t.progress;
                
                const dist = Math.hypot(mouseX - tx, mouseY - ty);
                if (dist < 12) {
                    foundHover = true;
                    canvas.style.cursor = 'pointer';
                    
                    tooltip.style.display = 'block';
                    tooltip.style.left = `${mouseX + 15}px`;
                    tooltip.style.top = `${mouseY + 15}px`;
                    tooltip.innerHTML = `
                        <div style="font-weight:700; color:var(--success); border-bottom:1px solid rgba(255,255,255,0.08); padding-bottom:4px; margin-bottom:6px;">Truck telemetry: ${t.id}</div>
                        <div style="margin-bottom:3px;"><span style="color:#a1a1aa">Route:</span> <b>${t.from} ➔ ${t.to}</b></div>
                        <div style="margin-bottom:3px;"><span style="color:#a1a1aa">Type:</span> <b>${t.vehicle}</b></div>
                        <div style="margin-bottom:3px;"><span style="color:#a1a1aa">Transit Progress:</span> <b>${Math.round(t.progress * 100)}%</b></div>
                        <div><span style="color:#a1a1aa">Status:</span> <span style="color:${t.status === 'delayed' ? 'var(--danger)' : 'var(--success)'}; font-weight:600;">${t.status.toUpperCase()}</span></div>
                    `;
                }
            });
        }

        if (!foundHover) {
            canvas.style.cursor = isDragging ? 'grabbing' : 'grab';
            tooltip.style.display = 'none';
        }
    });

    // Control triggers
    const zoomIn = document.getElementById('map-zoom-in');
    const zoomOut = document.getElementById('map-zoom-out');
    const mapReset = document.getElementById('map-reset');
    
    if (zoomIn) zoomIn.addEventListener('click', () => { zoom *= 1.2; });
    if (zoomOut) zoomOut.addEventListener('click', () => { zoom /= 1.2; });
    if (mapReset) mapReset.addEventListener('click', () => { zoom = 1.0; offsetX = 0; offsetY = 0; });

    window.addEventListener('refresh-map', () => {
        // Trigger brief simulated re-routing of trucks
        trucks.forEach(t => {
            t.progress = Math.random() * 0.5;
        });
        showToast('Telemetry refreshed at 120Hz.', 'success');
    });
}

// 4. Slide-over AI Chat Panel Drawer System
function initAIAssistant() {
    const trigger = document.getElementById('ai-assistant-trigger');
    const closeBtn = document.getElementById('ai-panel-close');
    const overlay = document.getElementById('ai-overlay');
    const panel = document.getElementById('ai-panel');
    
    const sendBtn = document.getElementById('ai-chat-send');
    const chatInput = document.getElementById('ai-chat-input');
    const messagesBox = document.getElementById('ai-messages');

    if (!panel) return;

    // Toggle drawer open/close
    if (trigger) {
        trigger.addEventListener('click', () => {
            panel.classList.add('open');
            overlay.classList.add('active');
        });
    }

    const chatToggle = document.getElementById('chat-toggle');
    if (chatToggle) {
        chatToggle.addEventListener('click', () => {
            panel.classList.add('open');
            overlay.classList.add('active');
        });
    }

    closeBtn.addEventListener('click', closePanel);
    overlay.addEventListener('click', closePanel);

    function closePanel() {
        panel.classList.remove('open');
        overlay.classList.remove('active');
    }

    // Suggested quick prompt actions
    const suggestedBtns = document.querySelectorAll('.suggested-prompt-btn');
    suggestedBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const prompt = btn.getAttribute('data-prompt');
            chatInput.value = prompt;
            sendChatMessage();
        });
    });

    // Send chat logic
    sendBtn.addEventListener('click', sendChatMessage);
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') sendChatMessage();
    });

    async function sendChatMessage() {
        const text = chatInput.value.trim();
        if (!text) return;

        chatInput.value = '';

        // Append User Bubble
        const userMsg = document.createElement('div');
        userMsg.className = 'chat-msg user';
        userMsg.textContent = text;
        messagesBox.appendChild(userMsg);
        messagesBox.scrollTop = messagesBox.scrollHeight;

        // Append Assistant Streaming Bubble with initial Thinking status
        const assistantMsg = document.createElement('div');
        assistantMsg.className = 'chat-msg assistant';
        
        const thinkingIndicator = document.createElement('div');
        thinkingIndicator.className = 'chat-msg-thinking';
        thinkingIndicator.innerHTML = `
            <span>Thinking</span>
            <div class="thinking-dot"></div>
            <div class="thinking-dot"></div>
            <div class="thinking-dot"></div>
        `;
        assistantMsg.appendChild(thinkingIndicator);
        messagesBox.appendChild(assistantMsg);
        messagesBox.scrollTop = messagesBox.scrollHeight;

        // Fetch stream response using Server-Sent Events (SSE)
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
                    
                    // Simple Markdown / HTML renderer helper for chat streaming
                    assistantMsg.innerHTML = renderMarkdown(buffer);
                    messagesBox.scrollTop = messagesBox.scrollHeight;
                }

                if (data.done) {
                    eventSource.close();
                    // Inject copy actions, code highlight triggers if needed here
                }
            };

            eventSource.onerror = (err) => {
                console.error('SSE connection error:', err);
                eventSource.close();
                
                // Fallback direct POST response if EventSource drops or gets blocked
                fetch(`${API_BASE}/chat/message`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({ message: text })
                }).then(res => res.json()).then(data => {
                    assistantMsg.innerHTML = renderMarkdown(data.response || 'Connection lost.');
                    messagesBox.scrollTop = messagesBox.scrollHeight;
                }).catch(() => {
                    thinkingIndicator.innerHTML = '<span style="color:var(--danger)">Connection to server timed out.</span>';
                });
            };

        } catch (err) {
            console.error(err);
            thinkingIndicator.innerHTML = '<span style="color:var(--danger)">Failed to establish chat session.</span>';
        }
    }
}

// Minimal markdown table, YAML & lists renderer
function renderMarkdown(md) {
    let html = md;

    // Convert YAML blocks
    html = html.replace(/```yaml([\s\S]*?)```/g, '<pre><code class="language-yaml">$1</code></pre>');
    // Convert generic code blocks
    html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');

    // Bold / italic — must run before the table/list regexes below, since
    // those operate line-by-line and would otherwise leave raw ** markers
    // sitting inside <td>/<li> content.
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/(?<!\*)\*([^*\n]+)\*(?!\*)/g, '<em>$1</em>');

    // Markdown table separator rows (e.g. "|:---|:---|:---|") carry no
    // content — without stripping them they render as a garbage row full
    // of dashes above the real data.
    html = html.replace(/^\s*\|?[\s:|-]*-[\s:|-]*\|[\s:|-]*\s*$/gm, '');

    // Markdown lists
    html = html.replace(/^\*\s+(.*)$/gm, '<li>$1</li>');
    html = html.replace(/^- (.*)$/gm, '<li>$1</li>');
    
    // Wrap lists in ul
    html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

    // Markdown headers
    html = html.replace(/^### (.*)$/gm, '<h4 style="margin: 10px 0 6px 0; font-weight:600;">$1</h4>');
    
    // Tables
    html = html.replace(/\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|/g, (match, p1, p2, p3, p4) => {
        return `<tr><td>${p1.trim()}</td><td>${p2.trim()}</td><td>${p3.trim()}</td><td>${p4.trim()}</td></tr>`;
    });
    html = html.replace(/\|([^|]+)\|([^|]+)\|([^|]+)\|/g, (match, p1, p2, p3) => {
        return `<tr><td>${p1.trim()}</td><td>${p2.trim()}</td><td>${p3.trim()}</td></tr>`;
    });
    
    // Wrap rows in table element
    html = html.replace(/((?:<tr>(?:<td>[^<]*<\/td>)+<\/tr>\s*)+)/g, '<table class="chat-md-table">$1</table>');
    
    // Clean double linebreaks
    html = html.replace(/\n/g, '<br>');

    return html;
}

// 5. Driver Management Tab Control & CRUD
let allDrivers = [];
let editingDriverId = null;

// 5b. Driver password visibility toggle (register/edit modal)
function initDriverPasswordToggle() {
    const toggleBtn = document.getElementById('driver-password-toggle');
    const passwordInput = document.getElementById('driver-password-input');
    if (!toggleBtn || !passwordInput) return;

    toggleBtn.addEventListener('click', () => {
        const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordInput.setAttribute('type', type);

        // Lucide replaces the original <i data-lucide="..."> with a
        // rendered <svg> on page load, so look for either.
        const icon = toggleBtn.querySelector('svg, i');
        if (!icon) return;
        icon.setAttribute('data-lucide', type === 'text' ? 'eye-off' : 'eye');

        if (window.lucide) {
            lucide.createIcons({ node: toggleBtn });
        }
    });
}

function initDriverManagement() {
    const sideNavOverview = document.getElementById('side-nav-overview');
    const sideNavDrivers = document.getElementById('side-nav-drivers');
    const viewOverview = document.getElementById('view-overview');
    const viewDrivers = document.getElementById('view-drivers');

    if (!sideNavOverview || !sideNavDrivers || !viewOverview || !viewDrivers) return;

    // View toggles
    sideNavOverview.addEventListener('click', (e) => {
        e.preventDefault();
        sideNavOverview.classList.add('active');
        sideNavDrivers.classList.remove('active');
        viewOverview.style.display = 'block';
        viewDrivers.style.display = 'none';
        
        // Trigger chart redraw to prevent canvas size rendering bugs
        window.dispatchEvent(new CustomEvent('refresh-charts'));
    });

    sideNavDrivers.addEventListener('click', (e) => {
        e.preventDefault();
        sideNavDrivers.classList.add('active');
        sideNavOverview.classList.remove('active');
        viewOverview.style.display = 'none';
        viewDrivers.style.display = 'block';
        
        loadDriversList();
    });

    // Modal Control
    const modal = document.getElementById('register-driver-modal');
    const overlay = document.getElementById('driver-modal-overlay');
    const btnOpen = document.getElementById('btn-open-register-driver');
    const btnClose = document.getElementById('btn-close-register-modal');

    if (btnOpen && modal && overlay && btnClose) {
        btnOpen.addEventListener('click', () => {
            editingDriverId = null;
            document.getElementById('register-driver-form').reset();
            const pwField = document.getElementById('driver-password-input');
            pwField.required = true;
            pwField.closest('.form-group').style.display = '';
            const submitBtn = form0Submit();
            if (submitBtn) submitBtn.textContent = 'Register Driver';
            modal.style.display = 'block';
            overlay.style.display = 'block';
        });

        function form0Submit() {
            const f = document.getElementById('register-driver-form');
            return f ? f.querySelector('button[type="submit"]') : null;
        }

        const closeModal = () => {
            modal.style.display = 'none';
            overlay.style.display = 'none';
            document.getElementById('register-driver-form').reset();
            editingDriverId = null;
        };

        btnClose.addEventListener('click', closeModal);
        overlay.addEventListener('click', closeModal);

        // Submit form — handles both "create" (POST) and "edit" (PATCH)
        const form = document.getElementById('register-driver-form');
        if (form) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const name = document.getElementById('driver-name-input').value.trim();
                const phone = document.getElementById('driver-phone-input').value.trim();
                const vehicle = document.getElementById('driver-vehicle-input').value.trim();
                const plate = document.getElementById('driver-plate-input').value.trim();
                const password = document.getElementById('driver-password-input').value.trim();

                const token = localStorage.getItem('access_token');

                if (editingDriverId) {
                    // Edit mode — PATCH, no password involved.
                    try {
                        const response = await fetch(`${API_BASE}/api/drivers/${editingDriverId}`, {
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

                        if (response.ok) {
                            showToast('Driver updated.', 'success');
                            closeModal();
                            loadDriversList();
                        } else {
                            const err = await response.json();
                            showToast(err.detail || 'Update failed.', 'danger');
                        }
                    } catch (error) {
                        showToast('Failed to update driver due to network error.', 'danger');
                    }
                    return;
                }

                // Create mode — POST, password required.
                if (password.length < 4) {
                    showToast('Password must be at least 4 characters.', 'warning');
                    return;
                }

                try {
                    const response = await fetch(`${API_BASE}/api/drivers`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${token}`
                        },
                        body: JSON.stringify({
                            name: name,
                            phone: phone,
                            vehicle_type: vehicle,
                            vehicle_number: plate,
                            password: password
                        })
                    });

                    if (response.ok) {
                        const data = await response.json();
                        showToast(`Driver successfully registered! Generated ID: ${data.driver_id}`, 'success');
                        closeModal();
                        loadDriversList();
                    } else {
                        const err = await response.json();
                        showToast(err.detail || 'Registration failed.', 'danger');
                    }
                } catch (error) {
                    showToast('Failed to register driver due to network error.', 'danger');
                }
            });
        }
    }

    // Search filter
    const searchInput = document.getElementById('driver-search-input');
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            const query = searchInput.value.toLowerCase().trim();
            filterDrivers(query);
        });
    }
}

async function loadDriversList() {
    const tableBody = document.getElementById('drivers-table-body');
    if (!tableBody) return;

    tableBody.innerHTML = `
        <tr>
            <td colspan="7" style="padding: 32px; text-align: center; color: var(--text-muted);">
                <div style="display: inline-block; animation: spin 1s linear infinite; margin-bottom: 8px;">
                    <i data-lucide="loader-2" style="width: 24px; height: 24px;"></i>
                </div>
                <div>Fetching active fleet operators...</div>
            </td>
        </tr>
    `;
    if (window.lucide) lucide.createIcons({ node: tableBody });

    const token = localStorage.getItem('access_token');
    try {
        const response = await fetch(`${API_BASE}/api/drivers`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            allDrivers = await response.json();
            renderDrivers(allDrivers);
        } else {
            tableBody.innerHTML = `<tr><td colspan="7" style="padding: 24px; text-align: center; color: var(--danger);">Failed to load drivers list.</td></tr>`;
        }
    } catch (error) {
        tableBody.innerHTML = `<tr><td colspan="7" style="padding: 24px; text-align: center; color: var(--danger);">Network error while loading drivers list.</td></tr>`;
    }
}

function renderDrivers(drivers) {
    const tableBody = document.getElementById('drivers-table-body');
    if (!tableBody) return;

    if (drivers.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="7" style="padding: 24px; text-align: center; color: var(--text-muted);">No drivers registered in the network.</td></tr>`;
        return;
    }

    tableBody.innerHTML = drivers.map(d => {
        const statusOptions = ['Offline', 'Active', 'On Duty'].map(s =>
            `<option value="${s}" ${d.status === s ? 'selected' : ''}>${s}</option>`
        ).join('');

        return `
            <tr style="border-bottom: 1px solid var(--border);">
                <td style="padding: 16px; font-family: var(--font-mono); font-size: 13px; font-weight: 600; color: var(--primary-lighter);"><code>${d.driver_id}</code></td>
                <td style="padding: 16px; font-size: 14px; font-weight: 500; color: var(--text-main);">${d.name}</td>
                <td style="padding: 16px; font-size: 13px; color: var(--text-muted);">${d.phone}</td>
                <td style="padding: 16px; font-size: 13px; color: var(--text-muted);">${d.vehicle_type}</td>
                <td style="padding: 16px; font-family: var(--font-mono); font-size: 13px; color: var(--text-main);">${d.vehicle_number}</td>
                <td style="padding: 16px;">
                    <select class="form-control" style="padding: 4px 8px; font-size: 12px; width: auto;" onchange="updateDriverStatus('${d.driver_id}', this.value)">
                        ${statusOptions}
                    </select>
                </td>
                <td style="padding: 16px; white-space: nowrap;">
                    <button type="button" class="btn btn-secondary" style="padding: 4px 10px; font-size: 12px; margin-right: 6px;" onclick='openEditDriverModal(${JSON.stringify(d).replace(/'/g, "&apos;")})'>Edit</button>
                    <button type="button" class="btn btn-danger" style="padding: 4px 10px; font-size: 12px; background: rgba(239,68,68,0.15); color: var(--danger, #EF4444); border: 1px solid rgba(239,68,68,0.3); border-radius: 6px;" onclick="deleteDriver('${d.driver_id}')">Delete</button>
                </td>
            </tr>
        `;
    }).join('');

    if (window.lucide) {
        lucide.createIcons({ node: tableBody });
    }
}

function openEditDriverModal(driver) {
    const modal = document.getElementById('register-driver-modal');
    const overlay = document.getElementById('driver-modal-overlay');
    if (!modal || !overlay) return;

    editingDriverId = driver.driver_id;
    document.getElementById('driver-name-input').value = driver.name;
    document.getElementById('driver-phone-input').value = driver.phone;
    document.getElementById('driver-vehicle-input').value = driver.vehicle_type;
    document.getElementById('driver-plate-input').value = driver.vehicle_number;

    // Password isn't editable here (PATCH doesn't take one) — hide the field.
    const pwField = document.getElementById('driver-password-input');
    pwField.required = false;
    pwField.value = '';
    pwField.closest('.form-group').style.display = 'none';

    const submitBtn = document.getElementById('register-driver-form').querySelector('button[type="submit"]');
    if (submitBtn) submitBtn.textContent = 'Save Changes';

    modal.style.display = 'block';
    overlay.style.display = 'block';
}

async function updateDriverStatus(driverId, newStatus) {
    const token = localStorage.getItem('access_token');
    try {
        const response = await fetch(`${API_BASE}/api/drivers/${driverId}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ status: newStatus })
        });
        if (response.ok) {
            showToast(`Status updated to ${newStatus}.`, 'success');
            const d = allDrivers.find(x => x.driver_id === driverId);
            if (d) d.status = newStatus;
        } else {
            showToast('Failed to update status.', 'danger');
            loadDriversList();
        }
    } catch (error) {
        showToast('Network error while updating status.', 'danger');
        loadDriversList();
    }
}

async function deleteDriver(driverId) {
    if (!confirm(`Delete driver ${driverId}? This cannot be undone.`)) return;

    const token = localStorage.getItem('access_token');
    try {
        const response = await fetch(`${API_BASE}/api/drivers/${driverId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (response.ok || response.status === 204) {
            showToast(`Driver ${driverId} deleted.`, 'success');
            loadDriversList();
        } else {
            showToast('Failed to delete driver.', 'danger');
        }
    } catch (error) {
        showToast('Network error while deleting driver.', 'danger');
    }
}

function filterDrivers(query) {
    const filtered = allDrivers.filter(d => 
        d.name.toLowerCase().includes(query) ||
        d.driver_id.toLowerCase().includes(query) ||
        d.phone.toLowerCase().includes(query) ||
        d.vehicle_type.toLowerCase().includes(query) ||
        d.vehicle_number.toLowerCase().includes(query)
    );
    renderDrivers(filtered);
}