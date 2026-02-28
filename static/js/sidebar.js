/**
 * NavAccounting - Sidebar Interactions
 *
 * Handles sidebar expand / collapse, size variants (default,
 * compact, small-icon, hover-icon), mobile hamburger toggle,
 * sub-menu accordion behaviour, active-link highlighting,
 * and responsive resize adjustments.
 */
(function () {
    'use strict';

    /* ------------------------------------------------------------------
     * Constants & selectors
     * ----------------------------------------------------------------*/
    var SIDEBAR_SELECTOR        = '.app-sidebar';
    var SIDEBAR_MENU_SELECTOR   = '.sidebar-menu';
    var MENU_ITEM_SELECTOR      = '.menu-item';
    var MENU_LINK_SELECTOR      = '.menu-link';
    var SUBMENU_SELECTOR        = '.submenu';
    var HAMBURGER_SELECTOR      = '[data-toggle="sidebar"]';
    var OVERLAY_CLASS           = 'sidebar-overlay-active';
    var COLLAPSED_CLASS         = 'sidebar-collapsed';
    var EXPANDED_HOVER_CLASS    = 'sidebar-hover-expanded';
    var MOBILE_OPEN_CLASS       = 'sidebar-mobile-open';
    var ACTIVE_CLASS            = 'active';
    var OPEN_CLASS              = 'open';
    var SUBMENU_ANIMATION_MS    = 250;
    var MOBILE_BREAKPOINT       = 992;  // Bootstrap lg

    /* ------------------------------------------------------------------
     * State
     * ----------------------------------------------------------------*/
    var overlay = null;

    /* ------------------------------------------------------------------
     * Helpers
     * ----------------------------------------------------------------*/

    /**
     * Get the current sidebar size from the <html> data attribute.
     * @returns {string}
     */
    function getSidebarSize() {
        return document.documentElement.getAttribute('data-sidebar-size') || 'default';
    }

    /**
     * Check if viewport is below the mobile breakpoint.
     * @returns {boolean}
     */
    function isMobile() {
        return window.innerWidth < MOBILE_BREAKPOINT;
    }

    /**
     * Get or create the sidebar backdrop overlay for mobile.
     * @returns {HTMLElement}
     */
    function getOverlay() {
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.className = 'sidebar-overlay';
            overlay.addEventListener('click', closeMobileSidebar);
            document.body.appendChild(overlay);
        }
        return overlay;
    }

    /**
     * Animate an element's height from 0 to scrollHeight (slide down).
     * @param {HTMLElement} el
     * @param {Function}    [callback]
     */
    function slideDown(el, callback) {
        el.style.display = 'block';
        el.style.overflow = 'hidden';
        el.style.height = '0px';
        el.style.transition = 'height ' + SUBMENU_ANIMATION_MS + 'ms ease';

        // Force reflow
        void el.offsetHeight;

        el.style.height = el.scrollHeight + 'px';

        setTimeout(function () {
            el.style.height = '';
            el.style.overflow = '';
            el.style.transition = '';
            if (typeof callback === 'function') callback();
        }, SUBMENU_ANIMATION_MS);
    }

    /**
     * Animate an element's height from current to 0 (slide up).
     * @param {HTMLElement} el
     * @param {Function}    [callback]
     */
    function slideUp(el, callback) {
        el.style.overflow = 'hidden';
        el.style.height = el.scrollHeight + 'px';
        el.style.transition = 'height ' + SUBMENU_ANIMATION_MS + 'ms ease';

        // Force reflow
        void el.offsetHeight;

        el.style.height = '0px';

        setTimeout(function () {
            el.style.display = 'none';
            el.style.height = '';
            el.style.overflow = '';
            el.style.transition = '';
            if (typeof callback === 'function') callback();
        }, SUBMENU_ANIMATION_MS);
    }

    /* ------------------------------------------------------------------
     * Sidebar toggle (desktop)
     * ----------------------------------------------------------------*/

    /**
     * Toggle the sidebar between its expanded and collapsed state
     * on desktop viewports. The collapsed style depends on the
     * configured sidebar size.
     */
    function toggleSidebar() {
        if (isMobile()) {
            toggleMobileSidebar();
            return;
        }

        var body = document.body;
        var isCollapsed = body.classList.contains(COLLAPSED_CLASS);

        if (isCollapsed) {
            body.classList.remove(COLLAPSED_CLASS);
            document.documentElement.setAttribute('data-sidebar-size', 'default');
        } else {
            body.classList.add(COLLAPSED_CLASS);
            document.documentElement.setAttribute('data-sidebar-size', 'small-icon');
        }

        // Notify layout module
        document.dispatchEvent(new CustomEvent('sidebar:toggled', {
            detail: { collapsed: !isCollapsed }
        }));
    }

    /* ------------------------------------------------------------------
     * Sidebar hover behaviour (icon-hover mode)
     * ----------------------------------------------------------------*/

    function bindHoverBehaviour() {
        var sidebar = document.querySelector(SIDEBAR_SELECTOR);
        if (!sidebar) return;

        sidebar.addEventListener('mouseenter', function () {
            if (getSidebarSize() === 'hover-icon' || document.body.classList.contains(COLLAPSED_CLASS)) {
                document.body.classList.add(EXPANDED_HOVER_CLASS);
            }
        });

        sidebar.addEventListener('mouseleave', function () {
            document.body.classList.remove(EXPANDED_HOVER_CLASS);
        });
    }

    /* ------------------------------------------------------------------
     * Mobile sidebar
     * ----------------------------------------------------------------*/

    function toggleMobileSidebar() {
        var body = document.body;
        if (body.classList.contains(MOBILE_OPEN_CLASS)) {
            closeMobileSidebar();
        } else {
            openMobileSidebar();
        }
    }

    function openMobileSidebar() {
        document.body.classList.add(MOBILE_OPEN_CLASS);
        getOverlay().classList.add(OVERLAY_CLASS);
    }

    function closeMobileSidebar() {
        document.body.classList.remove(MOBILE_OPEN_CLASS);
        if (overlay) {
            overlay.classList.remove(OVERLAY_CLASS);
        }
    }

    /* ------------------------------------------------------------------
     * Active menu item highlighting
     * ----------------------------------------------------------------*/

    /**
     * Walk the sidebar links and mark the one whose href matches the
     * current page path as active. Also expand its parent sub-menus.
     */
    function highlightActiveLink() {
        var currentPath = window.location.pathname;
        var links = document.querySelectorAll(SIDEBAR_SELECTOR + ' ' + MENU_LINK_SELECTOR);

        links.forEach(function (link) {
            var href = link.getAttribute('href');
            if (!href || href === '#') return;

            // Exact or prefix match
            var isActive = currentPath === href || (href !== '/' && currentPath.indexOf(href) === 0);

            var menuItem = link.closest(MENU_ITEM_SELECTOR);
            if (!menuItem) return;

            if (isActive) {
                link.classList.add(ACTIVE_CLASS);
                menuItem.classList.add(ACTIVE_CLASS);

                // Open all parent sub-menus
                var parent = menuItem.parentElement;
                while (parent) {
                    if (parent.classList && parent.classList.contains('submenu')) {
                        parent.classList.add(OPEN_CLASS);
                        parent.style.display = 'block';
                        var parentItem = parent.closest(MENU_ITEM_SELECTOR);
                        if (parentItem) {
                            parentItem.classList.add(OPEN_CLASS);
                        }
                    }
                    parent = parent.parentElement;
                }
            } else {
                link.classList.remove(ACTIVE_CLASS);
                menuItem.classList.remove(ACTIVE_CLASS);
            }
        });
    }

    /* ------------------------------------------------------------------
     * Sub-menu expand / collapse
     * ----------------------------------------------------------------*/

    /**
     * Toggle a sub-menu open/closed with animation. Implements
     * accordion behaviour: opening one sub-menu closes its siblings.
     * @param {HTMLElement} menuItem  The .menu-item that was clicked
     */
    function toggleSubmenu(menuItem) {
        var submenu = menuItem.querySelector(':scope > ' + SUBMENU_SELECTOR);
        if (!submenu) return;

        var isOpen = menuItem.classList.contains(OPEN_CLASS);

        // Accordion: close sibling sub-menus at the same level
        var siblingItems = menuItem.parentElement.querySelectorAll(':scope > ' + MENU_ITEM_SELECTOR + '.' + OPEN_CLASS);
        siblingItems.forEach(function (sibling) {
            if (sibling !== menuItem) {
                var sibSub = sibling.querySelector(':scope > ' + SUBMENU_SELECTOR);
                if (sibSub) {
                    slideUp(sibSub);
                }
                sibling.classList.remove(OPEN_CLASS);
            }
        });

        // Toggle this sub-menu
        if (isOpen) {
            slideUp(submenu);
            menuItem.classList.remove(OPEN_CLASS);
        } else {
            slideDown(submenu);
            menuItem.classList.add(OPEN_CLASS);
        }
    }

    /**
     * Bind click handlers on menu links that have sub-menus.
     */
    function bindSubmenuEvents() {
        var sidebar = document.querySelector(SIDEBAR_SELECTOR);
        if (!sidebar) return;

        sidebar.addEventListener('click', function (e) {
            var link = e.target.closest(MENU_LINK_SELECTOR);
            if (!link) return;

            var menuItem = link.closest(MENU_ITEM_SELECTOR);
            if (!menuItem) return;

            // Only intercept if this item has a submenu
            var submenu = menuItem.querySelector(':scope > ' + SUBMENU_SELECTOR);
            if (submenu) {
                e.preventDefault();
                toggleSubmenu(menuItem);
            }
        });
    }

    /* ------------------------------------------------------------------
     * Window resize handler
     * ----------------------------------------------------------------*/

    var resizeTimer = null;

    function handleResize() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function () {
            if (!isMobile()) {
                // Close mobile sidebar if screen grows past breakpoint
                closeMobileSidebar();
            }
        }, 150);
    }

    /* ------------------------------------------------------------------
     * Initialisation
     * ----------------------------------------------------------------*/

    function init() {
        // Hamburger / toggle buttons
        var hamburgers = document.querySelectorAll(HAMBURGER_SELECTOR);
        hamburgers.forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                toggleSidebar();
            });
        });

        // Hover expand for collapsed / hover-icon mode
        bindHoverBehaviour();

        // Sub-menu accordion
        bindSubmenuEvents();

        // Highlight current page link
        highlightActiveLink();

        // Resize listener
        window.addEventListener('resize', handleResize);
    }

    /* ------------------------------------------------------------------
     * Expose public API
     * ----------------------------------------------------------------*/
    window.NavSidebar = {
        init:                init,
        toggle:              toggleSidebar,
        openMobile:          openMobileSidebar,
        closeMobile:         closeMobileSidebar,
        highlightActiveLink: highlightActiveLink
    };

    // Auto-init
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
