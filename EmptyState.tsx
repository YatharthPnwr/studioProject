"use client";
import { Database, Loader2 } from "lucide-react";

export default function EmptyState({ error }: { error?: string | null }) {
  return (
    <div className="max-w-2xl mx-auto py-20 px-6 text-center">
      <div className="inline-flex items-center justify-center w-16 h-16 border border-ink-200 rounded-md mb-6">
        {error ? (
          <Database className="w-7 h-7 text-signal-red" />
        ) : (
          <Loader2 className="w-7 h-7 text-ink-400 animate-spin" />
        )}
      </div>

      <h2 className="font-serif text-3xl font-medium tracking-tightest text-ink-900">
        {error ? "Dataset failed to load" : "Loading datasets…"}
      </h2>

      <p className="mt-3 text-sm text-ink-500 max-w-md mx-auto leading-relaxed">
        {error
          ? "The Amazon product datasets could not be loaded. Check that all 4 CSV files are present in the amazon_datasets/ directory."
          : "Loading all Amazon product datasets from amazon_datasets/. This may take a moment."}
      </p>

      {error && (
        <div className="mt-4 inline-block text-xs text-signal-red border-l-2 border-signal-red pl-2 py-1 text-left max-w-md">
          {error}
        </div>
      )}
    </div>
  );
}
