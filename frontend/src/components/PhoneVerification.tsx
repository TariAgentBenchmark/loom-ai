'use client';

import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { sendVerificationCode, verifyPhoneCode } from '../lib/api';

interface PhoneVerificationProps {
  phone: string;
  onVerified: () => void;
  onCancel: () => void;
  autoSendOnMount?: boolean;
  initialCountdown?: number;
  onCodeSent?: (expiresInSeconds: number) => void;
}

const CODE_LENGTH = 6;

const PhoneVerification: React.FC<PhoneVerificationProps> = ({
  phone,
  onVerified,
  onCancel,
  autoSendOnMount = true,
  initialCountdown = 0,
  onCodeSent,
}) => {
  const [code, setCode] = useState(Array<string>(CODE_LENGTH).fill(''));
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState('');
  const [countdown, setCountdown] = useState(initialCountdown);
  
  // 验证码输入框引用
  const inputRefs = useRef<Array<HTMLInputElement | null>>(Array(CODE_LENGTH).fill(null));
  
  // 倒计时逻辑
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);
  
  // 初始化时自动发送验证码
  useEffect(() => {
    if (autoSendOnMount) {
      void handleSendCode();
    }
    inputRefs.current[0]?.focus();
  }, [autoSendOnMount, handleSendCode]);
  
  // 发送验证码
  const handleSendCode = useCallback(async () => {
    if (countdown > 0) return;
    
    setIsSending(true);
    setError('');
    
    try {
      const response = await sendVerificationCode({ phone });
      const expiresInSeconds = Math.max(
        0,
        Math.floor(response.data?.expires_in ?? 60),
      );
      setCountdown(expiresInSeconds);
      onCodeSent?.(expiresInSeconds);
    } catch (err) {
      setError(err instanceof Error ? err.message : '发送验证码失败');
    } finally {
      setIsSending(false);
    }
  }, [countdown, onCodeSent, phone]);
  
  // 验证验证码
  const handleVerify = useCallback(async () => {
    const codeString = code.join('');
    if (codeString.length !== 6) {
      setError('请输入完整的验证码');
      return;
    }
    
    setIsLoading(true);
    setError('');
    
    try {
      await verifyPhoneCode({ phone, code: codeString });
      onVerified();
    } catch (err) {
      setError(err instanceof Error ? err.message : '验证码错误');
    } finally {
      setIsLoading(false);
    }
  }, [code, onVerified, phone]);
  
  // 处理输入变化
  const handleInputChange = useCallback((index: number, value: string) => {
    // 只允许数字
    if (value && !/^\d$/.test(value)) return;
    
    const newCode = [...code];
    newCode[index] = value;
    setCode(newCode);
    
    // 自动跳转到下一个输入框
    if (value && index < CODE_LENGTH - 1) {
      inputRefs.current[index + 1]?.focus();
    }
  }, [code]);
  
  // 处理键盘事件
  const handleKeyDown = useCallback((index: number, e: React.KeyboardEvent) => {
    // 退格键处理
    if (e.key === 'Backspace' && !code[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
    
    // Enter键提交验证
    if (e.key === 'Enter' && code.join('').length === CODE_LENGTH) {
      void handleVerify();
    }
  }, [code, handleVerify]);
  
  // 粘贴处理
  const handlePaste = useCallback((e: React.ClipboardEvent) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text');
    if (new RegExp(`^\\d{${CODE_LENGTH}}$`).test(pastedData)) {
      setCode(pastedData.split(''));
      inputRefs.current[CODE_LENGTH - 1]?.focus();
    }
  }, []);
  
  // 格式化手机号显示
  const formatPhone = useCallback((phoneNumber: string) => {
    if (phoneNumber.length === 11) {
      return `${phoneNumber.slice(0, 3)}****${phoneNumber.slice(7)}`;
    }
    return phoneNumber;
  }, []);

  const maskedPhone = useMemo(() => formatPhone(phone), [formatPhone, phone]);

  useEffect(() => {
    setCode(Array(CODE_LENGTH).fill(''));
    setCountdown(initialCountdown);
    setError('');
  }, [initialCountdown]);

  useEffect(() => {
    if (!autoSendOnMount) {
      return;
    }
    void handleSendCode();
  }, [autoSendOnMount, handleSendCode]);

  useEffect(() => {
    inputRefs.current[0]?.focus();
  }, []);
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
      <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-2xl">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-900">手机验证</h2>
          <button
            onClick={onCancel}
            className="text-gray-400 hover:text-gray-600 text-xl leading-none"
            aria-label="关闭验证窗口"
          >
            ×
          </button>
        </div>
        
        <div className="mb-6">
          <p className="text-sm text-gray-600">
            验证码已发送至 <span className="font-medium">{maskedPhone}</span>
          </p>
        </div>
        
        <div className="mb-6">
          <div className="flex justify-between space-x-2">
            {code.map((digit, index) => (
              <input
                key={index}
                ref={(el) => (inputRefs.current[index] = el)}
                type="text"
                inputMode="numeric"
                maxLength={1}
                value={digit}
                onChange={(e) => handleInputChange(index, e.target.value)}
                onKeyDown={(e) => handleKeyDown(index, e)}
                onPaste={index === 0 ? handlePaste : undefined}
                className="w-12 h-12 text-center text-lg font-semibold border border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                disabled={isLoading}
              />
            ))}
          </div>
        </div>
        
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
            {error}
          </div>
        )}
        
        <div className="mb-6 flex justify-between items-center">
          <button
            type="button"
            onClick={handleSendCode}
            disabled={countdown > 0 || isSending || isLoading}
            className="text-sm text-blue-600 hover:text-blue-700 disabled:text-gray-400"
          >
            {isSending ? '发送中...' : countdown > 0 ? `重新发送 (${countdown}s)` : '重新发送'}
          </button>
          
          <button
            type="button"
            onClick={onCancel}
            disabled={isLoading}
            className="text-sm text-gray-600 hover:text-gray-700 disabled:text-gray-400"
          >
            取消
          </button>
        </div>
        
        <button
          onClick={handleVerify}
          disabled={isLoading || code.join('').length !== CODE_LENGTH}
          className="w-full rounded-lg bg-blue-600 px-4 py-2 text-white font-medium hover:bg-blue-700 disabled:from-gray-400 disabled:to-gray-500 disabled:cursor-not-allowed"
        >
          {isLoading ? '验证中...' : '验证'}
        </button>
      </div>
    </div>
  );
};

export default PhoneVerification;
