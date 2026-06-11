/**
 * Uday AI — WebSocket Client
 *
 * Real-time streaming chat connection with auto-reconnect.
 */

import type { WSMessage } from "@/types";

const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

type WSEventHandler = (message: WSMessage) => void;

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private token: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private handlers: Map<string, WSEventHandler[]> = new Map();
  private isConnecting = false;

  constructor(conversationId?: string, token?: string) {
    const path = conversationId
      ? `/ws/chat/${conversationId}`
      : "/ws/chat";

    this.token = token || localStorage.getItem("udayai_token") || "";
    this.url = `${WS_BASE}${path}?token=${this.token}`;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      if (this.isConnecting) {
        resolve();
        return;
      }

      this.isConnecting = true;

      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          console.log("[WS] Connected");
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const data: WSMessage = JSON.parse(event.data);
            this.emit(data.type, data);
          } catch (e) {
            console.error("[WS] Parse error:", e);
          }
        };

        this.ws.onclose = (event) => {
          this.isConnecting = false;
          console.log(`[WS] Disconnected: ${event.code}`);

          if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnect();
          }
        };

        this.ws.onerror = (error) => {
          this.isConnecting = false;
          console.error("[WS] Error:", error);
          reject(error);
        };
      } catch (e) {
        this.isConnecting = false;
        reject(e);
      }
    });
  }

  private reconnect() {
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    console.log(`[WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

    setTimeout(() => {
      this.connect().catch(console.error);
    }, delay);
  }

  sendMessage(content: string, metadata?: Record<string, unknown>) {
    if (this.ws?.readyState !== WebSocket.OPEN) {
      console.error("[WS] Not connected");
      return;
    }

    this.ws.send(JSON.stringify({
      type: "message",
      content,
      metadata,
    }));
  }

  ping() {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: "ping" }));
    }
  }

  on(event: string, handler: WSEventHandler) {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, []);
    }
    this.handlers.get(event)!.push(handler);
  }

  off(event: string, handler: WSEventHandler) {
    const handlers = this.handlers.get(event);
    if (handlers) {
      this.handlers.set(event, handlers.filter((h) => h !== handler));
    }
  }

  private emit(event: string, data: WSMessage) {
    const handlers = this.handlers.get(event) || [];
    handlers.forEach((handler) => handler(data));

    // Also emit to wildcard handlers
    const wildcardHandlers = this.handlers.get("*") || [];
    wildcardHandlers.forEach((handler) => handler(data));
  }

  disconnect() {
    this.maxReconnectAttempts = 0; // Prevent reconnect
    if (this.ws) {
      this.ws.close(1000);
      this.ws = null;
    }
    this.handlers.clear();
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

export function createWSClient(conversationId?: string): WebSocketClient {
  return new WebSocketClient(conversationId);
}
