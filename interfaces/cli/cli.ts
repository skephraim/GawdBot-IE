/**
 * GawdBotE — CLI Interface
 * Terminal chat with GawdBotE backend.
 * Usage: bun run cli.ts
 */

import * as readline from "readline";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";
const SESSION_ID = `cli-${Date.now()}`;

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

async function chat(message: string): Promise<string> {
  try {
    const res = await fetch(`${BACKEND_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, channel: "cli", session_id: SESSION_ID }),
    });
    const data = await res.json() as { response: string };
    return data.response || "(no response)";
  } catch {
    return "Error: Could not connect to backend. Is it running? (bun run dev:backend)";
  }
}

async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${BACKEND_URL}/health`);
    return res.ok;
  } catch {
    return false;
  }
}

async function main() {
  console.log("\n🤖 GawdBotE CLI");
  console.log("===============");

  const healthy = await checkHealth();
  if (!healthy) {
    console.error(`\n⚠️  Backend not reachable at ${BACKEND_URL}`);
    console.error("   Start it with: bun run dev:backend\n");
  } else {
    console.log(`✓ Connected to backend at ${BACKEND_URL}`);
  }

  console.log("Type your message and press Enter. Ctrl+C to exit.\n");

  const ask = () => {
    rl.question("You: ", async (input) => {
      const message = input.trim();
      if (!message) {
        ask();
        return;
      }

      if (message.toLowerCase() === "/exit" || message.toLowerCase() === "/quit") {
        console.log("\nGoodbye!");
        rl.close();
        process.exit(0);
      }

      process.stdout.write("GawdBotE: ");
      const response = await chat(message);
      console.log(response);
      console.log();
      ask();
    });
  };

  ask();
}

main();
