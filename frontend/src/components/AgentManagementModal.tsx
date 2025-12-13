"use client";

import React, { useCallback, useEffect, useState } from "react";
import { ShieldCheck, UserPlus, Users, X, AlertCircle } from "lucide-react";
import { agentGetManagedAgent, type ManagedAgentResponse } from "../lib/api";

type AgentManagementModalProps = {
  open: boolean;
  accessToken: string | null;
  onClose: () => void;
};

type AsyncState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready" }
  | { status: "submitting" };

const AgentManagementModal: React.FC<AgentManagementModalProps> = ({ open, accessToken, onClose }) => {
  const [agentInfo, setAgentInfo] = useState<ManagedAgentResponse | null>(null);
  const [state, setState] = useState<AsyncState>({ status: "idle" });

  const loadData = useCallback(async () => {
    if (!open || !accessToken) return;
    setState({ status: "loading" });
    try {
      const res = await agentGetManagedAgent(accessToken);
      setAgentInfo(res.data);
      setState({ status: "ready" });
    } catch (err) {
      setState({
        status: "error",
        message: (err as Error)?.message ?? "加载代理商信息失败",
      });
    }
  }, [accessToken, open]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="relative w-full max-w-3xl rounded-2xl bg-white p-6 shadow-2xl">
        <button
          type="button"
          onClick={onClose}
          className="absolute right-4 top-4 text-gray-400 hover:text-gray-600"
          aria-label="close"
        >
          <X className="h-5 w-5" />
        </button>

        <div className="mb-6 flex items-center gap-3">
          <div className="rounded-full bg-blue-50 p-2">
            <ShieldCheck className="h-5 w-5 text-blue-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">代理商管理</h3>
            <p className="text-sm text-gray-500">查看当前代理信息并创建二级代理（仅一级代理可创建）。</p>
          </div>
        </div>

        {state.status === "error" && (
          <div className="mb-4 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-amber-800">
            <AlertCircle className="mt-0.5 h-4 w-4" />
            <span className="text-sm">{state.message}</span>
          </div>
        )}

        {state.status === "loading" && (
          <div className="py-6 text-center text-sm text-gray-500">加载中…</div>
        )}

        {agentInfo && state.status !== "loading" && (
          <div className="space-y-6">
            <div className="grid gap-4 rounded-xl border border-gray-200 bg-gray-50 p-4 sm:grid-cols-2">
              <div>
                <div className="text-sm text-gray-500">代理商</div>
                <div className="mt-1 text-lg font-semibold text-gray-900">{agentInfo.name}</div>
                <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-gray-600">
                  <span className="rounded-full bg-blue-100 px-2 py-1 font-semibold text-blue-700">代理</span>
                  <span className="rounded-full bg-gray-100 px-2 py-1 font-semibold text-gray-700">
                    {agentInfo.status === "active" ? "启用" : "停用"}
                  </span>
                </div>
                <div className="mt-2 text-sm text-gray-600">
                  绑定用户：{agentInfo.ownerUserPhone || agentInfo.ownerUserId || "—"}
                </div>
                <div className="text-sm text-gray-600">
                  邀请码：<span className="font-semibold text-gray-900">{agentInfo.invitationCode || "—"}</span>
                </div>
              </div>
              <div className="space-y-1 text-sm text-gray-600">
                <div>联系方式：{agentInfo.contact || "—"}</div>
                <div>备注：{agentInfo.notes || "—"}</div>
                <div>创建时间：{agentInfo.createdAt?.slice(0, 19).replace("T", " ") || "—"}</div>
              </div>
            </div>

            <div className="rounded-xl border border-gray-200 bg-gray-50 p-4">
              <div className="mb-2 flex items-center gap-2 font-semibold text-gray-900">
                <UserPlus className="h-4 w-4 text-blue-600" />
                二级代理创建已关闭
              </div>
              <div className="text-sm text-gray-600">当前仅管理员可创建代理。如需新增下级代理，请联系管理员处理。</div>
            </div>

            <div className="rounded-xl border border-gray-200">
              <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
                <div className="flex items-center gap-2">
                  <Users className="h-4 w-4 text-blue-600" />
                  <span className="text-sm font-semibold text-gray-900">下级代理</span>
                </div>
                <span className="text-xs text-gray-500">共 0 个</span>
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
                    <tr>
                      <td className="px-3 py-4 text-center text-sm text-gray-500" colSpan={5}>
                        暂无二级代理
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AgentManagementModal;
