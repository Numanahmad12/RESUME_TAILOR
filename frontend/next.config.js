/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // The Next.js API routes in src/pages/api/* proxy to the FastAPI backend
  // using the BACKEND_URL env var (defaults to http://localhost:8000 for dev).
  // No rewrites needed — Next.js handles /api/* natively.
};

module.exports = nextConfig;
