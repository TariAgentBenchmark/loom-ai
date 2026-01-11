'use client';

import React, { useState, useEffect, useCallback } from 'react';
import PaymentModal from './PaymentModal';

interface Package {
  id: number;
  package_id: string;
  name: string;
  category: string;
  description: string;
  price_yuan: number;
  bonus_credits: number;
  total_credits: number;
  refund_policy: string;
  refund_deduction_rate: number;
  privileges: string[];
  popular: boolean;
  recommended: boolean;
  sort_order: number;
  credits_per_yuan: number;
  is_refundable: boolean;
  refund_amount_yuan: number;
}


interface MembershipPricingModalProps {
  onClose: () => void;
  accessToken?: string;
  onLogin?: () => void;
}

const MembershipPricingModal: React.FC<MembershipPricingModalProps> = ({ onClose, accessToken, onLogin }) => {
  const [activeTab, setActiveTab] = useState<'membership' | 'discount'>('membership');
  const [packages, setPackages] = useState<Package[]>([]);
  const [loading, setLoading] = useState(true);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [selectedPackage, setSelectedPackage] = useState<Package | null>(null);

  const fetchPackages = useCallback(async () => {
    try {
      const headers = accessToken ? { Authorization: `Bearer ${accessToken}` } : undefined;
      const endpoint = accessToken ? '/api/v1/membership/packages' : '/api/v1/membership/public/packages';
      const response = await fetch(endpoint, { headers });
      if (response.ok) {
        const data = await response.json();
        setPackages(data);
      } else if (response.status === 401 || response.status === 403) {
        alert('登录状态已失效，请重新登录后再试');
        onLogin?.();
        onClose();
      }
    } catch (error) {
      console.error('获取套餐失败:', error);
    } finally {
      setLoading(false);
    }
  }, [accessToken, onClose, onLogin]);

  useEffect(() => {
    fetchPackages();
  }, [fetchPackages]);

  const membershipPackages = packages.filter(pkg => pkg.category === 'membership');
  const discountPackages = packages.filter(pkg => pkg.category === 'discount');

  const handlePurchase = (pkg: Package) => {
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
    // 支付成功后的处理
    console.log('支付成功，刷新用户信息');
    // 这里可以刷新用户积分等信息
    alert('支付成功！积分已到账');
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl p-8">
          <div className="text-center">加载中...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-2 md:p-4">
      <div className="bg-white rounded-xl md:rounded-2xl shadow-2xl w-full max-w-6xl max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-4 md:px-8 py-4 md:py-6 rounded-t-xl md:rounded-t-2xl">
          <div className="flex items-center justify-between">
            <h2 className="text-lg md:text-2xl font-bold text-gray-900">会员与价格体系</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-xl md:text-2xl font-light"
            >
              ×
            </button>
          </div>

          <div className="flex gap-8 mt-6">
            <button
              onClick={() => setActiveTab('membership')}
              className={`pb-2 border-b-2 transition ${
                activeTab === 'membership'
                  ? 'text-blue-600 border-blue-600 font-medium'
                  : 'text-gray-600 hover:text-blue-600 border-transparent hover:border-blue-600'
              }`}
            >
              会员套餐
            </button>
            <button
              onClick={() => setActiveTab('discount')}
              className={`pb-2 border-b-2 transition ${
                activeTab === 'discount'
                  ? 'text-blue-600 border-blue-600 font-medium'
                  : 'text-gray-600 hover:text-blue-600 border-transparent hover:border-blue-600'
              }`}
            >
              积分套餐
            </button>
          </div>

        </div>

        <div className="px-4 md:px-8 py-4 md:py-8">

          {activeTab === 'membership' && (
            <div>
              <h3 className="text-xl font-bold text-gray-900 mb-4">👑 会员套餐</h3>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {membershipPackages.map((pkg) => (
                  <div
                    key={pkg.id}
                    className={`bg-white rounded-xl p-6 border-2 ${
                      pkg.popular ? 'border-yellow-400' : 'border-gray-200'
                    } relative`}
                  >
                    {pkg.popular && (
                      <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                        <span className="bg-yellow-500 text-white px-4 py-1 rounded-full text-sm font-medium">
                          推荐
                        </span>
                      </div>
                    )}

                    <div className="text-center mb-6">
                      <h4 className="text-xl font-bold text-gray-900 mb-2">{pkg.name}</h4>
                      <div className="rounded-md bg-blue-100 px-4 py-2 text-3xl font-extrabold text-blue-600 mb-3">
                        {pkg.total_credits} 积分
                      </div>
                      <div className="rounded-md bg-blue-50 px-3 py-1 text-lg text-gray-700 mb-2">
                        ¥{pkg.price_yuan}
                      </div>
                      <div className="text-sm text-gray-600">
                        {pkg.bonus_credits > 0 ? `赠送 ${pkg.bonus_credits} 积分` : ''}
                      </div>
                      
                    </div>

                    <button
                      onClick={() => handlePurchase(pkg)}
                      className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg font-medium mb-4 transition"
                    >
                      立即购买
                    </button>

                    <div className="space-y-2 text-sm">
                      {pkg.privileges.map((privilege, index) => (
                        <div key={index} className="flex items-center">
                          <span className="text-green-500 mr-2">✓</span>
                          <span className="text-gray-700">{privilege}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'discount' && (
            <div>
              <h3 className="text-xl font-bold text-gray-900 mb-4">💰 积分套餐</h3>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {discountPackages.map((pkg) => (
                  <div
                    key={pkg.id}
                    className={`bg-white rounded-xl p-6 border-2 ${
                      pkg.popular ? 'border-yellow-400 bg-yellow-50' : 'border-gray-200'
                    } relative`}
                  >
                    {pkg.popular && (
                      <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                        <span className="bg-yellow-500 text-white px-4 py-1 rounded-full text-sm font-medium">
                          推荐
                        </span>
                      </div>
                    )}

                    <div className="text-center mb-6">
                      <h4 className="text-xl font-bold text-gray-900 mb-2">{pkg.name}</h4>
                      <div className="rounded-md bg-blue-100 px-4 py-2 text-3xl font-extrabold text-blue-600 mb-3">
                        {pkg.total_credits} 积分
                      </div>
                      <div className="rounded-md bg-blue-50 px-3 py-1 text-lg text-gray-700 mb-2">
                        ¥{pkg.price_yuan}
                      </div>
                      <div className="text-sm text-gray-600">
                        {pkg.bonus_credits > 0 ? `赠送 ${pkg.bonus_credits} 积分` : ''}
                      </div>
                      
                    </div>

                    <button
                      onClick={() => handlePurchase(pkg)}
                      className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg font-medium mb-4 transition"
                    >
                      立即购买
                    </button>

                    <div className="space-y-2 text-sm">
                      {pkg.privileges.map((privilege, index) => (
                        <div key={index} className="flex items-center">
                          <span className="text-green-500 mr-2">✓</span>
                          <span className="text-gray-700">{privilege}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}


          {/* 总结说明 */}
          <div className="mt-8 p-4 bg-gray-50 rounded-lg">
            <h4 className="text-lg font-semibold text-gray-900 mb-2">📌 总结说明</h4>
            <ul className="text-sm text-gray-700 space-y-1">
              <li>• 积分永不过期</li>
            </ul>
          </div>
        </div>
      </div>

      {/* 支付弹窗 */}
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

export default MembershipPricingModal;
