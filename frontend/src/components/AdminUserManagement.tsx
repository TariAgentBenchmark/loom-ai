"use client";

import React, { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  adminGetUsers,
  adminCreateUser,
  adminDeleteUser,
  adminAdjustUserCredits,
  type AdminUser,
} from "../lib/api";
import { useAdminAccessToken } from "../contexts/AdminAuthContext";
import {
  Filter,
  ChevronLeft,
  ChevronRight,
  Eye,
  Edit,
  UserX,
  Crown,
  Plus,
} from "lucide-react";
import { formatDateTime } from "../lib/datetime";

interface FilterOptions {
  status_filter: string;
  email_filter: string;
  sort_by: string;
  sort_order: string;
}

interface CreateUserFormState {
  phone: string;
  email: string;
  nickname: string;
  password: string;
  confirmPassword: string;
  initialCredits: number;
  isAdmin: boolean;
}

interface CreditAdjustmentFormState {
  amount: number;
  reason: string;
  sendNotification: boolean;
}

const defaultFilters: FilterOptions = {
  status_filter: "",
  email_filter: "",
  sort_by: "created_at",
  sort_order: "desc",
};

const AdminUserManagement: React.FC = () => {
  const router = useRouter();
  const accessToken = useAdminAccessToken();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 20,
    total: 0,
    totalPages: 0,
  });
  const [filters, setFilters] = useState<FilterOptions>({ ...defaultFilters });
  const [activeFilters, setActiveFilters] = useState<FilterOptions>({ ...defaultFilters });
  const [showFilters, setShowFilters] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createForm, setCreateForm] = useState<CreateUserFormState>({
    phone: "",
    email: "",
    nickname: "",
    password: "",
    confirmPassword: "",
    initialCredits: 0,
    isAdmin: false,
  });
  const [createError, setCreateError] = useState<string | null>(null);
  const [isCreatingUser, setIsCreatingUser] = useState(false);
  const [showCreditModal, setShowCreditModal] = useState(false);
  const [creditTarget, setCreditTarget] = useState<AdminUser | null>(null);
  const [creditForm, setCreditForm] = useState<CreditAdjustmentFormState>({
    amount: 0,
    reason: "",
    sendNotification: true,
  });
  const [creditError, setCreditError] = useState<string | null>(null);
  const [isAdjustingCredits, setIsAdjustingCredits] = useState(false);
  const [userToDelete, setUserToDelete] = useState<AdminUser | null>(null);
  const [deleteReason, setDeleteReason] = useState("");
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [isDeletingUser, setIsDeletingUser] = useState(false);

  const fetchUsers = useCallback(
    async (page = 1, overrides?: FilterOptions) => {
      if (!accessToken) return;

      try {
        setLoading(true);
        const response = await adminGetUsers(accessToken, {
          page,
          page_size: pagination.limit,
          ...(overrides ?? activeFilters),
        });
        setUsers(response.data.users);
        const p: any = response.data.pagination || {};
        setPagination((prev) => {
          const resolvedLimit = p.limit ?? prev.limit;
          const resolvedTotal = p.total ?? prev.total ?? 0;
          const resolvedTotalPages =
            p.total_pages ??
            p.totalPages ??
            (resolvedLimit > 0 ? Math.ceil(resolvedTotal / resolvedLimit) : 0);
          return {
            page: p.page ?? page,
            limit: resolvedLimit,
            total: resolvedTotal,
            totalPages: resolvedTotalPages,
          };
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : "获取用户列表失败");
      } finally {
        setLoading(false);
      }
    },
    [accessToken, activeFilters, pagination.limit]
  );

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleFilterChange = (key: keyof FilterOptions, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const applyFilters = () => {
    setActiveFilters(filters);
    fetchUsers(1, filters);
  };

  const clearFilters = () => {
    setFilters({ ...defaultFilters });
    setActiveFilters({ ...defaultFilters });
    fetchUsers(1, { ...defaultFilters });
  };

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= pagination.totalPages) {
      fetchUsers(newPage);
    }
  };

  const handleViewUser = (userId: string) => {
    router.push(`/admin/users/${userId}`);
  };

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


  const resetCreateForm = () => {
    setCreateForm({
      phone: "",
      email: "",
      nickname: "",
      password: "",
      confirmPassword: "",
      initialCredits: 0,
      isAdmin: false,
    });
  };

  const closeCreateModal = () => {
    setShowCreateModal(false);
    setCreateError(null);
    resetCreateForm();
  };

  const openCreateModal = () => {
    setCreateError(null);
    setShowCreateModal(true);
  };

  const handleCreateUser = async () => {
    if (!accessToken) return;

    if (!createForm.phone.trim()) {
      setCreateError("请填写手机号");
      return;
    }

    if (!createForm.password) {
      setCreateError("请设置登录密码");
      return;
    }

    if (createForm.password !== createForm.confirmPassword) {
      setCreateError("两次输入的密码不一致");
      return;
    }

    try {
      setIsCreatingUser(true);
      await adminCreateUser(
        {
          phone: createForm.phone.trim(),
          email: createForm.email.trim() || undefined,
          nickname: createForm.nickname.trim() || undefined,
          password: createForm.password,
          initialCredits: Math.max(0, createForm.initialCredits),
          isAdmin: createForm.isAdmin,
        },
        accessToken
      );
      closeCreateModal();
      await fetchUsers(1);
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : "创建用户失败");
    } finally {
      setIsCreatingUser(false);
    }
  };

  const closeCreditModal = () => {
    setShowCreditModal(false);
    setCreditTarget(null);
    setCreditError(null);
    setCreditForm({
      amount: 0,
      reason: "",
      sendNotification: true,
    });
  };

  const openCreditModal = (user: AdminUser) => {
    setCreditTarget(user);
    setCreditForm({
      amount: 0,
      reason: "",
      sendNotification: true,
    });
    setCreditError(null);
    setShowCreditModal(true);
  };

  const handleAdjustCredits = async () => {
    if (!accessToken || !creditTarget) return;

    if (!creditForm.amount) {
      setCreditError("请输入非零的积分变更值，可为正负数");
      return;
    }

    if (!creditForm.reason.trim()) {
      setCreditError("请填写调整原因");
      return;
    }

    try {
      setIsAdjustingCredits(true);
      await adminAdjustUserCredits(
        creditTarget.userId,
        creditForm.amount,
        creditForm.reason.trim(),
        creditForm.sendNotification,
        accessToken
      );
      closeCreditModal();
      await fetchUsers(pagination.page);
    } catch (err) {
      setCreditError(err instanceof Error ? err.message : "调整积分失败");
    } finally {
      setIsAdjustingCredits(false);
    }
  };

  const closeDeleteModal = () => {
    setUserToDelete(null);
    setDeleteReason("");
    setDeleteError(null);
  };

  const openDeleteModal = (user: AdminUser) => {
    setUserToDelete(user);
    setDeleteReason("");
    setDeleteError(null);
  };

  const handleDeleteUser = async () => {
    if (!accessToken || !userToDelete) return;

    try {
      setIsDeletingUser(true);
      const reason = deleteReason.trim();
      await adminDeleteUser(
        userToDelete.userId,
        accessToken,
        reason ? { reason } : undefined
      );
      const nextPage =
        users.length <= 1 && pagination.page > 1 ? pagination.page - 1 : pagination.page;
      closeDeleteModal();
      await fetchUsers(nextPage);
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : "删除用户失败");
    } finally {
      setIsDeletingUser(false);
    }
  };

  if (loading && users.length === 0) {
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
      {/* Filters */}
      <div className="bg-white shadow rounded-lg mb-6">
        <div className="px-4 py-5 sm:p-6">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">用户管理</h3>
            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={openCreateModal}
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 shadow-sm"
              >
                <Plus className="h-4 w-4 mr-2" />
                新增用户
              </button>
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                <Filter className="h-4 w-4 mr-2" />
                筛选
              </button>
            </div>
          </div>

          {showFilters && (
            <div className="border-t pt-4">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    邮箱搜索
                  </label>
                  <input
                    type="text"
                    value={filters.email_filter}
                    onChange={(e) => handleFilterChange("email_filter", e.target.value)}
                    placeholder="输入邮箱"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    状态
                  </label>
                  <select
                    value={filters.status_filter}
                    onChange={(e) => handleFilterChange("status_filter", e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">全部</option>
                    <option value="active">活跃</option>
                    <option value="suspended">已暂停</option>
                    <option value="inactive">未激活</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    排序字段
                  </label>
                  <select
                    value={filters.sort_by}
                    onChange={(e) => handleFilterChange("sort_by", e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="created_at">创建时间</option>
                    <option value="last_login_at">最后登录</option>
                    <option value="credits">积分余额</option>
                    <option value="email">邮箱</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    排序方式
                  </label>
                  <select
                    value={filters.sort_order}
                    onChange={(e) => handleFilterChange("sort_order", e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="desc">降序</option>
                    <option value="asc">升序</option>
                  </select>
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

      {/* Users Table */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  用户
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  状态
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  积分余额
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  注册时间
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  最后登录
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {users.map((user) => (
                <tr key={user.userId} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-10 w-10">
                        <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                          <span className="text-sm font-medium text-gray-600">
                            {user.nickname?.charAt(0) || user.email?.charAt(0) || user.phone?.charAt(0) || "U"}
                          </span>
                        </div>
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">
                          {user.nickname || user.phone || user.email || "未设置昵称"}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          <span className="text-gray-600 mr-1">手机号</span>
                          {user.phone || "未设置手机号"}
                        </div>
                        <div className="text-xs text-gray-500">
                          <span className="text-gray-600 mr-1">邮箱</span>
                          {user.email || "未设置邮箱"}
                        </div>
                        {user.isAdmin && (
                          <div className="flex items-center mt-1">
                            <Crown className="h-3 w-3 text-yellow-500 mr-1" />
                            <span className="text-xs text-yellow-600">管理员</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {getStatusBadge(user.status)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {user.credits.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDateTime(user.createdAt)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {user.lastLoginAt ? formatDateTime(user.lastLoginAt) : "从未登录"}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex justify-end space-x-2">
                      <button
                        onClick={() => openCreditModal(user)}
                        className="text-amber-600 hover:text-amber-800"
                        title="调整积分"
                      >
                        <Edit className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => openDeleteModal(user)}
                        className="text-red-600 hover:text-red-800"
                        title="删除用户"
                      >
                        <UserX className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleViewUser(user.userId)}
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

      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-30 px-4 py-8">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl">
            <div className="px-6 py-4 border-b">
              <h4 className="text-lg font-medium text-gray-900">新增用户</h4>
              <p className="mt-1 text-sm text-gray-500">填写基础信息并设置初始积分</p>
            </div>
            <div className="px-6 py-4 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">手机号 *</label>
                  <input
                    type="text"
                    value={createForm.phone}
                    onChange={(e) => setCreateForm((prev) => ({ ...prev, phone: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    placeholder="请输入11位手机号"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">邮箱</label>
                  <input
                    type="email"
                    value={createForm.email}
                    onChange={(e) => setCreateForm((prev) => ({ ...prev, email: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    placeholder="user@example.com"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">昵称</label>
                  <input
                    type="text"
                    value={createForm.nickname}
                    onChange={(e) => setCreateForm((prev) => ({ ...prev, nickname: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    placeholder="用户昵称"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">初始积分</label>
                  <input
                    type="number"
                    min={0}
                    value={createForm.initialCredits}
                    onChange={(e) => {
                      const value = Number(e.target.value);
                      setCreateForm((prev) => ({
                        ...prev,
                        initialCredits: Number.isNaN(value) ? 0 : Math.max(0, value),
                      }));
                    }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    placeholder="0"
                  />
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">登录密码 *</label>
                  <input
                    type="password"
                    value={createForm.password}
                    onChange={(e) => setCreateForm((prev) => ({ ...prev, password: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    placeholder="至少6位字符"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">确认密码 *</label>
                  <input
                    type="password"
                    value={createForm.confirmPassword}
                    onChange={(e) =>
                      setCreateForm((prev) => ({ ...prev, confirmPassword: e.target.value }))
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    placeholder="再次输入密码"
                  />
                </div>
              </div>
              <label className="inline-flex items-center text-sm text-gray-700">
                <input
                  type="checkbox"
                  checked={createForm.isAdmin}
                  onChange={(e) => setCreateForm((prev) => ({ ...prev, isAdmin: e.target.checked }))}
                  className="h-4 w-4 text-blue-600 border-gray-300 rounded mr-2"
                />
                授予管理员权限
              </label>
              {createError && <p className="text-sm text-red-600">{createError}</p>}
            </div>
            <div className="px-6 py-4 border-t flex justify-end space-x-2">
              <button
                onClick={closeCreateModal}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                disabled={isCreatingUser}
              >
                取消
              </button>
              <button
                onClick={handleCreateUser}
                disabled={isCreatingUser}
                className="px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-60"
              >
                {isCreatingUser ? "创建中..." : "确认创建"}
              </button>
            </div>
          </div>
        </div>
      )}

      {showCreditModal && creditTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-30 px-4 py-8">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg">
            <div className="px-6 py-4 border-b">
              <h4 className="text-lg font-medium text-gray-900">调整积分</h4>
              <p className="mt-1 text-sm text-gray-500">
                {creditTarget.nickname || creditTarget.email || creditTarget.userId}
              </p>
            </div>
            <div className="px-6 py-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">变更数量 *</label>
                <input
                  type="number"
                  value={creditForm.amount}
                  onChange={(e) => {
                    const value = Number(e.target.value);
                    setCreditForm((prev) => ({
                      ...prev,
                      amount: Number.isNaN(value) ? 0 : value,
                    }));
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  placeholder="示例：100 或 -50"
                />
                <p className="mt-1 text-xs text-gray-500">正数为增加，负数为扣减</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">调整原因 *</label>
                <textarea
                  rows={3}
                  value={creditForm.reason}
                  onChange={(e) => setCreditForm((prev) => ({ ...prev, reason: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  placeholder="请输入具体原因"
                />
              </div>
              <label className="inline-flex items-center text-sm text-gray-700">
                <input
                  type="checkbox"
                  checked={creditForm.sendNotification}
                  onChange={(e) =>
                    setCreditForm((prev) => ({ ...prev, sendNotification: e.target.checked }))
                  }
                  className="h-4 w-4 text-blue-600 border-gray-300 rounded mr-2"
                />
                同时通知用户
              </label>
              {creditError && <p className="text-sm text-red-600">{creditError}</p>}
            </div>
            <div className="px-6 py-4 border-t flex justify-end space-x-2">
              <button
                onClick={closeCreditModal}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                disabled={isAdjustingCredits}
              >
                取消
              </button>
              <button
                onClick={handleAdjustCredits}
                disabled={isAdjustingCredits}
                className="px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-60"
              >
                {isAdjustingCredits ? "调整中..." : "确认调整"}
              </button>
            </div>
          </div>
        </div>
      )}

      {userToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-30 px-4 py-8">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg">
            <div className="px-6 py-4 border-b">
              <h4 className="text-lg font-medium text-gray-900">确认删除用户</h4>
              <p className="mt-1 text-sm text-gray-500">
                将永久移除 {userToDelete.nickname || userToDelete.email || userToDelete.userId} 及其关联数据
              </p>
            </div>
            <div className="px-6 py-4 space-y-4">
              <div className="bg-red-50 border border-red-200 rounded-md px-3 py-2 text-sm text-red-700">
                此操作不可撤销，请谨慎执行。
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">删除原因</label>
                <textarea
                  rows={3}
                  value={deleteReason}
                  onChange={(e) => setDeleteReason(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  placeholder="可选，用于审计记录"
                />
              </div>
              {deleteError && <p className="text-sm text-red-600">{deleteError}</p>}
            </div>
            <div className="px-6 py-4 border-t flex justify-end space-x-2">
              <button
                onClick={closeDeleteModal}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                disabled={isDeletingUser}
              >
                取消
              </button>
              <button
                onClick={handleDeleteUser}
                disabled={isDeletingUser}
                className="px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-red-600 hover:bg-red-700 disabled:opacity-60"
              >
                {isDeletingUser ? "删除中..." : "确认删除"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminUserManagement;
