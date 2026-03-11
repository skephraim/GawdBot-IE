"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { Send, ArrowLeft, Loader2 } from "lucide-react";
import Link from "next/link";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";
const SESSION_ID = `web-${Date.now()}`;

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const [connected, setConnected] = useState(false);
  const ws = useRef<WebSocket | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const addMessage = useCallback((role: Message["role"], content: string) => {
    setMessages((prev) => [
      ...prev,
      { id: crypto.randomUUID(), role, content, timestamp: new Date().toISOString() },
    ]);
  }, []);

  useEffect(() => {
    const connect = () => {
      const socket = new WebSocket(`${WS_URL}/ws`);
      ws.current = socket;

      socket.onopen = () => {
        setConnected(true);
        addMessage("system", "Connected to GawdBotE. How can I help?");
      };

      socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "typing") {
          setTyping(data.value);
        } else if (data.type === "message") {
          setTyping(false);
          addMessage("assistant", data.content);
        }
      };

      socket.onclose = () => {
        setConnected(false);
        setTimeout(connect, 3000);
      };

      socket.onerror = () => {
        setConnected(false);
      };
    };

    connect();
    return () => ws.current?.close();
  }, [addMessage]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, typing]);

  const send = () => {
    const text = input.trim();
    if (!text || !ws.current || ws.current.readyState !== WebSocket.OPEN) return;

    addMessage("user", text);
    ws.current.send(JSON.stringify({ message: text, channel: "web", session_id: SESSION_ID }));
    setInput("");
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <div className="flex h-screen flex-col bg-gray-950">
      {/* Header */}
      <header className="flex items-center gap-3 border-b border-gray-800 bg-gray-900 px-4 py-3">
        <Link href="/" className="text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <h1 className="font-semibold text-white">GawdBotE</h1>
        <span className={`ml-auto text-xs ${connected ? "text-green-400" : "text-red-400"}`}>
          {connected ? "● Online" : "● Reconnecting..."}
        </span>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            {msg.role === "system" ? (
              <p className="text-xs text-gray-500 italic">{msg.content}</p>
            ) : (
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-2 text-sm whitespace-pre-wrap ${
                  msg.role === "user"
                    ? "bg-green-600 text-white rounded-br-sm"
                    : "bg-gray-800 text-gray-100 rounded-bl-sm"
                }`}
              >
                {msg.content}
              </div>
            )}
          </div>
        ))}

        {typing && (
          <div className="flex justify-start">
            <div className="bg-gray-800 rounded-2xl rounded-bl-sm px-4 py-3">
              <Loader2 className="h-4 w-4 animate-spin text-green-400" />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-800 bg-gray-900 p-4">
        <div className="flex gap-3 items-end">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Message GawdBotE... (Enter to send, Shift+Enter for newline)"
            rows={1}
            className="flex-1 resize-none rounded-xl bg-gray-800 px-4 py-3 text-sm text-white placeholder-gray-500 outline-none focus:ring-1 focus:ring-green-500 max-h-32 scrollbar-thin"
            style={{ height: "auto" }}
            onInput={(e) => {
              const t = e.currentTarget;
              t.style.height = "auto";
              t.style.height = `${Math.min(t.scrollHeight, 128)}px`;
            }}
          />
          <button
            onClick={send}
            disabled={!input.trim() || !connected}
            className="rounded-xl bg-green-600 p-3 text-white transition-colors hover:bg-green-500 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
