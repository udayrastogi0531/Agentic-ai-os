/**
 * Uday AI — API Client
 *
 * Centralized HTTP client for all backend API calls.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_PREFIX = "/api/v1";

class ApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor() {
    this.baseUrl = `${API_BASE}${API_PREFIX}`;
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("udayai_token");
    }
  }

  setToken(token: string) {
    this.token = token;
    if (typeof window !== "undefined") {
      localStorage.setItem("udayai_token", token);
    }
  }

  clearToken() {
    this.token = null;
    if (typeof window !== "undefined") {
      localStorage.removeItem("udayai_token");
    }
  }

  getToken(): string | null {
    return this.token;
  }

  private async request<T>(
    method: string,
    path: string,
    body?: unknown,
    options?: { headers?: Record<string, string> }
  ): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...options?.headers,
    };

    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }

    const res = await fetch(`${this.baseUrl}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(error.detail || `API error: ${res.status}`);
    }

    if (res.status === 204) return null as T;
    return res.json();
  }

  // ── Auth ──────────────────────────────────────

  async register(data: { email: string; name: string; password: string; nickname?: string }) {
    const result = await this.request<{ access_token: string; user: unknown }>(
      "POST", "/auth/register", data
    );
    this.setToken(result.access_token);
    return result;
  }

  async login(email: string, password: string) {
    const result = await this.request<{ access_token: string; user: unknown }>(
      "POST", "/auth/login", { email, password }
    );
    this.setToken(result.access_token);
    return result;
  }

  async getMe() {
    return this.request<unknown>("GET", "/auth/me");
  }

  async updateProfile(data: Record<string, unknown>) {
    return this.request<unknown>("PATCH", "/auth/me", data);
  }

  // ── Chat ──────────────────────────────────────

  async sendMessage(message: string, conversationId?: string, modelOverride?: string) {
    return this.request<unknown>("POST", "/chat/send", {
      message,
      conversation_id: conversationId,
      model_override: modelOverride,
    });
  }

  async getConversations(page = 1) {
    return this.request<unknown[]>("GET", `/chat/conversations?page=${page}`);
  }

  async getConversation(id: string) {
    return this.request<unknown>("GET", `/chat/conversations/${id}`);
  }

  async createConversation(title = "New Conversation") {
    return this.request<unknown>("POST", "/chat/conversations", { title });
  }

  async deleteConversation(id: string) {
    return this.request<void>("DELETE", `/chat/conversations/${id}`);
  }

  // ── Memory ────────────────────────────────────

  async getMemories(category?: string, page = 1) {
    const params = new URLSearchParams({ page: String(page) });
    if (category) params.set("category", category);
    return this.request<unknown>("GET", `/memories?${params}`);
  }

  async searchMemories(query: string, category?: string, limit = 10) {
    return this.request<unknown[]>("POST", "/memories/search", {
      query, category, limit,
    });
  }

  async createMemory(content: string, category?: string, importance?: number) {
    return this.request<unknown>("POST", "/memories", {
      content, category, importance,
    });
  }

  async deleteMemory(id: string) {
    return this.request<void>("DELETE", `/memories/${id}`);
  }

  async getMemoryStats() {
    return this.request<unknown>("GET", "/memories/stats");
  }

  // ── Files / RAG ───────────────────────────────

  async uploadFile(file: File) {
    const formData = new FormData();
    formData.append("file", file);

    const headers: Record<string, string> = {};
    if (this.token) headers["Authorization"] = `Bearer ${this.token}`;

    const res = await fetch(`${this.baseUrl}/files/upload`, {
      method: "POST",
      headers,
      body: formData,
    });

    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(error.detail || "Upload failed");
    }

    return res.json();
  }

  async getFiles() {
    return this.request<unknown>("GET", "/files");
  }

  async deleteFile(id: string) {
    return this.request<void>("DELETE", `/files/${id}`);
  }

  async queryFile(fileId: string, question: string) {
    return this.request<unknown>("POST", `/files/${fileId}/query`, {
      question, top_k: 5,
    });
  }

  // ── Tasks ─────────────────────────────────────

  async getTasks(status?: string, priority?: string) {
    const params = new URLSearchParams();
    if (status) params.set("status_filter", status);
    if (priority) params.set("priority", priority);
    return this.request<unknown>("GET", `/tasks?${params}`);
  }

  async createTask(data: Record<string, unknown>) {
    return this.request<unknown>("POST", "/tasks", data);
  }

  async updateTask(id: string, data: Record<string, unknown>) {
    return this.request<unknown>("PATCH", `/tasks/${id}`, data);
  }

  async deleteTask(id: string) {
    return this.request<void>("DELETE", `/tasks/${id}`);
  }

  // ── Notes ─────────────────────────────────────

  async getNotes(category?: string) {
    const params = category ? `?category=${category}` : "";
    return this.request<unknown>("GET", `/notes${params}`);
  }

  async createNote(data: Record<string, unknown>) {
    return this.request<unknown>("POST", "/notes", data);
  }

  async updateNote(id: string, data: Record<string, unknown>) {
    return this.request<unknown>("PATCH", `/notes/${id}`, data);
  }

  async deleteNote(id: string) {
    return this.request<void>("DELETE", `/notes/${id}`);
  }

  // ── Admin ─────────────────────────────────────

  async getAnalytics() {
    return this.request<unknown>("GET", "/admin/analytics");
  }

  async getAgentLogs(agentName?: string, limit = 50) {
    const params = new URLSearchParams({ limit: String(limit) });
    if (agentName) params.set("agent_name", agentName);
    return this.request<unknown[]>("GET", `/admin/logs?${params}`);
  }

  async getAgentStatus() {
    return this.request<unknown>("GET", "/admin/agents");
  }

  // ── Voice ─────────────────────────────────────

  async transcribeAudio(file: Blob) {
    const formData = new FormData();
    formData.append("file", file, "audio.wav");

    const headers: Record<string, string> = {};
    if (this.token) headers["Authorization"] = `Bearer ${this.token}`;

    const res = await fetch(`${this.baseUrl}/voice/stt`, {
      method: "POST",
      headers,
      body: formData,
    });

    if (!res.ok) {
      throw new Error("STT transcription failed");
    }
    return res.json() as Promise<{ text: string }>;
  }

  async synthesizeSpeech(text: string): Promise<Blob> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (this.token) headers["Authorization"] = `Bearer ${this.token}`;

    const res = await fetch(`${this.baseUrl}/voice/tts`, {
      method: "POST",
      headers,
      body: JSON.stringify({ text }),
    });

    if (!res.ok) {
      throw new Error("TTS synthesis failed");
    }
    return res.blob();
  }
}

export const api = new ApiClient();
export default api;
