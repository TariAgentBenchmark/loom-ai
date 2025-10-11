'use client';

import { useState, useEffect, useRef } from 'react';
import { sendVerificationCode, verifyPhoneCode } from '../lib/api';

interface PhoneVerificationProps {
  phone: string;
  onVerified: () => void;
  onCancel: () => void;
}

const PhoneVerification: React.FC<PhoneVerificationProps> = ({ 
  phone, 
  onVerified, 
  onCancel 
}) => {
  const [code, setCode] = useState(['', '', '', '', '', '']);
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState('');
  const [countdown, setCountdown] = useState(0);
  
  // 验证码输入框引用
  const inputRefs = [
    useRef<HTMLInputElement>(null),
    useRef<HTMLInputElement>(null),
    useRef<HTMLInputElement>(null),
    useRef<HTMLInputElement>(null),
    useRef<HTMLInputElement>(null),
    useRef<HTMLInputElement>(null),
  ];
  
  // 倒计时逻辑
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);
  
  // 初始化时自动发送验证码
  useEffect(() => {
    handleSendCode();
    // 聚焦到第一个输入框
    if (inputRefs[0].current) {
      inputRefs[0].current.focus();
    }
  }, []);
  
  // 发送验证码
  const handleSendCode = async () => {
    if (countdown > 0) return;
    
    setIsSending(true);
    setError('');
    
    try {
      await sendVerificationCode({ phone });
      setCountdown(60); // 60秒倒计时
    } catch (err) {
      setError(err instanceof Error ? err.message : '发送验证码失败');
    } finally {
      setIsSending(false);
    }
  };
  
  // 验证验证码
  const handleVerify = async () => {
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
  };
  
  // 处理输入变化
  const handleInputChange = (index: number, value: string) => {
    // 只允许数字
    if (value && !/^\d$/.test(value)) return;
    
    const newCode = [...code];
    newCode[index] = value;
    setCode(newCode);
    
    // 自动跳转到下一个输入框
    if (value && index < 5) {
      inputRefs[index + 1].current?.focus();
    }
  };
  
  // 处理键盘事件
  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    // 退格键处理
    if (e.key === 'Backspace' && !code[index] && index > 0) {
      inputRefs[index - 1].current?.focus();
    }
    
    // Enter键提交验证
    if (e.key === 'Enter' && code.join('').length === 6) {
      handleVerify();
    }
  };
  
  // 粘贴处理
  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text');
    if (/^\d{6}$/.test(pastedData)) {
      setCode(pastedData.split(''));
      inputRefs[5].current?.focus();
    }
  };
  
  // 格式化手机号显示
  const formatPhone = (phone: string) => {
    if (phone.length === 11) {
      return `${phone.slice(0, 3)}****${phone.slice(7)}`;
    }
    return phone;
  };
  
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
            验证码已发送至 <span className="font-medium">{formatPhone(phone)}</span>
          </p>
        </div>
        
        <div className="mb-6">
          <div className="flex justify-between space-x-2">
            {code.map((digit, index) => (
              <input
                key={index}
                ref={inputRefs[index]}
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
          disabled={isLoading || code.join('').length !== 6}
          className="w-full rounded-lg bg-blue-600 px-4 py-2 text-white font-medium hover:bg-blue-700 disabled:from-gray-400 disabled:to-gray-500 disabled:cursor-not-allowed"
        >
          {isLoading ? '验证中...' : '验证'}
        </button>
      </div>
    </div>
  );
};

export default PhoneVerification;