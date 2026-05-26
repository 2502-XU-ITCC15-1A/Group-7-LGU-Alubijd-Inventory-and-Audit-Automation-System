(function () {
    'use strict';

    // ── Dashboard Charts ───────────────────────────
    window.initDashboardCharts = function() {
        const emergencyCtx = document.getElementById('emergencyChart');
        if (!emergencyCtx) return;

        const commonOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { enabled: true }
            },
            scales: {
                x: { display: true, grid: { display: false } },
                y: { display: true, beginAtZero: true, max: 100 }
            }
        };

        function createGradient(ctx) {
            let gradient = ctx.createLinearGradient(0, 0, 0, 120);
            gradient.addColorStop(0, 'rgba(49, 68, 155, 0.5)');
            gradient.addColorStop(1, 'rgba(49, 68, 155, 0.0)');
            return gradient;
        }

        // Chart 1: Emergency Supply
        new Chart(emergencyCtx.getContext('2d'), {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],
                datasets: [{
                    data: [10, 10, 40, 35, 70, 75, 85],
                    fill: true,
                    backgroundColor: createGradient(emergencyCtx.getContext('2d')),
                    borderColor: '#31449b',
                    tension: 0.4
                }]
            },
            options: commonOptions
        });

        // Chart 2: Medical Supply
        const medicalCtx = document.getElementById('medicalChart');
        if (medicalCtx) {
            new Chart(medicalCtx.getContext('2d'), {
                type: 'line',
                data: {
                    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],
                    datasets: [{
                        data: [15, 20, 10, 50, 40, 60, 70],
                        fill: true,
                        backgroundColor: createGradient(medicalCtx.getContext('2d')),
                        borderColor: '#31449b',
                        tension: 0.4
                    }]
                },
                options: commonOptions
            });
        }

        // Chart 3: Veterinary Supply
        const veterinaryCtx = document.getElementById('veterinaryChart');
        if (veterinaryCtx) {
            new Chart(veterinaryCtx.getContext('2d'), {
                type: 'line',
                data: {
                    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],
                    datasets: [{
                        data: [40, 20, 60, 50, 40, 70, 80],
                        fill: true,
                        backgroundColor: createGradient(veterinaryCtx.getContext('2d')),
                        borderColor: '#31449b',
                        tension: 0.4
                    }]
                },
                options: commonOptions
            });
        }
    };

    // ── Initialization ─────────────────────────────
    document.addEventListener('DOMContentLoaded', () => {
        const sidebar = document.querySelector('.sidebar');
        const mainContent = document.querySelector('.main-content');
        const toggleBtn = document.getElementById('sidebarToggle');

        if (toggleBtn && sidebar && mainContent) {
            // Check if sidebar should be collapsed on mobile by default
            if (window.innerWidth < 1024) {
                sidebar.classList.add('collapsed');
                mainContent.classList.add('expanded');
            }

            toggleBtn.addEventListener('click', () => {
                sidebar.classList.toggle('collapsed');
                mainContent.classList.toggle('expanded');
                toggleBtn.classList.toggle('active');
            });
        }

        // Initialize dashboard charts if on dashboard
        if (window.initDashboardCharts) window.initDashboardCharts();

        // \u2500\u2500 Pending-approval badge (admin only) \u2500\u2500\u2500\u2500\u2500
        const pendingBadge = document.getElementById('sidebarPendingBadge');
        if (pendingBadge) {
            async function refreshPendingCount() {
                try {
                    const res  = await fetch('/api/requests/count');
                    if (!res.ok) return;
                    const data = await res.json();
                    const n = data.count || 0;
                    if (n > 0) {
                        pendingBadge.textContent = n;
                        pendingBadge.style.display = 'inline-flex';
                    } else {
                        pendingBadge.style.display = 'none';
                    }
                } catch (_) { /* ignore network errors */ }
            }
            refreshPendingCount();
            setInterval(refreshPendingCount, 60000);
        }

        const notificationToggle = document.getElementById('notificationToggle');
        const notificationDropdown = document.getElementById('notificationDropdown');
        const notificationList = document.getElementById('notificationList');
        const notificationDot = document.getElementById('notificationDot');

        async function loadNotifications() {
            if (!notificationDropdown || !notificationList || !notificationToggle) return;
            try {
                const res = await fetch('/api/notifications');
                if (!res.ok) throw new Error('Request failed');

                const data = await res.json();
                const notifications = data.notifications || [];
                const count = data.count || 0;

                notificationList.innerHTML = '';

                if (notifications.length === 0) {
                    notificationList.innerHTML = '<div class="notification-empty">You have no new notifications.</div>';
                    notificationDot.classList.add('hidden');
                } else {
                    notifications.forEach(item => {
                        const row = document.createElement('div');
                        row.className = 'notification-item';
                        row.innerHTML = `
                            <div class="notification-item-title">${item.title}</div>
                            <div class="notification-item-message">${item.message}</div>
                            <div class="notification-item-time">${item.timestamp || ''}</div>
                        `;
                        notificationList.appendChild(row);
                    });
                    notificationDot.classList.remove('hidden');
                    notificationDot.setAttribute('aria-hidden', 'false');
                    notificationToggle.setAttribute('aria-label', `View ${count} notifications`);
                }
            } catch (error) {
                notificationList.innerHTML = '<div class="notification-empty">Unable to load notifications.</div>';
            }
        }

        if (notificationToggle) {
            notificationToggle.addEventListener('click', (event) => {
                event.stopPropagation();
                if (!notificationDropdown) return;
                notificationDropdown.classList.toggle('show');
                notificationDropdown.setAttribute('aria-hidden', notificationDropdown.classList.contains('show') ? 'false' : 'true');
                if (notificationDropdown.classList.contains('show')) {
                    loadNotifications();
                }
            });

            document.addEventListener('click', (event) => {
                if (!notificationDropdown || !notificationToggle) return;
                if (!notificationDropdown.contains(event.target) && !notificationToggle.contains(event.target)) {
                    notificationDropdown.classList.remove('show');
                    notificationDropdown.setAttribute('aria-hidden', 'true');
                }
            });
        }
    });

})();