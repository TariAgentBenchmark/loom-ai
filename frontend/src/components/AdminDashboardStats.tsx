"use client";

import React, { useEffect, useMemo, useState } from "react";
import { adminGetDashboardStats, type AdminDashboardStats } from "../lib/api";
import { useAdminAccessToken } from "../contexts/AdminAuthContext";
import { ArrowUpRight, RefreshCcw, ShoppingBag, Target, Users } from "lucide-react";

const formatCurrencyFromCents = (amount: number) =>
  new Intl.NumberFormat("zh-CN", {
    style: "currency",
    currency: "CNY",
    minimumFractionDigits: 0,
  }).format(amount / 100);

const formatNumber = (value: number) => new Intl.NumberFormat("zh-CN").format(value);

type ProgressMetric = {
  title: string;
  value: string;
  percent: number;
  accent: string;
  icon: React.ElementType;
};

const ProgressRing: React.FC<{
  percent: number;
  color: string;
}> = ({ percent, color }) => {
  const normalized = Math.min(Math.max(percent, 0), 100);
  const radius = 42;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (normalized / 100) * circumference;

  return (
    <div className="relative h-24 w-24">
      <svg className="h-full w-full" viewBox="0 0 100 100">
        <circle
          cx="50"
          cy="50"
          r={radius}
          stroke="#E5E7EB"
          strokeWidth="8"
          fill="transparent"
        />
        <circle
          cx="50"
          cy="50"
          r={radius}
          stroke={color}
          strokeWidth="8"
          fill="transparent"
          strokeDasharray={`${circumference} ${circumference}`}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(-90 50 50)"
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-lg font-semibold text-gray-900">{Math.round(normalized)}%</span>
      </div>
    </div>
  );
};

const MetricCard: React.FC<{ metric: ProgressMetric }> = ({ metric }) => {
  const Icon = metric.icon;
  return (
    <div className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white px-6 py-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-lg">
      <div>
        <div className="flex items-center gap-2 text-sm font-medium text-slate-500">
          <Icon className="h-4 w-4" />
          {metric.title}
        </div>
        <div className="mt-2 text-2xl font-semibold text-slate-900">{metric.value}</div>
        <div className="mt-1 flex items-center text-xs text-slate-400">
          <ArrowUpRight className="mr-1 h-3 w-3" />
          与昨日相比
        </div>
      </div>
      <ProgressRing percent={metric.percent} color={metric.accent} />
    </div>
  );
};

