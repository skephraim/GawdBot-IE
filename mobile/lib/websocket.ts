import { getBackendUrl } from './api';

type MessageHandler = (msg: { type: string; role?: string; content?: string; value?: boolean }) => void;

export class WSManager {
  private ws: WebSocket | null = null;
  private handler: MessageHandler | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private shouldConnect = false;
  private sessionId: string;

  constructor() {
    this.sessionId = `mobile-${Date.now()}`;
  }

  async connect(handler: MessageHandler) {
    this.handler = handler;
    this.shouldConnect = true;
    await this._connect();
  }

  private async _connect() {
    if (!this.shouldConnect) return;
    const base = await getBackendUrl();
    const wsUrl = base.replace(/^http/, 'ws') + '/ws';
    try {
      this.ws = new WebSocket(wsUrl);
      this.ws.onmessage = (e) => {
        try { this.handler?.(JSON.parse(e.data)); } catch {}
      };
      this.ws.onerror = () => this._scheduleReconnect();
      this.ws.onclose = () => this._scheduleReconnect();
    } catch {
      this._scheduleReconnect();
    }
  }

  private _scheduleReconnect() {
    if (!this.shouldConnect) return;
    this.reconnectTimer = setTimeout(() => this._connect(), 3000);
  }

  send(message: string) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ message, channel: 'mobile', session_id: this.sessionId }));
      return true;
    }
    return false;
  }

  disconnect() {
    this.shouldConnect = false;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.ws?.close();
    this.ws = null;
  }

  get isConnected() {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}
