/**
 * Nidhi — TypeScript Types
 */

// ── User & Auth ─────────────────────────────────

export interface User {
  id: string;
  email: string;
  name: string;
  nickname?: string;
  avatar_url?: string;
  preferences?: Record<string, unknown>;
  is_admin: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// ── Chat ────────────────────────────────────────

export interface Message {
  id: string;
  conversation_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  agent_name?: string;
  tool_calls?: Record<string, unknown>;
  citations?: Record<string, unknown>;
  token_count?: number;
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  status: string;
  created_at: string;
  updated_at: string;
  message_count?: number;
  last_message?: string;
}

export interface ChatResponse {
  message: Message;
  conversation_id: string;
  agent_actions: Record<string, unknown>[];
}

// ── WebSocket ───────────────────────────────────

export interface WSMessage {
  type: "token" | "agent_status" | "message_complete" | "error" | "pong";
  content?: string;
  agent_name?: string;
  metadata?: Record<string, unknown>;
}

// ── Memory ──────────────────────────────────────

export interface Memory {
  id: string;
  category: string;
  content: string;
  summary?: string;
  importance: number;
  access_count: number;
  created_at: string;
  last_accessed: string;
  relevance_score?: number;
}

// ── Task ────────────────────────────────────────

export interface Task {
  id: string;
  title: string;
  description?: string;
  priority: "low" | "medium" | "high" | "urgent";
  status: "todo" | "in_progress" | "done" | "cancelled";
  due_date?: string;
  category?: string;
  tags?: string[];
  created_at: string;
  updated_at: string;
}

// ── Note ────────────────────────────────────────

export interface Note {
  id: string;
  title: string;
  content: string;
  tags?: string[];
  category?: string;
  is_pinned: boolean;
  created_at: string;
  updated_at: string;
}

// ── File / RAG ──────────────────────────────────

export interface UploadedFile {
  id: string;
  filename: string;
  original_filename: string;
  file_type: string;
  file_size: number;
  chunk_count: number;
  status: string;
  created_at: string;
}

export interface Citation {
  document_id: string;
  document_name: string;
  chunk_index: number;
  page_number?: number;
  content: string;
  relevance_score: number;
}

// ── Dashboard ───────────────────────────────────

export interface NavItem {
  name: string;
  href: string;
  icon: string;
  badge?: number;
}

export interface AgentStatus {
  name: string;
  display_name: string;
  status: "active" | "pending_setup" | "error";
}

// ── Analytics ───────────────────────────────────

export interface Analytics {
  total_conversations: number;
  total_messages: number;
  total_memories: number;
  agent_stats: {
    agent: string;
    total_calls: number;
    avg_duration_ms: number;
  }[];
  llm_providers: {
    id: string;
    name: string;
    models: string[];
    is_default: boolean;
    status: string;
  }[];
}
