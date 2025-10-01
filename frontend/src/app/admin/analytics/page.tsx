"use client";

import React from "react";
import { useAdminIsAuthenticated } from "../../../contexts/AdminAuthContext";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import AdminLayout from "../../../components/AdminLayout";
import AdminDashboardStats from "../../../components/AdminDashboardStats";

export default function AdminAnalyticsPage() {
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
          <h1 className="text-2xl font-bold text-gray-900">统计分析</h1>
          <p className="mt-1 text-sm text-gray-600">
            查看详细的系统分析和报告
          </p>
        </div>
        
        <AdminDashboardStats />
      </div>
    </AdminLayout>
  );
}