'use client';

import Image from 'next/image';
import { FormEvent, useState } from 'react';
import {
  ArrowRight,
  Eye,
  EyeOff,
  Lock,
  Mail,
  ShieldCheck,
} from 'lucide-react';

type DesktopLoginPayload = {
  identifier: string;
  password: string;
  rememberMe: boolean;
};

interface DesktopLoginViewProps {
  isSubmitting: boolean;
  isCheckingSession?: boolean;
  errorMessage?: string;
  onSubmit: (payload: DesktopLoginPayload) => Promise<void>;
  onSwitchToRegister?: () => void;
  onForgotPassword?: () => void;
}

const DesktopLoginView: React.FC<DesktopLoginViewProps> = ({
  isSubmitting,
  isCheckingSession = false,
  errorMessage,
  onSubmit,
  onSwitchToRegister,
  onForgotPassword,
}) => {
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [localError, setLocalError] = useState('');
  const isDisabled = isSubmitting || isCheckingSession;
  const visibleError = errorMessage || localError;

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!identifier.trim() || !password) {
      setLocalError('请输入邮箱/手机号和密码');
      return;
    }

    setLocalError('');

    try {
      await onSubmit({ identifier: identifier.trim(), password, rememberMe });
      setIdentifier('');
      setPassword('');
    } catch {
      // 上层 authError 会展示服务端错误，这里只保留本地校验。
    }
  };

  return (
    <main className="min-h-[calc(100vh-54px)] bg-[#f3f6fa] text-slate-950">
      <div className="mx-auto flex min-h-[calc(100vh-54px)] w-full max-w-6xl flex-col px-5 py-6 sm:px-8">
        <header className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-lg border border-slate-200 bg-white shadow-sm">
              <Image
                src="/logo.png"
                width={34}
                height={20}
                alt="LoomAI"
                priority
                className="h-auto w-8"
              />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-950">LoomAI Desktop</p>
              <p className="text-xs text-slate-500">桌面工作区</p>
            </div>
          </div>

          <div className="hidden items-center gap-2 text-sm font-medium text-emerald-700 sm:flex">
            <ShieldCheck className="h-4 w-4" />
            安全登录
          </div>
        </header>

        <section className="flex flex-1 items-center justify-center py-10">
          <div className="w-full max-w-[432px]">
            <div className="mb-7 text-center">
              <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-lg border border-slate-200 bg-white shadow-sm">
                <Image
                  src="/logo.png"
                  width={42}
                  height={24}
                  alt="LoomAI"
                  priority
                  className="h-auto w-10"
                />
              </div>
              <p className="text-sm font-medium text-blue-700">桌面端登录</p>
              <h1 className="mt-2 text-2xl font-semibold text-slate-950">登录账号</h1>
              <p className="mt-3 text-sm leading-6 text-slate-500">
                {isCheckingSession ? '正在检查本机登录状态' : '使用手机号或邮箱登录'}
              </p>
            </div>

            <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
              <form className="space-y-5" onSubmit={handleSubmit}>
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-slate-700" htmlFor="desktop-login-identifier">
                    邮箱/手机号
                  </label>
                  <div className="relative">
                    <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                    <input
                      id="desktop-login-identifier"
                      type="text"
                      value={identifier}
                      onChange={(event) => {
                        setIdentifier(event.target.value);
                        if (localError) setLocalError('');
                      }}
                      className="h-11 w-full rounded-lg border border-slate-300 bg-white pl-10 pr-3 text-sm text-slate-950 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
                      placeholder="请输入邮箱或手机号"
                      autoComplete="username"
                      disabled={isDisabled}
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between gap-3">
                    <label className="block text-sm font-medium text-slate-700" htmlFor="desktop-login-password">
                      密码
                    </label>
                    {onForgotPassword && (
                      <button
                        type="button"
                        onClick={onForgotPassword}
                        className="text-sm font-medium text-blue-700 hover:text-blue-800 disabled:text-slate-400"
                        disabled={isDisabled}
                      >
                        忘记密码？
                      </button>
                    )}
                  </div>
                  <div className="relative">
                    <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                    <input
                      id="desktop-login-password"
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(event) => {
                        setPassword(event.target.value);
                        if (localError) setLocalError('');
                      }}
                      className="h-11 w-full rounded-lg border border-slate-300 bg-white pl-10 pr-11 text-sm text-slate-950 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
                      placeholder="请输入密码"
                      autoComplete="current-password"
                      disabled={isDisabled}
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword((value) => !value)}
                      className="absolute right-2 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100 hover:text-slate-800 disabled:text-slate-300"
                      disabled={isDisabled}
                      aria-label={showPassword ? '隐藏密码' : '显示密码'}
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>

                <div className="flex items-center justify-between gap-3">
                  <label className="flex items-center gap-2 text-sm text-slate-600">
                    <input
                      type="checkbox"
                      checked={rememberMe}
                      onChange={(event) => setRememberMe(event.target.checked)}
                      className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-200"
                      disabled={isDisabled}
                    />
                    记住我
                  </label>
                </div>

                {visibleError && (
                  <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
                    {visibleError}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={isDisabled}
                  className="flex h-11 w-full items-center justify-center gap-2 rounded-lg bg-slate-950 px-4 text-sm font-semibold text-white transition-colors hover:bg-slate-800 disabled:bg-slate-400"
                >
                  {isCheckingSession ? '正在检查登录状态' : isSubmitting ? '登录中...' : '登录'}
                  {!isDisabled && <ArrowRight className="h-4 w-4" />}
                </button>
              </form>

              {onSwitchToRegister && (
                <div className="mt-6 border-t border-slate-200 pt-5 text-center text-sm text-slate-600">
                  还没有账号？
                  <button
                    type="button"
                    onClick={onSwitchToRegister}
                    className="ml-1 font-semibold text-blue-700 hover:text-blue-800 disabled:text-slate-400"
                    disabled={isDisabled}
                  >
                    立即注册
                  </button>
                </div>
              )}
            </div>
          </div>
        </section>
      </div>
    </main>
  );
};

export default DesktopLoginView;
