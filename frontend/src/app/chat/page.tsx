"use client";

/**
 * Nidhi AI OS — Chat Page
 *
 * Full-screen conversation interface with Nidhi.
 * Supports URL query params: ?q=... to pre-fill message, ?id=... to load conversation.
 */

import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import Sidebar from "@/components/dashboard/Sidebar";
import ChatWindow from "@/components/chat/ChatWindow";

function ChatContent() {
  const searchParams = useSearchParams();
  const conversationId = searchParams.get("id") || undefined;

  return (
    <>
      <div className="aurora-bg" aria-hidden />
      <div className="flex h-screen" style={{ background: "var(--bg-primary)" }}>
        <Sidebar />
        <main
          className="flex-1 flex flex-col relative"
          style={{ marginLeft: "var(--sidebar-width)", zIndex: 1 }}
        >
          <ChatWindow conversationId={conversationId} />
        </main>
      </div>
    </>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={
      <div className="flex h-screen items-center justify-center" style={{ background: "var(--bg-primary)" }}>
        <div className="text-center">
          <div
            className="w-12 h-12 rounded-full mx-auto mb-4"
            style={{
              background: "linear-gradient(135deg, #7c6bff, #e879f9)",
              animation: "breathe 2s ease-in-out infinite",
            }}
          />
          <p style={{ color: "var(--text-muted)", fontSize: "0.875rem" }}>
            Nidhi loading…
          </p>
        </div>
      </div>
    }>
      <ChatContent />
    </Suspense>
  );
}
