"use client";

/**
 * Nidhi — Register Page
 *
 * Premium glassmorphic registration screen.
 */

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import api from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [nickname, setNickname] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (api.getToken()) {
      router.push("/");
    }
  }, [router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !name || !password) {
      setError("Please fill in all required fields");
      return;
    }

    setError("");
    setIsLoading(true);

    try {
      await api.register({
        email,
        name,
        password,
        nickname: nickname || undefined,
      });
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create account");
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
        <div className="flex flex-col items-center mb-6">
          <div
            className="w-14 h-14 rounded-2xl flex items-center justify-center text-3xl font-bold mb-3 glow"
            style={{ background: "var(--gradient-primary)" }}
          >
            U
          </div>
          <h1 className="text-3xl font-extrabold gradient-text">Nidhi</h1>
          <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
            Create your Personal AI OS account
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

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>
              Full Name *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="John Doe"
              required
              className="w-full rounded-xl px-4 py-2.5 text-sm outline-none transition-all duration-200"
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

          <div className="space-y-1.5">
            <label className="text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>
              Nickname (How Nidhi addresses you)
            </label>
            <input
              type="text"
              value={nickname}
              onChange={(e) => setNickname(e.target.value)}
              placeholder="e.g. Master"
              className="w-full rounded-xl px-4 py-2.5 text-sm outline-none transition-all duration-200"
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

          <div className="space-y-1.5">
            <label className="text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>
              Email Address *
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              className="w-full rounded-xl px-4 py-2.5 text-sm outline-none transition-all duration-200"
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

          <div className="space-y-1.5">
            <label className="text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>
              Password *
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              className="w-full rounded-xl px-4 py-2.5 text-sm outline-none transition-all duration-200"
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
            className="w-full py-3 mt-2 rounded-xl text-sm font-bold text-white transition-all duration-200 hover:scale-[1.02]"
            style={{
              background: "var(--gradient-primary)",
              boxShadow: "var(--shadow-glow)",
              cursor: isLoading ? "not-allowed" : "pointer",
              opacity: isLoading ? 0.7 : 1,
            }}
          >
            {isLoading ? "Creating Account..." : "Create Account"}
          </button>
        </form>

        <p className="text-sm text-center mt-6" style={{ color: "var(--text-muted)" }}>
          Already have an account?{" "}
          <Link href="/login" className="font-semibold" style={{ color: "var(--accent-primary)" }}>
            Sign In
          </Link>
        </p>
      </div>
    </div>
  );
}
