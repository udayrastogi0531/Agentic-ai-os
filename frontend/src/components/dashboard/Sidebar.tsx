"use client";

/**
 * Nidhi AI OS — Sidebar Navigation
 * Premium glassmorphic sidebar with Nidhi persona branding.
 */

import Link from "next/link";
import { usePathname } from "next/navigation";
import useAuth from "@/hooks/useAuth";
import { useState } from "react";

const NAV_ITEMS = [
  { name: "Home",       href: "/",          icon: "✦",  emoji: "🏠" },
  { name: "Chat",       href: "/chat",       icon: "◈",  emoji: "💬" },
  { name: "Voice",      href: "/voice",      icon: "◉",  emoji: "🎙️" },
  { name: "Memory",     href: "/memory",     icon: "◎",  emoji: "🧠" },
  { name: "Knowledge",  href: "/files",      icon: "◐",  emoji: "📚" },
  { name: "Research",   href: "/research",   icon: "◑",  emoji: "🔍" },
  { name: "Tasks",      href: "/tasks",      icon: "◧",  emoji: "✅" },
  { name: "Calendar",   href: "/calendar",   icon: "◫",  emoji: "📅" },
  { name: "Gmail",      href: "/gmail",      icon: "◬",  emoji: "📧" },
  { name: "Notes",      href: "/notes",      icon: "◭",  emoji: "📝" },
  { name: "Agents",     href: "/agents",     icon: "🤖",  emoji: "🤖" },
  { name: "Jobs",       href: "/jobs",       icon: "💼",  emoji: "💼" },
  { name: "Resume",     href: "/resume",     icon: "📄",  emoji: "📄" },
  { name: "Profile",    href: "/profile",    icon: "👤",  emoji: "👤" },
];

const BOTTOM_ITEMS = [
  { name: "Settings",   href: "/settings",   emoji: "⚙️" },
  { name: "Admin",      href: "/admin",      emoji: "🛡️" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth(false);
  const [hoveredItem, setHoveredItem] = useState<string | null>(null);

  const initials = user?.name ? user.name.slice(0, 2).toUpperCase() : "UN";

  return (
    <aside
      className="fixed left-0 top-0 bottom-0 z-40 flex flex-col"
      style={{
        width: "var(--sidebar-width)",
        background: "rgba(8, 8, 20, 0.95)",
        backdropFilter: "blur(32px)",
        borderRight: "1px solid rgba(124, 107, 255, 0.1)",
      }}
    >
      {/* Nidhi Brand Logo */}
      <div
        className="flex items-center gap-3 px-5 py-5"
        style={{ borderBottom: "1px solid rgba(124, 107, 255, 0.08)" }}
      >
        {/* Animated Orb Logo */}
        <div
          className="relative w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0"
          style={{
            background: "linear-gradient(135deg, #7c6bff, #a855f7, #e879f9)",
            boxShadow: "0 0 20px rgba(124, 107, 255, 0.5), 0 0 40px rgba(124, 107, 255, 0.2)",
            animation: "breathe 4s ease-in-out infinite",
          }}
        >
          <span style={{ fontSize: "1rem" }}>✦</span>
          {/* Pulse ring */}
          <span
            className="absolute inset-0 rounded-full"
            style={{
              border: "1px solid rgba(124, 107, 255, 0.4)",
              animation: "ripple 3s ease-out infinite",
            }}
          />
        </div>
        <div>
          <h1
            className="font-bold leading-tight"
            style={{
              fontFamily: "var(--font-display)",
              fontSize: "1.1rem",
              background: "linear-gradient(135deg, #c4b5fd 0%, #e879f9 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
            }}
          >
            Nidhi AI
          </h1>
          <p className="text-xs" style={{ color: "var(--text-muted)", letterSpacing: "0.06em" }}>
            Your AI Companion
          </p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-0.5 no-scrollbar">
        {NAV_ITEMS.map((item) => {
          const isActive =
            pathname === item.href ||
            (item.href !== "/" && pathname.startsWith(item.href));

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`sidebar-nav-item ${isActive ? "active" : ""}`}
              onMouseEnter={() => setHoveredItem(item.href)}
              onMouseLeave={() => setHoveredItem(null)}
            >
              <span
                className="flex-shrink-0 text-base transition-all duration-200"
                style={{
                  opacity: isActive ? 1 : hoveredItem === item.href ? 0.9 : 0.5,
                }}
              >
                {item.emoji}
              </span>
              <span className="flex-1 truncate">{item.name}</span>
              {isActive && (
                <span
                  className="ml-auto w-1.5 h-1.5 rounded-full flex-shrink-0"
                  style={{ background: "var(--accent-primary)" }}
                />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Bottom Section */}
      <div
        className="px-3 py-3 space-y-0.5"
        style={{ borderTop: "1px solid rgba(124, 107, 255, 0.08)" }}
      >
        {/* CMD+K Hint */}
        <div
          className="flex items-center justify-between px-3 py-2 mb-2 rounded-xl cursor-pointer transition-all"
          style={{
            background: "rgba(124, 107, 255, 0.06)",
            border: "1px solid rgba(124, 107, 255, 0.12)",
          }}
          onClick={() => {
            window.dispatchEvent(new KeyboardEvent("keydown", { key: "k", ctrlKey: true }));
          }}
        >
          <span className="text-xs" style={{ color: "var(--text-muted)" }}>
            Command Center
          </span>
          <div className="flex gap-1">
            <span className="kbd">Ctrl</span>
            <span className="kbd">K</span>
          </div>
        </div>

        {BOTTOM_ITEMS.map((item) => {
          const isActive = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`sidebar-nav-item ${isActive ? "active" : ""}`}
            >
              <span className="text-base opacity-60">{item.emoji}</span>
              <span>{item.name}</span>
            </Link>
          );
        })}

        {/* User Profile */}
        <div
          className="group flex items-center gap-3 px-3 py-3 mt-1 rounded-xl transition-all cursor-pointer relative"
          style={{
            background: "rgba(124, 107, 255, 0.05)",
            border: "1px solid rgba(124, 107, 255, 0.08)",
          }}
        >
          <div
            className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
            style={{
              background: "linear-gradient(135deg, #7c6bff, #a855f7)",
              boxShadow: "0 0 12px rgba(124, 107, 255, 0.3)",
            }}
          >
            {initials}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate" style={{ color: "var(--text-primary)" }}>
              {user?.nickname || user?.name || "Uday"}
            </p>
            <p className="text-xs truncate" style={{ color: "var(--text-muted)" }}>
              <span
                className="inline-block w-1.5 h-1.5 rounded-full mr-1.5 mb-px"
                style={{ background: "var(--success)", boxShadow: "0 0 6px var(--success)" }}
              />
              Online
            </p>
          </div>
          {user && (
            <button
              onClick={logout}
              title="Logout"
              className="text-xs opacity-0 group-hover:opacity-100 transition-all p-1.5 rounded-lg hover:bg-red-500/10"
              style={{ color: "var(--error)" }}
            >
              🚪
            </button>
          )}
        </div>
      </div>
    </aside>
  );
}
