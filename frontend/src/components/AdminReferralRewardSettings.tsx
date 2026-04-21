"use client";

import React, { useCallback, useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2, Loader2, RefreshCw, Save } from "lucide-react";
import {
  adminGetReferralRewardSettings,
  adminUpdateReferralRewardSettings,
} from "../lib/api";
import { useAdminAccessToken } from "../contexts/AdminAuthContext";

type FormState = {
  registrationReward: string;
  userReferralInviterReward: string;
  userReferralInviteeReward: string;
  agentInvitationReward: string;
};

const emptyState: FormState = {
  registrationReward: "",
  userReferralInviterReward: "",
  userReferralInviteeReward: "",
  agentInvitationReward: "",
};

const AdminReferralRewardSettings: React.FC = () => {
  const accessToken = useAdminAccessToken();
  const [formState, setFormState] = useState<FormState>(emptyState);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const loadSettings = useCallback(async () => {
    if (!accessToken) {
      return;
    }
    try {
      setIsLoading(true);
      setError(null);
      const response = await adminGetReferralRewardSettings(accessToken);
      setFormState({
        registrationReward: response.data.registrationReward.toString(),
        userReferralInviterReward: response.data.userReferralInviterReward.toString(),
        userReferralInviteeReward: response.data.userReferralInviteeReward.toString(),
        agentInvitationReward: response.data.agentInvitationReward.toString(),
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "获取邀请奖励配置失败");
    } finally {
      setIsLoading(false);
    }
  }, [accessToken]);

  useEffect(() => {
    void loadSettings();
  }, [loadSettings]);

  const updateField = (key: keyof FormState, value: string) => {
    setFormState((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!accessToken) {
      return;
    }

    const payload = {
      registrationReward: Number(formState.registrationReward),
      userReferralInviterReward: Number(formState.userReferralInviterReward),
      userReferralInviteeReward: Number(formState.userReferralInviteeReward),
      agentInvitationReward: Number(formState.agentInvitationReward),
    };

    if (Object.values(payload).some((value) => !Number.isFinite(value) || value < 0)) {
      setError("请输入大于等于 0 的有效积分值");
      setSuccessMessage(null);
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      setSuccessMessage(null);
      const response = await adminUpdateReferralRewardSettings(payload, accessToken);
      setFormState({
        registrationReward: response.data.registrationReward.toString(),
        userReferralInviterReward: response.data.userReferralInviterReward.toString(),
        userReferralInviteeReward: response.data.userReferralInviteeReward.toString(),
        agentInvitationReward: response.data.agentInvitationReward.toString(),
      });
      setSuccessMessage("邀请奖励配置已保存");
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存邀请奖励配置失败");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">邀请奖励配置</h2>
          <p className="mt-1 text-sm text-gray-600">
            在后台直接调整注册、好友邀请、代理邀请的积分规则，前台会实时读取。
          </p>
        </div>
        <button
          onClick={() => void loadSettings()}
          disabled={isLoading}
          className="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-700 shadow-sm transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
          刷新
        </button>
      </div>

      {error && (
        <div className="mt-4 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {successMessage && (
        <div className="mt-4 flex items-start gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}

      <form className="mt-6 grid gap-4 md:grid-cols-2" onSubmit={handleSubmit}>
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-gray-700">普通注册赠送</span>
          <input
            type="number"
            min="0"
            step="0.01"
            value={formState.registrationReward}
            onChange={(event) => updateField("registrationReward", event.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
          />
        </label>

        <label className="block">
          <span className="mb-2 block text-sm font-medium text-gray-700">好友邀请人奖励</span>
          <input
            type="number"
            min="0"
            step="0.01"
            value={formState.userReferralInviterReward}
            onChange={(event) => updateField("userReferralInviterReward", event.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
          />
        </label>

        <label className="block">
          <span className="mb-2 block text-sm font-medium text-gray-700">好友被邀请人奖励</span>
          <input
            type="number"
            min="0"
            step="0.01"
            value={formState.userReferralInviteeReward}
            onChange={(event) => updateField("userReferralInviteeReward", event.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
          />
        </label>

        <label className="block">
          <span className="mb-2 block text-sm font-medium text-gray-700">代理邀请人奖励</span>
          <input
            type="number"
            min="0"
            step="0.01"
            value={formState.agentInvitationReward}
            onChange={(event) => updateField("agentInvitationReward", event.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
          />
        </label>

        <div className="md:col-span-2 flex items-center justify-end">
          <button
            type="submit"
            disabled={isSubmitting || isLoading}
            className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300"
          >
            {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
            保存配置
          </button>
        </div>
      </form>
    </div>
  );
};

export default AdminReferralRewardSettings;
