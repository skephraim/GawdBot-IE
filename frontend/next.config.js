/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    BACKEND_URL: process.env.BACKEND_URL || "http://localhost:8000",
    NEXT_PUBLIC_BACKEND_URL: process.env.BACKEND_URL || "http://localhost:8000",
    NEXT_PUBLIC_WS_URL: process.env.WS_URL || "ws://localhost:8000",
  },
};

module.exports = nextConfig;