const DonutChart: React.FC<{
  segments: Array<{ label: string; value: number; color: string }>;
  totalLabel: string;
}> = ({ segments, totalLabel }) => {
  const total = segments.reduce((sum, item) => sum + item.value, 0) || 1;
  let cumulative = 0;
  const gradient = segments
    .map((segment) => {
      const start = (cumulative / total) * 100;
      cumulative += segment.value;
      const end = (cumulative / total) * 100;
      return `${segment.color} ${start}% ${end}%`;
    })
    .join(", ");

  return (
    <div>
      <div
        className="relative mx-auto h-56 w-56 rounded-full"
        style={{
          background: `conic-gradient(${gradient})`,
        }}
      >
        <div className="absolute inset-8 rounded-full bg-white shadow-inner" />
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <div className="text-xs font-medium uppercase tracking-wide text-slate-400">累计</div>
          <div className="mt-1 text-xl font-semibold text-slate-900">{totalLabel}</div>
        </div>
      </div>
      <ul className="mt-6 space-y-3">
        {segments.map((segment) => (
          <li key={segment.label} className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span
                className="h-3 w-3 rounded-full"
                style={{ backgroundColor: segment.color }}
              />
              <span className="text-sm font-medium text-slate-600">{segment.label}</span>
            </div>
            <span className="text-sm font-semibold text-slate-900">
              {Math.round((segment.value / total) * 100)}%
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
};

const RevenueAreaChart: React.FC<{
  points: Array<{ label: string; value: number }>;
}> = ({ points }) => {
  const fallbackPoint = { label: "无数据", value: 0 };
  const data = points.length > 1 ? points : [...points, fallbackPoint];
  const width = 420;
  const height = 160;
  const verticalPadding = 12;
  const maxValue = data.reduce((max, point) => (point.value > max ? point.value : max), 1);
  const step = data.length > 1 ? width / (data.length - 1) : width;
  const coords = data.map((point, index) => {
    const x = index * step;
    const y = height - (point.value / maxValue) * (height - verticalPadding) - verticalPadding / 2;
    return { x, y };
  });

  const linePath = coords
    .map((coord, index) => `${index === 0 ? "M" : "L"}${coord.x.toFixed(1)} ${coord.y.toFixed(1)}`)
    .join(" ");

  const areaPath = `${linePath} L${coords[coords.length - 1].x.toFixed(1)} ${height} L0 ${height} Z`;

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <div className="text-sm font-medium text-slate-500">收入趋势</div>
          <div className="text-2xl font-semibold text-slate-900">近7次交易走势</div>
        </div>
        <div className="rounded-full bg-emerald-100 px-3 py-1 text-sm font-semibold text-emerald-600">
          +{Math.round(((data[data.length - 1].value - data[0].value) / (data[0].value || 1)) * 100)}%
        </div>
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} className="h-40 w-full">
        <defs>
          <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.35" />
            <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
          </linearGradient>
        </defs>
        <path d={areaPath} fill="url(#revenueGradient)" />
        <path d={linePath} fill="none" stroke="#2563eb" strokeWidth="2.5" strokeLinecap="round" />
      </svg>
      <div className="mt-4 grid grid-cols-7 gap-2 text-center text-xs text-slate-400">
        {data.map((point, index) => (
          <span key={`${point.label}-${index}`}>{point.label}</span>
        ))}
      </div>
    </div>
  );
};

const AdminDashboardStats: React.FC = () => {
  const accessToken = useAdminAccessToken();
  const [stats, setStats] = useState<AdminDashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      if (!accessToken) {
        return;
      }

      try {
        setLoading(true);
        const response = await adminGetDashboardStats(accessToken);
        setStats(response.data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "获取统计数据失败");
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, [accessToken]);

  const metrics = useMemo<ProgressMetric[]>(() => {
    const snapshot = stats;
    if (!snapshot) {
      return [
        { title: "新访问", value: "0", percent: 0, accent: "#34D399", icon: Target },
        { title: "购买订单", value: "0", percent: 0, accent: "#60A5FA", icon: ShoppingBag },
        { title: "活跃用户", value: "0", percent: 0, accent: "#F59E0B", icon: Users },
        { title: "退订/退款", value: "0", percent: 0, accent: "#38BDF8", icon: RefreshCcw },
      ];
    }

    const { users, orders } = snapshot;

    return [
      {
        title: "新访问",
        value: formatNumber(users.newToday),
        percent: users.total === 0 ? 0 : (users.newToday / users.total) * 100,
        accent: "#34D399",
        icon: Target,
      },
      {
        title: "购买订单",
        value: formatNumber(orders.paid),
        percent: orders.total === 0 ? 0 : (orders.paid / orders.total) * 100,
        accent: "#60A5FA",
        icon: ShoppingBag,
      },
      {
        title: "活跃用户",
        value: formatNumber(users.active),
        percent: users.total === 0 ? 0 : (users.active / users.total) * 100,
        accent: "#F59E0B",
        icon: Users,
      },
      {
        title: "退订/退款",
        value: "0",
        percent: 0,
        accent: "#38BDF8",
        icon: RefreshCcw,
      },
    ];
  }, [stats]);

  const membershipSegments = useMemo(() => {
    const snapshot = stats;
    if (!snapshot) {
      return [
        { label: "免费体验", value: 0, color: "#A855F7" },
        { label: "基础会员", value: 0, color: "#60A5FA" },
        { label: "专业会员", value: 0, color: "#34D399" },
        { label: "企业会员", value: 0, color: "#F97316" },
      ];
    }

    const { membershipBreakdown } = snapshot.users;

    return [
      {
        label: "免费体验",
        value: membershipBreakdown.free,
        color: "#A855F7",
      },
      {
        label: "基础会员",
        value: membershipBreakdown.basic,
        color: "#60A5FA",
      },
      {
        label: "专业会员",
        value: membershipBreakdown.premium,
        color: "#34D399",
      },
      {
        label: "企业会员",
        value: membershipBreakdown.enterprise,
        color: "#F97316",
      },
    ];
  }, [stats]);

  const revenueTrend = useMemo(() => {
  const snapshot = stats;
  if (!snapshot) {
    return [{ label: "无数据", value: 0 }];
  }

  const dailyMap = new Map<string, number>();
  snapshot.recentActivity
    .filter((activity) => activity.type === "order" && activity.status === "paid")
    .forEach((activity) => {
      const day = new Date(activity.timestamp).toLocaleDateString("zh-CN", {
        month: "2-digit",
        day: "2-digit",
      });
      const current = dailyMap.get(day) || 0;
      dailyMap.set(day, current + activity.amount);
    });

  const ordered = Array.from(dailyMap.entries())
    .slice(-7)
    .map(([label, value]) => ({ label, value }));

    if (ordered.length === 0) {
      return [{ label: "无数据", value: 0 }];
    }

    if (ordered.length === 1) {
      return [...ordered, { label: ordered[0].label, value: ordered[0].value }];
    }

    return ordered;
  }, [stats]);

  if (loading) {
    return (
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
        {[...Array(4)].map((_, index) => (
          <div key={index} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="animate-pulse space-y-4">
              <div className="h-3 w-1/3 rounded bg-slate-200" />
              <div className="h-8 w-1/2 rounded bg-slate-200" />
              <div className="h-24 rounded-full bg-slate-100" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-red-700">
        {error || "无法加载统计数据"}
      </div>
    );
  }

  const paidRate = stats.orders.total === 0 ? 0 : (stats.orders.paid / stats.orders.total) * 100;
  const pendingRate = stats.orders.total === 0 ? 0 : (stats.orders.pending / stats.orders.total) * 100;
  const creditTurnoverRate =
    stats.credits.total === 0 ? 0 : (stats.credits.transactionsToday / stats.credits.total) * 100;
  const refundRatio = 0;

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => (
          <MetricCard key={metric.title} metric={metric} />
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-12">
        <div className="xl:col-span-6">
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium text-slate-500">渠道构成</div>
                <div className="text-2xl font-semibold text-slate-900">会员分布</div>
              </div>
              <div className="rounded-full bg-violet-100 px-3 py-1 text-xs font-semibold text-violet-600">
                {formatNumber(stats.users.total)} 用户
              </div>
            </div>
            <div className="mt-6 flex flex-col items-center justify-center">
              <DonutChart
                segments={membershipSegments}
                totalLabel={`${formatNumber(stats.users.total)} 位用户`}
              />
            </div>
          </div>
        </div>
        <div className="xl:col-span-6">
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="text-sm font-medium text-slate-500">积分与订单概览</div>
            <div className="mt-6 grid gap-6 lg:grid-cols-2">
              <div className="space-y-4">
                <div className="flex items-center justify-between rounded-xl border border-slate-100 bg-white/60 p-4 shadow-sm">
                  <div>
                    <div className="text-xs font-medium text-slate-500">积分余额</div>
                    <div className="mt-2 text-2xl font-semibold text-slate-900">
                      {formatNumber(stats.credits.total)}
                    </div>
                    <div className="mt-1 text-xs text-slate-400">当前可用积分</div>
                  </div>
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
                    kw
                  </div>
                </div>
                <div className="flex items-center justify-between rounded-xl border border-slate-100 bg-white/60 p-4 shadow-sm">
                  <div>
                    <div className="text-xs font-medium text-slate-500">今日收入</div>
                    <div className="mt-2 text-2xl font-semibold text-slate-900">
                      {formatCurrencyFromCents(stats.revenue.today)}
                    </div>
                    <div className="mt-1 text-xs text-slate-400">当日完成交易金额</div>
                  </div>
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-sky-100 text-sky-600">
                    ￥
                  </div>
                </div>
                <div className="flex items-center justify-between rounded-xl border border-slate-100 bg-white/60 p-4 shadow-sm">
                  <div>
                    <div className="text-xs font-medium text-slate-500">平均订单额</div>
                    <div className="mt-2 text-2xl font-semibold text-slate-900">
                      {formatCurrencyFromCents(stats.revenue.averageOrderValue)}
                    </div>
                    <div className="mt-1 text-xs text-slate-400">基于所有已支付订单</div>
                  </div>
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-violet-100 text-violet-600">
                    ¥
                  </div>
                </div>
              </div>
              <div className="space-y-5">
                <div>
                  <div className="flex items-center justify-between text-xs font-medium text-slate-500">
                    <span>付费订单占比</span>
                    <span className="text-slate-900">{Math.round(paidRate)}%</span>
                  </div>
                  <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full bg-emerald-500"
                      style={{ width: `${Math.round(paidRate)}%` }}
                    />
                  </div>
                  <div className="mt-1 text-xs text-slate-400">
                    已支付订单 {formatNumber(stats.orders.paid)} / {formatNumber(stats.orders.total)}
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-between text-xs font-medium text-slate-500">
                    <span>待支付订单</span>
                    <span className="text-slate-900">{Math.round(pendingRate)}%</span>
                  </div>
                  <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full bg-amber-400"
                      style={{ width: `${Math.round(pendingRate)}%` }}
                    />
                  </div>
                  <div className="mt-1 text-xs text-slate-400">
                    待支付订单 {formatNumber(stats.orders.pending)}
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-between text-xs font-medium text-slate-500">
                    <span>今日积分消耗</span>
                    <span className="text-slate-900">{Math.round(creditTurnoverRate)}%</span>
                  </div>
                  <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full bg-sky-400"
                      style={{ width: `${Math.min(100, Math.round(creditTurnoverRate))}%` }}
                    />
                  </div>
                  <div className="mt-1 text-xs text-slate-400">
                    今日交易 {formatNumber(stats.credits.transactionsToday)}
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-between text-xs font-medium text-slate-500">
                    <span>退款金额占比</span>
                    <span className="text-slate-900">{Math.round(refundRatio)}%</span>
                  </div>
                  <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full bg-rose-400"
                      style={{ width: `${Math.round(refundRatio)}%` }}
                    />
                  </div>
                  <div className="mt-1 text-xs text-slate-400">
                    累计退款 ￥0
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <RevenueAreaChart points={revenueTrend} />
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="text-sm font-medium text-slate-500">今日快览</div>
          <div className="mt-4 space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-500">今日交易</span>
              <span className="font-semibold text-slate-900">
                {formatNumber(stats.credits.transactionsToday)}
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-500">待支付订单</span>
              <span className="font-semibold text-yellow-600">
                {formatNumber(stats.orders.pending)}
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-500">退款金额</span>
              <span className="font-semibold text-rose-500">
                ￥0
              </span>
            </div>
          </div>
          <div className="mt-6 rounded-xl bg-slate-50 p-4">
            <div className="text-sm font-semibold text-slate-700">提示</div>
            <p className="mt-1 text-sm text-slate-500">
              查看待支付订单并及时跟进，确保关键交易顺利完成。
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="text-sm font-medium text-slate-500">总收入</div>
          <div className="mt-2 text-3xl font-semibold text-slate-900">
            {formatCurrencyFromCents(stats.revenue.total)}
          </div>
          <div className="mt-3 flex items-center text-xs text-emerald-500">
            <ArrowUpRight className="mr-1 h-3 w-3" /> 同比增长 18%
          </div>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="text-sm font-medium text-slate-500">订单概览</div>
          <div className="mt-4 space-y-3 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-slate-500">总订单数</span>
              <span className="font-semibold text-slate-900">{formatNumber(stats.orders.total)}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-500">已支付订单</span>
              <span className="font-semibold text-emerald-600">{formatNumber(stats.orders.paid)}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-500">待支付订单</span>
              <span className="font-semibold text-yellow-600">{formatNumber(stats.orders.pending)}</span>
            </div>
          </div>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-gradient-to-r from-sky-500 via-emerald-500 to-emerald-600 p-6 text-white shadow-sm">
          <div className="text-sm font-medium uppercase tracking-wide text-emerald-100">AI Service</div>
          <div className="mt-2 text-2xl font-semibold">图云AI</div>
          <p className="mt-2 text-sm text-emerald-50">
            集成去水印、提取花型、智能增强等多项能力，一站式完成设计生产流程。
          </p>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboardStats;