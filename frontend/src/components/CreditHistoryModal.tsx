'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { ArrowDownCircle, ArrowUpCircle, Clock, Loader2, Wallet, X } from 'lucide-react';
import {
  CreditTransaction,
  CreditTransactionSummary,
  getCreditTransactions,
} from '../lib/api';
import { formatDateTime } from '../lib/datetime';

interface CreditHistoryModalProps {
  accessToken?: string;
  onClose: () => void;
}

type FilterType = '' | 'earn' | 'spend';

const formatAmount = (transaction: CreditTransaction) => {
  const sign = transaction.type === 'earn' ? '+' : '-';
  return `${sign}${Math.abs(transaction.amount).toFixed(2)}`;
};

const typeLabel = (type: string) => {
  if (type === 'earn') return '充值';
  if (type === 'spend') return '消费';
  return '其他';
};

const typeBadgeClasses = (type: string) => {
  if (type === 'earn') return 'bg-emerald-50 text-emerald-700 ring-emerald-100';
  if (type === 'spend') return 'bg-amber-50 text-amber-700 ring-amber-100';
  return 'bg-gray-50 text-gray-600 ring-gray-100';
};

const CreditHistoryModal: React.FC<CreditHistoryModalProps> = ({ accessToken, onClose }) => {
  const [transactions, setTransactions] = useState<CreditTransaction[]>([]);
  const [summary, setSummary] = useState<CreditTransactionSummary>({
    totalEarned: 0,
    totalSpent: 0,
    netChange: 0,
    period: '',
  });
  const [filters, setFilters] = useState<{ type: FilterType; startDate: string; endDate: string }>({
    type: '',
    startDate: '',
    endDate: '',
  });
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 10,
    total: 0,
    totalPages: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTransactions = useCallback(
    async (page = 1) => {
      if (!accessToken) {
        setLoading(false);
        setError('请先登录后再查看积分记录');
        return;
      }

      try {
        setLoading(true);
        setError(null);
        const response = await getCreditTransactions(accessToken, {
          page,
          limit: pagination.limit,
          type: filters.type || undefined,
          start_date: filters.startDate || undefined,
          end_date: filters.endDate || undefined,
        });

        setTransactions(response.data.transactions ?? []);
        setSummary(
          response.data.summary ?? {
            totalEarned: 0,
            totalSpent: 0,
            netChange: 0,
            period: '',
          },
        );

        const p: any = response.data.pagination || {};
        const resolvedLimit = p.limit ?? pagination.limit;
        const resolvedTotal = p.total ?? 0;
        const resolvedTotalPages =
          p.total_pages ??
          p.totalPages ??
          (resolvedLimit > 0 ? Math.ceil(resolvedTotal / resolvedLimit) : 0);

        setPagination({
          page: p.page ?? page,
          limit: resolvedLimit,
          total: resolvedTotal,
          totalPages: resolvedTotalPages,
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : '获取积分记录失败');
      } finally {
        setLoading(false);
      }
    },
    [accessToken, filters.endDate, filters.startDate, filters.type, pagination.limit],
  );

  useEffect(() => {
    fetchTransactions(1);
  }, [fetchTransactions]);

  const handlePageChange = (nextPage: number) => {
    if (nextPage < 1 || nextPage > pagination.totalPages) return;
    fetchTransactions(nextPage);
  };

  const summaryCards = useMemo(
    () => [
      {
        title: '充值总计',
        value: summary.totalEarned.toFixed(2),
        accent: 'text-emerald-600',
        icon: ArrowDownCircle,
      },
      {
        title: '消费总计',
        value: summary.totalSpent.toFixed(2),
        accent: 'text-amber-600',
        icon: ArrowUpCircle,
      },
      {
        title: '净变动',
        value: summary.netChange.toFixed(2),
        accent: summary.netChange >= 0 ? 'text-emerald-600' : 'text-amber-600',
        icon: Wallet,
      },
    ],
    [summary.netChange, summary.totalEarned, summary.totalSpent],
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
      <div className="w-full max-w-4xl bg-white rounded-2xl shadow-2xl border border-gray-100 overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">充值 / 消费记录</h2>
            <p className="text-xs text-gray-500">查看积分充值、消耗明细，便于核对账单</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition rounded-full p-1 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            aria-label="关闭"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="px-6 py-5 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {summaryCards.map((card) => (
              <div
                key={card.title}
                className="rounded-xl border border-gray-100 bg-gray-50 px-4 py-3 flex items-center space-x-3"
              >
                <div className={`p-2 rounded-lg bg-white shadow-sm ${card.accent.replace('text', 'bg')}`}>
                  <card.icon className={`h-5 w-5 ${card.accent}`} />
                </div>
                <div>
                  <p className="text-xs text-gray-500">{card.title}</p>
                  <p className={`text-lg font-semibold ${card.accent}`}>{card.value}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="bg-gray-50 rounded-lg p-3 border border-gray-100 flex flex-wrap gap-3 items-center">
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-600">类型</span>
              {[
                { key: '', label: '全部' },
                { key: 'earn', label: '充值' },
                { key: 'spend', label: '消费' },
              ].map((item) => (
                <button
                  key={item.key}
                  onClick={() => setFilters((prev) => ({ ...prev, type: item.key as FilterType }))}
                  className={`px-3 py-1 text-xs rounded-full border transition ${
                    filters.type === item.key
                      ? 'border-blue-500 bg-white text-blue-600 shadow-sm'
                      : 'border-gray-200 text-gray-600 hover:bg-white'
                  }`}
                >
                  {item.label}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-600">时间</span>
              <input
                type="date"
                value={filters.startDate}
                onChange={(e) => setFilters((prev) => ({ ...prev, startDate: e.target.value }))}
                className="h-9 rounded border border-gray-200 px-2 text-xs text-gray-700 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              />
              <span className="text-xs text-gray-500">至</span>
              <input
                type="date"
                value={filters.endDate}
                onChange={(e) => setFilters((prev) => ({ ...prev, endDate: e.target.value }))}
                className="h-9 rounded border border-gray-200 px-2 text-xs text-gray-700 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              />
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => fetchTransactions(1)}
                className="px-3 py-1.5 text-xs rounded-md bg-blue-600 text-white hover:bg-blue-700 transition"
              >
                应用
              </button>
              <button
                onClick={() => {
                  setFilters({ type: '', startDate: '', endDate: '' });
                  fetchTransactions(1);
                }}
                className="px-3 py-1.5 text-xs rounded-md border border-gray-200 text-gray-600 hover:bg-white transition"
              >
                清除
              </button>
            </div>
          </div>

          <div className="border border-gray-100 rounded-xl overflow-hidden">
            <div className="bg-gray-50 px-4 py-2 flex items-center justify-between text-xs text-gray-500">
              <div>共 {pagination.total} 条 · {summary.period || '全部时间'}</div>
              <div className="flex items-center gap-1">
                <Clock className="h-4 w-4" />
                <span>按时间倒序</span>
              </div>
            </div>

            <div className="max-h-[480px] overflow-y-auto">
              {loading ? (
                <div className="flex items-center justify-center py-16 text-gray-500">
                  <Loader2 className="h-5 w-5 animate-spin mr-2" />
                  <span>加载中...</span>
                </div>
              ) : error ? (
                <div className="flex items-center justify-center py-12 text-red-600 text-sm">
                  {error}
                </div>
              ) : transactions.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-14 text-gray-500 text-sm">
                  <Wallet className="h-8 w-8 mb-2 text-gray-400" />
                  暂无积分记录
                </div>
              ) : (
                <ul className="divide-y divide-gray-100">
                  {transactions.map((txn) => (
                    <li key={txn.transactionId} className="px-4 py-3 hover:bg-gray-50">
                      <div className="flex items-start justify-between gap-3">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span
                              className={`inline-flex items-center px-2 py-0.5 text-[11px] font-medium rounded-full ring-1 ${typeBadgeClasses(
                                txn.type,
                              )}`}
                            >
                              {typeLabel(txn.type)}
                            </span>
                            <span className="text-xs text-gray-500">{formatDateTime(txn.createdAt)}</span>
                          </div>
                          <div className="text-sm font-semibold text-gray-900">{txn.description}</div>
                          <div className="text-xs text-gray-500 space-x-3">
                            {txn.relatedOrderId && <span>订单：{txn.relatedOrderId}</span>}
                            {txn.relatedTaskId && <span>任务：{txn.relatedTaskId}</span>}
                          </div>
                        </div>
                        <div className="text-right">
                          <div
                            className={`text-base font-semibold ${
                              txn.type === 'earn' ? 'text-emerald-600' : 'text-amber-600'
                            }`}
                          >
                            {formatAmount(txn)}
                          </div>
                          <div className="text-xs text-gray-500">交易后余额：{txn.balance.toFixed(2)}</div>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          <div className="flex items-center justify-between text-xs text-gray-600">
            <div>
              第 {pagination.page} / {Math.max(pagination.totalPages, 1)} 页
            </div>
            <div className="space-x-2">
              <button
                onClick={() => handlePageChange(pagination.page - 1)}
                disabled={pagination.page <= 1}
                className="px-3 py-1 rounded-md border border-gray-200 text-gray-600 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                上一页
              </button>
              <button
                onClick={() => handlePageChange(pagination.page + 1)}
                disabled={pagination.page >= pagination.totalPages}
                className="px-3 py-1 rounded-md border border-gray-200 text-gray-600 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
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

export default CreditHistoryModal;
