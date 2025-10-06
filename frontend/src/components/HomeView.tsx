'use client';

import React, { useState } from 'react';
import {
  Bell,
  Crown,
  Download,
  History,
  User,
  Zap,
  AlertTriangle,
  Menu,
  X,
} from 'lucide-react';
import { ProcessingMethod } from '../lib/processing';

type MembershipTag = 'free' | 'basic' | 'premium' | 'enterprise' | string | undefined;

type AccountSummary = {
  credits?: number;
  monthlyProcessed?: number;
  totalProcessed?: number;
  nickname?: string;
  membershipType?: MembershipTag;
};

interface HomeViewProps {
  onSelectMethod: (method: ProcessingMethod) => void;
  onOpenPricingModal: () => void;
  onLogout?: () => void;
  onLogin: () => void;
  isLoggedIn: boolean;
  isAuthenticating: boolean;
  authError?: string;
  accountSummary?: AccountSummary;
  onOpenLoginModal: () => void;
}

const formatNumber = (value: number | undefined, fallback: string) =>
  typeof value === 'number' ? value.toLocaleString() : fallback;

const membershipLabel = (membershipType: MembershipTag) => {
  switch (membershipType) {
    case 'premium':
      return '高级会员';
    case 'enterprise':
      return '企业会员';
    case 'basic':
      return '基础会员';
    case 'free':
      return '普通用户';
    default:
      return membershipType;
  }
};

