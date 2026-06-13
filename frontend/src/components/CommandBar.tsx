"use client";

/**
 * Nidhi AI OS — Global Command Bar (CTRL + K)
 *
 * A spotlight-style portal to dispatch natural language commands
 * to Nidhi's specialized agents.
 */

import { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";

interface CommandBarProps {
  isOpen: boolean;
  onClose: () => void;
}

/* ── Quick navigation commands ─────────── */
const NAV_COMMANDS = [
  { id: "chat",      icon: "💬", label: "Go to Chat",           action: "/chat",      category: "Navigate" },
  { id: "voice",     icon: "🎙️", label: "Open Voice Mode",      action: "/voice",     category: "Navigate" },
  { id: "memory",    icon: "🧠", label: "View My Memory",       action: "/memory",    category: "Navigate" },
  { id: "research",  icon: "🔍", label: "Start Research",       action: "/research",  category: "Navigate" },
  { id: "tasks",     icon: "✅", label: "My Tasks",             action: "/tasks",     category: "Navigate" },
  { id: "calendar",  icon: "📅", label: "Calendar",             action: "/calendar",  category: "Navigate" },
  { id: "gmail",     icon: "📧", label: "Gmail",                action: "/gmail",     category: "Navigate" },
  { id: "knowledge", icon: "📚", label: "Knowledge Base",       action: "/files",     category: "Navigate" },
  { id: "settings",  icon: "⚙️", label: "Settings",             action: "/settings",  category: "Navigate" },
];

const AGENT_COMMANDS = [
  { id: "ask-nidhi",    icon: "✦",  label: "Ask Nidhi...",              action: "chat",     category: "Agent" },
  { id: "research-web", icon: "🔍", label: "Research on the web...",    action: "research", category: "Agent" },
  { id: "write-email",  icon: "📧", label: "Write & send email...",     action: "gmail",    category: "Agent" },
  { id: "create-task",  icon: "✅", label: "Create a new task...",      action: "tasks",    category: "Agent" },
  { id: "schedule",     icon: "📅", label: "Schedule a meeting...",     action: "calendar", category: "Agent" },
  { id: "write-code",   icon: "💻", label: "Write code for me...",      action: "chat",     category: "Agent" },
];

const ALL_COMMANDS = [...AGENT_COMMANDS, ...NAV_COMMANDS];

export default function CommandBar({ isOpen, onClose }: CommandBarProps) {
  const router = useRouter();
  const [query, setQuery]   = useState("");
  const [selected, setSelected] = useState(0);
  const inputRef  = useRef<HTMLInputElement>(null);
  const listRef   = useRef<HTMLDivElement>(null);

  // Filter commands by query
  const filtered = query.trim().length > 0
    ? ALL_COMMANDS.filter((c) =>
        c.label.toLowerCase().includes(query.toLowerCase()) ||
        c.category.toLowerCase().includes(query.toLowerCase())
      )
    : ALL_COMMANDS;

  // Focus input when opening
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 60);
      setQuery("");
      setSelected(0);
    }
  }, [isOpen]);

  // Keyboard navigation
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelected((s) => Math.min(s + 1, filtered.length - 1));
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelected((s) => Math.max(s - 1, 0));
      } else if (e.key === "Enter") {
        e.preventDefault();
        const cmd = filtered[selected];
        if (cmd) executeCommand(cmd);
      } else if (e.key === "Escape") {
        onClose();
      }
    },
    [filtered, selected, onClose]
  );

  // Scroll selected into view
  useEffect(() => {
    const el = listRef.current?.querySelector(`[data-idx="${selected}"]`) as HTMLElement;
    el?.scrollIntoView({ block: "nearest" });
  }, [selected]);

  const executeCommand = (cmd: (typeof ALL_COMMANDS)[number]) => {
    onClose();
    if (cmd.category === "Navigate") {
      router.push(cmd.action as string);
    } else {
      // Navigate to relevant page with prefilled query
      const q = query.trim() || cmd.label.replace("...", "");
      const map: Record<string, string> = {
        chat:     `/chat?q=${encodeURIComponent(q)}`,
        research: `/research?q=${encodeURIComponent(q)}`,
        gmail:    `/gmail?compose=1&subject=${encodeURIComponent(q)}`,
        tasks:    `/tasks?new=${encodeURIComponent(q)}`,
        calendar: `/calendar?new=${encodeURIComponent(q)}`,
      };
      router.push(map[cmd.action as string] || `/chat?q=${encodeURIComponent(q)}`);
    }
  };

  // Quick freeform "chat" if user types & hits enter without selecting
  const handleFreeformSubmit = () => {
    if (!query.trim()) return;
    onClose();
    router.push(`/chat?q=${encodeURIComponent(query.trim())}`);
  };

  if (!isOpen) return null;

  // Group filtered commands by category
  const grouped = filtered.reduce<Record<string, typeof ALL_COMMANDS>>((acc, cmd) => {
    if (!acc[cmd.category]) acc[cmd.category] = [];
    acc[cmd.category].push(cmd);
    return acc;
  }, {});

  let flatIdx = 0;

  return (
    <div
      className="cmdbar-overlay"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
      role="dialog"
      aria-modal="true"
      aria-label="Command Center"
    >
      <div className="cmdbar-modal">
        {/* Input Row */}
        <div
          className="flex items-center gap-3 px-5 py-4"
          style={{ borderBottom: "1px solid rgba(124, 107, 255, 0.1)" }}
        >
          <span style={{ fontSize: "1.1rem", color: "var(--accent-primary)" }}>✦</span>
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => { setQuery(e.target.value); setSelected(0); }}
            onKeyDown={handleKeyDown}
            placeholder="Ask Nidhi anything, or navigate…"
            className="flex-1 bg-transparent outline-none"
            style={{
              color: "var(--text-primary)",
              fontSize: "1rem",
              fontFamily: "var(--font-sans)",
            }}
            autoComplete="off"
            spellCheck={false}
          />
          {query && (
            <button
              onClick={() => setQuery("")}
              className="text-xs px-2 py-1 rounded-lg transition-all"
              style={{
                color: "var(--text-muted)",
                background: "rgba(255,255,255,0.04)",
              }}
            >
              Clear
            </button>
          )}
          <span className="kbd hidden sm:flex">Esc</span>
        </div>

        {/* Results list */}
        <div
          ref={listRef}
          className="overflow-y-auto"
          style={{ maxHeight: "380px" }}
        >
          {filtered.length === 0 ? (
            <div className="flex flex-col items-center py-12 gap-2">
              <span className="text-3xl">🔍</span>
              <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                No commands found
              </p>
              {query.trim() && (
                <button
                  className="btn-nidhi text-xs mt-2 py-1.5 px-4"
                  onClick={handleFreeformSubmit}
                >
                  Ask Nidhi: "{query}"
                </button>
              )}
            </div>
          ) : (
            Object.entries(grouped).map(([category, cmds]) => (
              <div key={category} className="py-1">
                <p
                  className="px-5 py-2 text-xs font-semibold uppercase tracking-widest"
                  style={{ color: "var(--text-muted)" }}
                >
                  {category}
                </p>
                {cmds.map((cmd) => {
                  const idx = flatIdx++;
                  const isSelected = selected === idx;
                  return (
                    <button
                      key={cmd.id}
                      data-idx={idx}
                      className="w-full flex items-center gap-4 px-5 py-3 text-left transition-all"
                      style={{
                        background: isSelected
                          ? "rgba(124, 107, 255, 0.12)"
                          : "transparent",
                        color: isSelected ? "var(--text-primary)" : "var(--text-secondary)",
                        borderLeft: isSelected
                          ? "2px solid var(--accent-primary)"
                          : "2px solid transparent",
                      }}
                      onMouseEnter={() => setSelected(idx)}
                      onClick={() => executeCommand(cmd)}
                    >
                      <span className="text-lg flex-shrink-0">{cmd.icon}</span>
                      <span className="flex-1 text-sm font-medium">{cmd.label}</span>
                      {isSelected && (
                        <span className="flex items-center gap-1">
                          <span className="kbd">↵</span>
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            ))
          )}

          {/* Freeform ask Nidhi */}
          {query.trim() && (
            <div
              className="mx-4 mb-4 mt-2 rounded-xl overflow-hidden"
              style={{
                border: "1px solid rgba(124, 107, 255, 0.2)",
              }}
            >
              <button
                className="w-full flex items-center gap-4 px-4 py-3 transition-all"
                style={{ background: "rgba(124, 107, 255, 0.08)" }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "rgba(124, 107, 255, 0.15)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "rgba(124, 107, 255, 0.08)";
                }}
                onClick={handleFreeformSubmit}
              >
                <span className="text-lg">✦</span>
                <span className="text-sm" style={{ color: "var(--text-secondary)" }}>
                  Ask Nidhi: <strong style={{ color: "var(--text-primary)" }}>"{query}"</strong>
                </span>
                <span className="ml-auto text-xs" style={{ color: "var(--accent-tertiary)" }}>
                  Chat →
                </span>
              </button>
            </div>
          )}
        </div>

        {/* Footer */}
        <div
          className="flex items-center justify-between px-5 py-3"
          style={{
            borderTop: "1px solid rgba(124, 107, 255, 0.08)",
            background: "rgba(0,0,0,0.2)",
          }}
        >
          <div className="flex items-center gap-3 text-xs" style={{ color: "var(--text-muted)" }}>
            <span><span className="kbd">↑↓</span> Navigate</span>
            <span><span className="kbd">↵</span> Select</span>
            <span><span className="kbd">Esc</span> Close</span>
          </div>
          <span
            className="text-xs font-medium"
            style={{
              background: "var(--gradient-primary)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
            }}
          >
            ✦ Nidhi
          </span>
        </div>
      </div>
    </div>
  );
}
