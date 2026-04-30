import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "SmartShop AI — Trợ lý mua sắm thông minh",
  description:
    "AI chatbot tư vấn mua sắm và chăm sóc khách hàng tự động cho SmartShop. Hỗ trợ tư vấn sản phẩm, kiểm tra đơn hàng và giải đáp chính sách.",
  keywords: ["AI chatbot", "mua sắm", "tư vấn", "chăm sóc khách hàng", "e-commerce"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi" className={inter.variable}>
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}
