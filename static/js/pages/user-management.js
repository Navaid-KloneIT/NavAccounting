/**
 * NavAccounting - User Management Page
 *
 * Client-side search and filter functionality for the team members table.
 * Supports: search by name/email, filter by role, filter by status.
 */
(function () {
    'use strict';

    var searchInput  = document.getElementById('usersSearchInput');
    var roleFilter   = document.getElementById('usersRoleFilter');
    var statusFilter = document.getElementById('usersStatusFilter');
    var table        = document.getElementById('usersTable');
    var noResults    = document.getElementById('usersNoResults');
    var countEl      = document.getElementById('usersVisibleCount');

    if (!searchInput || !table) return;

    var rows = table.querySelectorAll('tbody tr[data-user-name]');

    function applyFilters() {
        var searchTerm  = searchInput.value.toLowerCase().trim();
        var roleValue   = roleFilter.value;
        var statusValue = statusFilter.value;
        var visibleCount = 0;

        rows.forEach(function (row) {
            var name   = row.getAttribute('data-user-name') || '';
            var email  = row.getAttribute('data-user-email') || '';
            var roles  = row.getAttribute('data-user-role') || '';
            var status = row.getAttribute('data-user-status') || '';

            var matchesSearch = !searchTerm ||
                name.indexOf(searchTerm) !== -1 ||
                email.indexOf(searchTerm) !== -1;

            var matchesRole = !roleValue ||
                roles.split(',').indexOf(roleValue) !== -1;

            var matchesStatus = !statusValue || status === statusValue;

            if (matchesSearch && matchesRole && matchesStatus) {
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
    roleFilter.addEventListener('change', applyFilters);
    statusFilter.addEventListener('change', applyFilters);

})();
