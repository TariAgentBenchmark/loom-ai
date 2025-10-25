'use client';

import React, { useState, useEffect } from 'react';
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
}

const MembershipPricingModal: React.FC<MembershipPricingModalProps> = ({ onClose }) => {
  const [activeTab, setActiveTab] = useState<'membership' | 'discount'>('membership');
  const [packages, setPackages] = useState<Package[]>([]);
  const [loading, setLoading] = useState(true);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [currentOrder, setCurrentOrder] = useState<any>(null);
  const [selectedPaymentMethod, setSelectedPaymentMethod] = useState<'wechat' | 'alipay'>('wechat');

  useEffect(() => {
    fetchPackages();
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
    } finally {
      setLoading(false);
    }
  };

  const membershipPackages = packages.filter(pkg => pkg.category === 'membership');
  const discountPackages = packages.filter(pkg => pkg.category === 'discount');

  const handlePurchase = async (packageId: string) => {
    try {
      console.log('开始购买套餐:', packageId);

      // 创建订单
      const response = await fetch('/api/v1/payment/orders', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          package_id: packageId,
          payment_method: selectedPaymentMethod,
          quantity: 1
        }),
      });

      if (response.ok) {
        const orderData = await response.json();
        console.log('订单创建成功:', orderData);

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

          {/* 支付方式选择 */}
          <div className="mt-4">
            <div className="text-sm font-medium text-gray-700 mb-2">支付方式</div>
            <div className="flex gap-4">
              <label className="flex items-center">
                <input
                  type="radio"
                  name="paymentMethod"
                  value="wechat"
                  checked={selectedPaymentMethod === 'wechat'}
                  onChange={(e) => setSelectedPaymentMethod(e.target.value as 'wechat' | 'alipay')}
                  className="mr-2"
                />
                微信支付
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  name="paymentMethod"
                  value="alipay"
                  checked={selectedPaymentMethod === 'alipay'}
                  onChange={(e) => setSelectedPaymentMethod(e.target.value as 'wechat' | 'alipay')}
                  className="mr-2"
                />
                支付宝
              </label>
            </div>
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
      {showPaymentModal && currentOrder && (
        <PaymentModal
          orderInfo={currentOrder}
          onClose={() => setShowPaymentModal(false)}
          onPaymentSuccess={handlePaymentSuccess}
        />
      )}
    </div>
  );
};

export default MembershipPricingModal;