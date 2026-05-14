(function () {
    'use strict';

    var SIDEBAR_KEY = 'alias_sidebar_open';
    var SIDEBAR_WIDTH = '280px';

    function getSidebar()   { return document.querySelector('.sidebar'); }
    function getContainer() { return document.getElementById('dashboardContainer'); }
    function getMain()      { return document.getElementById('mainContent'); }
    function getBtn()       { return document.getElementById('sidebarToggleBtn'); }
    function getOverlay()   { return document.getElementById('sidebarOverlay'); }

    function isMobile() { return window.innerWidth <= 768; }

    function openSidebar() {
        var sidebar   = getSidebar();
        var container = getContainer();
        var main      = getMain();
        var btn       = getBtn();
        var overlay   = getOverlay();

        sidebar.classList.add('sidebar--open');
        sidebar.classList.remove('sidebar--closed');
        container.classList.add('sidebar-is-open');
        container.classList.remove('sidebar-is-closed');
        btn.classList.add('btn--sidebar-open');

        if (isMobile()) {
            overlay.classList.add('overlay--visible');
        }

        try { localStorage.setItem(SIDEBAR_KEY, '1'); } catch(e) {}
    }

    function closeSidebar() {
        var sidebar   = getSidebar();
        var container = getContainer();
        var main      = getMain();
        var btn       = getBtn();
        var overlay   = getOverlay();

        sidebar.classList.remove('sidebar--open');
        sidebar.classList.add('sidebar--closed');
        container.classList.remove('sidebar-is-open');
        container.classList.add('sidebar-is-closed');
        btn.classList.remove('btn--sidebar-open');
        overlay.classList.remove('overlay--visible');

        try { localStorage.setItem(SIDEBAR_KEY, '0'); } catch(e) {}
    }

    function toggleSidebar() {
        var sidebar = getSidebar();
        if (sidebar.classList.contains('sidebar--open')) {
            closeSidebar();
        } else {
            openSidebar();
        }
    }

    function initSidebar() {
        var btn     = getBtn();
        var overlay = getOverlay();
        var sidebar = getSidebar();

        if (!btn || !sidebar) return;

        // Restore persisted state, defaulting to open on desktop
        var stored;
        try { stored = localStorage.getItem(SIDEBAR_KEY); } catch(e) {}

        if (stored === '0') {
            closeSidebar();
        } else {
            openSidebar();
        }

        btn.addEventListener('click', toggleSidebar);

        if (overlay) {
            overlay.addEventListener('click', closeSidebar);
        }
erlay.classList.remove('overlay--visible');
            }
        });
    }

    document.addEventListener('DOMContentLoaded', initSidebar);

})();
