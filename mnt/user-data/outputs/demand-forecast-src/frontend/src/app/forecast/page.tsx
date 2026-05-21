"use client";
import { useEffect, useState, useCallback } from "react";
import Nav from "@/components/Nav";
import EmptyState from "@/components/EmptyState";
import ProductCard from "@/components/ProductCard";
import { api, DatasetStatus, WeekForecast } from "@/lib/api";
import { useSession } from "@/lib/useSession";
import { Loader2 } from "lucide-react";

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];
const WEEKS = [1, 2, 3, 4];
const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const TOP_N_OPTIONS = [3, 5, 10, 15, 20];

export default function ForecastPage() {
  useSession();

  const [status, setStatus] = useState<DatasetStatus | null>(null);
  const [month, setMonth] = useState(10);
  const [week, setWeek] = useState(1);
  const [topN, setTopN] = useState(5);
  const [data, setData] = useState<WeekForecast | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const s = await api.datasetStatus();
      setStatus(s);
    } catch (e: any) {
      setError(e?.detail?.detail || e.message);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  useEffect(() => {
    if (!status?.loaded) return;
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await api.forecastWeek(month, week, topN);
        if (!cancelled) setData(res);
      } catch (e: any) {
        if (!cancelled) setError(e?.detail?.detail || e.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [month, week, topN, status?.loaded]);

  if (status && !status.loaded) {
    return (
      <>
        <Nav datasetStatus={status} />
        <EmptyState error={status.last_error} />
      </>
    );
  }

  return (
    <>
      <Nav datasetStatus={status} />
      <main className="max-w-7xl mx-auto px-8 py-10">
        <div className="mb-8">
          <h1 className="font-serif text-4xl font-medium tracking-tightest text-ink-900">
            Forecast
          </h1>
          <p className="mt-1.5 text-sm text-ink-500 max-w-2xl">
            Top-demand products for each day — ranked by predicted demand across all
            categories (Electronics, Grocery, Health &amp; Household, Health &amp; Personal Care).
            Based on historical patterns from the same month, week-of-month, and weekday
            in previous years with recency-weighting.
          </p>
        </div>

        {/* Controls */}
        <section className="bg-white border border-ink-200 rounded-md p-4 mb-6 flex flex-wrap items-end gap-6">
          <Field label="Month">
            <select
              value={month}
              onChange={(e) => setMonth(Number(e.target.value))}
              className="px-3 py-1.5 border border-ink-300 rounded-sm text-sm bg-white"
            >
              {MONTHS.map((m, i) => (
                <option key={m} value={i + 1}>
                  {m}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Top products per day">
            <select
              value={topN}
              onChange={(e) => setTopN(Number(e.target.value))}
              className="px-3 py-1.5 border border-ink-300 rounded-sm text-sm bg-white"
            >
              {TOP_N_OPTIONS.map((n) => (
                <option key={n} value={n}>
                  Top {n}
                </option>
              ))}
            </select>
          </Field>

          <div className="ml-auto text-xs text-ink-500">
            {loading ? (
              <span className="inline-flex items-center gap-1.5">
                <Loader2 className="w-3 h-3 animate-spin" /> Updating
              </span>
            ) : (
              <span>
                {MONTHS[month - 1]} · Week {week}
              </span>
            )}
          </div>
        </section>

        {/* Week tabs */}
        <div className="flex border-b border-ink-200 mb-5">
          {WEEKS.map((w) => (
            <button
              key={w}
              onClick={() => setWeek(w)}
              className={`px-5 py-2.5 text-sm border-b-2 -mb-px transition-colors ${
                week === w
                  ? "border-ink-900 text-ink-900 font-medium"
                  : "border-transparent text-ink-500 hover:text-ink-900"
              }`}
            >
              Week {w}
            </button>
          ))}
        </div>

        {error && (
          <div className="mb-4 text-sm text-signal-red border-l-2 border-signal-red pl-3 py-2">
            {error}
          </div>
        )}

        {/* Day-by-day — products mixed across all categories, ranked by demand */}
        <div className="space-y-3">
          {DAYS.map((day) => {
            const products = data?.forecast_by_day?.[day] ?? [];
            return (
              <div
                key={day}
                className="bg-white border border-ink-200 rounded-md overflow-hidden"
              >
                <div className="px-5 py-2.5 border-b border-ink-100 bg-ink-50 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="font-serif text-base font-medium text-ink-900">
                      {day}
                    </span>
                    <span className="text-xs text-ink-500">
                      Week {week} of {MONTHS[month - 1]}
                    </span>
                  </div>
                  <span className="text-[10px] font-mono uppercase tracking-wider text-ink-500">
                    {products.length} product{products.length === 1 ? "" : "s"} · all categories
                  </span>
                </div>
                <div className="p-3">
                  {products.length === 0 ? (
                    <p className="py-6 text-center text-xs text-ink-400 italic">
                      No historical data for this day.
                    </p>
                  ) : (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-2">
                      {products.map((p, idx) => (
                        <ProductCard key={p.parent_asin} product={p} rank={idx + 1} />
                      ))}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </main>
    </>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-[10px] font-medium text-ink-500 uppercase tracking-wider">
        {label}
      </label>
      {children}
    </div>
  );
}
