"use client";

/**
 * Nidhi AI OS — Resume Page
 *
 * ATS analysis, improvement, cover letter, LinkedIn summary, portfolio generation.
 */

import { useState, useEffect } from "react";
import Sidebar from "@/components/dashboard/Sidebar";
import api from "@/lib/api";
import useAuth from "@/hooks/useAuth";

type Tab = "analyze" | "improve" | "cover-letter" | "linkedin" | "generate";

function ATSScoreRing({ score }: { score: number }) {
  const radius = 40;
  const circumference = 2 * Math.PI * radius;
  const dashOffset = circumference - (score / 100) * circumference;
  const color =
    score >= 80 ? "#10b981" :
    score >= 60 ? "#f59e0b" :
    score >= 40 ? "#7c6bff" : "#f87171";

  return (
    <div className="flex flex-col items-center gap-2">
      <svg width="100" height="100" viewBox="0 0 100 100">
        {/* Background ring */}
        <circle cx="50" cy="50" r={radius} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="10" />
        {/* Score ring */}
        <circle
          cx="50" cy="50" r={radius}
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          strokeLinecap="round"
          transform="rotate(-90 50 50)"
          style={{ transition: "stroke-dashoffset 1s ease" }}
        />
        {/* Score text */}
        <text x="50" y="50" textAnchor="middle" dy="5" fill={color} fontSize="20" fontWeight="bold">
          {score}
        </text>
        <text x="50" y="65" textAnchor="middle" fill="rgba(255,255,255,0.4)" fontSize="8">
          ATS Score
        </text>
      </svg>
      <p className="text-xs font-medium" style={{ color }}>
        {score >= 80 ? "Excellent" : score >= 60 ? "Good" : score >= 40 ? "Average" : "Needs Work"}
      </p>
    </div>
  );
}

