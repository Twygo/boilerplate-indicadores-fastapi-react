import axios from "axios";

export const api = axios.create({ baseURL: "/api" });

export type FilterOptions = {
  categories: string[];
  regions: string[];
  channels: string[];
  date_min: string | null;
  date_max: string | null;
};

export type SeriesPoint = { label: string; revenue: number; units: number };

export type Summary = {
  total_revenue: number;
  total_units: number;
  total_sales: number;
  average_ticket: number;
  by_month: SeriesPoint[];
  by_category: SeriesPoint[];
  by_region: SeriesPoint[];
  by_channel: SeriesPoint[];
};

export type Filters = {
  date_from?: string;
  date_to?: string;
  category?: string;
  region?: string;
  channel?: string;
};

export async function getFilterOptions(): Promise<FilterOptions> {
  const { data } = await api.get("/sales/filters/options");
  return data;
}

export async function getSummary(filters: Filters): Promise<Summary> {
  const { data } = await api.get("/sales/summary", { params: filters });
  return data;
}
