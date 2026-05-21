"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSession } from "@/lib/useSession";
import { DatasetStatus } from "@/lib/api";
import { Database, LogOut } from "lucide-react";

interface NavProps {
  datasetStatus?: DatasetStatus | null;
}

export default function Nav({ datasetStatus }: NavProps) {
  const pathname = usePathname();
  const { username, logout } = useSession({ redirectIfUnauth: false });

  const links = [
    { href: "/", label: "Dashboard" },
    { href: "/forecast", label: "Forecast" },
  ];

  return (
    <header className="bg-white border-b border-ink-200 sticky top-0 z-20">
      <div className="max-w-7xl mx-auto px-8 h-14 flex items-center justify-between">
        {/* Left: brand + nav */}
        <div className="flex items-center gap-10">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="w-7 h-7 border border-ink-900 rounded-sm flex items-center justify-center">
              <span className="font-serif text-sm font-semibold tracking-tightest">df</span>
            </div>
            <span className="font-serif text-base font-medium tracking-tight text-ink-900">
              Demand Forecasting
            </span>
          </Link>

          <nav className="flex items-center gap-1">
            {links.map((l) => {
              const active = pathname === l.href;
              return (
                <Link
                  key={l.href}
                  href={l.href}
                  className={`px-3 py-1.5 text-sm rounded-sm transition-colors ${
                    active
                      ? "text-ink-900 font-medium"
                      : "text-ink-500 hover:text-ink-900"
                  }`}
                >
                  {l.label}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Right: dataset status chip + user */}
        <div className="flex items-center gap-3">
          {datasetStatus && (
            <div className="flex items-center gap-2 px-3 py-1.5 border border-ink-200 rounded-sm text-xs">
              <Database
                className={`w-3.5 h-3.5 ${
                  datasetStatus.loaded ? "text-signal-green" : "text-ink-400"
                }`}
              />
              <span className="text-ink-700 max-w-[240px] truncate">
                {datasetStatus.loaded
                  ? "Amazon Datasets — 4 categories"
                  : "Loading datasets…"}
              </span>
            </div>
          )}

          <div className="h-5 w-px bg-ink-200" />

          <span className="text-xs text-ink-500 font-mono">{username || "—"}</span>
          <button
            onClick={logout}
            className="p-1.5 text-ink-400 hover:text-ink-900 transition-colors"
            title="Sign out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
