'use client';

import { FormEvent, useEffect, useState } from 'react';

interface ForgotPasswordModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSendCode: (phone: string) => Promise<void>;
  onSubmit: (payload: { phone: string; code: string; newPassword: string; confirmPassword: string }) => Promise<void>;
  onSwitchToLogin?: () => void;
}

const ForgotPasswordModal: React.FC<ForgotPasswordModalProps> = ({
  isOpen,
  onClose,
  onSendCode,
  onSubmit,
  onSwitchToLogin,
}) => {
  const [phone, setPhone] = useState('');
  const [code, setCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [isSendingCode, setIsSendingCode] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [countdown, setCountdown] = useState(0);

  useEffect(() => {
    if (!isOpen) {
      setPhone('');
      setCode('');
      setNewPassword('');
      setConfirmPassword('');
      setErrorMessage('');
      setSuccessMessage('');
      setCountdown(0);
    }
  }, [isOpen]);

  useEffect(() => {
    if (countdown <= 0) {
      return;
    }

    const timer = setInterval(() => {
      setCountdown((prev) => (prev <= 1 ? 0 : prev - 1));
    }, 1000);

    return () => clearInterval(timer);
  }, [countdown]);

  if (!isOpen) {
    return null;
  }

  const handleSendCode = async () => {
    if (!phone || phone.trim().length < 6) {
      setErrorMessage('请输入正确的注册手机号');
      return;
    }

    setErrorMessage('');
    setSuccessMessage('');
    setIsSendingCode(true);

    try {
      await onSendCode(phone.trim());
      setSuccessMessage('验证码已发送，请注意查收');
      setCountdown(60);
    } catch (error) {
      setErrorMessage((error as Error)?.message ?? '验证码发送失败，请稍后重试');
    } finally {
      setIsSendingCode(false);
    }
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!phone || !code || !newPassword || !confirmPassword) {
      setErrorMessage('请填写完整的手机号、验证码和新密码');
      return;
    }

    if (newPassword.length < 8) {
      setErrorMessage('新密码长度至少需要8位');
      return;
    }

    if (newPassword !== confirmPassword) {
      setErrorMessage('两次输入的新密码不一致');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage('');
    setSuccessMessage('');

    try {
      await onSubmit({ phone: phone.trim(), code: code.trim(), newPassword, confirmPassword });
      setSuccessMessage('密码重置成功，请使用新密码登录');
      setTimeout(() => {
        onClose();
        onSwitchToLogin?.();
      }, 1500);
    } catch (error) {
      setErrorMessage((error as Error)?.message ?? '密码重置失败，请稍后再试');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-2 sm:p-4">
      <div className="w-full max-w-md rounded-xl sm:rounded-2xl bg-white shadow-2xl">
        <div className="border-b border-gray-200 px-4 py-3 sm:px-6 sm:py-4 flex items-center justify-between">
          <h2 className="text-base sm:text-lg font-semibold text-gray-900">找回密码</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl sm:text-2xl leading-none"
            aria-label="关闭找回密码窗口"
            disabled={isSubmitting || isSendingCode}
          >
            ×
          </button>
        </div>

        <form className="px-4 py-4 sm:px-6 sm:py-6 space-y-4" onSubmit={handleSubmit}>
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700" htmlFor="forgot-phone">
              注册手机号
            </label>
            <input
              id="forgot-phone"
              type="tel"
              value={phone}
              onChange={(event) => setPhone(event.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
              placeholder="请输入注册手机号"
              disabled={isSubmitting}
              required
            />
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700" htmlFor="forgot-code">
              验证码
            </label>
            <div className="flex space-x-3">
              <input
                id="forgot-code"
                type="text"
                value={code}
                onChange={(event) => setCode(event.target.value)}
                className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                placeholder="请输入验证码"
                disabled={isSubmitting}
                required
              />
              <button
                type="button"
                onClick={handleSendCode}
                className="w-32 rounded-lg border border-blue-500 px-3 py-2 text-sm font-medium text-blue-600 hover:bg-blue-50 disabled:border-gray-300 disabled:text-gray-400"
                disabled={isSendingCode || countdown > 0 || isSubmitting}
              >
                {countdown > 0 ? `${countdown}s后重发` : '获取验证码'}
              </button>
            </div>
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700" htmlFor="forgot-new-password">
              新密码
            </label>
            <input
              id="forgot-new-password"
              type="password"
              value={newPassword}
              onChange={(event) => setNewPassword(event.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
              placeholder="至少8位密码"
              disabled={isSubmitting}
              required
              minLength={8}
            />
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700" htmlFor="forgot-confirm-password">
              确认新密码
            </label>
            <input
              id="forgot-confirm-password"
              type="password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
              placeholder="再次输入新密码"
              disabled={isSubmitting}
              required
              minLength={8}
            />
          </div>

          {(errorMessage || successMessage) && (
            <div
              className={`rounded-lg px-3 py-2 text-sm ${
                errorMessage
                  ? 'border border-red-200 bg-red-50 text-red-600'
                  : 'border border-green-200 bg-green-50 text-green-600'
              }`}
            >
              {errorMessage || successMessage}
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-lg bg-gradient-to-r from-blue-500 to-blue-600 px-4 py-2 text-sm font-medium text-white shadow hover:from-blue-600 hover:to-blue-700 disabled:from-gray-400 disabled:to-gray-500"
          >
            {isSubmitting ? '重置中…' : '重置密码'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default ForgotPasswordModal;
