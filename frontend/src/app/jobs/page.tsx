"use client";

/**
 * Nidhi AI OS — Jobs Page
 *
 * Job search, save, match resume, track applications.
 * Powered by Job Agent + Brave Search.
 */

import { useState, useEffect } from "react";
import Sidebar from "@/components/dashboard/Sidebar";
import CommandBar from "@/components/CommandBar";
import api from "@/lib/api";
import useAuth from "@/hooks/useAuth";

const JOB_TYPES = [
  { key: "all", label: "All Jobs", emoji: "💼" },
  { key: "internship", label: "Internships", emoji: "🎓" },
  { key: "full-time", label: "Full-time", emoji: "🏢" },
  { key: "remote", label: "Remote", emoji: "🌐" },
  { key: "freelance", label: "Freelance", emoji: "💻" },
];

const ROLE_PRESETS = [
  "AI Engineer", "ML Engineer", "Full Stack Developer",
  "LangChain Developer", "GenAI Engineer", "Python Developer",
  "Backend Developer", "Data Scientist",
];

const STATUS_COLORS: Record<string, string> = {
  saved:      "rgba(124, 107, 255, 0.2)",
  applied:    "rgba(59, 130, 246, 0.2)",
  screening:  "rgba(245, 158, 11, 0.2)",
  interview:  "rgba(16, 185, 129, 0.2)",
  offer:      "rgba(236, 72, 153, 0.2)",
  rejected:   "rgba(248, 113, 113, 0.1)",
  accepted:   "rgba(34, 211, 168, 0.25)",
};

const PIPELINE_STAGES = ["saved", "applied", "screening", "interview", "offer", "accepted"];

interface JobCardProps {
  job: any;
  onSave?: (job: any) => void;
  onUpdateStatus?: (jobId: string, status: string) => void;
  isSaved?: boolean;
}

