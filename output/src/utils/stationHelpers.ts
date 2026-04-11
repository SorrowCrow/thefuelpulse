export const FUEL_ALIASES: Record<string, string> = {
  diesel_ecto: 'diesel',
  petrol_95_premium: 'petrol_95',
};

/**
 * Normalizes stations for CheapestFuelWidget.
 * Returns an array of station objects where each has a `prices` map
 * with keys diesel / petrol_95 / petrol_98.
 * Supports both old schema (prices: {}) and new schema (fuel_entries: []).
 */
export function normalizeStationPrices(
  stations: any[]
): Array<{ brand: string; prices: Record<string, number | null> }> {
  return stations
    .filter((s) => !s.error)
    .map((s) => {
      if (s.prices) return s;
      const prices: Record<string, number | null> = {
        diesel: null,
        petrol_95: null,
        petrol_98: null,
      };
      for (const e of s.fuel_entries ?? []) {
        const key = FUEL_ALIASES[e.fuel_type] ?? e.fuel_type;
        if (key in prices && e.price != null) {
          prices[key] =
            prices[key] === null ? e.price : Math.min(prices[key]!, e.price);
        }
      }
      return { ...s, prices };
    });
}

/**
 * Normalizes stations for FuelSavingsCalculator.
 * Returns a flat per-station object with brand / diesel / petrol_95 / petrol_98 keys.
 * Supports both old schema (prices: {}) and new schema (fuel_entries: []).
 */
export function normalizeStationFlat(
  stations: any[]
): Array<{
  brand: string;
  diesel: number | null;
  petrol_95: number | null;
  petrol_98: number | null;
}> {
  return stations
    .filter((s) => !s.error)
    .map((s) => {
      if (s.prices) {
        return {
          brand: s.brand,
          diesel: s.prices.diesel ?? null,
          petrol_95: s.prices.petrol_95 ?? null,
          petrol_98: s.prices.petrol_98 ?? null,
        };
      }
      const prices: Record<string, number | null> = {
        diesel: null,
        petrol_95: null,
        petrol_98: null,
      };
      for (const e of s.fuel_entries ?? []) {
        const key = FUEL_ALIASES[e.fuel_type] ?? e.fuel_type;
        if (key in prices && e.price != null) {
          prices[key] =
            prices[key] === null ? e.price : Math.min(prices[key]!, e.price);
        }
      }
      return {
        brand: s.brand,
        diesel: prices.diesel,
        petrol_95: prices.petrol_95,
        petrol_98: prices.petrol_98,
      };
    });
}

/**
 * Normalizes stations for HomePageContent.
 * Returns station objects with a `prices` map and a `displayLabels` map
 * (e.g. diesel → "Viada ADUS").
 * Supports both old schema (prices: {}) and new schema (fuel_entries: []).
 */
export function normalizeStationWithLabels(
  stations: any[]
): Array<{
  brand: string;
  prices: Record<string, number | null>;
  displayLabels: Record<string, string>;
  [key: string]: any;
}> {
  return stations
    .filter((s: any) => !s.error)
    .map((s: any) => {
      if (s.prices) return { ...s, displayLabels: {} }; // old schema — pass through
      const prices: Record<string, number | null> = {
        diesel: null,
        petrol_95: null,
        petrol_98: null,
      };
      const displayLabels: Record<string, string> = {};
      for (const entry of s.fuel_entries ?? []) {
        const key = FUEL_ALIASES[entry.fuel_type] ?? entry.fuel_type;
        if (key in prices && entry.price != null) {
          if (prices[key] === null || entry.price < prices[key]!) {
            prices[key] = entry.price;
            displayLabels[key] = entry.station_type
              ? `${s.brand} ${entry.station_type}`
              : s.brand;
          }
        }
      }
      return { ...s, prices, displayLabels };
    });
}
