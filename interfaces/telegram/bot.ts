/**
 * GawdBotE — Telegram Interface
 * Adapted from claude-telegram-relay/src/relay.ts
 *
 * Forwards messages to the FastAPI backend via REST/WebSocket.
 * Handles text, voice, images, documents.
 */

import { Bot, Context } from "grammy";
import { writeFile, mkdir, unlink } from "fs/promises";
import { join } from "path";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";
const BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN || "";
const ALLOWED_USER_ID = process.env.TELEGRAM_USER_ID || "";
const UPLOADS_DIR = join(process.env.HOME || "~", ".gawdbote", "uploads");

if (!BOT_TOKEN) {
  console.error("TELEGRAM_BOT_TOKEN not set!");
  process.exit(1);
}

if (!ALLOWED_USER_ID) {
  console.error("TELEGRAM_USER_ID not set! Refusing to start with open access.");
  process.exit(1);
}

await mkdir(UPLOADS_DIR, { recursive: true });

const bot = new Bot(BOT_TOKEN);

// ---- Security: only respond to authorized user ----
bot.use(async (ctx, next) => {
  const userId = ctx.from?.id.toString();
  if (ALLOWED_USER_ID && userId !== ALLOWED_USER_ID) {
    await ctx.reply("This bot is private.");
    return;
  }
  await next();
});

// ---- Send message to backend ----
async function sendToBackend(
  message: string,
  channel: string = "telegram",
  sessionId?: string
): Promise<string> {
  try {
    const res = await fetch(`${BACKEND_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, channel, session_id: sessionId }),
    });
    const data = await res.json() as { response: string };
    return data.response || "No response.";
  } catch (err) {
    console.error("Backend error:", err);
    return "Error connecting to GawdBotE backend. Is it running?";
  }
}

// ---- Split long messages for Telegram's 4096 char limit ----
async function sendResponse(ctx: Context, response: string): Promise<void> {
  const MAX = 4000;
  if (response.length <= MAX) {
    await ctx.reply(response);
    return;
  }
  let remaining = response;
  while (remaining.length > 0) {
    if (remaining.length <= MAX) {
      await ctx.reply(remaining);
      break;
    }
    let split = remaining.lastIndexOf("\n\n", MAX);
    if (split === -1) split = remaining.lastIndexOf("\n", MAX);
    if (split === -1) split = MAX;
    await ctx.reply(remaining.substring(0, split));
    remaining = remaining.substring(split).trim();
  }
}

// ---- Text messages ----
bot.on("message:text", async (ctx) => {
  const text = ctx.message.text;
  console.log(`[telegram] ${text.substring(0, 60)}`);
  await ctx.replyWithChatAction("typing");
  const response = await sendToBackend(text);
  await sendResponse(ctx, response);
});

// ---- Voice messages ----
bot.on("message:voice", async (ctx) => {
  const voice = ctx.message.voice;
  await ctx.replyWithChatAction("typing");

  try {
    const file = await ctx.getFile();
    const url = `https://api.telegram.org/file/bot${BOT_TOKEN}/${file.file_path}`;
    const res = await fetch(url);
    const buffer = Buffer.from(await res.arrayBuffer());

    // Send audio to backend for transcription
    const formData = new FormData();
    formData.append("audio", new Blob([buffer], { type: "audio/ogg" }), "voice.ogg");

    const transcribeRes = await fetch(`${BACKEND_URL}/voice/transcribe`, {
      method: "POST",
      body: formData,
    });

    const { text } = await transcribeRes.json() as { text: string };
    if (!text) {
      await ctx.reply("Could not transcribe voice message.");
      return;
    }

    await ctx.reply(`_Heard: ${text}_`, { parse_mode: "Markdown" });
    const response = await sendToBackend(`[Voice]: ${text}`);
    await sendResponse(ctx, response);
  } catch (err) {
    console.error("Voice error:", err);
    await ctx.reply("Could not process voice message.");
  }
});

// ---- Photos ----
bot.on("message:photo", async (ctx) => {
  await ctx.replyWithChatAction("typing");
  try {
    const photos = ctx.message.photo;
    const photo = photos[photos.length - 1];
    const file = await ctx.api.getFile(photo.file_id);
    const timestamp = Date.now();
    const filePath = join(UPLOADS_DIR, `img_${timestamp}.jpg`);

    const res = await fetch(`https://api.telegram.org/file/bot${BOT_TOKEN}/${file.file_path}`);
    const buffer = await res.arrayBuffer();
    await writeFile(filePath, Buffer.from(buffer));

    const caption = ctx.message.caption || "Analyze this image.";
    const response = await sendToBackend(`[Image at ${filePath}]: ${caption}`);
    await unlink(filePath).catch(() => {});
    await sendResponse(ctx, response);
  } catch (err) {
    console.error("Photo error:", err);
    await ctx.reply("Could not process image.");
  }
});

// ---- Documents ----
bot.on("message:document", async (ctx) => {
  const doc = ctx.message.document;
  await ctx.replyWithChatAction("typing");
  try {
    const file = await ctx.getFile();
    const timestamp = Date.now();
    const fileName = doc.file_name || `file_${timestamp}`;
    const filePath = join(UPLOADS_DIR, `${timestamp}_${fileName}`);

    const res = await fetch(`https://api.telegram.org/file/bot${BOT_TOKEN}/${file.file_path}`);
    const buffer = await res.arrayBuffer();
    await writeFile(filePath, Buffer.from(buffer));

    const caption = ctx.message.caption || `Analyze: ${doc.file_name}`;
    const response = await sendToBackend(`[File at ${filePath}]: ${caption}`);
    await unlink(filePath).catch(() => {});
    await sendResponse(ctx, response);
  } catch (err) {
    console.error("Document error:", err);
    await ctx.reply("Could not process document.");
  }
});

// ---- Start ----
console.log("GawdBotE Telegram bot starting...");
console.log(`Backend: ${BACKEND_URL}`);
console.log(`Authorized user: ${ALLOWED_USER_ID || "ANY"}`);

bot.start({
  onStart: () => console.log("Bot is running!"),
});
