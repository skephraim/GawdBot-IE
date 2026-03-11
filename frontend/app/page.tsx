"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { MessageCircle, Brain, Zap, Settings, Activity } from "lucide-react";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

interface HealthData {
  status: string;
  memory: string;
  model: string;
}

export default function Dashboard() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    fetch(`${BACKEND_URL}/health`)
      .then((r) => r.json())
      .then((d) => {
        setHealth(d);
        setConnected(true);
      })
      .catch(() => setConnected(false));
  }, []);

  const cards = [
    { href: "/chat", icon: MessageCircle, title: "Chat", desc: "Talk to GawdBotE" },
    { href: "/memory", icon: Brain, title: "Memory", desc: "Facts, goals, history" },
    { href: "/skills", icon: Zap, title: "Skills", desc: "Manage capabilities" },
    { href: "/settings", icon: Settings, title: "Settings", desc: "Configure everything" },
  ];

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold text-green-400 mb-2">GawdBotE</h1>
          <p className="text-gray-400">Your super AI partner</p>
        </div>

        {/* Status */}
        <div className="mb-6 flex items-center gap-2 rounded-lg border border-gray-800 bg-gray-900 p-3">
          <Activity className="h-4 w-4 text-gray-400" />
          <span className="text-sm text-gray-400">Backend:</span>
          {connected ? (
            <>
              <span className="text-sm font-medium text-green-400">Online</span>
              {health && (
                <span className="ml-auto text-xs text-gray-500">
                  {health.memory} · {health.model}
                </span>
              )}
            </>
          ) : (
            <span className="text-sm text-red-400">
              Offline — run <code className="text-xs bg-gray-800 px-1 rounded">bun run dev:backend</code>
            </span>
          )}
        </div>

        {/* Nav cards */}
        <div className="grid grid-cols-2 gap-4">
          {cards.map(({ href, icon: Icon, title, desc }) => (
            <Link
              key={href}
              href={href}
              className="group rounded-xl border border-gray-800 bg-gray-900 p-5 transition-all hover:border-green-500/50 hover:bg-gray-800"
            >
              <Icon className="mb-3 h-6 w-6 text-green-400 group-hover:scale-110 transition-transform" />
              <h2 className="font-semibold text-white">{title}</h2>
              <p className="text-sm text-gray-400">{desc}</p>
            </Link>
          ))}
        </div>
      </div>
    </main>
  );
}
