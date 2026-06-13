"use client";

import { useState, useRef } from "react";
import Sidebar from "@/components/dashboard/Sidebar";
import api from "@/lib/api";
import useAuth from "@/hooks/useAuth";

interface Question {
  id: number;
  question: string;
}

interface Evaluation {
  grade: string;
  score_percentage: number;
  feedback_summary: string;
  strengths: string[];
  improvements: string[];
  sample_ideal_answer: string;
}

export default function InterviewPage() {
  useAuth();
  const [role, setRole] = useState("AI Engineer");
  const [topic, setTopic] = useState("LLMs & RAG Architectures");
  const [difficulty, setDifficulty] = useState("Mid");

  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [evaluating, setEvaluating] = useState(false);

  // Results State
  const [evaluations, setEvaluations] = useState<Record<number, Evaluation>>({});
  const [showIdealAnswer, setShowIdealAnswer] = useState(false);
  const [sessionActive, setSessionActive] = useState(false);
  const [isPlayingText, setIsPlayingText] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const startSession = async () => {
    setLoading(true);
    setQuestions([]);
    setCurrentIdx(0);
    setAnswer("");
    setEvaluations({});
    setShowIdealAnswer(false);

    try {
      const res = await (api as any).getInterviewQuestions?.({
        role,
        topic,
        difficulty,
      });
      if (res?.questions?.length) {
        setQuestions(res.questions);
        setSessionActive(true);
      }
    } catch (err) {
      console.error("Failed to load interview questions", err);
    } finally {
      setLoading(false);
    }
  };

  const speakQuestion = async (text: string) => {
    if (isPlayingText) {
      if (audioRef.current) audioRef.current.pause();
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
      setIsPlayingText(false);
      return;
    }

    setIsPlayingText(true);
    try {
      const audioBlob = await api.synthesizeSpeech(text);
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      audioRef.current = audio;
      audio.onended = () => setIsPlayingText(false);
      audio.play();
    } catch {
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.onend = () => setIsPlayingText(false);
        window.speechSynthesis.speak(utterance);
      } else {
        setIsPlayingText(false);
      }
    }
  };

  const submitAnswer = async () => {
    if (!answer.trim() || evaluating) return;
    setEvaluating(true);
    const questionText = questions[currentIdx].question;

    try {
      const res = await (api as any).evaluateInterviewAnswer?.({
        question: questionText,
        answer: answer.trim(),
      });
      setEvaluations((prev) => ({
        ...prev,
        [currentIdx]: res.evaluation,
      }));
    } catch (err) {
      console.error("Failed to evaluate answer", err);
    } finally {
      setEvaluating(false);
    }
  };

  const nextQuestion = () => {
    if (currentIdx < questions.length - 1) {
      setCurrentIdx((prev) => prev + 1);
      setAnswer("");
      setShowIdealAnswer(false);
    } else {
      // Completed session
      setSessionActive(false);
    }
  };

  const cardStyle = {
    background: "rgba(17, 17, 40, 0.75)",
    border: "1px solid rgba(124, 107, 255, 0.12)",
    backdropFilter: "blur(16px)",
  };

  const activeQuestion = questions[currentIdx];
  const activeEval = evaluations[currentIdx];

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
                🎙️ Mock Interview Coach
              </h1>
              <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                Practice real-time technical answers and receive grades and STAR improvement tips from Nidhi
              </p>
            </div>
            {sessionActive && (
              <button
                onClick={() => setSessionActive(false)}
                className="btn-ghost text-xs px-3.5 py-1.5"
              >
                Quit Session
              </button>
            )}
          </header>

          <div className="max-w-4xl mx-auto px-6 py-8 space-y-6">
            {!sessionActive ? (
              /* Setup Panel */
              <div className="rounded-3xl p-6 space-y-5" style={cardStyle}>
                <h3 className="text-lg font-bold text-white font-display">Configure Mock Session</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-xs mb-1.5 font-medium text-gray-400">Target Role</label>
                    <select
                      value={role}
                      onChange={(e) => setRole(e.target.value)}
                      className="w-full bg-transparent text-xs px-3 py-2.5 rounded-xl border border-purple-500/15 outline-none text-white bg-purple-950/80"
                    >
                      <option value="AI Engineer">AI Engineer</option>
                      <option value="Gen AI Engineer">Gen AI Engineer</option>
                      <option value="ML Engineer">ML Engineer</option>
                      <option value="Software Engineer">Software Engineer</option>
                      <option value="Full Stack Developer">Full Stack Developer</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs mb-1.5 font-medium text-gray-400">Focus Topic</label>
                    <input
                      type="text"
                      value={topic}
                      onChange={(e) => setTopic(e.target.value)}
                      placeholder="e.g. System Design, Coding"
                      className="w-full bg-transparent text-xs px-3 py-2.5 rounded-xl border border-purple-500/15 outline-none text-white"
                    />
                  </div>

                  <div>
                    <label className="block text-xs mb-1.5 font-medium text-gray-400">Difficulty</label>
                    <div className="flex gap-2">
                      {["Junior", "Mid", "Senior"].map((d) => (
                        <button
                          key={d}
                          type="button"
                          onClick={() => setDifficulty(d)}
                          className="flex-1 text-xs py-2 rounded-xl border transition-all"
                          style={{
                            background: difficulty === d ? "rgba(124,107,255,0.15)" : "transparent",
                            borderColor: difficulty === d ? "var(--accent-primary)" : "rgba(124,107,255,0.15)",
                            color: difficulty === d ? "var(--text-primary)" : "var(--text-muted)",
                          }}
                        >
                          {d}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                <button
                  onClick={startSession}
                  disabled={loading || !topic.trim()}
                  className="btn-nidhi w-full py-3 text-sm"
                >
                  {loading ? "✦ Loading Questions…" : "🎙️ Start Mock Session"}
                </button>
              </div>
            ) : (
              /* Active Session Screen */
              <div className="space-y-6">
                {/* Progress Indicator */}
                <div className="flex justify-between items-center text-xs text-gray-400">
                  <span>
                    Question {currentIdx + 1} of {questions.length}
                  </span>
                  <div className="flex gap-1">
                    {questions.map((_, i) => (
                      <span
                        key={i}
                        className="w-2.5 h-2.5 rounded-full transition-all"
                        style={{
                          background:
                            i === currentIdx
                              ? "var(--accent-primary)"
                              : i < currentIdx
                              ? "var(--success)"
                              : "rgba(255,255,255,0.1)",
                        }}
                      />
                    ))}
                  </div>
                </div>

                {/* Question Card */}
                {activeQuestion && (
                  <div className="rounded-3xl p-6 space-y-4" style={cardStyle}>
                    <div className="flex justify-between items-start gap-4">
                      <h3 className="text-base font-semibold text-white leading-relaxed">
                        Q: {activeQuestion.question}
                      </h3>
                      <button
                        onClick={() => speakQuestion(activeQuestion.question)}
                        className="p-2 rounded-full hover:bg-white/5 border border-white/10 flex-shrink-0"
                        title="Read Question Out Loud"
                      >
                        {isPlayingText ? "⏹️" : "🔊"}
                      </button>
                    </div>

                    {!activeEval ? (
                      /* Input Box */
                      <div className="space-y-3">
                        <textarea
                          value={answer}
                          onChange={(e) => setAnswer(e.target.value)}
                          placeholder="Type your structured answer here… (you can also dictate using your browser voice keys)"
                          rows={6}
                          className="w-full bg-transparent p-4 text-xs outline-none border border-purple-500/10 focus:border-purple-500/40 rounded-2xl text-white resize-y font-sans"
                        />
                        <div className="flex gap-2">
                          <button
                            onClick={submitAnswer}
                            disabled={evaluating || !answer.trim()}
                            className="btn-nidhi text-xs flex-1 py-2.5"
                          >
                            {evaluating ? "✦ Evaluating answer…" : "🚀 Submit Response"}
                          </button>
                        </div>
                      </div>
                    ) : (
                      /* Evaluation Dashboard */
                      <div className="border-t border-purple-500/10 pt-4 space-y-4 animate-fade-in">
                        {/* Score and Grade block */}
                        <div className="flex items-center gap-5 bg-purple-950/10 border border-purple-500/10 p-4 rounded-2xl">
                          <div
                            className="w-14 h-14 rounded-2xl flex items-center justify-center text-2xl font-bold text-violet-300"
                            style={{ background: "rgba(124,107,255,0.15)" }}
                          >
                            {activeEval.grade}
                          </div>
                          <div>
                            <h4 className="text-sm font-bold text-white">
                              Score: {activeEval.score_percentage}%
                            </h4>
                            <p className="text-xs text-gray-400 mt-0.5">
                              {activeEval.feedback_summary}
                            </p>
                          </div>
                        </div>

                        {/* Pros / Cons grid */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div className="p-4 rounded-2xl border border-green-500/10 bg-green-500/5">
                            <span className="text-[10px] font-bold text-green-400 uppercase">
                              👍 Strengths
                            </span>
                            <ul className="list-disc ml-4 mt-2 space-y-1">
                              {activeEval.strengths?.map((s, i) => (
                                <li key={i} className="text-xs text-gray-300">
                                  {s}
                                </li>
                              ))}
                            </ul>
                          </div>

                          <div className="p-4 rounded-2xl border border-yellow-500/10 bg-yellow-500/5">
                            <span className="text-[10px] font-bold text-yellow-400 uppercase">
                              💡 Areas to Refine
                            </span>
                            <ul className="list-disc ml-4 mt-2 space-y-1">
                              {activeEval.improvements?.map((imp, i) => (
                                <li key={i} className="text-xs text-gray-300">
                                  {imp}
                                </li>
                              ))}
                            </ul>
                          </div>
                        </div>

                        {/* Ideal answer drawer */}
                        <div>
                          <button
                            onClick={() => setShowIdealAnswer(!showIdealAnswer)}
                            className="text-xs text-purple-300 hover:underline flex items-center gap-1"
                          >
                            {showIdealAnswer ? "🙈 Hide Ideal Answer" : "👁️ View Nidhi's Suggested Answer"}
                          </button>
                          {showIdealAnswer && (
                            <div className="mt-2.5 p-4 rounded-2xl bg-white/5 border border-white/10 text-xs text-gray-300 leading-relaxed whitespace-pre-wrap">
                              {activeEval.sample_ideal_answer}
                            </div>
                          )}
                        </div>

                        <button onClick={nextQuestion} className="btn-nidhi w-full py-2.5 text-xs">
                          {currentIdx === questions.length - 1 ? "Finish Session" : "Next Question →"}
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </main>
      </div>
    </>
  );
}
