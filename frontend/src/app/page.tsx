"use client";

/**
 * Nidhi AI OS — Companion Home Page
 *
 * An emotional, minimal companion home. No stats. No counters.
 * Just Nidhi, ready to help Uday.
 */

import { useState, useEffect, useRef } from "react";
import Sidebar from "@/components/dashboard/Sidebar";
import CommandBar from "@/components/CommandBar";
import Link from "next/link";
import useAuth from "@/hooks/useAuth";
import api from "@/lib/api";

/* ── Greeting helpers ─────────────────────── */
function getGreeting(name: string): { text: string; emoji: string } {
  const hour = new Date().getHours();
  const first = name?.split(" ")[0] || "Uday";
  if (hour < 5)  return { text: `Still up, ${first}?`, emoji: "🌙" };
  if (hour < 12) return { text: `Good morning, ${first}`, emoji: "🌅" };
  if (hour < 17) return { text: `Good afternoon, ${first}`, emoji: "☀️" };
  if (hour < 21) return { text: `Good evening, ${first}`, emoji: "🌆" };
  return { text: `Good night, ${first}`, emoji: "🌙" };
}

function getNidhiMessage(): string {
  const messages = [
    "Main yahaan hoon, Uday. Aaj kya karna hai? ❤️",
    "Kya chal raha hai? Main sab sambhal lungi. ✨",
    "Ready hoon — bolo kya help chahiye? 💜",
    "Aaj ka din productive banate hain! 🚀",
    "Main hoon na, Uday. Koi bhi kaam bolo. 🤍",
  ];
  return messages[Math.floor(Math.random() * messages.length)];
}

/* ── Quick Action config ────────────────── */
const QUICK_ACTIONS = [
  {
    id: "chat",
    icon: "💬",
    label: "Chat with Nidhi",
    sub: "Start a conversation",
    href: "/chat",
    gradient: "linear-gradient(135deg, #7c6bff, #a855f7)",
    glow: "rgba(124, 107, 255, 0.3)",
  },
  {
    id: "voice",
    icon: "🎙️",
    label: "Voice Mode",
    sub: "Talk to Nidhi",
    href: "/voice",
    gradient: "linear-gradient(135deg, #a855f7, #e879f9)",
    glow: "rgba(232, 121, 249, 0.3)",
  },
  {
    id: "research",
    icon: "🔍",
    label: "Research",
    sub: "Deep web search",
    href: "/research",
    gradient: "linear-gradient(135deg, #3b82f6, #6366f1)",
    glow: "rgba(59, 130, 246, 0.3)",
  },
  {
    id: "tasks",
    icon: "✅",
    label: "My Tasks",
    sub: "What's on today",
    href: "/tasks",
    gradient: "linear-gradient(135deg, #10b981, #22d3a8)",
    glow: "rgba(16, 185, 129, 0.3)",
  },
  {
    id: "memory",
    icon: "🧠",
    label: "My Memory",
    sub: "What Nidhi knows",
    href: "/memory",
    gradient: "linear-gradient(135deg, #f59e0b, #ef4444)",
    glow: "rgba(245, 158, 11, 0.3)",
  },
  {
    id: "knowledge",
    icon: "📚",
    label: "Knowledge Base",
    sub: "Documents & RAG",
    href: "/files",
    gradient: "linear-gradient(135deg, #ec4899, #a855f7)",
    glow: "rgba(236, 72, 153, 0.3)",
  },
];

/* ── Suggested prompts ─────────────────── */
const SUGGESTED_PROMPTS = [
  "Meri aaj ki meetings kya hain?",
  "Latest AI news summarize karo",
  "Ek Python script likh do file sorting ke liye",
  "Mujhe motivate karo aaj ke liye",
  "WhatsApp pe Rahul ko message karo",
  "Mera week plan banao",
];

