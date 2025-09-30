'use client';

import React from 'react';
import {
  Bell,
  Crown,
  Download,
  History,
  User,
  Zap,
  AlertTriangle,
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
  const creditsLabel = formatNumber(accountSummary?.credits, isLoggedIn ? '0' : '--');
  const monthlyLabel = formatNumber(accountSummary?.monthlyProcessed, isLoggedIn ? '0' : '--');
  const totalLabel = formatNumber(accountSummary?.totalProcessed, isLoggedIn ? '0' : '--');

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
        <div className="flex items-center justify-between px-6 py-4">
          <div className="flex items-center space-x-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl overflow-hidden">
              <img src="/logo.png" alt="Logo" className="h-full w-full object-cover" />
            </div>
            <span className="text-xl font-bold text-gray-900">应用中心</span>
          </div>

          <div className="flex items-center space-x-4">
            <button
              onClick={onOpenPricingModal}
              className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all shadow-sm"
            >
              套餐充值
            </button>

            {isLoggedIn ? (
              <>
                {accountSummary?.nickname && (
                  <span className="text-sm text-gray-600">你好，{accountSummary.nickname}</span>
                )}
                {membershipLabel(accountSummary?.membershipType) && (
                  <span className="text-xs text-blue-500 bg-blue-100 px-2 py-1 rounded-full">
                    {membershipLabel(accountSummary?.membershipType)}
                  </span>
                )}
                <div className="flex items-center space-x-2">
                  <Bell className="h-5 w-5 text-gray-600" />
                  <User className="h-5 w-5 text-gray-600" />
                </div>
                {onLogout && (
                  <button
                    onClick={onLogout}
                    className="text-sm text-gray-500 hover:text-gray-700 transition"
                  >
                    退出登录
                  </button>
                )}
              </>
            ) : (
              <div className="flex items-center space-x-3">
                <button
                  onClick={onOpenLoginModal}
                  disabled={isAuthenticating}
                  className="flex items-center justify-center rounded-lg border border-blue-500 px-4 py-2 text-sm font-medium text-blue-600 transition hover:bg-blue-50 disabled:border-gray-300 disabled:text-gray-400"
                >
                  {isAuthenticating ? '登录中…' : '登录'}
                </button>
                {authError && (
                  <div className="flex items-center space-x-1 text-xs text-red-500">
                    <AlertTriangle className="h-4 w-4" />
                    <span className="whitespace-nowrap">{authError}</span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </header>

      <div className="flex">
        <aside className="w-64 bg-white border-r border-gray-200 p-6 space-y-8">
          <section>
            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
              <User className="h-5 w-5 text-blue-500 mr-2" />
              我的账户
            </h3>
            <div className="space-y-3">
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-600">剩余算力</span>
                  <span className="text-lg font-bold text-blue-600">{creditsLabel}</span>
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
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <div className="text-lg font-bold text-gray-900">{monthlyLabel}</div>
                  <div className="text-xs text-gray-500">本月处理</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <div className="text-lg font-bold text-gray-900">{totalLabel}</div>
                  <div className="text-xs text-gray-500">总计处理</div>
                </div>
              </div>
            </div>
          </section>

          <section>
            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
              <Zap className="h-5 w-5 text-yellow-500 mr-2" />
              快捷操作
            </h3>
            <div className="space-y-2">
              <button
                onClick={onOpenPricingModal}
                className="w-full bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white p-3 rounded-lg text-sm font-medium transition-all flex items-center justify-center space-x-2"
              >
                <Crown className="h-4 w-4" />
                <span>充值算力</span>
              </button>
              <button className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 p-3 rounded-lg text-sm font-medium transition-all flex items-center justify-center space-x-2">
                <History className="h-4 w-4" />
                <span>查看历史</span>
              </button>
              <button className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 p-3 rounded-lg text-sm font-medium transition-all flex items-center justify-center space-x-2">
                <Download className="h-4 w-4" />
                <span>批量下载</span>
              </button>
            </div>
          </section>

          <section>
            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
              <span className="h-5 w-5 mr-2">💡</span>
              使用技巧
            </h3>
            <div className="space-y-3">
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                <div className="text-sm font-medium text-yellow-800 mb-1">💰 节省算力</div>
                <div className="text-xs text-yellow-700">上传前先裁剪图片，可节省20%算力消耗</div>
              </div>
              <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                <div className="text-sm font-medium text-green-800 mb-1">🎯 最佳效果</div>
                <div className="text-xs text-green-700">图片分辨率建议在1024-2048px之间</div>
              </div>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <div className="text-sm font-medium text-blue-800 mb-1">⚡ 处理速度</div>
                <div className="text-xs text-blue-700">会员用户享受优先处理队列</div>
              </div>
            </div>
          </section>
        </aside>

        <main className="flex-1 p-8">
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8">
            <div
              className="bg-white rounded-2xl border border-gray-200 p-8 hover:shadow-xl transition-all hover:scale-105 cursor-pointer group"
              onClick={() => onSelectMethod('seamless')}
            >
              <div className="text-center mb-6">
                <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-50 to-indigo-50 shadow-lg mx-auto mb-4 group-hover:shadow-xl transition-all">
                  <img src="/AI四方连续转换.png" alt="四方连续转换" className="h-12 w-12 object-contain" />
                </div>
                <h4 className="text-xl font-bold text-gray-900 mb-3">AI四方连续转换</h4>
                <p className="text-gray-600 leading-relaxed">
                  对独幅矩形图转换成可四方连续的打印图，如需对结果放大请用AI无缝图放大功能。
                </p>
              </div>
              <div className="bg-gradient-to-r from-blue-500 to-indigo-500 text-white py-3 px-6 rounded-xl text-center font-medium hover:from-blue-600 hover:to-indigo-600 transition-all">
                立即使用
              </div>
            </div>

            <div
              className="bg-white rounded-2xl border border-gray-200 p-8 hover:shadow-xl transition-all hover:scale-105 cursor-pointer group"
              onClick={() => onSelectMethod('style')}
            >
              <div className="text-center mb-6">
                <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-purple-50 to-pink-50 shadow-lg mx-auto mb-4 group-hover:shadow-xl transition-all">
                  <img src="/AI矢量化转SVG.png" alt="矢量化" className="h-12 w-12 object-contain" />
                </div>
                <h4 className="text-xl font-bold text-gray-900 mb-3">AI矢量化(转SVG)</h4>
                <p className="text-gray-600 leading-relaxed">
                  使用AI一键将图片变成矢量图，线条清晰，图片还原。助力您的产品设计。
                </p>
                <div className="inline-block bg-orange-100 text-orange-600 px-3 py-1 rounded-full text-sm font-medium mt-2">
                  100算力
                </div>
              </div>
              <div className="bg-gradient-to-r from-purple-500 to-pink-500 text-white py-3 px-6 rounded-xl text-center font-medium hover:from-purple-600 hover:to-pink-600 transition-all">
                立即使用
              </div>
            </div>

            <div
              className="bg-white rounded-2xl border border-gray-200 p-8 hover:shadow-xl transition-all hover:scale-105 cursor-pointer group"
              onClick={() => onSelectMethod('extract_edit')}
            >
              <div className="text-center mb-6">
                <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-green-50 to-emerald-50 shadow-lg mx-auto mb-4 group-hover:shadow-xl transition-all">
                  <img src="/AI提取编辑.png" alt="提取编辑" className="h-12 w-12 object-contain" />
                </div>
                <h4 className="text-xl font-bold text-gray-900 mb-3">AI提取编辑</h4>
                <p className="text-gray-600 leading-relaxed">
                  使用AI提取和编辑图片内容，支持语音控制进行智能编辑。
                </p>
                <div className="inline-block bg-green-100 text-green-600 px-3 py-1 rounded-full text-sm font-medium mt-2">
                  智能语音
                </div>
              </div>
              <div className="bg-gradient-to-r from-green-500 to-emerald-500 text-white py-3 px-6 rounded-xl text-center font-medium hover:from-green-600 hover:to-emerald-600 transition-all">
                立即使用
              </div>
            </div>

            <div
              className="bg-white rounded-2xl border border-gray-200 p-8 hover:shadow-xl transition-all hover:scale-105 cursor-pointer group"
              onClick={() => onSelectMethod('extract_pattern')}
            >
              <div className="text-center mb-6">
                <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-rose-50 to-pink-50 shadow-lg mx-auto mb-4 group-hover:shadow-xl transition-all">
                  <img src="/AI提取花型.png" alt="提取花型" className="h-12 w-12 object-contain" />
                </div>
                <h4 className="text-xl font-bold text-gray-900 mb-3">AI提取花型</h4>
                <p className="text-gray-600 leading-relaxed">
                  需预处理图片，支持用嘴改图。提取图案中的花型元素，适合设计应用。
                </p>
                <div className="inline-block bg-orange-100 text-orange-600 px-3 py-1 rounded-full text-sm font-medium mt-2">
                  100算力
                </div>
              </div>
              <div className="bg-gradient-to-r from-rose-500 to-pink-500 text-white py-3 px-6 rounded-xl text-center font-medium hover:from-rose-600 hover:to-pink-600 transition-all">
                立即使用
              </div>
            </div>

            <div
              className="bg-white rounded-2xl border border-gray-200 p-8 hover:shadow-xl transition-all hover:scale-105 cursor-pointer group"
              onClick={() => onSelectMethod('watermark_removal')}
            >
              <div className="text-center mb-6">
                <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-50 to-blue-50 shadow-lg mx-auto mb-4 group-hover:shadow-xl transition-all">
                  <img src="/AI智能去水印.png" alt="智能去水印" className="h-12 w-12 object-contain" />
                </div>
                <h4 className="text-xl font-bold text-gray-900 mb-3">AI智能去水印</h4>
                <p className="text-gray-600 leading-relaxed">
                  一键去水印。不管是顽固的文字水印、半透明logo水印，都能快捷去除。
                </p>
              </div>
              <div className="bg-gradient-to-r from-cyan-500 to-blue-500 text-white py-3 px-6 rounded-xl text-center font-medium hover:from-cyan-600 hover:to-blue-600 transition-all">
                立即使用
              </div>
            </div>

            <div
              className="bg-white rounded-2xl border border-gray-200 p-8 hover:shadow-xl transition-all hover:scale-105 cursor-pointer group"
              onClick={() => onSelectMethod('noise_removal')}
            >
              <div className="text-center mb-6">
                <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-50 to-yellow-50 shadow-lg mx-auto mb-4 group-hover:shadow-xl transition-all">
                  <img src="/AI布纹去噪.png" alt="布纹去噪" className="h-12 w-12 object-contain" />
                </div>
                <h4 className="text-xl font-bold text-gray-900 mb-3">AI布纹去噪去</h4>
                <p className="text-gray-600 leading-relaxed">
                  使用AI快速的去除图片中的噪点、布纹。还可用于对模糊矢量花的高清重绘。
                </p>
                <div className="inline-block bg-amber-100 text-amber-600 px-3 py-1 rounded-full text-sm font-medium mt-2">
                  80算力
                </div>
              </div>
              <div className="bg-gradient-to-r from-amber-500 to-yellow-500 text-white py-3 px-6 rounded-xl text-center font-medium hover:from-amber-600 hover:to-yellow-600 transition-all">
                立即使用
              </div>
            </div>

            <div
              className="bg-white rounded-2xl border border-gray-200 p-8 hover:shadow-xl transition-all hover:scale-105 cursor-pointer group"
              onClick={() => onSelectMethod('embroidery')}
            >
              <div className="text-center mb-6">
                <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-50 to-purple-50 shadow-lg mx-auto mb-4 group-hover:shadow-xl transition-all">
                  <img src="/AI毛线刺绣增强.png" alt="AI毛线刺绣增强" className="h-12 w-12 object-contain" />
                </div>
                <h4 className="text-xl font-bold text-gray-900 mb-3">AI毛线刺绣增强</h4>
                <p className="text-gray-600 leading-relaxed">
                  针对毛线刺绣转换的针对处理，转换出的刺绣对原图主体形状保持度高，毛线感的针法。
                </p>
              </div>
              <div className="bg-gradient-to-r from-indigo-500 to-purple-500 text-white py-3 px-6 rounded-xl text-center font-medium hover:from-indigo-600 hover:to-purple-600 transition-all">
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
