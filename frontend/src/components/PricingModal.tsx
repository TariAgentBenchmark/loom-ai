'use client';

import React, { useState } from 'react';
import PaymentModal from './PaymentModal';
import {
  membershipPackages as membershipPackageData,
  discountPackages as discountPackageData,
  PackageData,
} from '../data/packages';

interface PricingModalProps {
  onClose: () => void;
  isLoggedIn?: boolean;
  onLogin?: () => void;
}

const TABS: Array<{ key: 'membership' | 'discount'; label: string }> = [
  { key: 'membership', label: '会员套餐' },
  { key: 'discount', label: '积分套餐' },
];

const PAYMENT_ICON_URLS: Record<'wechat' | 'alipay', string> = {
  wechat: 'https://cdn.jsdelivr.net/npm/simple-icons@11.3.0/icons/wechat.svg',
  alipay: 'https://cdn.jsdelivr.net/npm/simple-icons@11.3.0/icons/alipay.svg',
};

const PaymentIcon = ({ type }: { type: 'wechat' | 'alipay' }) => (
  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-50">
    <img
      src={PAYMENT_ICON_URLS[type]}
      alt={type === 'wechat' ? '微信' : '支付宝'}
      className="h-6 w-6 object-contain"
      loading="lazy"
    />
  </span>
);

