// API client — all backend calls go through here.
// Stores the auth token in localStorage and attaches it to every request.

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
const TOKEN_KEY = "df_auth_token";

export const auth = {
  getToken: (): string | null => {
    if (typeof window === "undefined") return null;
    return localStorage.getItem(TOKEN_KEY);
  },
  setToken: (t: string) => localStorage.setItem(TOKEN_KEY, t),
  clear: () => localStorage.removeItem(TOKEN_KEY),
  isLoggedIn: (): boolean => !!auth.getToken(),
};

class HttpError extends Error {
  status: number;
  detail: any;
  constructor(status: number, detail: any) {
    super(typeof detail === "string" ? detail : detail?.detail ?? "Request failed");
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> | undefined),
  };
  const token = auth.getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (options.body && !(options.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    cache: "no-store",
  });
  if (!res.ok) {
    let detail: any = null;
    try {
      detail = await res.json();
    } catch {
      detail = await res.text();
    }
    if (res.status === 401) {
      auth.clear();
    }
    throw new HttpError(res.status, detail);
  }
  return res.json();
}

const get = <T,>(path: string) => request<T>(path, { method: "GET" });
const post = <T,>(path: string, body?: any) =>
  request<T>(path, {
    method: "POST",
    body: body instanceof FormData ? body : body ? JSON.stringify(body) : undefined,
  });

// ============ Types ============
export interface DatasetInfo {
  source: string;
  total_records: number;
  unique_products: number;
  unique_users: number;
  date_range_start: string | null;
  date_range_end: string | null;
  years_covered: number[];
}

export interface DatasetStatus {
  loaded: boolean;
  source: string | null;
  source_label: string | null;
  info?: DatasetInfo;
  last_error?: string | null;
}

export interface Product {
  parent_asin: string;
  title: string;
  main_category: string;
  average_rating: number | null;
  rating_number?: number | null;
  price?: number | null;
  image_url: string | null;
  predicted_demand: number;
  confidence: number;
  historical_years: number;
  total_historical_sales: number;
}

export interface WeekForecast {
  month: number;
  week_of_month: number;
  top_n: number;
  forecast_by_day: Record<string, Product[]>;
}

export interface WeekSummary {
  month: number;
  week_of_month: number;
  top_n: number;
  products: Product[];
}

// ============ API methods ============
export const api = {
  login: (username: string, password: string) =>
    post<{ token: string; username: string }>("/api/auth/login", { username, password }),
  me: () => get<{ username: string }>("/api/auth/me"),
  datasetStatus: () => get<DatasetStatus>("/api/dataset/status"),
  datasetInfo: () => get<DatasetInfo>("/api/dataset-info"),
  monthlyTrend: () =>
    get<{ month: number; month_name: string; total_sales: number }[]>(
      "/api/charts/monthly-trend"
    ),
  yearlyTrend: () =>
    get<{ year: number; total_sales: number }[]>("/api/charts/yearly-trend"),
  topCategories: (n = 8) =>
    get<{ main_category: string; total_sales: number }[]>(
      `/api/charts/top-categories?top_n=${n}`
    ),
  weekdayDistribution: (month: number) =>
    get<{ weekday: number; weekday_name: string; total_sales: number }[]>(
      `/api/charts/weekday-distribution?month=${month}`
    ),
  forecastWeek: (month: number, week: number, topN: number) =>
    get<WeekForecast>(
      `/api/forecast/week?month=${month}&week=${week}&top_n=${topN}`
    ),
  forecastWeekSummary: (month: number, week: number, topN: number) =>
    get<WeekSummary>(
      `/api/forecast/week-summary?month=${month}&week=${week}&top_n=${topN}`
    ),
};

export { HttpError };
