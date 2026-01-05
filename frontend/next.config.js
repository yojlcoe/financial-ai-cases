/** @type {import('next').NextConfig} */
const nextConfig = {
  // Use 'export' for Netlify, 'standalone' for local Docker
  output: process.env.NETLIFY ? 'export' : 'standalone',
  images: {
    // Disable image optimization for static export
    unoptimized: process.env.NETLIFY ? true : false,
  },
  async rewrites() {
    // Rewrites only work in non-export mode (local Docker)
    if (process.env.NETLIFY) {
      return [];
    }
    return [
      {
        source: '/api/:path*',
        destination: 'http://backend:8000/api/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
