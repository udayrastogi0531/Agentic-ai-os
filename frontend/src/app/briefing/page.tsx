"use client";

import { useState, useEffect, useRef } from "react";
import Sidebar from "@/components/dashboard/Sidebar";
import api from "@/lib/api";
import useAuth from "@/hooks/useAuth";

export default function BriefingPage() {
  useAuth();
  const [brief, setBrief] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    // Fetch briefing from API
    (api as any).getBriefing?.()
      .then((res: any) => {
        setBrief(res.brief || "");
        setLoading(false);
      })
      .catch((err: any) => {
        console.error("Error loading daily brief:", err);
        setBrief(
          "### 🌸 Namaste Uday!\n\nKuch connectivity issues ki wajah se main brief update nahi kar payi. Let's make today productive anyway!"
        );
        setLoading(false);
      });
  }, []);

  const handlePlayBriefing = async () => {
    if (!brief || isPlaying) return;
    setIsPlaying(true);

    const speakableText = brief
      .replace(/[#*`_\-]/g, "") // remove markdown characters
      .replace(/☕|🌸|😊|📝|💼|🎯|✅/g, "") // remove emoji icons
      .trim();

    try {
      // Priority 1 & 2: Edge TTS / Piper TTS from backend API
      const audioBlob = await api.synthesizeSpeech(speakableText);
      const audioUrl = URL.createObjectURL(audioBlob);

      if (audioRef.current) {
        audioRef.current.pause();
      }

      const audio = new Audio(audioUrl);
      audioRef.current = audio;
      audio.onended = () => setIsPlaying(false);
      await audio.play();
    } catch (err) {
      console.warn("Backend TTS failed, using browser client-side fallback Speech API", err);
      // Priority 3: Browser Speech API fallback
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(speakableText);
        const voices = window.speechSynthesis.getVoices();
        const preferred =
          voices.find((v) => v.lang.startsWith("en") && v.name.toLowerCase().includes("female")) ||
          voices.find((v) => v.lang.startsWith("en")) ||
          voices[0];
        if (preferred) utterance.voice = preferred;
        utterance.rate = 0.95;
        utterance.pitch = 1.1;
        utterance.onend = () => setIsPlaying(false);
        window.speechSynthesis.speak(utterance);
      } else {
        setIsPlaying(false);
      }
    }
  };

  const handleStopBriefing = () => {
    if (audioRef.current) {
      audioRef.current.pause();
    }
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    setIsPlaying(false);
  };

  function renderBoldText(text: string) {
    const parts = text.split(/\*\*(.*?)\*\*/g);
    return parts.map((part, i) =>
      i % 2 === 1 ? (
        <strong key={i} className="text-purple-300 font-semibold">
          {part}
        </strong>
      ) : (
        part
      )
    );
  }

  function parseMarkdown(text: string) {
    if (!text) return null;
    return text.split("\n").map((line, idx) => {
      if (line.startsWith("### ")) {
        return (
          <h3 key={idx} className="text-lg font-bold mt-4 mb-2 text-violet-300 font-display">
            {line.slice(4)}
          </h3>
        );
      }
      if (line.startsWith("## ")) {
        return (
          <h2 key={idx} className="text-xl font-bold mt-5 mb-2.5 text-violet-400 font-display">
            {line.slice(3)}
          </h2>
        );
      }
      if (line.startsWith("# ")) {
        return (
          <h1 key={idx} className="text-2xl font-bold mt-6 mb-3 text-purple-400 font-display">
            {line.slice(2)}
          </h1>
        );
      }
      if (line.startsWith("- ") || line.startsWith("* ")) {
        return (
          <li key={idx} className="ml-5 list-disc text-sm py-1 text-gray-300 leading-relaxed">
            {renderBoldText(line.slice(2))}
          </li>
        );
      }
      if (line.trim() === "") return <div key={idx} className="h-2.5" />;
      return (
        <p key={idx} className="text-sm my-2 leading-relaxed text-gray-300">
          {renderBoldText(line)}
        </p>
      );
    });
  }

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
                ☕ Daily Briefing
              </h1>
              <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                Start your day aligned with Nidhi's agenda check-in
              </p>
            </div>
            <div className="flex gap-2">
              {isPlaying ? (
                <button onClick={handleStopBriefing} className="btn-ghost text-xs px-4 py-2">
                  ⏹️ Stop Speech
                </button>
              ) : (
                <button
                  onClick={handlePlayBriefing}
                  disabled={loading || !brief}
                  className="btn-nidhi text-xs px-4 py-2"
                >
                  🔊 Read Briefing
                </button>
              )}
            </div>
          </header>

          <div className="max-w-3xl mx-auto px-6 py-10">
            {loading ? (
              <div className="flex flex-col items-center py-20 gap-4">
                <div
                  className="w-14 h-14 rounded-full"
                  style={{
                    background: "linear-gradient(135deg, #7c6bff, #e879f9)",
                    animation: "breathe 1.5s ease-in-out infinite",
                    boxShadow: "0 0 20px rgba(124, 107, 255, 0.4)",
                  }}
                />
                <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                  Nidhi is preparing today's briefing…
                </p>
              </div>
            ) : (
              <div
                className="rounded-3xl p-8 transition-all animate-fade-in"
                style={{
                  background: "rgba(17, 17, 40, 0.75)",
                  border: "1px solid rgba(124, 107, 255, 0.12)",
                  backdropFilter: "blur(20px)",
                }}
              >
                {/* Visual Orb representation */}
                <div className="flex items-center gap-4 mb-6 border-b border-purple-500/10 pb-5">
                  <div
                    className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0"
                    style={{
                      background: "linear-gradient(135deg, #7c6bff, #a855f7, #e879f9)",
                      boxShadow: "0 0 15px rgba(124, 107, 255, 0.5)",
                      animation: isPlaying ? "orb-speak 1s ease-in-out infinite" : "breathe 4s ease-in-out infinite",
                    }}
                  >
                    ✦
                  </div>
                  <div>
                    <h3 className="font-semibold text-sm" style={{ color: "var(--text-primary)" }}>
                      Nidhi's Daily Report
                    </h3>
                    <p className="text-[10px]" style={{ color: "var(--text-muted)" }}>
                      Aggregated schedule, goals status, and career updates
                    </p>
                  </div>
                </div>

                <div className="prose prose-invert max-w-none text-left">
                  {parseMarkdown(brief)}
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </>
  );
}