export default function ResumePage() {
  useAuth();
  const [activeTab, setActiveTab] = useState<Tab>("analyze");
  const [resumeText, setResumeText]   = useState("");
  const [targetRole, setTargetRole]   = useState("AI/ML Engineer");
  const [jd, setJd]                   = useState("");
  const [companyName, setCompanyName] = useState("");
  const [loading, setLoading]         = useState(false);
  const [result, setResult]           = useState<any>(null);
  const [outputText, setOutputText]   = useState("");
  const [storedResumeHint, setStoredResumeHint] = useState(false);

  // Check if profile has resume stored
  useEffect(() => {
    (api as any).getProfile?.().then((p: any) => {
      if (p?.resume_text) {
        setStoredResumeHint(true);
        setResumeText(p.resume_text);
      }
      if (p?.target_roles?.length) setTargetRole(p.target_roles[0]);
    }).catch(() => {});
  }, []);

  const handleAnalyze = async () => {
    if (!resumeText.trim()) return;
    setLoading(true); setResult(null);
    try {
      const res = await (api as any).analyzeResume?.({ resume_text: resumeText, target_role: targetRole });
      setResult(res);
    } catch (e: any) {
      setResult({ error: e.message });
    } finally {
      setLoading(false);
    }
  };

  const handleImprove = async () => {
    if (!resumeText.trim()) return;
    setLoading(true); setOutputText("");
    try {
      const res = await (api as any).improveResume?.({ resume_text: resumeText, target_role: targetRole, job_description: jd || null });
      setOutputText(res?.improved_resume || "No result");
    } catch (e: any) {
      setOutputText(`Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCoverLetter = async () => {
    if (!jd.trim()) return;
    setLoading(true); setOutputText("");
    try {
      const res = await (api as any).generateCoverLetter?.({ job_description: jd, company_name: companyName });
      setOutputText(res?.cover_letter || "No result");
    } catch (e: any) {
      setOutputText(`Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleLinkedIn = async () => {
    setLoading(true); setOutputText("");
    try {
      const res = await (api as any).generateLinkedIn?.({});
      setOutputText(res?.linkedin_summary || "No result");
    } catch (e: any) {
      setOutputText(`Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateResume = async () => {
    setLoading(true); setOutputText("");
    try {
      const res = await (api as any).generateATSResume?.();
      setOutputText(res?.generated_resume || "No result");
    } catch (e: any) {
      setOutputText(`Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const TABS: { key: Tab; label: string; emoji: string }[] = [
    { key: "analyze",      label: "Analyze",       emoji: "📊" },
    { key: "improve",      label: "Improve",        emoji: "⬆️" },
    { key: "cover-letter", label: "Cover Letter",   emoji: "✉️" },
    { key: "linkedin",     label: "LinkedIn",       emoji: "🔗" },
    { key: "generate",     label: "Generate",       emoji: "✨" },
  ];

  return (
    <>
      <div className="aurora-bg" aria-hidden />
      <div className="flex min-h-screen" style={{ background: "var(--bg-primary)" }}>
        <Sidebar />
        <main className="flex-1 overflow-y-auto relative" style={{ marginLeft: "var(--sidebar-width)", zIndex: 1 }}>
          {/* Header */}
          <header
            className="sticky top-0 z-30 glass-strong px-8 py-5 flex items-center justify-between"
            style={{ borderBottom: "1px solid rgba(124,107,255,0.08)" }}
          >
            <div>
              <h1
                className="text-2xl font-bold"
                style={{ color: "var(--text-primary)", fontFamily: "var(--font-display)" }}
              >
                📄 Resume Coach
              </h1>
              <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                Nidhi analyzes, improves, and optimizes your resume for ATS
              </p>
            </div>
            {storedResumeHint && (
              <span
                className="text-xs px-3 py-1.5 rounded-full"
                style={{
                  background: "rgba(16,185,129,0.1)",
                  border: "1px solid rgba(16,185,129,0.2)",
                  color: "var(--success)",
                }}
              >
                ✅ Resume from Profile
              </span>
            )}
          </header>

          <div className="max-w-4xl mx-auto px-6 py-8 space-y-6">
            {/* Tabs */}
            <div className="flex gap-1.5 flex-wrap">
              {TABS.map((t) => (
                <button
                  key={t.key}
                  onClick={() => { setActiveTab(t.key); setResult(null); setOutputText(""); }}
                  className="px-4 py-2 rounded-xl text-sm font-medium transition-all"
                  style={{
                    background: activeTab === t.key ? "rgba(124,107,255,0.2)" : "rgba(17,17,40,0.5)",
                    border: `1px solid ${activeTab === t.key ? "rgba(124,107,255,0.5)" : "rgba(124,107,255,0.1)"}`,
                    color: activeTab === t.key ? "var(--text-primary)" : "var(--text-muted)",
                  }}
                >
                  {t.emoji} {t.label}
                </button>
              ))}
            </div>

            {/* Target Role (shared) */}
            {(activeTab === "analyze" || activeTab === "improve") && (
              <div className="flex gap-3 items-center">
                <label className="text-xs whitespace-nowrap" style={{ color: "var(--text-muted)" }}>
                  Target Role:
                </label>
                <input
                  type="text"
                  value={targetRole}
                  onChange={(e) => setTargetRole(e.target.value)}
                  className="flex-1 bg-transparent text-sm outline-none px-3 py-1.5 rounded-xl"
                  style={{
                    border: "1px solid rgba(124,107,255,0.2)",
                    color: "var(--text-primary)",
                  }}
                />
              </div>
            )}

            {/* Resume input (shared for analyze + improve) */}
            {(activeTab === "analyze" || activeTab === "improve") && (
              <div
                className="rounded-2xl overflow-hidden"
                style={{ border: "1px solid rgba(124,107,255,0.12)" }}
              >
                <div
                  className="px-4 py-2 flex items-center justify-between"
                  style={{ background: "rgba(124,107,255,0.06)", borderBottom: "1px solid rgba(124,107,255,0.08)" }}
                >
                  <span className="text-xs font-medium" style={{ color: "var(--text-muted)" }}>
                    📄 Your Resume
                  </span>
                  <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                    {resumeText.length} chars
                  </span>
                </div>
                <textarea
                  value={resumeText}
                  onChange={(e) => setResumeText(e.target.value)}
                  placeholder="Paste your resume here… (plain text or Markdown)"
                  className="w-full bg-transparent p-4 text-xs font-mono outline-none resize-y"
                  style={{ color: "var(--text-secondary)", minHeight: "240px" }}
                />
              </div>
            )}

            {/* Job description input (for improve + cover letter) */}
            {(activeTab === "improve" || activeTab === "cover-letter") && (
              <div>
                {activeTab === "cover-letter" && (
                  <input
                    type="text"
                    value={companyName}
                    onChange={(e) => setCompanyName(e.target.value)}
                    placeholder="Company name (optional)"
                    className="w-full bg-transparent text-sm outline-none px-3 py-2 rounded-xl mb-3"
                    style={{
                      border: "1px solid rgba(124,107,255,0.15)",
                      color: "var(--text-primary)",
                    }}
                  />
                )}
                <textarea
                  value={jd}
                  onChange={(e) => setJd(e.target.value)}
                  placeholder="Paste job description here (optional for improve, required for cover letter)"
                  className="w-full bg-transparent p-4 text-xs font-mono outline-none resize-y rounded-2xl"
                  style={{
                    border: "1px solid rgba(124,107,255,0.12)",
                    color: "var(--text-secondary)",
                    minHeight: "140px",
                  }}
                />
              </div>
            )}

            {/* Info for generate/linkedin */}
            {activeTab === "generate" && (
              <div
                className="rounded-2xl p-5 text-sm"
                style={{
                  background: "rgba(124,107,255,0.06)",
                  border: "1px solid rgba(124,107,255,0.12)",
                  color: "var(--text-muted)",
                }}
              >
                ✨ Nidhi will generate a complete ATS-optimized resume from your Profile data.
                Make sure your profile has your skills, projects, education, and target roles filled in.
              </div>
            )}
            {activeTab === "linkedin" && (
              <div
                className="rounded-2xl p-5 text-sm"
                style={{
                  background: "rgba(124,107,255,0.06)",
                  border: "1px solid rgba(124,107,255,0.12)",
                  color: "var(--text-muted)",
                }}
              >
                🔗 Nidhi will generate your LinkedIn About section from your Profile data.
                Go to Profile to add your skills, goals, and projects first.
              </div>
            )}

            {/* Action Button */}
            <button
              onClick={
                activeTab === "analyze" ? handleAnalyze :
                activeTab === "improve" ? handleImprove :
                activeTab === "cover-letter" ? handleCoverLetter :
                activeTab === "linkedin" ? handleLinkedIn :
                handleGenerateResume
              }
              disabled={loading}
              className="btn-nidhi w-full py-3"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="inline-block w-4 h-4 rounded-full animate-ping" style={{ background: "rgba(255,255,255,0.5)" }} />
                  Nidhi is working…
                </span>
              ) : (
                <>
                  {activeTab === "analyze" && "📊 Analyze Resume"}
                  {activeTab === "improve" && "⬆️ Improve Resume"}
                  {activeTab === "cover-letter" && "✉️ Generate Cover Letter"}
                  {activeTab === "linkedin" && "🔗 Generate LinkedIn Summary"}
                  {activeTab === "generate" && "✨ Generate ATS Resume"}
                </>
              )}
            </button>

            {/* Analysis Result */}
            {activeTab === "analyze" && result && !result.error && (
              <div className="space-y-4">
                {/* Score */}
                <div
                  className="rounded-2xl p-6 flex items-center gap-8"
                  style={{
                    background: "rgba(17,17,40,0.8)",
                    border: "1px solid rgba(124,107,255,0.12)",
                  }}
                >
                  <ATSScoreRing score={result.ats_score || 0} />
                  <div className="flex-1">
                    <p className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>
                      {result.verdict}
                    </p>
                    <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>
                      {result.summary}
                    </p>
                    <p className="text-xs mt-2" style={{ color: "var(--text-muted)" }}>
                      Shortlist probability: <span style={{ color: "var(--accent-tertiary)" }}>{result.estimated_shortlist_probability}</span>
                    </p>
                  </div>
                </div>

                {/* Strengths + Weaknesses */}
                <div className="grid grid-cols-2 gap-4">
                  <div
                    className="rounded-2xl p-4"
                    style={{ background: "rgba(16,185,129,0.05)", border: "1px solid rgba(16,185,129,0.15)" }}
                  >
                    <p className="text-xs font-bold mb-2" style={{ color: "var(--success)" }}>✅ Strengths</p>
                    <ul className="space-y-1">
                      {(result.strengths || []).map((s: string, i: number) => (
                        <li key={i} className="text-xs" style={{ color: "var(--text-secondary)" }}>• {s}</li>
                      ))}
                    </ul>
                  </div>
                  <div
                    className="rounded-2xl p-4"
                    style={{ background: "rgba(248,113,113,0.05)", border: "1px solid rgba(248,113,113,0.15)" }}
                  >
                    <p className="text-xs font-bold mb-2" style={{ color: "#f87171" }}>⚠️ Weaknesses</p>
                    <ul className="space-y-1">
                      {(result.weaknesses || []).map((w: string, i: number) => (
                        <li key={i} className="text-xs" style={{ color: "var(--text-secondary)" }}>• {w}</li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* Improvements */}
                {result.improvements?.length > 0 && (
                  <div
                    className="rounded-2xl p-4 space-y-3"
                    style={{ background: "rgba(17,17,40,0.8)", border: "1px solid rgba(124,107,255,0.12)" }}
                  >
                    <p className="text-xs font-bold" style={{ color: "var(--accent-tertiary)" }}>
                      💡 Improvement Suggestions
                    </p>
                    {result.improvements.map((imp: any, i: number) => (
                      <div
                        key={i}
                        className="flex gap-3 p-3 rounded-xl"
                        style={{
                          background: imp.priority === "high" ? "rgba(124,107,255,0.08)" : "rgba(255,255,255,0.02)",
                          border: "1px solid rgba(124,107,255,0.08)",
                        }}
                      >
                        <span className="text-xs px-1.5 py-0.5 rounded h-fit flex-shrink-0" style={{
                          background: imp.priority === "high" ? "rgba(124,107,255,0.2)" : "rgba(245,158,11,0.15)",
                          color: imp.priority === "high" ? "var(--accent-tertiary)" : "#f59e0b",
                        }}>
                          {imp.priority}
                        </span>
                        <div>
                          <p className="text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>
                            {imp.section}: {imp.issue}
                          </p>
                          <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                            → {imp.fix}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Missing keywords */}
                {result.keyword_density?.missing_high_value?.length > 0 && (
                  <div
                    className="rounded-2xl p-4"
                    style={{ background: "rgba(17,17,40,0.8)", border: "1px solid rgba(124,107,255,0.12)" }}
                  >
                    <p className="text-xs font-bold mb-2" style={{ color: "var(--accent-tertiary)" }}>
                      🔑 Missing High-Value Keywords
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {result.keyword_density.missing_high_value.map((kw: string) => (
                        <span
                          key={kw}
                          className="text-xs px-2 py-0.5 rounded-full"
                          style={{
                            background: "rgba(248,113,113,0.1)",
                            border: "1px solid rgba(248,113,113,0.2)",
                            color: "#f87171",
                          }}
                        >
                          {kw}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Text output (improve, cover letter, linkedin, generate) */}
            {outputText && (
              <div
                className="rounded-2xl overflow-hidden"
                style={{ border: "1px solid rgba(124,107,255,0.15)" }}
              >
                <div
                  className="px-4 py-2.5 flex items-center justify-between"
                  style={{ background: "rgba(124,107,255,0.08)", borderBottom: "1px solid rgba(124,107,255,0.1)" }}
                >
                  <span className="text-xs font-semibold" style={{ color: "var(--accent-tertiary)" }}>
                    ✦ Nidhi&apos;s Output
                  </span>
                  <button
                    onClick={() => navigator.clipboard.writeText(outputText)}
                    className="text-xs px-2.5 py-1 rounded-full transition-all hover:scale-105"
                    style={{
                      background: "rgba(124,107,255,0.1)",
                      border: "1px solid rgba(124,107,255,0.2)",
                      color: "var(--text-secondary)",
                    }}
                  >
                    📋 Copy
                  </button>
                </div>
                <pre
                  className="p-5 text-xs leading-relaxed whitespace-pre-wrap overflow-auto"
                  style={{
                    background: "rgba(6,6,15,0.8)",
                    color: "var(--text-secondary)",
                    maxHeight: "500px",
                    fontFamily: "var(--font-mono)",
                  }}
                >
                  {outputText}
                </pre>
              </div>
            )}

            {result?.error && (
              <div
                className="rounded-2xl p-4 text-sm"
                style={{
                  background: "rgba(248,113,113,0.08)",
                  border: "1px solid rgba(248,113,113,0.2)",
                  color: "#f87171",
                }}
              >
                ⚠️ {result.error}
              </div>
            )}
          </div>
        </main>
      </div>
    </>
  );
}
