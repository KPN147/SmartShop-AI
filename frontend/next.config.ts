import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Bật standalone output cho Docker deployment
  output: "standalone",
  // Cho phép load ảnh từ CDN của tgdd.vn (ảnh sản phẩm)
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "cdn.tgdd.vn",
      },
    ],
  },
};

export default nextConfig;
