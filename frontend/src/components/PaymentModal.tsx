'use client';

import React, { useCallback, useMemo, useState } from 'react';

interface PaymentModalProps {
  packageInfo: {
    packageId: string;
    packageName: string;
    priceYuan: number;
    totalCredits?: number;
  };
  onClose: () => void;
  onPaymentSuccess: () => void;
  accessToken?: string;
}

type PaymentStatus = 'idle' | 'processing' | 'redirecting' | 'success' | 'failed';
type PaymentChannel = 'ALIPAY' | 'WECHAT';

const CHANNEL_OPTIONS: Array<{ key: PaymentChannel; label: string }> = [
  { key: 'WECHAT', label: '微信支付' },
  { key: 'ALIPAY', label: '支付宝' },
];

const generateTradeNo = () =>
  `WEB${Date.now()}${Math.random().toString(36).slice(2, 8).toUpperCase()}`;

const unwrapLakalaPayload = (payload: any) => payload?.data ?? payload;

const extractCounterUrl = (payload: any): string | null => {
  if (!payload) return null;
  const respData = payload?.resp_data ?? payload?.respData ?? payload;
  const counterUrl = respData?.counter_url;
  
  if (typeof counterUrl === 'string' && counterUrl.trim().length > 0) {
    return counterUrl.trim();
  }
  return null;
};

