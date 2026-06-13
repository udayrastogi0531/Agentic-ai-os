"use client";

import { useState, useEffect, useRef } from "react";
import Sidebar from "@/components/dashboard/Sidebar";
import CommandBar from "@/components/CommandBar";
import Link from "next/link";
import useAuth from "@/hooks/useAuth";
import api from "@/lib/api";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles,
  Play,
  Square,
  Brain,
  Calendar,
  Mail,
  MessageSquare,
  FileText,
  ChevronRight,
  Clock,
  Briefcase,
  Globe,
  Settings
} from "lucide-react";

function getGreeting(name: string): { text: string; emoji: string } {
  const hour = new Date().getHours();
  const first = name?.split(" ")[0] || "Uday";
  if (hour < 5)  return { text: `Still working, ${first}?`, emoji: "🌙" };
  if (hour < 12) return { text: `Good morning, ${first} ❤️`, emoji: "🌅" };
  if (hour < 17) return { text: `Good afternoon, ${first} ❤️`, emoji: "☀️" };
  if (hour < 21) return { text: `Good evening, ${first} ❤️`, emoji: "🌆" };
  return { text: `Good night, ${first} ❤️`, emoji: "🌙" };
}

function getNidhiMessage(): string {
  const messages = [
    "Main yahaan hoon, Uday. Aaj kya karna hai? ❤️",
    "Kya chal raha hai? Main sab sambhal lungi. ✨",
    "Ready hoon — bolo kya help chahiye? 💜",
    "Aaj ka din productive banate hain! 🚀",
    "Main hoon na, Uday. Koi bhi kaam bolo. 🤍",
  ];
  return messages[Math.floor(Math.random() * messages.length)];
}

const QUICK_ACTIONS = [
  { id: "chat", icon: <MessageSquare className="w-5 h-5 text-purple-400" />, label: "Smart Chat", sub: "Hinglish chat session", href: "/chat" },
  { id: "voice", icon: <Sparkles className="w-5 h-5 text-pink-400" />, label: "Voice Mode", sub: "Talk to Nidhi", href: "/voice" },
  { id: "files", icon: <FileText className="w-5 h-5 text-blue-400" />, label: "File Chat", sub: "PDF & RAG parsing", href: "/files" },
  { id: "research", icon: <Globe className="w-5 h-5 text-emerald-400" />, label: "Research Agent", sub: "Deep web research", href: "/research" },
  { id: "career", icon: <Briefcase className="w-5 h-5 text-yellow-400" />, label: "Career Coach", sub: "Skill maps & advice", href: "/career" },
  { id: "gmail", icon: <Mail className="w-5 h-5 text-rose-400" />, label: "Gmail Summary", sub: "Email assistant", href: "/gmail" },
  { id: "calendar", icon: <Calendar className="w-5 h-5 text-cyan-400" />, label: "My Schedule", sub: "View today's plan", href: "/calendar" },
];

