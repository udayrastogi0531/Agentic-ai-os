"use client";

/**
 * Nidhi — Tasks Page
 *
 * Full productivity task board with stats, status toggle, filtering, creation, and deletion.
 */

import { useState, useEffect } from "react";
import Sidebar from "@/components/dashboard/Sidebar";
import useAuth from "@/hooks/useAuth";
import api from "@/lib/api";
import type { Task } from "@/types";

export default function TasksPage() {
  useAuth(); // Require authentication
  const [tasks, setTasks] = useState<Task[]>([]);
  const [taskStats, setTaskStats] = useState<Record<string, number>>({});
  const [selectedTab, setSelectedTab] = useState("all");
  const [isLoading, setIsLoading] = useState(true);

  // Form States for creating a task
  const [showAddForm, setShowAddForm] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState<"low" | "medium" | "high" | "urgent">("medium");
  const [category, setCategory] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  const loadTasks = async () => {
    setIsLoading(true);
    try {
      const statusFilter = selectedTab === "all" ? undefined : selectedTab;
      const response = (await api.getTasks(statusFilter)) as {
        tasks: Task[];
        stats: Record<string, number>;
      };
      setTasks(response.tasks || []);
      setTaskStats(response.stats || {});
    } catch (err) {
      console.error("Failed to load tasks:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadTasks();
  }, [selectedTab]);

  // Handle Toggle Done
  const handleToggleDone = async (task: Task) => {
    const newStatus = task.status === "done" ? "todo" : "done";
    try {
      await api.updateTask(task.id, { status: newStatus });
      setTasks((prev) =>
        prev.map((t) => (t.id === task.id ? { ...t, status: newStatus } : t))
      );
      // reload stats
      const statsResponse = (await api.getTasks()) as { stats: Record<string, number> };
      setTaskStats(statsResponse.stats || {});
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to update task");
    }
  };

  // Handle Delete
  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this task?")) return;

    try {
      await api.deleteTask(id);
      setTasks((prev) => prev.filter((t) => t.id !== id));
      const statsResponse = (await api.getTasks()) as { stats: Record<string, number> };
      setTaskStats(statsResponse.stats || {});
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to delete task");
    }
  };

  // Handle Create
  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    setIsSaving(true);
    try {
      await api.createTask({
        title,
        description: description || undefined,
        priority,
        category: category || undefined,
        due_date: dueDate || undefined,
        status: "todo",
      });
      setTitle("");
      setDescription("");
      setPriority("medium");
      setCategory("");
      setDueDate("");
      setShowAddForm(false);
      await loadTasks();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to create task");
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
            <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>✅ Tasks & Goals</h1>
            <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>Manage your tasks and daily schedule</p>
          </div>
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium text-white transition-all duration-200 hover:scale-105"
            style={{ background: "var(--gradient-primary)" }}
          >
            ➕ Add Task
          </button>
        </header>

        <div className="px-8 py-6 space-y-6 animate-fade-in max-w-5xl">
          {/* Form to add a task */}
          {showAddForm && (
            <form onSubmit={handleCreate} className="p-6 rounded-2xl border space-y-4 animate-fade-in" style={{ background: "var(--bg-card)", borderColor: "var(--border-color)" }}>
              <h3 className="font-semibold text-sm" style={{ color: "var(--text-primary)" }}>Add New Task</h3>
              <div className="space-y-3">
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Task title..."
                  required
                  className="w-full rounded-xl px-4 py-2.5 text-sm outline-none"
                  style={{ background: "var(--bg-tertiary)", border: "1px solid var(--border-color)", color: "var(--text-primary)" }}
                />
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Description (optional)..."
                  rows={2}
                  className="w-full rounded-xl px-4 py-2.5 text-sm outline-none resize-none"
                  style={{ background: "var(--bg-tertiary)", border: "1px solid var(--border-color)", color: "var(--text-primary)" }}
                />
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="space-y-1">
                    <label className="text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>Priority</label>
                    <select
                      value={priority}
                      onChange={(e) => setPriority(e.target.value as "low" | "medium" | "high" | "urgent")}
                      className="w-full rounded-xl px-4 py-2.5 text-sm outline-none"
                      style={{ background: "var(--bg-tertiary)", border: "1px solid var(--border-color)", color: "var(--text-primary)" }}
                    >
                      <option value="low">🟢 Low</option>
                      <option value="medium">🟡 Medium</option>
                      <option value="high">🟠 High</option>
                      <option value="urgent">🔴 Urgent</option>
                    </select>
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>Category</label>
                    <input
                      type="text"
                      value={category}
                      onChange={(e) => setCategory(e.target.value)}
                      placeholder="e.g. Work, Personal"
                      className="w-full rounded-xl px-4 py-2.5 text-sm outline-none"
                      style={{ background: "var(--bg-tertiary)", border: "1px solid var(--border-color)", color: "var(--text-primary)" }}
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>Due Date</label>
                    <input
                      type="date"
                      value={dueDate}
                      onChange={(e) => setDueDate(e.target.value)}
                      className="w-full rounded-xl px-4 py-2.5 text-sm outline-none"
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
                  disabled={isSaving}
                  className="px-5 py-2 rounded-xl text-sm font-semibold text-white transition-all"
                  style={{ background: "var(--gradient-primary)", opacity: isSaving ? 0.7 : 1 }}
                >
                  {isSaving ? "Saving..." : "Add Task"}
                </button>
              </div>
            </form>
          )}

          {/* Mini Stats Row */}
          <div className="grid grid-cols-3 gap-4">
            <div className="p-4 rounded-2xl border flex flex-col justify-between" style={{ background: "var(--bg-card)", borderColor: "var(--border-color)" }}>
              <span className="text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>To Do</span>
              <span className="text-2xl font-bold mt-1" style={{ color: "var(--warning)" }}>{taskStats.todo || 0}</span>
            </div>
            <div className="p-4 rounded-2xl border flex flex-col justify-between" style={{ background: "var(--bg-card)", borderColor: "var(--border-color)" }}>
              <span className="text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>In Progress</span>
              <span className="text-2xl font-bold mt-1" style={{ color: "var(--info)" }}>{taskStats.in_progress || 0}</span>
            </div>
            <div className="p-4 rounded-2xl border flex flex-col justify-between" style={{ background: "var(--bg-card)", borderColor: "var(--border-color)" }}>
              <span className="text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>Completed</span>
              <span className="text-2xl font-bold mt-1" style={{ color: "var(--success)" }}>{taskStats.done || 0}</span>
            </div>
          </div>

          {/* Filter Tabs */}
          <div className="flex gap-2 border-b border-[var(--border-color)] pb-3">
            {[
              { label: "All Tasks", value: "all" },
              { label: "To Do", value: "todo" },
              { label: "In Progress", value: "in_progress" },
              { label: "Completed", value: "done" },
            ].map((tab) => {
              const isActive = selectedTab === tab.value;
              return (
                <button
                  key={tab.value}
                  onClick={() => setSelectedTab(tab.value)}
                  className="px-4 py-2 text-sm font-semibold transition-all duration-200 border-b-2"
                  style={{
                    borderColor: isActive ? "var(--accent-primary)" : "transparent",
                    color: isActive ? "var(--text-primary)" : "var(--text-muted)",
                  }}
                >
                  {tab.label}
                </button>
              );
            })}
          </div>

          {/* Tasks List */}
          {isLoading ? (
            <div className="text-center py-20" style={{ color: "var(--text-muted)" }}>
              Loading tasks...
            </div>
          ) : tasks.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 rounded-2xl" style={{ background: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
              <span className="text-5xl mb-4">✅</span>
              <h3 className="text-lg font-semibold mb-2" style={{ color: "var(--text-primary)" }}>No tasks here</h3>
              <p className="text-sm text-center max-w-md" style={{ color: "var(--text-secondary)" }}>
                {selectedTab !== "all" ? "No tasks match this filter status." : "Add a task above or say in chat: 'Add task: finish planning website'"}
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {tasks.map((task) => {
                const isCompleted = task.status === "done";
                return (
                  <div
                    key={task.id}
                    className="p-4 rounded-xl border flex items-center gap-4 transition-all hover:bg-[var(--bg-hover)]"
                    style={{
                      background: "var(--bg-card)",
                      borderColor: "var(--border-color)",
                      opacity: isCompleted ? 0.7 : 1,
                    }}
                  >
                    {/* Checkbox */}
                    <button
                      onClick={() => handleToggleDone(task)}
                      className="w-5 h-5 rounded-md flex items-center justify-center border transition-all"
                      style={{
                        borderColor: isCompleted ? "var(--success)" : "var(--border-color)",
                        background: isCompleted ? "var(--success)" : "transparent",
                      }}
                    >
                      {isCompleted && <span className="text-white text-xs">✓</span>}
                    </button>

                    {/* Task Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span
                          className={`text-sm font-semibold truncate ${
                            isCompleted ? "line-through" : ""
                          }`}
                          style={{ color: isCompleted ? "var(--text-muted)" : "var(--text-primary)" }}
                        >
                          {task.title}
                        </span>
                        {task.priority === "urgent" && (
                          <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-red-900/40 text-red-300">
                            URGENT
                          </span>
                        )}
                        {task.priority === "high" && (
                          <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-orange-900/40 text-orange-300">
                            HIGH
                          </span>
                        )}
                      </div>
                      {task.description && (
                        <p className="text-xs truncate mt-0.5" style={{ color: "var(--text-muted)" }}>
                          {task.description}
                        </p>
                      )}
                    </div>

                    {/* Details and Delete */}
                    <div className="flex items-center gap-3">
                      {task.category && (
                        <span className="text-xs px-2.5 py-1 rounded-full" style={{ background: "var(--bg-tertiary)", color: "var(--text-secondary)" }}>
                          📁 {task.category}
                        </span>
                      )}
                      {task.due_date && (
                        <span className="text-[10px] font-semibold flex items-center gap-1" style={{ color: new Date(task.due_date) < new Date() && !isCompleted ? "var(--error)" : "var(--text-muted)" }}>
                          📅 {new Date(task.due_date).toLocaleDateString()}
                        </span>
                      )}
                      <button
                        onClick={() => handleDelete(task.id)}
                        className="p-1 hover:bg-[var(--bg-tertiary)] rounded-lg transition-colors text-xs"
                        style={{ color: "var(--error)" }}
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