const PaymentModal: React.FC<PaymentModalProps> = ({
  packageInfo,
  onClose,
  onPaymentSuccess,
  accessToken,
}) => {
  const [paymentStatus, setPaymentStatus] = useState<PaymentStatus>('idle');
  const [resultMessage, setResultMessage] = useState<string>('');
  const [counterUrl, setCounterUrl] = useState<string | null>(null);
  const [tradeNo, setTradeNo] = useState(generateTradeNo());
  const [paymentChannel, setPaymentChannel] = useState<PaymentChannel>('WECHAT');

  const amountInFen = useMemo(
    () => Math.round(packageInfo.priceYuan * 100),
    [packageInfo.priceYuan]
  );

  const selectedChannelLabel =
    CHANNEL_OPTIONS.find((item) => item.key === paymentChannel)?.label ?? '';

  const openCounterInNewTab = useCallback((url: string): boolean => {
    const newWindow = window.open(url, '_blank', 'noopener,noreferrer');
    if (!newWindow) {
      return false;
    }
    newWindow.opener = null;
    newWindow.focus();
    return true;
  }, []);

  const createCounterOrder = useCallback(async () => {
    if (!accessToken) {
      setPaymentStatus('failed');
      setResultMessage('登录状态已失效，请重新登录后再试');
      return;
    }

    setPaymentStatus('processing');
    setResultMessage('');
    setCounterUrl(null);

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (accessToken) {
      headers.Authorization = `Bearer ${accessToken}`;
    }

    const freshTradeNo = generateTradeNo();
    setTradeNo(freshTradeNo);

    const requestData = {
      out_order_no: `${freshTradeNo}_${packageInfo.packageId}`,
      total_amount: amountInFen,
      order_info: `购买${packageInfo.packageName}`,
      notify_url: `${window.location.origin}/api/v1/payment/lakala/counter/notify`,
      callback_url: `${window.location.origin}/payment/success`,
      payment_method: paymentChannel,
      support_refund: 1,
      support_repeat_pay: 1,
    };

    try {
      const response = await fetch('/api/v1/payment/lakala/counter/create', {
        method: 'POST',
        headers,
        body: JSON.stringify(requestData),
      });

      const raw = await response.json().catch(() => ({}));
      const payload = unwrapLakalaPayload(raw);

      if (!response.ok) {
        throw new Error(
          raw.detail || payload?.msg || payload?.message || '请求失败'
        );
      }

      // 测试用户走直充：payload.paymentSkipped=true
      if (payload?.paymentSkipped) {
        setPaymentStatus('success');
        setResultMessage(payload?.message || '测试用户已完成充值');
        onPaymentSuccess();
        onClose();
        return;
      }

      const code = (payload?.code || payload?.resp_code || '')
        .toString()
        .toUpperCase();
      if (code && code !== 'SUCCESS' && code !== '000000') {
        setPaymentStatus('failed');
        setResultMessage(payload?.msg || '创建支付订单失败，请稍后重试');
        return;
      }

      const counterUrlValue = extractCounterUrl(payload);
      if (!counterUrlValue) {
        setPaymentStatus('failed');
        setResultMessage('拉卡拉返回结果中缺少收银台地址');
        return;
      }

      setCounterUrl(counterUrlValue);
      setPaymentStatus('redirecting');
      setResultMessage(`即将在新标签页打开${selectedChannelLabel}收银台...`);

      const opened = openCounterInNewTab(counterUrlValue);
      if (!opened) {
        setPaymentStatus('failed');
        setResultMessage(
          '浏览器阻止了弹出窗口，请允许后重试或手动在新标签页打开收银台。'
        );
      } else {
        setResultMessage(`已在新标签页打开${selectedChannelLabel}收银台，请完成支付。`);
      }
    } catch (error) {
      const message =
        error instanceof Error ? error.message : '创建支付订单失败，请稍后再试';
      setPaymentStatus('failed');
      setResultMessage(message);
    }
  }, [
    accessToken,
    amountInFen,
    openCounterInNewTab,
    packageInfo.packageId,
    packageInfo.packageName,
    paymentChannel,
    selectedChannelLabel,
  ]);

  const handleChannelChange = (channel: PaymentChannel) => {
    setPaymentChannel(channel);
  };

  const handleCreateOrder = () => {
    void createCounterOrder();
  };

  const formatPrice = (value: number) => `¥${value.toLocaleString()}`;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
        <div className="p-6 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-gray-900">{packageInfo.packageName}</h2>
              <p className="text-sm text-gray-500">
                套餐价格：{formatPrice(packageInfo.priceYuan)} · 最终扣款：¥{(amountInFen / 100).toFixed(2)}
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl font-light"
            >
              ×
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <p className="text-sm font-medium text-gray-700 mb-2">选择支付方式</p>
              <div className="grid grid-cols-2 gap-3">
                {CHANNEL_OPTIONS.map((channel) => (
                  <button
                    key={channel.key}
                    type="button"
                    onClick={() => handleChannelChange(channel.key)}
                    className={`rounded-lg border px-3 py-2 text-sm font-medium transition ${
                      paymentChannel === channel.key
                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                        : 'border-gray-200 text-gray-600 hover:border-blue-200'
                    }`}
                  >
                    {channel.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>当前订单号：{tradeNo}</span>
            </div>

            {paymentStatus === 'idle' && (
              <div className="rounded-2xl border border-dashed border-blue-200 bg-blue-50/60 p-6 text-center">
                <div className="mx-auto flex h-32 w-32 items-center justify-center rounded-xl bg-white p-3 shadow-inner mb-4">
                  <svg className="w-16 h-16 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                </div>
                <p className="text-sm font-semibold text-gray-800 mb-2">
                  选择{selectedChannelLabel}支付
                </p>
                <p className="text-xs text-gray-500 mb-4">
                  点击下方按钮进入收银台完成支付
                </p>
                <button
                  onClick={handleCreateOrder}
                  disabled={paymentStatus !== 'idle'}
                  className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 disabled:bg-blue-300 disabled:cursor-not-allowed transition"
                >
                  {paymentStatus !== 'idle' ? '创建订单中...' : `前往${selectedChannelLabel}收银台`}
                </button>
              </div>
            )}

            {paymentStatus === 'processing' && (
              <div className="rounded-2xl border border-dashed border-blue-200 bg-blue-50/60 p-6 text-center">
                <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-4"></div>
                <p className="text-sm font-semibold text-gray-800">正在创建支付订单...</p>
                <p className="text-xs text-gray-500 mt-1">请稍候</p>
              </div>
            )}

            {paymentStatus === 'redirecting' && (
              <div className="rounded-2xl border border-dashed border-green-200 bg-green-50/60 p-6 text-center">
                <div className="animate-pulse rounded-full h-16 w-16 bg-green-500 mx-auto mb-4"></div>
                <p className="text-sm font-semibold text-gray-800">正在跳转到收银台...</p>
                <p className="text-xs text-gray-500 mt-1">请稍候，即将自动跳转</p>
              </div>
            )}

            {resultMessage && (
              <div
                className={`rounded-lg px-3 py-2 text-sm ${
                  paymentStatus === 'success'
                    ? 'bg-green-50 text-green-700'
                    : paymentStatus === 'failed'
                      ? 'bg-red-50 text-red-600'
                      : 'bg-blue-50 text-blue-600'
                }`}
              >
                {resultMessage}
              </div>
            )}

            {counterUrl && paymentStatus !== 'processing' && (
              <button
                type="button"
                onClick={() => {
                  const opened = openCounterInNewTab(counterUrl);
                  if (!opened) {
                    setPaymentStatus('failed');
                    setResultMessage(
                      '浏览器仍然阻止了弹出窗口，请检查浏览器设置或复制链接手动打开。'
                    );
                  } else {
                    setPaymentStatus('redirecting');
                    setResultMessage(
                      `已在新标签页打开${selectedChannelLabel}收银台，请完成支付。`
                    );
                  }
                }}
                className="w-full rounded-lg border border-blue-200 bg-white py-2 text-sm font-medium text-blue-600 hover:bg-blue-50 transition"
              >
                在新标签页打开收银台
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PaymentModal;
