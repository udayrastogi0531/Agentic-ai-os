"use client";

/**
 * Nidhi — Notes Page
 *
 * Full featured notes pad with pin functionality, grid list, search, inline creation/edit.
 */

import { useState, useEffect } from "react";
import Sidebar from "@/components/dashboard/Sidebar";
import useAuth from "@/hooks/useAuth";
import api from "@/lib/api";
import type { Note } from "@/types";

export default function NotesPage() {
  useAuth(); // Require authentication
  const [notes, setNotes] = useState<Note[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  // Editor Modal / Form States
  const [showEditor, setShowEditor] = useState(false);
  const [activeNote, setActiveNote] = useState<Note | null>(null);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [category, setCategory] = useState("");
  const [isPinned, setIsPinned] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const loadNotes = async () => {
    setIsLoading(true);
    try {
      const response = (await api.getNotes()) as { notes: Note[] };
      setNotes(response.notes || []);
    } catch (err) {
      console.error("Failed to load notes:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadNotes();
  }, []);

  // Filter notes client-side based on search query
  const filteredNotes = notes.filter((note) => {
    const query = searchQuery.toLowerCase();
    return (
      note.title.toLowerCase().includes(query) ||
      note.content.toLowerCase().includes(query) ||
      note.category?.toLowerCase().includes(query)
    );
  });

  // Handle Pin Toggle
  const handleTogglePin = async (note: Note) => {
    try {
      const updated = await api.updateNote(note.id, { is_pinned: !note.is_pinned });
      setNotes((prev) =>
        prev
          .map((n) => (n.id === note.id ? (updated as Note) : n))
          .sort((a, b) => Number(b.is_pinned) - Number(a.is_pinned))
      );
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to toggle pin");
    }
  };

  // Handle Delete
  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this note?")) return;

    try {
      await api.deleteNote(id);
      setNotes((prev) => prev.filter((n) => n.id !== id));
      if (activeNote?.id === id) {
        setShowEditor(false);
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to delete note");
    }
  };

  // Open Editor for new or existing note
  const openEditor = (note: Note | null = null) => {
    if (note) {
      setActiveNote(note);
      setTitle(note.title);
      setContent(note.content);
      setCategory(note.category || "");
      setIsPinned(note.is_pinned);
    } else {
      setActiveNote(null);
      setTitle("");
      setContent("");
      setCategory("");
      setIsPinned(false);
    }
    setShowEditor(true);
  };

  // Save Note
  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) return;

    setIsSaving(true);
    try {
      if (activeNote) {
        // Edit existing
        const updated = await api.updateNote(activeNote.id, {
          title,
          content,
          category: category || undefined,
          is_pinned: isPinned,
        });
        setNotes((prev) =>
          prev
            .map((n) => (n.id === activeNote.id ? (updated as Note) : n))
            .sort((a, b) => Number(b.is_pinned) - Number(a.is_pinned))
        );
      } else {
        // Create new
        await api.createNote({
          title,
          content,
          category: category || undefined,
          is_pinned: isPinned,
        });
        await loadNotes();
      }
      setShowEditor(false);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to save note");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="flex min-h-screen" style={{ background: "var(--bg-primary)" }}>
      <Sidebar />
      <main className="flex-1" style={{ marginLeft: "var(--sidebar-width)" }}>
        <header className="sticky top-0 z-30 glass-strong px-8 py-5 flex items-center justify-between" style={{ borderBottom: "1px solid var(--border-color)" }}>
          <div>
            <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>📝 Notes & Memos</h1>
            <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>Capture ideas and thoughts instantly</p>
          </div>
          <button
            onClick={() => openEditor(null)}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium text-white transition-all duration-200 hover:scale-105"
            style={{ background: "var(--gradient-primary)" }}
          >
            ➕ New Note
          </button>
        </header>

        <div className="px-8 py-6 space-y-6 animate-fade-in max-w-5xl">
          {/* Editor Modal */}
          {showEditor && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-fade-in">
              <form
                onSubmit={handleSave}
                className="w-full max-w-2xl rounded-3xl p-6 glass-strong space-y-4 max-h-[90vh] overflow-y-auto"
                style={{ border: "1px solid var(--border-color)", boxShadow: "var(--shadow-card)" }}
              >
                <div className="flex items-center justify-between">
                  <h3 className="font-bold text-base" style={{ color: "var(--text-primary)" }}>
                    {activeNote ? "Edit Note" : "Create New Note"}
                  </h3>
                  <button
                    type="button"
                    onClick={() => setShowEditor(false)}
                    className="p-1 hover:bg-[var(--bg-hover)] rounded-lg text-sm"
                  >
                    ✕
                  </button>
                </div>

                <div className="space-y-3">
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="Note title..."
                    required
                    className="w-full bg-transparent text-lg font-bold outline-none border-b py-2"
                    style={{ borderColor: "var(--border-color)", color: "var(--text-primary)" }}
                  />
                  <textarea
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    placeholder="Write your note contents here..."
                    required
                    rows={10}
                    className="w-full bg-transparent text-sm outline-none resize-none font-sans"
                    style={{ color: "var(--text-primary)" }}
                  />
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                    <div className="space-y-1">
                      <label className="text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>Category</label>
                      <input
                        type="text"
                        value={category}
                        onChange={(e) => setCategory(e.target.value)}
                        placeholder="e.g. Ideas, Research"
                        className="w-full rounded-xl px-4 py-2 text-sm outline-none"
                        style={{ background: "var(--bg-tertiary)", border: "1px solid var(--border-color)", color: "var(--text-primary)" }}
                      />
                    </div>
                    <div className="flex items-end pb-1.5">
                      <label className="flex items-center gap-2 text-sm cursor-pointer select-none" style={{ color: "var(--text-secondary)" }}>
                        <input
                          type="checkbox"
                          checked={isPinned}
                          onChange={(e) => setIsPinned(e.target.checked)}
                          className="w-4 h-4 rounded"
                        />
                        📌 Pin note to top
                      </label>
                    </div>
                  </div>
                </div>

                <div className="flex gap-2 justify-end pt-4 border-t border-[var(--border-color)]">
                  {activeNote && (
                    <button
                      type="button"
                      onClick={() => handleDelete(activeNote.id)}
                      className="px-4 py-2 rounded-xl text-sm border mr-auto"
                      style={{ color: "var(--error)", borderColor: "rgba(239, 68, 68, 0.3)" }}
                    >
                      Delete Note
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => setShowEditor(false)}
                    className="px-4 py-2 rounded-xl text-sm"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSaving}
                    className="px-5 py-2 rounded-xl text-sm font-semibold text-white transition-all"
                    style={{ background: "var(--gradient-primary)", opacity: isSaving ? 0.7 : 1 }}
                  >
                    {isSaving ? "Saving..." : "Save Note"}
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Search Bar */}
          <div>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search notes by title, content, or category..."
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

          {/* Notes List */}
          {isLoading ? (
            <div className="text-center py-20" style={{ color: "var(--text-muted)" }}>
              Loading notes...
            </div>
          ) : filteredNotes.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 rounded-2xl" style={{ background: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
              <span className="text-5xl mb-4">📝</span>
              <h3 className="text-lg font-semibold mb-2" style={{ color: "var(--text-primary)" }}>No notes here</h3>
              <p className="text-sm text-center max-w-md" style={{ color: "var(--text-secondary)" }}>
                {searchQuery ? "Try searching for a different keyword." : "Add a note above or say in chat: 'Create a note about my shopping list'"}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredNotes.map((note) => (
                <div
                  key={note.id}
                  onClick={() => openEditor(note)}
                  className="p-5 rounded-2xl border transition-all duration-200 cursor-pointer flex flex-col justify-between hover:scale-[1.02]"
                  style={{
                    background: "var(--bg-card)",
                    borderColor: note.is_pinned ? "var(--accent-primary)" : "var(--border-color)",
                  }}
                >
                  <div>
                    <div className="flex items-start justify-between mb-3">
                      {note.category ? (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider" style={{ background: "var(--bg-tertiary)", color: "var(--text-secondary)" }}>
                          {note.category}
                        </span>
                      ) : (
                        <span />
                      )}
                      <div className="flex gap-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleTogglePin(note);
                          }}
                          className="p-1 hover:bg-[var(--bg-tertiary)] rounded-lg transition-colors text-sm"
                          title={note.is_pinned ? "Unpin Note" : "Pin Note"}
                        >
                          {note.is_pinned ? "📌" : "📍"}
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(note.id);
                          }}
                          className="p-1 hover:bg-[var(--bg-tertiary)] rounded-lg transition-colors text-sm"
                          style={{ color: "var(--error)" }}
                        >
                          🗑️
                        </button>
                      </div>
                    </div>
                    <h3 className="text-sm font-semibold truncate" style={{ color: "var(--text-primary)" }}>
                      {note.title}
                    </h3>
                    <p className="text-xs mt-2 line-clamp-4 leading-relaxed whitespace-pre-wrap" style={{ color: "var(--text-secondary)" }}>
                      {note.content}
                    </p>
                  </div>
                  <div className="text-[10px] mt-4 flex justify-between" style={{ color: "var(--text-muted)" }}>
                    <span>Last edit: {new Date(note.updated_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
