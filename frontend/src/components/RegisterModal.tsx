'use client';

import { useState } from 'react';

interface RegisterModalProps {
  isOpen: boolean;
  isSubmitting: boolean;
  errorMessage?: string;
  onClose: () => void;
  onSubmit: (payload: { phone: string; password: string; confirmPassword: string; nickname?: string; email?: string }) => Promise<void>;
  onSwitchToLogin: () => void;
}

const RegisterModal: React.FC<RegisterModalProps> = ({ 
  isOpen, 
  isSubmitting, 
  errorMessage, 
  onClose, 
  onSubmit,
  onSwitchToLogin
}) => {
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [nickname, setNickname] = useState('');
  const [email, setEmail] = useState('');
  const [localError, setLocalError] = useState('');

  if (!isOpen) {
    return null;
  }

  const validatePassword = (pwd: string): { isValid: boolean; message: string } => {
    if (pwd.length < 8) {
      return { isValid: false, message: '密码长度至少需要8位字符' };
    }
    
    // Check for at least one letter
    if (!/[a-zA-Z]/.test(pwd)) {
      return { isValid: false, message: '密码需要包含至少一个字母' };
    }
    
    // Check for at least one number
    if (!/\d/.test(pwd)) {
      return { isValid: false, message: '密码需要包含至少一个数字' };
    }
    
    // Check for common weak passwords
    const commonPasswords = ['password', '12345678', '87654321', 'abcdefgh', 'qwertyui'];
    if (commonPasswords.includes(pwd.toLowerCase())) {
      return { isValid: false, message: '密码过于简单，请使用更复杂的密码' };
    }
    
    return { isValid: true, message: '' };
  };

  const validateForm = () => {
    if (!phone || !password || !confirmPassword) {
      setLocalError('请填写所有必填字段（手机号、密码、确认密码）');
      return false;
    }

    // Basic phone validation
    const phoneRegex = /^1[3-9]\d{9}$/; // Chinese mobile number format
    if (!phoneRegex.test(phone)) {
      setLocalError('请输入有效的手机号');
      return false;
    }

    // If email is provided, validate it
    if (email) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(email)) {
        setLocalError('请输入有效的邮箱地址');
        return false;
      }
    }

    const passwordValidation = validatePassword(password);
    if (!passwordValidation.isValid) {
      setLocalError(passwordValidation.message);
      return false;
    }

    if (password !== confirmPassword) {
      setLocalError('两次输入的密码不一致，请重新输入');
      return false;
    }

    return true;
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    console.log('RegisterModal: Form submitted', { phone, password: '***', confirmPassword: '***', nickname, email });

    // Clear any previous error
    setLocalError('');

    if (!validateForm()) {
      console.log('RegisterModal: Form validation failed');
      return;
    }

    console.log('RegisterModal: Calling onSubmit');

    try {
      await onSubmit({
        phone,
        password,
        confirmPassword,
        nickname: nickname || undefined,
        email: email || undefined
      });
      console.log('RegisterModal: onSubmit completed successfully');
      setPhone('');
      setPassword('');
      setConfirmPassword('');
      setNickname('');
      setEmail('');
    } catch (error) {
      console.error('RegisterModal: onSubmit failed', error);
      // 交由上层 errorMessage 展示，必要时可添加本地兜底
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-2 sm:p-4">
      <div className="w-full max-w-md rounded-xl sm:rounded-2xl bg-white shadow-2xl">
        <div className="border-b border-gray-200 px-4 py-3 sm:px-6 sm:py-4 flex items-center justify-between">
          <h2 className="text-base sm:text-lg font-semibold text-gray-900">注册账号</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl sm:text-2xl leading-none"
            aria-label="关闭注册窗口"
            disabled={isSubmitting}
          >
            ×
          </button>
        </div>

        <form className="px-4 py-4 sm:px-6 sm:py-6 space-y-3 sm:space-y-4" onSubmit={handleSubmit}>
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700" htmlFor="register-phone">
              手机号 <span className="text-red-500">*</span>
            </label>
            <input
              id="register-phone"
              type="tel"
              value={phone}
              onChange={(event) => setPhone(event.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
              placeholder="请输入手机号"
              disabled={isSubmitting}
              required
            />
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700" htmlFor="register-password">
              密码 <span className="text-red-500">*</span>
            </label>
            <input
              id="register-password"
              type="password"
              value={password}
              onChange={(event) => {
                setPassword(event.target.value);
                // Clear error when user starts typing again
                if (localError && validatePassword(event.target.value).isValid) {
                  setLocalError('');
                }
              }}
              className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 ${
                localError && !validatePassword(password).isValid
                  ? 'border-red-300 focus:border-red-500 focus:ring-red-200'
                  : 'border-gray-300 focus:border-blue-500 focus:ring-blue-200'
              }`}
              placeholder="至少8位密码"
              disabled={isSubmitting}
              required
            />
            {password && (
              <div className="text-xs space-y-1 mt-1">
                <div className={`flex items-center ${password.length >= 8 ? 'text-green-600' : 'text-gray-400'}`}>
                  <span className="mr-1">{password.length >= 8 ? '✓' : '○'}</span>
                  <span>至少8位字符</span>
                </div>
                <div className={`flex items-center ${/[a-zA-Z]/.test(password) ? 'text-green-600' : 'text-gray-400'}`}>
                  <span className="mr-1">{/[a-zA-Z]/.test(password) ? '✓' : '○'}</span>
                  <span>包含字母</span>
                </div>
                <div className={`flex items-center ${/\d/.test(password) ? 'text-green-600' : 'text-gray-400'}`}>
                  <span className="mr-1">{/\d/.test(password) ? '✓' : '○'}</span>
                  <span>包含数字</span>
                </div>
              </div>
            )}
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700" htmlFor="register-confirm-password">
              确认密码 <span className="text-red-500">*</span>
            </label>
            <input
              id="register-confirm-password"
              type="password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
              placeholder="再次输入密码"
              disabled={isSubmitting}
              required
            />
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700" htmlFor="register-nickname">
              昵称
            </label>
            <input
              id="register-nickname"
              type="text"
              value={nickname}
              onChange={(event) => setNickname(event.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
              placeholder="选填"
              disabled={isSubmitting}
            />
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700" htmlFor="register-email">
              邮箱
            </label>
            <input
              id="register-email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
              placeholder="选填"
              disabled={isSubmitting}
            />
          </div>

          {(localError || errorMessage) && (
            <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 sm:px-4 text-xs text-red-600">
              {errorMessage || localError}
            </div>
          )}

          <div className="text-xs text-gray-500">
            注册即表示您同意我们的服务条款和隐私政策
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-lg bg-gradient-to-r from-blue-500 to-blue-600 px-4 py-2 text-sm font-medium text-white shadow hover:from-blue-600 hover:to-blue-700 disabled:from-gray-400 disabled:to-gray-500"
          >
            {isSubmitting ? '注册中…' : '注册'}
          </button>

          <div className="text-center text-sm text-gray-600">
            已有账号？
            <button
              type="button"
              onClick={onSwitchToLogin}
              className="ml-1 text-blue-600 hover:text-blue-700 font-medium"
              disabled={isSubmitting}
            >
              立即登录
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default RegisterModal;