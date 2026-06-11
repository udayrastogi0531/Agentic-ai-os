"use client";

/**
 * Uday AI — Calendar Page
 *
 * Displays active meetings and calendar schedules when connected in user settings.
 */

import { useState, useEffect } from "react";
import Sidebar from "@/components/dashboard/Sidebar";
import useAuth from "@/hooks/useAuth";
import Link from "next/link";

interface EventItem {
  id: string;
  title: string;
  time: string;
  duration: string;
  type: string;
}

const MOCK_EVENTS: EventItem[] = [
  { id: "1", title: "🤖 Daily Standup — Uday AI Projects", time: "09:30 AM", duration: "30 min", type: "work" },
  { id: "2", title: "🎨 Design Critique & Glassmorphic UI Review", time: "11:00 AM", duration: "1 hour", type: "design" },
  { id: "3", title: "⚡ Agentic Workflow Architecture Sync", time: "02:00 PM", duration: "45 min", type: "tech" },
  { id: "4", title: "🍕 Lunch with Team", time: "01:00 PM", duration: "1 hour", type: "social" },
  { id: "5", title: "💼 Client Proposal Pitch", time: "04:30 PM", duration: "1 hour", type: "work" },
];

export default function CalendarPage() {
  const { user } = useAuth(); // Require authentication
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    if (user) {
      const prefs = (user.preferences as Record<string, any>) || {};
      setIsConnected(!!prefs.google_calendar_connected);
    }
  }, [user]);

  return (
    <div className="flex min-h-screen" style={{ background: "var(--bg-primary)" }}>
      <Sidebar />
      <main className="flex-1 font-sans" style={{ marginLeft: "var(--sidebar-width)" }}>
        <header className="sticky top-0 z-30 glass-strong px-8 py-5 flex items-center justify-between" style={{ borderBottom: "1px solid var(--border-color)" }}>
          <div>
            <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>📅 Calendar</h1>
            <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>Manage your schedule and calendar events</p>
          </div>
        </header>

        <div className="px-8 py-6 animate-fade-in max-w-4xl">
          {!isConnected ? (
            <div className="flex flex-col items-center justify-center py-20 rounded-2xl" style={{ background: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
              <span className="text-5xl mb-4">📅</span>
              <h3 className="text-lg font-semibold mb-2" style={{ color: "var(--text-primary)" }}>Connect Google Calendar</h3>
              <p className="text-sm text-center max-w-md mb-6" style={{ color: "var(--text-secondary)" }}>
                Link your Google account in settings to fetch active meetings and schedule them dynamically via chat commands.
              </p>
              <Link href="/settings" className="px-6 py-3 rounded-xl text-sm font-semibold text-white transition-all hover:scale-105 shadow-glow" style={{ background: "var(--gradient-primary)" }}>
                ⚙️ Go to Integrations Settings
              </Link>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>Today&apos;s Schedule</h2>
                <span className="text-xs px-2.5 py-1 rounded-full font-semibold border bg-emerald-500/10 text-emerald-400 border-emerald-500/30">
                  ● Google Calendar Sync Active
                </span>
              </div>

              <div className="space-y-3">
                {MOCK_EVENTS.map((event) => (
                  <div
                    key={event.id}
                    className="p-4 rounded-xl border flex items-center justify-between hover:bg-[var(--bg-hover)] transition-all"
                    style={{ background: "var(--bg-card)", borderColor: "var(--border-color)" }}
                  >
                    <div className="flex items-center gap-4">
                      <div
                        className="w-12 h-12 rounded-xl flex flex-col items-center justify-center text-xs font-bold"
                        style={{
                          background:
                            event.type === "work"
                              ? "rgba(59, 130, 246, 0.15)"
                              : event.type === "design"
                              ? "rgba(139, 92, 246, 0.15)"
                              : event.type === "tech"
                              ? "rgba(236, 72, 153, 0.15)"
                              : "rgba(16, 185, 129, 0.15)",
                          color:
                            event.type === "work"
                              ? "#3b82f6"
                              : event.type === "design"
                              ? "#8b5cf6"
                              : event.type === "tech"
                              ? "#ec4899"
                              : "#10b981",
                        }}
                      >
                        {event.time.split(" ")[0]}
                        <span className="text-[8px]">{event.time.split(" ")[1]}</span>
                      </div>
                      <div>
                        <h4 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{event.title}</h4>
                        <span className="text-xs" style={{ color: "var(--text-muted)" }}>Duration: {event.duration}</span>
                      </div>
                    </div>
                    <span className="text-xs font-semibold uppercase tracking-wider px-2.5 py-0.5 rounded-full" style={{ background: "var(--bg-tertiary)", color: "var(--text-secondary)" }}>
                      {event.type}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
