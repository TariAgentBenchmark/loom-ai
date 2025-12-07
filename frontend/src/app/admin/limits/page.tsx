"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import AdminLayout from "../../../components/AdminLayout";
import { useAdminIsAuthenticated } from "../../../contexts/AdminAuthContext";
import AdminApiLimitMetrics from "../../../components/AdminApiLimitMetrics";

export default function AdminApiLimitsPage() {
  const isAuthenticated = useAdminIsAuthenticated();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/admin/login");
    }
  }, [isAuthenticated, router]);

  if (!isAuthenticated) {
    return null;
  }

  return (
    <AdminLayout>
      <div className="px-4 py-6 sm:px-6 lg:px-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">并发限流监控</h1>
          <p className="mt-1 text-sm text-gray-600">
            实时查看各下游 API 的并发利用率、空闲槽位与租约状态，定位拥堵和排队。
          </p>
        </div>

        <AdminApiLimitMetrics />
      </div>
    </AdminLayout>
  );
}