function JobCard({ job, onSave, onUpdateStatus, isSaved }: JobCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [generatingCL, setGeneratingCL] = useState(false);
  const [coverLetter, setCoverLetter] = useState<string | null>(null);

  const matchScore = job.match_score;
  const matchColor =
    matchScore >= 80 ? "var(--success)" :
    matchScore >= 60 ? "var(--warning)" :
    matchScore >= 40 ? "var(--accent-tertiary)" :
    "var(--text-muted)";

  const handleGenerateCL = async () => {
    if (!job.id) return;
    setGeneratingCL(true);
    try {
      const res = await (api as any).generateJobCoverLetter(job.id);
      setCoverLetter(res.cover_letter);
    } catch {
      setCoverLetter("Could not generate cover letter. Please try again.");
    } finally {
      setGeneratingCL(false);
    }
  };

  return (
    <div
      className="rounded-2xl p-5 transition-all duration-200"
      style={{
        background: "rgba(17, 17, 40, 0.8)",
        border: `1px solid ${isSaved && job.application ? STATUS_COLORS[job.application.status] || "rgba(124,107,255,0.12)" : "rgba(124,107,255,0.12)"}`,
        backdropFilter: "blur(16px)",
      }}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3 flex-1 min-w-0">
          {/* Company avatar */}
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center text-lg flex-shrink-0 font-bold"
            style={{
              background: "linear-gradient(135deg, rgba(124,107,255,0.2), rgba(232,121,249,0.2))",
              border: "1px solid rgba(124,107,255,0.2)",
              color: "var(--accent-tertiary)",
            }}
          >
            {job.company?.[0]?.toUpperCase() || "?"}
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-sm truncate" style={{ color: "var(--text-primary)" }}>
              {job.title}
            </p>
            <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
              {job.company} · {job.location || "Location N/A"}
            </p>
          </div>
        </div>

        {/* Match score badge */}
        {matchScore != null && (
          <div
            className="px-2.5 py-1 rounded-full text-xs font-bold flex-shrink-0"
            style={{
              background: `${matchColor}22`,
              border: `1px solid ${matchColor}44`,
              color: matchColor,
            }}
          >
            {Math.round(matchScore)}% match
          </div>
        )}
      </div>

      {/* Tags */}
      {job.tags && job.tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-3">
          {job.tags.slice(0, 5).map((tag: string) => (
            <span
              key={tag}
              className="text-xs px-2 py-0.5 rounded-full"
              style={{
                background: "rgba(124,107,255,0.08)",
                border: "1px solid rgba(124,107,255,0.15)",
                color: "var(--text-muted)",
              }}
            >
              {tag}
            </span>
          ))}
          {job.salary_range && (
            <span
              className="text-xs px-2 py-0.5 rounded-full"
              style={{
                background: "rgba(16,185,129,0.1)",
                border: "1px solid rgba(16,185,129,0.2)",
                color: "var(--success)",
              }}
            >
              💰 {job.salary_range}
            </span>
          )}
        </div>
      )}

      {/* Application status (if saved) */}
      {isSaved && job.application && (
        <div className="mt-3 flex items-center gap-2">
          <span className="text-xs" style={{ color: "var(--text-muted)" }}>Status:</span>
          <select
            className="text-xs px-2 py-1 rounded-lg border-0 outline-none cursor-pointer"
            style={{
              background: STATUS_COLORS[job.application.status] || "rgba(124,107,255,0.1)",
              color: "var(--text-secondary)",
            }}
            value={job.application.status}
            onChange={(e) => onUpdateStatus?.(job.id, e.target.value)}
          >
            {PIPELINE_STAGES.map((s) => (
              <option key={s} value={s} style={{ background: "#0d0d1a" }}>
                {s.charAt(0).toUpperCase() + s.slice(1)}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Expand/collapse description */}
      {job.description && (
        <div className="mt-3">
          <p
            className={`text-xs leading-relaxed ${expanded ? "" : "line-clamp-2"}`}
            style={{ color: "var(--text-muted)" }}
          >
            {job.description}
          </p>
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs mt-1 transition-colors"
            style={{ color: "var(--accent-tertiary)" }}
          >
            {expanded ? "Show less" : "Show more"}
          </button>
        </div>
      )}

      {/* Cover letter (if generated) */}
      {coverLetter && (
        <div
          className="mt-3 p-3 rounded-xl text-xs leading-relaxed"
          style={{
            background: "rgba(124,107,255,0.06)",
            border: "1px solid rgba(124,107,255,0.15)",
            color: "var(--text-secondary)",
          }}
        >
          <p className="font-semibold mb-2" style={{ color: "var(--accent-tertiary)" }}>
            ✉️ Cover Letter
          </p>
          <pre className="whitespace-pre-wrap font-sans">{coverLetter}</pre>
          <button
            onClick={() => navigator.clipboard.writeText(coverLetter)}
            className="mt-2 text-xs"
            style={{ color: "var(--accent-primary)" }}
          >
            📋 Copy to Clipboard
          </button>
        </div>
      )}

      {/* Action buttons */}
      <div className="flex items-center gap-2 mt-4">
        {job.url && (
          <a
            href={job.url}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-ghost text-xs py-1.5 px-3"
          >
            🔗 View
          </a>
        )}
        {!isSaved && (
          <button
            onClick={() => onSave?.(job)}
            className="btn-nidhi text-xs py-1.5 px-3"
          >
            💾 Save
          </button>
        )}
        {isSaved && (
          <button
            onClick={handleGenerateCL}
            disabled={generatingCL}
            className="btn-nidhi text-xs py-1.5 px-3"
          >
            {generatingCL ? "✦ Generating…" : "✉️ Cover Letter"}
          </button>
        )}
        {isSaved && job.application?.status === "saved" && (
          <button
            onClick={() => onUpdateStatus?.(job.id, "applied")}
            className="text-xs px-3 py-1.5 rounded-full transition-all"
            style={{
              background: "rgba(59,130,246,0.1)",
              border: "1px solid rgba(59,130,246,0.3)",
              color: "#60a5fa",
            }}
          >
            ✅ Mark Applied
          </button>
        )}
      </div>
    </div>
  );
}

export default function JobsPage() {
  useAuth();
  const [query, setQuery]             = useState("");
  const [jobType, setJobType]         = useState("all");
  const [activeTab, setActiveTab]     = useState<"search" | "saved" | "pipeline">("search");
  const [searching, setSearching]     = useState(false);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [savedJobs, setSavedJobs]     = useState<any[]>([]);
  const [cmdOpen, setCmdOpen]         = useState(false);
  const [pipeline, setPipeline]       = useState<Record<string, any[]>>({});

  // Load saved jobs
  useEffect(() => {
    (api as any).getJobs?.().then((data: any) => {
      if (data?.jobs) {
        setSavedJobs(data.jobs);
        // Build pipeline
        const p: Record<string, any[]> = {};
        PIPELINE_STAGES.forEach((s) => (p[s] = []));
        data.jobs.forEach((j: any) => {
          const stage = j.application?.status || "saved";
          if (!p[stage]) p[stage] = [];
          p[stage].push(j);
        });
        setPipeline(p);
      }
    }).catch(() => {});
  }, []);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setSearching(true);
    setActiveTab("search");
    try {
      const res = await (api as any).searchJobs?.({ query, job_type: jobType, count: 12 });
      setSearchResults(res?.results || []);
    } catch {
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  const handleSaveJob = async (job: any) => {
    try {
      const saved = await (api as any).saveJob?.(job);
      setSavedJobs((prev) => [saved, ...prev]);
    } catch {}
  };

  const handleUpdateStatus = async (jobId: string, status: string) => {
    try {
      await (api as any).updateJobStatus?.(jobId, { status });
      setSavedJobs((prev) =>
        prev.map((j) =>
          j.id === jobId
            ? { ...j, application: { ...j.application, status } }
            : j
        )
      );
    } catch {}
  };

  // CTRL+K
  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") { e.preventDefault(); setCmdOpen(true); }
      if (e.key === "Escape") setCmdOpen(false);
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, []);

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
                💼 Jobs & Internships
              </h1>
              <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                Nidhi finds and tracks the best opportunities for you
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span
                className="px-3 py-1.5 rounded-full text-xs"
                style={{
                  background: "rgba(16,185,129,0.1)",
                  border: "1px solid rgba(16,185,129,0.2)",
                  color: "var(--success)",
                }}
              >
                {savedJobs.length} saved
              </span>
            </div>
          </header>

          <div className="max-w-5xl mx-auto px-6 py-8 space-y-6">
            {/* Search Bar */}
            <div
              className="rounded-2xl p-5"
              style={{
                background: "rgba(17,17,40,0.8)",
                border: "1px solid rgba(124,107,255,0.12)",
              }}
            >
              <div className="flex gap-3 mb-4">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                  placeholder="Search jobs… e.g. 'AI Engineer', 'React Developer', 'Python intern'"
                  className="flex-1 bg-transparent outline-none text-sm"
                  style={{
                    color: "var(--text-primary)",
                    borderBottom: "1px solid rgba(124,107,255,0.2)",
                    padding: "0.5rem 0",
                  }}
                />
                <button
                  onClick={handleSearch}
                  disabled={searching || !query.trim()}
                  className="btn-nidhi px-5 py-2"
                >
                  {searching ? "✦ Searching…" : "🔍 Search"}
                </button>
              </div>

              {/* Job type filters */}
              <div className="flex flex-wrap gap-2">
                {JOB_TYPES.map((t) => (
                  <button
                    key={t.key}
                    onClick={() => setJobType(t.key)}
                    className="px-3 py-1.5 rounded-full text-xs font-medium transition-all"
                    style={{
                      background: jobType === t.key ? "rgba(124,107,255,0.2)" : "transparent",
                      border: `1px solid ${jobType === t.key ? "rgba(124,107,255,0.5)" : "rgba(124,107,255,0.12)"}`,
                      color: jobType === t.key ? "var(--text-primary)" : "var(--text-muted)",
                    }}
                  >
                    {t.emoji} {t.label}
                  </button>
                ))}
              </div>

              {/* Quick role presets */}
              <div className="flex flex-wrap gap-1.5 mt-3">
                {ROLE_PRESETS.map((r) => (
                  <button
                    key={r}
                    onClick={() => setQuery(r)}
                    className="text-xs px-2.5 py-1 rounded-full transition-all hover:scale-105"
                    style={{
                      background: "rgba(124,107,255,0.06)",
                      border: "1px solid rgba(124,107,255,0.1)",
                      color: "var(--text-muted)",
                    }}
                  >
                    {r}
                  </button>
                ))}
              </div>
            </div>

            {/* Tabs */}
            <div className="flex gap-1">
              {["search", "saved", "pipeline"].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab as any)}
                  className="px-4 py-2 rounded-xl text-sm font-medium transition-all"
                  style={{
                    background: activeTab === tab ? "rgba(124,107,255,0.15)" : "transparent",
                    border: `1px solid ${activeTab === tab ? "rgba(124,107,255,0.4)" : "transparent"}`,
                    color: activeTab === tab ? "var(--text-primary)" : "var(--text-muted)",
                  }}
                >
                  {tab === "search" && `🔍 Results (${searchResults.length})`}
                  {tab === "saved" && `💾 Saved (${savedJobs.length})`}
                  {tab === "pipeline" && "📊 Pipeline"}
                </button>
              ))}
            </div>

            {/* Content */}
            {activeTab === "search" && (
              <div>
                {searching ? (
                  <div className="flex flex-col items-center py-16 gap-3">
                    <div
                      className="w-12 h-12 rounded-full"
                      style={{
                        background: "linear-gradient(135deg, #7c6bff, #e879f9)",
                        animation: "breathe 1.5s ease-in-out infinite",
                      }}
                    />
                    <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                      Nidhi is searching for opportunities…
                    </p>
                  </div>
                ) : searchResults.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {searchResults.map((job, i) => (
                      <JobCard key={i} job={job} onSave={handleSaveJob} isSaved={false} />
                    ))}
                  </div>
                ) : (
                  <div className="flex flex-col items-center py-16 gap-3">
                    <span className="text-4xl">🔍</span>
                    <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                      Search for jobs above, Uday. Nidhi will find the best ones for you!
                    </p>
                  </div>
                )}
              </div>
            )}

            {activeTab === "saved" && (
              <div>
                {savedJobs.length === 0 ? (
                  <div className="flex flex-col items-center py-16 gap-3">
                    <span className="text-4xl">💼</span>
                    <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                      No saved jobs yet. Search and save jobs you&apos;re interested in!
                    </p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {savedJobs.map((job) => (
                      <JobCard
                        key={job.id}
                        job={job}
                        isSaved
                        onUpdateStatus={handleUpdateStatus}
                      />
                    ))}
                  </div>
                )}
              </div>
            )}

            {activeTab === "pipeline" && (
              <div className="space-y-4">
                {PIPELINE_STAGES.filter((s) => s !== "rejected").map((stage) => {
                  const jobs = pipeline[stage] || [];
                  return (
                    <div key={stage}>
                      <div className="flex items-center gap-2 mb-2">
                        <span
                          className="w-2 h-2 rounded-full"
                          style={{ background: STATUS_COLORS[stage]?.replace("0.2", "0.8") || "var(--accent-primary)" }}
                        />
                        <h3 className="text-sm font-semibold capitalize" style={{ color: "var(--text-secondary)" }}>
                          {stage} ({jobs.length})
                        </h3>
                      </div>
                      {jobs.length > 0 ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 ml-4">
                          {jobs.map((job) => (
                            <JobCard key={job.id} job={job} isSaved onUpdateStatus={handleUpdateStatus} />
                          ))}
                        </div>
                      ) : (
                        <p className="text-xs ml-4" style={{ color: "var(--text-muted)" }}>
                          No jobs in this stage
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </main>
      </div>
      <CommandBar isOpen={cmdOpen} onClose={() => setCmdOpen(false)} />
    </>
  );
}
