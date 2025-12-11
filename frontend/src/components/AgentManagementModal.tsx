"use client";

import React, { useCallback, useEffect, useState } from "react";
import { ShieldCheck, UserPlus, Users, X, AlertCircle } from "lucide-react";
import {
  agentCreateChildAgent,
  agentGetManagedAgent,
  type ManagedAgentChild,
  type ManagedAgentResponse,
} from "../lib/api";

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
  const [childForm, setChildForm] = useState({
    name: "",
    userIdentifier: "",
    contact: "",
    notes: "",
  });

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

  const handleCreateChild = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!accessToken || !agentInfo) return;
    if ((agentInfo.level ?? 1) >= 2) {
      setState({ status: "error", message: "仅一级代理商可创建二级代理" });
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
      // 将新创建的代理拼接在列表前
      setAgentInfo((prev) =>
        prev
          ? { ...prev, children: [res.data, ...(prev.children || [])] }
          : prev,
      );
      setChildForm({ name: "", userIdentifier: "", contact: "", notes: "" });
      setState({ status: "ready" });
    } catch (err) {
      setState({
        status: "error",
        message: (err as Error)?.message ?? "创建二级代理失败",
      });
    }
  };

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
                  <span className="rounded-full bg-blue-100 px-2 py-1 font-semibold text-blue-700">
                    {agentInfo.level === 1 ? "一级代理" : "二级代理"}
                  </span>
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

            {agentInfo.level === 1 && (
              <div className="rounded-xl border border-gray-200 p-4">
                <div className="mb-3 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <UserPlus className="h-4 w-4 text-blue-600" />
                    <span className="text-sm font-semibold text-gray-900">创建二级代理商</span>
                  </div>
                  <span className="text-xs text-gray-500">二级代理不可再发展下级</span>
                </div>
                <form onSubmit={handleCreateChild} className="grid gap-3 sm:grid-cols-2">
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
                    <label className="text-xs text-gray-500">绑定用户</label>
                    <input
                      type="text"
                      value={childForm.userIdentifier}
                      onChange={(e) => setChildForm({ ...childForm, userIdentifier: e.target.value })}
                      className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                      placeholder="用户ID / 手机号 / 邮箱"
                      required
                    />
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
                  <div className="sm:col-span-2 flex justify-end gap-2">
                    <button
                      type="button"
                      onClick={() => setChildForm({ name: "", userIdentifier: "", contact: "", notes: "" })}
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

            <div className="rounded-xl border border-gray-200">
              <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
                <div className="flex items-center gap-2">
                  <Users className="h-4 w-4 text-blue-600" />
                  <span className="text-sm font-semibold text-gray-900">下级代理</span>
                </div>
                <span className="text-xs text-gray-500">共 {agentInfo.children?.length ?? 0} 个</span>
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
                    {agentInfo.children?.map((child) => (
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
                    {(!agentInfo.children || agentInfo.children.length === 0) && (
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
          </div>
        )}
      </div>
    </div>
  );
};

export default AgentManagementModal;
