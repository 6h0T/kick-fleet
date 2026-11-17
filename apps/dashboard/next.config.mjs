/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  async rewrites() {
    const internal = process.env.CONTROLLER_INTERNAL_URL || "http://controller:8000";
    if (!internal) return [];
    return [
      { source: "/api/:path*", destination: `${internal}/api/:path*` },
      { source: "/health", destination: `${internal}/health` },
      { source: "/ws", destination: `${internal}/ws` },
    ];
  },
};

export default nextConfig;
