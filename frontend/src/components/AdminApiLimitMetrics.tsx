"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { AlertCircle, Gauge, RefreshCcw, Signal, Timer } from "lucide-react";
import {
  adminGetApiLimitMetrics,
  type AdminApiLimitMetric,
} from "../lib/api";
import { useAdminAccessToken } from "../contexts/AdminAuthContext";

const formatPercent = (value: number) =>
  `${Math.min(100, Math.max(0, Math.round(value)))}%`;

type MetricState =
  | { status: "idle" }
  | { status: "error"; message: string }
  | { status: "ready"; items: AdminApiLimitMetric[]; fetchedAt: string };

const StatusBadge: React.FC<{ utilization: number }> = ({ utilization }) => {
  let label = "空闲";
  let color = "bg-emerald-100 text-emerald-700 ring-emerald-200";
  if (utilization >= 0.9) {
    label = "拥堵";
    color = "bg-red-100 text-red-700 ring-red-200";
  } else if (utilization >= 0.6) {
    label = "紧张";
    color = "bg-amber-100 text-amber-700 ring-amber-200";
  }
  return (
    <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ring-1 ring-inset ${color}`}>
      {label}
    </span>
  );
};

const AdminApiLimitMetrics: React.FC = () => {
  const accessToken = useAdminAccessToken();
  const [state, setState] = useState<MetricState>({ status: "idle" });
  const [isFetching, setIsFetching] = useState(false);
  const [countdown, setCountdown] = useState(10);

  const REFRESH_INTERVAL_SECONDS = 10;

  const fetchMetrics = useCallback(async () => {
    if (!accessToken) return;
    setIsFetching(true);
    try {
      const res = await adminGetApiLimitMetrics(accessToken);
      setState({
        status: "ready",
        items: (res.data.metrics || []).map((m) => ({
          ...m,
          leasedTokens: m.leasedTokens ?? m.leased_tokens ?? 0,
        })),
        fetchedAt: new Date().toLocaleTimeString("zh-CN", { hour12: false }),
      });
    } catch (err) {
      setState({
        status: "error",
        message: (err as Error)?.message ?? "获取限流数据失败",
      });
    }
    setIsFetching(false);
  }, [accessToken]);

  useEffect(() => {
    if (!accessToken) return;

    // 首次加载 + 定时刷新，保持仪表盘接近实时
    fetchMetrics();
    setCountdown(REFRESH_INTERVAL_SECONDS);

    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          fetchMetrics();
          return REFRESH_INTERVAL_SECONDS;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [accessToken, fetchMetrics]);

  const ordered = useMemo(() => {
    if (state.status !== "ready") return [];
    return [...state.items].sort((a, b) => a.api.localeCompare(b.api));
  }, [state]);

  if (!accessToken) {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-amber-800">
        请先登录管理员账户。
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">下游 API 并发限流</h2>
          <p className="text-sm text-gray-500">
            查看各服务商的并发占用、空闲槽与租约情况，便于定位拥堵与排队。
          </p>
        </div>
        <button
          type="button"
          onClick={fetchMetrics}
          className="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
        >
          <RefreshCcw className="h-4 w-4" />
          刷新
        </button>
      </div>

      {state.status === "error" && (
        <div className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-800">
          <AlertCircle className="mt-0.5 h-5 w-5" />
          <div>
            <p className="text-sm font-semibold">加载失败</p>
            <p className="text-sm">{state.message}</p>
          </div>
        </div>
      )}

      {state.status === "ready" && (
        <>
          <div className="text-xs text-gray-500">
            上次刷新：{state.fetchedAt}
            <span className="ml-2">
              自动刷新倒计时：{countdown}s {isFetching ? "(刷新中…)" : ""}
            </span>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {ordered.map((metric) => {
              const utilization = metric.limit > 0 ? metric.active / metric.limit : 0;
              const leased = metric.leasedTokens ?? 0;
              const queueHint = Math.max(leased - metric.active, 0);
              return (
                <div
                  key={metric.api}
                  className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm"
                >
                  <div className="mb-3 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
                        <Gauge className="h-4 w-4" />
                      </div>
                      <div>
                        <div className="text-sm font-semibold text-gray-900 uppercase">
                          {metric.api}
                        </div>
                        <div className="text-xs text-gray-500">
                          并发上限 {metric.limit}
                        </div>
                      </div>
                    </div>
                    <StatusBadge utilization={utilization} />
                  </div>

                  <div className="space-y-2 text-sm text-gray-700">
                    <div className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2">
                      <span className="flex items-center gap-2 text-gray-600">
                        <Signal className="h-4 w-4" />
                        正在占用
                      </span>
                      <span className="font-semibold text-gray-900">{metric.active}</span>
                    </div>
                    <div className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2">
                      <span className="flex items-center gap-2 text-gray-600">
                        <Gauge className="h-4 w-4" />
                        空闲槽位
                      </span>
                      <span className="font-semibold text-gray-900">{metric.available}</span>
                    </div>
                    <div className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2">
                      <span className="flex items-center gap-2 text-gray-600">
                        <Timer className="h-4 w-4" />
                        租约中的令牌
                      </span>
                      <span className="font-semibold text-gray-900">
                        {metric.leasedTokens}
                        {queueHint > 0 ? `（排队估计 ${queueHint}）` : ""}
                      </span>
                    </div>
                  </div>

                  <div className="mt-3">
                    <div className="mb-1 flex items-center justify-between text-xs text-gray-500">
                      <span>并发占用</span>
                      <span>{formatPercent(utilization * 100)}</span>
                    </div>
                    <div className="h-2 w-full overflow-hidden rounded-full bg-gray-100">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-blue-500 to-indigo-500 transition-all"
                        style={{
                          width: `${Math.min(100, Math.max(0, utilization * 100))}%`,
                        }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
};

export default AdminApiLimitMetrics;