const HomeView: React.FC<HomeViewProps> = ({
  onSelectMethod,
  onOpenPricingModal,
  onLogout,
  onLogin,
  isLoggedIn,
  isAuthenticating,
  authError,
  accountSummary,
  onOpenLoginModal,
}) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const creditsLabel = formatNumber(accountSummary?.credits, isLoggedIn ? '0' : '--');
  const monthlyLabel = formatNumber(accountSummary?.monthlyProcessed, isLoggedIn ? '0' : '--');
  const totalLabel = formatNumber(accountSummary?.totalProcessed, isLoggedIn ? '0' : '--');

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
        <div className="flex items-center justify-between px-4 md:px-6 py-3 md:py-4">
          <div className="flex items-center space-x-2 md:space-x-3">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="md:hidden text-gray-500 hover:text-gray-700"
            >
              {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
            <div className="flex h-8 w-8 md:h-10 md:w-10 items-center justify-center rounded-xl overflow-hidden">
              <img src="/logo.png" alt="Logo" className="h-full w-full object-cover" />
            </div>
            <span className="text-lg md:text-xl font-bold text-gray-900">应用中心</span>
          </div>

          <div className="flex items-center space-x-2 md:space-x-4">
            <button
              onClick={onOpenPricingModal}
              className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white px-3 py-1.5 md:px-4 md:py-2 rounded-lg text-xs md:text-sm font-medium transition-all shadow-sm"
            >
              套餐充值
            </button>

            {isLoggedIn ? (
              <>
                {accountSummary?.nickname && (
                  <span className="hidden sm:block text-sm text-gray-600">你好，{accountSummary.nickname}</span>
                )}
                {membershipLabel(accountSummary?.membershipType) && (
                  <span className="hidden sm:block text-xs text-blue-500 bg-blue-100 px-2 py-1 rounded-full">
                    {membershipLabel(accountSummary?.membershipType)}
                  </span>
                )}
                <div className="flex items-center space-x-2">
                  <Bell className="h-4 w-4 md:h-5 md:w-5 text-gray-600" />
                  <User className="h-4 w-4 md:h-5 md:w-5 text-gray-600" />
                </div>
                {onLogout && (
                  <button
                    onClick={onLogout}
                    className="hidden md:block text-sm text-gray-500 hover:text-gray-700 transition"
                  >
                    退出登录
                  </button>
                )}
              </>
            ) : (
              <div className="flex items-center space-x-2 md:space-x-3">
                <button
                  onClick={onOpenLoginModal}
                  disabled={isAuthenticating}
                  className="flex items-center justify-center rounded-lg border border-blue-500 px-3 py-1.5 md:px-4 md:py-2 text-xs md:text-sm font-medium text-blue-600 transition hover:bg-blue-50 disabled:border-gray-300 disabled:text-gray-400"
                >
                  {isAuthenticating ? '登录中…' : '登录'}
                </button>
                {authError && (
                  <div className="hidden md:flex items-center space-x-1 text-xs text-red-500">
                    <AlertTriangle className="h-4 w-4" />
                    <span className="whitespace-nowrap">{authError}</span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </header>

      {/* 移动端侧边栏 */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div
            className="fixed inset-0 bg-gray-600 bg-opacity-75"
            onClick={() => setSidebarOpen(false)}
          />
          <div className="fixed inset-y-0 left-0 flex w-64 flex-col bg-white">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="text-lg font-semibold text-gray-900">菜单</h2>
              <button
                onClick={() => setSidebarOpen(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-6">
              <section>
                <h3 className="text-base font-bold text-gray-900 mb-3 flex items-center">
                  <User className="h-4 w-4 text-blue-500 mr-2" />
                  我的账户
                </h3>
                <div className="space-y-3">
                  <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-gray-600">剩余算力</span>
                      <span className="text-base font-bold text-blue-600">{creditsLabel}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-blue-500 to-indigo-500 h-2 rounded-full"
                        style={{ width: isLoggedIn ? '65%' : '35%' }}
                      ></div>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">本月已使用 35%</div>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-gray-50 rounded-lg p-2 text-center">
                      <div className="text-base font-bold text-gray-900">{monthlyLabel}</div>
                      <div className="text-xs text-gray-500">本月处理</div>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-2 text-center">
                      <div className="text-base font-bold text-gray-900">{totalLabel}</div>
                      <div className="text-xs text-gray-500">总计处理</div>
                    </div>
                  </div>
                </div>
              </section>

              <section>
                <h3 className="text-base font-bold text-gray-900 mb-3 flex items-center">
                  <Zap className="h-4 w-4 text-yellow-500 mr-2" />
                  快捷操作
                </h3>
                <div className="space-y-2">
                  <button
                    onClick={() => {
                      onOpenPricingModal();
                      setSidebarOpen(false);
                    }}
                    className="w-full bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white p-2 rounded-lg text-xs font-medium transition-all flex items-center justify-center space-x-2"
                  >
                    <Crown className="h-3 w-3" />
                    <span>充值算力</span>
                  </button>
                  <button className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 p-2 rounded-lg text-xs font-medium transition-all flex items-center justify-center space-x-2">
                    <History className="h-3 w-3" />
                    <span>查看历史</span>
                  </button>
                  <button className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 p-2 rounded-lg text-xs font-medium transition-all flex items-center justify-center space-x-2">
                    <Download className="h-3 w-3" />
                    <span>批量下载</span>
                  </button>
                </div>
              </section>

              {isLoggedIn && onLogout && (
                <button
                  onClick={() => {
                    onLogout();
                    setSidebarOpen(false);
                  }}
                  className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 p-2 rounded-lg text-xs font-medium transition-all"
                >
                  退出登录
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="flex flex-col md:flex-row">
        <aside className="hidden md:block w-full md:w-64 bg-white border-r border-gray-200 p-4 md:p-6 space-y-6 md:space-y-8 order-2 md:order-1">
          <section>
            <h3 className="text-base md:text-lg font-bold text-gray-900 mb-3 md:mb-4 flex items-center">
              <User className="h-4 w-4 md:h-5 md:w-5 text-blue-500 mr-2" />
              我的账户
            </h3>
            <div className="space-y-3">
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-3 md:p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs md:text-sm text-gray-600">剩余算力</span>
                  <span className="text-base md:text-lg font-bold text-blue-600">{creditsLabel}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-gradient-to-r from-blue-500 to-indigo-500 h-2 rounded-full"
                    style={{ width: isLoggedIn ? '65%' : '35%' }}
                  ></div>
                </div>
                <div className="text-xs text-gray-500 mt-1">本月已使用 35%</div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-gray-50 rounded-lg p-2 md:p-3 text-center">
                  <div className="text-base md:text-lg font-bold text-gray-900">{monthlyLabel}</div>
                  <div className="text-xs text-gray-500">本月处理</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-2 md:p-3 text-center">
                  <div className="text-base md:text-lg font-bold text-gray-900">{totalLabel}</div>
                  <div className="text-xs text-gray-500">总计处理</div>
                </div>
              </div>
            </div>
          </section>

          <section>
            <h3 className="text-base md:text-lg font-bold text-gray-900 mb-3 md:mb-4 flex items-center">
              <Zap className="h-4 w-4 md:h-5 md:w-5 text-yellow-500 mr-2" />
              快捷操作
            </h3>
            <div className="space-y-2">
              <button
                onClick={onOpenPricingModal}
                className="w-full bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white p-2 md:p-3 rounded-lg text-xs md:text-sm font-medium transition-all flex items-center justify-center space-x-2"
              >
                <Crown className="h-3 w-3 md:h-4 md:w-4" />
                <span>充值算力</span>
              </button>
              <button className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 p-2 md:p-3 rounded-lg text-xs md:text-sm font-medium transition-all flex items-center justify-center space-x-2">
                <History className="h-3 w-3 md:h-4 md:w-4" />
                <span>查看历史</span>
              </button>
              <button className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 p-2 md:p-3 rounded-lg text-xs md:text-sm font-medium transition-all flex items-center justify-center space-x-2">
                <Download className="h-3 w-3 md:h-4 md:w-4" />
                <span>批量下载</span>
              </button>
            </div>
          </section>

          <section>
            <h3 className="text-base md:text-lg font-bold text-gray-900 mb-3 md:mb-4 flex items-center">
              <span className="h-4 w-4 md:h-5 md:w-5 mr-2">💡</span>
              使用技巧
            </h3>
            <div className="space-y-3">
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-2 md:p-3">
                <div className="text-xs md:text-sm font-medium text-yellow-800 mb-1">💰 节省算力</div>
                <div className="text-xs text-yellow-700">上传前先裁剪图片，可节省20%算力消耗</div>
              </div>
              <div className="bg-green-50 border border-green-200 rounded-lg p-2 md:p-3">
                <div className="text-xs md:text-sm font-medium text-green-800 mb-1">🎯 最佳效果</div>
                <div className="text-xs text-green-700">图片分辨率建议在1024-2048px之间</div>
              </div>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-2 md:p-3">
                <div className="text-xs md:text-sm font-medium text-blue-800 mb-1">⚡ 处理速度</div>
                <div className="text-xs text-blue-700">会员用户享受优先处理队列</div>
              </div>
            </div>
          </section>
        </aside>

        <main className="flex-1 p-4 md:p-8 order-1 md:order-2">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-8">
            <div
              className="relative bg-white rounded-xl md:rounded-2xl border border-gray-200 p-4 md:p-8 hover:shadow-xl transition-all hover:scale-105 cursor-pointer group"
              onClick={() => onSelectMethod('prompt_edit')}
            >
              <div className="text-center mb-4 md:mb-6">
                <div className="flex h-16 w-16 md:h-20 md:w-20 items-center justify-center rounded-xl md:rounded-2xl bg-gradient-to-br from-blue-50 to-indigo-50 shadow-lg mx-auto mb-3 md:mb-4 group-hover:shadow-xl transition-all">
                  <img src="/AI用嘴改图.png" alt="用嘴改图" className="h-10 w-10 md:h-12 md:w-12 object-contain" />
                </div>
                <h4 className="text-lg md:text-xl font-bold text-gray-900 mb-2 md:mb-3">AI用嘴改图</h4>
                <p className="text-sm text-gray-600 leading-relaxed">
                  上传图片并输入一句中文指令，AI即可帮你快速完成改图，适合服装电商等使用场景。
                </p>
              </div>
              <div className="bg-gradient-to-r from-blue-500 to-indigo-500 text-white py-2 px-4 md:py-3 md:px-6 rounded-lg md:rounded-xl text-center font-medium hover:from-blue-600 hover:to-indigo-600 transition-all">
                立即使用
              </div>
            </div>

            <div
              className="relative bg-white rounded-xl md:rounded-2xl border border-gray-200 p-4 md:p-8 hover:shadow-xl transition-all hover:scale-105 cursor-pointer group"
              onClick={() => onSelectMethod('style')}
            >
              <div className="text-center mb-4 md:mb-6">
                <div className="flex h-16 w-16 md:h-20 md:w-20 items-center justify-center rounded-xl md:rounded-2xl bg-gradient-to-br from-purple-50 to-pink-50 shadow-lg mx-auto mb-3 md:mb-4 group-hover:shadow-xl transition-all">
                  <img src="/AI矢量化转SVG.png" alt="矢量化" className="h-10 w-10 md:h-12 md:w-12 object-contain" />
                </div>
                <h4 className="text-lg md:text-xl font-bold text-gray-900 mb-2 md:mb-3">AI矢量化(转SVG)</h4>
                <p className="text-sm text-gray-600 leading-relaxed">
                  使用AI一键将图片变成矢量图，线条清晰，图片还原。助力您的产品设计。
                </p>
              </div>
              <div className="bg-gradient-to-r from-purple-500 to-pink-500 text-white py-2 px-4 md:py-3 md:px-6 rounded-lg md:rounded-xl text-center font-medium hover:from-purple-600 hover:to-pink-600 transition-all">
                立即使用
              </div>
            </div>

            <div
              className="relative bg-white rounded-xl md:rounded-2xl border border-gray-200 p-4 md:p-8 hover:shadow-xl transition-all hover:scale-105 cursor-pointer group"
              onClick={() => onSelectMethod('extract_pattern')}
            >
              <div className="text-center mb-4 md:mb-6">
                <div className="flex h-16 w-16 md:h-20 md:w-20 items-center justify-center rounded-xl md:rounded-2xl bg-gradient-to-br from-rose-50 to-pink-50 shadow-lg mx-auto mb-3 md:mb-4 group-hover:shadow-xl transition-all">
                  <img src="/AI提取花型.png" alt="提取花型" className="h-10 w-10 md:h-12 md:w-12 object-contain" />
                </div>
                <h4 className="text-lg md:text-xl font-bold text-gray-900 mb-2 md:mb-3">AI提取花型</h4>
                <p className="text-sm text-gray-600 leading-relaxed">
                  需预处理图片，支持用嘴改图。提取图案中的花型元素，适合设计应用。
                </p>
              </div>
              <div className="bg-gradient-to-r from-rose-500 to-pink-500 text-white py-2 px-4 md:py-3 md:px-6 rounded-lg md:rounded-xl text-center font-medium hover:from-rose-600 hover:to-pink-600 transition-all">
                立即使用
              </div>
            </div>

            <div
              className="relative bg-white rounded-xl md:rounded-2xl border border-gray-200 p-4 md:p-8 hover:shadow-xl transition-all hover:scale-105 cursor-pointer group"
              onClick={() => onSelectMethod('watermark_removal')}
            >
              <div className="text-center mb-4 md:mb-6">
                <div className="flex h-16 w-16 md:h-20 md:w-20 items-center justify-center rounded-xl md:rounded-2xl bg-gradient-to-br from-cyan-50 to-blue-50 shadow-lg mx-auto mb-3 md:mb-4 group-hover:shadow-xl transition-all">
                  <img src="/AI智能去水印.png" alt="智能去水印" className="h-10 w-10 md:h-12 md:w-12 object-contain" />
                </div>
                <h4 className="text-lg md:text-xl font-bold text-gray-900 mb-2 md:mb-3">AI智能去水印</h4>
                <p className="text-sm text-gray-600 leading-relaxed">
                  一键去水印。不管是顽固的文字水印、半透明logo水印，都能快捷去除。
                </p>
              </div>
              <div className="bg-gradient-to-r from-cyan-500 to-blue-500 text-white py-2 px-4 md:py-3 md:px-6 rounded-lg md:rounded-xl text-center font-medium hover:from-cyan-600 hover:to-blue-600 transition-all">
                立即使用
              </div>
            </div>

            <div
              className="relative bg-white rounded-xl md:rounded-2xl border border-gray-200 p-4 md:p-8 hover:shadow-xl transition-all hover:scale-105 cursor-pointer group"
              onClick={() => onSelectMethod('noise_removal')}
            >
              <div className="text-center mb-4 md:mb-6">
                <div className="flex h-16 w-16 md:h-20 md:w-20 items-center justify-center rounded-xl md:rounded-2xl bg-gradient-to-br from-amber-50 to-yellow-50 shadow-lg mx-auto mb-3 md:mb-4 group-hover:shadow-xl transition-all">
                  <img src="/AI布纹去噪.png" alt="布纹去噪" className="h-10 w-10 md:h-12 md:w-12 object-contain" />
                </div>
                <h4 className="text-lg md:text-xl font-bold text-gray-900 mb-2 md:mb-3">AI布纹去噪去</h4>
                <p className="text-sm text-gray-600 leading-relaxed">
                  使用AI快速的去除图片中的噪点、布纹。还可用于对模糊矢量花的高清重绘。
                </p>
              </div>
              <div className="bg-gradient-to-r from-amber-500 to-yellow-500 text-white py-2 px-4 md:py-3 md:px-6 rounded-lg md:rounded-xl text-center font-medium hover:from-amber-600 hover:to-yellow-600 transition-all">
                立即使用
              </div>
            </div>

            <div
              className="relative bg-white rounded-xl md:rounded-2xl border border-gray-200 p-4 md:p-8 hover:shadow-xl transition-all hover:scale-105 cursor-pointer group"
              onClick={() => onSelectMethod('embroidery')}
            >
              <div className="text-center mb-4 md:mb-6">
                <div className="flex h-16 w-16 md:h-20 md:w-20 items-center justify-center rounded-xl md:rounded-2xl bg-gradient-to-br from-red-50 to-pink-50 shadow-lg mx-auto mb-3 md:mb-4 group-hover:shadow-xl transition-all">
                  <img src="/AI毛线刺绣增强.png" alt="AI毛线刺绣增强" className="h-10 w-10 md:h-12 md:w-12 object-contain" />
                </div>
                <h4 className="text-lg md:text-xl font-bold text-gray-900 mb-2 md:mb-3">AI毛线刺绣增强</h4>
                <p className="text-sm text-gray-600 leading-relaxed">
                  使用AI技术进行毛线刺绣增强，支持4K超高清输出，提供更真实的毛线质感和精细的针脚效果。
                </p>
              </div>
              <div className="bg-gradient-to-r from-red-500 to-pink-500 text-white py-2 px-4 md:py-3 md:px-6 rounded-lg md:rounded-xl text-center font-medium hover:from-red-600 hover:to-pink-600 transition-all">
                立即使用
              </div>
            </div>

            <div
              className="relative bg-white rounded-xl md:rounded-2xl border border-gray-200 p-4 md:p-8 hover:shadow-xl transition-all hover:scale-105 cursor-pointer group"
              onClick={() => onSelectMethod('upscale')}
            >
              <div className="text-center mb-4 md:mb-6">
                <div className="flex h-16 w-16 md:h-20 md:w-20 items-center justify-center rounded-xl md:rounded-2xl bg-gradient-to-br from-green-50 to-emerald-50 shadow-lg mx-auto mb-3 md:mb-4 group-hover:shadow-xl transition-all">
                  <img src="/进一步处理.png" alt="无损放大" className="h-10 w-10 md:h-12 md:w-12 object-contain" />
                </div>
                <h4 className="text-lg md:text-xl font-bold text-gray-900 mb-2 md:mb-3">AI无损放大</h4>
                <p className="text-sm text-gray-600 leading-relaxed">
                  使用AI技术对图片进行无损放大，最高支持8K分辨率，保持图片清晰度和细节，适合印刷和展示。
                </p>
              </div>
              <div className="bg-gradient-to-r from-green-500 to-emerald-500 text-white py-2 px-4 md:py-3 md:px-6 rounded-lg md:rounded-xl text-center font-medium hover:from-green-600 hover:to-emerald-600 transition-all">
                立即使用
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default HomeView;
