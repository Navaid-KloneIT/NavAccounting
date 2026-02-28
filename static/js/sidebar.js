/**
 * NavAccounting - Sidebar Interactions
 */
(function () {
    'use strict';

    var MOBILE_BREAKPOINT = 992;

    function isMobile() {
        return window.innerWidth < MOBILE_BREAKPOINT;
    }

    function init() {
        var sidebar = document.getElementById('sidebar');
        var toggleBtn = document.getElementById('sidebar-toggle');
        var overlay = document.getElementById('sidebar-overlay');

        if (!sidebar) return;

        // Toggle button
        if (toggleBtn) {
            toggleBtn.addEventListener('click', function (e) {
                e.preventDefault();
                if (isMobile()) {
                    document.body.classList.toggle('sidebar-open');
                } else {
                    document.body.classList.toggle('sidebar-collapsed');
                }
            });
        }

        // Overlay click closes sidebar on mobile
        if (overlay) {
            overlay.addEventListener('click', function () {
                document.body.classList.remove('sidebar-open');
            });
        }

        // Highlight active link based on current path
        var currentPath = window.location.pathname;
        var links = sidebar.querySelectorAll('.sidebar-link');
        links.forEach(function (link) {
            var href = link.getAttribute('href');
            if (!href || href === '#') return;
            if (currentPath === href || (href !== '/' && currentPath.indexOf(href) === 0)) {
                var item = link.closest('.sidebar-item');
                if (item) item.classList.add('active');
            }
        });

        // Close mobile sidebar on resize past breakpoint
        window.addEventListener('resize', function () {
            if (!isMobile()) {
                document.body.classList.remove('sidebar-open');
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
