"use client";

import React, { useState, useEffect } from "react";
import { useAdminIsAuthenticated, useAdminAccessToken } from "../../../contexts/AdminAuthContext";
import { useRouter } from "next/navigation";
import AdminLayout from "../../../components/AdminLayout";
import { adminGetAllTasks, adminSearchUserSuggestions, type AdminUserTask, type HistoryTask, type UserSuggestion, resolveFileUrl } from "../../../lib/api";
import { formatDateTime } from "../../../lib/datetime";
import { Search, Filter, ChevronLeft, ChevronRight, Calendar, User, Layers, AlertCircle, X } from "lucide-react";
import ImagePreview from "../../../components/ImagePreview";

export default function AdminTaskBrowserPage() {
  const isAuthenticated = useAdminIsAuthenticated();
  const accessToken = useAdminAccessToken();
  const router = useRouter();

  const [tasks, setTasks] = useState<(AdminUserTask & { user?: { userId: string; email?: string; nickname?: string } })[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTask, setSelectedTask] = useState<HistoryTask | null>(null);
  const [errorDetailTask, setErrorDetailTask] = useState<AdminUserTask & { user?: { userId: string; email?: string; nickname?: string } } | null>(null);

  // 用户搜索自动完成
  const [userSearchInput, setUserSearchInput] = useState("");
  const [userSuggestions, setUserSuggestions] = useState<UserSuggestion[]>([]);
  const [selectedUser, setSelectedUser] = useState<UserSuggestion | null>(null);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  // 筛选条件
  const [filters, setFilters] = useState({
    userSearch: "",
    taskType: "",
    status: "",
    startDate: "",
    endDate: "",
  });

  // 分页
  const [page, setPage] = useState(1);
  const [limit] = useState(20);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/admin/login");
    }
  }, [isAuthenticated, router]);

  useEffect(() => {
    if (isAuthenticated && accessToken) {
      fetchTasks();
    }
  }, [isAuthenticated, accessToken, page, filters]);

  // 搜索用户建议
  useEffect(() => {
    const searchUsers = async () => {
      // 如果已选择用户或输入为空，不进行搜索
      if (selectedUser || !accessToken || !userSearchInput || userSearchInput.length < 2) {
        setUserSuggestions([]);
        return;
      }

      try {
        setSearchLoading(true);
        setSearchError(null);
        const response = await adminSearchUserSuggestions(accessToken, userSearchInput, 10);
        if (response.success && response.data) {
          setUserSuggestions(response.data.suggestions);
        }
      } catch (err) {
        console.error("搜索用户失败:", err);
        setSearchError("搜索用户失败，请稍后重试");
      } finally {
        setSearchLoading(false);
      }
    };

    const debounceTimer = setTimeout(searchUsers, 300);
    return () => clearTimeout(debounceTimer);
  }, [userSearchInput, accessToken, selectedUser]);

  // 点击外部关闭建议框
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (!target.closest('.user-search-container')) {
        setShowSuggestions(false);
      }
    };

    if (showSuggestions) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [showSuggestions]);

  const fetchTasks = async () => {
    if (!accessToken) return;

    try {
      setLoading(true);
      setError(null);

      const response = await adminGetAllTasks(accessToken, {
        page,
        limit,
        userSearch: filters.userSearch || undefined,
        taskType: filters.taskType || undefined,
        status: filters.status || undefined,
        startDate: filters.startDate || undefined,
        endDate: filters.endDate || undefined,
      });

      if (response.success && response.data) {
        setTasks(response.data.tasks || []);
        setTotal(response.data.pagination.total);
        setTotalPages(response.data.pagination.totalPages);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "获取任务列表失败");
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key: string, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setPage(1); // 重置到第一页
  };

  const handleResetFilters = () => {
    setFilters({
      userSearch: "",
      taskType: "",
      status: "",
      startDate: "",
      endDate: "",
    });
    setSelectedUser(null);
    setUserSearchInput("");
    setUserSuggestions([]);
    setPage(1);
  };

  const handleSelectSuggestion = (suggestion: UserSuggestion) => {
    setSelectedUser(suggestion);
    setUserSearchInput("");
    setFilters((prev) => ({ ...prev, userSearch: suggestion.displayText }));
    setShowSuggestions(false);
    setUserSuggestions([]);
    setPage(1);
  };

  const handleClearUserSearch = () => {
    setSelectedUser(null);
    setUserSearchInput("");
    setFilters((prev) => ({ ...prev, userSearch: "" }));
    setUserSuggestions([]);
    setPage(1);
  };

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      completed: { label: "已完成", color: "bg-green-100 text-green-800" },
      processing: { label: "处理中", color: "bg-blue-100 text-blue-800" },
      queued: { label: "排队中", color: "bg-yellow-100 text-yellow-800" },
      failed: { label: "失败", color: "bg-red-100 text-red-800" },
    };
    const config = statusConfig[status as keyof typeof statusConfig] || {
      label: status,
      color: "bg-gray-100 text-gray-800",
    };
    return (
      <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${config.color}`}>
        {config.label}
      </span>
    );
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return "-";
    return formatDateTime(dateString, {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getPreviewImage = (task: AdminUserTask & { user?: { userId: string; email?: string; nickname?: string } }) => {
    const firstResultUrl = task.resultImage?.url?.split(',')[0]?.trim();
    const firstResultName = task.resultImage?.filename?.split(',')[0]?.trim();

    if (firstResultUrl) {
      return {
        url: resolveFileUrl(firstResultUrl),
        alt: firstResultName || `${task.typeName}结果图`,
      };
    }

    if (task.originalImage) {
      return {
        url: resolveFileUrl(task.originalImage.url),
        alt: task.originalImage.filename,
      };
    }

    return {
      url: '/placeholder.png',
      alt: '暂无图片',
    };
  };

  const convertToHistoryTask = (task: AdminUserTask & { user?: { userId: string; email?: string; nickname?: string } }): HistoryTask | null => {
    if (!task.originalImage) return null;

    return {
      taskId: task.taskId,
      type: task.type,
      typeName: task.typeName || task.type,
      status: task.status,
      originalImage: {
        url: task.originalImage.url,
        filename: task.originalImage.filename,
        size: task.originalImage.size,
        dimensions: task.originalImage.dimensions,
      },
      resultImage: task.resultImage ? {
        url: task.resultImage.url,
        filename: task.resultImage.filename,
        size: task.resultImage.size,
        dimensions: task.resultImage.dimensions,
      } : undefined,
      creditsUsed: task.creditsUsed,
      processingTime: 0,
      favorite: false,
      tags: [],
      createdAt: task.createdAt || new Date().toISOString(),
      completedAt: task.completedAt || undefined,
    };
  };

  const handleTaskClick = (task: AdminUserTask & { user?: { userId: string; email?: string; nickname?: string } }) => {
    const historyTask = convertToHistoryTask(task);
    if (historyTask) {
      setSelectedTask(historyTask);
    }
  };

  if (!isAuthenticated) {
    return null;
  }

  return (
    <AdminLayout>
      <div className="px-4 py-6 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">任务浏览器</h1>
          <p className="mt-1 text-sm text-gray-600">
            查看和筛选所有用户的历史任务记录
          </p>
        </div>

        {/* 筛选表单 */}
        <div className="mb-6 rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <div className="mb-4 flex items-center gap-2 text-sm font-medium text-gray-700">
            <Filter className="h-4 w-4" />
            筛选条件
          </div>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            <div className="user-search-container relative">
              <label className="mb-1 block text-sm font-medium text-gray-700">
                <User className="mb-1 inline h-4 w-4" /> 用户搜索
              </label>
              {selectedUser ? (
                <div className="mt-1 flex items-start gap-2 rounded-lg border border-blue-200 bg-blue-50 px-3 py-2">
                  <div className="flex-1">
                    <div className="font-semibold text-gray-900">
                      {selectedUser.nickname || selectedUser.email || selectedUser.phone || selectedUser.userId}
                    </div>
                    <div className="text-xs text-gray-700">
                      {selectedUser.email && <div>邮箱：{selectedUser.email}</div>}
                      {selectedUser.phone && <div>手机：{selectedUser.phone}</div>}
                      <div>ID：{selectedUser.userId}</div>
                    </div>
                  </div>
                  <button
                    onClick={handleClearUserSearch}
                    className="text-gray-500 hover:text-gray-700"
                    title="清除"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ) : (
                <div className="relative">
                  <input
                    type="text"
                    placeholder="输入用户名、邮箱或手机号"
                    value={userSearchInput}
                    onChange={(e) => {
                      setUserSearchInput(e.target.value);
                      setShowSuggestions(true);
                    }}
                    onFocus={() => setShowSuggestions(true)}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 pr-8 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                  {searchLoading && (
                    <div className="absolute right-3 top-1/2 -translate-y-1/2">
                      <div className="h-4 w-4 animate-spin rounded-full border-2 border-blue-600 border-r-transparent"></div>
                    </div>
                  )}
                  {showSuggestions && userSuggestions.length > 0 && (
                    <div className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md border border-gray-200 bg-white shadow-lg">
                      {userSuggestions.map((suggestion) => (
                        <button
                          key={suggestion.userId}
                          onClick={() => handleSelectSuggestion(suggestion)}
                          className="w-full px-3 py-2 text-left text-sm hover:bg-blue-50"
                        >
                          <div className="font-medium text-gray-900">{suggestion.displayText}</div>
                          <div className="text-xs text-gray-500">
                            {suggestion.email && <span>邮箱: {suggestion.email} · </span>}
                            {suggestion.phone && <span>手机: {suggestion.phone} · </span>}
                            <span>ID: {suggestion.userId}</span>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                  {searchError && (
                    <div className="mt-1 text-xs text-red-600">{searchError}</div>
                  )}
                </div>
              )}
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                <Layers className="mb-1 inline h-4 w-4" /> 任务类型
              </label>
              <select
                value={filters.taskType}
                onChange={(e) => handleFilterChange("taskType", e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value="">全部类型</option>
                <option value="remove_watermark">AI智能去水印</option>
                <option value="extract_pattern">AI提取花型</option>
                <option value="vectorize">AI矢量化(转SVG)</option>
                <option value="upscale">AI高清</option>
                <option value="seamless">AI四方连续转换</option>
                <option value="denoise">AI布纹去噪</option>
                <option value="embroidery">AI毛线刺绣增强</option>
                <option value="flat_to_3d">AI平面转3D</option>
                <option value="expand_image">AI扩图</option>
                <option value="seamless_loop">AI接循环</option>
                <option value="similar_image">AI相似图</option>
                <option value="prompt_edit">AI用嘴改图</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">状态</label>
              <select
                value={filters.status}
                onChange={(e) => handleFilterChange("status", e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value="">全部状态</option>
                <option value="completed">已完成</option>
                <option value="processing">处理中</option>
                <option value="queued">排队中</option>
                <option value="failed">失败</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                <Calendar className="mb-1 inline h-4 w-4" /> 开始日期
              </label>
              <input
                type="date"
                value={filters.startDate}
                onChange={(e) => handleFilterChange("startDate", e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                <Calendar className="mb-1 inline h-4 w-4" /> 结束日期
              </label>
              <input
                type="date"
                value={filters.endDate}
                onChange={(e) => handleFilterChange("endDate", e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
            <div className="flex items-end">
              <button
                onClick={handleResetFilters}
                className="w-full rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                重置筛选
              </button>
            </div>
          </div>
        </div>

        {/* 任务列表 */}
        {loading ? (
          <div className="rounded-lg border border-gray-200 bg-white p-8 text-center shadow-sm">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
            <p className="mt-4 text-sm text-gray-600">加载中...</p>
          </div>
        ) : error ? (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
            {error}
          </div>
        ) : (
          <>
            <div className="mb-4 text-sm text-gray-600">
              共找到 {total} 条任务记录
            </div>
            <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        预览
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        用户
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        类型
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        状态
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        积分
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        创建时间
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        完成时间
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 bg-white">
                    {tasks.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="px-6 py-8 text-center text-sm text-gray-500">
                          暂无任务记录
                        </td>
                      </tr>
                    ) : (
                      tasks.map((task) => {
                        const preview = getPreviewImage(task);
                        return (
                          <tr
                            key={task.taskId}
                            className="hover:bg-gray-50 cursor-pointer"
                            onClick={() => handleTaskClick(task)}
                          >
                            <td className="px-6 py-4">
                              <img
                                src={preview.url}
                                alt={preview.alt}
                                className="h-12 w-12 rounded border border-gray-200 object-cover"
                              />
                            </td>
                            <td className="px-6 py-4 text-sm text-gray-900">
                              <div className="flex flex-col">
                                <span className="font-medium">{task.user?.nickname || task.user?.email || "-"}</span>
                                <span className="text-xs text-gray-500">{task.user?.userId || "-"}</span>
                              </div>
                            </td>
                            <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900">
                              {task.typeName}
                            </td>
                            <td className="whitespace-nowrap px-6 py-4 text-sm">
                              <div className="flex items-center gap-2">
                                {getStatusBadge(task.status)}
                                {task.status === "failed" && task.errorMessage && (
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      setErrorDetailTask(task);
                                    }}
                                    className="text-red-500 hover:text-red-700"
                                    title="查看错误详情"
                                  >
                                    <AlertCircle className="h-4 w-4" />
                                  </button>
                                )}
                              </div>
                            </td>
                            <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900">
                              {task.creditsUsed.toFixed(2)}
                            </td>
                            <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                              {formatDate(task.createdAt || "")}
                            </td>
                            <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                              {formatDate(task.completedAt || "")}
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* 分页 */}
            {totalPages > 1 && (
              <div className="mt-4 flex items-center justify-between">
                <div className="text-sm text-gray-700">
                  第 {page} 页，共 {totalPages} 页
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="inline-flex items-center rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <ChevronLeft className="h-4 w-4" />
                    上一页
                  </button>
                  <button
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                    className="inline-flex items-center rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    下一页
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* 图片预览 */}
      {selectedTask && accessToken && (
        <ImagePreview
          task={selectedTask}
          onClose={() => setSelectedTask(null)}
          accessToken={accessToken}
        />
      )}

      {/* 错误详情模态框 */}
      {errorDetailTask && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="mx-4 w-full max-w-3xl rounded-lg bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
              <div className="flex items-center gap-2">
                <AlertCircle className="h-5 w-5 text-red-500" />
                <h3 className="text-lg font-semibold text-gray-900">任务错误详情</h3>
              </div>
              <button
                onClick={() => setErrorDetailTask(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="px-6 py-4">
              <div className="mb-4 space-y-2">
                <div className="flex items-center gap-2 text-sm">
                  <span className="font-medium text-gray-700">任务ID:</span>
                  <span className="text-gray-600">{errorDetailTask.taskId}</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <span className="font-medium text-gray-700">任务类型:</span>
                  <span className="text-gray-600">{errorDetailTask.typeName}</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <span className="font-medium text-gray-700">用户:</span>
                  <span className="text-gray-600">
                    {errorDetailTask.user?.nickname || errorDetailTask.user?.email || "-"}
                  </span>
                </div>
                {errorDetailTask.errorCode && (
                  <div className="flex items-center gap-2 text-sm">
                    <span className="font-medium text-gray-700">错误代码:</span>
                    <span className="rounded bg-red-100 px-2 py-1 font-mono text-xs text-red-800">
                      {errorDetailTask.errorCode}
                    </span>
                  </div>
                )}
              </div>
              <div>
                <div className="mb-2 font-medium text-gray-700">错误信息:</div>
                <div className="max-h-96 overflow-y-auto rounded border border-gray-200 bg-gray-50 p-4">
                  <pre className="whitespace-pre-wrap font-mono text-xs text-gray-800">
                    {errorDetailTask.errorMessage}
                  </pre>
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-2 border-t border-gray-200 px-6 py-4">
              <button
                onClick={() => setErrorDetailTask(null)}
                className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      )}
    </AdminLayout>
  );
}
