"use client";

import React, { useCallback, useEffect, useState } from "react";
import { Plus, RefreshCw, Loader2, CheckCircle2, AlertTriangle, Bell, Trash2 } from "lucide-react";
import {
  adminGetNotifications,
  adminCreateNotification,
  adminUpdateNotification,
  adminUpdateNotificationStatus,
  adminDeleteNotification,
  AdminNotification,
} from "../lib/api";
import { useAdminAccessToken } from "../contexts/AdminAuthContext";
import { formatDateTime } from "../lib/datetime";

interface EditFormState {
  title: string;
  content: string;
  type: string;
}

const defaultFormState: EditFormState = {
  title: "",
  content: "",
  type: "system",
};

const AdminNotifications: React.FC = () => {
  const accessToken = useAdminAccessToken();
  const [notifications, setNotifications] = useState<AdminNotification[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [editingNotification, setEditingNotification] = useState<AdminNotification | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [formState, setFormState] = useState<EditFormState>(defaultFormState);
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchNotifications = useCallback(async () => {
    if (!accessToken) {
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      const response = await adminGetNotifications(accessToken, { include_inactive: true });
      setNotifications(response.data.notifications);
    } catch (err) {
      setError(err instanceof Error ? err.message : "获取通知列表失败");
    } finally {
      setIsLoading(false);
    }
  }, [accessToken]);

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  const openCreateModal = () => {
    setIsCreating(true);
    setEditingNotification(null);
    setFormState(defaultFormState);
    setFormError(null);
  };

  const openEditModal = (notification: AdminNotification) => {
    setIsCreating(false);
    setEditingNotification(notification);
    setFormState({
      title: notification.title,
      content: notification.content,
      type: notification.type,
    });
    setFormError(null);
  };

  const closeModal = () => {
    setIsCreating(false);
    setEditingNotification(null);
    setFormState(defaultFormState);
    setFormError(null);
    setIsSubmitting(false);
  };

  const updateFormState = (updates: Partial<EditFormState>) => {
    setFormState((prev) => ({
      ...prev,
      ...updates,
    }));
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!accessToken) {
      return;
    }

    const trimmedTitle = formState.title.trim();
    if (!trimmedTitle) {
      setFormError("标题不能为空");
      return;
    }

    const trimmedContent = formState.content.trim();
    if (!trimmedContent) {
      setFormError("内容不能为空");
      return;
    }

    setIsSubmitting(true);
    setFormError(null);
    setError(null);
    setSuccessMessage(null);

    try {
      if (isCreating) {
        await adminCreateNotification(
          {
            title: trimmedTitle,
            content: trimmedContent,
            type: formState.type,
          },
          accessToken
        );
        setSuccessMessage("通知创建成功");
      } else if (editingNotification) {
        await adminUpdateNotification(
          editingNotification.notificationId,
          {
            title: trimmedTitle,
            content: trimmedContent,
            type: formState.type,
          },
          accessToken
        );
        setSuccessMessage("通知更新成功");
      }
      closeModal();
      fetchNotifications();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : isCreating ? "创建通知失败" : "更新通知失败");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleToggleStatus = async (notification: AdminNotification) => {
    if (!accessToken) {
      return;
    }

    try {
      await adminUpdateNotificationStatus(notification.notificationId, !notification.active, accessToken);
      setSuccessMessage("通知状态已更新");
      fetchNotifications();
    } catch (err) {
      setError(err instanceof Error ? err.message : "更新通知状态失败");
    }
  };

  const handleDelete = async (notification: AdminNotification) => {
    if (!accessToken) {
      return;
    }

    if (!confirm("确定要删除这条通知吗？此操作不可撤销。")) {
      return;
    }

    try {
      await adminDeleteNotification(notification.notificationId, accessToken);
      setSuccessMessage("通知已删除");
      fetchNotifications();
    } catch (err) {
      setError(err instanceof Error ? err.message : "删除通知失败");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">系统通知管理</h1>
          <p className="mt-1 text-sm text-gray-600">
            创建、编辑和管理系统通知，所有用户都能在首页铃铛图标处查看。
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchNotifications}
            disabled={isLoading}
            className="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-700 shadow-sm transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                刷新中...
              </>
            ) : (
              <>
                <RefreshCw className="h-4 w-4" />
                刷新
              </>
            )}
          </button>
          <button
            onClick={openCreateModal}
            className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-blue-700"
          >
            <Plus className="h-4 w-4" />
            新建通知
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 flex items-start gap-2">
          <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {successMessage && (
        <div className="flex items-start gap-2 rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
          <CheckCircle2 className="h-4 w-4 mt-0.5 flex-shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}

      <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500">
                通知标题
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500">
                内容
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500">
                状态
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500">
                创建时间
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500">
                更新时间
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wide text-gray-500">
                操作
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {notifications.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-sm text-gray-500">
                  暂无通知
                </td>
              </tr>
            ) : (
              notifications.map((notification) => (
                <tr key={notification.notificationId} className="hover:bg-gray-50">
                  <td className="px-4 py-4">
                    <div className="flex items-center gap-2">
                      <Bell className="h-4 w-4 text-blue-500" />
                      <span className="font-medium text-gray-900">{notification.title}</span>
                    </div>
                  </td>
                  <td className="px-4 py-4">
                    <p className="max-w-xs truncate text-sm text-gray-600">{notification.content}</p>
                  </td>
                  <td className="px-4 py-4">
                    <span
                      className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${
                        notification.active
                          ? "bg-green-100 text-green-800"
                          : "bg-gray-100 text-gray-800"
                      }`}
                    >
                      {notification.active ? "启用" : "禁用"}
                    </span>
                  </td>
                  <td className="px-4 py-4 text-sm text-gray-600">
                    {formatDateTime(notification.createdAt)}
                  </td>
                  <td className="px-4 py-4 text-sm text-gray-600">
                    {formatDateTime(notification.updatedAt)}
                  </td>
                  <td className="px-4 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => openEditModal(notification)}
                        className="text-sm text-blue-600 hover:text-blue-700"
                      >
                        编辑
                      </button>
                      <button
                        onClick={() => handleToggleStatus(notification)}
                        className="text-sm text-gray-600 hover:text-gray-700"
                      >
                        {notification.active ? "禁用" : "启用"}
                      </button>
                      <button
                        onClick={() => handleDelete(notification)}
                        className="text-sm text-red-600 hover:text-red-700"
                      >
                        删除
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {(isCreating || editingNotification) && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-lg">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900">
                {isCreating ? "新建通知" : "编辑通知"}
              </h2>
              <button
                onClick={closeModal}
                className="rounded-full p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
              >
                <Trash2 className="h-5 w-5" />
              </button>
            </div>

            {formError && (
              <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {formError}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="title" className="block text-sm font-medium text-gray-700">
                  标题
                </label>
                <input
                  type="text"
                  id="title"
                  value={formState.title}
                  onChange={(e) => updateFormState({ title: e.target.value })}
                  placeholder="请输入通知标题"
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  maxLength={200}
                />
              </div>

              <div>
                <label htmlFor="content" className="block text-sm font-medium text-gray-700">
                  内容
                </label>
                <textarea
                  id="content"
                  value={formState.content}
                  onChange={(e) => updateFormState({ content: e.target.value })}
                  placeholder="请输入通知内容"
                  rows={4}
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={closeModal}
                  disabled={isSubmitting}
                  className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  取消
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="inline-block h-4 w-4 animate-spin" />
                      提交中...
                    </>
                  ) : (
                    isCreating ? "创建" : "更新"
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminNotifications;
