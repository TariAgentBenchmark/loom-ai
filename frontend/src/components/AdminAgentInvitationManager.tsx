"use client";

import React, { useCallback, useEffect, useState } from "react";
import { BadgeCheck, Ban, Link2, Plus, RefreshCcw, Users, X } from "lucide-react";
import { adminCreateAgent, adminGetAgents, adminUpdateAgent, type AdminAgent } from "../lib/api";
import { useAdminAccessToken } from "../contexts/AdminAuthContext";

type AsyncState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready" };

const statusBadge = (status: string) => {
  if (status === "active") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700 ring-1 ring-inset ring-emerald-100">
        <BadgeCheck className="h-3.5 w-3.5" />
        启用
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2.5 py-1 text-xs font-semibold text-gray-600 ring-1 ring-inset ring-gray-200">
      <Ban className="h-3.5 w-3.5" />
      停用
    </span>
  );
};

const AdminAgentInvitationManager: React.FC = () => {
  const accessToken = useAdminAccessToken();
  const [agents, setAgents] = useState<AdminAgent[]>([]);
  const [state, setState] = useState<AsyncState>({ status: "idle" });
  const [agentForm, setAgentForm] = useState({
    name: "",
    contact: "",
    notes: "",
  });
  const [showCreateModal, setShowCreateModal] = useState(false);

  const loadData = useCallback(async () => {
    if (!accessToken) return;
    setState({ status: "loading" });
    try {
      const agentRes = await adminGetAgents(accessToken);
      setAgents(agentRes.data.agents ?? []);
      setState({ status: "ready" });
    } catch (err) {
      setState({
        status: "error",
        message: (err as Error)?.message ?? "加载失败",
      });
    }
  }, [accessToken]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleCreateAgent = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!accessToken) return;
    if (!agentForm.name.trim()) {
      setState({ status: "error", message: "请填写代理商名称" });
      return;
    }
    setState({ status: "loading" });
    try {
      await adminCreateAgent(
        {
          name: agentForm.name.trim(),
          contact: agentForm.contact.trim() || undefined,
          notes: agentForm.notes.trim() || undefined,
        },
        accessToken,
      );
      setAgentForm({ name: "", contact: "", notes: "" });
      setShowCreateModal(false);
      await loadData();
    } catch (err) {
      setState({
        status: "error",
        message: (err as Error)?.message ?? "创建代理商失败",
      });
    }
  };

  const toggleAgentStatus = async (agent: AdminAgent) => {
    if (!accessToken) return;
    const nextStatus = agent.status === "active" ? "disabled" : "active";
    setState({ status: "loading" });
    try {
      await adminUpdateAgent(
        agent.id,
        { status: nextStatus },
        accessToken,
      );
      await loadData();
    } catch (err) {
      setState({
        status: "error",
        message: (err as Error)?.message ?? "更新代理商状态失败",
      });
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">渠道与邀请码管理</h2>
          <p className="text-sm text-gray-500">配置代理商渠道并查看来源用户（邀请码随渠道自动生成）。</p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700"
          >
            <Plus className="h-4 w-4" />
            新建代理商
          </button>
          <button
            type="button"
            onClick={loadData}
            className="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
          >
            <RefreshCcw className="h-4 w-4" />
            重新加载
          </button>
        </div>
      </div>

      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl">
            <div className="mb-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Users className="h-5 w-5 text-blue-600" />
                <h3 className="text-lg font-semibold text-gray-900">新建代理商</h3>
              </div>
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="text-gray-400 hover:text-gray-600"
                aria-label="close"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleCreateAgent} className="space-y-4">
              <div>
                <label className="text-xs text-gray-500">名称</label>
                <input
                  type="text"
                  value={agentForm.name}
                  onChange={(e) => setAgentForm({ ...agentForm, name: e.target.value })}
                  className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                  placeholder="渠道名称"
                  required
                />
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <label className="text-xs text-gray-500">联系人/电话</label>
                  <input
                    type="text"
                    value={agentForm.contact}
                    onChange={(e) => setAgentForm({ ...agentForm, contact: e.target.value })}
                    className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                    placeholder="选填"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500">备注</label>
                  <input
                    type="text"
                    value={agentForm.notes}
                    onChange={(e) => setAgentForm({ ...agentForm, notes: e.target.value })}
                    className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                    placeholder="选填"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="rounded-lg border border-gray-200 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  type="submit"
                  className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300"
                  disabled={state.status === "loading"}
                >
                  <Plus className="h-4 w-4" />
                  创建
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {state.status === "error" && (
        <div className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-800">
          <Ban className="mt-0.5 h-5 w-5" />
          <div>
            <p className="text-sm font-semibold">操作失败</p>
            <p className="text-sm">{state.message}</p>
          </div>
        </div>
      )}

      {/* 新建代理商改为弹窗，不在主界面占用空间 */}

      <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
        <div className="mb-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Link2 className="h-5 w-5 text-blue-600" />
            <h3 className="text-sm font-semibold text-gray-900">代理商列表</h3>
          </div>
          <span className="text-xs text-gray-500">总计 {agents.length} 个</span>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead>
              <tr className="bg-gray-50">
                <th className="px-3 py-2 text-left font-medium text-gray-600">名称</th>
                <th className="px-3 py-2 text-left font-medium text-gray-600">用户数</th>
                <th className="px-3 py-2 text-left font-medium text-gray-600">邀请码</th>
                <th className="px-3 py-2 text-left font-medium text-gray-600">联系人</th>
                <th className="px-3 py-2 text-left font-medium text-gray-600">状态</th>
                <th className="px-3 py-2 text-right font-medium text-gray-600">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {agents.map((agent) => (
                <tr key={agent.id}>
                  <td className="px-3 py-2">
                    <div className="font-semibold text-gray-900">{agent.name}</div>
                    <div className="text-xs text-gray-500">
                      创建于 {agent.createdAt?.slice(0, 19).replace("T", " ")}
                    </div>
                  </td>
                  <td className="px-3 py-2">
                    <span className="font-semibold text-gray-900">{agent.userCount}</span>
                  </td>
                  <td className="px-3 py-2">
                    <div className="font-semibold text-gray-900">{agent.invitationCode || "—"}</div>
                  </td>
                  <td className="px-3 py-2 text-gray-700">
                    {agent.contact || "-"}
                  </td>
                  <td className="px-3 py-2">{statusBadge(agent.status)}</td>
                  <td className="px-3 py-2 text-right">
                    <button
                      type="button"
                      onClick={() => toggleAgentStatus(agent)}
                      className="text-xs font-medium text-blue-600 hover:text-blue-800"
                      disabled={state.status === "loading"}
                    >
                      {agent.status === "active" ? "停用" : "启用"}
                    </button>
                  </td>
                </tr>
              ))}
              {agents.length === 0 && (
                <tr>
                  <td className="px-3 py-4 text-center text-sm text-gray-500" colSpan={6}>
                    暂无代理商，请先创建。
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 邀请码列表简化后移除，邀请码随代理商自动生成 */}
    </div>
  );
};

export default AdminAgentInvitationManager;
