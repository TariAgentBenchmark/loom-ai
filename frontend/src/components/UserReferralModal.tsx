'use client';

import React, { useMemo, useState } from 'react';
import { Copy, Gift, Link2, Users, X } from 'lucide-react';
import { ReferralRewardSettings } from '../lib/api';

type UserReferralModalProps = {
  isOpen: boolean;
  onClose: () => void;
  referralCode?: string | null;
  referralCount?: number;
  rewardSettings?: ReferralRewardSettings;
};

const UserReferralModal: React.FC<UserReferralModalProps> = ({
  isOpen,
  onClose,
  referralCode,
  referralCount = 0,
  rewardSettings,
}) => {
  const [copiedTarget, setCopiedTarget] = useState<'code' | 'link' | null>(null);

  const referralLink = useMemo(() => {
    if (!referralCode) return '';
    const origin = typeof window !== 'undefined' ? window.location.origin : '';
    return origin ? `${origin}/login?ref=${encodeURIComponent(referralCode)}` : '';
  }, [referralCode]);

  const inviterReward = rewardSettings?.userReferralInviterReward ?? 10;
  const inviteeReward = rewardSettings?.userReferralInviteeReward ?? 5;

  if (!isOpen) {
    return null;
  }

  const handleCopy = async (target: 'code' | 'link') => {
    const value = target === 'code' ? referralCode : referralLink;
    if (!value) {
      return;
    }

    try {
      await navigator.clipboard.writeText(value);
      setCopiedTarget(target);
      window.setTimeout(() => setCopiedTarget(null), 1500);
    } catch {
      setCopiedTarget(null);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-xl rounded-2xl bg-white shadow-2xl">
        <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">我的邀请</h2>
            <p className="text-xs text-gray-500">邀请 1 位新用户，你得 {inviterReward} 积分，对方得 {inviteeReward} 积分。</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full p-1 text-gray-400 hover:text-gray-600"
            aria-label="关闭邀请弹窗"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-4 px-6 py-5">
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-xl border border-blue-100 bg-blue-50 p-4">
              <div className="flex items-center gap-2 text-sm font-medium text-blue-700">
                <Users className="h-4 w-4" />
                <span>成功邀请</span>
              </div>
              <div className="mt-2 text-2xl font-bold text-blue-900">{referralCount}</div>
            </div>
            <div className="rounded-xl border border-emerald-100 bg-emerald-50 p-4">
              <div className="flex items-center gap-2 text-sm font-medium text-emerald-700">
                <Gift className="h-4 w-4" />
                <span>奖励规则</span>
              </div>
              <div className="mt-2 text-sm font-semibold text-emerald-900">每邀请 1 人，你得 {inviterReward} 积分，对方得 {inviteeReward} 积分</div>
            </div>
          </div>

          <div className="rounded-xl border border-gray-200 bg-gray-50 p-4">
            <div className="text-xs text-gray-500">我的邀请码</div>
            <div className="mt-2 flex items-center justify-between gap-3">
              <div className="truncate text-lg font-semibold tracking-[0.2em] text-gray-900">
                {referralCode || '暂未生成'}
              </div>
              <button
                type="button"
                onClick={() => handleCopy('code')}
                disabled={!referralCode}
                className="inline-flex items-center gap-1 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <Copy className="h-4 w-4" />
                {copiedTarget === 'code' ? '已复制' : '复制邀请码'}
              </button>
            </div>
          </div>

          <div className="rounded-xl border border-gray-200 bg-gray-50 p-4">
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <Link2 className="h-4 w-4" />
              <span>邀请链接</span>
            </div>
            <div className="mt-2 break-all text-sm text-gray-700">{referralLink || '暂未生成'}</div>
            <div className="mt-3">
              <button
                type="button"
                onClick={() => handleCopy('link')}
                disabled={!referralLink}
                className="inline-flex items-center gap-1 rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300"
              >
                <Copy className="h-4 w-4" />
                {copiedTarget === 'link' ? '已复制' : '复制邀请链接'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserReferralModal;
