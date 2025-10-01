"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  adminGetRefunds,
  adminProcessRefund,
  type AdminRefund,
  type AdminRefundsResponse,
} from "../lib/api";
import { useAdminAccessToken } from "../contexts/AdminAuthContext";
import {
  Search,
  Filter,
  ChevronLeft,
  ChevronRight,
  Eye,
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
  DollarSign,
  Calendar,
  User,
} from "lucide-react";

interface FilterOptions {
  status_filter: string;
  user_filter: string;
  start_date: string;
  end_date: string;
}

const AdminRefundManagement: React.FC = () => {
  const router = useRouter();
  const accessToken = useAdminAccessToken();
  const [refunds, setRefunds] = useState<AdminRefund[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 20,
    total: 0,
    totalPages: 0,
  });
  const [filters, setFilters] = useState<FilterOptions>({
    status_filter: "",
    user_filter: "",
    start_date: "",
    end_date: "",
  });
  const [showFilters, setShowFilters] = useState(false);
  const [summary, setSummary] = useState({
    pendingRefunds: 0,
    approvedRefunds: 0,
    totalRefundAmount: 0,
  });
  const [processingRefund, setProcessingRefund] = useState<string | null>(null);

  const fetchRefunds = async (page = 1) => {
    if (!accessToken) return;

    try {
      setLoading(true);
      const response = await adminGetRefunds(accessToken, {
        page,
        page_size: pagination.limit,
        ...filters,
      });
      setRefunds(response.data.refunds);
      setPagination(response.data.pagination);
      setSummary(response.data.summary);
    } catch (err) {
      setError(err instanceof Error ? err.message : "获取退款列表失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRefunds();
  }, [accessToken]);

  const handleFilterChange = (key: keyof FilterOptions, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const applyFilters = () => {
    fetchRefunds(1);
  };

  const clearFilters = () => {
    setFilters({
      status_filter: "",
      user_filter: "",
      start_date: "",
      end_date: "",
    });
    fetchRefunds(1);
  };

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= pagination.totalPages) {
      fetchRefunds(newPage);
    }
  };

  const handleProcessRefund = async (
    refundId: string,
    action: "approve" | "reject" | "complete",
    reason: string,
    adminNotes: string
  ) => {
    if (!accessToken) return;

    try {
      setProcessingRefund(refundId);
      await adminProcessRefund(refundId, action, reason, adminNotes, null, accessToken);
      await fetchRefunds(pagination.page);
    } catch (err) {
      setError(err instanceof Error ? err.message : "处理退款申请失败");
    } finally {
      setProcessingRefund(null);
    }
  };

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      processing: { bg: "bg-yellow-100", text: "text-yellow-800", label: "处理中", icon: Clock },
      approved: { bg: "bg-blue-100", text: "text-blue-800", label: "已批准", icon: CheckCircle },
      rejected: { bg: "bg-red-100", text: "text-red-800", label: "已拒绝", icon: XCircle },
      completed: { bg: "bg-green-100", text: "text-green-800", label: "已完成", icon: CheckCircle },
    };

    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.processing;
    const Icon = config.icon;
    return (
      <span className={`inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full ${config.bg} ${config.text}`}>
        <Icon className="h-3 w-3 mr-1" />
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

  if (loading && refunds.length === 0) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="text-red-800">{error}</div>
      </div>
    );
  }

  return (
    <div>
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Clock className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">待处理退款</dt>
                  <dd className="text-lg font-medium text-gray-900">{summary.pendingRefunds}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
        
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <CheckCircle className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">已批准退款</dt>
                  <dd className="text-lg font-medium text-gray-900">{summary.approvedRefunds}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
        
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <DollarSign className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">退款总额</dt>
                  <dd className="text-lg font-medium text-gray-900">{formatCurrency(summary.totalRefundAmount)}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white shadow rounded-lg mb-6">
        <div className="px-4 py-5 sm:p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">退款管理</h3>
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              <Filter className="h-4 w-4 mr-2" />
              筛选
            </button>
          </div>

          {showFilters && (
            <div className="border-t pt-4">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    用户搜索
                  </label>
                  <input
                    type="text"
                    value={filters.user_filter}
                    onChange={(e) => handleFilterChange("user_filter", e.target.value)}
                    placeholder="输入邮箱或用户ID"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    退款状态
                  </label>
                  <select
                    value={filters.status_filter}
                    onChange={(e) => handleFilterChange("status_filter", e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">全部</option>
                    <option value="processing">处理中</option>
                    <option value="approved">已批准</option>
                    <option value="rejected">已拒绝</option>
                    <option value="completed">已完成</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    开始日期
                  </label>
                  <input
                    type="date"
                    value={filters.start_date}
                    onChange={(e) => handleFilterChange("start_date", e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    结束日期
                  </label>
                  <input
                    type="date"
                    value={filters.end_date}
                    onChange={(e) => handleFilterChange("end_date", e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
              <div className="mt-4 flex justify-end space-x-2">
                <button
                  onClick={clearFilters}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  清除
                </button>
                <button
                  onClick={applyFilters}
                  className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
                >
                  应用筛选
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Refunds Table */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  退款信息
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  用户
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  订单
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  金额
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  状态
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  申请时间
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {refunds.map((refund) => (
                <tr key={refund.refundId} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{refund.refundId}</div>
                    <div className="text-sm text-gray-500 max-w-xs truncate">{refund.reason}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{refund.userEmail}</div>
                    <div className="text-sm text-gray-500">{refund.userId}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{refund.orderId}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{formatCurrency(refund.amount)}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {getStatusBadge(refund.status)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(refund.createdAt)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex justify-end space-x-2">
                      {refund.status === "processing" && (
                        <>
                          <button
                            onClick={() => {
                              const reason = "退款申请符合条件";
                              const adminNotes = "管理员审核通过";
                              handleProcessRefund(refund.refundId, "approve", reason, adminNotes);
                            }}
                            disabled={processingRefund === refund.refundId}
                            className="text-green-600 hover:text-green-900 disabled:opacity-50"
                            title="批准"
                          >
                            <CheckCircle className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => {
                              const reason = "退款申请不符合条件";
                              const adminNotes = "管理员审核拒绝";
                              handleProcessRefund(refund.refundId, "reject", reason, adminNotes);
                            }}
                            disabled={processingRefund === refund.refundId}
                            className="text-red-600 hover:text-red-900 disabled:opacity-50"
                            title="拒绝"
                          >
                            <XCircle className="h-4 w-4" />
                          </button>
                        </>
                      )}
                      {refund.status === "approved" && (
                        <button
                          onClick={() => {
                            const reason = "退款已完成";
                            const adminNotes = "管理员确认退款完成";
                            handleProcessRefund(refund.refundId, "complete", reason, adminNotes);
                          }}
                          disabled={processingRefund === refund.refundId}
                          className="text-blue-600 hover:text-blue-900 disabled:opacity-50"
                          title="标记完成"
                        >
                          <CheckCircle className="h-4 w-4" />
                        </button>
                      )}
                      <button
                        onClick={() => router.push(`/admin/refunds/${refund.refundId}`)}
                        className="text-blue-600 hover:text-blue-900"
                        title="查看详情"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
          <div className="flex-1 flex justify-between sm:hidden">
            <button
              onClick={() => handlePageChange(pagination.page - 1)}
              disabled={pagination.page <= 1}
              className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              上一页
            </button>
            <button
              onClick={() => handlePageChange(pagination.page + 1)}
              disabled={pagination.page >= pagination.totalPages}
              className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              下一页
            </button>
          </div>
          <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
            <div>
              <p className="text-sm text-gray-700">
                显示第 <span className="font-medium">{(pagination.page - 1) * pagination.limit + 1}</span> 至{" "}
                <span className="font-medium">
                  {Math.min(pagination.page * pagination.limit, pagination.total)}
                </span>{" "}
                条，共 <span className="font-medium">{pagination.total}</span> 条记录
              </p>
            </div>
            <div>
              <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                <button
                  onClick={() => handlePageChange(pagination.page - 1)}
                  disabled={pagination.page <= 1}
                  className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronLeft className="h-5 w-5" />
                </button>
                
                {/* Page numbers */}
                {Array.from({ length: Math.min(5, pagination.totalPages) }, (_, i) => {
                  let pageNum;
                  if (pagination.totalPages <= 5) {
                    pageNum = i + 1;
                  } else if (pagination.page <= 3) {
                    pageNum = i + 1;
                  } else if (pagination.page >= pagination.totalPages - 2) {
                    pageNum = pagination.totalPages - 4 + i;
                  } else {
                    pageNum = pagination.page - 2 + i;
                  }
                  
                  return (
                    <button
                      key={pageNum}
                      onClick={() => handlePageChange(pageNum)}
                      className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                        pageNum === pagination.page
                          ? "z-10 bg-blue-50 border-blue-500 text-blue-600"
                          : "bg-white border-gray-300 text-gray-500 hover:bg-gray-50"
                      }`}
                    >
                      {pageNum}
                    </button>
                  );
                })}
                
                <button
                  onClick={() => handlePageChange(pagination.page + 1)}
                  disabled={pagination.page >= pagination.totalPages}
                  className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronRight className="h-5 w-5" />
                </button>
              </nav>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminRefundManagement;