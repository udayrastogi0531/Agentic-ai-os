"use client";

/**
 * Uday AI — Dashboard Home Page
 *
 * Main landing page with stats, quick actions, and agent network status.
 */

import { useState, useEffect } from "react";
import Sidebar from "@/components/dashboard/Sidebar";
import Link from "next/link";
import useAuth from "@/hooks/useAuth";
import api from "@/lib/api";

const QUICK_ACTIONS = [
  { name: "New Chat", icon: "💬", href: "/chat", color: "#6366f1" },
  { name: "Research", icon: "🔍", href: "/research", color: "#ec4899" },
  { name: "Add Task", icon: "✅", href: "/tasks", color: "#10b981" },
  { name: "New Note", icon: "📝", href: "/notes", color: "#f59e0b" },
  { name: "Upload File", icon: "📄", href: "/files", color: "#3b82f6" },
  { name: "Settings", icon: "🔧", href: "/settings", color: "#8b5cf6" },
];

export default function DashboardPage() {
  const { user } = useAuth(); // Require authentication

  const [stats, setStats] = useState([
    { label: "Conversations", value: "—", icon: "💬" },
    { label: "Memories", value: "—", icon: "🧠" },
    { label: "Tasks", value: "—", icon: "✅" },
    { label: "Documents", value: "—", icon: "📄" },
  ]);

  const [agents, setAgents] = useState([
    { name: "Planner", icon: "🧠", status: "active" },
    { name: "Memory", icon: "💾", status: "active" },
    { name: "Research", icon: "🔍", status: "active" },
    { name: "Coding", icon: "💻", status: "active" },
    { name: "Browser", icon: "🌐", status: "active" },
    { name: "File", icon: "📁", status: "active" },
    { name: "Calendar", icon: "📅", status: "pending" },
    { name: "Gmail", icon: "📧", status: "pending" },
    { name: "Notes", icon: "📝", status: "active" },
    { name: "Tasks", icon: "✅", status: "active" },
  ]);

  useEffect(() => {
    if (!user) return;

    // Load Overview Stats
    const loadOverviewData = async () => {
      try {
        const [convs, memoriesRes, tasksRes, filesRes] = await Promise.all([
          api.getConversations().catch(() => []),
          api.getMemories().catch(() => ({ total: 0 })),
          api.getTasks().catch(() => ({ total: 0 })),
          api.getFiles().catch(() => ({ total: 0 })),
        ]);

        const conversationsCount = Array.isArray(convs) ? convs.length : 0;
        const memoriesCount = (memoriesRes as any).total || 0;
        const tasksCount = (tasksRes as any).total || 0;
        const filesCount = (filesRes as any).total || 0;

        setStats([
          { label: "Conversations", value: String(conversationsCount), icon: "💬" },
          { label: "Memories", value: String(memoriesCount), icon: "🧠" },
          { label: "Tasks", value: String(tasksCount), icon: "✅" },
          { label: "Documents", value: String(filesCount), icon: "📄" },
        ]);
      } catch (err) {
        console.error("Failed to load overview data:", err);
      }
    };

    // Load Agent network statuses
    const loadAgentStatuses = async () => {
      try {
        const result: any = await api.getAgentStatus().catch(() => null);
        if (result && Array.isArray(result)) {
          // Map backend response if applicable
          // Assuming structure similar to AGENT_LIST
        }
      } catch (err) {
        console.error("Failed to load agent status:", err);
      }
    };

    loadOverviewData();
    loadAgentStatuses();
  }, [user]);

  return (
    <div className="flex min-h-screen" style={{ background: "var(--bg-primary)" }}>
      <Sidebar />

      <main
        className="flex-1 overflow-y-auto"
        style={{ marginLeft: "var(--sidebar-width)" }}
      >
        {/* Header */}
        <header
          className="sticky top-0 z-30 glass-strong px-8 py-5"
          style={{ borderBottom: "1px solid var(--border-color)" }}
        >
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
                Welcome back, {user?.nickname || user?.name || "User"}! 👋
              </h1>
              <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
                {new Date().toLocaleDateString("en-US", {
                  weekday: "long",
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                })}
              </p>
            </div>
            <Link
              href="/chat"
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium text-white transition-all duration-200 hover:scale-105"
              style={{ background: "var(--gradient-primary)", boxShadow: "var(--shadow-glow)" }}
            >
              💬 New Chat
            </Link>
          </div>
        </header>

        <div className="px-8 py-6 space-y-8 animate-fade-in">
          {/* Stats Grid */}
          <section>
            <h2 className="text-lg font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
              Overview
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {stats.map((stat) => (
                <div
                  key={stat.label}
                  className="rounded-2xl p-5 transition-all duration-200 hover:scale-[1.02]"
                  style={{
                    background: "var(--gradient-card)",
                    border: "1px solid var(--border-color)",
                  }}
                >
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-2xl">{stat.icon}</span>
                  </div>
                  <p className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
                    {stat.value}
                  </p>
                  <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>
                    {stat.label}
                  </p>
                </div>
              ))}
            </div>
          </section>

          {/* Quick Actions */}
          <section>
            <h2 className="text-lg font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
              Quick Actions
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
              {QUICK_ACTIONS.map((action) => (
                <Link
                  key={action.name}
                  href={action.href}
                  className="flex flex-col items-center gap-2 rounded-2xl p-5 transition-all duration-200 hover:scale-105"
                  style={{
                    background: "var(--bg-card)",
                    border: "1px solid var(--border-color)",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = action.color;
                    e.currentTarget.style.boxShadow = `0 0 20px ${action.color}30`;
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = "var(--border-color)";
                    e.currentTarget.style.boxShadow = "none";
                  }}
                >
                  <span className="text-2xl">{action.icon}</span>
                  <span className="text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                    {action.name}
                  </span>
                </Link>
              ))}
            </div>
          </section>

          {/* Agent Status */}
          <section>
            <h2 className="text-lg font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
              Agent Network
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
              {agents.map((agent) => (
                <div
                  key={agent.name}
                  className="flex items-center gap-3 rounded-xl p-4 transition-all duration-200"
                  style={{
                    background: "var(--bg-card)",
                    border: "1px solid var(--border-color)",
                  }}
                >
                  <span className="text-xl">{agent.icon}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate" style={{ color: "var(--text-primary)" }}>
                      {agent.name}
                    </p>
                    <div className="flex items-center gap-1.5 mt-0.5">
                      <div
                        className="w-1.5 h-1.5 rounded-full"
                        style={{
                          background: agent.status === "active" ? "var(--success)" : "var(--warning)",
                        }}
                      />
                      <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                        {agent.status === "active" ? "Active" : "Setup needed"}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Getting Started */}
          <section
            className="rounded-2xl p-6"
            style={{
              background: "var(--gradient-card)",
              border: "1px solid var(--border-color)",
            }}
          >
            <h2 className="text-lg font-semibold mb-3 gradient-text">
              🚀 Getting Started
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                  1. Start Chatting
                </h3>
                <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                  Open a new chat and talk naturally. I understand English and Hinglish!
                </p>
              </div>
              <div className="space-y-2">
                <h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                  2. Upload Documents
                </h3>
                <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                  Upload PDFs, DOCX, or images and ask questions about them.
                </p>
              </div>
              <div className="space-y-2">
                <h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                  3. Connect Services
                </h3>
                <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                  Link Google Calendar and Gmail in Settings for full integration.
                </p>
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
