/**
 * NavAccounting - Topbar Interactions
 *
 * Handles the top navigation bar features: search toggle,
 * notification dropdown, user profile dropdown, fullscreen
 * toggle, and responsive behaviour for mobile viewports.
 */
(function () {
    'use strict';

    /* ------------------------------------------------------------------
     * Selectors
     * ----------------------------------------------------------------*/
    var SEARCH_TOGGLE       = '[data-toggle="search"]';
    var SEARCH_INPUT        = '.topbar-search-input';
    var SEARCH_OVERLAY      = '.search-overlay';
    var SEARCH_CONTAINER    = '.topbar-search';
    var FULLSCREEN_BTN      = '[data-toggle="fullscreen"]';
    var NOTIFICATION_DROP   = '.notification-dropdown';
    var USER_DROP           = '.user-dropdown';
    var TOPBAR_MOBILE_TOGGLE= '[data-toggle="topbar-menu"]';
    var TOPBAR_NAV          = '.topbar-nav-items';
    var ACTIVE_CLASS        = 'show';

    /* ------------------------------------------------------------------
     * Search toggle
     * ----------------------------------------------------------------*/

    function initSearch() {
        var toggleBtns = document.querySelectorAll(SEARCH_TOGGLE);
        var container  = document.querySelector(SEARCH_CONTAINER);
        var searchOverlay = document.querySelector(SEARCH_OVERLAY);
        var input      = document.querySelector(SEARCH_INPUT);

        if (!toggleBtns.length || !container) return;

        function openSearch() {
            container.classList.add(ACTIVE_CLASS);
            if (searchOverlay) searchOverlay.classList.add(ACTIVE_CLASS);
            if (input) {
                setTimeout(function () { input.focus(); }, 100);
            }
        }

        function closeSearch() {
            container.classList.remove(ACTIVE_CLASS);
            if (searchOverlay) searchOverlay.classList.remove(ACTIVE_CLASS);
            if (input) input.value = '';
        }

        toggleBtns.forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                if (container.classList.contains(ACTIVE_CLASS)) {
                    closeSearch();
                } else {
                    openSearch();
                }
            });
        });

        // Close on overlay click
        if (searchOverlay) {
            searchOverlay.addEventListener('click', closeSearch);
        }

        // Close on Escape key
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && container.classList.contains(ACTIVE_CLASS)) {
                closeSearch();
            }
        });
    }

    /* ------------------------------------------------------------------
     * Notification dropdown
     * ----------------------------------------------------------------*/

    function initNotifications() {
        var dropdown = document.querySelector(NOTIFICATION_DROP);
        if (!dropdown) return;

        // Mark all as read
        var markReadBtn = dropdown.querySelector('.mark-all-read');
        if (markReadBtn) {
            markReadBtn.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();

                var unread = dropdown.querySelectorAll('.notification-item.unread');
                unread.forEach(function (item) {
                    item.classList.remove('unread');
                });

                // Update badge count
                var badge = document.querySelector('.notification-badge');
                if (badge) {
                    badge.textContent = '0';
                    badge.style.display = 'none';
                }
            });
        }

        // Individual notification click
        var items = dropdown.querySelectorAll('.notification-item');
        items.forEach(function (item) {
            item.addEventListener('click', function () {
                this.classList.remove('unread');

                // Recount unread
                var remaining = dropdown.querySelectorAll('.notification-item.unread').length;
                var badge = document.querySelector('.notification-badge');
                if (badge) {
                    badge.textContent = remaining.toString();
                    if (remaining === 0) {
                        badge.style.display = 'none';
                    }
                }
            });
        });
    }

    /* ------------------------------------------------------------------
     * User dropdown menu
     * ----------------------------------------------------------------*/

    function initUserDropdown() {
        var dropdown = document.querySelector(USER_DROP);
        if (!dropdown) return;

        // Sign-out confirmation
        var signOutLink = dropdown.querySelector('.sign-out-link');
        if (signOutLink) {
            signOutLink.addEventListener('click', function (e) {
                // The form-based sign out (via POST) is preferred for CSRF.
                // If this is a plain link, we can optionally confirm.
                var form = document.querySelector('#sign-out-form');
                if (form) {
                    e.preventDefault();
                    form.submit();
                }
            });
        }
    }

    /* ------------------------------------------------------------------
     * Fullscreen toggle
     * ----------------------------------------------------------------*/

    function initFullscreen() {
        var btn = document.querySelector(FULLSCREEN_BTN);
        if (!btn) return;

        btn.addEventListener('click', function (e) {
            e.preventDefault();

            if (!document.fullscreenElement &&
                !document.mozFullScreenElement &&
                !document.webkitFullscreenElement &&
                !document.msFullscreenElement) {
                // Enter fullscreen
                var docEl = document.documentElement;
                if (docEl.requestFullscreen) {
                    docEl.requestFullscreen();
                } else if (docEl.mozRequestFullScreen) {
                    docEl.mozRequestFullScreen();
                } else if (docEl.webkitRequestFullscreen) {
                    docEl.webkitRequestFullscreen();
                } else if (docEl.msRequestFullscreen) {
                    docEl.msRequestFullscreen();
                }
            } else {
                // Exit fullscreen
                if (document.exitFullscreen) {
                    document.exitFullscreen();
                } else if (document.mozCancelFullScreen) {
                    document.mozCancelFullScreen();
                } else if (document.webkitExitFullscreen) {
                    document.webkitExitFullscreen();
                } else if (document.msExitFullscreen) {
                    document.msExitFullscreen();
                }
            }
        });

        // Update icon on fullscreen change
        var updateIcon = function () {
            var isFullscreen = !!(document.fullscreenElement ||
                                  document.mozFullScreenElement ||
                                  document.webkitFullscreenElement ||
                                  document.msFullscreenElement);

            var expandIcon   = btn.querySelector('.fullscreen-expand');
            var compressIcon = btn.querySelector('.fullscreen-compress');

            if (expandIcon && compressIcon) {
                if (isFullscreen) {
                    expandIcon.classList.add('d-none');
                    compressIcon.classList.remove('d-none');
                } else {
                    expandIcon.classList.remove('d-none');
                    compressIcon.classList.add('d-none');
                }
            }
        };

        document.addEventListener('fullscreenchange', updateIcon);
        document.addEventListener('mozfullscreenchange', updateIcon);
        document.addEventListener('webkitfullscreenchange', updateIcon);
        document.addEventListener('msfullscreenchange', updateIcon);
    }

    /* ------------------------------------------------------------------
     * Mobile responsive menu
     * ----------------------------------------------------------------*/

    function initMobileMenu() {
        var toggleBtn = document.querySelector(TOPBAR_MOBILE_TOGGLE);
        var navItems  = document.querySelector(TOPBAR_NAV);

        if (!toggleBtn || !navItems) return;

        toggleBtn.addEventListener('click', function (e) {
            e.preventDefault();
            navItems.classList.toggle(ACTIVE_CLASS);
            toggleBtn.classList.toggle(ACTIVE_CLASS);
        });

        // Close when clicking outside
        document.addEventListener('click', function (e) {
            if (!navItems.contains(e.target) && !toggleBtn.contains(e.target)) {
                navItems.classList.remove(ACTIVE_CLASS);
                toggleBtn.classList.remove(ACTIVE_CLASS);
            }
        });
    }

    /* ------------------------------------------------------------------
     * Initialisation
     * ----------------------------------------------------------------*/

    function init() {
        initSearch();
        initNotifications();
        initUserDropdown();
        initFullscreen();
        initMobileMenu();
    }

    /* ------------------------------------------------------------------
     * Expose public API
     * ----------------------------------------------------------------*/
    window.NavTopbar = {
        init: init
    };

    // Auto-init
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
