/**
 * Shared Chart.js configuration helpers.
 *
 * These functions return plain objects (no function values) so they can be
 * safely serialised with JSON.stringify and spread into the x-data template
 * literals used by Astro + Alpine chart components.
 *
 * Functions (tooltip callbacks, tick callbacks) MUST remain as literal code
 * strings inside the x-data template literal — JSON.stringify silently drops
 * them, so they are intentionally excluded here.
 */

/**
 * Returns the tooltip styling properties that are identical in every chart.
 * Does NOT include `callbacks` — those differ per chart and must stay inline.
 */
export function getSharedTooltipConfig(): Record<string, unknown> {
  return {
    backgroundColor: '#18181b',
    titleColor: '#a1a1aa',
    bodyColor: '#fafafa',
    borderColor: '#27272a',
    borderWidth: 1,
    padding: 12,
  };
}

/**
 * Returns the `scales` config shared between charts.
 * The x scale is identical everywhere.
 * The y scale differs only in `grid.color`; pass `yGridColor` to customise it.
 * The y `ticks.callback` function is excluded (not serialisable) and must be
 * added inline in each component.
 *
 * @param yGridColor  CSS colour string for the y-axis grid lines.
 *                    Defaults to the value used in PriceChart.
 */
export function getSharedScaleConfig(
  yGridColor = 'rgba(255,255,255,0.05)',
): Record<string, unknown> {
  return {
    x: {
      grid: { display: false },
      border: { display: false },
      ticks: { color: '#71717a', font: { size: 12 } },
    },
    y: {
      grid: { color: yGridColor },
      border: { display: false },
      ticks: { color: '#71717a', font: { size: 12 } },
      // Note: ticks.callback must be added inline — functions are not serialisable.
    },
  };
}

/**
 * Composes a full Chart.js `options` object (without tooltip callbacks or
 * ticks callbacks, which contain functions and cannot be serialised).
 *
 * Callers must merge the result with:
 *   - `plugins.tooltip.callbacks`
 *   - `scales.y.ticks.callback`
 *
 * @param overrides.yGridColor  Forwarded to `getSharedScaleConfig`.
 */
export function getSharedChartOptions(
  overrides: { yGridColor?: string } = {},
): Record<string, unknown> {
  const scales = getSharedScaleConfig(overrides.yGridColor);
  return {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: { display: false },
      tooltip: getSharedTooltipConfig(),
    },
    scales,
  };
}
