"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Copy, Link2, ShieldCheck, X, Calendar, RefreshCcw } from "lucide-react";
import { agentGetLedger, agentGetManagedAgent, type ManagedAgentResponse, type AgentLedgerItem } from "../../lib/api";
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
const buildInviteUrl = (code?: string | null) => {
  if (!code) return "";
  const origin = typeof window !== "undefined" ? window.location.origin : "";
  return origin ? `${origin}/login?invite=${encodeURIComponent(code)}` : "";
};

const AgentPage: React.FC = () => {
  const router = useRouter();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [agentInfo, setAgentInfo] = useState<ManagedAgentResponse | null>(null);
  const [state, setState] = useState<AsyncState>({ status: "idle" });
  const [ledgerState, setLedgerState] = useState<AsyncState>({ status: "idle" });
  const [inviteCopied, setInviteCopied] = useState(false);
  const [ledgerItems, setLedgerItems] = useState<AgentLedgerItem[]>([]);
  const [ledgerSummary, setLedgerSummary] = useState({
    totalAmount: 0,
    totalCommission: 0,
    totalOrders: 0,
    settledAmount: 0,
    unsettledAmount: 0,
    page: 1,
    pageSize: 20,
    totalPages: 1,
  });
  const [filters, setFilters] = useState<{ startDate?: string; endDate?: string }>({});
  const [noAgent, setNoAgent] = useState(false);
  const referralUrl = useMemo(() => buildInviteUrl(agentInfo?.invitationCode), [agentInfo?.invitationCode]);

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
        setNoAgent(true);
        return;
      }
      setNoAgent(false);
      const res = await agentGetManagedAgent(accessToken);
      setAgentInfo(res.data);
      setState({ status: "ready" });
    } catch (err) {
      const msg = (err as Error)?.message ?? "加载失败";
      const friendly = msg.includes("404") ? "当前账号未绑定代理商" : msg;
      setState({ status: "error", message: friendly });
      if (msg.includes("404")) {
        setNoAgent(true);
      }
      if ((err as Error)?.message?.includes("401")) {
        clearAuthTokens();
      }
    }
  }, [accessToken]);

  const loadLedger = useCallback(
    async (page = 1) => {
      if (!accessToken || noAgent) return;
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
          settledAmount: res.data.settledAmount || 0,
          unsettledAmount: res.data.unsettledAmount || 0,
          page: res.data.page,
          pageSize: res.data.pageSize,
          totalPages: res.data.totalPages,
        });
        setLedgerState({ status: "ready" });
      } catch (err) {
        const msg = (err as Error)?.message ?? "加载流水失败";
        const friendly = msg.includes("404") ? "当前账号未绑定代理商" : msg;
        setLedgerState({ status: "error", message: friendly });
      }
    },
    [accessToken, filters.startDate, filters.endDate, ledgerSummary.pageSize, noAgent],
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
            <p className="text-sm text-gray-600">查看渠道信息、查询佣金流水。</p>
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
            <div className="grid grid-cols-1 gap-3 text-sm text-gray-700 md:grid-cols-2">
              <div>
                <div className="text-xs text-gray-500">邀请注册人数</div>
                <div className="text-lg font-semibold text-gray-900">{agentInfo.invitedCount ?? 0}</div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500">邀请链接</span>
                <span className="rounded bg-gray-100 px-2 py-1 font-semibold text-gray-900">
                  {referralUrl || "—"}
                </span>
                {referralUrl && (
                  <button
                    type="button"
                    onClick={async () => {
                      if (!referralUrl) return;
                      try {
                        await navigator.clipboard.writeText(referralUrl);
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
            </div>
          </div>
        )}

        <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
          <div className="mb-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Link2 className="h-5 w-5 text-blue-600" />
              <div>
                <div className="text-sm font-semibold text-gray-900">佣金流水</div>
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

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-4">
            <div className="rounded-lg border border-gray-100 bg-gray-50 p-3">
              <div className="text-xs text-gray-500">总充值</div>
              <div className="text-lg font-semibold text-gray-900 mt-1">¥{yuan(ledgerSummary.totalAmount)}</div>
            </div>
            <div className="rounded-lg border border-gray-100 bg-gray-50 p-3">
              <div className="text-xs text-gray-500">预计佣金</div>
              <div className="text-lg font-semibold text-emerald-600 mt-1">¥{yuan(ledgerSummary.totalCommission)}</div>
            </div>
            <div className="rounded-lg border border-gray-100 bg-gray-50 p-3">
              <div className="text-xs text-gray-500">已结算</div>
              <div className="text-lg font-semibold text-blue-600 mt-1">¥{yuan(ledgerSummary.settledAmount)}</div>
            </div>
            <div className="rounded-lg border border-gray-100 bg-gray-50 p-3">
              <div className="text-xs text-gray-500">未结算</div>
              <div className="text-lg font-semibold text-amber-600 mt-1">¥{yuan(ledgerSummary.unsettledAmount)}</div>
            </div>
          </div>
          <div className="mt-1 text-xs text-gray-500">当前筛选共 {ledgerSummary.totalOrders} 笔订单</div>

          <div className="mt-3 overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left font-medium text-gray-600">订单号</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-600">用户</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-600">充值金额</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-600">佣金</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-600">比例</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-600">状态</th>
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
                    <td className="px-3 py-2 text-gray-600">{item.paidAt?.slice(0, 19).replace("T", " ") || "—"}</td>
                  </tr>
                ))}
                {ledgerItems.length === 0 && (
                  <tr>
                    <td className="px-3 py-4 text-center text-sm text-gray-500" colSpan={7}>
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
