"use client";

/**
 * Nidhi AI OS — Profile Page
 *
 * Full user profile editor: personal, career, skills, social, preferences.
 * Nidhi uses this to personalize every interaction.
 */

import { useState, useEffect, useRef } from "react";
import Sidebar from "@/components/dashboard/Sidebar";
import api from "@/lib/api";
import useAuth from "@/hooks/useAuth";

type ProfileTab = "personal" | "career" | "skills" | "projects" | "social" | "prefs";

const PROFILE_TABS: { key: ProfileTab; label: string; emoji: string }[] = [
  { key: "personal",  label: "Personal",     emoji: "👤" },
  { key: "career",    label: "Career",        emoji: "🎯" },
  { key: "skills",    label: "Skills",        emoji: "⚡" },
  { key: "projects",  label: "Projects",      emoji: "🚀" },
  { key: "social",    label: "Social",        emoji: "🔗" },
  { key: "prefs",     label: "Preferences",   emoji: "✨" },
];

const DEFAULT_SKILLS = ["Python", "React", "FastAPI", "LangChain", "Machine Learning", "TypeScript"];
const DEFAULT_DREAM_COMPANIES = ["Google", "OpenAI", "Microsoft", "Anthropic", "Meta AI"];

interface SkillChip {
  label: string;
  onRemove: () => void;
}

function SkillChip({ label, onRemove }: SkillChip) {
  return (
    <div
      className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm transition-all group"
      style={{
        background: "rgba(124,107,255,0.12)",
        border: "1px solid rgba(124,107,255,0.25)",
        color: "var(--text-secondary)",
      }}
    >
      {label}
      <button
        onClick={onRemove}
        className="w-4 h-4 rounded-full flex items-center justify-center text-xs opacity-50 group-hover:opacity-100 transition-opacity"
        style={{ background: "rgba(248,113,113,0.3)", color: "#f87171" }}
      >
        ×
      </button>
    </div>
  );
}

function InputField({
  label, value, onChange, placeholder = "", type = "text", fullWidth = true
}: {
  label: string; value: string | number | undefined; onChange: (v: string) => void;
  placeholder?: string; type?: string; fullWidth?: boolean;
}) {
  return (
    <div className={fullWidth ? "w-full" : ""}>
      <label className="block text-xs mb-1.5 font-medium" style={{ color: "var(--text-muted)" }}>
        {label}
      </label>
      <input
        type={type}
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full bg-transparent outline-none text-sm px-3 py-2 rounded-xl"
        style={{
          border: "1px solid rgba(124,107,255,0.15)",
          color: "var(--text-primary)",
        }}
      />
    </div>
  );
}

