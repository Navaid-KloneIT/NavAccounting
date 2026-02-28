/**
 * NavAccounting - Main Application Initialisation
 *
 * Central entry point that bootstraps all UI modules, initialises
 * third-party libraries, and provides common utility functions
 * used throughout the application.
 *
 * Expected script load order (all deferred):
 *   1. vendor libs (Bootstrap, Feather Icons, ApexCharts, etc.)
 *   2. preloader.js   (runs immediately, not deferred)
 *   3. theme.js
 *   4. layout.js
 *   5. sidebar.js
 *   6. topbar.js
 *   7. app.js          <-- this file
 *   8. page-specific scripts (dashboard-charts.js, etc.)
 */
(function () {
    'use strict';

    /* ==================================================================
     * 1.  Third-party library initialisation
     * ================================================================*/

    /**
     * Activate all Bootstrap tooltips on the page.
     */
    function initTooltips() {
        if (typeof bootstrap === 'undefined') return;

        var tooltipEls = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltipEls.forEach(function (el) {
            new bootstrap.Tooltip(el);
        });
    }

    /**
     * Activate all Bootstrap popovers on the page.
     */
    function initPopovers() {
        if (typeof bootstrap === 'undefined') return;

        var popoverEls = document.querySelectorAll('[data-bs-toggle="popover"]');
        popoverEls.forEach(function (el) {
            new bootstrap.Popover(el);
        });
    }

    /**
     * Replace <i data-feather="..."> elements with inline SVG icons.
     */
    function initFeatherIcons() {
        if (typeof feather !== 'undefined' && feather.replace) {
            feather.replace();
        }
    }

    /* ==================================================================
     * 2.  CSRF token for AJAX requests
     * ================================================================*/

    /**
     * Read the Django CSRF token from the cookie.
     * @returns {string|null}
     */
    function getCsrfToken() {
        var name = 'csrftoken';
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.indexOf(name + '=') === 0) {
                return decodeURIComponent(cookie.substring(name.length + 1));
            }
        }
        // Fallback: read from hidden input
        var input = document.querySelector('[name=csrfmiddlewaretoken]');
        return input ? input.value : null;
    }

    /**
     * Patch the global fetch so every same-origin request automatically
     * includes the X-CSRFToken header. Also sets up XMLHttpRequest
     * defaults for legacy code.
     */
    function setupCsrfAjax() {
        var token = getCsrfToken();
        if (!token) return;

        // ---- XMLHttpRequest ----
        var _origOpen = XMLHttpRequest.prototype.open;
        XMLHttpRequest.prototype.open = function (method, url) {
            _origOpen.apply(this, arguments);

            // Only add header for unsafe methods to same origin
            if (/^(POST|PUT|PATCH|DELETE)$/i.test(method)) {
                this.setRequestHeader('X-CSRFToken', token);
            }
        };

        // ---- Fetch API wrapper ----
        var _origFetch = window.fetch;
        window.fetch = function (input, init) {
            init = init || {};
            var method = (init.method || 'GET').toUpperCase();

            if (/^(POST|PUT|PATCH|DELETE)$/.test(method)) {
                init.headers = init.headers || {};

                // Support both Headers object and plain object
                if (init.headers instanceof Headers) {
                    if (!init.headers.has('X-CSRFToken')) {
                        init.headers.append('X-CSRFToken', token);
                    }
                } else {
                    if (!init.headers['X-CSRFToken']) {
                        init.headers['X-CSRFToken'] = token;
                    }
                }
            }

            return _origFetch.call(window, input, init);
        };
    }

    /* ==================================================================
     * 3.  Flash / toast message auto-dismiss
     * ================================================================*/

    /**
     * Auto-dismiss Django messages (Bootstrap alerts) after a timeout.
     * @param {number} [delay=5000]  Milliseconds before dismissal
     */
    function initFlashMessages(delay) {
        delay = delay || 5000;

        var alerts = document.querySelectorAll('.alert-dismissible.auto-dismiss');
        alerts.forEach(function (alert) {
            setTimeout(function () {
                // Use Bootstrap's Alert dismiss if available
                if (typeof bootstrap !== 'undefined' && bootstrap.Alert) {
                    var bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                    if (bsAlert) {
                        bsAlert.close();
                        return;
                    }
                }
                // Fallback: manual fade + remove
                alert.style.transition = 'opacity 0.3s ease';
                alert.style.opacity = '0';
                setTimeout(function () {
                    alert.remove();
                }, 300);
            }, delay);
        });
    }

    /* ==================================================================
     * 4.  Smooth scroll for anchor links
     * ================================================================*/

    function initSmoothScroll() {
        document.addEventListener('click', function (e) {
            var link = e.target.closest('a[href^="#"]:not([href="#"])');
            if (!link) return;

            var targetId = link.getAttribute('href');
            var target = document.querySelector(targetId);
            if (!target) return;

            e.preventDefault();
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });

            // Update URL hash without jumping
            if (history.pushState) {
                history.pushState(null, null, targetId);
            }
        });
    }

    /* ==================================================================
     * 5.  Back-to-top button
     * ================================================================*/

    function initBackToTop() {
        var btn = document.getElementById('back-to-top');
        if (!btn) return;

        var SCROLL_THRESHOLD = 300;

        function toggleVisibility() {
            if (window.scrollY > SCROLL_THRESHOLD) {
                btn.classList.add('show');
            } else {
                btn.classList.remove('show');
            }
        }

        window.addEventListener('scroll', toggleVisibility, { passive: true });

        btn.addEventListener('click', function (e) {
            e.preventDefault();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });

        // Initial check
        toggleVisibility();
    }

    /* ==================================================================
     * 6.  Common utility functions (exposed globally)
     * ================================================================*/

    var Utils = {
        /**
         * Debounce a function call.
         * @param {Function} fn
         * @param {number}   wait  Milliseconds
         * @returns {Function}
         */
        debounce: function (fn, wait) {
            var timer;
            return function () {
                var context = this;
                var args = arguments;
                clearTimeout(timer);
                timer = setTimeout(function () {
                    fn.apply(context, args);
                }, wait);
            };
        },

        /**
         * Throttle a function so it fires at most once per interval.
         * @param {Function} fn
         * @param {number}   limit  Milliseconds
         * @returns {Function}
         */
        throttle: function (fn, limit) {
            var waiting = false;
            return function () {
                if (!waiting) {
                    fn.apply(this, arguments);
                    waiting = true;
                    setTimeout(function () { waiting = false; }, limit);
                }
            };
        },

        /**
         * Format a number as currency.
         * @param {number} value
         * @param {string} [currency='USD']
         * @param {string} [locale='en-US']
         * @returns {string}
         */
        formatCurrency: function (value, currency, locale) {
            currency = currency || 'USD';
            locale = locale || 'en-US';
            return new Intl.NumberFormat(locale, {
                style: 'currency',
                currency: currency
            }).format(value);
        },

        /**
         * Format a number with thousand separators.
         * @param {number} value
         * @param {string} [locale='en-US']
         * @returns {string}
         */
        formatNumber: function (value, locale) {
            locale = locale || 'en-US';
            return new Intl.NumberFormat(locale).format(value);
        },

        /**
         * Retrieve the Django CSRF token.
         * @returns {string|null}
         */
        getCsrfToken: getCsrfToken,

        /**
         * Simple convenience wrapper around fetch for JSON APIs.
         * Automatically includes CSRF token and content-type header.
         *
         * @param {string} url
         * @param {Object} [options]
         * @returns {Promise<Object>}
         */
        fetchJSON: function (url, options) {
            options = options || {};
            options.headers = options.headers || {};
            options.headers['Content-Type'] = options.headers['Content-Type'] || 'application/json';
            options.headers['X-Requested-With'] = 'XMLHttpRequest';

            return fetch(url, options).then(function (response) {
                if (!response.ok) {
                    throw new Error('HTTP ' + response.status + ': ' + response.statusText);
                }
                return response.json();
            });
        }
    };

    /* ==================================================================
     * 7.  Master initialisation
     * ================================================================*/

    function init() {
        // Third-party libraries
        initTooltips();
        initPopovers();
        initFeatherIcons();

        // CSRF protection for AJAX
        setupCsrfAjax();

        // UI features
        initFlashMessages();
        initSmoothScroll();
        initBackToTop();

        // Module re-init hooks (modules self-initialise, but we
        // can re-trigger here if scripts loaded in unexpected order)
        if (window.NavTheme   && typeof window.NavTheme.init   === 'function') window.NavTheme.init();
        if (window.NavLayout  && typeof window.NavLayout.init  === 'function') window.NavLayout.init();
        if (window.NavSidebar && typeof window.NavSidebar.init === 'function') window.NavSidebar.init();
        if (window.NavTopbar  && typeof window.NavTopbar.init  === 'function') window.NavTopbar.init();
    }

    /* ==================================================================
     * Expose public API on window.NavApp
     * ================================================================*/
    window.NavApp = {
        init:  init,
        Utils: Utils
    };

    // Auto-init when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
