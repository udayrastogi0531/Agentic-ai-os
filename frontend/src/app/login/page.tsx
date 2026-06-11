"use client";

/**
 * Uday AI — Login Page
 *
 * Premium glassmorphic login screen.
 */

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import api from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // If already logged in, redirect to dashboard
    if (api.getToken()) {
      router.push("/");
    }
  }, [router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError("Please fill in all fields");
      return;
    }

    setError("");
    setIsLoading(true);

    try {
      await api.login(email, password);
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invalid email or password");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      className="flex min-h-screen items-center justify-center p-4"
      style={{
        background: "radial-gradient(circle at center, #1e1b4b 0%, #0a0a0f 100%)",
      }}
    >
      <div
        className="w-full max-w-md rounded-3xl p-8 glass-strong animate-fade-in"
        style={{ boxShadow: "var(--shadow-card)" }}
      >
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div
            className="w-16 h-16 rounded-2xl flex items-center justify-center text-3xl font-bold mb-4 glow"
            style={{ background: "var(--gradient-primary)" }}
          >
            U
          </div>
          <h1 className="text-3xl font-extrabold gradient-text">Uday AI</h1>
          <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
            Sign in to your Personal AI OS
          </p>
        </div>

        {error && (
          <div
            className="mb-6 p-4 rounded-xl text-sm border flex items-center gap-2"
            style={{
              background: "rgba(239, 68, 68, 0.1)",
              borderColor: "var(--error)",
              color: "var(--error)",
            }}
          >
            ⚠️ {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-2">
            <label className="text-sm font-semibold" style={{ color: "var(--text-secondary)" }}>
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              className="w-full rounded-xl px-4 py-3 text-sm outline-none transition-all duration-200"
              style={{
                background: "var(--bg-tertiary)",
                border: "1px solid var(--border-color)",
                color: "var(--text-primary)",
              }}
              onFocus={(e) => {
                e.target.style.borderColor = "var(--accent-primary)";
              }}
              onBlur={(e) => {
                e.target.style.borderColor = "var(--border-color)";
              }}
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-semibold" style={{ color: "var(--text-secondary)" }}>
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              className="w-full rounded-xl px-4 py-3 text-sm outline-none transition-all duration-200"
              style={{
                background: "var(--bg-tertiary)",
                border: "1px solid var(--border-color)",
                color: "var(--text-primary)",
              }}
              onFocus={(e) => {
                e.target.style.borderColor = "var(--accent-primary)";
              }}
              onBlur={(e) => {
                e.target.style.borderColor = "var(--border-color)";
              }}
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3.5 mt-2 rounded-xl text-sm font-bold text-white transition-all duration-200 hover:scale-[1.02]"
            style={{
              background: "var(--gradient-primary)",
              boxShadow: "var(--shadow-glow)",
              cursor: isLoading ? "not-allowed" : "pointer",
              opacity: isLoading ? 0.7 : 1,
            }}
          >
            {isLoading ? "Signing In..." : "Sign In"}
          </button>
        </form>

        <p className="text-sm text-center mt-8" style={{ color: "var(--text-muted)" }}>
          Don&apos;t have an account?{" "}
          <Link href="/register" className="font-semibold" style={{ color: "var(--accent-primary)" }}>
            Create Account
          </Link>
        </p>
      </div>
    </div>
  );
}
