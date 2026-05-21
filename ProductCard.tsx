"use client";
import { Product } from "@/lib/api";
import { Star } from "lucide-react";

function confidenceTone(conf: number) {
  if (conf >= 75) return { text: "text-signal-green", bar: "bg-signal-green" };
  if (conf >= 50) return { text: "text-signal-amber", bar: "bg-signal-amber" };
  return { text: "text-signal-red", bar: "bg-signal-red" };
}

export default function ProductCard({
  product,
  rank,
}: {
  product: Product;
  rank: number;
}) {
  const tone = confidenceTone(product.confidence);
  return (
    <div className="flex gap-3 p-3 border border-ink-200 rounded-sm bg-white hover:border-ink-400 transition-colors">
      {/* Rank */}
      <div className="flex-shrink-0 w-6 text-center pt-0.5">
        <span className="font-serif text-base font-medium text-ink-400">
          {String(rank).padStart(2, "0")}
        </span>
      </div>

      {/* Image */}
      <div className="flex-shrink-0 w-14 h-14 border border-ink-200 bg-ink-50 overflow-hidden flex items-center justify-center rounded-sm">
        {product.image_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={product.image_url}
            alt={product.title}
            className="w-full h-full object-cover"
            onError={(e) => {
              (e.currentTarget as HTMLImageElement).style.display = "none";
            }}
          />
        ) : (
          <span className="text-[10px] text-ink-400 font-mono">no img</span>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <h4 className="text-sm font-medium text-ink-900 leading-snug line-clamp-2">
          {product.title}
        </h4>

        <div className="flex items-center gap-2 mt-1 text-xs text-ink-500">
          {product.average_rating !== null && (
            <span className="inline-flex items-center gap-0.5">
              <Star className="w-3 h-3 fill-current text-ink-400" />
              {product.average_rating.toFixed(1)}
            </span>
          )}
          {product.main_category && product.main_category !== "Unknown" && (
            <>
              <span className="text-ink-300">·</span>
              <span>{product.main_category}</span>
            </>
          )}
          <span className="text-ink-300">·</span>
          <span className="font-mono">{product.historical_years}y data</span>
        </div>

        {/* Confidence + demand row */}
        <div className="mt-2 flex items-center gap-3">
          <div className="flex-1">
            <div className="flex items-baseline justify-between mb-1">
              <span className="text-[10px] uppercase tracking-wide text-ink-500">
                Confidence
              </span>
              <span className={`text-xs font-mono font-medium ${tone.text}`}>
                {product.confidence.toFixed(0)}%
              </span>
            </div>
            <div className="h-1 bg-ink-100 rounded-full overflow-hidden">
              <div
                className={`h-full ${tone.bar} transition-all`}
                style={{ width: `${product.confidence}%` }}
              />
            </div>
          </div>
          <div className="text-right">
            <div className="text-[10px] uppercase tracking-wide text-ink-500">
              Demand
            </div>
            <div className="text-sm font-mono font-medium text-ink-900">
              {product.predicted_demand.toFixed(2)}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
