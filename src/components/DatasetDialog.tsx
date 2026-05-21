"use client";
import { useState, useRef } from "react";
import { api, ColumnInfo, ColumnMapping, UploadPreview, HttpError } from "@/lib/api";
import { X, Upload, FileText, ArrowLeft, CheckCircle2, AlertCircle } from "lucide-react";

interface Props {
  open: boolean;
  onClose: () => void;
  onActivated: () => void;
}

type Step = "choose" | "mapping" | "activating" | "done";

const MAPPING_FIELDS: {
  key: keyof ColumnMapping;
  label: string;
  required: boolean;
  help: string;
}[] = [
  {
    key: "timestamp_col",
    label: "Timestamp",
    required: true,
    help: "Column with the sale/review date. Epoch seconds, milliseconds, or a date string.",
  },
  {
    key: "product_id_col",
    label: "Product ID (target)",
    required: true,
    help: "The unique product identifier. Demand is forecasted per unique value.",
  },
  {
    key: "title_col",
    label: "Product title",
    required: true,
    help: "Human-readable name shown in the UI.",
  },
  {
    key: "category_col",
    label: "Category",
    required: false,
    help: "Used for the category charts on the dashboard.",
  },
  {
    key: "rating_col",
    label: "Average rating",
    required: false,
    help: "Higher-rated products get a small lift in the forecast.",
  },
  {
    key: "rating_count_col",
    label: "Rating count",
    required: false,
    help: "Number of ratings per product. Optional display field.",
  },
  {
    key: "price_col",
    label: "Price",
    required: false,
    help: "Optional display field.",
  },
  {
    key: "image_col",
    label: "Image",
    required: false,
    help: "Column containing a URL or an image-variants dict (HiRes is extracted automatically).",
  },
];

export default function DatasetDialog({ open, onClose, onActivated }: Props) {
  const [step, setStep] = useState<Step>("choose");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [preview, setPreview] = useState<UploadPreview | null>(null);
  const [mapping, setMapping] = useState<Partial<ColumnMapping>>({});
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!open) return null;

  function reset() {
    setStep("choose");
    setBusy(false);
    setErr(null);
    setPreview(null);
    setMapping({});
  }

  function handleClose() {
    reset();
    onClose();
  }

  async function handleFile(file: File) {
    setBusy(true);
    setErr(null);
    try {
      const p = await api.uploadDataset(file);
      setPreview(p);
      // Auto-guess mapping by column-name heuristics
      const guessed = guessMapping(p.columns);
      setMapping(guessed);
      setStep("mapping");
    } catch (e: any) {
      setErr(humanError(e));
    } finally {
      setBusy(false);
    }
  }

  async function handleActivate() {
    if (!preview) return;
    // Validate required fields
    const missing = MAPPING_FIELDS.filter((f) => f.required && !mapping[f.key]);
    if (missing.length > 0) {
      setErr(`Required columns not set: ${missing.map((m) => m.label).join(", ")}`);
      return;
    }
    setBusy(true);
    setErr(null);
    setStep("activating");
    try {
      await api.activateDataset(preview.upload_id, mapping as ColumnMapping);
      setStep("done");
      setTimeout(() => {
        onActivated();
        handleClose();
      }, 800);
    } catch (e: any) {
      setErr(humanError(e));
      setStep("mapping");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink-900/40 backdrop-blur-sm">
      <div className="bg-white border border-ink-200 rounded-md shadow-xl w-full max-w-2xl max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-ink-200">
          <div className="flex items-center gap-3">
            {step === "mapping" && (
              <button
                onClick={() => {
                  setStep("choose");
                  setPreview(null);
                  setErr(null);
                }}
                className="p-1 text-ink-500 hover:text-ink-900"
              >
                <ArrowLeft className="w-4 h-4" />
              </button>
            )}
            <div>
              <h2 className="font-serif text-lg font-medium text-ink-900">
                {step === "choose" && "Attach dataset"}
                {step === "mapping" && "Configure columns"}
                {step === "activating" && "Activating…"}
                {step === "done" && "Dataset attached"}
              </h2>
              <p className="text-xs text-ink-500 mt-0.5">
                {step === "choose" && "Upload a cleaned parquet or CSV file."}
                {step === "mapping" &&
                  `${preview?.label} · ${preview?.row_count.toLocaleString()} rows · ${preview?.columns.length} columns`}
                {step === "activating" && "Preprocessing and building forecaster"}
                {step === "done" && "Ready to forecast"}
              </p>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="p-1.5 text-ink-400 hover:text-ink-900"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-5">
          {step === "choose" && (
            <ChooseStep
              busy={busy}
              onFile={handleFile}
              onPickFile={() => fileInputRef.current?.click()}
            />
          )}
          {step === "mapping" && preview && (
            <MappingStep
              columns={preview.columns}
              mapping={mapping}
              setMapping={setMapping}
            />
          )}
          {step === "activating" && (
            <div className="py-12 text-center text-ink-500 text-sm">
              <div className="inline-block w-6 h-6 border-2 border-ink-200 border-t-accent-500 rounded-full animate-spin mb-3" />
              <div>Building forecast engine…</div>
            </div>
          )}
          {step === "done" && (
            <div className="py-12 text-center">
              <CheckCircle2 className="w-12 h-12 text-signal-green mx-auto mb-3" />
              <p className="text-sm text-ink-700">Dataset is now active.</p>
            </div>
          )}

          {err && (
            <div className="mt-4 flex items-start gap-2 text-sm text-signal-red border-l-2 border-signal-red pl-3 py-2 bg-red-50/50">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>{err}</span>
            </div>
          )}
        </div>

        {/* Footer */}
        {step === "mapping" && (
          <div className="flex items-center justify-end gap-2 px-6 py-3 border-t border-ink-200">
            <button
              onClick={handleClose}
              className="px-4 py-1.5 text-sm text-ink-700 hover:text-ink-900"
            >
              Cancel
            </button>
            <button
              onClick={handleActivate}
              disabled={busy}
              className="px-4 py-1.5 bg-ink-900 text-white text-sm rounded-sm hover:bg-ink-800 disabled:opacity-50"
            >
              Activate dataset
            </button>
          </div>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept=".parquet,.pq,.csv,.tsv"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) handleFile(f);
            e.target.value = "";
          }}
          className="hidden"
        />
      </div>
    </div>
  );
}