const PricingModal: React.FC<PricingModalProps> = ({ onClose, isLoggedIn = false, onLogin }) => {
  const [activeTab, setActiveTab] = useState<'membership' | 'discount'>('membership');
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [currentOrder, setCurrentOrder] = useState<any>(null);
  const [selectedPaymentMethod, setSelectedPaymentMethod] = useState<'wechat' | 'alipay'>('wechat');
  const [showMethodSelector, setShowMethodSelector] = useState(false);
  const [pendingPackage, setPendingPackage] = useState<PackageData | null>(null);

  const membershipPackages = membershipPackageData;
  const discountPackages = discountPackageData;

  const handlePurchase = async (packageId: string, paymentMethod: 'wechat' | 'alipay') => {
    try {
      const response = await fetch('/api/v1/payment/orders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ package_id: packageId, payment_method: paymentMethod, quantity: 1 }),
      });

      if (response.ok) {
        const orderData = await response.json();
        setSelectedPaymentMethod(paymentMethod);
        setCurrentOrder(orderData.data);
        setShowPaymentModal(true);
      } else {
        const errorData = await response.json();
        alert(`创建订单失败: ${errorData.detail || '未知错误'}`);
      }
    } catch (error) {
      console.error('购买失败:', error);
      alert('购买失败，请稍后重试');
    }
  };

  const handlePaymentSuccess = () => {
    alert('支付成功！积分已到账');
  };

  const requestPaymentMethod = (pkg: PackageData) => {
    setPendingPackage(pkg);
    setShowMethodSelector(true);
  };

  const handleSelectPaymentMethod = (method: 'wechat' | 'alipay') => {
    if (!pendingPackage) return;
    setShowMethodSelector(false);
    handlePurchase(pendingPackage.package_id, method);
  };

  const formatPrice = (value: number) => {
    if (value === 0) return '¥0';
    return `¥${value.toLocaleString()}`;
  };

  const renderPrivileges = (privileges: string[]) => {
    if (!privileges || privileges.length === 0) {
      return (
        <div className="flex items-center text-sm text-gray-600">
          <span className="mr-2 text-green-500">✓</span>
          <span>购买后立即生效，随时可用</span>
        </div>
      );
    }

    return privileges.map((privilege, index) => (
      <div key={`${privilege}-${index}`} className="flex items-center text-sm text-gray-600">
        <span className="mr-2 text-green-500">✓</span>
        <span>{privilege}</span>
      </div>
    ));
  };

  const renderPackageGrid = (pkgList: PackageData[]) => {
    if (pkgList.length === 0) {
      return (
        <div className="rounded-2xl border border-dashed border-gray-200 bg-gray-50 px-6 py-10 text-center text-gray-500">
          暂无可购买的套餐
        </div>
      );
    }

    return (
      <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-4">
        {pkgList.map((pkg, index) => {
          const isHighlighted = pkg.recommended || pkg.popular || index === 0;
          return (
            <div
              key={pkg.id}
              className={`relative flex h-full flex-col rounded-2xl border bg-white p-6 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-xl ${
                isHighlighted ? 'border-blue-300 ring-1 ring-blue-200' : 'border-gray-200'
              }`}
            >
              {(pkg.popular || pkg.recommended) && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-gradient-to-r from-red-500 to-orange-500 px-4 py-1 text-xs font-semibold text-white shadow">
                  推荐
                </div>
              )}

              <div className="text-center flex flex-col flex-1">
                <p className="text-sm text-gray-500">{pkg.category === 'membership' ? '会员长效权益' : '积分灵活使用'}</p>
                <h4 className="mt-2 text-2xl font-bold text-gray-900">{pkg.name}</h4>
                <div className="mt-4 flex flex-col items-center space-y-1">
                  <span className="text-4xl font-extrabold text-gray-900">{formatPrice(pkg.price_yuan)}</span>
                  <span className="text-sm text-gray-500">
                    赠送 {pkg.bonus_credits.toLocaleString()} 积分 · 实得 {pkg.total_credits.toLocaleString()} 积分
                  </span>
                  <span className="text-sm font-medium text-green-600">每元 {pkg.credits_per_yuan.toFixed(2)} 积分</span>
                </div>
                <div className="mt-6 space-y-2 text-left w-full">{renderPrivileges(pkg.privileges)}</div>
              </div>

              <button
                onClick={() => requestPaymentMethod(pkg)}
                className="mt-6 w-full rounded-xl bg-gradient-to-r from-blue-500 to-blue-600 py-3 text-base font-semibold text-white shadow hover:from-blue-600 hover:to-blue-700"
              >
                立即开通
              </button>
            </div>
          );
        })}
      </div>
    );
  };

  if (!isLoggedIn) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4">
        <div className="w-full max-w-md rounded-2xl bg-white p-8 text-center shadow-xl">
          <h3 className="text-xl font-bold text-gray-900">需要登录</h3>
          <p className="mt-2 text-sm text-gray-600">请先登录后再查看套餐信息</p>
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            {onLogin && (
              <button
                onClick={() => {
                  onClose();
                  onLogin();
                }}
                className="rounded-lg bg-blue-600 px-6 py-2 text-white shadow hover:bg-blue-700"
              >
                去登录
              </button>
            )}
            <button
              onClick={onClose}
              className="rounded-lg bg-gray-100 px-6 py-2 text-gray-700 shadow hover:bg-gray-200"
            >
              取消
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-3 py-6">
      <div className="flex w-full max-w-6xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl">
        <div className="border-b border-gray-100 px-6 py-5 md:px-10 md:py-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-blue-500">选择套餐</p>
              <h2 className="mt-1 text-2xl font-bold text-gray-900">会员 / 积分套餐</h2>
            </div>
            <button
              onClick={onClose}
              className="flex h-9 w-9 items-center justify-center rounded-full bg-gray-100 text-lg text-gray-500 transition hover:bg-gray-200"
            >
              ×
            </button>
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            {TABS.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`rounded-full px-5 py-2 text-sm font-medium transition ${
                  activeTab === tab.key
                    ? 'bg-blue-600 text-white shadow'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* 支付方式放到下单弹窗内选择 */}
        </div>

        <div className="space-y-8 px-6 py-6 md:px-10 md:py-8">
          {activeTab === 'membership' && (
            <>
              <h3 className="text-lg font-semibold text-gray-900">包月会员</h3>
              {renderPackageGrid(membershipPackages)}
            </>
          )}

          {activeTab === 'discount' && (
            <>
              <h3 className="text-lg font-semibold text-gray-900">积分套餐</h3>
              {renderPackageGrid(discountPackages)}
            </>
          )}

          <div className="rounded-2xl bg-gray-50 px-6 py-4 text-sm text-gray-600">
            <p>• 积分永不过期，支付后立即到账，可用于所有 AI 功能。</p>
            <p>• 交易会同步到账户中心，方便随时查看和开票。</p>
          </div>
        </div>
      </div>

      {showPaymentModal && currentOrder && (
        <PaymentModal
          orderInfo={currentOrder}
          onClose={() => setShowPaymentModal(false)}
          onPaymentSuccess={handlePaymentSuccess}
        />
      )}

      {showMethodSelector && pendingPackage && (
        <div className="fixed inset-0 z-60 flex items-center justify-center bg-black/60 px-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
            <h3 className="text-xl font-bold text-gray-900">选择支付方式</h3>
            <p className="mt-2 text-sm text-gray-600">{pendingPackage.name}</p>
            <div className="mt-6 grid grid-cols-1 gap-3">
              <button
                onClick={() => handleSelectPaymentMethod('wechat')}
                className="flex items-center justify-between rounded-xl border border-gray-200 px-4 py-3 text-base font-semibold text-gray-800 hover:border-blue-400"
              >
                <span className="flex items-center gap-3">
                  <PaymentIcon type="wechat" />
                  微信支付
                </span>
                <span className="text-xs text-gray-400">推荐</span>
              </button>
              <button
                onClick={() => handleSelectPaymentMethod('alipay')}
                className="flex items-center justify-between rounded-xl border border-gray-200 px-4 py-3 text-base font-semibold text-gray-800 hover:border-blue-400"
              >
                <span className="flex items-center gap-3">
                  <PaymentIcon type="alipay" />
                  支付宝
                </span>
              </button>
            </div>
            <div className="mt-4 flex justify-end">
              <button
                onClick={() => {
                  setShowMethodSelector(false);
                  setPendingPackage(null);
                }}
                className="rounded-lg bg-gray-100 px-4 py-2 text-sm text-gray-600 hover:bg-gray-200"
              >
                取消
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PricingModal;
