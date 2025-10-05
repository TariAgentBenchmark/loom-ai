/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    // 仅在开发环境中启用代理
    if (process.env.NODE_ENV === 'development') {
      return [
        {
          source: '/api/:path*',
          destination: 'http://localhost:8000/v1/:path*',
        },
        {
          source: '/files/:path*',
          destination: 'http://localhost:8000/files/:path*',
        },
        {
          source: '/uploads/:path*',
          destination: 'http://localhost:8000/uploads/:path*',
        },
      ];
    }
    return [];
  },
};

export default nextConfig;
