"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import { BadgeCheck, Ban, Link2, Plus, RefreshCcw, Users, X } from "lucide-react";
import {
  adminCreateAgent,
  adminGetAgents,
  adminUpdateAgent,
  adminDeleteAgent,
  adminSearchUsers,
  adminSettleAgentCommissions,
  adminGetAgentCommissions,
  adminSettleAgentOrder,
  adminRotateAgentReferralLink,
  type AdminAgent,
  type AdminUserLookupItem,
  type AdminCommissionItem,
} from "../lib/api";
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
  const [settlingId, setSettlingId] = useState<number | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<AdminAgent | null>(null);
  const [commissionItems, setCommissionItems] = useState<AdminCommissionItem[]>([]);
  const [commissionLoading, setCommissionLoading] = useState(false);
  const [commissionError, setCommissionError] = useState<string | null>(null);
  const [settlingOrderId, setSettlingOrderId] = useState<string | null>(null);
  const [commissionPage, setCommissionPage] = useState(1);
  const COMMISSION_PAGE_SIZE = 10;
  const [copiedAgentId, setCopiedAgentId] = useState<number | null>(null);
  const [rotatingLinkId, setRotatingLinkId] = useState<number | null>(null);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingAgent, setEditingAgent] = useState<AdminAgent | null>(null);
  const [commissionModeDraft, setCommissionModeDraft] = useState<string>("TIERED");
  const [agentForm, setAgentForm] = useState({
    name: "",
    userIdentifier: "",
    contact: "",
    notes: "",
    commissionMode: "TIERED",
  });
  const [selectedUser, setSelectedUser] = useState<AdminUserLookupItem | null>(null);
  const [userOptions, setUserOptions] = useState<AdminUserLookupItem[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const searchTimer = useRef<NodeJS.Timeout | null>(null);
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

  const handleSettleAgent = useCallback(
    async (agent: AdminAgent) => {
      if (!accessToken) return;
      setSelectedAgent(agent);
      setCommissionError(null);
      setCommissionLoading(true);
      setCommissionPage(1);
      try {
        const res = await adminGetAgentCommissions(agent.id, accessToken);
        setCommissionItems(res.data.items || []);
      } catch (err) {
        setCommissionError((err as Error)?.message ?? "加载失败");
      }
      setCommissionLoading(false);
    },
    [accessToken],
  );

  const reloadCommissions = useCallback(
    async (agentId: number) => {
      if (!accessToken) return;
      setCommissionLoading(true);
      setCommissionPage(1);
      try {
        const res = await adminGetAgentCommissions(agentId, accessToken);
        setCommissionItems(res.data.items || []);
      } catch (err) {
        setCommissionError((err as Error)?.message ?? "加载失败");
      }
      setCommissionLoading(false);
    },
    [accessToken],
  );

  const handleSettleOrder = useCallback(
    async (orderId: string) => {
      if (!accessToken || !selectedAgent) return;
      setSettlingOrderId(orderId);
      try {
        await adminSettleAgentOrder(selectedAgent.id, orderId, {}, accessToken);
        await reloadCommissions(selectedAgent.id);
      } catch (err) {
        setCommissionError((err as Error)?.message ?? "结算失败");
      }
      setSettlingOrderId(null);
    },
    [accessToken, reloadCommissions, selectedAgent],
  );

  const handleSettleAll = useCallback(
    async () => {
      if (!accessToken || !selectedAgent) return;
      setSettlingId(selectedAgent.id);
      try {
        await adminSettleAgentCommissions(selectedAgent.id, {}, accessToken);
        await reloadCommissions(selectedAgent.id);
        await loadData();
      } catch (err) {
        setCommissionError((err as Error)?.message ?? "批量结算失败");
      }
      setSettlingId(null);
    },
    [accessToken, loadData, reloadCommissions, selectedAgent],
  );

  const searchUsers = useCallback(
    (keyword: string) => {
      if (!accessToken) return;
      if (searchTimer.current) {
        clearTimeout(searchTimer.current);
      }
      if (!keyword.trim()) {
        setUserOptions([]);
        setSearchError(null);
        setSelectedUser(null);
        return;
      }
      setIsSearching(true);
      setSearchError(null);
      searchTimer.current = setTimeout(async () => {
        try {
          const res = await adminSearchUsers(keyword.trim(), accessToken, 10);
          setUserOptions(res.data.users || []);
        } catch (err) {
          setUserOptions([]);
          setSearchError((err as Error)?.message ?? "搜索失败");
        } finally {
          setIsSearching(false);
        }
      }, 250);
    },
    [accessToken],
  );

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
    if (!agentForm.userIdentifier.trim()) {
      setState({ status: "error", message: "请填写绑定的用户标识" });
      return;
    }
    setState({ status: "loading" });
    try {
      await adminCreateAgent(
        {
          name: agentForm.name.trim(),
          userIdentifier: agentForm.userIdentifier.trim(),
          contact: agentForm.contact.trim() || undefined,
          notes: agentForm.notes.trim() || undefined,
          commissionMode: agentForm.commissionMode,
        },
        accessToken,
      );
      setAgentForm({
        name: "",
        userIdentifier: "",
        contact: "",
        notes: "",
        commissionMode: "TIERED",
      });
      setSelectedUser(null);
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

  const handleDeleteAgent = async (agent: AdminAgent) => {
    if (!accessToken) return;
    if (agent.status !== "disabled") {
      setState({ status: "error", message: "请先停用后再删除" });
      return;
    }
    setState({ status: "loading" });
    try {
      await adminDeleteAgent(agent.id, accessToken);
      await loadData();
    } catch (err) {
      setState({
        status: "error",
        message: (err as Error)?.message ?? "删除代理商失败",
      });
    }
  };

  const buildReferralUrl = (token?: string | null) => {
    if (!token) return "";
    const origin = typeof window !== "undefined" ? window.location.origin : "";
    return origin ? `${origin}/?ref=${token}` : "";
  };

  const handleCopyReferralLink = async (agent: AdminAgent) => {
    if (agent.referralLinkStatus && agent.referralLinkStatus !== "active") {
      setState({ status: "error", message: "注册链接已停用，无法复制" });
      return;
    }
    const url = buildReferralUrl(agent.referralLinkToken);
    if (!url) {
      setState({ status: "error", message: "暂无可复制的注册链接" });
      return;
    }
    try {
      await navigator.clipboard.writeText(url);
      setCopiedAgentId(agent.id);
      setTimeout(() => setCopiedAgentId(null), 1500);
    } catch (err) {
      setState({ status: "error", message: "复制失败，请手动复制" });
    }
  };

  const handleRotateReferralLink = async (agent: AdminAgent) => {
    if (!accessToken) return;
    const confirmed = window.confirm(
      `确认重置「${agent.name}」的注册链接？旧链接将失效，新链接生成后需要重新分发。`,
    );
    if (!confirmed) return;
    setRotatingLinkId(agent.id);
    try {
      await adminRotateAgentReferralLink(agent.id, accessToken);
      await loadData();
    } catch (err) {
      setState({
        status: "error",
        message: (err as Error)?.message ?? "重置注册链接失败",
      });
    } finally {
      setRotatingLinkId(null);
    }
  };

  const openEditModal = (agent: AdminAgent) => {
    setEditingAgent(agent);
    setCommissionModeDraft(agent.commissionMode || "TIERED");
    setShowEditModal(true);
  };

  const handleUpdateCommissionMode = async () => {
    if (!accessToken || !editingAgent) return;
    if (!commissionModeDraft) {
      setState({ status: "error", message: "请选择佣金模式" });
      return;
    }
    const readable =
      commissionModeDraft === "FIXED_30" ? "固定30%" : "阶梯20/25%";
    const confirmed = window.confirm(
      `确认将「${editingAgent.name}」的佣金模式调整为：${readable}？\n已结算订单金额不会变，未结算将按新模式计算。`,
    );
    if (!confirmed) return;

    setState({ status: "loading" });
    try {
      await adminUpdateAgent(
        editingAgent.id,
        { commissionMode: commissionModeDraft },
        accessToken,
      );
      await loadData();
      setShowEditModal(false);
      setEditingAgent(null);
    } catch (err) {
      setState({
        status: "error",
        message: (err as Error)?.message ?? "更新佣金模式失败",
      });
    } finally {
      setState({ status: "ready" });
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
                  <label className="text-xs text-gray-500">绑定用户（已注册）</label>
                  {selectedUser ? (
                    <div className="mt-1 flex items-start gap-2 rounded-lg border border-blue-200 bg-blue-50 px-3 py-2 text-sm text-gray-900 shadow-sm">
                      <div className="flex-1">
                        <div className="font-semibold">
                          {selectedUser.nickname || selectedUser.phone || selectedUser.email || selectedUser.userId}
                        </div>
                        <div className="text-xs text-gray-700">手机：{selectedUser.phone || "—"}</div>
                        <div className="text-[11px] text-gray-600">ID: {selectedUser.userId}</div>
                      </div>
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedUser(null);
                          setAgentForm({ ...agentForm, userIdentifier: "" });
                          setUserOptions([]);
                          setSearchError(null);
                        }}
                        className="mt-0.5 text-gray-400 hover:text-gray-600"
                        aria-label="clear-user"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  ) : (
                    <div className="relative">
                      <input
                        type="text"
                        value={agentForm.userIdentifier}
                        onChange={(e) => {
                          const value = e.target.value;
                          setAgentForm({ ...agentForm, userIdentifier: value });
                          searchUsers(value);
                        }}
                        className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                        placeholder="用户ID / 手机号 / 邮箱"
                        required
                      />
                      {agentForm.userIdentifier && (
                        <div className="absolute z-10 mt-1 w-full rounded-lg border border-gray-200 bg-white shadow-lg">
                          <div className="max-h-56 overflow-y-auto text-sm">
                            {isSearching && (
                              <div className="px-3 py-2 text-gray-500">搜索中…</div>
                            )}
                            {!isSearching && userOptions.length === 0 && !searchError && (
                              <div className="px-3 py-2 text-gray-400">未找到匹配用户</div>
                            )}
                            {searchError && !isSearching && (
                              <div className="px-3 py-2 text-red-500">搜索失败：{searchError}</div>
                            )}
                            {userOptions.map((user) => (
                              <button
                              key={user.userId}
                              type="button"
                              onClick={() => {
                                setAgentForm({ ...agentForm, userIdentifier: user.userId });
                                setSelectedUser(user);
                                if (!agentForm.contact && user.phone) {
                                  setAgentForm((prev) => ({ ...prev, contact: user.phone || "" }));
                                }
                                setUserOptions([]);
                              }}
                                className="flex w-full flex-col items-start px-3 py-2 text-left hover:bg-blue-50"
                              >
                                <span className="font-semibold text-gray-900">{user.nickname || user.phone || user.email || user.userId}</span>
                                <span className="text-xs text-gray-600">
                                  {user.phone ? `手机：${user.phone}` : user.email ? `邮箱：${user.email}` : "ID 匹配"}
                                </span>
                                <span className="text-[11px] text-gray-400">ID: {user.userId}</span>
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
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
                <div className="sm:col-span-2">
                  <label className="text-xs text-gray-500">佣金模式</label>
                  <select
                    value={agentForm.commissionMode}
                    onChange={(e) => setAgentForm({ ...agentForm, commissionMode: e.target.value })}
                    className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                  >
                    <option value="TIERED">阶梯：3万以内20%，超出25%</option>
                    <option value="FIXED_30">固定30%</option>
                  </select>
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
                <th className="px-3 py-2 text-left font-medium text-gray-600">绑定用户</th>
                <th className="px-3 py-2 text-left font-medium text-gray-600">用户数</th>
                <th className="px-3 py-2 text-left font-medium text-gray-600">邀请码</th>
                <th className="px-3 py-2 text-left font-medium text-gray-600">注册链接</th>
                <th className="px-3 py-2 text-left font-medium text-gray-600">佣金模式</th>
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
                  <td className="px-3 py-2 text-gray-700">
                    <div className="font-semibold text-gray-900">{agent.ownerUserPhone || agent.ownerUserId || "—"}</div>
                    <div className="text-xs text-gray-500">{agent.ownerUserId ? `ID: ${agent.ownerUserId}` : ""}</div>
                  </td>
                  <td className="px-3 py-2">
                    <span className="font-semibold text-gray-900">{agent.userCount}</span>
                  </td>
                  <td className="px-3 py-2">
                    <div className="font-semibold text-gray-900">{agent.invitationCode || "—"}</div>
                  </td>
                  <td className="px-3 py-2">
                    <div className="flex flex-col gap-1">
                      <span className="font-semibold text-gray-900">{agent.referralLinkToken || "—"}</span>
                      <div className="flex items-center gap-2 text-xs text-gray-500">
                        <button
                          type="button"
                          onClick={() => handleCopyReferralLink(agent)}
                          className="text-blue-600 hover:text-blue-800"
                          disabled={
                            !agent.referralLinkToken ||
                            (agent.referralLinkStatus && agent.referralLinkStatus !== "active")
                          }
                        >
                          {copiedAgentId === agent.id ? "已复制" : "复制链接"}
                        </button>
                        {agent.referralLinkStatus && agent.referralLinkStatus !== "active" && (
                          <span className="text-amber-600">已停用</span>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-3 py-2 text-gray-700">
                    {agent.commissionMode === "FIXED_30" ? "固定30%" : "阶梯20/25%"}
                  </td>
                  <td className="px-3 py-2 text-gray-700">
                    {agent.contact || "-"}
                  </td>
                  <td className="px-3 py-2">{statusBadge(agent.status)}</td>
                  <td className="px-3 py-2 text-right">
                    <div className="flex justify-end gap-3">
                      <button
                        type="button"
                        onClick={() => handleSettleAgent(agent)}
                        className="text-xs font-medium text-indigo-600 hover:text-indigo-800 disabled:opacity-50"
                        disabled={settlingId === agent.id || state.status === "loading"}
                      >
                        {settlingId === agent.id ? "结算中..." : "结算"}
                      </button>
                      <button
                        type="button"
                        onClick={() => toggleAgentStatus(agent)}
                        className="text-xs font-medium text-blue-600 hover:text-blue-800"
                        disabled={state.status === "loading"}
                      >
                        {agent.status === "active" ? "停用" : "启用"}
                      </button>
                      <button
                        type="button"
                        onClick={() => openEditModal(agent)}
                        className="text-xs font-medium text-gray-700 hover:text-gray-900"
                        disabled={state.status === "loading"}
                      >
                        编辑
                      </button>
                      {agent.status === "disabled" && (
                        <button
                          type="button"
                          onClick={() => handleDeleteAgent(agent)}
                          className="text-xs font-medium text-red-600 hover:text-red-800"
                          disabled={state.status === "loading"}
                        >
                          删除
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
              {agents.length === 0 && (
                <tr>
                  <td className="px-3 py-4 text-center text-sm text-gray-500" colSpan={9}>
                    暂无代理商，请先创建。
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {selectedAgent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 px-4">
          <div className="w-full max-w-5xl rounded-2xl bg-white p-5 shadow-xl">
            <div className="flex items-start justify-between">
              <div>
                <div className="text-sm text-gray-500">代理商</div>
                <div className="text-lg font-semibold text-gray-900">{selectedAgent.name}</div>
              </div>
              <button
                type="button"
                onClick={() => {
                  setSelectedAgent(null);
                  setCommissionItems([]);
                  setCommissionError(null);
                }}
                className="rounded-full p-2 text-gray-500 hover:bg-gray-100"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="mt-3 flex items-center justify-between">
              <div className="text-sm text-gray-600">查看并手动结算订单佣金（单笔或批量）。</div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => reloadCommissions(selectedAgent.id)}
                  className="rounded border border-gray-200 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
                  disabled={commissionLoading}
                >
                  重新加载
                </button>
                <button
                  type="button"
                  onClick={handleSettleAll}
                  className="rounded bg-indigo-600 px-3 py-1.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:opacity-50"
                  disabled={commissionLoading || settlingId === selectedAgent.id}
                >
                  {settlingId === selectedAgent.id ? "批量结算中..." : "全部结算"}
                </button>
              </div>
            </div>

            {commissionError && (
              <div className="mt-3 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                {commissionError}
              </div>
            )}

            <div className="mt-4 overflow-auto rounded-lg border border-gray-200">
              <table className="min-w-full divide-y divide-gray-200 text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-3 py-2 text-left font-medium text-gray-600">订单号</th>
                    <th className="px-3 py-2 text-left font-medium text-gray-600">用户</th>
                    <th className="px-3 py-2 text-left font-medium text-gray-600">充值金额</th>
                    <th className="px-3 py-2 text-left font-medium text-gray-600">佣金</th>
                    <th className="px-3 py-2 text-left font-medium text-gray-600">比例</th>
                    <th className="px-3 py-2 text-left font-medium text-gray-600">状态</th>
                    <th className="px-3 py-2 text-left font-medium text-gray-600">支付时间</th>
                    <th className="px-3 py-2 text-right font-medium text-gray-600">操作</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {commissionLoading && (
                    <tr>
                      <td colSpan={8} className="px-3 py-4 text-center text-sm text-gray-500">
                        加载中...
                      </td>
                    </tr>
                  )}
                  {!commissionLoading && commissionItems.length === 0 && (
                    <tr>
                      <td colSpan={8} className="px-3 py-4 text-center text-sm text-gray-500">
                        暂无订单
                      </td>
                    </tr>
                  )}
                  {!commissionLoading &&
                    commissionItems
                      .slice(
                        (commissionPage - 1) * COMMISSION_PAGE_SIZE,
                        commissionPage * COMMISSION_PAGE_SIZE,
                      )
                      .map((item) => (
                      <tr key={item.orderId}>
                        <td className="px-3 py-2 text-gray-900">{item.orderId}</td>
                        <td className="px-3 py-2 text-gray-700">
                          <div className="font-semibold text-gray-900">{item.userPhone || item.userId || "-"}</div>
                          {item.userId && <div className="text-xs text-gray-500">ID: {item.userId}</div>}
                        </td>
                        <td className="px-3 py-2 text-gray-900">¥{((item.amount || 0) / 100).toFixed(2)}</td>
                        <td className="px-3 py-2 text-emerald-600">¥{((item.commission || 0) / 100).toFixed(2)}</td>
                        <td className="px-3 py-2 text-gray-700">{(item.rate * 100).toFixed(0)}%</td>
                        <td className="px-3 py-2">
                          <span
                            className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${
                              item.status === "settled"
                                ? "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-100"
                                : "bg-amber-50 text-amber-700 ring-1 ring-amber-100"
                            }`}
                          >
                            {item.status === "settled" ? "已结算" : "未结算"}
                          </span>
                        </td>
                        <td className="px-3 py-2 text-gray-600">{item.paidAt?.slice(0, 19).replace("T", " ") || "-"}</td>
                        <td className="px-3 py-2 text-right">
                          {item.status === "settled" ? (
                            <span className="text-xs text-gray-500">已结算</span>
                          ) : (
                            <button
                              type="button"
                              onClick={() => handleSettleOrder(item.orderId)}
                              className="text-xs font-medium text-indigo-600 hover:text-indigo-800 disabled:opacity-50"
                              disabled={settlingOrderId === item.orderId}
                            >
                              {settlingOrderId === item.orderId ? "结算中..." : "结算"}
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
            {!commissionLoading && commissionItems.length > 0 && (
              <div className="mt-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between text-sm text-gray-600">
                <span>
                  共 {commissionItems.length} 条，当前第 {commissionPage} /
                  {Math.max(1, Math.ceil(commissionItems.length / COMMISSION_PAGE_SIZE))} 页
                </span>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setCommissionPage((prev) => Math.max(1, prev - 1))}
                    className="rounded border border-gray-200 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                    disabled={commissionPage === 1}
                  >
                    上一页
                  </button>
                  <button
                    type="button"
                    onClick={() =>
                      setCommissionPage((prev) =>
                        Math.min(
                          Math.max(1, Math.ceil(commissionItems.length / COMMISSION_PAGE_SIZE)),
                          prev + 1,
                        )
                      )
                    }
                    className="rounded border border-gray-200 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                    disabled={
                      commissionPage >= Math.max(1, Math.ceil(commissionItems.length / COMMISSION_PAGE_SIZE))
                    }
                  >
                    下一页
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 邀请码列表简化后移除，邀请码随代理商自动生成 */}

      {showEditModal && editingAgent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">编辑代理</h3>
              <button
                type="button"
                onClick={() => {
                  setShowEditModal(false);
                  setEditingAgent(null);
                }}
                className="text-gray-400 hover:text-gray-600"
                aria-label="close"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <div className="text-sm text-gray-500">名称</div>
                <div className="font-semibold text-gray-900">{editingAgent.name}</div>
              </div>
              <div>
                <label className="text-xs text-gray-500">佣金模式</label>
                <select
                  value={commissionModeDraft}
                  onChange={(e) => setCommissionModeDraft(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                >
                  <option value="TIERED">阶梯：3万以内20%，超出25%</option>
                  <option value="FIXED_30">固定30%</option>
                </select>
                <p className="mt-1 text-xs text-gray-500">
                  已结算订单金额保持不变，未结算订单会按新模式计算。
                </p>
              </div>
              <div>
                <label className="text-xs text-gray-500">注册链接</label>
                <div className="mt-1 flex items-center gap-3">
                  <div className="text-sm text-gray-800 font-mono break-all">
                    {editingAgent.referralLinkToken || "—"}
                  </div>
                  <button
                    type="button"
                    onClick={() => handleRotateReferralLink(editingAgent)}
                    className="text-xs font-medium text-emerald-600 hover:text-emerald-800 disabled:opacity-50"
                    disabled={rotatingLinkId === editingAgent.id || state.status === "loading"}
                  >
                    {rotatingLinkId === editingAgent.id ? "重置中..." : "重置链接"}
                  </button>
                </div>
                <p className="mt-1 text-xs text-gray-500">
                  重置后旧链接立即失效，请重新分发新链接。
                </p>
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => {
                  setShowEditModal(false);
                  setEditingAgent(null);
                }}
                className="rounded-lg border border-gray-200 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                取消
              </button>
              <button
                type="button"
                onClick={handleUpdateCommissionMode}
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 disabled:opacity-50"
                disabled={state.status === "loading"}
              >
                保存
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminAgentInvitationManager;
