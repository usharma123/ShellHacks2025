import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Keep lint strict in dev, but do not fail production builds on lint errors
  eslint: {
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;
