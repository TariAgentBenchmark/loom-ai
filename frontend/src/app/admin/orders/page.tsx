"use client";

import React from "react";
import { useAdminIsAuthenticated } from "../../../contexts/AdminAuthContext";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import AdminLayout from "../../../components/AdminLayout";
import AdminOrderManagement from "../../../components/AdminOrderManagement";

export default function AdminOrdersPage() {
  const isAuthenticated = useAdminIsAuthenticated();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/admin/login");
    }
  }, [isAuthenticated, router]);

  if (!isAuthenticated) {
    return null; // Will redirect
  }

  return (
    <AdminLayout>
      <div className="px-4 py-6 sm:px-6 lg:px-8">
        <AdminOrderManagement />
      </div>
    </AdminLayout>
  );
}