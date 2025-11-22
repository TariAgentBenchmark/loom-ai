import type { Metadata, Viewport } from "next";
import React from "react";
import "./globals.css";

type RootLayoutProps = {
  children: React.ReactNode;
};

export const metadata: Metadata = {
  title: "图云",
  description: "Frontend for the 图云 platform",
  icons: {
    icon: "/favicon.png",
  },
  other: {
    "google": "notranslate",
    "googlebot": "notranslate",
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
    <html lang="en" translate="no">
      <body className="notranslate">{children}</body>
    </html>
  );
}
