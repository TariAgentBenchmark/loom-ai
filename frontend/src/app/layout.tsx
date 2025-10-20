import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import React from "react";
import "./globals.css";

type RootLayoutProps = {
  children: React.ReactNode;
};

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "图云",
  description: "Frontend for the 图云 platform",
  icons: {
    icon: "/favicon.png",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en" className={inter.className}>
      <body>{children}</body>
    </html>
  );
}
