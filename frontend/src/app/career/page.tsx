"use client";

import { useState, useEffect } from "react";
import Sidebar from "@/components/dashboard/Sidebar";
import api from "@/lib/api";
import useAuth from "@/hooks/useAuth";

interface Readiness {
  role: string;
  readiness_percentage: number;
  gap_skills: string[];
}

interface Phase {
  phase_number: number;
  title: string;
  timeline: string;
  skills_to_learn: string[];
  recommended_action_items: string[];
}

interface Roadmap {
  summary: string;
  target_roles_readiness: Readiness[];
  roadmap_phases: Phase[];
  suggested_certifications: string[];
}

interface ChatMessage {
  id: string;
  role: "user" | "nidhi";
  text: string;
}

export default function CareerPage() {
  useAuth();
  const [activeSubTab, setActiveSubTab] = useState<"roadmap" | "gaps" | "chat">("roadmap");
  const [roadmap, setRoadmap] = useState<Roadmap | null>(null);
  const [loading, setLoading] = useState(true);

  // Chat State
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);

  useEffect(() => {
    loadRoadmap();
    setChatMessages([
      {
        id: "init",
        role: "nidhi",
        text: "Namaste Uday! Main Nidhi hoon. Aapki career, placements, aur skill paths ko grow karne ke liye main ready hoon. Aap niche query puch sakte hain or roadmap view kar sakte hain! 💜",
      },
    ]);
  }, []);

  const loadRoadmap = async () => {
    try {
      const res = await (api as any).getRoadmap?.();
      setRoadmap(res?.roadmap || null);
    } catch (err) {
      console.error("Failed to load career roadmap", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSendChat = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || chatLoading) return;

    const userText = chatInput.trim();
    setChatInput("");
    setChatMessages((prev) => [...prev, { id: crypto.randomUUID(), role: "user", text: userText }]);
    setChatLoading(true);

    try {
      const res = await (api as any).sendCareerChat?.({ message: userText });
      setChatMessages((prev) => [
        ...prev,
        { id: crypto.randomUUID(), role: "nidhi", text: res.response },
      ]);
    } catch {
      setChatMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "nidhi",
          text: "Sorry, network error ki wajah se main connect nahi kar payi.",
        },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  const cardStyle = {
    background: "rgba(17, 17, 40, 0.75)",
    border: "1px solid rgba(124, 107, 255, 0.12)",
    backdropFilter: "blur(16px)",
  };

  return (
    <>
      <div className="aurora-bg" aria-hidden />
      <div className="flex min-h-screen" style={{ background: "var(--bg-primary)" }}>
        <Sidebar />
        <main
          className="flex-1 overflow-y-auto relative"
          style={{ marginLeft: "var(--sidebar-width)", zIndex: 1 }}
        >
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
                🚀 Nidhi Career Coach
              </h1>
              <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                Get custom placement advice, skill matrices, roadmaps, and career reviews
              </p>
            </div>
          </header>

          <div className="max-w-4xl mx-auto px-6 py-8 space-y-6">
            {/* Tabs */}
            <div className="flex gap-1">
              {[
                { key: "roadmap", label: "Map Roadmap", emoji: "🗺️" },
                { key: "gaps", label: "Readiness Matrix", emoji: "📊" },
                { key: "chat", label: "Coach Chat", emoji: "💬" },
              ].map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveSubTab(tab.key as any)}
                  className="px-4 py-2 rounded-xl text-sm font-medium transition-all"
                  style={{
                    background: activeSubTab === tab.key ? "rgba(124,107,255,0.15)" : "transparent",
                    border: `1px solid ${activeSubTab === tab.key ? "rgba(124,107,255,0.4)" : "transparent"}`,
                    color: activeSubTab === tab.key ? "var(--text-primary)" : "var(--text-muted)",
                  }}
                >
                  {tab.emoji} {tab.label}
                </button>
              ))}
            </div>

            {loading ? (
              <div className="flex justify-center py-20">
                <div
                  className="w-10 h-10 rounded-full"
                  style={{
                    background: "linear-gradient(135deg, #7c6bff, #e879f9)",
                    animation: "breathe 1.5s ease-in-out infinite",
                  }}
                />
              </div>
            ) : (
              <>
                {/* Roadmap View */}
                {activeSubTab === "roadmap" && roadmap && (
                  <div className="space-y-6">
                    {/* Summary */}
                    <div className="rounded-2xl p-5" style={cardStyle}>
                      <h3 className="text-xs font-bold text-violet-300 uppercase tracking-wide">
                        Summary Insight
                      </h3>
                      <p className="text-sm mt-2 leading-relaxed text-gray-300">
                        {roadmap.summary}
                      </p>
                    </div>

                    {/* Timeline Node Grid */}
                    <div className="relative border-l border-purple-500/20 pl-6 ml-4 space-y-8">
                      {roadmap.roadmap_phases?.map((p, idx) => (
                        <div key={idx} className="relative">
                          {/* Dot */}
                          <span className="absolute -left-[31px] top-1.5 w-4.5 h-4.5 rounded-full border-2 border-purple-500 bg-black flex items-center justify-center text-[10px] font-bold text-purple-400">
                            {p.phase_number}
                          </span>
                          <div className="rounded-2xl p-5" style={cardStyle}>
                            <div className="flex justify-between items-center border-b border-purple-500/5 pb-2 mb-3">
                              <h4 className="font-bold text-sm text-purple-200">{p.title}</h4>
                              <span className="text-xs px-2.5 py-0.5 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-300">
                                ⏳ {p.timeline}
                              </span>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              <div>
                                <h5 className="text-[10px] text-gray-400 font-bold uppercase">
                                  Skills to Master
                                </h5>
                                <div className="flex flex-wrap gap-1.5 mt-2">
                                  {p.skills_to_learn?.map((s) => (
                                    <span
                                      key={s}
                                      className="text-xs px-2 py-0.5 rounded-full bg-white/5 border border-white/10 text-gray-300"
                                    >
                                      {s}
                                    </span>
                                  ))}
                                </div>
                              </div>
                              <div>
                                <h5 className="text-[10px] text-gray-400 font-bold uppercase">
                                  Action Projects
                                </h5>
                                <ul className="list-disc ml-4 mt-2 space-y-1">
                                  {p.recommended_action_items?.map((item, id) => (
                                    <li key={id} className="text-xs text-gray-300 leading-normal">
                                      {item}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Certifications */}
                    {roadmap.suggested_certifications?.length > 0 && (
                      <div className="rounded-2xl p-5" style={cardStyle}>
                        <h3 className="text-xs font-bold text-violet-300 uppercase tracking-wide">
                          Recommended Certifications
                        </h3>
                        <div className="flex flex-wrap gap-2 mt-3">
                          {roadmap.suggested_certifications.map((c) => (
                            <span
                              key={c}
                              className="text-xs px-3 py-1 rounded-xl bg-purple-500/5 border border-purple-500/20 text-purple-300 font-medium"
                            >
                              🏆 {c}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Gaps / Readiness Matrix View */}
                {activeSubTab === "gaps" && roadmap && (
                  <div className="space-y-4">
                    {roadmap.target_roles_readiness?.map((r) => (
                      <div key={r.role} className="rounded-2xl p-5" style={cardStyle}>
                        <div className="flex justify-between items-center mb-2">
                          <h4 className="font-bold text-sm text-white">{r.role}</h4>
                          <span className="text-xs font-bold text-purple-300">
                            {r.readiness_percentage}% ready
                          </span>
                        </div>

                        {/* Bar */}
                        <div className="w-full h-2.5 rounded-full bg-white/5 overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all duration-700"
                            style={{
                              width: `${r.readiness_percentage}%`,
                              background: "linear-gradient(90deg, #7c6bff, #e879f9)",
                              boxShadow: "0 0 10px rgba(124,107,255,0.4)",
                            }}
                          />
                        </div>

                        {/* Gaps */}
                        {r.gap_skills?.length > 0 && (
                          <div className="mt-3.5">
                            <span className="text-[10px] text-red-400 font-bold uppercase">
                              Gap Skills to Learn:
                            </span>
                            <div className="flex flex-wrap gap-1.5 mt-1.5">
                              {r.gap_skills.map((skill) => (
                                <span
                                  key={skill}
                                  className="text-xs px-2 py-0.5 rounded-full bg-red-500/10 border border-red-500/20 text-red-300"
                                >
                                  {skill}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* Coaching Chat Console */}
                {activeSubTab === "chat" && (
                  <div
                    className="rounded-3xl flex flex-col h-[520px] overflow-hidden"
                    style={cardStyle}
                  >
                    {/* Chat Messages */}
                    <div className="flex-1 overflow-y-auto p-5 space-y-4">
                      {chatMessages.map((m) => (
                        <div
                          key={m.id}
                          className={`flex gap-3 ${m.role === "user" ? "flex-row-reverse text-right" : "flex-row"}`}
                        >
                          <div
                            className="w-7 h-7 rounded-full flex items-center justify-center font-bold text-xs flex-shrink-0"
                            style={{
                              background:
                                m.role === "nidhi"
                                  ? "linear-gradient(135deg, #7c6bff, #e879f9)"
                                  : "rgba(255,255,255,0.1)",
                              color: "white",
                            }}
                          >
                            {m.role === "nidhi" ? "✦" : "U"}
                          </div>
                          <div
                            className="max-w-[80%] text-xs leading-relaxed p-3 rounded-2xl whitespace-pre-wrap text-left"
                            style={{
                              background:
                                m.role === "nidhi"
                                  ? "rgba(124,107,255,0.1)"
                                  : "rgba(255,255,255,0.04)",
                              border: "1px solid rgba(124,107,255,0.12)",
                              color: "var(--text-secondary)",
                              borderRadius:
                                m.role === "nidhi"
                                  ? "4px 16px 16px 16px"
                                  : "16px 4px 16px 16px",
                            }}
                          >
                            {m.text}
                          </div>
                        </div>
                      ))}
                      {chatLoading && (
                        <div className="flex gap-3">
                          <div
                            className="w-7 h-7 rounded-full flex items-center justify-center font-bold text-xs flex-shrink-0 animate-pulse"
                            style={{ background: "linear-gradient(135deg, #7c6bff, #e879f9)" }}
                          >
                            ✦
                          </div>
                          <div className="w-12 h-6 rounded-2xl flex items-center justify-center bg-white/5 border border-white/10">
                            <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-bounce" />
                            <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-bounce mx-0.5 [animation-delay:0.2s]" />
                            <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-bounce [animation-delay:0.4s]" />
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Chat Input */}
                    <form
                      onSubmit={handleSendChat}
                      className="p-4 border-t border-purple-500/10 flex gap-2"
                    >
                      <input
                        type="text"
                        value={chatInput}
                        onChange={(e) => setChatInput(e.target.value)}
                        placeholder="Ask Nidhi about skill choices, job readiness or certificates…"
                        className="flex-1 bg-transparent text-xs outline-none px-3 py-2.5 rounded-xl border border-purple-500/15 focus:border-purple-500/40 text-white"
                      />
                      <button
                        type="submit"
                        disabled={chatLoading || !chatInput.trim()}
                        className="btn-nidhi text-xs px-4 py-2.5"
                      >
                        Send
                      </button>
                    </form>
                  </div>
                )}
              </>
            )}
          </div>
        </main>
      </div>
    </>
  );
}
