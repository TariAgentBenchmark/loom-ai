"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Copy, Link2, ShieldCheck, UserPlus, Users, X, Calendar, RefreshCcw } from "lucide-react";
import {
  agentCreateChildAgent,
  agentGetLedger,
  agentGetManagedAgent,
  type ManagedAgentChild,
  type ManagedAgentResponse,
  type AgentLedgerItem,
} from "../../lib/api";
import { restoreSession } from "../../lib/auth";
import { getUserProfile } from "../../lib/api";
import { clearAuthTokens, setInitialAuthTokens } from "../../lib/tokenManager";

type AsyncState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready" }
  | { status: "submitting" };

const yuan = (cents?: number) => ((cents || 0) / 100).toFixed(2);

const AgentPage: React.FC = () => {
  const router = useRouter();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [agentInfo, setAgentInfo] = useState<ManagedAgentResponse | null>(null);
  const [state, setState] = useState<AsyncState>({ status: "idle" });
  const [ledgerState, setLedgerState] = useState<AsyncState>({ status: "idle" });
  const [childForm, setChildForm] = useState({
    name: "",
    userIdentifier: "",
    contact: "",
    notes: "",
  });
  const [inviteCopied, setInviteCopied] = useState(false);
  const [ledgerItems, setLedgerItems] = useState<AgentLedgerItem[]>([]);
  const [ledgerSummary, setLedgerSummary] = useState({
    totalAmount: 0,
    totalCommission: 0,
    totalOrders: 0,
    page: 1,
    pageSize: 20,
    totalPages: 1,
  });
  const [filters, setFilters] = useState<{ startDate?: string; endDate?: string }>({});

  const loadSession = useCallback(async () => {
    const restored = restoreSession();
    if (!restored) {
      router.push("/admin/login");
      return;
    }
    setInitialAuthTokens(
      { accessToken: restored.accessToken, refreshToken: restored.refreshToken },
      { rememberMe: restored.rememberMe },
    );
    setAccessToken(restored.accessToken);
  }, [router]);

  const loadAgent = useCallback(async () => {
    if (!accessToken) return;
    setState({ status: "loading" });
    try {
      const profile = await getUserProfile(accessToken);
      if (!profile.data?.managedAgentId) {
        setState({ status: "error", message: "当前账号未绑定代理商" });
        return;
      }
      const res = await agentGetManagedAgent(accessToken);
      setAgentInfo(res.data);
      setState({ status: "ready" });
    } catch (err) {
      setState({ status: "error", message: (err as Error)?.message ?? "加载失败" });
      if ((err as Error)?.message?.includes("401")) {
        clearAuthTokens();
      }
    }
  }, [accessToken]);

  const loadLedger = useCallback(
    async (page = 1) => {
      if (!accessToken) return;
      setLedgerState({ status: "loading" });
      try {
        const res = await agentGetLedger(accessToken, {
          startDate: filters.startDate,
          endDate: filters.endDate,
          page,
          pageSize: ledgerSummary.pageSize,
        });
        setLedgerItems(res.data.items || []);
        setLedgerSummary({
          totalAmount: res.data.totalAmount,
          totalCommission: res.data.totalCommission,
          totalOrders: res.data.totalOrders,
          page: res.data.page,
          pageSize: res.data.pageSize,
          totalPages: res.data.totalPages,
        });
        setLedgerState({ status: "ready" });
      } catch (err) {
        setLedgerState({ status: "error", message: (err as Error)?.message ?? "加载流水失败" });
      }
    },
    [accessToken, filters.startDate, filters.endDate, ledgerSummary.pageSize],
  );

  useEffect(() => {
    loadSession();
  }, [loadSession]);

  useEffect(() => {
    loadAgent();
  }, [loadAgent]);

  useEffect(() => {
    loadLedger();
  }, [loadLedger]);

  const handleCreateChild = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!agentInfo || !accessToken) return;
    if ((agentInfo.level ?? 1) >= 2) {
      setState({ status: "error", message: "仅一级代理可创建二级代理" });
      return;
    }
    if (!childForm.name.trim() || !childForm.userIdentifier.trim()) {
      setState({ status: "error", message: "请填写二级代理名称和绑定用户" });
      return;
    }
    setState({ status: "submitting" });
    try {
      const res = await agentCreateChildAgent(
        {
          name: childForm.name.trim(),
          userIdentifier: childForm.userIdentifier.trim(),
          contact: childForm.contact.trim() || undefined,
          notes: childForm.notes.trim() || undefined,
        },
        accessToken,
      );
      setAgentInfo((prev) =>
        prev ? { ...prev, children: [res.data as ManagedAgentChild, ...(prev.children || [])] } : prev,
      );
      setChildForm({ name: "", userIdentifier: "", contact: "", notes: "" });
      setState({ status: "ready" });
    } catch (err) {
      setState({ status: "error", message: (err as Error)?.message ?? "创建二级代理失败" });
    }
  };

  const commissionRuleText = useMemo(
    () => ({
      level1: "一级：下级用户充值 < 10000 抽成20%，>= 10000 抽成30%",
      level2: "二级：统一抽成6%",
    }),
    [],
  );

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-6xl px-4 py-6">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 text-sm text-blue-600">
              <ShieldCheck className="h-4 w-4" />
              <span>代理商管理 / 结算</span>
            </div>
            <h1 className="mt-1 text-2xl font-bold text-gray-900">代理中心</h1>
            <p className="text-sm text-gray-600">查看渠道信息、创建二级代理、查询佣金流水。</p>
          </div>
          <button
            type="button"
            onClick={() => router.push("/")}
            className="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
          >
            <X className="h-4 w-4" />
            返回首页
          </button>
        </div>

        <div className="mb-4 flex items-center justify-end">
          <button
            type="button"
            onClick={() => loadAgent()}
            className="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
          >
            <RefreshCcw className="h-4 w-4" />
            重新加载
          </button>
        </div>

        {state.status === "error" && (
          <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-amber-800 text-sm">
            {state.message}
          </div>
        )}

        {agentInfo && (
          <div className="mb-6 rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div className="space-y-1">
                <div className="text-sm text-gray-500">代理商</div>
                <div className="text-xl font-semibold text-gray-900">{agentInfo.name}</div>
                <div className="flex flex-wrap items-center gap-2 text-xs text-gray-600">
                  <span className="rounded-full bg-blue-100 px-2 py-1 font-semibold text-blue-700">
                    {agentInfo.level === 1 ? "一级代理" : "二级代理"}
                  </span>
                  <span className="rounded-full bg-gray-100 px-2 py-1 font-semibold text-gray-700">
                    {agentInfo.status === "active" ? "启用" : "停用"}
                  </span>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm text-gray-700 md:grid-cols-3">
                <div>
                  <div className="text-xs text-gray-500">绑定用户</div>
                  <div className="font-semibold text-gray-900">{agentInfo.ownerUserPhone || agentInfo.ownerUserId || "—"}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">联系方式</div>
                  <div className="font-semibold text-gray-900">{agentInfo.contact || "—"}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">创建时间</div>
                  <div className="font-semibold text-gray-900">
                    {agentInfo.createdAt?.slice(0, 16).replace("T", " ") || "—"}
                  </div>
                </div>
              </div>
            </div>
            <div className="mt-3 flex flex-wrap items-center gap-3 text-sm text-gray-700">
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500">邀请码</span>
                <span className="rounded bg-gray-100 px-2 py-1 font-semibold text-gray-900">
                  {agentInfo.invitationCode || "—"}
                </span>
                {agentInfo.invitationCode && (
                  <button
                    type="button"
                    onClick={async () => {
                      if (!agentInfo.invitationCode) return;
                      try {
                        await navigator.clipboard.writeText(agentInfo.invitationCode);
                        setInviteCopied(true);
                        setTimeout(() => setInviteCopied(false), 1500);
                      } catch {
                        setInviteCopied(false);
                      }
                    }}
                    className="inline-flex items-center gap-1 rounded bg-white px-2 py-1 text-xs font-medium text-blue-600 ring-1 ring-inset ring-blue-200 hover:bg-blue-50"
                  >
                    <Copy className="h-3.5 w-3.5" />
                    {inviteCopied ? "已复制" : "复制"}
                  </button>
                )}
              </div>
              <div className="text-xs text-gray-500">
                佣金规则：{agentInfo.level === 1 ? `${commissionRuleText.level1}；${commissionRuleText.level2}` : commissionRuleText.level2}
              </div>
            </div>
          </div>
        )}

        {agentInfo?.level === 1 && (
          <div className="mb-6 rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
            <div className="mb-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <UserPlus className="h-5 w-5 text-blue-600" />
                <div>
                  <div className="text-sm font-semibold text-gray-900">创建二级代理商</div>
                  <div className="text-xs text-gray-500">二级代理不可再发展下级</div>
                </div>
              </div>
            </div>
            <form onSubmit={handleCreateChild} className="grid gap-3 md:grid-cols-2">
              <div>
                <label className="text-xs text-gray-500">名称</label>
                <input
                  type="text"
                  value={childForm.name}
                  onChange={(e) => setChildForm({ ...childForm, name: e.target.value })}
                  className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                  placeholder="二级代理名称"
                  required
                />
              </div>
              <div>
                <label className="text-xs text-gray-500">绑定用户（手机号）</label>
                <input
                  type="text"
                  value={childForm.userIdentifier}
                  onChange={(e) => {
                    const value = e.target.value;
                    setChildForm({ ...childForm, userIdentifier: value });
                  }}
                  className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                  placeholder="请输入手机号"
                  required
                />
                <p className="mt-1 text-xs text-gray-500">请直接填写手机号，提交后校验是否存在。</p>
              </div>
              <div>
                <label className="text-xs text-gray-500">联系人/电话</label>
                <input
                  type="text"
                  value={childForm.contact}
                  onChange={(e) => setChildForm({ ...childForm, contact: e.target.value })}
                  className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                  placeholder="选填"
                />
              </div>
              <div>
                <label className="text-xs text-gray-500">备注</label>
                <input
                  type="text"
                  value={childForm.notes}
                  onChange={(e) => setChildForm({ ...childForm, notes: e.target.value })}
                  className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                  placeholder="选填"
                />
              </div>
              <div className="md:col-span-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setChildForm({ name: "", userIdentifier: "", contact: "", notes: "" });
                  }}
                  className="rounded-lg border border-gray-200 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  重置
                </button>
                <button
                  type="submit"
                  className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300"
                  disabled={state.status === "submitting"}
                >
                  <UserPlus className="h-4 w-4" />
                  创建二级代理
                </button>
              </div>
            </form>
          </div>
        )}

        {agentInfo?.level === 1 && (
          <div className="mb-6 rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
            <div className="mb-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Users className="h-5 w-5 text-blue-600" />
                <div className="text-sm font-semibold text-gray-900">下级代理</div>
              </div>
              <span className="text-xs text-gray-500">共 {agentInfo?.children?.length ?? 0} 个</span>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-3 py-2 text-left font-medium text-gray-600">名称</th>
                    <th className="px-3 py-2 text-left font-medium text-gray-600">绑定用户</th>
                    <th className="px-3 py-2 text-left font-medium text-gray-600">邀请码</th>
                    <th className="px-3 py-2 text-left font-medium text-gray-600">状态</th>
                    <th className="px-3 py-2 text-left font-medium text-gray-600">创建时间</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {agentInfo?.children?.map((child) => (
                    <tr key={child.id}>
                      <td className="px-3 py-2">
                        <div className="font-semibold text-gray-900">{child.name}</div>
                        <div className="text-xs text-gray-500">ID: {child.id}</div>
                      </td>
                      <td className="px-3 py-2 text-gray-700">
                        <div className="font-semibold text-gray-900">{child.ownerUserPhone || child.ownerUserId || "—"}</div>
                        <div className="text-xs text-gray-500">{child.ownerUserId ? `ID: ${child.ownerUserId}` : ""}</div>
                      </td>
                      <td className="px-3 py-2 text-gray-900">{child.invitationCode || "—"}</td>
                      <td className="px-3 py-2">
                        <span className="rounded-full bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-700 ring-1 ring-inset ring-emerald-100">
                          {child.status === "active" ? "启用" : "停用"}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-gray-600">
                        {child.createdAt?.slice(0, 19).replace("T", " ") || "—"}
                      </td>
                    </tr>
                  ))}
                  {(!agentInfo?.children || agentInfo.children.length === 0) && (
                    <tr>
                      <td className="px-3 py-4 text-center text-sm text-gray-500" colSpan={5}>
                        暂无二级代理
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
          <div className="mb-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Link2 className="h-5 w-5 text-blue-600" />
              <div>
                <div className="text-sm font-semibold text-gray-900">佣金流水</div>
                <div className="text-xs text-gray-500">
                  {agentInfo?.level === 1 ? `${commissionRuleText.level1}；${commissionRuleText.level2}` : commissionRuleText.level2}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <label className="flex items-center gap-1 text-xs text-gray-500">
                <Calendar className="h-4 w-4" />
                <input
                  type="date"
                  value={filters.startDate || ""}
                  onChange={(e) => setFilters((prev) => ({ ...prev, startDate: e.target.value || undefined }))}
                  className="rounded border border-gray-200 px-2 py-1 text-xs focus:border-blue-500 focus:outline-none"
                />
              </label>
              <span className="text-xs text-gray-400">至</span>
              <input
                type="date"
                value={filters.endDate || ""}
                onChange={(e) => setFilters((prev) => ({ ...prev, endDate: e.target.value || undefined }))}
                className="rounded border border-gray-200 px-2 py-1 text-xs focus:border-blue-500 focus:outline-none"
              />
              <button
                type="button"
                onClick={() => loadLedger(1)}
                className="inline-flex items-center gap-1 rounded border border-gray-200 bg-white px-2 py-1 text-xs text-gray-700 hover:bg-gray-50"
              >
                筛选
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <div className="rounded-lg border border-gray-100 bg-gray-50 p-3">
              <div className="text-xs text-gray-500">总充值</div>
              <div className="text-lg font-semibold text-gray-900 mt-1">¥{yuan(ledgerSummary.totalAmount)}</div>
            </div>
            <div className="rounded-lg border border-gray-100 bg-gray-50 p-3">
              <div className="text-xs text-gray-500">预计佣金</div>
              <div className="text-lg font-semibold text-emerald-600 mt-1">¥{yuan(ledgerSummary.totalCommission)}</div>
            </div>
            <div className="rounded-lg border border-gray-100 bg-gray-50 p-3">
              <div className="text-xs text-gray-500">订单数</div>
              <div className="text-lg font-semibold text-gray-900 mt-1">{ledgerSummary.totalOrders}</div>
            </div>
          </div>

          <div className="mt-3 overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left font-medium text-gray-600">订单号</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-600">用户</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-600">充值金额</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-600">佣金</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-600">比例</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-600">时间</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {ledgerItems.map((item) => (
                  <tr key={item.orderId}>
                    <td className="px-3 py-2 text-gray-900">{item.orderId}</td>
                    <td className="px-3 py-2 text-gray-700">
                      <div className="font-semibold text-gray-900">{item.userPhone || item.userId}</div>
                      <div className="text-xs text-gray-500">ID: {item.userId}</div>
                    </td>
                    <td className="px-3 py-2 text-gray-900">¥{yuan(item.amount)}</td>
                    <td className="px-3 py-2 text-emerald-600">¥{yuan(item.commission)}</td>
                    <td className="px-3 py-2 text-gray-700">{(item.rate * 100).toFixed(0)}%</td>
                    <td className="px-3 py-2 text-gray-600">{item.paidAt?.slice(0, 19).replace("T", " ") || "—"}</td>
                  </tr>
                ))}
                {ledgerItems.length === 0 && (
                  <tr>
                    <td className="px-3 py-4 text-center text-sm text-gray-500" colSpan={6}>
                      暂无数据
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          <div className="mt-3 flex items-center justify-between text-xs text-gray-600">
            <div>
              第 {ledgerSummary.page} / {ledgerSummary.totalPages} 页
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                disabled={ledgerSummary.page <= 1}
                onClick={() => loadLedger(Math.max(1, ledgerSummary.page - 1))}
                className="rounded border border-gray-200 px-2 py-1 disabled:opacity-50"
              >
                上一页
              </button>
              <button
                type="button"
                disabled={ledgerSummary.page >= ledgerSummary.totalPages}
                onClick={() => loadLedger(Math.min(ledgerSummary.totalPages, ledgerSummary.page + 1))}
                className="rounded border border-gray-200 px-2 py-1 disabled:opacity-50"
              >
                下一页
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentPage;
