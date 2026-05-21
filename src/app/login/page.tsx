"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, auth } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    // If already logged in, send to dashboard
    if (auth.isLoggedIn()) router.replace("/");
  }, [router]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const res = await api.login(username, password);
      auth.setToken(res.token);
      router.replace("/");
    } catch (err: any) {
      setError(err?.detail?.detail || err?.message || "Login failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-ink-50 bg-grid flex items-center justify-center px-6">
      <div className="w-full max-w-sm">
        {/* Brand mark */}
        <div className="mb-12 text-center">
          <div className="inline-flex items-center justify-center w-12 h-12 mb-5 border border-ink-900 rounded-sm">
            <span className="font-serif text-xl font-semibold tracking-tightest">df</span>
          </div>
          <h1 className="font-serif text-3xl font-medium tracking-tightest text-ink-900">
            Demand Forecasting
          </h1>
          <p className="mt-2 text-sm text-ink-500">Inventory intelligence platform</p>
        </div>

        {/* Card */}
        <div className="bg-white border border-ink-200 rounded-md shadow-crisp p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-xs font-medium text-ink-700 mb-1.5 uppercase tracking-wide">
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoFocus
                autoComplete="username"
                className="w-full px-3 py-2 border border-ink-300 rounded-sm bg-white text-ink-900 text-sm focus:border-accent-500 focus:ring-0 outline-none transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-700 mb-1.5 uppercase tracking-wide">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                className="w-full px-3 py-2 border border-ink-300 rounded-sm bg-white text-ink-900 text-sm focus:border-accent-500 focus:ring-0 outline-none transition-colors"
              />
            </div>

            {error && (
              <div className="text-sm text-signal-red border-l-2 border-signal-red pl-3 py-1">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="w-full bg-ink-900 text-white text-sm font-medium py-2.5 rounded-sm hover:bg-ink-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? "Signing in…" : "Sign in"}
            </button>
          </form>

          <div className="mt-6 pt-5 border-t border-ink-100 text-xs text-ink-500">
            Demo credentials:{" "}
            <code className="font-mono text-ink-700">admin</code> /{" "}
            <code className="font-mono text-ink-700">admin</code>
          </div>
        </div>

        <p className="mt-8 text-center text-xs text-ink-400">
          © Demand Forecasting Platform
        </p>
      </div>
    </div>
  );
}
