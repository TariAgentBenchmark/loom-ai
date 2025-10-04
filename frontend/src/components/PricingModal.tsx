'use client';

import React from 'react';
import { PricingTab, pricingTabs } from '../lib/pricing';

interface PricingModalProps {
  activeTab: PricingTab;
  onChangeTab: (tab: PricingTab) => void;
  onClose: () => void;
}

const PricingModal: React.FC<PricingModalProps> = ({ activeTab, onChangeTab, onClose }) => (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div className="bg-white rounded-2xl shadow-2xl w-full max-w-6xl max-h-[90vh] overflow-y-auto">
      <div className="sticky top-0 bg-white border-b border-gray-200 px-8 py-6 rounded-t-2xl">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">选择套餐</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl font-light"
          >
            ×
          </button>
        </div>

        <div className="flex space-x-8 mt-6">
          {pricingTabs.map((tab) => (
            <button
              key={tab}
              onClick={() => onChangeTab(tab)}
              className={`pb-2 border-b-2 transition ${
                activeTab === tab
                  ? 'text-blue-600 border-blue-600 font-medium'
                  : 'text-gray-600 hover:text-blue-600 border-transparent hover:border-blue-600'
              }`}
            >
              {tab}
            </button>
          ))}
          <button className="ml-auto text-blue-600 hover:text-blue-700 text-sm">联系方式</button>
        </div>
      </div>

      <div className="px-8 py-8">
        {activeTab === '包月会员' && (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
            <div className="bg-gray-50 rounded-2xl p-6 relative">
              <div className="text-center mb-6">
                <h3 className="text-xl font-bold text-gray-900 mb-2">试用体验</h3>
                <div className="text-4xl font-bold text-gray-900 mb-1">
                  <span className="text-xl">¥</span>0
                </div>
                <p className="text-sm text-gray-500">免费试用高级智能设计体验</p>
              </div>

              <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-medium mb-6 transition">
                立即开通
              </button>

              <div className="space-y-3 text-sm">
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">赠送200算力积分</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">7天内有效</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">循环图案处理</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">定位花提取</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">高清放大</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">毛线刺绣增强</span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-2xl p-6 border-2 border-blue-200 relative">
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                <span className="bg-red-500 text-white px-4 py-1 rounded-full text-sm font-medium">限时优惠</span>
              </div>

              <div className="text-center mb-6">
                <h3 className="text-xl font-bold text-gray-900 mb-2">轻享版</h3>
                <div className="text-4xl font-bold text-gray-900 mb-1">
                  <span className="text-xl">¥</span>29
                </div>
                <p className="text-sm text-gray-400 line-through">原价49</p>
              </div>

              <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-medium mb-6 transition">
                立即开通
              </button>

              <div className="space-y-3 text-sm">
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">每月3000算力积分</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">AI应用高速队列</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">循环图案处理</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">定位花提取</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">高清放大</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">矢量风格转换</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">毛线刺绣增强</span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-2xl p-6 border-2 border-blue-200 relative">
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                <span className="bg-red-500 text-white px-4 py-1 rounded-full text-sm font-medium">限时优惠</span>
              </div>

              <div className="text-center mb-6">
                <h3 className="text-xl font-bold text-gray-900 mb-2">基础版</h3>
                <div className="text-4xl font-bold text-gray-900 mb-1">
                  <span className="text-xl">¥</span>69
                </div>
                <p className="text-sm text-gray-400 line-through">原价119</p>
              </div>

              <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-medium mb-6 transition">
                立即开通
              </button>

              <div className="space-y-3 text-sm">
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">每月6000算力积分</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">AI应用高速队列</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">循环图案处理</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">定位花提取</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">高清放大</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">矢量风格转换</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">毛线刺绣增强</span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-2xl p-6 border-2 border-blue-200 relative">
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                <span className="bg-green-500 text-white px-4 py-1 rounded-full text-sm font-medium">尊享版</span>
              </div>

              <div className="text-center mb-6">
                <h3 className="text-xl font-bold text-gray-900 mb-2">尊享版</h3>
                <div className="text-4xl font-bold text-gray-900 mb-1">
                  <span className="text-xl">¥</span>129
                </div>
                <p className="text-sm text-gray-400 line-through">原价199</p>
              </div>

              <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-medium mb-6 transition">
                立即开通
              </button>

              <div className="space-y-3 text-sm">
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">每月11000算力积分</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">AI应用高速队列</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">循环图案处理</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">定位花提取</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">矢量风格转换</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">进一步处理</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">高清放大</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">超级高速队列</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">自定义处理指令</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">毛线刺绣增强</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === '优惠套餐' && (
          <div className="text-center py-16">
            <div className="text-6xl mb-4">🎁</div>
            <h3 className="text-2xl font-bold text-gray-900 mb-2">优惠套餐</h3>
            <p className="text-gray-600">特价优惠套餐即将推出，敬请期待！</p>
          </div>
        )}

        {activeTab === '季度会员' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-2xl p-6 border-2 border-blue-200 relative">
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                <span className="bg-green-500 text-white px-4 py-1 rounded-full text-sm font-medium">季度优惠</span>
              </div>

              <div className="text-center mb-6">
                <h3 className="text-xl font-bold text-gray-900 mb-2">轻享季度版</h3>
                <div className="text-4xl font-bold text-gray-900 mb-1">
                  <span className="text-xl">¥</span>79
                </div>
                <p className="text-sm text-gray-400 line-through">原价129</p>
                <p className="text-xs text-gray-500 mt-1">3个月套餐</p>
              </div>

              <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-medium mb-6 transition">
                立即开通
              </button>

              <div className="space-y-2 text-sm">
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">每月8000算力积分</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">所有基础功能</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">矢量风格转换</span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-2xl p-6 border-2 border-blue-200 relative">
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                <span className="bg-green-500 text-white px-4 py-1 rounded-full text-sm font-medium">最受欢迎</span>
              </div>

              <div className="text-center mb-6">
                <h3 className="text-xl font-bold text-gray-900 mb-2">标准季度版</h3>
                <div className="text-4xl font-bold text-gray-900 mb-1">
                  <span className="text-xl">¥</span>179
                </div>
                <p className="text-sm text-gray-400 line-through">原价239</p>
                <p className="text-xs text-gray-500 mt-1">3个月套餐</p>
              </div>

              <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-medium mb-6 transition">
                立即开通
              </button>

              <div className="space-y-2 text-sm">
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">每月20000算力积分</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">所有功能无限制</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">优先处理队列</span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-2xl p-6 border-2 border-blue-200 relative">
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                <span className="bg-purple-500 text-white px-4 py-1 rounded-full text-sm font-medium">专业版</span>
              </div>

              <div className="text-center mb-6">
                <h3 className="text-xl font-bold text-gray-900 mb-2">专业季度版</h3>
                <div className="text-4xl font-bold text-gray-900 mb-1">
                  <span className="text-xl">¥</span>259
                </div>
                <p className="text-sm text-gray-400 line-through">原价359</p>
                <p className="text-xs text-gray-500 mt-1">3个月套餐</p>
              </div>

              <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-medium mb-6 transition">
                立即开通
              </button>

              <div className="space-y-2 text-sm">
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">每月30000算力积分</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">专业功能全解锁</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">超级高速队列</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === '包年会员' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-2xl p-6 border-2 border-blue-200 relative">
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                <span className="bg-yellow-500 text-white px-4 py-1 rounded-full text-sm font-medium">超值年费</span>
              </div>

              <div className="text-center mb-6">
                <h3 className="text-xl font-bold text-gray-900 mb-2">标准年费版</h3>
                <div className="text-4xl font-bold text-gray-900 mb-1">
                  <span className="text-xl">¥</span>299
                </div>
                <p className="text-sm text-gray-400 line-through">原价588</p>
                <p className="text-xs text-gray-500 mt-1">12个月套餐</p>
              </div>

              <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-medium mb-6 transition">
                立即开通
              </button>

              <div className="space-y-2 text-sm">
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">每月12000算力积分</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">所有功能无限制</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">专属客户经理</span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-2xl p-6 border-2 border-blue-200 relative">
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                <span className="bg-yellow-500 text-white px-4 py-1 rounded-full text-sm font-medium">企业版</span>
              </div>

              <div className="text-center mb-6">
                <h3 className="text-xl font-bold text-gray-900 mb-2">尊享年费版</h3>
                <div className="text-4xl font-bold text-gray-900 mb-1">
                  <span className="text-xl">¥</span>499
                </div>
                <p className="text-sm text-gray-400 line-through">原价899</p>
                <p className="text-xs text-gray-500 mt-1">12个月套餐</p>
              </div>

              <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-medium mb-6 transition">
                立即开通
              </button>

              <div className="space-y-2 text-sm">
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">每月30000算力积分</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">无限协作成员</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">专属技术支持</span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-2xl p-6 border-2 border-blue-200 relative">
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                <span className="bg-purple-500 text-white px-4 py-1 rounded-full text-sm font-medium">旗舰版</span>
              </div>

              <div className="text-center mb-6">
                <h3 className="text-xl font-bold text-gray-900 mb-2">旗舰年费版</h3>
                <div className="text-4xl font-bold text-gray-900 mb-1">
                  <span className="text-xl">¥</span>899
                </div>
                <p className="text-sm text-gray-400 line-through">原价1299</p>
                <p className="text-xs text-gray-500 mt-1">12个月套餐</p>
              </div>

              <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-medium mb-6 transition">
                立即开通
              </button>

              <div className="space-y-2 text-sm">
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">每月60000算力积分</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">定制化功能开发</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">专属成功经理</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === '算力充值' && (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
            <div className="bg-white rounded-2xl p-6 border border-gray-200">
              <div className="text-center mb-6">
                <h3 className="text-xl font-bold text-gray-900 mb-2">基础算力包</h3>
                <div className="text-4xl font-bold text-gray-900 mb-1">
                  <span className="text-xl">¥</span>19
                </div>
                <p className="text-sm text-gray-500">1000算力积分</p>
              </div>

              <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-medium mb-4 transition">
                立即购买
              </button>

              <div className="text-xs text-gray-500 text-center">适合偶尔使用</div>
            </div>

            <div className="bg-white rounded-2xl p-6 border-2 border-blue-200 relative">
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                <span className="bg-blue-500 text-white px-4 py-1 rounded-full text-sm font-medium">推荐</span>
              </div>

              <div className="text-center mb-6">
                <h3 className="text-xl font-bold text-gray-900 mb-2">标准算力包</h3>
                <div className="text-4xl font-bold text-gray-900 mb-1">
                  <span className="text-xl">¥</span>49
                </div>
                <p className="text-sm text-gray-500">3000算力积分</p>
              </div>

              <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-medium mb-4 transition">
                立即购买
              </button>

              <div className="text-xs text-gray-500 text-center">性价比最高</div>
            </div>

            <div className="bg-white rounded-2xl p-6 border border-gray-200">
              <div className="text-center mb-6">
                <h3 className="text-xl font-bold text-gray-900 mb-2">专业算力包</h3>
                <div className="text-4xl font-bold text-gray-900 mb-1">
                  <span className="text-xl">¥</span>99
                </div>
                <p className="text-sm text-gray-500">7000算力积分</p>
              </div>

              <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-medium mb-4 transition">
                立即购买
              </button>

              <div className="text-xs text-gray-500 text-center">适合专业用户</div>
            </div>

            <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-2xl p-6 border-2 border-purple-200 relative">
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                <span className="bg-purple-500 text-white px-4 py-1 rounded-full text-sm font-medium">超值</span>
              </div>

              <div className="text-center mb-6">
                <h3 className="text-xl font-bold text-gray-900 mb-2">企业算力包</h3>
                <div className="text-4xl font-bold text-gray-900 mb-1">
                  <span className="text-xl">¥</span>199
                </div>
                <p className="text-sm text-gray-500">15000算力积分</p>
              </div>

              <button className="w-full bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white py-3 rounded-xl font-medium mb-4 transition">
                立即购买
              </button>

              <div className="text-xs text-gray-500 text-center">企业团队首选</div>
            </div>
          </div>
        )}

        {(activeTab === '包月会员' || activeTab === '季度会员' || activeTab === '包年会员') && (
          <div className="mt-8 text-xs text-gray-500 space-y-2">
            <p>1. 算力积分有效期：包套餐购买的算力积分，有效期为一年，如果有效期内未使用算力积分，将自动失效。</p>
            <p>2. 取消续费：第三方支付的套餐，用户可在支付管理中心，取消自动续费。</p>
          </div>
        )}

        {activeTab === '算力充值' && (
          <div className="mt-8 text-xs text-gray-500 space-y-2">
            <p>1. 算力积分永久有效：单独购买的算力积分永久有效，不会过期。</p>
            <p>2. 支付方式：支持微信支付、支付宝等多种支付方式。</p>
            <p>3. 发票服务：企业用户可联系客服开具发票。</p>
          </div>
        )}
      </div>
    </div>
  </div>
);

export default PricingModal;
