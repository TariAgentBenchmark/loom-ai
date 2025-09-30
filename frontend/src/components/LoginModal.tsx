'use client';

import { useState } from 'react';

interface LoginModalProps {
  isOpen: boolean;
  isSubmitting: boolean;
  errorMessage?: string;
  onClose: () => void;
  onSubmit: (payload: { email: string; password: string; rememberMe: boolean }) => Promise<void>;
}

const LoginModal: React.FC<LoginModalProps> = ({ isOpen, isSubmitting, errorMessage, onClose, onSubmit }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(true);
  const [localError, setLocalError] = useState('');

  if (!isOpen) {
    return null;
  }

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!email || !password) {
      setLocalError('请输入邮箱和密码');
      return;
    }

    setLocalError('');

    try {
      await onSubmit({ email, password, rememberMe });
      setEmail('');
      setPassword('');
    } catch (error) {
      // 交由上层 errorMessage 展示，必要时可添加本地兜底
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
      <div className="w-full max-w-md rounded-2xl bg-white shadow-2xl">
        <div className="border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">登录账号</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
            aria-label="关闭登录窗口"
            disabled={isSubmitting}
          >
            ×
          </button>
        </div>

        <form className="px-6 py-6 space-y-4" onSubmit={handleSubmit}>
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700" htmlFor="login-email">
              邮箱
            </label>
            <input
              id="login-email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
              placeholder="name@example.com"
              disabled={isSubmitting}
              required
            />
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700" htmlFor="login-password">
              密码
            </label>
            <input
              id="login-password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
              placeholder="请输入密码"
              disabled={isSubmitting}
              required
            />
          </div>

          <label className="flex items-center space-x-2 text-sm text-gray-600">
            <input
              type="checkbox"
              checked={rememberMe}
              onChange={(event) => setRememberMe(event.target.checked)}
              className="rounded border-gray-300"
              disabled={isSubmitting}
            />
            <span>记住我</span>
          </label>

          {(localError || errorMessage) && (
            <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-2 text-xs text-red-600">
              {errorMessage ?? localError}
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-lg bg-gradient-to-r from-blue-500 to-blue-600 px-4 py-2 text-sm font-medium text-white shadow hover:from-blue-600 hover:to-blue-700 disabled:from-gray-400 disabled:to-gray-500"
          >
            {isSubmitting ? '登录中…' : '登录'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default LoginModal;


