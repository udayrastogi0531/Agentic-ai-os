"use client";

/**
 * Nidhi AI OS — Agents Console
 *
 * Visual command center for all 12 Nidhi agents.
 * Click any agent → send it a natural language command.
 * See live execution logs.
 */

import { useState, useEffect, useRef } from "react";
import Sidebar from "@/components/dashboard/Sidebar";
import api from "@/lib/api";
import useAuth from "@/hooks/useAuth";

const AGENTS = [
  {
    key: "planner",
    name: "Planner",
    emoji: "🧠",
    description: "Plans tasks, breaks goals into steps, coordinates other agents",
    color: "#7c6bff",
    examples: ["Plan my week", "Break down my AI project", "Create a study schedule"],
  },
  {
    key: "research",
    name: "Research",
    emoji: "🔍",
    description: "Searches the web, reads articles, summarizes findings",
    color: "#6ee7f7",
    examples: ["Research LangGraph", "Compare Next.js vs Remix", "Find AI papers on RAG"],
  },
  {
    key: "coding",
    name: "Coding",
    emoji: "💻",
    description: "Generates, reviews, and debugs code across any language",
    color: "#10b981",
    examples: ["Write a FastAPI endpoint", "Debug this Python error", "Review my React component"],
  },
  {
    key: "browser",
    name: "Browser",
    emoji: "🌐",
    description: "Controls Chrome to navigate, click, fill forms, extract data",
    color: "#f59e0b",
    examples: ["Open LinkedIn", "Search YouTube for LangGraph tutorial", "Scrape job listings"],
  },
  {
    key: "computer",
    name: "Computer",
    emoji: "🖥️",
    description: "Opens apps, runs commands, manages files on your PC",
    color: "#e879f9",
    examples: ["Open VS Code", "Open my AI project folder", "Run npm run dev"],
    requiresApproval: true,
  },
  {
    key: "memory",
    name: "Memory",
    emoji: "🧬",
    description: "Stores and retrieves long-term memories about you",
    color: "#f87171",
    examples: ["Remember I prefer dark mode", "What do you know about my goals?", "Forget my old email"],
  },
  {
    key: "calendar",
    name: "Calendar",
    emoji: "📅",
    description: "Manages Google Calendar — creates events, checks schedule",
    color: "#34d399",
    examples: ["Show today's schedule", "Add meeting tomorrow at 3pm", "Block 2 hours for coding"],
  },
  {
    key: "email",
    name: "Email (Gmail)",
    emoji: "📧",
    description: "Reads, summarizes, and sends Gmail emails",
    color: "#60a5fa",
    examples: ["Show unread emails", "Summarize inbox", "Draft reply to last email"],
    requiresApproval: true,
  },
  {
    key: "file",
    name: "File",
    emoji: "📁",
    description: "Reads, creates, moves, and organizes files on your computer",
    color: "#fbbf24",
    examples: ["Read README.md", "List files in my projects folder", "Create notes/ideas.md"],
  },
  {
    key: "task",
    name: "Tasks",
    emoji: "✅",
    description: "Creates, updates, and manages your to-do tasks",
    color: "#a78bfa",
    examples: ["Add task: finish resume", "Show pending tasks", "Complete task 'setup Nidhi'"],
  },
  {
    key: "job",
    name: "Job Agent",
    emoji: "💼",
    description: "Searches jobs, matches resume, generates cover letters",
    color: "#fb923c",
    examples: ["Find AI intern jobs", "Match my resume to this JD", "Generate cover letter for Google"],
  },
  {
    key: "resume",
    name: "Resume",
    emoji: "📄",
    description: "Analyzes resume, improves it, generates LinkedIn content",
    color: "#f472b6",
    examples: ["Analyze my resume", "Improve resume for AI roles", "Generate LinkedIn summary"],
  },
];

interface AgentCardProps {
  agent: typeof AGENTS[0];
  isActive: boolean;
  onSelect: () => void;
}

function AgentCard({ agent, isActive, onSelect }: AgentCardProps) {
  return (
    <button
      onClick={onSelect}
      className="rounded-2xl p-4 text-left transition-all duration-200 hover:scale-105"
      style={{
        background: isActive
          ? `${agent.color}18`
          : "rgba(17,17,40,0.7)",
        border: `1px solid ${isActive ? agent.color + "44" : "rgba(124,107,255,0.08)"}`,
        backdropFilter: "blur(12px)",
      }}
    >
      <div className="flex items-center gap-3 mb-2">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center text-xl"
          style={{ background: `${agent.color}18`, border: `1px solid ${agent.color}33` }}
        >
          {agent.emoji}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold" style={{ color: isActive ? agent.color : "var(--text-primary)" }}>
            {agent.name}
          </p>
          {agent.requiresApproval && (
            <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ background: "rgba(245,158,11,0.15)", color: "#f59e0b" }}>
              Needs Approval
            </span>
          )}
        </div>
        <div
          className="w-2 h-2 rounded-full"
          style={{ background: isActive ? agent.color : "rgba(255,255,255,0.1)" }}
        />
      </div>
      <p className="text-xs leading-relaxed" style={{ color: "var(--text-muted)" }}>
        {agent.description}
      </p>
    </button>
  );
}

