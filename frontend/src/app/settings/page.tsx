"use client";

/**
 * Uday AI — Settings Page
 *
 * Full-featured profile and preferences editor with integrations toggling.
 */

import { useState, useEffect } from "react";
import Sidebar from "@/components/dashboard/Sidebar";
import useAuth from "@/hooks/useAuth";
import api from "@/lib/api";

export default function SettingsPage() {
  const { user } = useAuth(); // Require authentication

  // Form state
  const [name, setName] = useState("");
  const [nickname, setNickname] = useState("");
  const [email, setEmail] = useState("");
  const [provider, setProvider] = useState("ollama");
  const [model, setModel] = useState("llama3:8b");
  const [temperature, setTemperature] = useState(0.7);

  // Integration states (simulated / stored in preference)
  const [googleCalendarConnected, setGoogleCalendarConnected] = useState(false);
  const [gmailConnected, setGmailConnected] = useState(false);
  const [githubConnected, setGithubConnected] = useState(false);

  const [isSaving, setIsSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => {
    if (user) {
      setName(user.name || "");
      setNickname(user.nickname || "");
      setEmail(user.email || "");

      // Load preferences
      const prefs = (user.preferences as Record<string, any>) || {};
      setProvider(prefs.llm_provider || "ollama");
      setModel(prefs.llm_model || "llama3:8b");
      setTemperature(prefs.llm_temperature ?? 0.7);

      setGoogleCalendarConnected(!!prefs.google_calendar_connected);
      setGmailConnected(!!prefs.gmail_connected);
      setGithubConnected(!!prefs.github_connected);
    }
  }, [user]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setSuccessMsg("");
    setErrorMsg("");

    const preferences = {
      llm_provider: provider,
      llm_model: model,
      llm_temperature: Number(temperature),
      google_calendar_connected: googleCalendarConnected,
      gmail_connected: gmailConnected,
      github_connected: githubConnected,
    };

    try {
      await api.updateProfile({
        name,
        nickname: nickname || null,
        preferences,
      });
      setSuccessMsg("Settings saved successfully!");
      // Automatically clear toast after 3s
      setTimeout(() => setSuccessMsg(""), 3000);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Failed to update profile settings");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="flex min-h-screen" style={{ background: "var(--bg-primary)" }}>
      <Sidebar />
      <main className="flex-1" style={{ marginLeft: "var(--sidebar-width)" }}>
        <header className="sticky top-0 z-30 glass-strong px-8 py-5 flex items-center justify-between" style={{ borderBottom: "1px solid var(--border-color)" }}>
          <div>
            <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>🔧 Settings & Config</h1>
            <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>Configure profile details, integrations, and default LLM</p>
          </div>
        </header>

        <form onSubmit={handleSave} className="px-8 py-6 space-y-6 max-w-3xl animate-fade-in pb-20">
          {successMsg && (
            <div className="p-4 rounded-xl text-sm border bg-[rgba(16,185,129,0.1)] border-[var(--success)] text-[var(--success)]">
              ✓ {successMsg}
            </div>
          )}

          {errorMsg && (
            <div className="p-4 rounded-xl text-sm border bg-[rgba(239,68,68,0.1)] border-[var(--error)] text-[var(--error)]">
              ⚠️ {errorMsg}
            </div>
          )}

          {/* Profile Section */}
          <div className="rounded-2xl p-6 space-y-4" style={{ background: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
            <h3 className="text-base font-semibold border-b pb-2" style={{ color: "var(--text-primary)", borderColor: "var(--border-color)" }}>👤 User Profile</h3>
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <label className="text-sm font-medium" style={{ color: "var(--text-secondary)" }}>Email Address</label>
                <input
                  type="email"
                  value={email}
                  disabled
                  className="rounded-lg px-3 py-2 text-sm w-full sm:w-64 cursor-not-allowed opacity-60 text-right bg-[var(--bg-tertiary)]"
                  style={{ border: "1px solid var(--border-color)", color: "var(--text-primary)" }}
                />
              </div>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <label className="text-sm font-medium" style={{ color: "var(--text-secondary)" }}>Full Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  className="rounded-lg px-3 py-2 text-sm w-full sm:w-64 text-right outline-none transition-all focus:border-[var(--accent-primary)] bg-[var(--bg-tertiary)]"
                  style={{ border: "1px solid var(--border-color)", color: "var(--text-primary)" }}
                />
              </div>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <label className="text-sm font-medium" style={{ color: "var(--text-secondary)" }}>Nickname</label>
                <input
                  type="text"
                  value={nickname}
                  onChange={(e) => setNickname(e.target.value)}
                  className="rounded-lg px-3 py-2 text-sm w-full sm:w-64 text-right outline-none transition-all focus:border-[var(--accent-primary)] bg-[var(--bg-tertiary)]"
                  style={{ border: "1px solid var(--border-color)", color: "var(--text-primary)" }}
                />
              </div>
            </div>
          </div>

          {/* LLM Config Section */}
          <div className="rounded-2xl p-6 space-y-4" style={{ background: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
            <h3 className="text-base font-semibold border-b pb-2" style={{ color: "var(--text-primary)", borderColor: "var(--border-color)" }}>🤖 AI Engine Config</h3>
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <label className="text-sm font-medium" style={{ color: "var(--text-secondary)" }}>Default LLM Provider</label>
                <select
                  value={provider}
                  onChange={(e) => setProvider(e.target.value)}
                  className="rounded-lg px-3 py-2 text-sm w-full sm:w-64 outline-none bg-[var(--bg-tertiary)]"
                  style={{ border: "1px solid var(--border-color)", color: "var(--text-primary)" }}
                >
                  <option value="ollama">Ollama (Local LLM)</option>
                  <option value="openai">OpenAI (GPT-4o / GPT-3.5)</option>
                  <option value="gemini">Google Gemini (Gemini Pro)</option>
                </select>
              </div>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <label className="text-sm font-medium" style={{ color: "var(--text-secondary)" }}>Default Model</label>
                <input
                  type="text"
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  className="rounded-lg px-3 py-2 text-sm w-full sm:w-64 text-right outline-none transition-all focus:border-[var(--accent-primary)] bg-[var(--bg-tertiary)]"
                  style={{ border: "1px solid var(--border-color)", color: "var(--text-primary)" }}
                />
              </div>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex flex-col">
                  <label className="text-sm font-medium" style={{ color: "var(--text-secondary)" }}>Temperature ({temperature})</label>
                  <span className="text-[10px]" style={{ color: "var(--text-muted)" }}>Lower is more focused/deterministic, higher is creative</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1.2"
                  step="0.1"
                  value={temperature}
                  onChange={(e) => setTemperature(parseFloat(e.target.value))}
                  className="w-full sm:w-64"
                />
              </div>
            </div>
          </div>

          {/* Integrations Section */}
          <div className="rounded-2xl p-6 space-y-4" style={{ background: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
            <h3 className="text-base font-semibold border-b pb-2" style={{ color: "var(--text-primary)", borderColor: "var(--border-color)" }}>🔌 External Service Integrations</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex flex-col">
                  <span className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Google Calendar Connection</span>
                  <span className="text-xs" style={{ color: "var(--text-muted)" }}>Allows Uday AI to check and plan your calendar meetings</span>
                </div>
                <button
                  type="button"
                  onClick={() => setGoogleCalendarConnected(!googleCalendarConnected)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold transition-all border"
                  style={{
                    background: googleCalendarConnected ? "rgba(16,185,129,0.15)" : "var(--bg-tertiary)",
                    borderColor: googleCalendarConnected ? "var(--success)" : "var(--border-color)",
                    color: googleCalendarConnected ? "var(--success)" : "var(--text-secondary)",
                  }}
                >
                  {googleCalendarConnected ? "✓ Connected" : "Connect"}
                </button>
              </div>

              <div className="flex items-center justify-between border-t border-[var(--border-color)] pt-4">
                <div className="flex flex-col">
                  <span className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Gmail Connection</span>
                  <span className="text-xs" style={{ color: "var(--text-muted)" }}>Allows Uday AI to draft, fetch, and send emails for you</span>
                </div>
                <button
                  type="button"
                  onClick={() => setGmailConnected(!gmailConnected)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold transition-all border"
                  style={{
                    background: gmailConnected ? "rgba(16,185,129,0.15)" : "var(--bg-tertiary)",
                    borderColor: gmailConnected ? "var(--success)" : "var(--border-color)",
                    color: gmailConnected ? "var(--success)" : "var(--text-secondary)",
                  }}
                >
                  {gmailConnected ? "✓ Connected" : "Connect"}
                </button>
              </div>

              <div className="flex items-center justify-between border-t border-[var(--border-color)] pt-4">
                <div className="flex flex-col">
                  <span className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>GitHub Connection</span>
                  <span className="text-xs" style={{ color: "var(--text-muted)" }}>Allows Uday AI to inspect repos and manage issue PRs</span>
                </div>
                <button
                  type="button"
                  onClick={() => setGithubConnected(!githubConnected)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold transition-all border"
                  style={{
                    background: githubConnected ? "rgba(16,185,129,0.15)" : "var(--bg-tertiary)",
                    borderColor: githubConnected ? "var(--success)" : "var(--border-color)",
                    color: githubConnected ? "var(--success)" : "var(--text-secondary)",
                  }}
                >
                  {githubConnected ? "✓ Connected" : "Connect"}
                </button>
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={isSaving}
            className="w-full py-3.5 rounded-xl text-sm font-bold text-white transition-all hover:scale-[1.01]"
            style={{
              background: "var(--gradient-primary)",
              boxShadow: "var(--shadow-glow)",
              cursor: isSaving ? "not-allowed" : "pointer",
            }}
          >
            {isSaving ? "Saving..." : "💾 Save Settings"}
          </button>
        </form>
      </main>
    </div>
  );
}
