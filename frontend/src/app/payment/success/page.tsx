'use client';

import Link from 'next/link';
import { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';

function SuccessContent() {
  const searchParams = useSearchParams();
  const orderNo = searchParams.get('order_no');
  const amount = searchParams.get('amount');

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-xl rounded-2xl bg-white shadow-xl border border-slate-100 p-8 space-y-6">
        <div className="flex items-center">
          <div className="h-12 w-12 rounded-full bg-green-100 text-green-700 flex items-center justify-center text-2xl font-semibold mr-4">
            ✓
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">支付成功</h1>
            <p className="text-sm text-slate-500">感谢您的购买，积分将很快到账</p>
          </div>
        </div>

        <div className="rounded-xl border border-slate-100 bg-slate-50 p-4 space-y-2 text-sm text-slate-700">
          {orderNo && (
            <div className="flex justify-between">
              <span className="text-slate-500">订单号</span>
              <span className="font-mono text-slate-900">{orderNo}</span>
            </div>
          )}
          {amount && (
            <div className="flex justify-between">
              <span className="text-slate-500">支付金额</span>
              <span className="font-semibold text-slate-900">¥{Number(amount) / 100}</span>
            </div>
          )}
          {!orderNo && !amount && (
            <p className="text-slate-600">您可以安全关闭此页面。</p>
          )}
        </div>

        <div className="space-y-2 text-sm text-slate-600">
          <p>如果积分未到账，请刷新页面或稍等片刻。仍有问题可联系我们的客服处理。</p>
        </div>

        <div className="flex gap-3">
          <Link
            href="/"
            className="flex-1 inline-flex items-center justify-center rounded-lg bg-blue-600 text-white px-4 py-3 text-sm font-medium hover:bg-blue-700 transition"
          >
            返回首页
          </Link>
          <Link
            href="/profile"
            className="flex-1 inline-flex items-center justify-center rounded-lg border border-slate-200 text-slate-700 px-4 py-3 text-sm font-medium hover:bg-slate-50 transition"
          >
            查看账户
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function PaymentSuccessPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center text-slate-600">加载中...</div>}>
      <SuccessContent />
    </Suspense>
  );
}
