"use client";
import { useEffect, useState, useCallback } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
} from "recharts";
import Nav from "@/components/Nav";
import EmptyState from "@/components/EmptyState";
import { api, DatasetStatus } from "@/lib/api";
import { useSession } from "@/lib/useSession";

const CHART_COLOR = "#1a3a8f";
const CHART_GRID = "#e5e5e5";

export default function DashboardPage() {
  useSession();

  const [status, setStatus] = useState<DatasetStatus | null>(null);
  const [monthly, setMonthly] = useState<any[]>([]);
  const [yearly, setYearly] = useState<any[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const s = await api.datasetStatus();
      setStatus(s);
      if (s.loaded) {
        const [m, y, c] = await Promise.all([
          api.monthlyTrend(),
          api.yearlyTrend(),
          api.topCategories(8),
        ]);
        setMonthly(m);
        setYearly(y);
        setCategories(c);
      }
    } catch (e: any) {
      setError(e?.detail?.detail || e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <>
      <Nav datasetStatus={status} />
      <main className="max-w-7xl mx-auto px-8 py-10">
        {loading && !status && (
          <div className="text-center py-20 text-sm text-ink-500">Loading…</div>
        )}

        {error && (
          <div className="max-w-xl mx-auto py-20 text-center">
            <p className="text-sm text-signal-red">Error: {error}</p>
            <p className="text-xs text-ink-500 mt-2">
              Verify the backend is running on{" "}
              <code className="font-mono">http://localhost:8000</code>.
            </p>
          </div>
        )}

        {!loading && !error && status && !status.loaded && (
          <EmptyState error={status.last_error} />
        )}

        {!loading && status?.loaded && status.info && (
          <>
            {/* Page heading */}
            <div className="mb-8">
              <h1 className="font-serif text-4xl font-medium tracking-tightest text-ink-900">
                Dashboard
              </h1>
              <p className="mt-1.5 text-sm text-ink-500">
                Historical patterns across all Amazon product categories.
              </p>
            </div>

            {/* Dataset summary card */}
            <section className="bg-white border border-ink-200 rounded-md mb-8">
              <div className="flex items-center justify-between px-5 py-3 border-b border-ink-100">
                <h2 className="text-xs font-medium text-ink-500 uppercase tracking-wider">
                  Active Dataset
                </h2>
                <span className="text-xs text-ink-400">
                  Amazon Product Datasets — 4 categories
                </span>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 divide-x divide-ink-100">
                <Stat label="Total records" value={status.info.total_records.toLocaleString()} />
                <Stat label="Unique products" value={status.info.unique_products.toLocaleString()} />
                <Stat label="Categories" value={String(categories.length || "—")} />
                <Stat label="Years covered" value={status.info.years_covered.join(", ")} />
              </div>
              <div className="border-t border-ink-100 px-5 py-3 text-xs text-ink-500">
                {status.info.date_range_start &&
                  `Date range: ${new Date(
                    status.info.date_range_start
                  ).toLocaleDateString()} — ${new Date(
                    status.info.date_range_end!
                  ).toLocaleDateString()}`}
              </div>
            </section>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              <ChartCard title="Sales by month" subtitle="Aggregated across all years and categories">
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={monthly} margin={{ top: 5, right: 5, left: -10, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID} vertical={false} />
                    <XAxis
                      dataKey="month_name"
                      tick={{ fontSize: 10, fill: "#525252" }}
                      tickLine={false}
                      axisLine={{ stroke: CHART_GRID }}
                    />
                    <YAxis
                      tick={{ fontSize: 10, fill: "#525252" }}
                      tickLine={false}
                      axisLine={false}
                    />
                    <Tooltip
                      contentStyle={{
                        background: "white",
                        border: "1px solid #e5e5e5",
                        borderRadius: 2,
                        fontSize: 11,
                      }}
                    />
                    <Bar dataKey="total_sales" fill={CHART_COLOR} radius={[2, 2, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>

              <ChartCard title="Sales by year" subtitle="Trend over time">
                <ResponsiveContainer width="100%" height={240}>
                  <LineChart data={yearly} margin={{ top: 5, right: 5, left: -10, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID} vertical={false} />
                    <XAxis
                      dataKey="year"
                      tick={{ fontSize: 10, fill: "#525252" }}
                      tickLine={false}
                      axisLine={{ stroke: CHART_GRID }}
                    />
                    <YAxis
                      tick={{ fontSize: 10, fill: "#525252" }}
                      tickLine={false}
                      axisLine={false}
                    />
                    <Tooltip
                      contentStyle={{
                        background: "white",
                        border: "1px solid #e5e5e5",
                        borderRadius: 2,
                        fontSize: 11,
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="total_sales"
                      stroke={CHART_COLOR}
                      strokeWidth={1.5}
                      dot={{ r: 3, fill: CHART_COLOR }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </ChartCard>

              <ChartCard
                title="Categories"
                subtitle="All categories — cross-category forecasting enabled"
                span={2}
              >
                <ResponsiveContainer width="100%" height={Math.max(180, categories.length * 28)}>
                  <BarChart
                    data={categories}
                    layout="vertical"
                    margin={{ top: 5, right: 15, left: 0, bottom: 5 }}
                  >
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke={CHART_GRID}
                      horizontal={false}
                    />
                    <XAxis
                      type="number"
                      tick={{ fontSize: 10, fill: "#525252" }}
                      tickLine={false}
                      axisLine={false}
                    />
                    <YAxis
                      type="category"
                      dataKey="main_category"
                      tick={{ fontSize: 11, fill: "#0a0a0a" }}
                      width={160}
                      tickLine={false}
                      axisLine={{ stroke: CHART_GRID }}
                    />
                    <Tooltip
                      contentStyle={{
                        background: "white",
                        border: "1px solid #e5e5e5",
                        borderRadius: 2,
                        fontSize: 11,
                      }}
                    />
                    <Bar dataKey="total_sales" fill={CHART_COLOR} radius={[0, 2, 2, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>
            </div>
          </>
        )}
      </main>
    </>
  );
}

function Stat({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="px-5 py-4">
      <div className="text-[10px] uppercase tracking-wider text-ink-500 mb-1.5">{label}</div>
      <div
        className={`text-sm font-medium text-ink-900 truncate ${mono ? "font-mono text-xs" : ""}`}
        title={value}
      >
        {value}
      </div>
    </div>
  );
}

function ChartCard({
  title,
  subtitle,
  children,
  span = 1,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  span?: 1 | 2;
}) {
  return (
    <div
      className={`bg-white border border-ink-200 rounded-md ${
        span === 2 ? "lg:col-span-2" : ""
      }`}
    >
      <div className="px-5 py-3 border-b border-ink-100">
        <h3 className="text-sm font-medium text-ink-900">{title}</h3>
        {subtitle && <p className="text-xs text-ink-500 mt-0.5">{subtitle}</p>}
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}
