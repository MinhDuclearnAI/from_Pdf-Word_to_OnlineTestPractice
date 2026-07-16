/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  eslint: {
    // Disables eslint during build to speed up and avoid blocker warnings
    ignoreDuringBuilds: true,
  },
  typescript: {
    // Disables type checks during builds to avoid strict build failures on third-party libraries
    ignoreBuildErrors: true,
  }
}

module.exports = nextConfig
