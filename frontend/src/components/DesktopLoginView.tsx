'use client';

import Image from 'next/image';
import { FormEvent, useState } from 'react';
import {
  ArrowRight,
  CheckCircle2,
  Eye,
  EyeOff,
  Lock,
  Mail,
  Monitor,
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
    <main className="min-h-[calc(100vh-54px)] bg-[#eef2f7] text-slate-950">
      <div className="mx-auto flex min-h-[calc(100vh-54px)] w-full max-w-6xl items-center justify-center px-5 py-8 sm:px-8">
        <section className="grid w-full max-w-[920px] overflow-hidden rounded-lg border border-slate-200 bg-white shadow-[0_20px_60px_rgba(15,23,42,0.12)] lg:grid-cols-[320px_1fr]">
          <aside className="hidden bg-slate-950 p-7 text-white lg:flex lg:flex-col">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-white shadow-sm">
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
                <p className="text-sm font-semibold">LoomAI Desktop</p>
                <p className="text-xs text-slate-400">桌面工作区</p>
              </div>
            </div>

            <div className="mt-16">
              <div className="mb-5 flex h-10 w-10 items-center justify-center rounded-lg bg-cyan-400/15 text-cyan-200">
                <Monitor className="h-5 w-5" />
              </div>
              <h1 className="max-w-[240px] text-2xl font-semibold leading-tight tracking-normal">
                进入创作工作台
              </h1>
              <p className="mt-4 text-sm leading-6 text-slate-300">
                登录后同步任务、历史记录和账户权益，桌面端会保持独立的会话状态。
              </p>
            </div>

            <div className="mt-auto space-y-3 border-t border-white/10 pt-6 text-sm text-slate-300">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-cyan-300" />
                独立桌面登录流程
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-cyan-300" />
                加密传输账号信息
              </div>
            </div>
          </aside>

          <div className="flex min-h-[560px] flex-col">
            <header className="flex h-12 items-center justify-between border-b border-slate-100 bg-slate-50 px-5">
              <div className="flex items-center gap-2">
                <span className="h-3 w-3 rounded-full bg-[#ff5f57]" />
                <span className="h-3 w-3 rounded-full bg-[#ffbd2e]" />
                <span className="h-3 w-3 rounded-full bg-[#28c840]" />
              </div>
              <div className="flex items-center gap-2 text-xs font-medium text-emerald-700">
                <ShieldCheck className="h-4 w-4" />
                安全登录
              </div>
            </header>

            <div className="flex flex-1 items-center justify-center px-6 py-8 sm:px-10">
              <div className="w-full max-w-[420px]">
                <div className="mb-8">
                  <div className="mb-5 flex items-center gap-3 lg:hidden">
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
                  <p className="text-sm font-semibold text-blue-700">桌面端登录</p>
                  <h2 className="mt-3 text-3xl font-semibold text-slate-950">欢迎回来</h2>
                  <p className="mt-3 text-sm leading-6 text-slate-500">
                    {isCheckingSession ? '正在检查本机登录状态' : '使用手机号或邮箱继续使用 LoomAI。'}
                  </p>
                </div>

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
                        className="h-12 w-full rounded-lg border border-slate-300 bg-white pl-10 pr-3 text-sm text-slate-950 placeholder:text-slate-400 transition-colors focus:border-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-100"
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
                        className="h-12 w-full rounded-lg border border-slate-300 bg-white pl-10 pr-11 text-sm text-slate-950 placeholder:text-slate-400 transition-colors focus:border-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-100"
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
                    className="flex h-12 w-full items-center justify-center gap-2 rounded-lg bg-slate-950 px-4 text-sm font-semibold text-white transition-colors hover:bg-slate-800 disabled:bg-slate-400"
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
          </div>
        </section>
      </div>
    </main>
  );
};

export default DesktopLoginView;