export default function AgentsPage() {
  useAuth();
  const [selectedAgent, setSelectedAgent] = useState<typeof AGENTS[0] | null>(null);
  const [command, setCommand]   = useState("");
  const [running, setRunning]   = useState(false);
  const [logs, setLogs]         = useState<{ role: string; text: string; time: string }[]>([]);
  const [filterKey, setFilterKey] = useState("");
  const logsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const addLog = (role: string, text: string) => {
    setLogs((prev) => [...prev, { role, text, time: new Date().toLocaleTimeString() }]);
  };

  const handleRun = async () => {
    if (!command.trim() || !selectedAgent || running) return;
    setRunning(true);
    addLog("user", command);
    const cmd = command;
    setCommand("");

    try {
      // Route to chat with agent prefix
      const agentCommand = `[${selectedAgent.name} Agent] ${cmd}`;
      const ws = new WebSocket(`ws://localhost:8000/ws/chat?token=${localStorage.getItem("access_token") || ""}`);

      ws.onopen = () => {
        ws.send(JSON.stringify({ content: agentCommand, conversation_id: null }));
      };

      let response = "";
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "token") {
            response += data.content;
          } else if (data.type === "done" || data.type === "complete") {
            if (response) addLog("nidhi", response);
            ws.close();
            setRunning(false);
          } else if (data.type === "agent_status") {
            addLog("status", data.content);
          } else if (data.type === "error") {
            addLog("error", data.content || "An error occurred");
            ws.close();
            setRunning(false);
          }
        } catch {}
      };

      ws.onerror = () => {
        addLog("error", "Connection error. Is the backend running?");
        setRunning(false);
      };

      ws.onclose = () => {
        if (running) setRunning(false);
      };

    } catch (e: any) {
      addLog("error", `Failed: ${e.message}`);
      setRunning(false);
    }
  };

  const filteredAgents = filterKey
    ? AGENTS.filter((a) => a.name.toLowerCase().includes(filterKey.toLowerCase()))
    : AGENTS;

  return (
    <>
      <div className="aurora-bg" aria-hidden />
      <div className="flex min-h-screen" style={{ background: "var(--bg-primary)" }}>
        <Sidebar />
        <main className="flex-1 overflow-y-auto relative" style={{ marginLeft: "var(--sidebar-width)", zIndex: 1 }}>
          {/* Header */}
          <header
            className="sticky top-0 z-30 glass-strong px-8 py-5"
            style={{ borderBottom: "1px solid rgba(124,107,255,0.08)" }}
          >
            <h1
              className="text-2xl font-bold"
              style={{ color: "var(--text-primary)", fontFamily: "var(--font-display)" }}
            >
              🤖 Agent Console
            </h1>
            <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
              {AGENTS.length} specialized agents ready to help you
            </p>
          </header>

          <div className="flex h-[calc(100vh-80px)]">
            {/* Left: Agent Grid */}
            <div
              className="w-80 flex-shrink-0 overflow-y-auto p-4 space-y-3"
              style={{ borderRight: "1px solid rgba(124,107,255,0.08)" }}
            >
              {/* Filter */}
              <input
                value={filterKey}
                onChange={(e) => setFilterKey(e.target.value)}
                placeholder="Filter agents…"
                className="w-full bg-transparent text-xs px-3 py-2 rounded-xl outline-none mb-2"
                style={{ border: "1px solid rgba(124,107,255,0.15)", color: "var(--text-primary)" }}
              />
              {filteredAgents.map((agent) => (
                <AgentCard
                  key={agent.key}
                  agent={agent}
                  isActive={selectedAgent?.key === agent.key}
                  onSelect={() => {
                    setSelectedAgent(agent);
                    setCommand("");
                  }}
                />
              ))}
            </div>

            {/* Right: Command + Logs */}
            <div className="flex-1 flex flex-col">
              {selectedAgent ? (
                <>
                  {/* Agent header */}
                  <div
                    className="px-6 py-4 flex items-center gap-3"
                    style={{ borderBottom: "1px solid rgba(124,107,255,0.08)" }}
                  >
                    <span className="text-2xl">{selectedAgent.emoji}</span>
                    <div>
                      <h2 className="text-base font-bold" style={{ color: "var(--text-primary)" }}>
                        {selectedAgent.name} Agent
                      </h2>
                      <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                        {selectedAgent.description}
                      </p>
                    </div>
                    {selectedAgent.requiresApproval && (
                      <span
                        className="ml-auto text-xs px-2.5 py-1 rounded-full"
                        style={{ background: "rgba(245,158,11,0.15)", border: "1px solid rgba(245,158,11,0.3)", color: "#f59e0b" }}
                      >
                        ⚠️ Requires your approval for sensitive actions
                      </span>
                    )}
                  </div>

                  {/* Log area */}
                  <div className="flex-1 overflow-y-auto p-6 space-y-3">
                    {logs.length === 0 && (
                      <div className="flex flex-col items-center justify-center h-full gap-4">
                        <span className="text-5xl">{selectedAgent.emoji}</span>
                        <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                          Try asking the {selectedAgent.name} agent:
                        </p>
                        <div className="space-y-2">
                          {selectedAgent.examples.map((ex) => (
                            <button
                              key={ex}
                              onClick={() => setCommand(ex)}
                              className="block w-full text-left text-xs px-4 py-2 rounded-xl transition-all hover:scale-105"
                              style={{
                                background: "rgba(124,107,255,0.06)",
                                border: "1px solid rgba(124,107,255,0.12)",
                                color: "var(--text-muted)",
                              }}
                            >
                              &quot;{ex}&quot;
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {logs.map((log, i) => (
                      <div
                        key={i}
                        className={`flex ${log.role === "user" ? "justify-end" : "justify-start"}`}
                      >
                        <div
                          className="max-w-[80%] rounded-2xl px-4 py-3 text-xs"
                          style={{
                            background:
                              log.role === "user" ? "rgba(124,107,255,0.2)" :
                              log.role === "error" ? "rgba(248,113,113,0.15)" :
                              log.role === "status" ? "rgba(245,158,11,0.1)" :
                              "rgba(17,17,40,0.9)",
                            border: `1px solid ${
                              log.role === "user" ? "rgba(124,107,255,0.3)" :
                              log.role === "error" ? "rgba(248,113,113,0.3)" :
                              log.role === "status" ? "rgba(245,158,11,0.2)" :
                              "rgba(124,107,255,0.1)"
                            }`,
                            color:
                              log.role === "error" ? "#f87171" :
                              log.role === "status" ? "#f59e0b" :
                              "var(--text-primary)",
                          }}
                        >
                          {log.role === "status" && <span className="font-medium">⚡ {log.text}</span>}
                          {log.role === "error" && <span>⚠️ {log.text}</span>}
                          {log.role !== "status" && log.role !== "error" && (
                            <pre className="whitespace-pre-wrap font-sans leading-relaxed">{log.text}</pre>
                          )}
                          <div className="text-[10px] mt-1 opacity-40 text-right">{log.time}</div>
                        </div>
                      </div>
                    ))}

                    {running && (
                      <div className="flex justify-start">
                        <div
                          className="rounded-2xl px-4 py-3 flex items-center gap-2"
                          style={{ background: "rgba(17,17,40,0.9)", border: "1px solid rgba(124,107,255,0.1)" }}
                        >
                          <div className="typing-indicator flex gap-1">
                            <span /> <span /> <span />
                          </div>
                          <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                            {selectedAgent.name} is working…
                          </span>
                        </div>
                      </div>
                    )}
                    <div ref={logsEndRef} />
                  </div>

                  {/* Command input */}
                  <div
                    className="p-4"
                    style={{ borderTop: "1px solid rgba(124,107,255,0.08)" }}
                  >
                    <div className="flex gap-3">
                      <input
                        value={command}
                        onChange={(e) => setCommand(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && handleRun()}
                        placeholder={`Tell ${selectedAgent.name} agent what to do…`}
                        className="flex-1 bg-transparent text-sm px-4 py-2.5 rounded-xl outline-none"
                        style={{
                          background: "rgba(17,17,40,0.8)",
                          border: "1px solid rgba(124,107,255,0.15)",
                          color: "var(--text-primary)",
                        }}
                      />
                      <button
                        onClick={handleRun}
                        disabled={!command.trim() || running}
                        className="btn-nidhi px-5"
                      >
                        {running ? "✦" : "▶ Run"}
                      </button>
                      {logs.length > 0 && (
                        <button
                          onClick={() => setLogs([])}
                          className="text-xs px-3 rounded-xl transition-all"
                          style={{ background: "rgba(124,107,255,0.05)", border: "1px solid rgba(124,107,255,0.1)", color: "var(--text-muted)" }}
                        >
                          Clear
                        </button>
                      )}
                    </div>
                  </div>
                </>
              ) : (
                <div className="flex flex-col items-center justify-center h-full gap-4">
                  <div
                    className="w-16 h-16 rounded-2xl flex items-center justify-center text-3xl"
                    style={{ background: "rgba(124,107,255,0.08)", border: "1px solid rgba(124,107,255,0.12)" }}
                  >
                    🤖
                  </div>
                  <h2 className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
                    Select an Agent
                  </h2>
                  <p className="text-sm text-center max-w-sm" style={{ color: "var(--text-muted)" }}>
                    Choose a specialized agent from the left panel to send it commands.
                    Nidhi will route your request and stream the response.
                  </p>
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </>
  );
}
