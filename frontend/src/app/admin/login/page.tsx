"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAdminAuth } from "../../../contexts/AdminAuthContext";
import AdminLoginModal from "../../../components/AdminLoginModal";

export default function AdminLoginPage() {
  const { state } = useAdminAuth();
  const router = useRouter();
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    // If already authenticated, redirect to dashboard
    if (state.status === "authenticated") {
      router.push("/admin/dashboard");
    } else {
      setIsModalOpen(true);
    }
  }, [state.status, router]);

  const handleCloseModal = () => {
    setIsModalOpen(false);
    // Redirect back to home page if login is cancelled
    router.push("/");
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center">
          <h1 className="text-3xl font-extrabold text-gray-900">LoomAI 管理后台</h1>
          <p className="mt-2 text-sm text-gray-600">
            请使用管理员账户登录
          </p>
        </div>
      </div>

      <AdminLoginModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
      />
    </div>
  );
}