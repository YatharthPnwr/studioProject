"use client";
import { useEffect, useState, useCallback } from "react";
import Image from "next/image";
import Nav from "@/components/Nav";
import EmptyState from "@/components/EmptyState";
import { api, DatasetStatus } from "@/lib/api";
import { useSession } from "@/lib/useSession";

// ── Category config ─────────────────────────────────────────────────────────

type CategoryKey = "electronics" | "grocery" | "health_household" | "health_personal";

interface Category {
  key: CategoryKey;
  label: string;
  prefix: string;
  color: string;          // accent for button active state
  borderColor: string;    // tailwind-friendly inline style
  description: string;
}

const CATEGORIES: Category[] = [
  {
    key: "electronics",
    label: "Electronics",
    prefix: "Electronics",
    color: "#6366f1",
    borderColor: "#6366f1",
    description: "520K+ products · Computers, accessories, audio, cameras & more",
  },
  {
    key: "grocery",
    label: "Grocery & Gourmet Food",
    prefix: "Grocery_and_Gourmet_Food",
    color: "#10b981",
    borderColor: "#10b981",
    description: "Packaged foods, beverages, organic & specialty items",
  },
  {
    key: "health_household",
    label: "Health & Household",
    prefix: "Health_Household",
    color: "#14b8a6",
    borderColor: "#14b8a6",
    description: "Household cleaning, personal care basics & vitamins",
  },
  {
    key: "health_personal",
    label: "Health & Personal Care",
    prefix: "Health_and_Personal_Care",
    color: "#ec4899",
    borderColor: "#ec4899",
    description: "Beauty, grooming, wellness & medical devices",
  },
];

const GRAPHS = [
  { suffix: "_rating_dist",         title: "Rating Distribution",          subtitle: "Histogram + KDE of average star ratings" },
  { suffix: "_price_dist",          title: "Price Distribution",           subtitle: "Log-scale histogram & box plot of product prices" },
  { suffix: "_volume_vs_rating",    title: "Review Volume vs. Rating",     subtitle: "Hexbin density — how reviews correlate with ratings" },
  { suffix: "_correlation_heatmap", title: "Numeric Correlation Matrix",   subtitle: "Pearson correlations across all numeric features" },
  { suffix: "_pivot_heatmap",       title: "Store × Category Ratings",     subtitle: "Mean rating per store/brand across top sub-categories" },
  { suffix: "_temporal_line",       title: "Temporal Catalog Growth",      subtitle: "Product count & average rating trend year over year" },
  { suffix: "_completeness",        title: "Data Completeness",            subtitle: "Percentage of rows populated per column" },
];

// ── Dashboard ────────────────────────────────────────────────────────────────