function ChooseStep({
  busy,
  onFile,
  onPickFile,
}: {
  busy: boolean;
  onFile: (f: File) => void;
  onPickFile: () => void;
}) {
  const [drag, setDrag] = useState(false);
  return (
    <div>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDrag(true);
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDrag(false);
          const f = e.dataTransfer.files?.[0];
          if (f) onFile(f);
        }}
        onClick={onPickFile}
        className={`border-2 border-dashed rounded-md py-12 px-8 text-center cursor-pointer transition-colors ${
          drag
            ? "border-accent-500 bg-accent-50"
            : "border-ink-300 hover:border-ink-500 hover:bg-ink-50"
        }`}
      >
        {busy ? (
          <div className="text-sm text-ink-500">
            <div className="inline-block w-5 h-5 border-2 border-ink-200 border-t-accent-500 rounded-full animate-spin mb-2" />
            <div>Reading file…</div>
          </div>
        ) : (
          <>
            <Upload className="w-8 h-8 text-ink-400 mx-auto mb-3" />
            <p className="text-sm text-ink-900 font-medium">
              Drop a file here or click to browse
            </p>
            <p className="text-xs text-ink-500 mt-1">
              Parquet (.parquet) or CSV (.csv, .tsv)
            </p>
          </>
        )}
      </div>

      <div className="mt-6 pt-5 border-t border-ink-100">
        <h3 className="text-xs font-medium text-ink-700 uppercase tracking-wide mb-2">
          Next step
        </h3>
        <p className="text-xs text-ink-500 leading-relaxed">
          After upload, you&apos;ll choose which column represents the timestamp,
          product ID, title, etc. The forecaster needs these to find historical
          patterns by month, week-of-month, and weekday.
        </p>
      </div>
    </div>
  );
}

function MappingStep({
  columns,
  mapping,
  setMapping,
}: {
  columns: ColumnInfo[];
  mapping: Partial<ColumnMapping>;
  setMapping: (m: Partial<ColumnMapping>) => void;
}) {
  return (
    <div className="space-y-4">
      <div className="bg-accent-50 border-l-2 border-accent-500 px-3 py-2 text-xs text-ink-700">
        Map your dataset columns to the fields below. <strong>Required</strong>{" "}
        fields define <strong>what</strong> is forecasted. Optional fields enrich the
        forecast and display.
      </div>

      {MAPPING_FIELDS.map((f) => (
        <div key={f.key} className="grid grid-cols-12 gap-3 items-start">
          <div className="col-span-4">
            <label className="block text-sm font-medium text-ink-900">
              {f.label}
              {f.required && <span className="text-signal-red ml-1">*</span>}
            </label>
            <p className="text-xs text-ink-500 mt-0.5 leading-snug">{f.help}</p>
          </div>
          <div className="col-span-8">
            <select
              value={(mapping[f.key] as string) || ""}
              onChange={(e) =>
                setMapping({
                  ...mapping,
                  [f.key]: e.target.value || undefined,
                })
              }
              className="w-full px-3 py-1.5 border border-ink-300 rounded-sm bg-white text-sm focus:border-accent-500 outline-none"
            >
              <option value="">— None —</option>
              {columns.map((c) => (
                <option key={c.name} value={c.name}>
                  {c.name} ({c.dtype})
                </option>
              ))}
            </select>
            {mapping[f.key] && (
              <p className="text-xs text-ink-400 mt-1 font-mono truncate">
                e.g. {columns.find((c) => c.name === mapping[f.key])?.sample || "—"}
              </p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

// ---- helpers ----
function guessMapping(columns: ColumnInfo[]): Partial<ColumnMapping> {
  const names = columns.map((c) => c.name.toLowerCase());
  function find(...patterns: string[]) {
    for (const p of patterns) {
      const i = names.findIndex((n) => n === p);
      if (i >= 0) return columns[i].name;
    }
    for (const p of patterns) {
      const i = names.findIndex((n) => n.includes(p));
      if (i >= 0) return columns[i].name;
    }
    return undefined;
  }
  return {
    timestamp_col: find("timestamp", "date", "time"),
    product_id_col: find("parent_asin", "asin", "product_id", "sku"),
    title_col: find("title", "name", "product_name"),
    rating_col: find("average_rating", "avg_rating", "rating"),
    rating_count_col: find("rating_number", "rating_count", "num_ratings"),
    category_col: find("main_category", "category"),
    price_col: find("price"),
    image_col: find("images", "image", "image_url"),
  };
}

function humanError(e: any): string {
  if (e instanceof HttpError) {
    if (typeof e.detail === "string") return e.detail;
    return e.detail?.detail || e.message;
  }
  return e?.message || "Something went wrong";
}
