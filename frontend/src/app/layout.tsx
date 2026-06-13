import type { Metadata, Viewport } from "next";
import "./globals.css";

export const viewport: Viewport = {
  themeColor: "#7c6bff",
};

export const metadata: Metadata = {
  title: "Nidhi AI — Your Personal AI Companion",
  description:
    "Nidhi is your intelligent AI companion — combining the power of ChatGPT, Jarvis, and a personal assistant. " +
    "Long-term memory, research, coding, calendar, email, tasks, voice interaction, and more.",
  keywords: ["Nidhi AI", "AI Companion", "Personal AI OS", "AI Assistant", "Hinglish AI"],
  authors: [{ name: "Uday Rastogi" }],
  openGraph: {
    title: "Nidhi AI — Your Personal AI Companion",
    description: "Your intelligent AI companion for daily life — Nidhi speaks your language.",
    type: "website",
  },
};


export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&family=Outfit:wght@300;400;500;600;700;800;900&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased">{children}</body>
    </html>
  );
}
