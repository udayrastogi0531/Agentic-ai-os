"use client";

/**
 * Nidhi — Voice Overlay Component
 *
 * Premium glassmorphic voice interaction overlay with waveform visualizer.
 */

import { useState, useRef, useEffect } from "react";
import api from "@/lib/api";

interface VoiceOverlayProps {
  isOpen: boolean;
  onClose: () => void;
  onSendText?: (text: string) => void;
}

export default function VoiceOverlay({ isOpen, onClose, onSendText }: VoiceOverlayProps) {
  const [status, setStatus] = useState<"idle" | "listening" | "processing" | "speaking">("idle");
  const [transcription, setTranscription] = useState("");
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [bars, setBars] = useState<number[]>([10, 10, 10, 10, 10]);

  // Waveform animation loop
  useEffect(() => {
    let animFrame: number;
    const updateWaveform = () => {
      if (status === "listening") {
        setBars(Array.from({ length: 15 }, () => Math.floor(Math.random() * 40) + 10));
      } else if (status === "speaking") {
        setBars(Array.from({ length: 15 }, () => Math.floor(Math.random() * 30) + 10));
      } else {
        setBars(Array.from({ length: 15 }, () => 10));
      }
      animFrame = requestAnimationFrame(updateWaveform);
    };

    updateWaveform();
    return () => cancelAnimationFrame(animFrame);
  }, [status]);

  // Start recording
  const startRecording = async () => {
    audioChunksRef.current = [];
    setTranscription("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/wav" });
        await handleSTT(audioBlob);
      };

      mediaRecorder.start();
      setStatus("listening");
    } catch (err) {
      console.error("Failed to start mic:", err);
      alert("Please allow microphone permissions to use voice mode.");
      onClose();
    }
  };

  // Stop recording
  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      mediaRecorderRef.current.stop();
      // Stop the stream tracks
      mediaRecorderRef.current.stream.getTracks().forEach((track) => track.stop());
      setStatus("processing");
    }
  };

  // Handle Speech-to-Text
  const handleSTT = async (blob: Blob) => {
    try {
      const res = await api.transcribeAudio(blob);
      const text = res.text.trim();
      setTranscription(text);

      if (text) {
        if (onSendText) {
          onSendText(text);
        }
        setStatus("idle");
        onClose();
      } else {
        setStatus("idle");
      }
    } catch (err) {
      console.error("STT process failed:", err);
      setStatus("idle");
    }
  };

  // Trigger recording on modal open
  useEffect(() => {
    if (isOpen) {
      startRecording();
    } else {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
        mediaRecorderRef.current.stop();
      }
      setStatus("idle");
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-black/80 backdrop-blur-md p-6 animate-fade-in">
      <button
        onClick={onClose}
        className="absolute top-6 right-6 w-12 h-12 rounded-xl flex items-center justify-center border transition-all text-lg hover:bg-[var(--bg-hover)]"
        style={{ borderColor: "var(--border-color)", color: "var(--text-secondary)" }}
      >
        ✕
      </button>

      {/* Voice Assistant Visualizer */}
      <div className="flex flex-col items-center max-w-lg text-center space-y-8">
        <div
          className={`w-32 h-32 rounded-full flex items-center justify-center shadow-glow transition-all duration-300 ${
            status === "listening" ? "scale-105 animate-pulse-glow" : ""
          }`}
          style={{ background: "var(--gradient-primary)" }}
        >
          <span className="text-4xl">🎙️</span>
        </div>

        <div>
          <h2 className="text-xl font-bold uppercase tracking-wider gradient-text">
            {status === "listening" && "Listening..."}
            {status === "processing" && "Processing..."}
            {status === "speaking" && "Nidhi speaking"}
            {status === "idle" && "Tap mic to talk"}
          </h2>
          <p className="text-sm mt-2 max-w-sm" style={{ color: "var(--text-secondary)" }}>
            {transcription && `You: "${transcription}"`}
          </p>
        </div>

        {/* Waveform Visualization */}
        <div className="flex items-center gap-1.5 h-16">
          {bars.map((barHeight, idx) => (
            <div
              key={idx}
              className="w-1.5 rounded-full transition-all duration-150"
              style={{
                height: `${barHeight}px`,
                background: "var(--gradient-primary)",
              }}
            />
          ))}
        </div>

        {/* Action Controls */}
        <div className="flex gap-4">
          {status === "listening" ? (
            <button
              onClick={stopRecording}
              className="px-6 py-3 rounded-xl text-sm font-semibold text-white transition-all bg-red-600 hover:bg-red-700"
            >
              🛑 Done Speaking
            </button>
          ) : (
            <button
              onClick={startRecording}
              className="px-6 py-3 rounded-xl text-sm font-semibold text-white transition-all"
              style={{ background: "var(--gradient-primary)" }}
            >
              🎙️ Talk Again
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
