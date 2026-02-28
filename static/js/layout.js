/**
 * NavAccounting - Layout Switching Logic
 *
 * Manages layout modes (vertical, horizontal, detached),
 * container width (fluid, boxed), and element positioning
 * (fixed, scrollable). Reads data-* attributes from <html>,
 * persists user preferences in localStorage, and wires up
 * the settings-panel radio buttons.
 */
(function () {
    'use strict';

    /* ------------------------------------------------------------------
     * Constants
     * ----------------------------------------------------------------*/
    var STORAGE_KEY = 'nav_layout_prefs';

    var DEFAULTS = {
        layout:      'vertical',   // vertical | horizontal | detached
        width:       'fluid',      // fluid | boxed
        position:    'fixed',      // fixed | scrollable
        sidebarSize: 'default',    // default | compact | small-icon | hover-icon
        sidebarColor:'dark',       // dark | light | gradient
        topbarColor: 'light'       // dark | light
    };

    /* CSS class maps applied to <body> or specific wrappers */
    var LAYOUT_CLASSES = {
        vertical:   'layout-vertical',
        horizontal: 'layout-horizontal',
        detached:   'layout-detached'
    };

    var WIDTH_CLASSES = {
        fluid: 'container-fluid',
        boxed: 'container-boxed'
    };

    var POSITION_CLASSES = {
        fixed:      'layout-position-fixed',
        scrollable: 'layout-position-scrollable'
    };

    var SIDEBAR_SIZE_CLASSES = {
        'default':    'sidebar-default',
        'compact':    'sidebar-compact',
        'small-icon': 'sidebar-small-icon',
        'hover-icon': 'sidebar-hover-icon'
    };

    /* ------------------------------------------------------------------
     * Helpers
     * ----------------------------------------------------------------*/

    /**
     * Read stored preferences from localStorage, merged with defaults.
     * @returns {Object}
     */
    function loadPreferences() {
        var stored = {};
        try {
            var raw = localStorage.getItem(STORAGE_KEY);
            if (raw) {
                stored = JSON.parse(raw);
            }
        } catch (e) {
            // localStorage unavailable or corrupt - fall back to defaults
        }

        var prefs = {};
        var keys = Object.keys(DEFAULTS);
        for (var i = 0; i < keys.length; i++) {
            var k = keys[i];
            prefs[k] = stored[k] || DEFAULTS[k];
        }
        return prefs;
    }

    /**
     * Save current preferences object to localStorage.
     * @param {Object} prefs
     */
    function savePreferences(prefs) {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
        } catch (e) {
            // Silently ignore storage errors
        }
    }

    /**
     * Read initial data-* attributes from the <html> element.
     * These act as server-side defaults and can be overridden by localStorage.
     * @returns {Object}
     */
    function readHtmlAttributes() {
        var html = document.documentElement;
        return {
            layout:      html.getAttribute('data-layout')        || undefined,
            width:       html.getAttribute('data-layout-width')  || undefined,
            position:    html.getAttribute('data-layout-position')|| undefined,
            sidebarSize: html.getAttribute('data-sidebar-size')  || undefined,
            sidebarColor:html.getAttribute('data-sidebar-color') || undefined,
            topbarColor: html.getAttribute('data-topbar-color')  || undefined
        };
    }

    /**
     * Remove every class in a class-map from the target element.
     * @param {HTMLElement} el
     * @param {Object}     classMap  e.g. { vertical: 'layout-vertical', ... }
     */
    function removeAllClasses(el, classMap) {
        var values = Object.keys(classMap).map(function (k) { return classMap[k]; });
        for (var i = 0; i < values.length; i++) {
            el.classList.remove(values[i]);
        }
    }

    /* ------------------------------------------------------------------
     * Core apply functions
     * ----------------------------------------------------------------*/

    /**
     * Apply the layout mode to <body>.
     * @param {string} mode  'vertical' | 'horizontal' | 'detached'
     */
    function applyLayout(mode) {
        var body = document.body;
        removeAllClasses(body, LAYOUT_CLASSES);
        if (LAYOUT_CLASSES[mode]) {
            body.classList.add(LAYOUT_CLASSES[mode]);
        }
        document.documentElement.setAttribute('data-layout', mode);
    }

    /**
     * Apply container width setting.
     * @param {string} mode  'fluid' | 'boxed'
     */
    function applyWidth(mode) {
        var body = document.body;
        removeAllClasses(body, WIDTH_CLASSES);
        if (WIDTH_CLASSES[mode]) {
            body.classList.add(WIDTH_CLASSES[mode]);
        }
        document.documentElement.setAttribute('data-layout-width', mode);
    }

    /**
     * Apply position setting (navbar / sidebar fixed or scrollable).
     * @param {string} mode  'fixed' | 'scrollable'
     */
    function applyPosition(mode) {
        var body = document.body;
        removeAllClasses(body, POSITION_CLASSES);
        if (POSITION_CLASSES[mode]) {
            body.classList.add(POSITION_CLASSES[mode]);
        }
        document.documentElement.setAttribute('data-layout-position', mode);
    }

    /**
     * Apply sidebar size variant.
     * @param {string} size  'default' | 'compact' | 'small-icon' | 'hover-icon'
     */
    function applySidebarSize(size) {
        var body = document.body;
        removeAllClasses(body, SIDEBAR_SIZE_CLASSES);
        if (SIDEBAR_SIZE_CLASSES[size]) {
            body.classList.add(SIDEBAR_SIZE_CLASSES[size]);
        }
        document.documentElement.setAttribute('data-sidebar-size', size);
    }

    /**
     * Apply sidebar colour scheme.
     * @param {string} color  'dark' | 'light' | 'gradient'
     */
    function applySidebarColor(color) {
        document.documentElement.setAttribute('data-sidebar-color', color);
    }

    /**
     * Apply topbar colour scheme.
     * @param {string} color  'dark' | 'light'
     */
    function applyTopbarColor(color) {
        document.documentElement.setAttribute('data-topbar-color', color);
    }

    /* ------------------------------------------------------------------
     * Public API
     * ----------------------------------------------------------------*/

    /**
     * Apply all preferences at once.
     * @param {Object} prefs
     */
    function applyAll(prefs) {
        applyLayout(prefs.layout);
        applyWidth(prefs.width);
        applyPosition(prefs.position);
        applySidebarSize(prefs.sidebarSize);
        applySidebarColor(prefs.sidebarColor);
        applyTopbarColor(prefs.topbarColor);
    }

    /**
     * Update one or more settings, apply them, and persist.
     * @param {Object} changes  Partial prefs, e.g. { layout: 'horizontal' }
     */
    function updateSettings(changes) {
        var prefs = loadPreferences();
        var keys = Object.keys(changes);
        for (var i = 0; i < keys.length; i++) {
            prefs[keys[i]] = changes[keys[i]];
        }
        applyAll(prefs);
        savePreferences(prefs);

        // Dispatch a custom event so other modules can react
        document.dispatchEvent(new CustomEvent('layout:changed', { detail: prefs }));
    }

    /**
     * Reset all preferences to defaults, apply, and clear storage.
     */
    function resetSettings() {
        var prefs = Object.assign({}, DEFAULTS);
        applyAll(prefs);
        savePreferences(prefs);
        syncRadioButtons(prefs);
        document.dispatchEvent(new CustomEvent('layout:changed', { detail: prefs }));
    }

    /* ------------------------------------------------------------------
     * Settings panel wiring
     * ----------------------------------------------------------------*/

    /**
     * Set checked state for radio buttons in the settings panel that
     * match the current preferences.
     * @param {Object} prefs
     */
    function syncRadioButtons(prefs) {
        var mappings = [
            { name: 'data-layout',          value: prefs.layout },
            { name: 'data-layout-width',    value: prefs.width },
            { name: 'data-layout-position', value: prefs.position },
            { name: 'data-sidebar-size',    value: prefs.sidebarSize },
            { name: 'data-sidebar-color',   value: prefs.sidebarColor },
            { name: 'data-topbar-color',    value: prefs.topbarColor }
        ];

        mappings.forEach(function (m) {
            var radios = document.querySelectorAll('input[name="' + m.name + '"]');
            radios.forEach(function (radio) {
                radio.checked = radio.value === m.value;
            });
        });
    }

    /**
     * Bind change listeners on every settings-panel radio / input group.
     */
    function bindSettingsPanelEvents() {
        var settingNames = {
            'data-layout':          'layout',
            'data-layout-width':    'width',
            'data-layout-position': 'position',
            'data-sidebar-size':    'sidebarSize',
            'data-sidebar-color':   'sidebarColor',
            'data-topbar-color':    'topbarColor'
        };

        Object.keys(settingNames).forEach(function (attrName) {
            var prefKey = settingNames[attrName];
            var radios = document.querySelectorAll('input[name="' + attrName + '"]');
            radios.forEach(function (radio) {
                radio.addEventListener('change', function () {
                    if (this.checked) {
                        var change = {};
                        change[prefKey] = this.value;
                        updateSettings(change);
                    }
                });
            });
        });

        // Reset button
        var resetBtn = document.getElementById('reset-layout');
        if (resetBtn) {
            resetBtn.addEventListener('click', function (e) {
                e.preventDefault();
                resetSettings();
            });
        }
    }

    /* ------------------------------------------------------------------
     * Initialisation
     * ----------------------------------------------------------------*/

    function init() {
        // 1. Read server-side defaults from <html> data-* attributes
        var htmlAttrs = readHtmlAttributes();

        // 2. Load persisted preferences (localStorage wins over HTML attrs)
        var stored = loadPreferences();

        // 3. Merge: localStorage > html attributes > defaults
        var prefs = {};
        var keys = Object.keys(DEFAULTS);
        for (var i = 0; i < keys.length; i++) {
            var k = keys[i];
            prefs[k] = stored[k] || htmlAttrs[k] || DEFAULTS[k];
        }

        // 4. Apply to DOM
        applyAll(prefs);

        // 5. Save merged result
        savePreferences(prefs);

        // 6. Sync settings panel radio buttons
        syncRadioButtons(prefs);

        // 7. Wire up event listeners
        bindSettingsPanelEvents();
    }

    /* ------------------------------------------------------------------
     * Expose minimal public API on window.NavLayout
     * ----------------------------------------------------------------*/
    window.NavLayout = {
        init:            init,
        updateSettings:  updateSettings,
        resetSettings:   resetSettings,
        loadPreferences: loadPreferences
    };

    // Auto-init when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
