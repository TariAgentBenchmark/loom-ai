"use client";

import React, { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  adminGetUserDetail,
  adminUpdateUserStatus,
  adminGetUserTransactions,
  adminAdjustUserCredits,
  type AdminUserDetail,
  type AdminCreditTransaction,
  type AdminCreditTransactionsResponse,
} from "../lib/api";
import { useAdminAccessToken } from "../contexts/AdminAuthContext";
import {
  ArrowLeft,
  User,
  Mail,
  Calendar,
  CreditCard,
  Activity,
  Edit,
  Save,
  X,
  Plus,
  Minus,
  Crown,
  UserCheck,
  UserX,
  History,
} from "lucide-react";

const AdminUserDetail: React.FC = () => {
  const params = useParams();
  const router = useRouter();
  const accessToken = useAdminAccessToken();
  const userId = params.userId as string;

  const [user, setUser] = useState<AdminUserDetail | null>(null);
  const [transactions, setTransactions] = useState<AdminCreditTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"overview" | "transactions" | "actions">("overview");
  
  // Status update state
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);
  const [statusReason, setStatusReason] = useState("");
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [newStatus, setNewStatus] = useState("");
  
  
  // Credit adjustment state
  const [isAdjustingCredits, setIsAdjustingCredits] = useState(false);
  const [creditAdjustment, setCreditAdjustment] = useState({
    amount: 0,
    reason: "",
    sendNotification: true,
  });
  const [showCreditModal, setShowCreditModal] = useState(false);

  const fetchUserDetail = useCallback(async () => {
    if (!accessToken || !userId) return;

    try {
      setLoading(true);
      const response = await adminGetUserDetail(userId, accessToken);
      setUser(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "获取用户详情失败");
    } finally {
      setLoading(false);
    }
  }, [accessToken, userId]);

  const fetchUserTransactions = useCallback(async () => {
    if (!accessToken || !userId) return;

    try {
      const response = await adminGetUserTransactions(userId, accessToken, {
        page: 1,
        page_size: 10,
      });
      setTransactions(response.data.transactions);
    } catch (err) {
      console.error("获取用户交易记录失败:", err);
    }
  }, [accessToken, userId]);

  useEffect(() => {
    fetchUserDetail();
    fetchUserTransactions();
  }, [fetchUserDetail, fetchUserTransactions]);

  const handleUpdateStatus = useCallback(async () => {
    if (!accessToken || !userId || !newStatus || !statusReason) return;

    try {
      setIsUpdatingStatus(true);
      await adminUpdateUserStatus(userId, newStatus, statusReason, accessToken);
      await fetchUserDetail();
      setShowStatusModal(false);
      setStatusReason("");
      setNewStatus("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "更新用户状态失败");
    } finally {
      setIsUpdatingStatus(false);
    }
  }, [accessToken, fetchUserDetail, newStatus, statusReason, userId]);


  const handleAdjustCredits = useCallback(async () => {
    if (!accessToken || !userId || !creditAdjustment.reason) return;

    try {
      setIsAdjustingCredits(true);
      await adminAdjustUserCredits(
        userId,
        creditAdjustment.amount,
        creditAdjustment.reason,
        creditAdjustment.sendNotification,
        accessToken
      );
      await fetchUserDetail();
      await fetchUserTransactions();
      setShowCreditModal(false);
      setCreditAdjustment({ amount: 0, reason: "", sendNotification: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "调整用户算力失败");
    } finally {
      setIsAdjustingCredits(false);
    }
  }, [accessToken, creditAdjustment, fetchUserDetail, fetchUserTransactions, userId]);

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      active: { bg: "bg-green-100", text: "text-green-800", label: "活跃" },
      suspended: { bg: "bg-red-100", text: "text-red-800", label: "已暂停" },
      inactive: { bg: "bg-gray-100", text: "text-gray-800", label: "未激活" },
    };

    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.inactive;
    return (
      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${config.bg} ${config.text}`}>
        {config.label}
      </span>
    );
  };


  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString("zh-CN");
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !user) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="text-red-800">{error || "无法加载用户详情"}</div>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => router.back()}
          className="flex items-center text-sm text-gray-500 hover:text-gray-700 mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          返回用户列表
        </button>
        
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="flex-shrink-0 h-16 w-16">
                <div className="h-16 w-16 rounded-full bg-gray-300 flex items-center justify-center">
                  <span className="text-xl font-medium text-gray-600">
                    {user.nickname?.charAt(0) || user.email?.charAt(0) || "U"}
                  </span>
                </div>
              </div>
              <div className="ml-6">
                <h1 className="text-2xl font-bold text-gray-900">
                  {user.nickname || "未设置昵称"}
                </h1>
                <p className="text-sm text-gray-500">{user.email || "未设置邮箱"}</p>
                <div className="mt-2 flex items-center space-x-2">
                  {getStatusBadge(user.status)}
                  {user.isAdmin && (
                    <div className="flex items-center">
                      <Crown className="h-3 w-3 text-yellow-500 mr-1" />
                      <span className="text-xs text-yellow-600">管理员</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
            
            <div className="flex space-x-2">
              <button
                onClick={() => {
                  setNewStatus(user.status === "active" ? "suspended" : "active");
                  setShowStatusModal(true);
                }}
                className={`inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white ${
                  user.status === "active"
                    ? "bg-red-600 hover:bg-red-700"
                    : "bg-green-600 hover:bg-green-700"
                }`}
              >
                {user.status === "active" ? (
                  <>
                    <UserX className="h-4 w-4 mr-1" />
                    暂停用户
                  </>
                ) : (
                  <>
                    <UserCheck className="h-4 w-4 mr-1" />
                    激活用户
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab("overview")}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === "overview"
                ? "border-blue-500 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            }`}
          >
            概览
          </button>
          <button
            onClick={() => setActiveTab("transactions")}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === "transactions"
                ? "border-blue-500 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            }`}
          >
            交易记录
          </button>
          <button
            onClick={() => setActiveTab("actions")}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === "actions"
                ? "border-blue-500 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            }`}
          >
            管理操作
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-white shadow rounded-lg p-6">
            <div className="flex items-center">
              <CreditCard className="h-8 w-8 text-blue-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">算力余额</p>
                <p className="text-2xl font-semibold text-gray-900">{user.credits.toLocaleString()}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white shadow rounded-lg p-6">
            <div className="flex items-center">
              <Calendar className="h-8 w-8 text-green-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">注册时间</p>
                <p className="text-sm text-gray-900">{formatDate(user.createdAt)}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white shadow rounded-lg p-6">
            <div className="flex items-center">
              <Activity className="h-8 w-8 text-purple-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">最后登录</p>
                <p className="text-sm text-gray-900">
                  {user.lastLoginAt ? formatDate(user.lastLoginAt) : "从未登录"}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === "transactions" && (
        <div className="bg-white shadow rounded-lg">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    交易ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    类型
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    金额
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    余额后
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    来源
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    时间
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {transactions.map((transaction) => (
                  <tr key={transaction.transactionId}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {transaction.transactionId}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          transaction.type === "earn"
                            ? "bg-green-100 text-green-800"
                            : "bg-red-100 text-red-800"
                        }`}
                      >
                        {transaction.type === "earn" ? "获得" : "消费"}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <span className={transaction.type === "earn" ? "text-green-600" : "text-red-600"}>
                        {transaction.type === "earn" ? "+" : "-"}
                        {transaction.amount.toLocaleString()}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {transaction.balanceAfter.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {transaction.source}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(transaction.createdAt)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === "actions" && (
        <div className="space-y-6">
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">算力调整</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  当前算力
                </label>
                <p className="text-2xl font-semibold text-gray-900">{user.credits.toLocaleString()}</p>
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => {
                    setCreditAdjustment({ ...creditAdjustment, amount: 100 });
                    setShowCreditModal(true);
                  }}
                  className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700"
                >
                  <Plus className="h-4 w-4 mr-1" />
                  增加算力
                </button>
                <button
                  onClick={() => {
                    setCreditAdjustment({ ...creditAdjustment, amount: -100 });
                    setShowCreditModal(true);
                  }}
                  className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700"
                >
                  <Minus className="h-4 w-4 mr-1" />
                  减少算力
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Status Update Modal */}
      {showStatusModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                更新用户状态
              </h3>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  新状态
                </label>
                <select
                  value={newStatus}
                  onChange={(e) => setNewStatus(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="active">活跃</option>
                  <option value="suspended">已暂停</option>
                  <option value="inactive">未激活</option>
                </select>
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  原因
                </label>
                <textarea
                  value={statusReason}
                  onChange={(e) => setStatusReason(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="请输入状态变更原因"
                />
              </div>
              <div className="flex justify-end space-x-2">
                <button
                  onClick={() => {
                    setShowStatusModal(false);
                    setStatusReason("");
                    setNewStatus("");
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  onClick={handleUpdateStatus}
                  disabled={isUpdatingStatus || !statusReason}
                  className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                >
                  {isUpdatingStatus ? "更新中..." : "确认"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}


      {/* Credit Adjustment Modal */}
      {showCreditModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                调整用户算力
              </h3>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  调整金额
                </label>
                <input
                  type="number"
                  value={creditAdjustment.amount}
                  onChange={(e) =>
                    setCreditAdjustment({ ...creditAdjustment, amount: parseInt(e.target.value) || 0 })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                  正数为增加，负数为减少
                </p>
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  原因
                </label>
                <textarea
                  value={creditAdjustment.reason}
                  onChange={(e) =>
                    setCreditAdjustment({ ...creditAdjustment, reason: e.target.value })
                  }
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="请输入算力调整原因"
                />
              </div>
              <div className="mb-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={creditAdjustment.sendNotification}
                    onChange={(e) =>
                      setCreditAdjustment({ ...creditAdjustment, sendNotification: e.target.checked })
                    }
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">发送通知给用户</span>
                </label>
              </div>
              <div className="flex justify-end space-x-2">
                <button
                  onClick={() => {
                    setShowCreditModal(false);
                    setCreditAdjustment({ amount: 0, reason: "", sendNotification: true });
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  onClick={handleAdjustCredits}
                  disabled={isAdjustingCredits || !creditAdjustment.reason || creditAdjustment.amount === 0}
                  className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                >
                  {isAdjustingCredits ? "调整中..." : "确认"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminUserDetail;