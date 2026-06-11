"use client";

/**
 * Uday AI — Sidebar Component
 *
 * Main navigation sidebar with glassmorphism design.
 */

import Link from "next/link";
import { usePathname } from "next/navigation";
import useAuth from "@/hooks/useAuth";

const NAV_ITEMS = [
  { name: "Dashboard", href: "/", icon: "🏠" },
  { name: "Chat", href: "/chat", icon: "💬" },
  { name: "Memory", href: "/memory", icon: "🧠" },
  { name: "Files", href: "/files", icon: "📁" },
  { name: "Research", href: "/research", icon: "🔍" },
  { name: "Tasks", href: "/tasks", icon: "✅" },
  { name: "Notes", href: "/notes", icon: "📝" },
  { name: "Calendar", href: "/calendar", icon: "📅" },
  { name: "Gmail", href: "/gmail", icon: "📧" },
];

const BOTTOM_ITEMS = [
  { name: "Admin", href: "/admin", icon: "⚙️" },
  { name: "Settings", href: "/settings", icon: "🔧" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth(false);

  const initials = user?.name ? user.name.slice(0, 2).toUpperCase() : "U";

  return (
    <aside
      className="fixed left-0 top-0 bottom-0 z-40 flex flex-col glass-strong"
      style={{ width: "var(--sidebar-width)" }}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 py-5 border-b border-[var(--border-color)]">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center text-lg font-bold"
          style={{ background: "var(--gradient-primary)" }}
        >
          {initials[0]}
        </div>
        <div>
          <h1 className="text-lg font-bold gradient-text">Uday AI</h1>
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            Personal AI OS
          </p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href || 
            (item.href !== "/" && pathname.startsWith(item.href));

          return (
            <Link
              key={item.href}
              href={item.href}
              className="flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200"
              style={{
                background: isActive ? "var(--accent-primary)" : "transparent",
                color: isActive ? "white" : "var(--text-secondary)",
                boxShadow: isActive ? "var(--shadow-glow)" : "none",
              }}
              onMouseEnter={(e) => {
                if (!isActive) {
                  e.currentTarget.style.background = "var(--bg-hover)";
                  e.currentTarget.style.color = "var(--text-primary)";
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive) {
                  e.currentTarget.style.background = "transparent";
                  e.currentTarget.style.color = "var(--text-secondary)";
                }
              }}
            >
              <span className="text-lg">{item.icon}</span>
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* Bottom Section */}
      <div className="px-3 py-4 space-y-1 border-t border-[var(--border-color)]">
        {BOTTOM_ITEMS.map((item) => {
          const isActive = pathname.startsWith(item.href);

          return (
            <Link
              key={item.href}
              href={item.href}
              className="flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200"
              style={{
                background: isActive ? "var(--bg-hover)" : "transparent",
                color: isActive ? "var(--text-primary)" : "var(--text-muted)",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "var(--bg-hover)";
                e.currentTarget.style.color = "var(--text-primary)";
              }}
              onMouseLeave={(e) => {
                if (!isActive) {
                  e.currentTarget.style.background = "transparent";
                  e.currentTarget.style.color = "var(--text-muted)";
                }
              }}
            >
              <span className="text-lg">{item.icon}</span>
              <span>{item.name}</span>
            </Link>
          );
        })}

        {/* User Profile */}
        <div className="flex items-center gap-3 px-4 py-3 mt-2 rounded-xl group relative" style={{ background: "var(--bg-tertiary)" }}>
          <div
            className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold"
            style={{ background: "var(--gradient-primary)" }}
          >
            {initials}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate" style={{ color: "var(--text-primary)" }}>
              {user?.nickname || user?.name || "Uday"}
            </p>
            <p className="text-xs truncate" style={{ color: "var(--text-muted)" }}>
              {user ? "Online" : "Loading..."}
            </p>
          </div>
          {user && (
            <button
              onClick={logout}
              title="Logout"
              className="text-xs opacity-0 group-hover:opacity-100 transition-opacity p-1.5 hover:bg-[var(--bg-hover)] rounded-lg"
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