export default function NidhiHomePage() {
  const { user } = useAuth();
  const [nidhiMsg] = useState(getNidhiMessage);
  const [tasks, setTasks] = useState<any[]>([]);
  const [memories, setMemories] = useState<any[]>([]);
  const [briefing, setBriefing] = useState<string>("");
  const [loadingBriefing, setLoadingBriefing] = useState<boolean>(true);
  const [isPlayingBrief, setIsPlayingBrief] = useState<boolean>(false);
  const [cmdOpen, setCmdOpen] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());

  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Time & Date Updates
  useEffect(() => {
    const t = setInterval(() => setCurrentTime(new Date()), 60000);
    return () => clearInterval(t);
  }, []);

  // Fetch Home Widgets Data
  useEffect(() => {
    if (!user) return;
    
    // Load tasks
    api.getTasks().then((r: any) => {
      if (r?.items) setTasks(r.items.slice(0, 4));
    }).catch(() => {});

    // Load recent memories
    api.getMemories().then((r: any) => {
      if (r?.items) {
        setMemories(r.items.slice(0, 4));
      } else if (Array.isArray(r)) {
        setMemories(r.slice(0, 4));
      }
    }).catch(() => {});

    // Load briefing
    api.getBriefing().then((r: any) => {
      if (r?.brief) setBriefing(r.brief);
      setLoadingBriefing(false);
    }).catch(() => {
      setBriefing("Namaste Uday! Let's tackle today's projects and learnings. Main help ke liye ready hoon.");
      setLoadingBriefing(false);
    });
  }, [user]);

  // Command+K listener
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        setCmdOpen(true);
      }
      if (e.key === "Escape") setCmdOpen(false);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  // Audio briefing controls
  const handlePlayBriefing = async () => {
    if (!briefing || isPlayingBrief) return;
    setIsPlayingBrief(true);

    const speakableText = briefing
      .replace(/[#*`_\-]/g, "")
      .replace(/☕|🌸|😊|📝|💼|🎯|✅|❤️/g, "")
      .trim();

    try {
      const audioBlob = await api.synthesizeSpeech(speakableText);
      const audioUrl = URL.createObjectURL(audioBlob);

      if (audioRef.current) {
        audioRef.current.pause();
      }

      const audio = new Audio(audioUrl);
      audioRef.current = audio;
      audio.onended = () => setIsPlayingBrief(false);
      await audio.play();
    } catch (err) {
      console.warn("Backend TTS synthesis failed, running browser fallback SpeechSynthesis", err);
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
        utterance.onend = () => setIsPlayingBrief(false);
        window.speechSynthesis.speak(utterance);
      } else {
        setIsPlayingBrief(false);
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
    setIsPlayingBrief(false);
  };

  const greeting = getGreeting(user?.name || "Uday");

  const formattedDate = currentTime.toLocaleDateString("en-IN", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });

  const formattedTime = currentTime.toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
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
          <div className="max-w-6xl mx-auto px-8 py-10 space-y-8">
            
            {/* Header / Top Panel */}
            <div className="flex items-center justify-between border-b border-purple-500/10 pb-6">
              <div>
                <span className="text-xs uppercase tracking-wider text-purple-400 font-semibold">
                  Personal AI OS
                </span>
                <h1 className="text-3xl font-extrabold tracking-tight mt-1 text-white font-display">
                  Nidhi AI
                </h1>
              </div>
              <div className="text-right text-xs text-gray-400">
                <p className="font-semibold text-gray-200">{formattedDate}</p>
                <p className="mt-0.5">{formattedTime} · India Standard Time</p>
              </div>
            </div>

            {/* Hero Split Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              
              {/* Left Column: Greeting & Quick Ask */}
              <div className="lg:col-span-2 space-y-6 flex flex-col justify-center">
                <motion.div
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5 }}
                >
                  <h2 className="text-4xl font-extrabold leading-tight text-white font-display">
                    {greeting.emoji} {greeting.text}
                  </h2>
                  <p className="text-lg mt-3 text-purple-300 font-medium max-w-lg">
                    {nidhiMsg}
                  </p>
                </motion.div>

                {/* Notion-style Quick Command launcher */}
                <div
                  className="flex items-center gap-3 rounded-2xl px-5 py-4 cursor-pointer hover:border-purple-500/30 transition-all border border-purple-500/10 glass-subtle"
                  onClick={() => setCmdOpen(true)}
                >
                  <span className="text-purple-400 font-bold">✦</span>
                  <span className="text-gray-400 text-sm flex-1">
                    Ask Nidhi anything... or press <span className="kbd">Ctrl</span> <span className="kbd">K</span>
                  </span>
                </div>
              </div>

              {/* Right Column: Large Animated Voice Orb */}
              <div className="flex flex-col items-center justify-center p-6 rounded-3xl border border-purple-500/10 glass-strong">
                <p className="text-xs text-gray-400 font-semibold mb-4 uppercase tracking-widest">
                  Empathetic Voice Orb
                </p>
                <Link href="/voice">
                  <div className="nidhi-orb-container w-40 h-40">
                    {/* Ripple layers */}
                    {[1.2, 1.5, 1.8].map((s, idx) => (
                      <span
                        key={idx}
                        className="absolute inset-0 rounded-full"
                        style={{
                          border: "1px solid rgba(124, 107, 255, 0.25)",
                          transform: `scale(${s})`,
                          animation: `ripple 3s ease-out infinite`,
                          animationDelay: `${idx * 0.8}s`
                        }}
                      />
                    ))}
                    {/* Central interactive Orb */}
                    <div
                      className="w-28 h-28 rounded-full flex items-center justify-center text-3xl font-bold cursor-pointer"
                      style={{
                        background: "linear-gradient(135deg, #7c6bff, #a855f7, #e879f9)",
                        boxShadow: "0 0 35px rgba(124, 107, 255, 0.6), inset 0 2px 4px rgba(255, 255, 255, 0.3)",
                        animation: "breathe 3.5s ease-in-out infinite"
                      }}
                    >
                      ✦
                    </div>
                  </div>
                </Link>
                <p className="text-xs text-purple-300 font-medium mt-4">
                  Tap Orb to enter Voice Mode
                </p>
              </div>

            </div>

            {/* Quick Actions Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {QUICK_ACTIONS.map((act) => (
                <Link
                  key={act.id}
                  href={act.href}
                  className="p-5 rounded-2xl border border-purple-500/10 glass hover:border-purple-500/30 transition-all flex flex-col gap-3 group relative overflow-hidden"
                >
                  <div className="w-10 h-10 rounded-xl bg-purple-950/40 border border-purple-500/20 flex items-center justify-center transition-all group-hover:scale-110">
                    {act.icon}
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-gray-200 group-hover:text-white transition-colors">
                      {act.label}
                    </h4>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {act.sub}
                    </p>
                  </div>
                  <ChevronRight className="absolute right-4 bottom-4 w-4 h-4 text-purple-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                </Link>
              ))}
            </div>

            {/* Three Column Widgets Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

              {/* 1. Daily Briefing Panel */}
              <div className="lg:col-span-2 rounded-3xl border border-purple-500/10 p-6 glass-strong flex flex-col">
                <div className="flex items-center justify-between border-b border-purple-500/10 pb-4 mb-4">
                  <h3 className="font-bold text-sm text-gray-200 flex items-center gap-2">
                    <span>☕</span> Today's Briefing
                  </h3>
                  <div className="flex gap-2">
                    {isPlayingBrief ? (
                      <button
                        onClick={handleStopBriefing}
                        className="text-xs px-3 py-1 rounded-full border border-red-500/30 bg-red-950/20 text-red-400 flex items-center gap-1.5 hover:bg-red-950/40 transition-colors"
                      >
                        <Square className="w-2.5 h-2.5 fill-current" /> Stop
                      </button>
                    ) : (
                      <button
                        onClick={handlePlayBriefing}
                        disabled={loadingBriefing || !briefing}
                        className="text-xs px-3 py-1 rounded-full bg-purple-600 hover:bg-purple-500 text-white flex items-center gap-1.5 transition-colors disabled:opacity-50"
                      >
                        <Play className="w-2.5 h-2.5 fill-current" /> Play Briefing
                      </button>
                    )}
                  </div>
                </div>

                <div className="flex-1 overflow-y-auto max-h-60 no-scrollbar text-sm text-gray-300 space-y-3 leading-relaxed text-left">
                  {loadingBriefing ? (
                    <div className="flex flex-col items-center justify-center py-10 gap-3">
                      <div className="w-6 h-6 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
                      <p className="text-xs text-gray-500">Formulating agenda...</p>
                    </div>
                  ) : (
                    briefing.split("\n").map((line, idx) => {
                      if (line.startsWith("- ") || line.startsWith("* ")) {
                        return <li key={idx} className="ml-4 list-disc py-0.5 text-gray-300">{line.slice(2)}</li>;
                      }
                      if (line.startsWith("### ")) {
                        return <h4 key={idx} className="font-bold text-violet-300 mt-3">{line.slice(4)}</h4>;
                      }
                      if (line.trim() === "") return null;
                      return <p key={idx}>{line}</p>;
                    })
                  )}
                </div>
              </div>

              {/* 2. Memories & Focus Panel */}
              <div className="rounded-3xl border border-purple-500/10 p-6 glass-strong flex flex-col">
                <h3 className="font-bold text-sm text-gray-200 border-b border-purple-500/10 pb-4 mb-4 flex items-center gap-2">
                  <Brain className="w-4 h-4 text-pink-400" /> Recent Memories
                </h3>
                <div className="flex-1 overflow-y-auto max-h-60 no-scrollbar space-y-3 text-left">
                  {memories.length > 0 ? (
                    memories.map((mem: any, idx: number) => (
                      <div
                        key={mem.id || idx}
                        className="p-3 rounded-xl border border-purple-500/5 bg-purple-950/10 flex items-start gap-2.5 hover:border-purple-500/20 transition-all"
                      >
                        <span className="text-xs text-purple-400 mt-0.5">✦</span>
                        <div>
                          <p className="text-xs text-gray-300 font-medium">
                            {mem.content || mem.summary}
                          </p>
                          <p className="text-[10px] text-gray-500 mt-1 flex items-center gap-1">
                            <Clock className="w-2.5 h-2.5" />
                            {mem.created_at
                              ? new Date(mem.created_at).toLocaleDateString("en-IN", {
                                  day: "numeric",
                                  month: "short",
                                })
                              : "Recent"}
                          </p>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="flex flex-col items-center justify-center py-10 gap-2">
                      <span className="text-2xl">🧠</span>
                      <p className="text-xs text-gray-500 text-center leading-relaxed">
                        Abhi koi memories nahi hain.<br />Talk to Nidhi to create memories!
                      </p>
                    </div>
                  )}
                </div>
              </div>

            </div>

          </div>
        </main>
      </div>

      <CommandBar isOpen={cmdOpen} onClose={() => setCmdOpen(false)} />
    </>
  );
}
