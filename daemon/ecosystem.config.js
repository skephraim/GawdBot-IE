/**
 * GawdBotE — PM2 Process Configuration (Linux/Windows/macOS)
 *
 * Install PM2: npm install -g pm2
 * Start all:   pm2 start daemon/ecosystem.config.js
 * Save:        pm2 save && pm2 startup
 * Status:      pm2 status
 * Logs:        pm2 logs
 */

module.exports = {
  apps: [
    {
      name: "gawdbote-backend",
      script: "python3",
      args: "backend/main.py",
      cwd: process.env.HOME + "/GawdBotE",
      env: { PYTHONUNBUFFERED: "1" },
      watch: false,
      autorestart: true,
      max_restarts: 10,
      restart_delay: 5000,
      log_file: "/tmp/gawdbote-backend.log",
      error_file: "/tmp/gawdbote-backend.err",
    },
    {
      name: "gawdbote-frontend",
      script: "bun",
      args: "start",
      cwd: process.env.HOME + "/GawdBotE/frontend",
      watch: false,
      autorestart: true,
    },
    {
      name: "gawdbote-telegram",
      script: "bun",
      args: "run bot.ts",
      cwd: process.env.HOME + "/GawdBotE/interfaces/telegram",
      watch: false,
      autorestart: true,
      log_file: "/tmp/gawdbote-telegram.log",
    },
  ],
};
