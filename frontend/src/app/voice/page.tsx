"use client";

/**
 * Nidhi AI OS — Voice Page
 *
 * A full-screen immersive voice interface with an animated orb
 * that changes state: Idle, Listening, Thinking, Speaking.
 */

import { useState, useEffect, useRef, useCallback } from "react";
import Sidebar from "@/components/dashboard/Sidebar";
import Link from "next/link";

type OrbState = "idle" | "listening" | "thinking" | "speaking";

interface TranscriptEntry {
  id: string;
  role: "user" | "nidhi";
  text: string;
  timestamp: Date;
}

/* ── Nidhi responses (offline fallback) ── */
const NIDHI_RESPONSES = [
  "Haan Uday, main sun rahi hoon. Bolo kya chahiye? 💜",
  "Samajh gayi. Main abhi karta hoon. ✨",
  "Bilkul! Aapke liye main yeh kar sakti hoon. 🌸",
  "Shukriya bataane ke liye. Main yeh note kar leti hoon. 📝",
  "Uday, mujhe lagta hai yeh bohot important hai. Main poora dhyan deti hoon.",
  "Aapki baat sun ke main thodi concerned hoon. Kya sab theek hai? ❤️",
];

const ORB_STATE_CONFIG: Record<OrbState, {
  label: string;
  sublabel: string;
  size: number;
  colors: string;
  glow: string;
  animation: string;
}> = {
  idle: {
    label: "Nidhi",
    sublabel: "Tap to speak",
    size: 180,
    colors: "linear-gradient(135deg, #7c6bff 0%, #a855f7 50%, #e879f9 100%)",
    glow: "rgba(124, 107, 255, 0.4)",
    animation: "orb-idle 5s ease-in-out infinite",
  },
  listening: {
    label: "Listening…",
    sublabel: "Speak now",
    size: 200,
    colors: "linear-gradient(135deg, #22d3a8 0%, #3b82f6 50%, #7c6bff 100%)",
    glow: "rgba(34, 211, 168, 0.5)",
    animation: "orb-listen 0.7s ease-in-out infinite",
  },
  thinking: {
    label: "Thinking…",
    sublabel: "Processing",
    size: 180,
    colors: "linear-gradient(135deg, #f59e0b 0%, #ef4444 50%, #a855f7 100%)",
    glow: "rgba(245, 158, 11, 0.4)",
    animation: "orb-think 2s linear infinite",
  },
  speaking: {
    label: "Speaking",
    sublabel: "Nidhi is responding",
    size: 210,
    colors: "linear-gradient(135deg, #e879f9 0%, #a855f7 50%, #7c6bff 100%)",
    glow: "rgba(232, 121, 249, 0.5)",
    animation: "orb-speak 0.9s ease-in-out infinite",
  },
};

