"use client";

/**
 * Nidhi — Chat Window Component
 *
 * Full-featured chat interface with streaming, markdown, voice mode, and read-aloud support.
 */

import { useState, useRef, useEffect, useCallback } from "react";
import api from "@/lib/api";
import { WebSocketClient } from "@/lib/ws";
import type { Message } from "@/types";
import VoiceOverlay from "@/components/voice/VoiceOverlay";

interface ChatWindowProps {
  conversationId?: string;
}

export default function ChatWindow({ conversationId }: ChatWindowProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [agentStatus, setAgentStatus] = useState("");
  const [currentConvId, setCurrentConvId] = useState(conversationId);
  const [isVoiceOpen, setIsVoiceOpen] = useState(false);
  const [isVoiceOutputEnabled, setIsVoiceOutputEnabled] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const wsRef = useRef<WebSocketClient | null>(null);
  const activeAudioRef = useRef<HTMLAudioElement | null>(null);

  // Sync ref to read latest voice-output status inside websocket callbacks
  const isVoiceOutputEnabledRef = useRef(isVoiceOutputEnabled);
  useEffect(() => {
    isVoiceOutputEnabledRef.current = isVoiceOutputEnabled;
  }, [isVoiceOutputEnabled]);

  // Scroll to bottom
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingContent, scrollToBottom]);

  // Load conversation history on mount or when currentConvId changes
  useEffect(() => {
    if (currentConvId) {
      api.getConversation(currentConvId)
        .then((data: any) => {
          if (data && data.messages) {
            setMessages(data.messages);
          }
        })
        .catch((err) => console.error("Error loading conversation history:", err));
    } else {
      setMessages([]);
    }
  }, [currentConvId]);

  // Establish WebSocket connection
  useEffect(() => {
    const token = api.getToken();
    if (!token) return;

    const ws = new WebSocketClient(currentConvId, token);
    wsRef.current = ws;

    ws.connect().catch((err) => console.error("[WS] Connect error:", err));

    ws.on("token", (data) => {
      setStreamingContent((prev) => prev + (data.content || ""));
    });

    ws.on("agent_status", (data) => {
      setAgentStatus(data.content || "Thinking...");
    });

    ws.on("message_complete", (data) => {
      const metadata = data.metadata || {};
      const convId = metadata.conversation_id as string;
      const msgId = (metadata.message_id as string) || crypto.randomUUID();

      if (convId && convId !== currentConvId) {
        setCurrentConvId(convId);
      }

      const newMsg: Message = {
        id: msgId,
        conversation_id: convId || currentConvId || "",
        role: "assistant",
        content: data.content || "",
        agent_name: data.agent_name || "planner",
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, newMsg]);
      setStreamingContent("");
      setAgentStatus("");
      setIsLoading(false);

      // Synthesize audio readout if enabled
      if (isVoiceOutputEnabledRef.current && data.content) {
        api.synthesizeSpeech(data.content)
          .then((audioBlob) => {
            const audioUrl = URL.createObjectURL(audioBlob);
            if (activeAudioRef.current) {
              activeAudioRef.current.pause();
            }
            const audio = new Audio(audioUrl);
            activeAudioRef.current = audio;
            audio.play().catch((err) => console.error("Audio playback error:", err));
          })
          .catch((err) => console.error("Audio synthesis failed:", err));
      }
    });

    ws.on("error", (data) => {
      const errorMsg: Message = {
        id: crypto.randomUUID(),
        conversation_id: currentConvId || "",
        role: "assistant",
        content: `❌ Error: ${data.content || "An unknown error occurred"}`,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
      setIsLoading(false);
      setAgentStatus("");
    });

    return () => {
      ws.disconnect();
    };
  }, [currentConvId]);

  // Auto-resize textarea
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = `${Math.min(e.target.scrollHeight, 200)}px`;
  };

  // Send message
  const handleSend = async (textToSend?: string) => {
    const text = textToSend !== undefined ? textToSend.trim() : input.trim();
    if (!text || isLoading) return;

    if (textToSend === undefined) {
      setInput("");
      if (inputRef.current) inputRef.current.style.height = "auto";
    }

    // Add user message
    const userMsg: Message = {
      id: crypto.randomUUID(),
      conversation_id: currentConvId || "",
      role: "user",
      content: text,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);
    setAgentStatus("Thinking...");
    setStreamingContent("");

    if (wsRef.current && wsRef.current.isConnected) {
      wsRef.current.sendMessage(text);
    } else {
      // Fallback to REST API if WS isn't connected
      try {
        const response = (await api.sendMessage(text, currentConvId)) as {
          message: Message;
          conversation_id: string;
        };

        if (response.conversation_id && !currentConvId) {
          setCurrentConvId(response.conversation_id);
        }

        const aiMsg: Message = {
          id: response.message.id || crypto.randomUUID(),
          conversation_id: response.conversation_id,
          role: "assistant",
          content: response.message.content,
          agent_name: response.message.agent_name,
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, aiMsg]);

        // Synthesize audio readout if enabled
        if (isVoiceOutputEnabledRef.current && response.message.content) {
          api.synthesizeSpeech(response.message.content)
            .then((audioBlob) => {
              const audioUrl = URL.createObjectURL(audioBlob);
              if (activeAudioRef.current) activeAudioRef.current.pause();
              const audio = new Audio(audioUrl);
              activeAudioRef.current = audio;
              audio.play().catch((err) => console.error("Audio playback error:", err));
            })
            .catch((err) => console.error("Audio synthesis failed:", err));
        }
      } catch (error) {
        const errorMsg: Message = {
          id: crypto.randomUUID(),
          conversation_id: currentConvId || "",
          role: "assistant",
          content: `❌ Error: ${error instanceof Error ? error.message : "Failed to send message"}`,
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, errorMsg]);
      } finally {
        setIsLoading(false);
        setAgentStatus("");
      }
    }
  };

  // Handle Enter key
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Cleanup audio playback on unmount
  useEffect(() => {
    return () => {
      if (activeAudioRef.current) {
        activeAudioRef.current.pause();
      }
    };
  }, []);

  return (
    <div className="flex flex-col h-full bg-[var(--bg-primary)]">
      {/* Header */}
      <header className="sticky top-0 z-30 glass-strong px-6 py-4 flex items-center justify-between border-b border-[var(--border-color)]">
        <div>
          <h2 className="text-base font-bold" style={{ color: "var(--text-primary)" }}>
            💬 Chat with Nidhi
          </h2>
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            {currentConvId ? "Active Conversation" : "Start a conversation"}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {/* Audio Output Toggle */}
          <button
            onClick={() => {
              if (isVoiceOutputEnabled && activeAudioRef.current) {
                activeAudioRef.current.pause();
              }
              setIsVoiceOutputEnabled(!isVoiceOutputEnabled);
            }}
            className="px-3 py-1.5 rounded-lg transition-all text-xs font-semibold hover:bg-[var(--bg-hover)] border border-[var(--border-color)]"
            style={{
              background: isVoiceOutputEnabled ? "rgba(99,102,241,0.15)" : "var(--bg-card)",
              borderColor: isVoiceOutputEnabled ? "var(--accent-primary)" : "var(--border-color)",
              color: isVoiceOutputEnabled ? "var(--accent-primary)" : "var(--text-secondary)",
            }}
          >
            {isVoiceOutputEnabled ? "🔊 Read Aloud On" : "🔇 Silent Mode"}
          </button>
          {currentConvId && (
            <button
              onClick={() => {
                setCurrentConvId(undefined);
                setMessages([]);
              }}
              className="text-xs px-3 py-1.5 rounded-lg font-semibold transition-all hover:bg-[var(--bg-hover)] border border-[var(--border-color)]"
              style={{ color: "var(--text-secondary)" }}
            >
              ➕ New Thread
            </button>
          )}
        </div>
      </header>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full animate-fade-in py-10">
            <div
              className="w-16 h-16 rounded-2xl flex items-center justify-center text-3xl mb-6 shadow-glow animate-pulse-glow"
              style={{ background: "var(--gradient-primary)" }}
            >
              🧠
            </div>
            <h2 className="text-2xl font-bold gradient-text mb-2 animate-fade-in">
              Hey! I&apos;m Nidhi
            </h2>
            <p className="text-center max-w-md text-sm" style={{ color: "var(--text-secondary)" }}>
              Your personal AI operating system. Ask me anything — I can research, code,
              manage tasks, take notes, and much more!
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-8 max-w-lg w-full">
              {[
                "🔍 Research AI Engineer jobs in India",
                "💻 Write a Python function to sort a list",
                "📝 Create a note about my project ideas",
                "✅ Add task: Complete portfolio website",
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => setInput(suggestion.slice(2).trim())}
                  className="text-left px-4 py-3 rounded-xl text-sm transition-all duration-200"
                  style={{
                    background: "var(--bg-card)",
                    border: "1px solid var(--border-color)",
                    color: "var(--text-secondary)",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = "var(--accent-primary)";
                    e.currentTarget.style.color = "var(--text-primary)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = "var(--border-color)";
                    e.currentTarget.style.color = "var(--text-secondary)";
                  }}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"} ${
              msg.role === "user" ? "chat-message-user" : "chat-message-ai"
            }`}
          >
            <div
              className="max-w-[80%] rounded-2xl px-5 py-3.5"
              style={{
                background:
                  msg.role === "user"
                    ? "var(--accent-primary)"
                    : "var(--bg-card)",
                border:
                  msg.role === "user"
                    ? "none"
                    : "1px solid var(--border-color)",
                color: msg.role === "user" ? "white" : "var(--text-primary)",
              }}
            >
              {msg.agent_name && msg.role === "assistant" && (
                <div
                  className="text-xs font-semibold mb-1 flex items-center gap-1"
                  style={{ color: "var(--accent-secondary)" }}
                >
                  🤖 {msg.agent_name.toUpperCase()} AGENT
                </div>
              )}
              <div className="prose text-sm whitespace-pre-wrap">{msg.content}</div>
              <div
                className="text-[10px] mt-2 opacity-60 text-right"
                style={{
                  color: msg.role === "user" ? "rgba(255,255,255,0.7)" : "var(--text-muted)",
                }}
              >
                {new Date(msg.created_at).toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}

        {/* Streaming Content */}
        {streamingContent && (
          <div className="flex justify-start chat-message-ai">
            <div
              className="max-w-[80%] rounded-2xl px-5 py-3.5"
              style={{
                background: "var(--bg-card)",
                border: "1px solid var(--border-color)",
                color: "var(--text-primary)",
              }}
            >
              <div className="prose text-sm whitespace-pre-wrap">{streamingContent}</div>
            </div>
          </div>
        )}

        {/* Agent Status */}
        {isLoading && !streamingContent && (
          <div className="flex justify-start animate-fade-in">
            <div
              className="rounded-2xl px-5 py-3.5 flex items-center gap-3"
              style={{
                background: "var(--bg-card)",
                border: "1px solid var(--border-color)",
              }}
            >
              <div className="typing-indicator flex gap-1">
                <span />
                <span />
                <span />
              </div>
              <span className="text-sm" style={{ color: "var(--text-secondary)" }}>
                {agentStatus || "Thinking..."}
              </span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div
        className="border-t px-6 py-4"
        style={{ borderColor: "var(--border-color)", background: "var(--bg-secondary)" }}
      >
        <div
          className="flex items-end gap-3 rounded-2xl px-4 py-3 bg-[var(--bg-tertiary)] border border-[var(--border-color)]"
        >
          <textarea
            ref={inputRef}
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder="Message Nidhi…"
            rows={1}
            className="flex-1 bg-transparent text-sm resize-none outline-none"
            style={{
              color: "var(--text-primary)",
              maxHeight: "200px",
              lineHeight: "1.5",
            }}
          />
          <div className="flex items-center gap-1.5">
            {/* Mic Toggle Button */}
            <button
              onClick={() => setIsVoiceOpen(true)}
              className="flex items-center justify-center w-10 h-10 rounded-xl transition-all duration-200 hover:bg-[var(--bg-hover)] border border-[var(--border-color)]"
              title="Speech-to-Text Input"
            >
              🎙️
            </button>
            <button
              onClick={() => handleSend()}
              disabled={!input.trim() || isLoading}
              className="flex items-center justify-center w-10 h-10 rounded-xl transition-all duration-200"
              style={{
                background:
                  input.trim() && !isLoading
                    ? "var(--gradient-primary)"
                    : "var(--bg-hover)",
                cursor: input.trim() && !isLoading ? "pointer" : "not-allowed",
                opacity: input.trim() && !isLoading ? 1 : 0.5,
              }}
            >
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="white"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M22 2L11 13" />
                <path d="M22 2L15 22L11 13L2 9L22 2Z" />
              </svg>
            </button>
          </div>
        </div>
        <p className="text-xs text-center mt-2" style={{ color: "var(--text-muted)" }}>
          Nidhi can make mistakes. Always verify important information. 💜
        </p>
      </div>

      {/* Speech-to-Text Recording Modal overlay */}
      <VoiceOverlay
        isOpen={isVoiceOpen}
        onClose={() => setIsVoiceOpen(false)}
        onSendText={(text) => {
          handleSend(text);
        }}
      />
    </div>
  );
}
