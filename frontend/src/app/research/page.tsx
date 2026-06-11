"use client";

/**
 * Uday AI — Research Portal Page
 *
 * Dedicated research dashboard interface that triggers deep-dive web research requests
 * to the backend Research Agent and renders generated markdown reports.
 */

import { useState } from "react";
import Sidebar from "@/components/dashboard/Sidebar";
import useAuth from "@/hooks/useAuth";
import api from "@/lib/api";

export default function ResearchPage() {
  useAuth(); // Require authentication
  const [topic, setTopic] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState("");
  const [report, setReport] = useState("");

  const handleResearch = async (e: React.FormEvent) => {
    e.preventDefault();
    const query = topic.trim();
    if (!query || isLoading) return;

    setIsLoading(true);
    setReport("");
    setStatus("Initializing Research Agent...");

    // Simulate progress milestones
    const progressMilestones = [
      { delay: 1500, status: "🌐 Querying multi-source search indexes..." },
      { delay: 4000, status: "📄 Reading document snippets and verifying facts..." },
      { delay: 7000, status: "✏️ Compiling comprehensive markdown report..." },
    ];

    progressMilestones.forEach((m) => {
      setTimeout(() => {
        if (isLoading) {
          setStatus(m.status);
        }
      }, m.delay);
    });

    try {
      // Send the query formatted as a research command
      const response = (await api.sendMessage(`Research: ${query}`)) as {
        message: { content: string };
      };

      setReport(response.message.content);
    } catch (err) {
      setReport(
        `❌ Research failed: ${err instanceof Error ? err.message : "An unknown error occurred"}`
      );
    } finally {
      setIsLoading(false);
      setStatus("");
    }
  };

  return (
    <div className="flex min-h-screen" style={{ background: "var(--bg-primary)" }}>
      <Sidebar />
      <main className="flex-1 font-sans" style={{ marginLeft: "var(--sidebar-width)" }}>
        <header className="sticky top-0 z-30 glass-strong px-8 py-5 flex items-center justify-between" style={{ borderBottom: "1px solid var(--border-color)" }}>
          <div>
            <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>🔍 Research Portal</h1>
            <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>Web search, multi-source synthesis, and facts verification</p>
          </div>
        </header>

        <div className="px-8 py-6 space-y-6 max-w-4xl animate-fade-in pb-20">
          {/* Research Input Form */}
          <div className="rounded-2xl p-6" style={{ background: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
            <h3 className="text-sm font-semibold mb-3" style={{ color: "var(--text-primary)" }}>Start a Deep Research Task</h3>
            <form onSubmit={handleResearch} className="flex gap-3">
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="What topic would you like Uday AI to research? (e.g. 'Compare Rust vs Python for AI agentic systems')"
                required
                disabled={isLoading}
                className="flex-1 rounded-xl px-5 py-3 text-sm outline-none transition-all duration-200"
                style={{
                  background: "var(--bg-tertiary)",
                  border: "1px solid var(--border-color)",
                  color: "var(--text-primary)",
                }}
                onFocus={(e) => { e.target.style.borderColor = "var(--accent-primary)"; }}
                onBlur={(e) => { e.target.style.borderColor = "var(--border-color)"; }}
              />
              <button
                type="submit"
                disabled={!topic.trim() || isLoading}
                className="px-6 py-3 rounded-xl text-sm font-semibold text-white hover:scale-105 transition-all"
                style={{
                  background: "var(--gradient-primary)",
                  opacity: topic.trim() && !isLoading ? 1 : 0.5,
                  cursor: topic.trim() && !isLoading ? "pointer" : "not-allowed",
                  boxShadow: topic.trim() && !isLoading ? "var(--shadow-glow)" : "none",
                }}
              >
                {isLoading ? "🔍 Researching..." : "Research"}
              </button>
            </form>
            <div className="flex flex-wrap gap-2 mt-4">
              {[
                "AI Engineer Jobs in India",
                "Latest React Features in 2026",
                "Self-Hosted LLM Security Guidelines",
              ].map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => !isLoading && setTopic(s)}
                  className="px-3 py-1.5 rounded-lg text-xs hover:text-[var(--text-primary)] transition-colors"
                  style={{ background: "var(--bg-tertiary)", color: "var(--text-muted)" }}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          {/* Research Progress / Report Output */}
          {isLoading && (
            <div className="rounded-2xl p-8 text-center space-y-4 flex flex-col items-center border animate-pulse-glow" style={{ background: "var(--bg-card)", borderColor: "var(--border-color)" }}>
              <div className="w-12 h-12 rounded-full border-4 border-t-[var(--accent-primary)] animate-spin border-[var(--border-color)]" />
              <h3 className="font-bold text-sm" style={{ color: "var(--text-primary)" }}>{status || "Agent executing plan..."}</h3>
              <p className="text-xs max-w-sm" style={{ color: "var(--text-muted)" }}>
                Deep research queries multiple search indexes and synthesizes pages. This can take up to 20-30 seconds.
              </p>
            </div>
          )}

          {!isLoading && report && (
            <div className="rounded-2xl p-6 space-y-4 border animate-fade-in" style={{ background: "var(--bg-card)", borderColor: "var(--border-color)" }}>
              <h3 className="text-base font-bold gradient-text">📋 Generated Research Report</h3>
              <div className="prose text-sm leading-relaxed whitespace-pre-wrap py-4" style={{ color: "var(--text-primary)" }}>
                {report}
              </div>
            </div>
          )}

          {!isLoading && !report && (
            <div className="flex flex-col items-center justify-center py-20 rounded-2xl border" style={{ background: "var(--bg-card)", borderColor: "var(--border-color)" }}>
              <span className="text-5xl mb-4">🔍</span>
              <h3 className="text-lg font-semibold mb-2" style={{ color: "var(--text-primary)" }}>No research history</h3>
              <p className="text-sm text-center max-w-md" style={{ color: "var(--text-secondary)" }}>
                Enter a topic above to initiate deep research. The Research Agent will compile web summaries, verify details, and output a structured report.
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
