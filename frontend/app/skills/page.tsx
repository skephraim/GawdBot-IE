"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Zap, ToggleLeft, ToggleRight, RefreshCw } from "lucide-react";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

interface Skill {
  name: string;
  description: string;
  commands: string[];
  enabled: boolean;
}

export default function SkillsPage() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/skills`);
      const data = await res.json();
      setSkills(data.skills || []);
    } catch {
      setSkills([]);
    }
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const toggle = async (name: string, enabled: boolean) => {
    await fetch(`${BACKEND_URL}/skills/${name}/toggle?enabled=${!enabled}`, { method: "POST" });
    setSkills((prev) => prev.map((s) => s.name === name ? { ...s, enabled: !enabled } : s));
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <header className="flex items-center gap-3 border-b border-gray-800 bg-gray-900 px-4 py-3">
        <Link href="/" className="text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <h1 className="font-semibold">Skills</h1>
        <button onClick={load} className="ml-auto text-gray-400 hover:text-white">
          <RefreshCw className="h-4 w-4" />
        </button>
      </header>

      <div className="max-w-2xl mx-auto p-6">
        <div className="mb-6">
          <p className="text-gray-400 text-sm">
            Skills extend GawdBotE with new capabilities. Drop a folder with a <code className="text-xs bg-gray-800 px-1 rounded">main.py</code> into <code className="text-xs bg-gray-800 px-1 rounded">skills/</code> to add one.
          </p>
        </div>

        {loading && <p className="text-center text-gray-500">Loading skills...</p>}

        {!loading && skills.length === 0 && (
          <div className="rounded-xl border border-dashed border-gray-700 p-8 text-center">
            <Zap className="h-8 w-8 text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400 font-medium">No skills installed</p>
            <p className="text-gray-500 text-sm mt-1">Add skill folders to <code className="text-xs bg-gray-800 px-1 rounded">~/GawdBotE/skills/</code></p>
          </div>
        )}

        <ul className="space-y-3">
          {skills.map((skill) => (
            <li key={skill.name} className="rounded-lg border border-gray-800 bg-gray-900 px-4 py-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="font-medium text-white">{skill.name}</h3>
                  {skill.description && <p className="text-sm text-gray-400 mt-0.5">{skill.description}</p>}
                  {skill.commands.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {skill.commands.map((cmd) => (
                        <span key={cmd} className="text-xs bg-gray-800 text-gray-300 px-2 py-0.5 rounded">
                          /{cmd}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <button onClick={() => toggle(skill.name, skill.enabled)} className="mt-0.5">
                  {skill.enabled
                    ? <ToggleRight className="h-6 w-6 text-green-400" />
                    : <ToggleLeft className="h-6 w-6 text-gray-600" />
                  }
                </button>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
