"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  adminGetOrderDetail,
  adminUpdateOrderStatus,
  type AdminOrderDetail,
} from "../lib/api";
import { useAdminAccessToken } from "../contexts/AdminAuthContext";
import {
  ArrowLeft,
  User,
  Mail,
  Calendar,
  CreditCard,
  ShoppingBag,
  Edit,
  Save,
  X,
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
  DollarSign,
} from "lucide-react";

const AdminOrderDetail: React.FC = () => {
  const params = useParams();
  const router = useRouter();
  const accessToken = useAdminAccessToken();
  const orderId = params.orderId as string;

  const [order, setOrder] = useState<AdminOrderDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Status update state
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);
  const [statusReason, setStatusReason] = useState("");
  const [adminNotes, setAdminNotes] = useState("");
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [newStatus, setNewStatus] = useState("");

  const fetchOrderDetail = async () => {
    if (!accessToken || !orderId) return;

    try {
      setLoading(true);
      const response = await adminGetOrderDetail(orderId, accessToken);
      setOrder(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "获取订单详情失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrderDetail();
  }, [accessToken, orderId]);

  const handleUpdateStatus = async () => {
    if (!accessToken || !orderId || !newStatus || !statusReason) return;

    try {
      setIsUpdatingStatus(true);
      await adminUpdateOrderStatus(orderId, newStatus, statusReason, adminNotes, accessToken);
      await fetchOrderDetail();
      setShowStatusModal(false);
      setStatusReason("");
      setAdminNotes("");
      setNewStatus("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "更新订单状态失败");
    } finally {
      setIsUpdatingStatus(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      pending: { bg: "bg-yellow-100", text: "text-yellow-800", label: "待支付", icon: Clock },
      paid: { bg: "bg-green-100", text: "text-green-800", label: "已支付", icon: CheckCircle },
      failed: { bg: "bg-red-100", text: "text-red-800", label: "支付失败", icon: XCircle },
      cancelled: { bg: "bg-gray-100", text: "text-gray-800", label: "已取消", icon: XCircle },
    };

    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.pending;
    const Icon = config.icon;
    return (
      <span className={`inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full ${config.bg} ${config.text}`}>
        <Icon className="h-3 w-3 mr-1" />
        {config.label}
      </span>
    );
  };

  const getPackageTypeBadge = (type: string) => {
    const typeConfig = {
      membership: { bg: "bg-purple-100", text: "text-purple-800", label: "会员套餐" },
      credits: { bg: "bg-blue-100", text: "text-blue-800", label: "算力套餐" },
    };

    const config = typeConfig[type as keyof typeof typeConfig] || typeConfig.credits;
    return (
      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${config.bg} ${config.text}`}>
        {config.label}
      </span>
    );
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("zh-CN", {
      style: "currency",
      currency: "CNY",
      minimumFractionDigits: 0,
    }).format(amount / 100); // Convert from cents to yuan
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

  if (error || !order) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="text-red-800">{error || "无法加载订单详情"}</div>
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
          返回订单列表
        </button>
        
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <ShoppingBag className="h-8 w-8 text-gray-400" />
              </div>
              <div className="ml-6">
                <h1 className="text-2xl font-bold text-gray-900">订单详情</h1>
                <p className="text-sm text-gray-500">{order.orderId}</p>
              </div>
            </div>
            
            <div className="flex space-x-2">
              <button
                onClick={() => {
                  setNewStatus(order.status === "pending" ? "paid" : "pending");
                  setShowStatusModal(true);
                }}
                className={`inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white ${
                  order.status === "pending"
                    ? "bg-green-600 hover:bg-green-700"
                    : "bg-blue-600 hover:bg-blue-700"
                }`}
              >
                {order.status === "pending" ? (
                  <>
                    <CheckCircle className="h-4 w-4 mr-1" />
                    确认支付
                  </>
                ) : (
                  <>
                    <Edit className="h-4 w-4 mr-1" />
                    更新状态
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Order Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">订单信息</h3>
          <div className="space-y-4">
            <div>
              <p className="text-sm font-medium text-gray-500">订单ID</p>
              <p className="text-sm text-gray-900">{order.orderId}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">套餐名称</p>
              <p className="text-sm text-gray-900">{order.packageName}</p>
              <div className="mt-1">{getPackageTypeBadge(order.packageType)}</div>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">套餐ID</p>
              <p className="text-sm text-gray-900">{order.packageId}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">状态</p>
              <div className="mt-1">{getStatusBadge(order.status)}</div>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">支付方式</p>
              <p className="text-sm text-gray-900">{order.paymentMethod}</p>
            </div>
          </div>
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">金额信息</h3>
          <div className="space-y-4">
            <div>
              <p className="text-sm font-medium text-gray-500">原价</p>
              <p className="text-sm text-gray-900">{formatCurrency(order.originalAmount)}</p>
            </div>
            {order.discountAmount > 0 && (
              <div>
                <p className="text-sm font-medium text-gray-500">折扣金额</p>
                <p className="text-sm text-gray-900">{formatCurrency(order.discountAmount)}</p>
              </div>
            )}
            <div>
              <p className="text-sm font-medium text-gray-500">实付金额</p>
              <p className="text-lg font-semibold text-gray-900">{formatCurrency(order.finalAmount)}</p>
            </div>
            {order.creditsAmount && (
              <div>
                <p className="text-sm font-medium text-gray-500">包含算力</p>
                <p className="text-sm text-gray-900">{order.creditsAmount.toLocaleString()}</p>
              </div>
            )}
            {order.membershipDuration && (
              <div>
                <p className="text-sm font-medium text-gray-500">会员时长</p>
                <p className="text-sm text-gray-900">{order.membershipDuration} 天</p>
              </div>
            )}
          </div>
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">用户信息</h3>
          <div className="space-y-4">
            <div>
              <p className="text-sm font-medium text-gray-500">用户ID</p>
              <p className="text-sm text-gray-900">{order.userId}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">用户邮箱</p>
              <p className="text-sm text-gray-900">{order.userEmail}</p>
            </div>
          </div>
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">时间信息</h3>
          <div className="space-y-4">
            <div>
              <p className="text-sm font-medium text-gray-500">创建时间</p>
              <p className="text-sm text-gray-900">{formatDate(order.createdAt)}</p>
            </div>
            {order.paidAt && (
              <div>
                <p className="text-sm font-medium text-gray-500">支付时间</p>
                <p className="text-sm text-gray-900">{formatDate(order.paidAt)}</p>
              </div>
            )}
            {order.expiresAt && (
              <div>
                <p className="text-sm font-medium text-gray-500">过期时间</p>
                <p className="text-sm text-gray-900">{formatDate(order.expiresAt)}</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Status Update Modal */}
      {showStatusModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                更新订单状态
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
                  <option value="pending">待支付</option>
                  <option value="paid">已支付</option>
                  <option value="failed">支付失败</option>
                  <option value="cancelled">已取消</option>
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
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  管理员备注
                </label>
                <textarea
                  value={adminNotes}
                  onChange={(e) => setAdminNotes(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="请输入管理员备注（可选）"
                />
              </div>
              <div className="flex justify-end space-x-2">
                <button
                  onClick={() => {
                    setShowStatusModal(false);
                    setStatusReason("");
                    setAdminNotes("");
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
    </div>
  );
};

export default AdminOrderDetail;