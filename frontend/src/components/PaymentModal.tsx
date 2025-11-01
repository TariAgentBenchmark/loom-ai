'use client';

import React, { useState } from 'react';

interface PaymentModalProps {
  orderInfo: {
    order_id: string;
    package_name: string;
    final_amount: number;
    payment_method?: string;
    pay_order_no?: string;
    payment_url?: string;
    qr_code_url?: string;
    expires_at: string;
  };
  onClose: () => void;
  onPaymentSuccess: () => void;
  accessToken?: string;
}

const PaymentModal: React.FC<PaymentModalProps> = ({
  orderInfo,
  onClose,
  onPaymentSuccess,
  accessToken,
}) => {
  const [paymentStatus, setPaymentStatus] = useState<'pending' | 'success' | 'failed'>('pending');
  const [isChecking, setIsChecking] = useState(false);

  const handlePayment = () => {
    if (orderInfo.payment_url) {
      // 打开支付页面
      window.open(orderInfo.payment_url, '_blank');

      // 开始轮询检查支付状态
      startPaymentPolling();
    }
  };

  const startPaymentPolling = () => {
    setIsChecking(true);

    const checkInterval = setInterval(async () => {
      try {
        const headers = accessToken
          ? { Authorization: `Bearer ${accessToken}` }
          : undefined;

        const response = await fetch(`/api/v1/payment/orders/${orderInfo.order_id}`, {
          headers,
        });
        if (!response.ok) {
          if ([401, 403].includes(response.status)) {
            setPaymentStatus('failed');
            clearInterval(checkInterval);
            setIsChecking(false);
          }
          return;
        }

        const data = await response.json();

        if (data.data.status === 'paid') {
          setPaymentStatus('success');
          clearInterval(checkInterval);
          setIsChecking(false);

          // 延迟关闭并触发成功回调
          setTimeout(() => {
            onPaymentSuccess();
            onClose();
          }, 2000);
        }
      } catch (error) {
        console.error('检查支付状态失败:', error);
      }
    }, 3000); // 每3秒检查一次

    // 30分钟后停止检查
    setTimeout(() => {
      clearInterval(checkInterval);
      setIsChecking(false);
    }, 30 * 60 * 1000);
  };

  const formatAmount = (amount: number) => {
    return `¥${(amount / 100).toLocaleString()}`;
  };

  const getPaymentMethodName = (method: string) => {
    switch (method) {
      case 'lakala_counter':
        return '聚合收银台';
      default:
        return method;
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900">
              {paymentStatus === 'success' ? '支付成功' : '订单支付'}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl font-light"
            >
              ×
            </button>
          </div>

          {paymentStatus === 'pending' && (
            <>
              <div className="bg-gray-50 rounded-lg p-4 mb-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900 mb-2">
                    {formatAmount(orderInfo.final_amount)}
                  </div>
                  <div className="text-sm text-gray-600">
                    {orderInfo.package_name}
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                {orderInfo.qr_code_url && (
                  <div className="text-center">
                    <div className="text-sm text-gray-600 mb-2">
                      请使用{getPaymentMethodName(orderInfo.payment_method || 'lakala_counter')}扫描二维码
                    </div>
                    <img
                      src={orderInfo.qr_code_url}
                      alt="支付二维码"
                      className="mx-auto w-48 h-48 border border-gray-200 rounded-lg"
                    />
                  </div>
                )}

                <div className="text-center">
                  <button
                    onClick={handlePayment}
                    disabled={isChecking}
                    className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white py-3 rounded-lg font-medium transition"
                  >
                    {isChecking ? '正在检查支付状态...' : '跳转至收银台支付'}
                  </button>
                </div>

                <div className="text-xs text-gray-500 text-center">
                  支付页面将在新窗口打开，如未跳转请检查浏览器弹窗拦截。
                </div>

                <div className="text-xs text-gray-500 text-center">
                  订单将在 {new Date(orderInfo.expires_at).toLocaleString()} 过期
                </div>
                {orderInfo.pay_order_no && (
                  <div className="text-xs text-gray-500 text-center">
                    平台订单号：{orderInfo.pay_order_no}
                  </div>
                )}
              </div>
            </>
          )}

          {paymentStatus === 'success' && (
            <div className="text-center py-8">
              <div className="text-green-500 text-6xl mb-4">✓</div>
              <div className="text-xl font-bold text-gray-900 mb-2">
                支付成功！
              </div>
              <div className="text-gray-600">
                套餐已激活，积分已到账
              </div>
            </div>
          )}

          {paymentStatus === 'failed' && (
            <div className="text-center py-8">
              <div className="text-red-500 text-6xl mb-4">✗</div>
              <div className="text-xl font-bold text-gray-900 mb-2">
                支付失败
              </div>
              <div className="text-gray-600 mb-4">
                请重试或联系客服
              </div>
              <button
                onClick={handlePayment}
                className="bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg font-medium"
              >
                重新支付
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PaymentModal;
