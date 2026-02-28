/**
 * NavAccounting - Theme Management
 *
 * Handles dark / light mode toggling via the Bootstrap 5.3
 * data-bs-theme attribute on <html>. Persists the choice in
 * localStorage and auto-detects the OS colour-scheme preference
 * on first visit.
 */
(function () {
    'use strict';

    /* ------------------------------------------------------------------
     * Constants
     * ----------------------------------------------------------------*/
    var STORAGE_KEY  = 'nav_theme';
    var ATTR_NAME    = 'data-bs-theme';
    var THEME_LIGHT  = 'light';
    var THEME_DARK   = 'dark';

    /* ------------------------------------------------------------------
     * Helpers
     * ----------------------------------------------------------------*/

    /**
     * Detect the operating-system / browser colour-scheme preference.
     * @returns {string} 'dark' or 'light'
     */
    function detectSystemPreference() {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return THEME_DARK;
        }
        return THEME_LIGHT;
    }

    /**
     * Read the stored theme from localStorage.
     * Returns null when nothing has been stored yet (first visit).
     * @returns {string|null}
     */
    function loadTheme() {
        try {
            return localStorage.getItem(STORAGE_KEY);
        } catch (e) {
            return null;
        }
    }

    /**
     * Persist the current theme string.
     * @param {string} theme
     */
    function saveTheme(theme) {
        try {
            localStorage.setItem(STORAGE_KEY, theme);
        } catch (e) {
            // Silently ignore
        }
    }

    /* ------------------------------------------------------------------
     * Core
     * ----------------------------------------------------------------*/

    /**
     * Apply a theme value to the document.
     * @param {string} theme  'light' or 'dark'
     */
    function applyTheme(theme) {
        document.documentElement.setAttribute(ATTR_NAME, theme);

        // Update any toggle buttons / icons in the DOM
        var toggleBtns = document.querySelectorAll('[data-toggle="theme"]');
        toggleBtns.forEach(function (btn) {
            var iconLight = btn.querySelector('.theme-icon-light');
            var iconDark  = btn.querySelector('.theme-icon-dark');

            if (iconLight && iconDark) {
                if (theme === THEME_DARK) {
                    iconLight.classList.add('d-none');
                    iconDark.classList.remove('d-none');
                } else {
                    iconLight.classList.remove('d-none');
                    iconDark.classList.add('d-none');
                }
            }
        });

        // Dispatch event for other modules (e.g. charts need to update colours)
        document.dispatchEvent(new CustomEvent('theme:changed', {
            detail: { theme: theme }
        }));
    }

    /**
     * Return the currently active theme.
     * @returns {string}
     */
    function getTheme() {
        return document.documentElement.getAttribute(ATTR_NAME) || THEME_LIGHT;
    }

    /**
     * Toggle between dark and light.
     */
    function toggle() {
        var next = getTheme() === THEME_DARK ? THEME_LIGHT : THEME_DARK;
        applyTheme(next);
        saveTheme(next);
    }

    /**
     * Explicitly set the theme.
     * @param {string} theme  'light' or 'dark'
     */
    function setTheme(theme) {
        if (theme !== THEME_LIGHT && theme !== THEME_DARK) {
            theme = THEME_LIGHT;
        }
        applyTheme(theme);
        saveTheme(theme);
    }

    /* ------------------------------------------------------------------
     * Event listeners
     * ----------------------------------------------------------------*/

    function bindEvents() {
        // Toggle buttons (e.g. sun/moon icon in topbar)
        var toggleBtns = document.querySelectorAll('[data-toggle="theme"]');
        toggleBtns.forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                toggle();
            });
        });

        // Settings-panel radio buttons
        var radios = document.querySelectorAll('input[name="data-bs-theme"]');
        radios.forEach(function (radio) {
            radio.addEventListener('change', function () {
                if (this.checked) {
                    setTheme(this.value);
                }
            });
        });

        // Listen for OS-level theme changes in real time
        if (window.matchMedia) {
            var mql = window.matchMedia('(prefers-color-scheme: dark)');
            var handler = function (e) {
                // Only auto-switch if user hasn't explicitly chosen
                var stored = loadTheme();
                if (!stored) {
                    applyTheme(e.matches ? THEME_DARK : THEME_LIGHT);
                }
            };

            if (mql.addEventListener) {
                mql.addEventListener('change', handler);
            } else if (mql.addListener) {
                // Fallback for older browsers
                mql.addListener(handler);
            }
        }
    }

    /* ------------------------------------------------------------------
     * Initialisation
     * ----------------------------------------------------------------*/

    function init() {
        // 1. Check localStorage
        var stored = loadTheme();

        // 2. If nothing stored, check <html> attribute set by server
        var serverTheme = document.documentElement.getAttribute(ATTR_NAME);

        // 3. Determine effective theme
        var theme;
        if (stored) {
            theme = stored;
        } else if (serverTheme) {
            theme = serverTheme;
        } else {
            // First visit: auto-detect system preference
            theme = detectSystemPreference();
        }

        // 4. Apply
        applyTheme(theme);
        saveTheme(theme);

        // 5. Sync settings-panel radios
        var radios = document.querySelectorAll('input[name="data-bs-theme"]');
        radios.forEach(function (radio) {
            radio.checked = radio.value === theme;
        });

        // 6. Bind events
        bindEvents();
    }

    /* ------------------------------------------------------------------
     * Expose public API on window.NavTheme
     * ----------------------------------------------------------------*/
    window.NavTheme = {
        init:     init,
        toggle:   toggle,
        setTheme: setTheme,
        getTheme: getTheme
    };

    // Auto-init when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
