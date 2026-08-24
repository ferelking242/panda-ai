import type { NextConfig } from "next";

// Origin of the Python gateway API.
// - Native install: http://127.0.0.1:8000 (default)
// - Docker:         http://panda-ai:8000 (service name)
const API_ORIGIN = process.env.API_ORIGIN || "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  experimental: {
    optimizePackageImports: ["lucide-react", "@radix-ui/react-icons"],
    // Static generation workers — keep low so the build fits in
    // constrained environments (2 GB containers, small VPS).
    cpus: 1,
  },
  allowedDevOrigins: [
    "127.0.0.1",
    "*.replit.dev",
    "*.riker.replit.dev",
    "*.picard.replit.dev",
    "*.kirk.replit.dev",
    "*.spock.replit.dev",
    "*.janeway.replit.dev",
  ],

  images: {
    remotePatterns: [
      { protocol: "https", hostname: "ui.shadcn.com" },
      { protocol: "https", hostname: "images.unsplash.com" },
    ],
    formats: ["image/webp", "image/avif"],
  },

  async rewrites() {
    return [
      { source: "/api/dashboard/:path*", destination: `${API_ORIGIN}/api/dashboard/:path*` },
      { source: "/v1/:path*",            destination: `${API_ORIGIN}/v1/:path*` },
      { source: "/threads",              destination: `${API_ORIGIN}/threads` },
      { source: "/chat",                 destination: `${API_ORIGIN}/chat` },
      { source: "/status",               destination: `${API_ORIGIN}/status` },
      { source: "/healthz",              destination: `${API_ORIGIN}/healthz` },
    ];
  },

  async redirects() {
    return [
      { source: "/home", destination: "/dashboard", permanent: true },
      { source: "/", destination: "/dashboard", permanent: false },
    ];
  },
};

export default nextConfig;
