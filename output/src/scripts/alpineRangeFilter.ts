/**
 * Shared Alpine range-filter mixin for chart components.
 * Provides the initial state values for: range, fromDate, toDate.
 * NOTE: setRange() calls this.updateChart() which is chart-specific,
 * so it must remain defined inline in each component's x-data.
 * JSON.stringify drops functions — only state properties are exported.
 */
export function rangeFilterMixin() {
  return {
    range: '7d' as string,
    fromDate: '' as string,
    toDate: '' as string,
  };
}
