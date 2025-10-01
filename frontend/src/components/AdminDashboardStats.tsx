"use client";

import React, { useEffect, useState } from "react";
import { adminGetDashboardStats, type AdminDashboardStats } from "../lib/api";
import { useAdminAccessToken } from "../contexts/AdminAuthContext";
import {
  Users,
  CreditCard,
  ShoppingBag,
  DollarSign,
  TrendingUp,
  Activity,
} from "lucide-react";

const StatCard: React.FC<{
  title: string;
  value: string | number;
  icon: React.ElementType;
  change?: number;
  changeType?: "increase" | "decrease";
}> = ({ title, value, icon: Icon, change, changeType }) => (
  <div className="bg-white overflow-hidden shadow rounded-lg">
    <div className="p-5">
      <div className="flex items-center">
        <div className="flex-shrink-0">
          <Icon className="h-6 w-6 text-gray-400" />
        </div>
        <div className="ml-5 w-0 flex-1">
          <dl>
            <dt className="text-sm font-medium text-gray-500 truncate">{title}</dt>
            <dd className="flex items-baseline">
              <div className="text-2xl font-semibold text-gray-900">{value}</div>
              {change !== undefined && (
                <div
                  className={`ml-2 flex items-baseline text-sm font-semibold ${
                    changeType === "increase" ? "text-green-600" : "text-red-600"
                  }`}
                >
                  {changeType === "increase" ? (
                    <TrendingUp className="self-center flex-shrink-0 h-4 w-4 text-green-500" />
                  ) : (
                    <TrendingUp className="self-center flex-shrink-0 h-4 w-4 text-red-500 transform rotate-180" />
                  )}
                  <span className="sr-only">
                    {changeType === "increase" ? "Increased" : "Decreased"} by
                  </span>
                  {change}%
                </div>
              )}
            </dd>
          </dl>
        </div>
      </div>
    </div>
  </div>
);

const AdminDashboardStats: React.FC = () => {
  const accessToken = useAdminAccessToken();
  const [stats, setStats] = useState<AdminDashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      if (!accessToken) return;

      try {
        setLoading(true);
        const response = await adminGetDashboardStats(accessToken);
        setStats(response.data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "获取统计数据失败");
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, [accessToken]);

  if (loading) {
    return (
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {[...Array(8)].map((_, i) => (
          <div key={i} className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
                <div className="h-8 bg-gray-200 rounded w-3/4"></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="text-red-800">{error || "无法加载统计数据"}</div>
      </div>
    );
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("zh-CN", {
      style: "currency",
      currency: "CNY",
      minimumFractionDigits: 0,
    }).format(amount / 100); // Convert from cents to yuan
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat("zh-CN").format(num);
  };

  return (
    <div>
      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="总用户数"
          value={formatNumber(stats.users.total)}
          icon={Users}
          change={stats.users.newToday > 0 ? undefined : 0}
          changeType={stats.users.newToday > 0 ? "increase" : "decrease"}
        />
        <StatCard
          title="活跃用户"
          value={formatNumber(stats.users.active)}
          icon={Activity}
        />
        <StatCard
          title="总订单数"
          value={formatNumber(stats.orders.total)}
          icon={ShoppingBag}
        />
        <StatCard
          title="总收入"
          value={formatCurrency(stats.revenue.total)}
          icon={DollarSign}
        />
      </div>

      {/* Additional Stats */}
      <div className="mt-8 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <h3 className="text-lg font-medium text-gray-900 mb-4">用户分布</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">免费用户</span>
                <span className="text-sm font-medium">{formatNumber(stats.users.membershipBreakdown.free)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">基础用户</span>
                <span className="text-sm font-medium">{formatNumber(stats.users.membershipBreakdown.basic)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">高级用户</span>
                <span className="text-sm font-medium">{formatNumber(stats.users.membershipBreakdown.premium)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">企业用户</span>
                <span className="text-sm font-medium">{formatNumber(stats.users.membershipBreakdown.enterprise)}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <h3 className="text-lg font-medium text-gray-900 mb-4">算力统计</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">总算力</span>
                <span className="text-sm font-medium">{formatNumber(stats.credits.total)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">今日交易</span>
                <span className="text-sm font-medium">{formatNumber(stats.credits.transactionsToday)}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <h3 className="text-lg font-medium text-gray-900 mb-4">退款统计</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">待处理退款</span>
                <span className="text-sm font-medium">{formatNumber(stats.subscriptions.pendingRefunds)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">退款总额</span>
                <span className="text-sm font-medium">{formatCurrency(stats.subscriptions.totalRefundAmount)}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="mt-8 bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">最近活动</h3>
          <div className="flow-root">
            <ul className="-mb-8">
              {stats.recentActivity.map((activity, activityIdx) => (
                <li key={activityIdx}>
                  <div className="relative pb-8">
                    {activityIdx !== stats.recentActivity.length - 1 ? (
                      <span
                        className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200"
                        aria-hidden="true"
                      />
                    ) : null}
                    <div className="relative flex space-x-3">
                      <div>
                        <span
                          className={`h-8 w-8 rounded-full flex items-center justify-center ring-8 ring-white ${
                            activity.type === "order"
                              ? "bg-green-500"
                              : activity.type === "refund"
                              ? "bg-yellow-500"
                              : "bg-gray-400"
                          }`}
                        >
                          {activity.type === "order" ? (
                            <ShoppingBag className="h-4 w-4 text-white" />
                          ) : activity.type === "refund" ? (
                            <CreditCard className="h-4 w-4 text-white" />
                          ) : (
                            <Activity className="h-4 w-4 text-white" />
                          )}
                        </span>
                      </div>
                      <div className="min-w-0 flex-1 pt-1.5 flex justify-between space-x-4">
                        <div>
                          <p className="text-sm text-gray-500">
                            {activity.user} {activity.description}
                          </p>
                        </div>
                        <div className="text-right text-sm whitespace-nowrap text-gray-500">
                          <time dateTime={activity.timestamp}>
                            {new Date(activity.timestamp).toLocaleString("zh-CN")}
                          </time>
                          <div className="font-medium text-gray-900">
                            {formatCurrency(activity.amount)}
                          </div>
                          <div
                            className={`text-xs ${
                              activity.status === "paid"
                                ? "text-green-600"
                                : activity.status === "pending"
                                ? "text-yellow-600"
                                : activity.status === "processing"
                                ? "text-blue-600"
                                : "text-red-600"
                            }`}
                          >
                            {activity.status === "paid"
                              ? "已支付"
                              : activity.status === "pending"
                              ? "待支付"
                              : activity.status === "processing"
                              ? "处理中"
                              : activity.status === "approved"
                              ? "已批准"
                              : activity.status === "rejected"
                              ? "已拒绝"
                              : activity.status}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboardStats;