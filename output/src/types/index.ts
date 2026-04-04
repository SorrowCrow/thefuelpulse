export type FuelType = 'diesel' | 'petrol_95' | 'petrol_98';

export interface FuelPrices {
  diesel: number | null;
  petrol_95: number | null;
  petrol_98: number | null;
}

export interface FuelAverages {
  diesel: number;
  petrol_95: number;
  petrol_98: number;
}

export interface Station {
  brand: string;
  key: string;
  prices: FuelPrices;
  currency: string;
  error: string | null;
}

export interface StationPricesData {
  scraped_at: string;
  stations: Station[];
}

export interface PriceHistory {
  date: string;
  diesel: number;
  petrol_95: number;
  petrol_98: number;
}

export interface PriceData {
  averages: FuelAverages;
  currency: string;
  unit: string;
  last_updated: string;
  history: PriceHistory[];
}

export interface NewsArticle {
  id: number;
  title_lv: string;
  title_en: string;
  summary_lv: string;
  summary_en: string;
  date: string;
  category: string;
}

export interface NewsData {
  articles: NewsArticle[];
}
