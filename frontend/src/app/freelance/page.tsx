"use client";

import { useState, useEffect } from "react";
import Sidebar from "@/components/dashboard/Sidebar";
import api from "@/lib/api";
import useAuth from "@/hooks/useAuth";

interface Gig {
  id: number;
  title: string;
  platform: string;
  budget: string;
  description: string;
  match_score: number;
  required_skills: string[];
}

export default function FreelancePage() {
  useAuth();
  const [gigs, setGigs] = useState<Gig[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState<number | null>(null);
  const [selectedGig, setSelectedGig] = useState<Gig | null>(null);
  const [proposal, setProposal] = useState<string | null>(null);

  useEffect(() => {
    loadGigs();
  }, []);

  const loadGigs = async () => {
    try {
      const res = await (api as any).getFreelanceGigs?.();
      setGigs(res?.gigs || []);
    } catch (err) {
      console.error("Failed to load freelance gigs", err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateProposal = async (gig: Gig) => {
    setGenerating(gig.id);
    setSelectedGig(gig);
    setProposal(null);
    try {
      const res = await (api as any).generateFreelanceProposal?.({
        title: gig.title,
        platform: gig.platform,
        description: gig.description,
        budget: gig.budget,
      });
      setProposal(res.proposal);
    } catch (err) {
      setProposal("Failed to generate freelance bid proposal.");
    } finally {
      setGenerating(null);
    }
  };

  const cardStyle = {
    background: "rgba(17, 17, 40, 0.75)",
    border: "1px solid rgba(124, 107, 255, 0.12)",
    backdropFilter: "blur(16px)",
  };

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
                💻 Freelancing Assistant
              </h1>
              <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                Find matched gigs on Upwork and Wellfound, and write high-conversion proposals
              </p>
            </div>
            <button onClick={loadGigs} className="btn-ghost text-xs px-3.5 py-1.5">
              🔄 Refresh matched gigs
            </button>
          </header>

          <div className="max-w-5xl mx-auto px-6 py-8 grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Gigs List */}
            <div className="lg:col-span-2 space-y-4">
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
              ) : gigs.length === 0 ? (
                <div className="text-center py-16 rounded-3xl border border-purple-500/10 p-6 bg-purple-950/5">
                  <span className="text-4xl block mb-3">💻</span>
                  <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                    No freelance matches found yet. Please make sure your profile has your core skills updated!
                  </p>
                </div>
              ) : (
                gigs.map((gig) => (
                  <div key={gig.id} className="rounded-2xl p-5 space-y-3" style={cardStyle}>
                    <div className="flex justify-between items-start gap-4">
                      <div>
                        <div className="flex gap-2 items-center flex-wrap">
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-300 font-semibold uppercase">
                            {gig.platform}
                          </span>
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-green-500/10 border border-green-500/20 text-green-400 font-bold">
                            💰 {gig.budget}
                          </span>
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-300 font-bold">
                            {gig.match_score}% Match
                          </span>
                        </div>
                        <h3 className="text-base font-bold mt-2.5 text-white">{gig.title}</h3>
                      </div>
                      <button
                        onClick={() => handleGenerateProposal(gig)}
                        disabled={generating != null}
                        className="btn-nidhi text-xs px-3.5 py-2 whitespace-nowrap"
                      >
                        {generating === gig.id ? "✦ proposal…" : "✉️ Bid Proposal"}
                      </button>
                    </div>

                    <p className="text-xs text-gray-400 leading-relaxed">{gig.description}</p>

                    <div className="flex flex-wrap gap-1 pt-1">
                      {gig.required_skills?.map((s) => (
                        <span
                          key={s}
                          className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 border border-white/10 text-gray-300"
                        >
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Proposal Panel */}
            <div>
              <div
                className="rounded-3xl p-5 min-h-[400px] flex flex-col"
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
                    <h3 className="text-sm font-semibold text-white">Proposal Builder</h3>
                    <p className="text-[9px] text-gray-500">Auto-matches proposal copy based on skills</p>
                  </div>
                </div>

                {selectedGig ? (
                  <div className="flex-1 flex flex-col h-full">
                    <div className="flex justify-between items-center mb-3">
                      <h4 className="text-xs font-bold text-purple-300 truncate max-w-[70%]">
                        Bid: {selectedGig.title}
                      </h4>
                      {proposal && (
                        <button
                          onClick={() => {
                            navigator.clipboard.writeText(proposal);
                            alert("Proposal copied to clipboard, Uday!");
                          }}
                          className="text-[10px] text-purple-300 hover:underline"
                        >
                          📋 Copy Bid
                        </button>
                      )}
                    </div>

                    {generating === selectedGig.id ? (
                      <div className="flex-1 flex flex-col items-center justify-center py-20 space-y-2">
                        <div className="w-6 h-6 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
                        <p className="text-xs text-gray-400">Nidhi is writing proposal copy…</p>
                      </div>
                    ) : (
                      <pre
                        className="flex-1 text-[11px] leading-relaxed text-gray-300 whitespace-pre-wrap overflow-y-auto max-h-[460px] bg-black/30 p-3 rounded-2xl border border-white/5 font-sans"
                        style={{ outline: "none" }}
                      >
                        {proposal}
                      </pre>
                    )}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-24 text-center text-gray-500 space-y-2">
                    <span className="text-2xl">✉️</span>
                    <p className="text-xs">
                      Click the **Bid Proposal** button on any matched project card to construct customized proposal template copy here.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </main>
      </div>
    </>
  );
}