export default function ProfilePage() {
  useAuth();
  const [activeTab, setActiveTab] = useState<ProfileTab>("personal");
  const [profile, setProfile]   = useState<any>({});
  const [loading, setLoading]   = useState(true);
  const [saving, setSaving]     = useState(false);
  const [saved, setSaved]       = useState(false);
  const [newSkill, setNewSkill] = useState("");
  const [newCompany, setNewCompany] = useState("");
  const [newRole, setNewRole]   = useState("");
  const skillInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    (api as any).getProfile?.()
      .then((p: any) => { setProfile(p || {}); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const update = (key: string, value: any) => {
    setProfile((prev: any) => ({ ...prev, [key]: value }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const updated = await (api as any).updateProfile?.(profile);
      setProfile(updated);
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch {}
    finally { setSaving(false); }
  };

  const addSkill = () => {
    if (!newSkill.trim()) return;
    const existing = profile.skills || [];
    if (!existing.includes(newSkill.trim())) {
      update("skills", [...existing, newSkill.trim()]);
    }
    setNewSkill("");
  };

  const removeSkill = (s: string) => {
    update("skills", (profile.skills || []).filter((x: string) => x !== s));
  };

  const addCompany = () => {
    if (!newCompany.trim()) return;
    const existing = profile.dream_companies || [];
    if (!existing.includes(newCompany.trim())) {
      update("dream_companies", [...existing, newCompany.trim()]);
    }
    setNewCompany("");
  };

  const addRole = () => {
    if (!newRole.trim()) return;
    const existing = profile.target_roles || [];
    if (!existing.includes(newRole.trim())) {
      update("target_roles", [...existing, newRole.trim()]);
    }
    setNewRole("");
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center" style={{ background: "var(--bg-primary)" }}>
        <div
          className="w-12 h-12 rounded-full"
          style={{ background: "linear-gradient(135deg, #7c6bff, #e879f9)", animation: "breathe 1.5s ease-in-out infinite" }}
        />
      </div>
    );
  }

  const cardStyle = {
    background: "rgba(17,17,40,0.8)",
    border: "1px solid rgba(124,107,255,0.10)",
    backdropFilter: "blur(16px)",
  };

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
                👤 My Profile
              </h1>
              <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                Everything Nidhi knows about you — keep it updated for better personalization
              </p>
            </div>
            <button
              onClick={handleSave}
              disabled={saving}
              className="btn-nidhi"
            >
              {saving ? "✦ Saving…" : saved ? "✅ Saved!" : "💾 Save Profile"}
            </button>
          </header>

          <div className="max-w-4xl mx-auto px-6 py-8 space-y-6">
            {/* Hero card */}
            <div className="rounded-2xl p-6 flex items-center gap-5" style={cardStyle}>
              <div
                className="w-20 h-20 rounded-2xl flex items-center justify-center text-3xl font-bold flex-shrink-0"
                style={{
                  background: "linear-gradient(135deg, rgba(124,107,255,0.3), rgba(232,121,249,0.3))",
                  border: "2px solid rgba(124,107,255,0.3)",
                  color: "var(--accent-tertiary)",
                }}
              >
                {profile.name?.[0]?.toUpperCase() || "?"}
              </div>
              <div className="flex-1">
                <h2 className="text-xl font-bold" style={{ color: "var(--text-primary)" }}>
                  {profile.name || "Your Name"}
                </h2>
                <p className="text-sm mt-0.5" style={{ color: "var(--text-muted)" }}>
                  {profile.current_role || "Add your role"} • {profile.location || "Add location"}
                </p>
                <p className="text-xs mt-1.5 line-clamp-2" style={{ color: "var(--text-muted)" }}>
                  {profile.bio || "Add a bio to let Nidhi know more about you…"}
                </p>
              </div>
              <div className="text-right flex flex-col gap-1">
                {profile.github_url && (
                  <a href={profile.github_url} target="_blank" rel="noopener noreferrer"
                    className="text-xs hover:underline" style={{ color: "var(--accent-primary)" }}>
                    GitHub ↗
                  </a>
                )}
                {profile.linkedin_url && (
                  <a href={profile.linkedin_url} target="_blank" rel="noopener noreferrer"
                    className="text-xs hover:underline" style={{ color: "var(--accent-primary)" }}>
                    LinkedIn ↗
                  </a>
                )}
              </div>
            </div>

            {/* Tabs */}
            <div className="flex gap-1 flex-wrap">
              {PROFILE_TABS.map((t) => (
                <button
                  key={t.key}
                  onClick={() => setActiveTab(t.key)}
                  className="px-4 py-2 rounded-xl text-sm font-medium transition-all"
                  style={{
                    background: activeTab === t.key ? "rgba(124,107,255,0.2)" : "rgba(17,17,40,0.5)",
                    border: `1px solid ${activeTab === t.key ? "rgba(124,107,255,0.5)" : "rgba(124,107,255,0.08)"}`,
                    color: activeTab === t.key ? "var(--text-primary)" : "var(--text-muted)",
                  }}
                >
                  {t.emoji} {t.label}
                </button>
              ))}
            </div>

            {/* Personal Tab */}
            {activeTab === "personal" && (
              <div className="rounded-2xl p-6 space-y-4" style={cardStyle}>
                <div className="grid grid-cols-2 gap-4">
                  <InputField label="Full Name" value={profile.name} onChange={(v) => update("name", v)} placeholder="Uday Rastogi" />
                  <InputField label="Nickname" value={profile.nickname} onChange={(v) => update("nickname", v)} placeholder="Uday" />
                  <InputField label="Age" value={profile.age} onChange={(v) => update("age", parseInt(v) || "")} placeholder="22" type="number" />
                  <InputField label="Location" value={profile.location} onChange={(v) => update("location", v)} placeholder="Lucknow, India" />
                  <InputField label="University" value={profile.university} onChange={(v) => update("university", v)} placeholder="Your university" />
                  <InputField label="Graduation Year" value={profile.graduation_year} onChange={(v) => update("graduation_year", parseInt(v) || "")} placeholder="2026" type="number" />
                  <InputField label="Education" value={profile.education} onChange={(v) => update("education", v)} placeholder="B.Tech Computer Science" />
                </div>
                <div>
                  <label className="block text-xs mb-1.5 font-medium" style={{ color: "var(--text-muted)" }}>Bio</label>
                  <textarea
                    value={profile.bio || ""}
                    onChange={(e) => update("bio", e.target.value)}
                    placeholder="Tell Nidhi about yourself…"
                    rows={3}
                    className="w-full bg-transparent text-sm px-3 py-2 rounded-xl outline-none resize-y"
                    style={{ border: "1px solid rgba(124,107,255,0.15)", color: "var(--text-primary)" }}
                  />
                </div>
              </div>
            )}

            {/* Career Tab */}
            {activeTab === "career" && (
              <div className="rounded-2xl p-6 space-y-5" style={cardStyle}>
                <div className="grid grid-cols-2 gap-4">
                  <InputField label="Current Role" value={profile.current_role} onChange={(v) => update("current_role", v)} placeholder="AI Engineer Intern" />
                  <InputField label="Experience (years)" value={profile.experience_years} onChange={(v) => update("experience_years", parseFloat(v) || "")} placeholder="1.5" type="number" />
                  <InputField label="Expected Salary" value={profile.expected_salary} onChange={(v) => update("expected_salary", v)} placeholder="₹8-12 LPA" />
                  <InputField label="Work Type Preference" value={profile.preferred_work_type} onChange={(v) => update("preferred_work_type", v)} placeholder="remote / hybrid / onsite" />
                  <InputField label="Notice Period" value={profile.notice_period} onChange={(v) => update("notice_period", v)} placeholder="Immediate / 30 days" />
                </div>

                {/* Target Roles */}
                <div>
                  <label className="block text-xs mb-2 font-medium" style={{ color: "var(--text-muted)" }}>
                    🎯 Target Roles
                  </label>
                  <div className="flex flex-wrap gap-2 mb-2">
                    {(profile.target_roles || []).map((r: string) => (
                      <SkillChip key={r} label={r} onRemove={() =>
                        update("target_roles", (profile.target_roles || []).filter((x: string) => x !== r))
                      } />
                    ))}
                  </div>
                  <div className="flex gap-2">
                    <input
                      value={newRole}
                      onChange={(e) => setNewRole(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && addRole()}
                      placeholder="Add target role…"
                      className="flex-1 bg-transparent text-xs px-3 py-1.5 rounded-xl outline-none"
                      style={{ border: "1px solid rgba(124,107,255,0.15)", color: "var(--text-primary)" }}
                    />
                    <button onClick={addRole} className="btn-nidhi text-xs px-3 py-1.5">+ Add</button>
                  </div>
                </div>

                {/* Dream Companies */}
                <div>
                  <label className="block text-xs mb-2 font-medium" style={{ color: "var(--text-muted)" }}>
                    🏢 Dream Companies
                  </label>
                  <div className="flex flex-wrap gap-2 mb-2">
                    {(profile.dream_companies || []).map((c: string) => (
                      <SkillChip key={c} label={c} onRemove={() =>
                        update("dream_companies", (profile.dream_companies || []).filter((x: string) => x !== c))
                      } />
                    ))}
                  </div>
                  <div className="flex gap-2">
                    <input
                      value={newCompany}
                      onChange={(e) => setNewCompany(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && addCompany()}
                      placeholder="Add dream company…"
                      className="flex-1 bg-transparent text-xs px-3 py-1.5 rounded-xl outline-none"
                      style={{ border: "1px solid rgba(124,107,255,0.15)", color: "var(--text-primary)" }}
                    />
                    <button onClick={addCompany} className="btn-nidhi text-xs px-3 py-1.5">+ Add</button>
                  </div>
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {DEFAULT_DREAM_COMPANIES
                      .filter((c) => !(profile.dream_companies || []).includes(c))
                      .map((c) => (
                        <button
                          key={c}
                          onClick={() => update("dream_companies", [...(profile.dream_companies || []), c])}
                          className="text-xs px-2 py-0.5 rounded-full hover:scale-105 transition-all"
                          style={{
                            background: "rgba(124,107,255,0.05)",
                            border: "1px solid rgba(124,107,255,0.1)",
                            color: "var(--text-muted)",
                          }}
                        >
                          + {c}
                        </button>
                      ))}
                  </div>
                </div>

                {/* Job hunt toggle */}
                <div className="flex items-center gap-3">
                  <label className="text-sm" style={{ color: "var(--text-secondary)" }}>
                    Actively looking for jobs?
                  </label>
                  <button
                    onClick={() => update("job_hunt_active", !profile.job_hunt_active)}
                    className="px-4 py-1.5 rounded-full text-xs font-medium transition-all"
                    style={{
                      background: profile.job_hunt_active ? "rgba(16,185,129,0.15)" : "rgba(124,107,255,0.08)",
                      border: `1px solid ${profile.job_hunt_active ? "rgba(16,185,129,0.3)" : "rgba(124,107,255,0.1)"}`,
                      color: profile.job_hunt_active ? "var(--success)" : "var(--text-muted)",
                    }}
                  >
                    {profile.job_hunt_active ? "✅ Yes, actively" : "😴 Not right now"}
                  </button>
                </div>
              </div>
            )}

            {/* Skills Tab */}
            {activeTab === "skills" && (
              <div className="rounded-2xl p-6 space-y-4" style={cardStyle}>
                <label className="block text-xs font-medium" style={{ color: "var(--text-muted)" }}>
                  Your Skills (click × to remove)
                </label>
                <div className="flex flex-wrap gap-2">
                  {(profile.skills || []).map((s: string) => (
                    <SkillChip key={s} label={s} onRemove={() => removeSkill(s)} />
                  ))}
                </div>
                <div className="flex gap-2">
                  <input
                    ref={skillInputRef}
                    value={newSkill}
                    onChange={(e) => setNewSkill(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && addSkill()}
                    placeholder="Type a skill and press Enter…"
                    className="flex-1 bg-transparent text-sm px-3 py-2 rounded-xl outline-none"
                    style={{ border: "1px solid rgba(124,107,255,0.15)", color: "var(--text-primary)" }}
                  />
                  <button onClick={addSkill} className="btn-nidhi text-xs px-4">+ Add</button>
                </div>
                <div>
                  <p className="text-xs mb-2" style={{ color: "var(--text-muted)" }}>Quick add:</p>
                  <div className="flex flex-wrap gap-1.5">
                    {DEFAULT_SKILLS
                      .filter((s) => !(profile.skills || []).includes(s))
                      .map((s) => (
                        <button
                          key={s}
                          onClick={() => update("skills", [...(profile.skills || []), s])}
                          className="text-xs px-2.5 py-1 rounded-full hover:scale-105 transition-all"
                          style={{
                            background: "rgba(124,107,255,0.05)",
                            border: "1px solid rgba(124,107,255,0.12)",
                            color: "var(--text-muted)",
                          }}
                        >
                          + {s}
                        </button>
                      ))}
                  </div>
                </div>
              </div>
            )}

            {/* Projects Tab */}
            {activeTab === "projects" && (
              <div className="rounded-2xl p-6 space-y-4" style={cardStyle}>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs font-medium" style={{ color: "var(--text-muted)" }}>
                    Your Projects
                  </label>
                  <button
                    onClick={() => update("current_projects", [...(profile.current_projects || []), { name: "", description: "", tech: [], url: "" }])}
                    className="btn-nidhi text-xs px-3 py-1.5"
                  >
                    + Add Project
                  </button>
                </div>
                {(profile.current_projects || []).length === 0 && (
                  <p className="text-sm text-center py-8" style={{ color: "var(--text-muted)" }}>
                    No projects yet. Add your projects to power the Resume and Portfolio generators!
                  </p>
                )}
                {(profile.current_projects || []).map((proj: any, i: number) => (
                  <div
                    key={i}
                    className="rounded-xl p-4 space-y-3"
                    style={{ background: "rgba(124,107,255,0.04)", border: "1px solid rgba(124,107,255,0.1)" }}
                  >
                    <div className="flex items-center gap-2">
                      <input
                        value={proj.name || ""}
                        onChange={(e) => {
                          const updated = [...(profile.current_projects || [])];
                          updated[i] = { ...updated[i], name: e.target.value };
                          update("current_projects", updated);
                        }}
                        placeholder="Project name"
                        className="flex-1 bg-transparent text-sm font-semibold outline-none px-2 py-1 rounded-lg"
                        style={{ color: "var(--text-primary)", border: "1px solid rgba(124,107,255,0.1)" }}
                      />
                      <button
                        onClick={() => {
                          const updated = (profile.current_projects || []).filter((_: any, j: number) => j !== i);
                          update("current_projects", updated);
                        }}
                        className="text-xs px-2 py-1 rounded-lg"
                        style={{ color: "#f87171", background: "rgba(248,113,113,0.1)" }}
                      >
                        Remove
                      </button>
                    </div>
                    <textarea
                      value={proj.description || ""}
                      onChange={(e) => {
                        const updated = [...(profile.current_projects || [])];
                        updated[i] = { ...updated[i], description: e.target.value };
                        update("current_projects", updated);
                      }}
                      placeholder="Describe what this project does…"
                      rows={2}
                      className="w-full bg-transparent text-xs outline-none resize-none px-2 py-1.5 rounded-lg"
                      style={{ color: "var(--text-secondary)", border: "1px solid rgba(124,107,255,0.08)" }}
                    />
                    <input
                      value={proj.url || ""}
                      onChange={(e) => {
                        const updated = [...(profile.current_projects || [])];
                        updated[i] = { ...updated[i], url: e.target.value };
                        update("current_projects", updated);
                      }}
                      placeholder="GitHub / Demo URL"
                      className="w-full bg-transparent text-xs outline-none px-2 py-1 rounded-lg"
                      style={{ color: "var(--text-muted)", border: "1px solid rgba(124,107,255,0.08)" }}
                    />
                  </div>
                ))}
              </div>
            )}

            {/* Social Tab */}
            {activeTab === "social" && (
              <div className="rounded-2xl p-6 space-y-4" style={cardStyle}>
                <InputField label="🐙 GitHub URL" value={profile.github_url} onChange={(v) => update("github_url", v)} placeholder="https://github.com/username" />
                <InputField label="💼 LinkedIn URL" value={profile.linkedin_url} onChange={(v) => update("linkedin_url", v)} placeholder="https://linkedin.com/in/username" />
                <InputField label="🌐 Portfolio URL" value={profile.portfolio_url} onChange={(v) => update("portfolio_url", v)} placeholder="https://yourportfolio.com" />
                <InputField label="🐦 Twitter URL" value={profile.twitter_url} onChange={(v) => update("twitter_url", v)} placeholder="https://twitter.com/username" />

                {/* Resume upload */}
                <div>
                  <label className="block text-xs mb-1.5 font-medium" style={{ color: "var(--text-muted)" }}>
                    📄 Resume (paste text or upload)
                  </label>
                  <textarea
                    value={profile.resume_text || ""}
                    onChange={(e) => update("resume_text", e.target.value)}
                    placeholder="Paste your resume in plain text format…"
                    rows={6}
                    className="w-full bg-transparent text-xs px-3 py-2 rounded-xl outline-none resize-y font-mono"
                    style={{ border: "1px solid rgba(124,107,255,0.15)", color: "var(--text-secondary)" }}
                  />
                  {profile.resume_ats_score != null && (
                    <p className="text-xs mt-1.5" style={{ color: "var(--text-muted)" }}>
                      Last ATS Score: <span style={{ color: "var(--accent-tertiary)" }}>{profile.resume_ats_score}/100</span>
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* Preferences Tab */}
            {activeTab === "prefs" && (
              <div className="rounded-2xl p-6 space-y-4" style={cardStyle}>
                <InputField label="🎵 Favorite Music" value={profile.favorite_music} onChange={(v) => update("favorite_music", v)} placeholder="Lofi, Bollywood, English Pop…" />

                <div>
                  <label className="block text-xs mb-2 font-medium" style={{ color: "var(--text-muted)" }}>
                    💻 Favorite Technologies
                  </label>
                  <div className="flex flex-wrap gap-2 mb-2">
                    {(profile.favorite_tech || []).map((t: string) => (
                      <SkillChip key={t} label={t} onRemove={() =>
                        update("favorite_tech", (profile.favorite_tech || []).filter((x: string) => x !== t))
                      } />
                    ))}
                  </div>
                  <input
                    placeholder="Type tech name and press Enter…"
                    className="w-full bg-transparent text-xs px-3 py-1.5 rounded-xl outline-none"
                    style={{ border: "1px solid rgba(124,107,255,0.15)", color: "var(--text-primary)" }}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        const val = (e.target as HTMLInputElement).value.trim();
                        if (val) {
                          update("favorite_tech", [...(profile.favorite_tech || []), val]);
                          (e.target as HTMLInputElement).value = "";
                        }
                      }
                    }}
                  />
                </div>

                <div>
                  <label className="block text-xs mb-2 font-medium" style={{ color: "var(--text-muted)" }}>
                    📚 Learning Goals
                  </label>
                  {(profile.learning_goals || []).map((g: any, i: number) => (
                    <div key={i} className="flex gap-2 mb-2 items-center">
                      <input
                        value={g.topic || ""}
                        onChange={(e) => {
                          const updated = [...(profile.learning_goals || [])];
                          updated[i] = { ...updated[i], topic: e.target.value };
                          update("learning_goals", updated);
                        }}
                        placeholder="e.g. Reinforcement Learning"
                        className="flex-1 bg-transparent text-xs px-3 py-1.5 rounded-xl outline-none"
                        style={{ border: "1px solid rgba(124,107,255,0.12)", color: "var(--text-primary)" }}
                      />
                      <select
                        value={g.status || "planned"}
                        onChange={(e) => {
                          const updated = [...(profile.learning_goals || [])];
                          updated[i] = { ...updated[i], status: e.target.value };
                          update("learning_goals", updated);
                        }}
                        className="text-xs px-2 py-1.5 rounded-xl outline-none"
                        style={{ background: "rgba(124,107,255,0.08)", border: "1px solid rgba(124,107,255,0.1)", color: "var(--text-muted)" }}
                      >
                        <option value="planned">Planned</option>
                        <option value="in-progress">In Progress</option>
                        <option value="completed">Completed</option>
                      </select>
                      <button
                        onClick={() => update("learning_goals", (profile.learning_goals || []).filter((_: any, j: number) => j !== i))}
                        className="text-xs" style={{ color: "#f87171" }}
                      >×</button>
                    </div>
                  ))}
                  <button
                    onClick={() => update("learning_goals", [...(profile.learning_goals || []), { topic: "", status: "planned" }])}
                    className="text-xs mt-1" style={{ color: "var(--accent-primary)" }}
                  >
                    + Add Learning Goal
                  </button>
                </div>
              </div>
            )}

            {/* Save bar */}
            <div className="pb-8">
              <button onClick={handleSave} disabled={saving} className="btn-nidhi w-full py-3">
                {saving ? "✦ Saving Profile…" : saved ? "✅ Profile Saved!" : "💾 Save All Changes"}
              </button>
            </div>
          </div>
        </main>
      </div>
    </>
  );
}
