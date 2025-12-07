"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import AdminLayout from "../../../components/AdminLayout";
import { useAdminIsAuthenticated } from "../../../contexts/AdminAuthContext";
import AdminAgentInvitationManager from "../../../components/AdminAgentInvitationManager";

export default function AdminAgentsPage() {
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
          <h1 className="text-2xl font-bold text-gray-900">渠道 / 邀请码</h1>
          <p className="mt-1 text-sm text-gray-600">
            管理代理商渠道，生成和停用邀请码，并查看各渠道用户归属。
          </p>
        </div>

        <AdminAgentInvitationManager />
      </div>
    </AdminLayout>
  );
}
