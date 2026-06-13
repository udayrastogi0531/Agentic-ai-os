"use client";

import { useState, useEffect } from "react";
import Sidebar from "@/components/dashboard/Sidebar";
import api from "@/lib/api";
import useAuth from "@/hooks/useAuth";

interface Milestone {
  id: string;
  title: string;
  is_completed: boolean;
  due_date?: string;
}

interface Goal {
  id: string;
  title: string;
  description: string;
  category: string;
  progress: number;
  status: string;
  target_date?: string;
  milestones: Milestone[];
}

export default function GoalsPage() {
  useAuth();
  const [goals, setGoals] = useState<Goal[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<string>("active");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isEvaluating, setIsEvaluating] = useState<string | null>(null);
  const [evaluationText, setEvaluationText] = useState<string | null>(null);
  const [selectedGoalForEval, setSelectedGoalForEval] = useState<Goal | null>(null);

  // Form State
  const [newTitle, setNewTitle] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newCategory, setNewCategory] = useState("career");
  const [newTargetDate, setNewTargetDate] = useState("");
  const [newMilestones, setNewMilestones] = useState<string[]>([""]);

  useEffect(() => {
    loadGoals();
  }, []);

  const loadGoals = async () => {
    try {
      const res = await (api as any).getGoals?.();
      setGoals(res?.goals || []);
    } catch (err) {
      console.error("Failed to load goals", err);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleMilestone = async (goalId: string, milestoneId: string, isCompleted: boolean) => {
    const goal = goals.find((g) => g.id === goalId);
    if (!goal) return;

    const updatedMilestones = goal.milestones.map((m) =>
      m.id === milestoneId ? { ...m, is_completed: isCompleted } : m
    );

    try {
      // Calculate optimistic progress
      const completedCount = updatedMilestones.filter((m) => m.is_completed).length;
      const optimisticProgress = Math.round((completedCount / updatedMilestones.length) * 100);

      // Call API
      const updated = await (api as any).updateGoal?.(goalId, {
        milestones: updatedMilestones,
        progress: optimisticProgress,
      });

      // Update state
      setGoals((prev) => prev.map((g) => (g.id === goalId ? updated : g)));
    } catch (err) {
      console.error("Error toggling milestone", err);
    }
  };

  const handleCreateGoal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;

    const milestoneObjects = newMilestones
      .filter((m) => m.trim())
      .map((title) => ({ title }));

    try {
      const created = await (api as any).createGoal?.({
        title: newTitle,
        description: newDesc || null,
        category: newCategory,
        target_date: newTargetDate || null,
        milestones: milestoneObjects,
      });

      setGoals((prev) => [created, ...prev]);
      setIsModalOpen(false);

      // Reset Form
      setNewTitle("");
      setNewDesc("");
      setNewCategory("career");
      setNewTargetDate("");
      setNewMilestones([""]);
    } catch (err) {
      console.error("Error creating goal", err);
    }
  };

  const handleDeleteGoal = async (id: string) => {
    if (!confirm("Are you sure you want to delete this goal, Uday?")) return;
    try {
      await (api as any).deleteGoal?.(id);
      setGoals((prev) => prev.filter((g) => g.id !== id));
      if (selectedGoalForEval?.id === id) {
        setEvaluationText(null);
        setSelectedGoalForEval(null);
      }
    } catch (err) {
      console.error("Error deleting goal", err);
    }
  };

  const handleEvaluateGoal = async (goal: Goal) => {
    setIsEvaluating(goal.id);
    setSelectedGoalForEval(goal);
    setEvaluationText(null);
    try {
      const res = await (api as any).evaluateGoal?.(goal.id);
      setEvaluationText(res.evaluation);
    } catch (err) {
      setEvaluationText("Nidhi encountered an issue loading evaluations.");
    } finally {
      setIsEvaluating(null);
    }
  };

  const handleAddMilestoneInput = () => {
    setNewMilestones((prev) => [...prev, ""]);
  };

  const handleMilestoneInputChange = (index: number, val: string) => {
    const updated = [...newMilestones];
    updated[index] = val;
    setNewMilestones(updated);
  };

  const handleRemoveMilestoneInput = (index: number) => {
    setNewMilestones((prev) => prev.filter((_, i) => i !== index));
  };

  const filteredGoals = goals.filter((g) => {
    if (activeTab === "completed") return g.status === "completed" || g.progress === 100;
    return g.status === "active" && g.progress < 100;
  });

  return (
    <>
      <div className="aurora-bg" aria-hidden />
      <div className="flex min-h-screen" style={{ background: "var(--bg-primary)" }}>
        <Sidebar />
        <main
          className="flex-1 overflow-y-auto relative"
          style={{ marginLeft: "var(--sidebar-width)", zIndex: 1 }}
        >
          {/* Header */}
          <header
            className="sticky top-0 z-30 glass-strong px-8 py-5 flex items-center justify-between"
            style={{ borderBottom: "1px solid rgba(124,107,255,0.08)" }}
          >
            <div>
              <h1
                className="text-2xl font-bold"
                style={{ color: "var(--text-primary)", fontFamily: "var(--font-display)" }}
              >
                🎯 Goal Tracker
              </h1>
              <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                Track your placement milestones, career projects, and personal achievements
              </p>
            </div>
            <button onClick={() => setIsModalOpen(true)} className="btn-nidhi text-xs px-4 py-2">
              + Add Target Goal
            </button>
          </header>

          <div className="max-w-5xl mx-auto px-6 py-8 grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Goals Column */}
            <div className="lg:col-span-2 space-y-6">
              {/* Tabs */}
              <div className="flex gap-1">
                {["active", "completed"].map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className="px-4 py-2 rounded-xl text-sm font-medium transition-all"
                    style={{
                      background: activeTab === tab ? "rgba(124,107,255,0.15)" : "transparent",
                      border: `1px solid ${activeTab === tab ? "rgba(124,107,255,0.4)" : "transparent"}`,
                      color: activeTab === tab ? "var(--text-primary)" : "var(--text-muted)",
                    }}
                  >
                    {tab === "active" ? "🎯 Active Goals" : "🏆 Completed Goals"}
                  </button>
                ))}
              </div>

              {loading ? (
                <div className="flex justify-center py-20">
                  <div
                    className="w-10 h-10 rounded-full"
                    style={{
                      background: "linear-gradient(135deg, #7c6bff, #e879f9)",
                      animation: "breathe 1.5s ease-in-out infinite",
                    }}
                  />
                </div>
              ) : filteredGoals.length === 0 ? (
                <div className="text-center py-16 rounded-3xl border border-purple-500/10 p-6 bg-purple-950/5">
                  <span className="text-4xl block mb-3">🎯</span>
                  <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                    No {activeTab} goals found. Let's create your first goal, Uday!
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {filteredGoals.map((goal) => (
                    <div
                      key={goal.id}
                      className="rounded-2xl p-5 transition-all"
                      style={{
                        background: "rgba(17, 17, 40, 0.75)",
                        border: "1px solid rgba(124, 107, 255, 0.12)",
                        backdropFilter: "blur(16px)",
                      }}
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <span
                            className="text-[10px] px-2 py-0.5 rounded-full border border-purple-500/30 uppercase font-semibold text-purple-300"
                            style={{ background: "rgba(124,107,255,0.1)" }}
                          >
                            {goal.category}
                          </span>
                          <h3
                            className="text-base font-bold mt-2"
                            style={{ color: "var(--text-primary)" }}
                          >
                            {goal.title}
                          </h3>
                          <p className="text-xs text-gray-400 mt-1">{goal.description}</p>
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleEvaluateGoal(goal)}
                            disabled={isEvaluating != null}
                            className="text-xs bg-purple-500/10 border border-purple-500/30 hover:bg-purple-500/20 text-purple-300 px-2.5 py-1.5 rounded-xl transition-all"
                          >
                            {isEvaluating === goal.id ? "✦ evaluating…" : "🤖 Ask Nidhi"}
                          </button>
                          <button
                            onClick={() => handleDeleteGoal(goal.id)}
                            className="text-xs bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 p-1.5 rounded-xl transition-all"
                          >
                            🗑️
                          </button>
                        </div>
                      </div>

                      {/* Progress Bar */}
                      <div className="mt-4 space-y-1">
                        <div className="flex justify-between text-xs font-semibold text-gray-400">
                          <span>Progress</span>
                          <span>{goal.progress}%</span>
                        </div>
                        <div className="w-full h-2 rounded-full bg-white/5 overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all duration-500"
                            style={{
                              width: `${goal.progress}%`,
                              background: "linear-gradient(90deg, #7c6bff, #e879f9)",
                              boxShadow: "0 0 10px rgba(124,107,255,0.5)",
                            }}
                          />
                        </div>
                      </div>

                      {/* Milestones list */}
                      {goal.milestones.length > 0 && (
                        <div className="mt-4 border-t border-purple-500/10 pt-3 space-y-2">
                          <p className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">
                            Milestones
                          </p>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                            {goal.milestones.map((m) => (
                              <label
                                key={m.id}
                                className="flex items-center gap-2 px-3 py-2 rounded-xl transition-all cursor-pointer hover:bg-white/5"
                                style={{
                                  background: m.is_completed ? "rgba(16,185,129,0.05)" : "rgba(255,255,255,0.01)",
                                  border: `1px solid ${m.is_completed ? "rgba(16,185,129,0.15)" : "rgba(255,255,255,0.04)"}`,
                                }}
                              >
                                <input
                                  type="checkbox"
                                  checked={m.is_completed}
                                  onChange={(e) =>
                                    handleToggleMilestone(goal.id, m.id, e.target.checked)
                                  }
                                  className="w-3.5 h-3.5 rounded text-purple-600 focus:ring-purple-500 border-gray-600 bg-gray-700"
                                />
                                <span
                                  className={`text-xs ${m.is_completed ? "line-through text-gray-500" : "text-gray-300"}`}
                                >
                                  {m.title}
                                </span>
                              </label>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* AI Advisor Panel */}
            <div className="space-y-4">
              <div
                className="rounded-3xl p-5 min-h-[300px]"
                style={{
                  background: "rgba(17, 17, 40, 0.6)",
                  border: "1px solid rgba(124, 107, 255, 0.12)",
                  backdropFilter: "blur(20px)",
                }}
              >
                <div className="flex items-center gap-3 border-b border-purple-500/10 pb-4 mb-4">
                  <div
                    className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold"
                    style={{
                      background: "linear-gradient(135deg, #7c6bff, #e879f9)",
                      boxShadow: "0 0 10px rgba(124, 107, 255, 0.3)",
                    }}
                  >
                    ✦
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-white">Nidhi's Goal Insights</h3>
                    <p className="text-[9px] text-gray-500">Ask Nidhi to evaluate to view roadmap reviews</p>
                  </div>
                </div>

                {selectedGoalForEval ? (
                  <div>
                    <h4 className="text-xs font-bold text-violet-300 mb-2">
                      Reviewing: {selectedGoalForEval.title}
                    </h4>
                    {isEvaluating ? (
                      <div className="text-center py-10 space-y-2">
                        <div className="w-6 h-6 border-2 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto" />
                        <p className="text-xs text-gray-400">Nidhi is evaluating goal progress…</p>
                      </div>
                    ) : (
                      <div className="text-xs leading-relaxed text-gray-300 space-y-2 whitespace-pre-wrap max-h-[400px] overflow-y-auto pr-1">
                        {evaluationText}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-20 text-center text-gray-500 space-y-2">
                    <span className="text-2xl">🤖</span>
                    <p className="text-xs">
                      Click the **Ask Nidhi** button on any goal to receive personalized, actionable feedback here.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </main>
      </div>

      {/* Goal Creation Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div
            className="rounded-3xl p-6 w-full max-w-lg animate-fade-in"
            style={{
              background: "rgba(10, 10, 25, 0.95)",
              border: "1px solid rgba(124, 107, 255, 0.2)",
            }}
          >
            <div className="flex justify-between items-center border-b border-purple-500/10 pb-3 mb-4">
              <h3 className="text-lg font-bold text-white font-display">🎯 Create New Goal</h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-gray-400 hover:text-white"
              >
                ×
              </button>
            </div>

            <form onSubmit={handleCreateGoal} className="space-y-4">
              <div>
                <label className="block text-xs mb-1.5 font-medium text-gray-400">Goal Title</label>
                <input
                  type="text"
                  required
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g. Build an AI Operating System"
                  className="w-full bg-transparent text-sm px-3 py-2.5 rounded-xl border border-purple-500/15 focus:border-purple-500/50 outline-none text-white"
                />
              </div>

              <div>
                <label className="block text-xs mb-1.5 font-medium text-gray-400">Description</label>
                <textarea
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  placeholder="Describe details or targets…"
                  className="w-full bg-transparent text-sm px-3 py-2 rounded-xl border border-purple-500/15 focus:border-purple-500/50 outline-none text-white resize-y"
                  rows={2}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs mb-1.5 font-medium text-gray-400">Category</label>
                  <select
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                    className="w-full bg-transparent text-xs px-3 py-2.5 rounded-xl border border-purple-500/15 focus:border-purple-500/50 outline-none text-white bg-purple-950/80"
                  >
                    <option value="career">Career / Job</option>
                    <option value="projects">Projects</option>
                    <option value="learnings">Learnings</option>
                    <option value="academic">Academic</option>
                    <option value="personal">Personal / Wellness</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs mb-1.5 font-medium text-gray-400">Target Date</label>
                  <input
                    type="date"
                    value={newTargetDate}
                    onChange={(e) => setNewTargetDate(e.target.value)}
                    className="w-full bg-transparent text-xs px-3 py-2.5 rounded-xl border border-purple-500/15 focus:border-purple-500/50 outline-none text-white"
                  />
                </div>
              </div>

              {/* Milestones Inputs */}
              <div>
                <div className="flex justify-between items-center mb-1.5">
                  <label className="block text-xs font-medium text-gray-400">Milestones</label>
                  <button
                    type="button"
                    onClick={handleAddMilestoneInput}
                    className="text-xs text-purple-300 hover:underline"
                  >
                    + Add milestone
                  </button>
                </div>

                <div className="space-y-2 max-h-[140px] overflow-y-auto pr-1">
                  {newMilestones.map((m, idx) => (
                    <div key={idx} className="flex gap-2 items-center">
                      <input
                        type="text"
                        value={m}
                        onChange={(e) => handleMilestoneInputChange(idx, e.target.value)}
                        placeholder={`Milestone #${idx + 1}`}
                        className="flex-1 bg-transparent text-xs px-3 py-2 rounded-xl border border-purple-500/10 focus:border-purple-500/40 outline-none text-white"
                      />
                      {newMilestones.length > 1 && (
                        <button
                          type="button"
                          onClick={() => handleRemoveMilestoneInput(idx)}
                          className="text-red-400 text-xs px-1.5"
                        >
                          ×
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="btn-ghost flex-1 text-xs py-2.5"
                >
                  Cancel
                </button>
                <button type="submit" className="btn-nidhi flex-1 text-xs py-2.5">
                  Create Goal
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
