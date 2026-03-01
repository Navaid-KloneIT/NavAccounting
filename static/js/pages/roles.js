/**
 * NavAccounting - Roles Page
 *
 * Client-side search and filter functionality for the roles table.
 * Uses data-* attributes on table rows for matching.
 */
(function () {
    'use strict';

    var searchInput = document.getElementById('rolesSearchInput');
    var typeFilter  = document.getElementById('rolesTypeFilter');
    var table       = document.getElementById('rolesTable');
    var noResults   = document.getElementById('rolesNoResults');
    var countEl     = document.getElementById('rolesVisibleCount');

    if (!searchInput || !table) return;

    var rows = table.querySelectorAll('tbody tr[data-role-name]');

    function applyFilters() {
        var searchTerm = searchInput.value.toLowerCase().trim();
        var typeValue  = typeFilter.value;
        var visibleCount = 0;

        rows.forEach(function (row) {
            var name = row.getAttribute('data-role-name') || '';
            var desc = row.getAttribute('data-role-desc') || '';
            var type = row.getAttribute('data-role-type') || '';

            var matchesSearch = !searchTerm ||
                name.indexOf(searchTerm) !== -1 ||
                desc.indexOf(searchTerm) !== -1;

            var matchesType = !typeValue || type === typeValue;

            if (matchesSearch && matchesType) {
                row.classList.remove('filter-hidden');
                visibleCount++;
            } else {
                row.classList.add('filter-hidden');
            }
        });

        // Toggle "no results" message
        if (noResults) {
            if (visibleCount === 0 && rows.length > 0) {
                noResults.classList.add('show');
            } else {
                noResults.classList.remove('show');
            }
        }

        // Update count
        if (countEl) {
            countEl.textContent = visibleCount;
        }
    }

    // Bind events with debounce on search
    var debouncedFilter = NavApp.Utils.debounce(applyFilters, 250);
    searchInput.addEventListener('input', debouncedFilter);
    typeFilter.addEventListener('change', applyFilters);

})();