export default function VoicePage() {
  const [orbState, setOrbState] = useState<OrbState>("idle");
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);
  const [isSupported, setIsSupported] = useState(true);
  const transcriptRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);
  const synthRef = useRef<SpeechSynthesisUtterance | null>(null);
  const orbStateRef = useRef<OrbState>("idle");

  // Check Web Speech API support
  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;
    setIsSupported(!!SpeechRecognition);
  }, []);

  // Keep ref in sync with state
  const setOrbStateSynced = (state: OrbState) => {
    orbStateRef.current = state;
    setOrbState(state);
  };

  // Auto-scroll transcript
  useEffect(() => {
    if (transcriptRef.current) {
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
    }
  }, [transcript]);

  const addEntry = (role: "user" | "nidhi", text: string) => {
    setTranscript((prev) => [
      ...prev,
      { id: crypto.randomUUID(), role, text, timestamp: new Date() },
    ]);
  };

  const speakNidhi = useCallback((text: string) => {
    setOrbStateSynced("speaking");
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      // Prefer a female English-India voice
      const voices = window.speechSynthesis.getVoices();
      const preferred = voices.find(
        (v) => v.lang.startsWith("en") && v.name.toLowerCase().includes("female")
      ) || voices.find((v) => v.lang.startsWith("en")) || voices[0];
      if (preferred) utterance.voice = preferred;
      utterance.rate = 0.95;
      utterance.pitch = 1.1;
      utterance.onend = () => setOrbStateSynced("idle");
      synthRef.current = utterance;
      window.speechSynthesis.speak(utterance);
    } else {
      setTimeout(() => setOrbStateSynced("idle"), 2500);
    }
  }, []);

  const nidhiRespond = useCallback((userText: string) => {
    setOrbStateSynced("thinking");
    const thinkTime = 1200 + Math.random() * 800;
    setTimeout(() => {
      const response =
        NIDHI_RESPONSES[Math.floor(Math.random() * NIDHI_RESPONSES.length)];
      addEntry("nidhi", response);
      speakNidhi(response.replace(/[💜✨🌸📝❤️]/g, ""));
    }, thinkTime);
  }, [speakNidhi]);

  const startListening = useCallback(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      addEntry("nidhi", "Maafi, browser mein voice support nahi hai. Chrome use karo please.");
      return;
    }

    if (orbStateRef.current === "listening") {
      recognitionRef.current?.stop();
      setOrbStateSynced("idle");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-IN";
    recognition.interimResults = false;
    recognition.continuous = false;

    recognition.onstart = () => setOrbStateSynced("listening");

    recognition.onresult = (event: any) => {
      const text = event.results[0][0].transcript;
      addEntry("user", text);
      nidhiRespond(text);
    };

    recognition.onerror = (event: any) => {
      console.error("Speech recognition error:", event.error);
      setOrbStateSynced("idle");
    };

    recognition.onend = () => {
      if (orbStateRef.current === "listening") setOrbStateSynced("idle");
    };

    recognitionRef.current = recognition;
    recognition.start();
  }, [orbState, nidhiRespond]);

  // Demo tap when Web Speech not available
  const handleOrbClick = () => {
    if (orbStateRef.current === "thinking" || orbStateRef.current === "speaking") return;
    if (orbStateRef.current === "listening") {
      recognitionRef.current?.stop();
      setOrbStateSynced("idle");
      return;
    }
    startListening();
  };

  const config = ORB_STATE_CONFIG[orbState];

  return (
    <div className="flex min-h-screen" style={{ background: "var(--bg-primary)" }}>
      {/* Aurora */}
      <div className="aurora-bg" aria-hidden />
      <Sidebar />

      <main
        className="flex-1 flex flex-col relative"
        style={{ marginLeft: "var(--sidebar-width)", zIndex: 1 }}
      >
        {/* Header */}
        <header
          className="flex items-center justify-between px-8 py-5 glass-strong"
          style={{ borderBottom: "1px solid rgba(124, 107, 255, 0.08)" }}
        >
          <div>
            <h1 className="font-bold text-lg" style={{ color: "var(--text-primary)", fontFamily: "var(--font-display)" }}>
              Voice Mode
            </h1>
            <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
              Talk to Nidhi naturally — English or Hinglish
            </p>
          </div>
          <div className="flex items-center gap-3">
            {!isSupported && (
              <span
                className="text-xs px-3 py-1.5 rounded-full"
                style={{
                  background: "rgba(248, 113, 113, 0.1)",
                  border: "1px solid rgba(248, 113, 113, 0.2)",
                  color: "var(--error)",
                }}
              >
                ⚠️ Voice not supported in this browser
              </span>
            )}
            <span
              className="px-3 py-1.5 rounded-full text-xs font-medium"
              style={{
                background:
                  orbState === "idle"
                    ? "rgba(124, 107, 255, 0.1)"
                    : orbState === "listening"
                    ? "rgba(34, 211, 168, 0.1)"
                    : orbState === "thinking"
                    ? "rgba(245, 158, 11, 0.1)"
                    : "rgba(232, 121, 249, 0.1)",
                border: "1px solid rgba(124, 107, 255, 0.2)",
                color:
                  orbState === "listening"
                    ? "var(--success)"
                    : orbState === "thinking"
                    ? "var(--warning)"
                    : orbState === "speaking"
                    ? "var(--accent-pink)"
                    : "var(--accent-tertiary)",
              }}
            >
              {orbState.charAt(0).toUpperCase() + orbState.slice(1)}
            </span>
          </div>
        </header>

        {/* Main area */}
        <div className="flex-1 flex flex-col lg:flex-row">

          {/* Orb Section */}
          <div className="flex-1 flex flex-col items-center justify-center py-12 px-8 relative">

            {/* State selector buttons (desktop) */}
            <div className="absolute top-6 right-6 flex gap-2 hidden lg:flex">
              {(["idle", "listening", "thinking", "speaking"] as OrbState[]).map((s) => (
                <button
                  key={s}
                  onClick={() => setOrbState(s)}
                  className="px-3 py-1 text-xs rounded-full transition-all"
                  style={{
                    background: orbState === s ? "rgba(124, 107, 255, 0.2)" : "transparent",
                    border: "1px solid rgba(124, 107, 255, 0.2)",
                    color: orbState === s ? "var(--text-primary)" : "var(--text-muted)",
                  }}
                >
                  {s}
                </button>
              ))}
            </div>

            {/* Nidhi Orb */}
            <div
              className="nidhi-orb-container"
              style={{ width: `${config.size + 120}px`, height: `${config.size + 120}px` }}
            >
              {/* Outer ripple rings */}
              {[1.6, 2.0, 2.5].map((scale, i) => (
                <div
                  key={i}
                  className="absolute rounded-full pointer-events-none"
                  style={{
                    width: `${config.size * scale}px`,
                    height: `${config.size * scale}px`,
                    border: `1px solid ${config.glow}`,
                    opacity: 0.3 - i * 0.08,
                    animation: `ripple ${2 + i * 0.8}s ease-out infinite`,
                    animationDelay: `${i * 0.6}s`,
                  }}
                />
              ))}

              {/* The Orb */}
              <button
                onClick={handleOrbClick}
                className="relative rounded-full flex items-center justify-center cursor-pointer transition-all"
                style={{
                  width: `${config.size}px`,
                  height: `${config.size}px`,
                  background: config.colors,
                  boxShadow: `0 0 40px ${config.glow}, 0 0 80px ${config.glow}80, inset 0 2px 0 rgba(255,255,255,0.2)`,
                  animation: config.animation,
                  border: "none",
                  outline: "none",
                  zIndex: 10,
                }}
                aria-label={`Nidhi orb — ${orbState}. Click to ${orbState === "idle" ? "start listening" : "stop"}`}
              >
                {/* Inner glow layer */}
                <div
                  className="absolute inset-4 rounded-full"
                  style={{
                    background: "radial-gradient(circle at 35% 35%, rgba(255,255,255,0.25) 0%, transparent 60%)",
                  }}
                />

                {/* Icon / indicator */}
                <div className="relative z-10 flex flex-col items-center gap-1">
                  {orbState === "idle" && (
                    <span style={{ fontSize: "3.5rem", lineHeight: 1 }}>✦</span>
                  )}
                  {orbState === "listening" && (
                    <div className="flex items-end gap-1.5">
                      {[...Array(7)].map((_, i) => (
                        <span key={i} className="voice-bar" style={{ background: "white" }} />
                      ))}
                    </div>
                  )}
                  {orbState === "thinking" && (
                    <div
                      className="w-12 h-12 rounded-full border-4 border-t-transparent animate-spin-slow"
                      style={{ borderColor: "rgba(255,255,255,0.8) transparent transparent transparent" }}
                    />
                  )}
                  {orbState === "speaking" && (
                    <div className="flex items-end gap-1.5">
                      {[...Array(7)].map((_, i) => (
                        <span
                          key={i}
                          className="voice-bar"
                          style={{
                            background: "white",
                            animationDuration: `${0.5 + i * 0.07}s`,
                          }}
                        />
                      ))}
                    </div>
                  )}
                </div>
              </button>
            </div>

            {/* Orb label */}
            <div className="text-center mt-8 animate-fade-in">
              <p
                className="font-bold text-xl"
                style={{
                  fontFamily: "var(--font-display)",
                  background: config.colors,
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                  backgroundClip: "text",
                }}
              >
                {config.label}
              </p>
              <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>
                {config.sublabel}
              </p>
            </div>

            {/* Action buttons */}
            <div className="flex gap-3 mt-8">
              <button
                className={`btn-nidhi ${orbState === "listening" ? "opacity-50" : ""}`}
                onClick={handleOrbClick}
                disabled={orbState === "thinking" || orbState === "speaking"}
              >
                {orbState === "idle" && "🎙️ Start Speaking"}
                {orbState === "listening" && "⏹️ Stop"}
                {orbState === "thinking" && "⏳ Thinking…"}
                {orbState === "speaking" && "🔊 Speaking…"}
              </button>
              <Link href="/chat" className="btn-ghost">
                💬 Switch to Chat
              </Link>
            </div>
          </div>

          {/* Transcript Panel */}
          <div
            className="w-full lg:w-96 flex flex-col glass-strong"
            style={{
              borderLeft: "1px solid rgba(124, 107, 255, 0.08)",
              minHeight: "400px",
            }}
          >
            <div
              className="px-5 py-4 flex items-center justify-between"
              style={{ borderBottom: "1px solid rgba(124, 107, 255, 0.08)" }}
            >
              <h3 className="font-semibold text-sm" style={{ color: "var(--text-primary)" }}>
                Conversation
              </h3>
              {transcript.length > 0 && (
                <button
                  className="text-xs"
                  style={{ color: "var(--text-muted)" }}
                  onClick={() => setTranscript([])}
                >
                  Clear
                </button>
              )}
            </div>

            <div
              ref={transcriptRef}
              className="flex-1 overflow-y-auto px-4 py-4 space-y-3"
              style={{ minHeight: "300px" }}
            >
              {transcript.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full gap-3 py-8">
                  <div
                    className="w-14 h-14 rounded-full flex items-center justify-center"
                    style={{
                      background: "linear-gradient(135deg, #7c6bff, #e879f9)",
                      boxShadow: "0 0 20px rgba(124, 107, 255, 0.3)",
                    }}
                  >
                    <span style={{ fontSize: "1.5rem" }}>✦</span>
                  </div>
                  <p className="text-sm text-center" style={{ color: "var(--text-muted)" }}>
                    Orb pe tap karo<br />aur baat karo Nidhi se
                  </p>
                </div>
              ) : (
                transcript.map((entry) => (
                  <div
                    key={entry.id}
                    className={`flex gap-3 ${entry.role === "user" ? "flex-row-reverse" : "flex-row"}`}
                  >
                    {/* Avatar */}
                    <div
                      className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold"
                      style={{
                        background:
                          entry.role === "nidhi"
                            ? "linear-gradient(135deg, #7c6bff, #e879f9)"
                            : "rgba(124, 107, 255, 0.2)",
                        boxShadow:
                          entry.role === "nidhi"
                            ? "0 0 10px rgba(124, 107, 255, 0.3)"
                            : "none",
                      }}
                    >
                      {entry.role === "nidhi" ? "✦" : "U"}
                    </div>
                    {/* Bubble */}
                    <div
                      className="max-w-[78%] px-3 py-2.5 rounded-2xl text-sm"
                      style={{
                        background:
                          entry.role === "nidhi"
                            ? "rgba(124, 107, 255, 0.1)"
                            : "rgba(255, 255, 255, 0.05)",
                        border: "1px solid rgba(124, 107, 255, 0.12)",
                        color: "var(--text-secondary)",
                        borderRadius:
                          entry.role === "nidhi"
                            ? "4px 18px 18px 18px"
                            : "18px 4px 18px 18px",
                      }}
                    >
                      {entry.text}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
