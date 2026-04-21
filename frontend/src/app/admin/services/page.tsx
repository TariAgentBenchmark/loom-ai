"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAdminIsAuthenticated } from "../../../contexts/AdminAuthContext";
import AdminLayout from "../../../components/AdminLayout";
import AdminReferralRewardSettings from "../../../components/AdminReferralRewardSettings";
import AdminServicePricing from "../../../components/AdminServicePricing";

export default function AdminServicePricingPage() {
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
      <div className="space-y-6 px-4 py-6 sm:px-6 lg:px-8">
        <AdminReferralRewardSettings />
        <AdminServicePricing />
      </div>
    </AdminLayout>
  );
}
