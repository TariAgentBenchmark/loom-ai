"use client";

import React from "react";
import { useAdminIsAuthenticated } from "../../../contexts/AdminAuthContext";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import AdminLayout from "../../../components/AdminLayout";

export default function AdminSubscriptionsPage() {
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
          <h1 className="text-2xl font-bold text-gray-900">订阅管理</h1>
          <p className="mt-1 text-sm text-gray-600">
            管理用户订阅和套餐
          </p>
        </div>
        
        <div className="bg-white shadow rounded-lg p-6">
          <div className="text-center py-12">
            <h3 className="text-lg font-medium text-gray-900 mb-2">订阅管理功能</h3>
            <p className="text-gray-500">
              此功能正在开发中。您可以通过用户管理页面来管理用户的订阅状态。
            </p>
            <div className="mt-6">
              <button
                onClick={() => router.push("/admin/users")}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
              >
                前往用户管理
              </button>
            </div>
          </div>
        </div>
      </div>
    </AdminLayout>
  );
}