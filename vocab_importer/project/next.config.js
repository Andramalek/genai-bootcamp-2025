/** @type {import('next').NextConfig} */
const nextConfig = {
  // We need to keep the app in server-rendered mode for API routes
  // Do NOT use output: 'export' as it disables API routes
  eslint: {
    ignoreDuringBuilds: true,
  },
  images: { unoptimized: true },
};

module.exports = nextConfig;