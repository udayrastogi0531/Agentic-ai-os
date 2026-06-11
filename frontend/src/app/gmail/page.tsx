"use client";

/**
 * Uday AI — Gmail Page
 *
 * Displays recent emails and drafts when connected in user settings.
 */

import { useState, useEffect } from "react";
import Sidebar from "@/components/dashboard/Sidebar";
import useAuth from "@/hooks/useAuth";
import Link from "next/link";

interface MailItem {
  id: string;
  sender: string;
  senderEmail: string;
  subject: string;
  snippet: string;
  time: string;
  isRead: boolean;
  tag: "inbox" | "draft" | "sent";
}

const MOCK_MAILS: MailItem[] = [
  {
    id: "1",
    sender: "Google Workspace Team",
    senderEmail: "workspace-noreply@google.com",
    subject: "Secure your Uday AI Developer credentials",
    snippet: "You recently created new OAuth client credentials in your GCP console. Ensure that you restrict access...",
    time: "10:45 AM",
    isRead: false,
    tag: "inbox",
  },
  {
    id: "2",
    sender: "GitHub Notifications",
    senderEmail: "noreply@github.com",
    subject: "[GitHub] Security Advisory published for modelcontextprotocol/server-filesystem",
    snippet: "A security alert was published for the model-context-protocol filesystem server package. Update your versions...",
    time: "Yesterday",
    isRead: true,
    tag: "inbox",
  },
  {
    id: "3",
    sender: "Draft Email",
    senderEmail: "",
    subject: "Follow up: AI OS Architecture proposal review",
    snippet: "Hi Team, Here is the revised architectural proposal diagram outlining the client manager and server interface...",
    time: "June 10",
    isRead: true,
    tag: "draft",
  },
  {
    id: "4",
    sender: "To: John Doe",
    senderEmail: "john.doe@example.com",
    subject: "Uday AI Deployment status check",
    snippet: "Hi John, just wanted to check if you had a chance to test the docker-compose deployment configuration on staging...",
    time: "June 08",
    isRead: true,
    tag: "sent",
  },
];

export default function GmailPage() {
  const { user } = useAuth(); // Require authentication
  const [isConnected, setIsConnected] = useState(false);
  const [activeFolder, setActiveFolder] = useState<"inbox" | "draft" | "sent">("inbox");

  useEffect(() => {
    if (user) {
      const prefs = (user.preferences as Record<string, any>) || {};
      setIsConnected(!!prefs.gmail_connected);
    }
  }, [user]);

  const filteredMails = MOCK_MAILS.filter((mail) => mail.tag === activeFolder);

  return (
    <div className="flex min-h-screen" style={{ background: "var(--bg-primary)" }}>
      <Sidebar />
      <main className="flex-1 font-sans flex flex-col" style={{ marginLeft: "var(--sidebar-width)" }}>
        <header className="sticky top-0 z-30 glass-strong px-8 py-5 flex items-center justify-between border-b border-[var(--border-color)]">
          <div>
            <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>📧 Gmail</h1>
            <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>Draft, organize, and reply to emails</p>
          </div>
        </header>

        <div className="px-8 py-6 animate-fade-in max-w-5xl flex-1 flex flex-col gap-6">
          {!isConnected ? (
            <div className="flex flex-col items-center justify-center py-20 rounded-2xl border border-[var(--border-color)]" style={{ background: "var(--bg-card)" }}>
              <span className="text-5xl mb-4">📧</span>
              <h3 className="text-lg font-semibold mb-2" style={{ color: "var(--text-primary)" }}>Connect Gmail account</h3>
              <p className="text-sm text-center max-w-md mb-6" style={{ color: "var(--text-secondary)" }}>
                Link your Google Gmail account in settings to browse inbox summaries, search mails, and write drafts dynamically.
              </p>
              <Link href="/settings" className="px-6 py-3 rounded-xl text-sm font-semibold text-white transition-all hover:scale-105 shadow-glow" style={{ background: "var(--gradient-primary)" }}>
                ⚙️ Go to Integrations Settings
              </Link>
            </div>
          ) : (
            <div className="flex-1 flex flex-col md:flex-row gap-6">
              {/* Mail Sidebar folders */}
              <div className="w-full md:w-48 flex flex-row md:flex-col gap-2 shrink-0">
                {[
                  { label: "📥 Inbox", folder: "inbox" },
                  { label: "📝 Drafts", folder: "draft" },
                  { label: "📤 Sent Mail", folder: "sent" },
                ].map((item) => {
                  const isActive = activeFolder === item.folder;
                  return (
                    <button
                      key={item.folder}
                      onClick={() => setActiveFolder(item.folder as any)}
                      className="flex-1 md:flex-initial px-4 py-2.5 rounded-xl text-xs font-semibold border text-left transition-all"
                      style={{
                        background: isActive ? "var(--accent-primary)" : "var(--bg-card)",
                        borderColor: isActive ? "var(--accent-primary)" : "var(--border-color)",
                        color: isActive ? "white" : "var(--text-secondary)",
                      }}
                    >
                      {item.label}
                    </button>
                  );
                })}
              </div>

              {/* Mail list panel */}
              <div className="flex-1 rounded-2xl border border-[var(--border-color)] overflow-hidden" style={{ background: "var(--bg-card)" }}>
                <div className="px-6 py-4 border-b border-[var(--border-color)] bg-[var(--bg-tertiary)] flex items-center justify-between">
                  <h3 className="text-sm font-bold uppercase tracking-wider" style={{ color: "var(--text-primary)" }}>
                    {activeFolder.toUpperCase()} ({filteredMails.length})
                  </h3>
                  <span className="text-[10px] font-semibold border border-emerald-500/30 text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full">
                    Active Mail Sync
                  </span>
                </div>

                <div className="divide-y divide-[var(--border-color)] overflow-y-auto max-h-[500px]">
                  {filteredMails.length === 0 ? (
                    <div className="py-20 text-center text-sm" style={{ color: "var(--text-muted)" }}>
                      No emails found in this folder.
                    </div>
                  ) : (
                    filteredMails.map((mail) => (
                      <div
                        key={mail.id}
                        className={`p-5 hover:bg-[var(--bg-hover)] transition-all cursor-pointer flex flex-col justify-between ${
                          !mail.isRead ? "border-l-4 border-l-[var(--accent-primary)]" : ""
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-bold" style={{ color: !mail.isRead ? "var(--text-primary)" : "var(--text-secondary)" }}>
                            {mail.sender}
                          </span>
                          <span className="text-[10px]" style={{ color: "var(--text-muted)" }}>{mail.time}</span>
                        </div>
                        <h4 className="text-xs font-semibold mb-1" style={{ color: "var(--text-primary)" }}>
                          {mail.subject}
                        </h4>
                        <p className="text-xs line-clamp-2" style={{ color: "var(--text-muted)" }}>
                          {mail.snippet}
                        </p>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