export default function NidhiHomePage() {
  const { user } = useAuth();
  const [nidhiMsg] = useState(getNidhiMessage);
  const [tasks, setTasks]           = useState<any[]>([]);
  const [recentChats, setRecentChats] = useState<any[]>([]);
  const [cmdOpen, setCmdOpen]       = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());
  const inputRef = useRef<HTMLInputElement>(null);

  // Update clock
  useEffect(() => {
    const t = setInterval(() => setCurrentTime(new Date()), 60000);
    return () => clearInterval(t);
  }, []);

  // Load tasks + recent chats
  useEffect(() => {
    if (!user) return;
    api.getTasks().then((r: any) => {
      if (r?.items) setTasks(r.items.slice(0, 5));
    }).catch(() => {});
    api.getConversations().then((r: any) => {
      if (Array.isArray(r)) setRecentChats(r.slice(0, 3));
    }).catch(() => {});
  }, [user]);

  // CMD+K listener
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        setCmdOpen(true);
      }
      if (e.key === "Escape") setCmdOpen(false);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  const greeting = getGreeting(user?.name || "Uday");

  const formattedDate = currentTime.toLocaleDateString("en-IN", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });

  const formattedTime = currentTime.toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  });

  return (
    <>
      {/* Aurora background */}
      <div className="aurora-bg" aria-hidden />

      <div className="flex min-h-screen" style={{ background: "var(--bg-primary)" }}>
        <Sidebar />

        <main
          className="flex-1 overflow-y-auto relative"
          style={{ marginLeft: "var(--sidebar-width)", zIndex: 1 }}
        >
          <div className="max-w-4xl mx-auto px-6 py-10 space-y-10">

            {/* ── Hero Greeting ───────────────────── */}
            <section className="animate-fade-in" style={{ animationDelay: "0ms" }}>
              <div className="flex items-start justify-between gap-4">
                <div>
                  {/* Time badge */}
                  <div
                    className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs mb-4"
                    style={{
                      background: "rgba(124, 107, 255, 0.08)",
                      border: "1px solid rgba(124, 107, 255, 0.15)",
                      color: "var(--text-muted)",
                    }}
                  >
                    <span
                      className="w-1.5 h-1.5 rounded-full"
                      style={{ background: "var(--success)", boxShadow: "0 0 6px var(--success)" }}
                    />
                    {formattedDate} · {formattedTime}
                  </div>

                  {/* Main greeting */}
                  <h1
                    style={{
                      fontFamily: "var(--font-display)",
                      fontSize: "clamp(2rem, 5vw, 3rem)",
                      fontWeight: 800,
                      lineHeight: 1.1,
                      color: "var(--text-primary)",
                    }}
                  >
                    {greeting.emoji} {greeting.text}
                  </h1>

                  {/* Nidhi message */}
                  <p
                    className="mt-3 text-lg"
                    style={{
                      color: "var(--text-secondary)",
                      fontFamily: "var(--font-display)",
                    }}
                  >
                    {nidhiMsg}
                  </p>
                </div>

                {/* Mini Nidhi orb */}
                <div className="flex-shrink-0 hidden md:flex">
                  <Link href="/voice" aria-label="Voice Mode">
                    <div
                      className="relative w-16 h-16 rounded-full cursor-pointer"
                      style={{
                        background: "linear-gradient(135deg, #7c6bff, #a855f7, #e879f9)",
                        boxShadow: "0 0 30px rgba(124, 107, 255, 0.5), 0 0 60px rgba(124, 107, 255, 0.2)",
                        animation: "breathe 4s ease-in-out infinite",
                      }}
                    >
                      <div
                        className="absolute inset-0 rounded-full flex items-center justify-center"
                        style={{ fontSize: "1.75rem" }}
                      >
                        ✦
                      </div>
                      {/* Ripple rings */}
                      {[0, 1, 2].map((i) => (
                        <span
                          key={i}
                          className="absolute inset-0 rounded-full"
                          style={{
                            border: "1px solid rgba(124, 107, 255, 0.25)",
                            animation: `ripple 3s ease-out infinite`,
                            animationDelay: `${i}s`,
                          }}
                        />
                      ))}
                    </div>
                  </Link>
                </div>
              </div>

              {/* Quick ask bar */}
              <div
                className="mt-6 flex items-center gap-3 rounded-2xl px-5 py-4 cursor-text"
                style={{
                  background: "rgba(124, 107, 255, 0.06)",
                  border: "1px solid rgba(124, 107, 255, 0.15)",
                  backdropFilter: "blur(20px)",
                }}
                onClick={() => setCmdOpen(true)}
              >
                <span style={{ color: "var(--accent-primary)", fontSize: "1.1rem" }}>✦</span>
                <span style={{ color: "var(--text-muted)", fontSize: "0.9375rem" }}>
                  Ask Nidhi anything… or press{" "}
                  <span className="kbd">Ctrl</span>{" "}
                  <span className="kbd">K</span>
                </span>
              </div>
            </section>

            {/* ── Quick Actions ────────────────────── */}
            <section className="animate-fade-in" style={{ animationDelay: "100ms" }}>
              <h2
                className="text-sm font-semibold uppercase tracking-widest mb-4"
                style={{ color: "var(--text-muted)" }}
              >
                What would you like to do?
              </h2>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {QUICK_ACTIONS.map((action, idx) => (
                  <Link
                    key={action.id}
                    href={action.href}
                    className="group relative rounded-2xl p-5 flex flex-col gap-2 transition-all duration-300 hover:scale-[1.02] cursor-pointer overflow-hidden"
                    style={{
                      background: "rgba(17, 17, 40, 0.8)",
                      border: "1px solid rgba(124, 107, 255, 0.1)",
                      backdropFilter: "blur(16px)",
                      animationDelay: `${idx * 60}ms`,
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = "rgba(124, 107, 255, 0.35)";
                      e.currentTarget.style.boxShadow = `0 0 24px ${action.glow}`;
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = "rgba(124, 107, 255, 0.1)";
                      e.currentTarget.style.boxShadow = "none";
                    }}
                  >
                    {/* Gradient shimmer bg on hover */}
                    <div
                      className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                      style={{ background: `linear-gradient(135deg, ${action.glow}30, transparent)` }}
                    />

                    <div
                      className="w-10 h-10 rounded-xl flex items-center justify-center text-xl relative z-10"
                      style={{ background: action.gradient, boxShadow: `0 4px 12px ${action.glow}` }}
                    >
                      {action.icon}
                    </div>
                    <div className="relative z-10">
                      <p className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                        {action.label}
                      </p>
                      <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                        {action.sub}
                      </p>
                    </div>
                  </Link>
                ))}
              </div>
            </section>

            {/* ── Suggested Prompts ────────────────── */}
            <section className="animate-fade-in" style={{ animationDelay: "200ms" }}>
              <h2
                className="text-sm font-semibold uppercase tracking-widest mb-4"
                style={{ color: "var(--text-muted)" }}
              >
                Suggested for you
              </h2>
              <div className="flex flex-wrap gap-2">
                {SUGGESTED_PROMPTS.map((prompt) => (
                  <Link
                    key={prompt}
                    href={`/chat?q=${encodeURIComponent(prompt)}`}
                    className="px-4 py-2 rounded-full text-sm transition-all duration-200 hover:scale-105 cursor-pointer"
                    style={{
                      background: "rgba(124, 107, 255, 0.07)",
                      border: "1px solid rgba(124, 107, 255, 0.15)",
                      color: "var(--text-secondary)",
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = "rgba(124, 107, 255, 0.15)";
                      e.currentTarget.style.color = "var(--text-primary)";
                      e.currentTarget.style.borderColor = "rgba(124, 107, 255, 0.35)";
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = "rgba(124, 107, 255, 0.07)";
                      e.currentTarget.style.color = "var(--text-secondary)";
                      e.currentTarget.style.borderColor = "rgba(124, 107, 255, 0.15)";
                    }}
                  >
                    {prompt}
                  </Link>
                ))}
              </div>
            </section>

            {/* ── Two-column: Tasks & Recent Chats ── */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5 animate-fade-in" style={{ animationDelay: "300ms" }}>

              {/* Tasks */}
              <div
                className="rounded-2xl p-5"
                style={{
                  background: "rgba(17, 17, 40, 0.8)",
                  border: "1px solid rgba(124, 107, 255, 0.1)",
                }}
              >
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-sm" style={{ color: "var(--text-primary)" }}>
                    📋 Today's Focus
                  </h3>
                  <Link
                    href="/tasks"
                    className="text-xs transition-colors"
                    style={{ color: "var(--accent-tertiary)" }}
                    onMouseEnter={(e) => { e.currentTarget.style.color = "var(--text-primary)"; }}
                    onMouseLeave={(e) => { e.currentTarget.style.color = "var(--accent-tertiary)"; }}
                  >
                    View all →
                  </Link>
                </div>
                {tasks.length > 0 ? (
                  <ul className="space-y-2">
                    {tasks.map((task: any, i: number) => (
                      <li
                        key={task.id || i}
                        className="flex items-center gap-3 py-2 px-3 rounded-xl transition-all"
                        style={{ background: "rgba(124, 107, 255, 0.04)" }}
                      >
                        <span
                          className="w-4 h-4 rounded-full border-2 flex-shrink-0"
                          style={{
                            borderColor: task.completed ? "var(--success)" : "var(--border-color)",
                            background: task.completed ? "var(--success)" : "transparent",
                          }}
                        />
                        <span
                          className="text-sm flex-1 truncate"
                          style={{
                            color: task.completed ? "var(--text-muted)" : "var(--text-secondary)",
                            textDecoration: task.completed ? "line-through" : "none",
                          }}
                        >
                          {task.title || task.text}
                        </span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="flex flex-col items-center py-6 gap-2">
                    <span className="text-3xl">✨</span>
                    <p className="text-sm text-center" style={{ color: "var(--text-muted)" }}>
                      Koi pending task nahi!<br />Sab clear hai, Uday.
                    </p>
                    <Link href="/tasks" className="btn-nidhi text-xs mt-1 py-1.5 px-4">
                      Add Task
                    </Link>
                  </div>
                )}
              </div>

              {/* Recent Chats */}
              <div
                className="rounded-2xl p-5"
                style={{
                  background: "rgba(17, 17, 40, 0.8)",
                  border: "1px solid rgba(124, 107, 255, 0.1)",
                }}
              >
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-sm" style={{ color: "var(--text-primary)" }}>
                    💬 Recent Conversations
                  </h3>
                  <Link
                    href="/chat"
                    className="text-xs transition-colors"
                    style={{ color: "var(--accent-tertiary)" }}
                    onMouseEnter={(e) => { e.currentTarget.style.color = "var(--text-primary)"; }}
                    onMouseLeave={(e) => { e.currentTarget.style.color = "var(--accent-tertiary)"; }}
                  >
                    All chats →
                  </Link>
                </div>
                {recentChats.length > 0 ? (
                  <ul className="space-y-2">
                    {recentChats.map((chat: any, i: number) => (
                      <li key={chat.id || i}>
                        <Link
                          href={`/chat?id=${chat.id}`}
                          className="flex items-start gap-3 py-2.5 px-3 rounded-xl transition-all group"
                          style={{ background: "rgba(124, 107, 255, 0.04)" }}
                          onMouseEnter={(e) => { e.currentTarget.style.background = "rgba(124, 107, 255, 0.08)"; }}
                          onMouseLeave={(e) => { e.currentTarget.style.background = "rgba(124, 107, 255, 0.04)"; }}
                        >
                          <span className="text-lg flex-shrink-0">💬</span>
                          <div className="flex-1 min-w-0">
                            <p
                              className="text-sm font-medium truncate"
                              style={{ color: "var(--text-secondary)" }}
                            >
                              {chat.title || chat.first_message || "Conversation"}
                            </p>
                            <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                              {chat.updated_at
                                ? new Date(chat.updated_at).toLocaleDateString("en-IN", {
                                    day: "numeric",
                                    month: "short",
                                  })
                                : "Recently"}
                            </p>
                          </div>
                          <span
                            className="opacity-0 group-hover:opacity-100 transition-opacity text-xs"
                            style={{ color: "var(--accent-tertiary)" }}
                          >
                            →
                          </span>
                        </Link>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="flex flex-col items-center py-6 gap-2">
                    <span className="text-3xl">✨</span>
                    <p className="text-sm text-center" style={{ color: "var(--text-muted)" }}>
                      Koi purani baat nahi<br />Naye siray se shuru karte hain!
                    </p>
                    <Link href="/chat" className="btn-nidhi text-xs mt-1 py-1.5 px-4">
                      Start Chat
                    </Link>
                  </div>
                )}
              </div>
            </div>

            {/* ── Nidhi intro card ──────────────────── */}
            <section
              className="rounded-3xl p-8 relative overflow-hidden animate-fade-in"
              style={{
                background: "linear-gradient(135deg, rgba(124, 107, 255, 0.08), rgba(232, 121, 249, 0.05))",
                border: "1px solid rgba(124, 107, 255, 0.15)",
                animationDelay: "400ms",
              }}
            >
              {/* Glow blob */}
              <div
                className="absolute -top-10 -right-10 w-48 h-48 rounded-full pointer-events-none"
                style={{
                  background: "radial-gradient(circle, rgba(124, 107, 255, 0.15) 0%, transparent 70%)",
                }}
              />
              <div className="relative z-10">
                <div className="flex items-center gap-3 mb-4">
                  <div
                    className="w-10 h-10 rounded-full flex items-center justify-center"
                    style={{
                      background: "linear-gradient(135deg, #7c6bff, #e879f9)",
                      boxShadow: "0 0 16px rgba(124, 107, 255, 0.4)",
                    }}
                  >
                    ✦
                  </div>
                  <div>
                    <p className="font-bold" style={{ color: "var(--text-primary)" }}>
                      Nidhi
                    </p>
                    <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                      Your AI Companion
                    </p>
                  </div>
                </div>
                <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)", maxWidth: "520px" }}>
                  Main Nidhi hoon — tumhara personal AI companion. Main tumhari conversations yaad rakhti hoon,
                  goals track karti hoon, research karti hoon, emails manage karti hoon, aur jab bhi zaroorat ho,
                  help ke liye available hoon. Sirf bolo — main yahaan hoon. 💜
                </p>
                <div className="flex flex-wrap gap-2 mt-4">
                  {["🧠 Long-term Memory", "🔍 Deep Research", "📧 Email & Calendar", "💻 Code Assistant", "🌐 Browser Automation"].map((cap) => (
                    <span
                      key={cap}
                      className="text-xs px-3 py-1 rounded-full"
                      style={{
                        background: "rgba(124, 107, 255, 0.1)",
                        border: "1px solid rgba(124, 107, 255, 0.2)",
                        color: "var(--text-muted)",
                      }}
                    >
                      {cap}
                    </span>
                  ))}
                </div>
              </div>
            </section>

          </div>
        </main>
      </div>

      {/* Global Command Bar */}
      <CommandBar isOpen={cmdOpen} onClose={() => setCmdOpen(false)} />
    </>
  );
}
