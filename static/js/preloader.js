/**
 * NavAccounting - Preloader Logic
 *
 * Shows a loading indicator while the page is rendering and
 * fades it out once the content is ready. Controlled by the
 * data-preloader attribute on <html>:
 *
 *   <html data-preloader="enable">   -> preloader active
 *   <html data-preloader="disable">  -> preloader skipped
 *
 * If the attribute is absent the preloader defaults to enabled.
 */
(function () {
    'use strict';

    /* ------------------------------------------------------------------
     * Constants
     * ----------------------------------------------------------------*/
    var PRELOADER_SELECTOR = '#preloader';
    var ATTR_NAME          = 'data-preloader';
    var FADE_DURATION_MS   = 350;

    /* ------------------------------------------------------------------
     * Helpers
     * ----------------------------------------------------------------*/

    /**
     * Check whether the preloader is enabled via the <html> attribute.
     * @returns {boolean}
     */
    function isEnabled() {
        var value = document.documentElement.getAttribute(ATTR_NAME);
        // Treat missing attribute as enabled; only "disable" turns it off
        return value !== 'disable';
    }

    /**
     * Get the preloader element if it exists.
     * @returns {HTMLElement|null}
     */
    function getPreloader() {
        return document.querySelector(PRELOADER_SELECTOR);
    }

    /* ------------------------------------------------------------------
     * Core
     * ----------------------------------------------------------------*/

    /**
     * Immediately show the preloader (no animation).
     */
    function show() {
        var el = getPreloader();
        if (!el) return;

        el.style.opacity = '1';
        el.style.visibility = 'visible';
        el.style.display = '';
    }

    /**
     * Fade out and then hide the preloader.
     */
    function hide() {
        var el = getPreloader();
        if (!el) return;

        // Apply CSS transition for a smooth fade-out
        el.style.transition = 'opacity ' + FADE_DURATION_MS + 'ms ease';
        el.style.opacity = '0';

        setTimeout(function () {
            el.style.visibility = 'hidden';
            el.style.display = 'none';
            el.style.transition = '';
        }, FADE_DURATION_MS);
    }

    /* ------------------------------------------------------------------
     * Initialisation
     * ----------------------------------------------------------------*/

    function init() {
        if (!isEnabled()) {
            // Preloader disabled - make sure it's hidden immediately
            var el = getPreloader();
            if (el) {
                el.style.display = 'none';
                el.style.visibility = 'hidden';
            }
            return;
        }

        // Ensure preloader is visible at start
        show();

        // Hide once the page has fully loaded (images, fonts, etc.)
        if (document.readyState === 'complete') {
            // Already loaded (unlikely but possible if script is deferred)
            hide();
        } else {
            window.addEventListener('load', function () {
                hide();
            });
        }
    }

    /* ------------------------------------------------------------------
     * Expose public API
     * ----------------------------------------------------------------*/
    window.NavPreloader = {
        init: init,
        show: show,
        hide: hide
    };

    // Run immediately (not waiting for DOMContentLoaded) so the preloader
    // is visible from the earliest possible moment.
    init();
})();