export default function DashboardPage() {
  useSession();

  const [status, setStatus] = useState<DatasetStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeCat, setActiveCat] = useState<CategoryKey>("electronics");

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const s = await api.datasetStatus();
      setStatus(s);
    } catch (e: any) {
      setError(e?.detail?.detail || e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const cat = CATEGORIES.find((c) => c.key === activeCat)!;

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

        {/* EDA section — show regardless of dataset load state once not loading */}
        {!loading && !error && (
          <>
            {/* Page heading */}
            <div className="mb-8">
              <h1 className="font-serif text-4xl font-medium tracking-tightest text-ink-900">
                EDA Dashboard
              </h1>
              <p className="mt-1.5 text-sm text-ink-500">
                Exploratory data analysis across all four Amazon product categories.
                Select a category to view its complete analysis suite.
              </p>
            </div>

            {/* ── Category selector ─────────────────────────────────────── */}
            <div className="flex flex-wrap gap-3 mb-8">
              {CATEGORIES.map((c) => {
                const active = c.key === activeCat;
                return (
                  <button
                    key={c.key}
                    onClick={() => setActiveCat(c.key)}
                    style={
                      active
                        ? { borderColor: c.color, color: c.color, background: `${c.color}12` }
                        : {}
                    }
                    className={`
                      inline-flex flex-col items-start gap-0.5
                      px-4 py-3 rounded-md border text-left transition-all
                      ${active
                        ? "border-current font-medium shadow-crisp"
                        : "border-ink-200 text-ink-600 hover:border-ink-400 hover:text-ink-900 bg-white"
                      }
                    `}
                  >
                    <span className="text-sm font-medium leading-tight">{c.label}</span>
                    <span
                      className="text-[10px] leading-snug"
                      style={{ color: active ? c.color : "#737373", opacity: active ? 0.8 : 1 }}
                    >
                      {c.description}
                    </span>
                  </button>
                );
              })}
            </div>

            {/* ── Active category header ─────────────────────────────────── */}
            <div
              className="flex items-center gap-3 mb-6 pb-4 border-b border-ink-200"
            >
              <span
                className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                style={{ background: cat.color }}
              />
              <div>
                <h2 className="text-base font-medium text-ink-900">{cat.label}</h2>
                <p className="text-xs text-ink-500">{cat.description}</p>
              </div>
              <span className="ml-auto text-[10px] font-mono uppercase tracking-wider text-ink-400">
                7 analyses
              </span>
            </div>

            {/* ── Graph grid ─────────────────────────────────────────────── */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              {GRAPHS.map((g, idx) => {
                const imgPath = `/eda/${cat.prefix}${g.suffix}.png`;
                const isWide = idx === GRAPHS.length - 1 && GRAPHS.length % 2 !== 0;
                return (
                  <div
                    key={g.suffix}
                    className={`bg-white border border-ink-200 rounded-md overflow-hidden shadow-crisp ${
                      isWide ? "lg:col-span-2" : ""
                    }`}
                  >
                    {/* Card header */}
                    <div
                      className="flex items-center justify-between px-5 py-3 border-b"
                      style={{ borderColor: "#f5f5f5" }}
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <span
                            className="text-[10px] font-mono font-medium px-1.5 py-0.5 rounded-sm"
                            style={{
                              background: `${cat.color}18`,
                              color: cat.color,
                            }}
                          >
                            {String(idx + 1).padStart(2, "0")}
                          </span>
                          <h3 className="text-sm font-medium text-ink-900">{g.title}</h3>
                        </div>
                        <p className="text-[11px] text-ink-500 mt-0.5 ml-8">{g.subtitle}</p>
                      </div>
                    </div>

                    {/* Image */}
                    <div className="p-3 bg-[#111827]">
                      <div className="relative w-full" style={{ paddingBottom: "60%" }}>
                        <Image
                          src={imgPath}
                          alt={`${cat.label} — ${g.title}`}
                          fill
                          className="object-contain rounded-sm"
                          sizes="(max-width: 1024px) 100vw, 50vw"
                          priority={idx < 2}
                        />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* ── Dataset info strip (if loaded) ─────────────────────────── */}
            {status?.loaded && status.info && (
              <section className="mt-8 bg-white border border-ink-200 rounded-md">
                <div className="flex items-center justify-between px-5 py-3 border-b border-ink-100">
                  <h2 className="text-xs font-medium text-ink-500 uppercase tracking-wider">
                    Live Dataset
                  </h2>
                  <span className="text-xs text-ink-400">
                    Amazon Product Datasets — 4 categories
                  </span>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 divide-x divide-ink-100">
                  <Stat label="Total records" value={status.info.total_records.toLocaleString()} />
                  <Stat label="Unique products" value={status.info.unique_products.toLocaleString()} />
                  <Stat label="Date range start" value={
                    status.info.date_range_start
                      ? new Date(status.info.date_range_start).toLocaleDateString()
                      : "—"
                  } />
                  <Stat label="Date range end" value={
                    status.info.date_range_end
                      ? new Date(status.info.date_range_end).toLocaleDateString()
                      : "—"
                  } />
                </div>
              </section>
            )}
          </>
        )}
      </main>
    </>
  );
}

// ── Sub-components ────────────────────────────────────────────────────────────

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="px-5 py-4">
      <div className="text-[10px] uppercase tracking-wider text-ink-500 mb-1.5">{label}</div>
      <div className="text-sm font-medium text-ink-900 truncate" title={value}>
        {value}
      </div>
    </div>
  );
}
