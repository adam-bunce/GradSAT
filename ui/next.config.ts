import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  // TODO: fix linting/type checks
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  output: "standalone",
};

export default nextConfig;
