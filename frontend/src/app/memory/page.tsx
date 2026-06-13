"use client";

/**
 * Nidhi AI OS — Memory Bank
 *
 * What Nidhi knows about you. Profile memories grouped by category.
 */

import { useState, useEffect } from "react";
import Sidebar from "@/components/dashboard/Sidebar";
import useAuth from "@/hooks/useAuth";
import api from "@/lib/api";
import type { Memory } from "@/types";

const CATEGORIES = [
  { name: "All", key: "", icon: "📋" },
  { name: "Preferences", key: "preference", icon: "❤️" },
  { name: "Goals", key: "goal", icon: "🎯" },
  { name: "Facts", key: "fact", icon: "📌" },
  { name: "Events", key: "event", icon: "📅" },
  { name: "Relationships", key: "relationship", icon: "👥" },
  { name: "Habits", key: "habit", icon: "🔄" },
  { name: "Skills", key: "skill", icon: "⚡" },
];

export default function MemoryPage() {
  useAuth(); // Require authentication
  const [memories, setMemories] = useState<Memory[]>([]);
  const [selectedCategory, setSelectedCategory] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [newMemoryContent, setNewMemoryContent] = useState("");
  const [newMemoryCategory, setNewMemoryCategory] = useState("preference");
  const [newMemoryImportance, setNewMemoryImportance] = useState(3); // default 3
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);

  // Load memories
  const loadMemories = async () => {
    setIsLoading(true);
    try {
      if (searchQuery.trim()) {
        const results = (await api.searchMemories(
          searchQuery,
          selectedCategory || undefined
        )) as Memory[];
        setMemories(results);
      } else {
        const response = (await api.getMemories(
          selectedCategory || undefined
        )) as { memories: Memory[] };
        setMemories(response.memories || []);
      }
    } catch (err) {
      console.error("Failed to fetch memories:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadMemories();
  }, [selectedCategory, searchQuery]);

  // Handle Delete
  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want Nidhi to forget this memory?")) return;

    try {
      await api.deleteMemory(id);
      setMemories((prev) => prev.filter((m) => m.id !== id));
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to delete memory");
    }
  };

  // Handle Create
  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMemoryContent.trim()) return;

    setIsCreating(true);
    try {
      await api.createMemory(
        newMemoryContent,
        newMemoryCategory,
        newMemoryImportance
      );
      setNewMemoryContent("");
      setShowAddForm(false);
      await loadMemories();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to save memory");
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <>
      <div className="aurora-bg" aria-hidden />
    <div className="flex min-h-screen" style={{ background: "var(--bg-primary)" }}>
      <Sidebar />
      <main className="flex-1 relative" style={{ marginLeft: "var(--sidebar-width)", zIndex: 1 }}>
        <header className="sticky top-0 z-30 glass-strong px-8 py-5 flex items-center justify-between" style={{ borderBottom: "1px solid rgba(124, 107, 255, 0.1)" }}>
          <div>
            <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-display)" }}>🧠 My Memory</h1>
            <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>What Nidhi knows about you — her long-term memory</p>
          </div>
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="btn-nidhi"
          >
            ✦ Teach Nidhi
          </button>
        </header>

        <div className="px-8 py-6 space-y-6 animate-fade-in max-w-5xl">
          {/* Create Memory Form Modal/Accordion */}
          {showAddForm && (
            <form onSubmit={handleCreate} className="p-6 rounded-2xl border space-y-4 animate-fade-in" style={{ background: "var(--bg-card)", borderColor: "var(--border-color)" }}>
              <h3 className="font-semibold text-sm" style={{ color: "var(--text-primary)" }}>Record a New Memory</h3>
              <div className="space-y-3">
                <textarea
                  value={newMemoryContent}
                  onChange={(e) => setNewMemoryContent(e.target.value)}
                  placeholder="What would you like me to remember? (e.g. 'I prefer coding in Dark Mode')"
                  required
                  rows={2}
                  className="w-full rounded-xl px-4 py-3 text-sm outline-none resize-none"
                  style={{ background: "var(--bg-tertiary)", border: "1px solid var(--border-color)", color: "var(--text-primary)" }}
                />
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>Category</label>
                    <select
                      value={newMemoryCategory}
                      onChange={(e) => setNewMemoryCategory(e.target.value)}
                      className="w-full rounded-xl px-4 py-2 text-sm outline-none"
                      style={{ background: "var(--bg-tertiary)", border: "1px solid var(--border-color)", color: "var(--text-primary)" }}
                    >
                      {CATEGORIES.filter(c => c.key !== "").map(c => (
                        <option key={c.key} value={c.key}>{c.name}</option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>Importance (1-5)</label>
                    <input
                      type="number"
                      min={1}
                      max={5}
                      value={newMemoryImportance}
                      onChange={(e) => setNewMemoryImportance(Number(e.target.value))}
                      className="w-full rounded-xl px-4 py-2 text-sm outline-none"
                      style={{ background: "var(--bg-tertiary)", border: "1px solid var(--border-color)", color: "var(--text-primary)" }}
                    />
                  </div>
                </div>
              </div>
              <div className="flex gap-2 justify-end">
                <button
                  type="button"
                  onClick={() => setShowAddForm(false)}
                  className="px-4 py-2 rounded-xl text-sm"
                  style={{ color: "var(--text-secondary)" }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isCreating}
                  className="px-5 py-2 rounded-xl text-sm font-semibold text-white transition-all"
                  style={{ background: "var(--gradient-primary)", opacity: isCreating ? 0.7 : 1 }}
                >
                  {isCreating ? "Saving..." : "Save Memory"}
                </button>
              </div>
            </form>
          )}

          {/* Search Bar */}
          <div>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search memories semantically... (e.g. 'coding choices' or 'my goals')"
              className="w-full rounded-xl px-5 py-3 text-sm outline-none transition-all duration-200"
              style={{
                background: "var(--bg-tertiary)",
                border: "1px solid var(--border-color)",
                color: "var(--text-primary)",
              }}
              onFocus={(e) => { e.target.style.borderColor = "var(--accent-primary)"; }}
              onBlur={(e) => { e.target.style.borderColor = "var(--border-color)"; }}
            />
          </div>

          {/* Categories Tab Grid */}
          <div className="flex gap-2 overflow-x-auto pb-2 flex-wrap">
            {CATEGORIES.map((cat) => {
              const isActive = selectedCategory === cat.key;
              return (
                <button
                  key={cat.key}
                  onClick={() => setSelectedCategory(cat.key)}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-full text-xs font-semibold transition-all duration-200 border"
                  style={{
                    background: isActive ? "var(--accent-primary)" : "var(--bg-card)",
                    borderColor: isActive ? "var(--accent-primary)" : "var(--border-color)",
                    color: isActive ? "white" : "var(--text-secondary)",
                  }}
                >
                  <span>{cat.icon}</span>
                  <span>{cat.name}</span>
                </button>
              );
            })}
          </div>

          {/* Memory List or Empty State */}
          {isLoading ? (
            <div className="text-center py-20" style={{ color: "var(--text-muted)" }}>
              Loading memories...
            </div>
          ) : memories.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 rounded-2xl" style={{ background: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
              <span className="text-5xl mb-4">🧠</span>
              <h3 className="text-lg font-semibold mb-2" style={{ color: "var(--text-primary)" }}>No memories found</h3>
              <p className="text-sm text-center max-w-md" style={{ color: "var(--text-secondary)" }}>
                {searchQuery ? "Try searching for a different phrase." : "As we chat, I'll automatically extract and store important facts, preferences, and details about you here."}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {memories.map((memory) => {
                const categoryIcon = CATEGORIES.find(c => c.key === memory.category)?.icon || "📌";
                return (
                  <div
                    key={memory.id}
                    className="p-5 rounded-2xl border transition-all duration-200 flex flex-col justify-between hover:scale-[1.01]"
                    style={{
                      background: "var(--bg-card)",
                      borderColor: "var(--border-color)",
                    }}
                  >
                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-xs px-2.5 py-1 rounded-full font-semibold flex items-center gap-1" style={{ background: "var(--bg-tertiary)", color: "var(--text-secondary)" }}>
                          {categoryIcon} {memory.category || "General"}
                        </span>
                        <div className="flex items-center gap-2">
                          {/* Importance rating */}
                          <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                            ⭐ {memory.importance}/5
                          </span>
                          <button
                            onClick={() => handleDelete(memory.id)}
                            className="p-1 hover:bg-[var(--bg-tertiary)] rounded-lg transition-colors"
                            style={{ color: "var(--error)" }}
                            title="Forget Memory"
                          >
                            🗑️
                          </button>
                        </div>
                      </div>
                      <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                        {memory.content}
                      </p>
                    </div>
                    <div className="text-[10px] mt-4 flex items-center justify-between" style={{ color: "var(--text-muted)" }}>
                      <span>Saved: {new Date(memory.created_at).toLocaleDateString()}</span>
                      {memory.relevance_score !== undefined && (
                        <span className="text-[var(--accent-secondary)] font-semibold">
                          Match: {Math.round(memory.relevance_score * 100)}%
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </main>
    </div>
    </>
  );
}
