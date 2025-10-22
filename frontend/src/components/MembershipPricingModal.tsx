'use client';

import React, { useState, useEffect } from 'react';

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

interface Service {
  id: number;
  service_id: string;
  service_name: string;
  service_key: string;
  description: string;
  price_credits: number;
  active: boolean;
}

interface MembershipPricingModalProps {
  onClose: () => void;
}

const MembershipPricingModal: React.FC<MembershipPricingModalProps> = ({ onClose }) => {
  const [activeTab, setActiveTab] = useState<'membership' | 'discount' | 'services'>('membership');
  const [packages, setPackages] = useState<Package[]>([]);
  const [services, setServices] = useState<Service[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPackages();
    fetchServices();
  }, []);

  const fetchPackages = async () => {
    try {
      const response = await fetch('/api/v1/membership/packages');
      if (response.ok) {
        const data = await response.json();
        setPackages(data);
      }
    } catch (error) {
      console.error('获取套餐失败:', error);
    }
  };

  const fetchServices = async () => {
    try {
      const response = await fetch('/api/v1/membership/services');
      if (response.ok) {
        const data = await response.json();
        setServices(data);
      }
    } catch (error) {
      console.error('获取服务价格失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const membershipPackages = packages.filter(pkg => pkg.category === 'membership');
  const discountPackages = packages.filter(pkg => pkg.category === 'discount');

  const handlePurchase = async (packageId: string) => {
    // 这里实现购买逻辑
    console.log('购买套餐:', packageId);
    // 实际实现中会调用支付API
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

          <div className="flex flex-wrap gap-2 md:gap-8 mt-4 md:mt-6">
            <button
              onClick={() => setActiveTab('membership')}
              className={`pb-2 border-b-2 transition text-sm md:text-base ${
                activeTab === 'membership'
                  ? 'text-blue-600 border-blue-600 font-medium'
                  : 'text-gray-600 hover:text-blue-600 border-transparent hover:border-blue-600'
              }`}
            >
              会员套餐
            </button>
            <button
              onClick={() => setActiveTab('discount')}
              className={`pb-2 border-b-2 transition text-sm md:text-base ${
                activeTab === 'discount'
                  ? 'text-blue-600 border-blue-600 font-medium'
                  : 'text-gray-600 hover:text-blue-600 border-transparent hover:border-blue-600'
              }`}
            >
              优惠套餐
            </button>
            <button
              onClick={() => setActiveTab('services')}
              className={`pb-2 border-b-2 transition text-sm md:text-base ${
                activeTab === 'services'
                  ? 'text-blue-600 border-blue-600 font-medium'
                  : 'text-gray-600 hover:text-blue-600 border-transparent hover:border-blue-600'
              }`}
            >
              服务项目
            </button>
          </div>
        </div>

        <div className="px-4 md:px-8 py-4 md:py-8">
          {/* 兑换说明 */}
          <div className="mb-6 p-4 bg-blue-50 rounded-lg">
            <h3 className="text-lg font-semibold text-blue-800 mb-2">🧾 积分与人民币兑换</h3>
            <p className="text-blue-700">1 元 = 1 积分</p>
          </div>

          {/* 新用户福利 */}
          <div className="mb-6 p-4 bg-green-50 rounded-lg">
            <h3 className="text-lg font-semibold text-green-800 mb-2">👤 新用户福利</h3>
            <p className="text-green-700">赠送 10 积分</p>
          </div>

          {activeTab === 'membership' && (
            <div>
              <h3 className="text-xl font-bold text-gray-900 mb-4">👑 会员套餐（可退款）</h3>
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
                      <div className="text-4xl font-bold text-gray-900 mb-2">
                        ¥{pkg.price_yuan}
                      </div>
                      <div className="text-sm text-gray-600">
                        赠送 {pkg.bonus_credits} 积分 | 实得 {pkg.total_credits} 积分
                      </div>
                      <div className="text-sm text-green-600 mt-1">
                        每元获得 {pkg.credits_per_yuan.toFixed(2)} 积分
                      </div>
                    </div>

                    <button
                      onClick={() => handlePurchase(pkg.package_id)}
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

                    {pkg.is_refundable && (
                      <div className="mt-4 p-3 bg-yellow-50 rounded-lg">
                        <p className="text-sm text-yellow-800">
                          💰 可退款：退款金额 ¥{pkg.refund_amount_yuan}（扣除{pkg.refund_deduction_rate * 100}%）
                        </p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'discount' && (
            <div>
              <h3 className="text-xl font-bold text-gray-900 mb-4">💰 优惠套餐（不可退款）</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {discountPackages.map((pkg) => (
                  <div
                    key={pkg.id}
                    className="bg-white rounded-xl p-4 border border-gray-200 text-center"
                  >
                    <h4 className="text-lg font-bold text-gray-900 mb-2">{pkg.name}</h4>
                    <div className="text-3xl font-bold text-gray-900 mb-2">
                      ¥{pkg.price_yuan}
                    </div>
                    <div className="text-sm text-gray-600 mb-4">
                      实得 {pkg.total_credits} 积分
                    </div>

                    <button
                      onClick={() => handlePurchase(pkg.package_id)}
                      className="w-full bg-green-600 hover:bg-green-700 text-white py-2 rounded-lg font-medium mb-3 transition"
                    >
                      立即购买
                    </button>

                    <div className="space-y-1 text-xs">
                      {pkg.privileges.map((privilege, index) => (
                        <div key={index} className="flex items-center justify-center">
                          <span className="text-green-500 mr-1">✓</span>
                          <span className="text-gray-700">{privilege}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'services' && (
            <div>
              <h3 className="text-xl font-bold text-gray-900 mb-4">🛠️ 服务项目与积分价格</h3>
              <div className="bg-gray-50 rounded-lg p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {services.map((service) => (
                    <div
                      key={service.id}
                      className="bg-white rounded-lg p-4 border border-gray-200"
                    >
                      <div className="flex justify-between items-center">
                        <div>
                          <h5 className="font-semibold text-gray-900">{service.service_name}</h5>
                          <p className="text-sm text-gray-600">{service.description}</p>
                        </div>
                        <div className="text-lg font-bold text-blue-600">
                          {service.price_credits} 积分
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* 总结说明 */}
          <div className="mt-8 p-4 bg-gray-50 rounded-lg">
            <h4 className="text-lg font-semibold text-gray-900 mb-2">📌 总结说明</h4>
            <ul className="text-sm text-gray-700 space-y-1">
              <li>• 积分永不过期</li>
              <li>• 会员套餐可退款（扣除20%充值金额）</li>
              <li>• 优惠套餐不可退款</li>
              <li>• 新用户赠送10积分</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MembershipPricingModal;