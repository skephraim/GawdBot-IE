"use client";

import Link from "next/link";
import { ArrowLeft, ExternalLink } from "lucide-react";

export default function SettingsPage() {
  const envPath = "~/GawdBotE/.env";

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <header className="flex items-center gap-3 border-b border-gray-800 bg-gray-900 px-4 py-3">
        <Link href="/" className="text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <h1 className="font-semibold">Settings</h1>
      </header>

      <div className="max-w-2xl mx-auto p-6 space-y-6">
        <div className="rounded-lg border border-gray-800 bg-gray-900 p-5">
          <h2 className="font-semibold text-white mb-2">Configuration</h2>
          <p className="text-sm text-gray-400 mb-3">
            GawdBotE is configured via environment variables in your <code className="text-xs bg-gray-800 px-1 rounded">.env</code> file.
          </p>
          <code className="text-sm text-green-400 block bg-gray-950 rounded px-3 py-2">{envPath}</code>
        </div>

        <div className="rounded-lg border border-gray-800 bg-gray-900 p-5">
          <h2 className="font-semibold text-white mb-3">Key Settings</h2>
          <div className="space-y-2 text-sm">
            {[
              ["LLM", "ANTHROPIC_API_KEY, CLAUDE_SMART_MODEL"],
              ["Memory", "SUPABASE_URL, SUPABASE_ANON_KEY (or SQLite fallback)"],
              ["Voice STT", "VOICE_STT_PROVIDER, GROQ_API_KEY"],
              ["Voice TTS", "VOICE_TTS_PROVIDER, ELEVENLABS_API_KEY"],
              ["Telegram", "TELEGRAM_BOT_TOKEN, TELEGRAM_USER_ID"],
              ["User", "USER_NAME, USER_TIMEZONE"],
            ].map(([label, value]) => (
              <div key={label} className="flex gap-3">
                <span className="text-gray-500 w-24 shrink-0">{label}</span>
                <span className="text-gray-300 font-mono text-xs">{value}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-lg border border-gray-800 bg-gray-900 p-5">
          <h2 className="font-semibold text-white mb-3">Quick Links</h2>
          <div className="space-y-2 text-sm">
            {[
              ["Anthropic Console", "console.anthropic.com"],
              ["Supabase Dashboard", "supabase.com/dashboard"],
              ["Groq Console", "console.groq.com"],
            ].map(([label, url]) => (
              <div key={url} className="flex items-center gap-2 text-gray-400">
                <ExternalLink className="h-3 w-3" />
                <span>{label} — <code className="text-xs text-gray-500">{url}</code></span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-lg border border-gray-800 bg-gray-900 p-5">
          <h2 className="font-semibold text-white mb-2">Restart Backend</h2>
          <p className="text-sm text-gray-400">After changing .env, restart the backend:</p>
          <code className="text-sm text-green-400 block bg-gray-950 rounded px-3 py-2 mt-2">
            cd ~/GawdBotE && bun run dev:backend
          </code>
        </div>
      </div>
    </div>
  );
}
