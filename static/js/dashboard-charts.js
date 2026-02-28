/**
 * NavAccounting - Dashboard Charts (ApexCharts)
 *
 * Renders the main dashboard visualisations:
 *   - Cash Flow (area chart with income / expense / net lines)
 *   - Revenue Breakdown (donut chart)
 *   - Monthly Overview (bar chart)
 *
 * All charts are theme-aware and will re-render when the
 * dark/light mode changes. Data is injected from Django context
 * via a global `window.__dashboardData` object, or sensible
 * defaults are used when that object is absent.
 */
(function () {
    'use strict';

    /* ==================================================================
     * 1.  Colour palettes (theme-aware)
     * ================================================================*/

    /**
     * Return a colour palette object that matches the active theme.
     * @returns {Object}
     */
    function getPalette() {
        var isDark = (document.documentElement.getAttribute('data-bs-theme') === 'dark');

        return {
            primary:    '#3b7ddd',
            success:    '#28a745',
            danger:     '#dc3545',
            warning:    '#ffc107',
            info:       '#17a2b8',
            secondary:  '#6c757d',

            // Chart-specific
            income:     '#28a745',
            expense:    '#dc3545',
            net:        '#3b7ddd',

            // Donut slices
            donut: ['#3b7ddd', '#28a745', '#ffc107', '#17a2b8', '#6c757d'],

            // Text / grid
            textColor:  isDark ? '#ced4da' : '#495057',
            gridColor:  isDark ? '#2c3034' : '#e9ecef',
            background: isDark ? '#212529' : '#ffffff',
            cardBg:     isDark ? '#2b3035' : '#ffffff',
            borderColor:isDark ? '#495057' : '#dee2e6'
        };
    }

    /* ==================================================================
     * 2.  Default / fallback data
     * ================================================================*/

    var FALLBACK_DATA = {
        cashFlow: {
            categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            inflow:     [42000, 38000, 51000, 46000, 55000, 48000],
            outflow:    [31000, 29000, 37000, 34000, 41000, 36000],
            net:        [11000,  9000, 14000, 12000, 14000, 12000]
        },
        revenueBreakdown: {
            labels: ['Sales', 'Services', 'Interest', 'Other'],
            values: [45000, 32000, 5000, 3000]
        },
        monthlyOverview: {
            categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            revenue:    [52000, 47000, 61000, 55000, 68000, 59000],
            expenses:   [31000, 29000, 37000, 34000, 41000, 36000]
        }
    };

    /**
     * Merge Django-injected data with fallbacks.
     * @returns {Object}
     */
    function getData() {
        var ctx = window.__dashboardData || {};
        return {
            cashFlow:         ctx.cashFlow         || FALLBACK_DATA.cashFlow,
            revenueBreakdown: ctx.revenueBreakdown || FALLBACK_DATA.revenueBreakdown,
            monthlyOverview:  ctx.monthlyOverview  || FALLBACK_DATA.monthlyOverview
        };
    }

    /* ==================================================================
     * 3.  Common chart options
     * ================================================================*/

    /**
     * Build base ApexCharts options shared across all charts.
     * @returns {Object}
     */
    function baseOptions() {
        var p = getPalette();
        return {
            chart: {
                fontFamily: 'inherit',
                background: 'transparent',
                toolbar: { show: false }
            },
            theme: {
                mode: document.documentElement.getAttribute('data-bs-theme') === 'dark' ? 'dark' : 'light'
            },
            grid: {
                borderColor: p.gridColor,
                strokeDashArray: 3
            },
            tooltip: {
                theme: document.documentElement.getAttribute('data-bs-theme') === 'dark' ? 'dark' : 'light'
            },
            xaxis: {
                labels: { style: { colors: p.textColor } },
                axisBorder: { color: p.borderColor },
                axisTicks:  { color: p.borderColor }
            },
            yaxis: {
                labels: {
                    style: { colors: p.textColor },
                    formatter: function (val) {
                        if (val >= 1000) return '$' + (val / 1000).toFixed(0) + 'k';
                        return '$' + val;
                    }
                }
            },
            legend: {
                labels: { colors: p.textColor }
            },
            responsive: [{
                breakpoint: 576,
                options: {
                    chart: { height: 250 },
                    legend: { position: 'bottom' }
                }
            }]
        };
    }

    /* ==================================================================
     * 4.  Individual chart builders
     * ================================================================*/

    var chartInstances = {};

    /**
     * Render the Cash Flow area chart.
     * @param {string} selector  CSS selector for the chart container
     */
    function renderCashFlowChart(selector) {
        var el = document.querySelector(selector);
        if (!el) return;

        var data = getData().cashFlow;
        var p    = getPalette();

        var options = Object.assign({}, baseOptions(), {
            chart: Object.assign({}, baseOptions().chart, {
                type: 'area',
                height: 340
            }),
            series: [
                { name: 'Income',  data: data.inflow },
                { name: 'Expense', data: data.outflow },
                { name: 'Net',     data: data.net }
            ],
            colors: [p.income, p.expense, p.net],
            fill: {
                type: 'gradient',
                gradient: {
                    shadeIntensity: 1,
                    opacityFrom: 0.4,
                    opacityTo: 0.1,
                    stops: [0, 90, 100]
                }
            },
            stroke: {
                curve: 'smooth',
                width: 2
            },
            dataLabels: { enabled: false },
            xaxis: Object.assign({}, baseOptions().xaxis, {
                categories: data.categories
            }),
            tooltip: {
                theme: document.documentElement.getAttribute('data-bs-theme') === 'dark' ? 'dark' : 'light',
                y: {
                    formatter: function (val) {
                        return '$' + val.toLocaleString();
                    }
                }
            }
        });

        if (chartInstances.cashFlow) {
            chartInstances.cashFlow.destroy();
        }
        chartInstances.cashFlow = new ApexCharts(el, options);
        chartInstances.cashFlow.render();
    }

    /**
     * Render the Revenue Breakdown donut chart.
     * @param {string} selector
     */
    function renderRevenueDonut(selector) {
        var el = document.querySelector(selector);
        if (!el) return;

        var data = getData().revenueBreakdown;
        var p    = getPalette();

        var options = {
            chart: {
                type: 'donut',
                height: 320,
                fontFamily: 'inherit',
                background: 'transparent'
            },
            series: data.values,
            labels: data.labels,
            colors: p.donut,
            theme: {
                mode: document.documentElement.getAttribute('data-bs-theme') === 'dark' ? 'dark' : 'light'
            },
            plotOptions: {
                pie: {
                    donut: {
                        size: '65%',
                        labels: {
                            show: true,
                            name: {
                                show: true,
                                fontSize: '14px',
                                color: p.textColor
                            },
                            value: {
                                show: true,
                                fontSize: '20px',
                                fontWeight: 600,
                                color: p.textColor,
                                formatter: function (val) {
                                    return '$' + parseInt(val, 10).toLocaleString();
                                }
                            },
                            total: {
                                show: true,
                                label: 'Total',
                                color: p.textColor,
                                formatter: function (w) {
                                    var total = w.globals.seriesTotals.reduce(function (a, b) {
                                        return a + b;
                                    }, 0);
                                    return '$' + total.toLocaleString();
                                }
                            }
                        }
                    }
                }
            },
            dataLabels: { enabled: false },
            legend: {
                position: 'bottom',
                labels: { colors: p.textColor }
            },
            stroke: {
                width: 2,
                colors: [p.cardBg]
            },
            tooltip: {
                theme: document.documentElement.getAttribute('data-bs-theme') === 'dark' ? 'dark' : 'light',
                y: {
                    formatter: function (val) {
                        return '$' + val.toLocaleString();
                    }
                }
            },
            responsive: [{
                breakpoint: 576,
                options: {
                    chart: { height: 260 },
                    legend: { position: 'bottom' }
                }
            }]
        };

        if (chartInstances.revenueDonut) {
            chartInstances.revenueDonut.destroy();
        }
        chartInstances.revenueDonut = new ApexCharts(el, options);
        chartInstances.revenueDonut.render();
    }

    /**
     * Render the Monthly Overview bar chart.
     * @param {string} selector
     */
    function renderMonthlyOverview(selector) {
        var el = document.querySelector(selector);
        if (!el) return;

        var data = getData().monthlyOverview;
        var p    = getPalette();

        var options = Object.assign({}, baseOptions(), {
            chart: Object.assign({}, baseOptions().chart, {
                type: 'bar',
                height: 340
            }),
            series: [
                { name: 'Revenue',  data: data.revenue },
                { name: 'Expenses', data: data.expenses }
            ],
            colors: [p.primary, p.danger],
            plotOptions: {
                bar: {
                    horizontal: false,
                    columnWidth: '55%',
                    borderRadius: 4,
                    borderRadiusApplication: 'end'
                }
            },
            dataLabels: { enabled: false },
            stroke: {
                show: true,
                width: 2,
                colors: ['transparent']
            },
            xaxis: Object.assign({}, baseOptions().xaxis, {
                categories: data.categories
            }),
            fill: { opacity: 0.9 },
            tooltip: {
                theme: document.documentElement.getAttribute('data-bs-theme') === 'dark' ? 'dark' : 'light',
                y: {
                    formatter: function (val) {
                        return '$' + val.toLocaleString();
                    }
                }
            }
        });

        if (chartInstances.monthlyOverview) {
            chartInstances.monthlyOverview.destroy();
        }
        chartInstances.monthlyOverview = new ApexCharts(el, options);
        chartInstances.monthlyOverview.render();
    }

    /* ==================================================================
     * 5.  Theme change handler
     * ================================================================*/

    function onThemeChanged() {
        // Re-render all active charts with updated colours
        if (chartInstances.cashFlow) {
            renderCashFlowChart('#cash-flow-chart');
        }
        if (chartInstances.revenueDonut) {
            renderRevenueDonut('#revenue-donut-chart');
        }
        if (chartInstances.monthlyOverview) {
            renderMonthlyOverview('#monthly-overview-chart');
        }
    }

    /* ==================================================================
     * 6.  Public initialisation
     * ================================================================*/

    /**
     * Initialise all dashboard charts.
     * Call this from your dashboard template after the DOM is ready
     * and (optionally) after setting window.__dashboardData.
     *
     * @param {Object} [data]  Optional data object. If provided it
     *                         will be assigned to window.__dashboardData
     *                         before charts are rendered.
     */
    function initCharts(data) {
        if (typeof ApexCharts === 'undefined') {
            console.warn('NavDashboardCharts: ApexCharts library not loaded. Skipping chart init.');
            return;
        }

        if (data) {
            window.__dashboardData = data;
        }

        renderCashFlowChart('#cash-flow-chart');
        renderRevenueDonut('#revenue-donut-chart');
        renderMonthlyOverview('#monthly-overview-chart');

        // Listen for theme changes to re-render with correct colours
        document.removeEventListener('theme:changed', onThemeChanged);
        document.addEventListener('theme:changed', onThemeChanged);
    }

    /**
     * Destroy all chart instances and free memory.
     */
    function destroyCharts() {
        Object.keys(chartInstances).forEach(function (key) {
            if (chartInstances[key]) {
                chartInstances[key].destroy();
                chartInstances[key] = null;
            }
        });
    }

    /* ==================================================================
     * Expose public API
     * ================================================================*/
    window.NavDashboardCharts = {
        init:                 initCharts,
        destroy:              destroyCharts,
        renderCashFlowChart:  renderCashFlowChart,
        renderRevenueDonut:   renderRevenueDonut,
        renderMonthlyOverview:renderMonthlyOverview
    };

    // NOTE: Dashboard charts are NOT auto-initialised. They should be
    // explicitly called from the dashboard template after the Django
    // context data has been injected:
    //
    //   <script>
    //     document.addEventListener('DOMContentLoaded', function() {
    //       NavDashboardCharts.init({
    //         cashFlow:         {{ cash_flow_json|safe }},
    //         revenueBreakdown: {{ revenue_breakdown_json|safe }},
    //         monthlyOverview:  {{ monthly_overview_json|safe }}
    //       });
    //     });
    //   </script>

})();
