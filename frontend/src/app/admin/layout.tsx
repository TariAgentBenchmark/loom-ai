"use client";

import React from "react";
import { AdminAuthProvider } from "../../contexts/AdminAuthContext";

type AdminLayoutProps = {
  children: React.ReactNode;
};

export default function AdminRootLayout({ children }: AdminLayoutProps) {
  return (
    <AdminAuthProvider>
      {children}
    </AdminAuthProvider>
  );
}