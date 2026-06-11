"use client";

/**
 * Uday AI — Admin Panel
 *
 * Full monitor dashboard displaying agent calls, duration metrics, and recent execution logs.
 */

import { useState, useEffect } from "react";
import Sidebar from "@/components/dashboard/Sidebar";
import useAuth from "@/hooks/useAuth";
import api from "@/lib/api";

interface AgentMetrics {
  agent: string;
  total_calls: number;
  avg_duration_ms: number;
}

interface LogEntry {
  id: string;
  agent_name: string;
  action: string;
  status: string;
  duration_ms: number;
  created_at: string;
}

export default function AdminPage() {
  useAuth(); // Require authentication
  const [stats, setStats] = useState({
    total_conversations: 0,
    total_messages: 0,
    total_memories: 0,
    active_agents: "8/10",
  });
  const [agentMetrics, setAgentMetrics] = useState<AgentMetrics[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const loadAdminData = async () => {
    try {
      const [analyticsRes, logsRes] = await Promise.all([
        api.getAnalytics().catch(() => null),
        api.getAgentLogs().catch(() => []),
      ]);

      if (analyticsRes) {
        const data = analyticsRes as any;
        setStats({
          total_conversations: data.total_conversations || 0,
          total_messages: data.total_messages || 0,
          total_memories: data.total_memories || 0,
          active_agents: "8/10", // Default or map if we have it
        });
        setAgentMetrics(data.agent_stats || []);
      }

      setLogs((logsRes as any[]) || []);
    } catch (err) {
      console.error("Failed to load admin data:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAdminData();
    // Poll logs every 10 seconds for real-time vibe
    const interval = setInterval(loadAdminData, 10000);
    return () => clearInterval(interval);
  }, []);

  const getAgentIcon = (name: string) => {
    const icons: Record<string, string> = {
      planner: "🧠",
      memory: "💾",
      research: "🔍",
      coding: "💻",
      browser: "🌐",
      file: "📁",
      calendar: "📅",
      gmail: "📧",
      notes: "📝",
      tasks: "✅",
    };
    return icons[name.toLowerCase()] || "🤖";
  };

  return (
    <div className="flex min-h-screen" style={{ background: "var(--bg-primary)" }}>
      <Sidebar />
      <main className="flex-1" style={{ marginLeft: "var(--sidebar-width)" }}>
        <header className="sticky top-0 z-30 glass-strong px-8 py-5 flex items-center justify-between" style={{ borderBottom: "1px solid var(--border-color)" }}>
          <div>
            <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>⚙️ Admin Panel</h1>
            <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>System monitoring, agent management, and analytics</p>
          </div>
          <button
            onClick={loadAdminData}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold text-white transition-all duration-200 hover:scale-105"
            style={{ background: "var(--bg-card)", border: "1px solid var(--border-color)" }}
          >
            🔄 Refresh
          </button>
        </header>

        <div className="px-8 py-6 space-y-8 overflow-y-auto animate-fade-in">
          {/* System Stats */}
          <section>
            <h2 className="text-lg font-semibold mb-4" style={{ color: "var(--text-primary)" }}>System Overview</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {[
                { label: "Total Conversations", value: stats.total_conversations, icon: "💬" },
                { label: "Total Messages", value: stats.total_messages, icon: "📨" },
                { label: "Total Memories", value: stats.total_memories, icon: "🧠" },
                { label: "Active Agents", value: stats.active_agents, icon: "🤖" },
              ].map((stat) => (
                <div key={stat.label} className="rounded-2xl p-5" style={{ background: "var(--gradient-card)", border: "1px solid var(--border-color)" }}>
                  <span className="text-2xl">{stat.icon}</span>
                  <p className="text-2xl font-bold mt-2" style={{ color: "var(--text-primary)" }}>{stat.value}</p>
                  <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>{stat.label}</p>
                </div>
              ))}
            </div>
          </section>

          {/* Agent Monitoring */}
          <section>
            <h2 className="text-lg font-semibold mb-4" style={{ color: "var(--text-primary)" }}>Agent Performance</h2>
            <div className="rounded-2xl overflow-hidden" style={{ border: "1px solid var(--border-color)", background: "var(--bg-card)" }}>
              <table className="w-full">
                <thead>
                  <tr style={{ background: "var(--bg-tertiary)" }}>
                    <th className="text-left px-6 py-3 text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>Agent</th>
                    <th className="text-left px-6 py-3 text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>Status</th>
                    <th className="text-left px-6 py-3 text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>Total Calls</th>
                    <th className="text-left px-6 py-3 text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>Avg Duration</th>
                  </tr>
                </thead>
                <tbody>
                  {["Planner", "Memory", "Research", "Coding", "Browser", "File", "Notes", "Tasks"].map((name) => {
                    const metrics = agentMetrics.find((m) => m.agent.toLowerCase() === name.toLowerCase());
                    const calls = metrics?.total_calls || 0;
                    const duration = metrics?.avg_duration_ms
                      ? `${(metrics.avg_duration_ms / 1000).toFixed(2)}s`
                      : "—";

                    return (
                      <tr key={name} className="transition-colors border-t border-[var(--border-color)]">
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <span className="text-lg">{getAgentIcon(name)}</span>
                            <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>{name} Agent</span>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium" style={{
                            background: "rgba(16,185,129,0.15)",
                            color: "var(--success)",
                          }}>
                            <span className="w-1.5 h-1.5 rounded-full" style={{ background: "var(--success)" }} />
                            Active
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm" style={{ color: "var(--text-secondary)" }}>{calls}</td>
                        <td className="px-6 py-4 text-sm" style={{ color: "var(--text-secondary)" }}>{duration}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>

          {/* Recent Logs */}
          <section>
            <h2 className="text-lg font-semibold mb-4" style={{ color: "var(--text-primary)" }}>Recent Execution Logs</h2>
            <div className="rounded-2xl overflow-hidden border border-[var(--border-color)]" style={{ background: "var(--bg-card)" }}>
              {isLoading ? (
                <div className="p-6 text-center text-sm" style={{ color: "var(--text-muted)" }}>Loading logs...</div>
              ) : logs.length === 0 ? (
                <div className="p-6 text-center text-sm" style={{ color: "var(--text-muted)" }}>No log records found. Logs will populate as you prompt Uday AI.</div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr style={{ background: "var(--bg-tertiary)" }}>
                        <th className="text-left px-6 py-3 text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>Time</th>
                        <th className="text-left px-6 py-3 text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>Agent</th>
                        <th className="text-left px-6 py-3 text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>Action</th>
                        <th className="text-left px-6 py-3 text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>Status</th>
                        <th className="text-left px-6 py-3 text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>Latency</th>
                      </tr>
                    </thead>
                    <tbody>
                      {logs.map((log) => (
                        <tr key={log.id} className="border-t border-[var(--border-color)] text-xs">
                          <td className="px-6 py-3.5" style={{ color: "var(--text-muted)" }}>
                            {new Date(log.created_at).toLocaleTimeString()}
                          </td>
                          <td className="px-6 py-3.5 font-semibold" style={{ color: "var(--text-primary)" }}>
                            {getAgentIcon(log.agent_name)} {log.agent_name}
                          </td>
                          <td className="px-6 py-3.5 font-mono max-w-[200px] truncate" style={{ color: "var(--text-secondary)" }}>
                            {log.action}
                          </td>
                          <td className="px-6 py-3.5">
                            <span className="px-2 py-0.5 rounded-full font-bold" style={{
                              background: log.status === "success" ? "rgba(16,185,129,0.15)" : "rgba(239,68,68,0.15)",
                              color: log.status === "success" ? "var(--success)" : "var(--error)",
                            }}>
                              {log.status.toUpperCase()}
                            </span>
                          </td>
                          <td className="px-6 py-3.5" style={{ color: "var(--text-muted)" }}>
                            {log.duration_ms}ms
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
