"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Target, Lightbulb, Trash2, RefreshCw } from "lucide-react";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

interface MemoryItem { id: string; content: string; deadline?: string; priority?: number; }

export default function MemoryPage() {
  const [facts, setFacts] = useState<MemoryItem[]>([]);
  const [goals, setGoals] = useState<MemoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const [f, g] = await Promise.all([
        fetch(`${BACKEND_URL}/memory/facts`).then((r) => r.json()),
        fetch(`${BACKEND_URL}/memory/goals`).then((r) => r.json()),
      ]);
      setFacts(f.facts || []);
      setGoals(g.goals || []);
    } catch {
      // Backend offline
    }
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const deleteFact = async (id: string) => {
    await fetch(`${BACKEND_URL}/memory/fact/${id}`, { method: "DELETE" });
    setFacts((prev) => prev.filter((f) => f.id !== id));
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <header className="flex items-center gap-3 border-b border-gray-800 bg-gray-900 px-4 py-3">
        <Link href="/" className="text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <h1 className="font-semibold">Memory</h1>
        <button onClick={load} className="ml-auto text-gray-400 hover:text-white">
          <RefreshCw className="h-4 w-4" />
        </button>
      </header>

      <div className="max-w-2xl mx-auto p-6 space-y-8">
        {loading && <p className="text-center text-gray-500">Loading memory...</p>}

        {/* Goals */}
        <section>
          <h2 className="flex items-center gap-2 text-lg font-semibold mb-4 text-green-400">
            <Target className="h-5 w-5" /> Active Goals ({goals.length})
          </h2>
          {goals.length === 0 ? (
            <p className="text-gray-500 text-sm">No active goals. Tell GawdBotE what you want to achieve.</p>
          ) : (
            <ul className="space-y-2">
              {goals.map((g) => (
                <li key={g.id} className="rounded-lg bg-gray-900 border border-gray-800 px-4 py-3 text-sm">
                  <p>{g.content}</p>
                  {g.deadline && (
                    <p className="mt-1 text-xs text-gray-500">Due: {new Date(g.deadline).toLocaleDateString()}</p>
                  )}
                </li>
              ))}
            </ul>
          )}
        </section>

        {/* Facts */}
        <section>
          <h2 className="flex items-center gap-2 text-lg font-semibold mb-4 text-blue-400">
            <Lightbulb className="h-5 w-5" /> Known Facts ({facts.length})
          </h2>
          {facts.length === 0 ? (
            <p className="text-gray-500 text-sm">No facts stored yet. GawdBotE will remember things as you chat.</p>
          ) : (
            <ul className="space-y-2">
              {facts.map((f) => (
                <li key={f.id} className="flex items-start gap-3 rounded-lg bg-gray-900 border border-gray-800 px-4 py-3 text-sm group">
                  <span className="flex-1">{f.content}</span>
                  <button
                    onClick={() => deleteFact(f.id)}
                    className="text-gray-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}
