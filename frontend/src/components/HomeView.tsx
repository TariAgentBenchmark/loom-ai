'use client';

import React, { useState, useEffect } from 'react';
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
  MessageCircle,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';
import { ProcessingMethod } from '../lib/processing';
import HistoryList from './HistoryList';
import ImagePreview from './ImagePreview';
import { HistoryTask, type CreditBalanceResponse, getNotifications, markNotificationRead, markAllNotificationsRead } from '../lib/api';

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
  onSelectBatchMode?: (method: ProcessingMethod) => void;
  onOpenPricingModal: () => void;
  onOpenCreditHistory: () => void;
  onLogout?: () => void;
  onLogin: () => void;
  onRegister?: () => void;
  onOpenAgentManager?: () => void;
  isLoggedIn: boolean;
  isAuthenticating: boolean;
  authError?: string;
  accountSummary?: AccountSummary;
  creditBalance?: CreditBalanceResponse;
  onOpenLoginModal: () => void;
  accessToken?: string;
  historyRefreshToken?: number;
  hasAgentManagement?: boolean;
}

const formatNumber = (value: number | undefined, fallback: string, fractionDigits = 0) =>
  typeof value === 'number'
    ? value.toLocaleString(undefined, {
      minimumFractionDigits: fractionDigits,
      maximumFractionDigits: fractionDigits,
    })
    : fallback;

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
  onOpenCreditHistory,
  onLogout,
  onLogin,
  onRegister,
  onOpenAgentManager,
  isLoggedIn,
  isAuthenticating,
  authError,
  accountSummary,
  creditBalance,
  onOpenLoginModal,
  accessToken,
  historyRefreshToken = 0,
  hasAgentManagement = false,
}) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [selectedTask, setSelectedTask] = useState<HistoryTask | null>(null);
  const [showBatchDownload, setShowBatchDownload] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showWechatModal, setShowWechatModal] = useState(false);
  const [notifications, setNotifications] = useState<any[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const creditsLabel = formatNumber(
    creditBalance?.credits ?? accountSummary?.credits,
    isLoggedIn ? '0.00' : '--',
    2,
  );
  const monthlyLabel = formatNumber(accountSummary?.monthlyProcessed, isLoggedIn ? '0' : '--');
  const totalLabel = formatNumber(accountSummary?.totalProcessed, isLoggedIn ? '0' : '--');
  const monthlySpentLabel = formatNumber(creditBalance?.monthlySpent, isLoggedIn ? '0.00' : '--', 2);
  const monthlyUsageText = isLoggedIn
    ? `本月已使用 ${monthlySpentLabel} 积分`
    : '登录后可查看本月积分使用情况';

  // 打开任意全屏弹窗时锁定页面滚动，避免背景跟随滚动
  useEffect(() => {
    const modalOpen = showBatchDownload || showHistory;
    if (modalOpen) {
      const originalOverflow = document.body.style.overflow;
      document.body.style.overflow = 'hidden';
      return () => {
        document.body.style.overflow = originalOverflow;
      };
    }
    return undefined;
  }, [showBatchDownload, showHistory]);

  // 获取通知
  useEffect(() => {
    if (isLoggedIn && accessToken) {
      getNotifications(accessToken, { page: 1, page_size: 10 })
        .then((response) => {
          setNotifications(response.data.notifications);
          setUnreadCount(response.data.unreadCount);
        })
        .catch((error) => {
          console.error('Failed to fetch notifications:', error);
        });
    } else {
      setNotifications([]);
      setUnreadCount(0);
    }
  }, [isLoggedIn, accessToken]);

  const handleLogout = () => {
    if (onLogout) {
      onLogout();
    }
  };

  const handleBatchDownload = () => {
    setShowBatchDownload(true);
    setSidebarOpen(false);
  };

  const handleNotificationClick = async () => {
    if (!showNotifications && unreadCount > 0 && accessToken) {
      try {
        await markAllNotificationsRead(accessToken);
        setUnreadCount(0);
        setNotifications((prev) =>
          prev.map((n) => ({ ...n, isRead: true }))
        );
      } catch (error) {
        console.error('Failed to mark notifications as read:', error);
      }
    }
    setShowNotifications(!showNotifications);
    setShowUserMenu(false);
  };

  const handleUserClick = () => {
    setShowUserMenu(!showUserMenu);
    setShowNotifications(false);
  };

  // 点击外部关闭下拉菜单
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Element;
      if (
        !target.closest('.notification-menu') &&
        !target.closest('.notification-menu-panel') &&
        !target.closest('.user-menu') &&
        !target.closest('.user-menu-panel')
      ) {
        setShowNotifications(false);
        setShowUserMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="sticky top-0 z-40 bg-white border-b border-gray-200 shadow-sm">
        <div className="flex items-center justify-between px-4 md:px-6 py-3 md:py-4">
          <div className="flex items-center space-x-3 md:space-x-4">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="md:hidden text-gray-500 hover:text-gray-700"
            >
              {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
            <div className="flex items-center space-x-2 md:space-x-3">
              <img src="/optimized/logo.webp" alt="Logo" className="h-11 md:h-14" style={{ margin: '0' }} />
            </div>
          </div>

          <div className="flex items-center space-x-2 md:space-x-4">
            <a
              href="https://jcnra80wsnt6.feishu.cn/wiki/Z3gyw5r6IiauObkUyo5cIaShniA?from=from_copylink"
              target="_blank"
              rel="noreferrer"
              className="hidden sm:inline-flex flex-col justify-center text-center px-3 py-1.5 md:px-4 md:py-2 rounded-lg border border-blue-200 bg-white text-xs md:text-sm font-semibold text-blue-600 hover:bg-blue-50 shadow-sm transition"
            >
              <span>使用教程</span>
              <span className="text-[11px] md:text-xs font-normal">(建议使用前阅读)</span>
            </a>
            <button
              onClick={() => setShowWechatModal(true)}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 md:px-4 md:py-2 rounded-lg bg-green-500 hover:bg-green-600 text-white text-xs md:text-sm font-medium transition-all shadow-sm"
            >
              <MessageCircle className="h-4 w-4" />
              <span>微信扫码</span>
            </button>
            <div className="hidden md:inline-flex items-center gap-2 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 px-3 py-1.5 text-[11px] font-semibold shadow-sm">
              <Sparkles className="h-3.5 w-3.5 text-amber-500" />
              <span className="leading-tight">加管理员微信</span>
              <span className="text-[10px] font-medium bg-white/70 px-2 py-0.5 rounded-lg tracking-wide text-amber-700">
                多领取3试用积分
              </span>
            </div>
            {isLoggedIn && (
              <button
                onClick={onOpenPricingModal}
                className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white px-3 py-1.5 md:px-4 md:py-2 rounded-lg text-xs md:text-sm font-medium transition-all shadow-sm"
              >
                套餐充值
              </button>
            )}

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
                {(accountSummary as any)?.isTestUser && (
                  <span className="hidden sm:block text-xs text-purple-600 bg-purple-100 px-2 py-1 rounded-full">
                    测试用户
                  </span>
                )}
                <div className="flex items-center space-x-2 relative">
                  <div className="notification-menu">
                    <button
                      onClick={handleNotificationClick}
                      className="relative p-1 text-gray-600 hover:text-gray-900 transition"
                    >
                      <Bell className="h-4 w-4 md:h-5 md:w-5" />
                      {unreadCount > 0 && (
                        <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-medium text-white">
                          {unreadCount > 9 ? '9+' : unreadCount}
                        </span>
                      )}
                    </button>
                  </div>
                  <div className="user-menu">
                    <button
                      onClick={handleUserClick}
                      className="p-1 text-gray-600 hover:text-gray-900 transition"
                    >
                      <User className="h-4 w-4 md:h-5 md:w-5" />
                    </button>
                  </div>

                  {/* 通知下拉菜单 */}
                  {showNotifications && (
                    <div className="absolute right-0 top-full mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200 z-50 notification-menu-panel">
                      <div className="p-4 border-b border-gray-200">
                        <h3 className="text-lg font-semibold text-gray-900">通知</h3>
                      </div>
                      <div className="max-h-96 overflow-y-auto">
                        <div className="p-4 space-y-3">
                          {notifications.length === 0 ? (
                            <div className="text-center text-sm text-gray-500 py-8">
                              暂无通知
                            </div>
                          ) : (
                            notifications.map((notification) => (
                              <div
                                key={notification.notificationId}
                                className={`${notification.isRead ? 'bg-gray-50 border-gray-200' : 'bg-blue-50 border-blue-200'} border rounded-lg p-3`}
                              >
                                <div className="flex items-start space-x-3">
                                  <div className="flex-shrink-0">
                                    <div className={`h-8 w-8 rounded-full flex items-center justify-center ${notification.isRead ? 'bg-gray-400' : 'bg-blue-500'}`}>
                                      <span className="text-white text-sm font-medium">
                                        {notification.type === 'system' ? '系' : '通'}
                                      </span>
                                    </div>
                                  </div>
                                  <div className="flex-1">
                                    <p className={`text-sm font-medium ${notification.isRead ? 'text-gray-700' : 'text-gray-900'}`}>
                                      {notification.title}
                                    </p>
                                    <p className="text-xs text-gray-600 mt-1">{notification.content}</p>
                                    <p className="text-xs text-gray-500 mt-2">
                                      {new Date(notification.createdAt).toLocaleString('zh-CN', {
                                        month: 'numeric',
                                        day: 'numeric',
                                        hour: '2-digit',
                                        minute: '2-digit',
                                      })}
                                    </p>
                                  </div>
                                </div>
                              </div>
                            ))
                          )}
                        </div>
                      </div>
                      <div className="p-3 border-t border-gray-200 text-center">
                        <button className="text-sm text-blue-600 hover:text-blue-700 font-medium">
                          查看全部通知
                        </button>
                      </div>
                    </div>
                  )}

                  {/* 用户菜单下拉 */}
                  {showUserMenu && (
                    <div className="absolute right-0 top-full mt-2 w-56 bg-white rounded-lg shadow-lg border border-gray-200 z-50 user-menu-panel">
                      <div className="p-4 border-b border-gray-200">
                        <p className="text-sm font-medium text-gray-900">
                          {accountSummary?.nickname || '用户'}
                        </p>
                        <p className="text-xs text-gray-500">
                          {membershipLabel(accountSummary?.membershipType)}
                        </p>
                      </div>
                      <div className="py-2">
                        <button
                          onClick={() => {
                            setShowUserMenu(false);
                            setShowHistory(true);
                          }}
                          className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center space-x-2"
                        >
                          <History className="h-4 w-4" />
                          <span>历史记录</span>
                        </button>
                        <button
                          onClick={() => {
                            setShowUserMenu(false);
                            handleBatchDownload();
                          }}
                          className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center space-x-2"
                        >
                          <Download className="h-4 w-4" />
                          <span>批量下载</span>
                        </button>
                        {hasAgentManagement && onOpenAgentManager && (
                          <button
                            onClick={() => {
                              setShowUserMenu(false);
                              onOpenAgentManager();
                            }}
                            className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center space-x-2"
                          >
                            <ShieldCheck className="h-4 w-4" />
                            <span>代理管理</span>
                          </button>
                        )}
                        {isLoggedIn && (
                          <button
                            onClick={() => {
                              setShowUserMenu(false);
                              onOpenCreditHistory();
                            }}
                            className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center space-x-2"
                          >
                            <Crown className="h-4 w-4" />
                            <span>充值消费记录</span>
                          </button>
                        )}
                        <hr className="my-2" />
                        {onLogout && (
                          <button
                            onClick={() => {
                              setShowUserMenu(false);
                              onLogout();
                            }}
                            className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center space-x-2"
                          >
                            <X className="h-4 w-4" />
                            <span>退出登录</span>
                          </button>
                        )}
                      </div>
                    </div>
                  )}
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
                {onRegister && (
                  <button
                    onClick={() => {
                      console.log('HomeView: Register button clicked');
                      onRegister();
                    }}
                    disabled={isAuthenticating}
                    className="flex items-center justify-center rounded-lg bg-blue-500 hover:bg-blue-600 px-3 py-1.5 md:px-4 md:py-2 text-xs md:text-sm font-medium text-white transition disabled:bg-gray-400"
                  >
                    {isAuthenticating ? '注册中…' : '注册'}
                  </button>
                )}
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
                      <span className="text-xs text-gray-600">剩余积分</span>
                      <span className="text-base font-bold text-blue-600">{creditsLabel}</span>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">{monthlyUsageText}</div>
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
                  {isLoggedIn && (
                    <button
                      onClick={() => {
                        onOpenPricingModal();
                        setSidebarOpen(false);
                      }}
                      className="w-full bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white p-2 rounded-lg text-xs font-medium transition-all flex items-center justify-center space-x-2"
                    >
                      <Crown className="h-3 w-3" />
                      <span>充值积分</span>
                    </button>
                  )}
                  <button
                    onClick={() => {
                      setShowHistory(true);
                      setSidebarOpen(false);
                    }}
                    className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 p-2 rounded-lg text-xs font-medium transition-all flex items-center justify-center space-x-2"
                  >
                    <History className="h-3 w-3" />
                    <span>查看历史</span>
                  </button>
                  {hasAgentManagement && onOpenAgentManager && (
                    <button
                      onClick={() => {
                        onOpenAgentManager();
                        setSidebarOpen(false);
                      }}
                      className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 p-2 rounded-lg text-xs font-medium transition-all flex items-center justify-center space-x-2"
                    >
                      <ShieldCheck className="h-3 w-3" />
                      <span>代理管理</span>
                    </button>
                  )}
                  <button
                    onClick={handleBatchDownload}
                    className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 p-2 rounded-lg text-xs font-medium transition-all flex items-center justify-center space-x-2"
                  >
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

      <div className="flex flex-col md:flex-row items-start">
        <aside className="hidden md:block w-full md:w-64 bg-white border-r border-gray-200 p-4 md:p-6 space-y-6 md:space-y-8 order-2 md:order-1 flex flex-col sticky top-[73px] h-[calc(100vh-73px)] overflow-y-auto">
          <section>
            <h3 className="text-base md:text-lg font-bold text-gray-900 mb-3 md:mb-4 flex items-center">
              <User className="h-4 w-4 md:h-5 md:w-5 text-blue-500 mr-2" />
              我的账户
            </h3>
            <div className="space-y-3">
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-3 md:p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs md:text-sm text-gray-600">剩余积分</span>
                  <span className="text-base md:text-lg font-bold text-blue-600">{creditsLabel}</span>
                </div>
                <div className="text-xs text-gray-500 mt-1">{monthlyUsageText}</div>
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
              {isLoggedIn && (
                <button
                  onClick={onOpenPricingModal}
                  className="w-full bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white p-2 md:p-3 rounded-lg text-xs md:text-sm font-medium transition-all flex items-center justify-center space-x-2"
                >
                  <Crown className="h-3 w-3 md:h-4 md:w-4" />
                  <span>充值积分</span>
                </button>
              )}
              <button
                onClick={() => setShowHistory(true)}
                className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 p-2 md:p-3 rounded-lg text-xs md:text-sm font-medium transition-all flex items-center justify-center space-x-2"
              >
                <History className="h-3 w-3 md:h-4 md:w-4" />
                <span>查看历史</span>
              </button>
              {hasAgentManagement && onOpenAgentManager && (
                <button
                  onClick={onOpenAgentManager}
                  className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 p-2 md:p-3 rounded-lg text-xs md:text-sm font-medium transition-all flex items-center justify-center space-x-2"
                >
                  <ShieldCheck className="h-3 w-3 md:h-4 md:w-4" />
                  <span>代理管理</span>
                </button>
              )}
              <button
                onClick={handleBatchDownload}
                className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 p-2 md:p-3 rounded-lg text-xs md:text-sm font-medium transition-all flex items-center justify-center space-x-2"
              >
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
              className="relative flex flex-col h-full bg-white rounded-xl md:rounded-2xl border border-gray-200 p-4 md:p-8 hover:shadow-xl transition-all hover:scale-105 cursor-pointer group"
              onClick={() => onSelectMethod('prompt_edit')}
            >
              <div className="text-center mb-4 md:mb-6 flex-1">
                <div className="flex h-16 w-16 md:h-20 md:w-20 items-center justify-center rounded-xl md:rounded-2xl bg-gradient-to-br from-blue-50 to-indigo-50 shadow-lg mx-auto mb-3 md:mb-4 group-hover:shadow-xl transition-all">
                  <img src="/optimized/AI用嘴改图.webp" alt="用嘴改图" className="h-10 w-10 md:h-12 md:w-12 object-contain" />
                </div>
                <h4 className="text-lg md:text-xl font-bold text-gray-900 mb-2 md:mb-3">AI用嘴改图</h4>
                <p className="text-sm text-gray-600 leading-relaxed">
                  上传图片并输入一句中文指令，AI即可帮你快速完成改图，适合服装电商等使用场景。
                </p>
              </div>
              <div className="mt-auto bg-gradient-to-r from-blue-500 to-indigo-500 text-white py-2 px-4 md:py-3 md:px-6 rounded-lg md:rounded-xl text-center font-medium hover:from-blue-600 hover:to-indigo-600 transition-all">
                立即使用
              </div>
            </div>

            <div
              className="relative flex flex-col h-full bg-white rounded-xl md:rounded-2xl border border-gray-200 p-4 md:p-8 hover:shadow-xl transition-all hover:scale-105 cursor-pointer group"
              onClick={() => onSelectMethod('style')}
            >
              <div className="text-center mb-4 md:mb-6 flex-1">
                <div className="flex h-16 w-16 md:h-20 md:w-20 items-center justify-center rounded-xl md:rounded-2xl bg-gradient-to-br from-purple-50 to-pink-50 shadow-lg mx-auto mb-3 md:mb-4 group-hover:shadow-xl transition-all">
                  <img src="/optimized/AI矢量化转SVG.webp" alt="矢量化" className="h-10 w-10 md:h-12 md:w-12 object-contain" />
                </div>
                <h4 className="text-lg md:text-xl font-bold text-gray-900 mb-2 md:mb-3">AI矢量化(转SVG)</h4>
                <p className="text-sm text-gray-600 leading-relaxed">
                  使用AI一键将图片变成矢量图，线条清晰，图片还原。助力您的产品设计。
                </p>
              </div>
              <div className="mt-auto bg-gradient-to-r from-purple-500 to-pink-500 text-white py-2 px-4 md:py-3 md:px-6 rounded-lg md:rounded-xl text-center font-medium hover:from-purple-600 hover:to-pink-600 transition-all">
                立即使用
              </div>
            </div>

            <div
              className="relative flex flex-col h-full bg-white rounded-xl md:rounded-2xl border border-gray-200 p-4 md:p-8 hover:shadow-xl transition-all hover:scale-105 cursor-pointer group"
              onClick={() => onSelectMethod('extract_pattern')}
            >
              <div className="text-center mb-4 md:mb-6 flex-1">
                <div className="flex h-16 w-16 md:h-20 md:w-20 items-center justify-center rounded-xl md:rounded-2xl bg-gradient-to-br from-rose-50 to-pink-50 shadow-lg mx-auto mb-3 md:mb-4 group-hover:shadow-xl transition-all">
                  <img src="/optimized/AI提取花型.webp" alt="提取花型" className="h-10 w-10 md:h-12 md:w-12 object-contain" />
                </div>
                <h4 className="text-lg md:text-xl font-bold text-gray-900 mb-2 md:mb-3">AI提取花型</h4>
                <p className="text-sm text-gray-600 leading-relaxed">
                  自动提取图案并赋予高清增强效果，帮助您快速获取可用的花型素材。
                </p>
              </div>
              <div className="mt-auto bg-gradient-to-r from-rose-500 to-pink-500 text-white py-2 px-4 md:py-3 md:px-6 rounded-lg md:rounded-xl text-center font-medium hover:from-rose-600 hover:to-pink-600 transition-all">
                立即使用
              </div>
            </div>

            <div
              className="relative flex flex-col h-full bg-white rounded-xl md:rounded-2xl border border-gray-200 p-4 md:p-8 hover:shadow-xl transition-all hover:scale-105 cursor-pointer group"
              onClick={() => onSelectMethod('similar_image')}
            >
              <div className="text-center mb-4 md:mb-6 flex-1">
                <div className="flex h-16 w-16 md:h-20 md:w-20 items-center justify-center rounded-xl md:rounded-2xl bg-gradient-to-br from-teal-50 to-emerald-50 shadow-lg mx-auto mb-3 md:mb-4 group-hover:shadow-xl transition-all">
                  <img src="/optimized/AI智能去水印.webp" alt="AI相似图" className="h-10 w-10 md:h-12 md:w-12 object-contain" />
                </div>
                <h4 className="text-lg md:text-xl font-bold text-gray-900 mb-2 md:mb-3">AI相似图</h4>
                <p className="text-sm text-gray-600 leading-relaxed">
                  上传参考图，一键生成风格/构图相近的相似图，快速收集灵感并辅助选款。
                </p>
              </div>
              <div className="mt-auto bg-gradient-to-r from-teal-500 to-emerald-500 text-white py-2 px-4 md:py-3 md:px-6 rounded-lg md:rounded-xl text-center font-medium hover:from-teal-600 hover:to-emerald-600 transition-all">
                立即使用
              </div>
            </div>

            <div
              className="relative flex flex-col h-full bg-white rounded-xl md:rounded-2xl border border-gray-200 p-4 md:p-8 hover:shadow-xl transition-all hover:scale-105 cursor-pointer group"
              onClick={() => onSelectMethod('watermark_removal')}
            >
              <div className="text-center mb-4 md:mb-6 flex-1">
                <div className="flex h-16 w-16 md:h-20 md:w-20 items-center justify-center rounded-xl md:rounded-2xl bg-gradient-to-br from-cyan-50 to-blue-50 shadow-lg mx-auto mb-3 md:mb-4 group-hover:shadow-xl transition-all">
                  <img src="/optimized/AI智能去水印.webp" alt="智能去水印" className="h-10 w-10 md:h-12 md:w-12 object-contain" />
                </div>
                <h4 className="text-lg md:text-xl font-bold text-gray-900 mb-2 md:mb-3">AI智能去水印</h4>
                <p className="text-sm text-gray-600 leading-relaxed">
                  一键去水印。不管是顽固的文字水印、半透明logo水印，都能快捷去除。
                </p>
              </div>
              <div className="mt-auto bg-gradient-to-r from-cyan-500 to-blue-500 text-white py-2 px-4 md:py-3 md:px-6 rounded-lg md:rounded-xl text-center font-medium hover:from-cyan-600 hover:to-blue-600 transition-all">
                立即使用
              </div>
            </div>

            <div
              className="relative flex flex-col h-full bg-white rounded-xl md:rounded-2xl border border-gray-200 p-4 md:p-8 hover:shadow-xl transition-all hover:scale-105 cursor-pointer group"
              onClick={() => onSelectMethod('noise_removal')}
            >
              <div className="text-center mb-4 md:mb-6 flex-1">
                <div className="flex h-16 w-16 md:h-20 md:w-20 items-center justify-center rounded-xl md:rounded-2xl bg-gradient-to-br from-amber-50 to-yellow-50 shadow-lg mx-auto mb-3 md:mb-4 group-hover:shadow-xl transition-all">
                  <img src="/optimized/进一步处理.webp" alt="布纹去噪" className="h-10 w-10 md:h-12 md:w-12 object-contain" />
                </div>
                <h4 className="text-lg md:text-xl font-bold text-gray-900 mb-2 md:mb-3">AI布纹去噪</h4>
                <p className="text-sm text-gray-600 leading-relaxed">
                  使用AI快速的去除图片中的噪点、布纹。还可用于对模糊矢量花的高清重绘。
                </p>
              </div>
              <div className="mt-auto bg-gradient-to-r from-amber-500 to-yellow-500 text-white py-2 px-4 md:py-3 md:px-6 rounded-lg md:rounded-xl text-center font-medium hover:from-amber-600 hover:to-yellow-600 transition-all">
                立即使用
              </div>
            </div>

            <div
              className="relative flex flex-col h-full bg-white rounded-xl md:rounded-2xl border border-gray-200 p-4 md:p-8 hover:shadow-xl transition-all hover:scale-105 cursor-pointer group"
              onClick={() => onSelectMethod('embroidery')}
            >
              <div className="text-center mb-4 md:mb-6 flex-1">
                <div className="flex h-16 w-16 md:h-20 md:w-20 items-center justify-center rounded-xl md:rounded-2xl bg-gradient-to-br from-red-50 to-pink-50 shadow-lg mx-auto mb-3 md:mb-4 group-hover:shadow-xl transition-all">
                  <img src="/optimized/AI毛线刺绣增强.webp" alt="AI刺绣" className="h-10 w-10 md:h-12 md:w-12 object-contain" />
                </div>
                <h4 className="text-lg md:text-xl font-bold text-gray-900 mb-2 md:mb-3">AI刺绣</h4>
                <p className="text-sm text-gray-600 leading-relaxed">
                  使用AI技术进行刺绣增强，支持4K超高清输出，提供更真实的质感和精细的针脚效果。
                </p>
              </div>
              <div className="mt-auto bg-gradient-to-r from-red-500 to-pink-500 text-white py-2 px-4 md:py-3 md:px-6 rounded-lg md:rounded-xl text-center font-medium hover:from-red-600 hover:to-pink-600 transition-all">
                立即使用
              </div>
            </div>

            <div
              className="relative flex flex-col h-full bg-white rounded-xl md:rounded-2xl border border-gray-200 p-4 md:p-8 hover:shadow-xl transition-all hover:scale-105 cursor-pointer group"
              onClick={() => onSelectMethod('flat_to_3d')}
            >
              <div className="text-center mb-4 md:mb-6 flex-1">
                <div className="flex h-16 w-16 md:h-20 md:w-20 items-center justify-center rounded-xl md:rounded-2xl bg-gradient-to-br from-indigo-50 to-blue-50 shadow-lg mx-auto mb-3 md:mb-4 group-hover:shadow-xl transition-all">
                  <img src="/optimized/AI提取花型.webp" alt="AI平面转3D" className="h-10 w-10 md:h-12 md:w-12 object-contain" />
                </div>
                <h4 className="text-lg md:text-xl font-bold text-gray-900 mb-2 md:mb-3">AI平面转3D</h4>
                <p className="text-sm text-gray-600 leading-relaxed">
                  将平面图案快速转换为立体效果，自动生成鲜艳色彩与精致细节，让作品更具空间感与展示力。
                </p>
              </div>
              <div className="mt-auto bg-gradient-to-r from-indigo-500 to-blue-500 text-white py-2 px-4 md:py-3 md:px-6 rounded-lg md:rounded-xl text-center font-medium hover:from-indigo-600 hover:to-blue-600 transition-all">
                立即使用
              </div>
            </div>

            <div
              className="relative flex flex-col h-full bg-white rounded-xl md:rounded-2xl border border-gray-200 p-4 md:p-8 hover:shadow-xl transition-all hover:scale-105 cursor-pointer group"
              onClick={() => onSelectMethod('upscale')}
            >
              <div className="text-center mb-4 md:mb-6 flex-1">
                <div className="flex h-16 w-16 md:h-20 md:w-20 items-center justify-center rounded-xl md:rounded-2xl bg-gradient-to-br from-green-50 to-emerald-50 shadow-lg mx-auto mb-3 md:mb-4 group-hover:shadow-xl transition-all">
                  <img src="/optimized/AI布纹去噪.webp" alt="AI高清" className="h-10 w-10 md:h-12 md:w-12 object-contain" />
                </div>
                <h4 className="text-lg md:text-xl font-bold text-gray-900 mb-2 md:mb-3">AI高清</h4>
                <p className="text-sm text-gray-600 leading-relaxed">
                  双引擎高清放大，通用1注重稳定还原，通用2强化锐度与纹理，兼顾模糊图与高清素材。
                </p>
              </div>
              <div className="mt-auto bg-gradient-to-r from-green-500 to-emerald-500 text-white py-2 px-4 md:py-3 md:px-6 rounded-lg md:rounded-xl text-center font-medium hover:from-green-600 hover:to-emerald-600 transition-all">
                立即使用
              </div>
            </div>

            <div
              className="relative flex flex-col h-full bg-white rounded-xl md:rounded-2xl border border-gray-200 p-4 md:p-8 hover:shadow-xl transition-all hover:scale-105 cursor-pointer group"
              onClick={() => onSelectMethod('expand_image')}
            >
              <div className="text-center mb-4 md:mb-6 flex-1">
                <div className="flex h-16 w-16 md:h-20 md:w-20 items-center justify-center rounded-xl md:rounded-2xl bg-gradient-to-br from-sky-50 to-blue-50 shadow-lg mx-auto mb-3 md:mb-4 group-hover:shadow-xl transition-all">
                  <img src="/optimized/AI智能去水印.webp" alt="AI扩图" className="h-10 w-10 md:h-12 md:w-12 object-contain" />
                </div>
                <h4 className="text-lg md:text-xl font-bold text-gray-900 mb-2 md:mb-3">AI扩图</h4>
                <p className="text-sm text-gray-600 leading-relaxed">
                  智能延展图片边缘，自动补充背景与细节，适合海报、主图和尺寸适配场景。
                </p>
              </div>
              <div className="mt-auto bg-gradient-to-r from-sky-500 to-blue-500 text-white py-2 px-4 md:py-3 md:px-6 rounded-lg md:rounded-xl text-center font-medium hover:from-sky-600 hover:to-blue-600 transition-all">
                立即使用
              </div>
            </div>

            <div
              className="relative flex flex-col h-full bg-white rounded-xl md:rounded-2xl border border-gray-200 p-4 md:p-8 hover:shadow-xl transition-all hover:scale-105 cursor-pointer group"
              onClick={() => onSelectMethod('seamless_loop')}
            >
              <div className="text-center mb-4 md:mb-6 flex-1">
                <div className="flex h-16 w-16 md:h-20 md:w-20 items-center justify-center rounded-xl md:rounded-2xl bg-gradient-to-br from-lime-50 to-green-50 shadow-lg mx-auto mb-3 md:mb-4 group-hover:shadow-xl transition-all">
                  <img src="/optimized/AI提取花型.webp" alt="AI接循环" className="h-10 w-10 md:h-12 md:w-12 object-contain" />
                </div>
                <h4 className="text-lg md:text-xl font-bold text-gray-900 mb-2 md:mb-3">AI接循环</h4>
                <p className="text-sm text-gray-600 leading-relaxed">
                  将花型快速转换为可无缝平铺的循环图案，同时生成网格预览，省心对接打样需求。
                </p>
              </div>
              <div className="mt-auto bg-gradient-to-r from-lime-500 to-green-500 text-white py-2 px-4 md:py-3 md:px-6 rounded-lg md:rounded-xl text-center font-medium hover:from-lime-600 hover:to-green-600 transition-all">
                立即使用
              </div>
            </div>
          </div>
        </main>
      </div>

      {/* 历史记录弹窗 */}
      {showHistory && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-lg w-full max-w-4xl h-4/5 flex flex-col">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="text-lg font-semibold">历史记录</h2>
              <button
                onClick={() => setShowHistory(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="flex-1 overflow-hidden">
              {accessToken && (
                <HistoryList
                  accessToken={accessToken}
                  onTaskSelect={setSelectedTask}
                  refreshToken={historyRefreshToken}
                />
              )}
            </div>
          </div>
        </div>
      )}

      {/* 图片预览弹窗 */}
      {selectedTask && (
        <ImagePreview
          task={selectedTask}
          onClose={() => setSelectedTask(null)}
          accessToken={accessToken || ''}
        />
      )}

      {/* 批量下载弹窗 */}
      {showBatchDownload && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-lg w-full max-w-4xl h-4/5 flex flex-col">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="text-lg font-semibold">批量下载</h2>
              <button
                onClick={() => setShowBatchDownload(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="flex-1 overflow-hidden p-4">
              {accessToken ? (
                <div className="flex flex-col h-full overflow-hidden">
                  <div className="text-center mb-6">
                    <Download className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">批量下载功能</h3>
                    <p className="text-gray-600 max-w-md">
                      选择您要下载的历史记录图片，支持一次性下载多张图片。您可以按日期、类型或状态筛选记录。
                    </p>
                  </div>
                  <div className="w-full max-w-2xl flex-1 overflow-hidden">
                    <HistoryList
                      accessToken={accessToken}
                      onTaskSelect={setSelectedTask}
                      showBatchSelection={true}
                      refreshToken={historyRefreshToken}
                    />
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-full">
                  <div className="text-center">
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 max-w-md">
                      <AlertTriangle className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
                      <h3 className="text-lg font-semibold text-yellow-800 mb-2">需要登录</h3>
                      <p className="text-yellow-700 mb-4">
                        请先登录后再使用批量下载功能
                      </p>
                      <button
                        onClick={() => {
                          setShowBatchDownload(false);
                          onOpenLoginModal();
                        }}
                        className="bg-yellow-500 hover:bg-yellow-600 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                      >
                        去登录
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 微信二维码弹窗 */}
      {showWechatModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-lg w-80 max-w-sm shadow-2xl p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold text-gray-900">添加微信</h3>
              <button
                onClick={() => setShowWechatModal(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <p className="text-sm text-gray-600 mb-3">扫码添加微信，获取快速支持。</p>
            <div className="w-full flex justify-center">
              <img
                src="/qrcode.png"
                alt="微信二维码"
                className="w-48 h-48 object-contain rounded-lg border border-gray-200"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HomeView;
