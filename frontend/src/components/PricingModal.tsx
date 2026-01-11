'use client';

import React, { useEffect, useState } from 'react';
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
  accessToken?: string;
}

const PricingModal: React.FC<PricingModalProps> = ({
  onClose,
  isLoggedIn = false,
  onLogin,
  accessToken,
}) => {
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [selectedPackage, setSelectedPackage] = useState<PackageData | null>(null);

  const membershipPackages = membershipPackageData;
  const discountPackages = discountPackageData;

  // 防止弹窗打开时背景滚动
  useEffect(() => {
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = prev;
    };
  }, []);

  const handlePurchase = (pkg: PackageData) => {
    if (!accessToken) {
      alert('登录状态已失效，请重新登录后再试');
      onClose();
      onLogin?.();
      return;
    }

    setSelectedPackage(pkg);
    setShowPaymentModal(true);
  };

  const handlePaymentSuccess = () => {
    alert('支付成功！积分已到账');
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
          const isHighlighted = pkg.recommended || pkg.popular;
          return (
            <div
              key={pkg.id}
              className={`relative flex h-full flex-col rounded-2xl border bg-white p-6 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-xl ${
                isHighlighted ? 'border-blue-300 ring-1 ring-blue-200' : 'border-gray-200'
              }`}
            >
              {(pkg.popular || pkg.recommended) && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-gradient-to-r from-orange-500 to-red-500 px-4 py-1 text-xs font-semibold text-white shadow">
                  推荐
                </div>
              )}

              <div className="text-center flex flex-col flex-1">
                <p className="text-sm text-gray-500">{pkg.category === 'membership' ? '积分灵活使用' : '积分灵活使用'}</p>
                <h4 className="mt-2 text-2xl font-bold text-gray-900">{pkg.name}</h4>
                <div className="mt-4 flex flex-col items-center gap-2">
                  <div className="flex items-baseline justify-center gap-2">
                    <span className="rounded-md border-2 border-blue-300 bg-blue-100 px-4 py-2 text-2xl font-bold text-blue-600 shadow">
                      {pkg.total_credits} 积分
                    </span>
                  </div>
                  <div className="rounded-md bg-blue-50 px-3 py-1 text-sm text-gray-700">
                    {formatPrice(pkg.price_yuan)}
                    {pkg.bonus_credits > 0 && ` · 送 ${Math.round((pkg.bonus_credits / Math.max(pkg.price_yuan, 1)) * 100)}%`}
                  </div>
                </div>
                <div className="mt-6 space-y-2 text-left w-full">{renderPrivileges(pkg.privileges)}</div>
              </div>

              <button
                onClick={() => handlePurchase(pkg)}
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
      <div className="flex w-full max-w-6xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl max-h-[90vh]">
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
        </div>

        <div className="space-y-8 px-6 py-6 md:px-10 md:py-8 overflow-y-auto">
          <div className="space-y-6">
            <div className="space-y-3">
              <h3 className="text-lg font-semibold text-gray-900">积分套餐</h3>
              {renderPackageGrid(discountPackages)}
            </div>
            <div className="space-y-3">
              <h3 className="text-lg font-semibold text-gray-900">会员套餐</h3>
              {renderPackageGrid(membershipPackages)}
            </div>
            <div className="rounded-2xl bg-gray-50 px-6 py-4 text-sm text-gray-600">
              <p>1. 积分永不过期。</p>
              <p>2. 优惠套餐不可退款；会员套餐如需退款请联系客服（赠送部分不退）。</p>
            </div>
          </div>
        </div>
      </div>

      {showPaymentModal && selectedPackage && (
        <PaymentModal
          packageInfo={{
            packageId: selectedPackage.package_id,
            packageName: selectedPackage.name,
            priceYuan: selectedPackage.price_yuan,
            totalCredits: selectedPackage.total_credits,
          }}
          onClose={() => setShowPaymentModal(false)}
          onPaymentSuccess={handlePaymentSuccess}
          accessToken={accessToken}
        />
      )}

    </div>
  );
};

export default PricingModal;
