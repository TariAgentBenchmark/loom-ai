"use client";

import React from "react";
import { useAdminIsAuthenticated } from "../../../contexts/AdminAuthContext";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import AdminLayout from "../../../components/AdminLayout";
import AdminDashboardStats from "../../../components/AdminDashboardStats";

export default function AdminDashboardPage() {
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
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">仪表板</h1>
          <p className="mt-1 text-sm text-gray-600">
            查看系统概览和关键指标
          </p>
        </div>
        
        <AdminDashboardStats />
      </div>
    </AdminLayout>
  );
}