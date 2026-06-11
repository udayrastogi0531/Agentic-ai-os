"use client";

/**
 * Uday AI — Chat Page
 */

import Sidebar from "@/components/dashboard/Sidebar";
import ChatWindow from "@/components/chat/ChatWindow";

export default function ChatPage() {
  return (
    <div className="flex h-screen" style={{ background: "var(--bg-primary)" }}>
      <Sidebar />
      <main className="flex-1 flex flex-col" style={{ marginLeft: "var(--sidebar-width)" }}>
        <ChatWindow />
      </main>
    </div>
  );
}
