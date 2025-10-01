"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAdminIsAuthenticated } from "../contexts/AdminAuthContext";

interface AdminProtectedRouteProps {
  children: React.ReactNode;
}

const AdminProtectedRoute: React.FC<AdminProtectedRouteProps> = ({ children }) => {
  const router = useRouter();
  const isAuthenticated = useAdminIsAuthenticated();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/admin/login");
    }
  }, [isAuthenticated, router]);

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">正在验证管理员身份...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};

export default AdminProtectedRoute;