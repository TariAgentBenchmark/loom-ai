'use client';

import React, { useMemo, useState } from 'react';

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

type PaymentStatus = 'idle' | 'processing' | 'success' | 'failed';

const generateTradeNo = () =>
  `WEB${Date.now()}${Math.random().toString(36).slice(2, 8).toUpperCase()}`;

const PaymentModal: React.FC<PaymentModalProps> = ({
  packageInfo,
  onClose,
  onPaymentSuccess,
  accessToken,
}) => {
  const [authCode, setAuthCode] = useState('135178236713755038');
  const [paymentStatus, setPaymentStatus] = useState<PaymentStatus>('idle');
  const [resultMessage, setResultMessage] = useState<string>('');
  const [responseData, setResponseData] = useState<any>(null);
  const [tradeNo, setTradeNo] = useState(generateTradeNo());

  const amountInFen = useMemo(
    () => Math.round(packageInfo.priceYuan * 100),
    [packageInfo.priceYuan]
  );

  const handleMicropay = async () => {
    if (!authCode.trim()) {
      alert('请输入拉卡拉扫码枪获得的付款码（auth_code）');
      return;
    }

    setPaymentStatus('processing');
    setResultMessage('');
    setResponseData(null);

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (accessToken) {
      headers.Authorization = `Bearer ${accessToken}`;
    }

    const freshTradeNo = generateTradeNo();
    setTradeNo(freshTradeNo);

    const reqData = {
      out_trade_no: freshTradeNo,
      out_order_no: `${freshTradeNo}_${packageInfo.packageId}`,
      auth_code: authCode.trim(),
      total_amount: String(amountInFen),
      location_info: {
        request_ip:
          typeof window !== 'undefined' ? window.location.hostname : '127.0.0.1',
        location: '+37.123456789,-121.123456789',
      },
    };

    try {
      const response = await fetch('/api/v1/payment/lakala/micropay', {
        method: 'POST',
        headers,
        body: JSON.stringify({ req_data: reqData }),
      });

      const data = await response.json().catch(() => ({}));
      setResponseData(data);

      if (!response.ok) {
        throw new Error(data.detail || data.message || '请求失败');
      }

      const code = (data.code || '').toString().toUpperCase();
      if (code === 'SUCCESS' || code === '000000') {
        setPaymentStatus('success');
        setResultMessage('支付成功，积分已到账。');
        onPaymentSuccess();
      } else {
        setPaymentStatus('failed');
        setResultMessage(data.msg || '支付失败，请重试');
      }
    } catch (error) {
      const message =
        error instanceof Error ? error.message : '支付失败，请重试';
      setPaymentStatus('failed');
      setResultMessage(message);
    }
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
            <label className="block text-sm font-medium text-gray-700">
              付款码（auth_code）
              <input
                type="text"
                value={authCode}
                onChange={(e) => setAuthCode(e.target.value)}
                placeholder="请扫描顾客付款码后填写"
                className="mt-2 w-full rounded-lg border border-gray-200 px-3 py-2 focus:border-blue-500 focus:outline-none"
              />
            </label>

            <div className="text-xs text-gray-500">
              当前订单号：{tradeNo}
            </div>

            <button
              onClick={handleMicropay}
              disabled={paymentStatus === 'processing'}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white py-3 rounded-lg font-medium transition"
            >
              {paymentStatus === 'processing' ? '支付处理中...' : '立即发起支付'}
            </button>

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

            {responseData && (
              <div className="rounded-lg bg-gray-50 p-3 text-xs text-gray-600 max-h-60 overflow-auto">
                <div className="font-semibold text-gray-800 mb-1">拉卡拉返回</div>
                <pre className="whitespace-pre-wrap break-all">
                  {JSON.stringify(responseData, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PaymentModal;
