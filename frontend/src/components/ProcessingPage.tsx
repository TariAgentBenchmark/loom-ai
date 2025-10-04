'use client';

import React, { useState } from 'react';
import { History } from 'lucide-react';
import { ProcessingMethod, getProcessingMethodInfo } from '../lib/processing';
import { resolveFileUrl, HistoryTask } from '../lib/api';
import HistoryList from './HistoryList';
import ImagePreview from './ImagePreview';

interface ProcessingPageProps {
  method: ProcessingMethod;
  imagePreview: string | null;
  processedImage: string | null;
  isProcessing: boolean;
  hasUploadedImage: boolean;
  onBack: () => void;
  onOpenPricingModal: () => void;
  onProcessImage: () => void;
  onDragOver: (event: React.DragEvent<HTMLDivElement>) => void;
  onDrop: (event: React.DragEvent<HTMLDivElement>) => void;
  fileInputRef: React.RefObject<HTMLInputElement>;
  onFileInputChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  errorMessage?: string;
  successMessage?: string;
  accessToken?: string;
  promptInstruction?: string;
  onPromptInstructionChange?: (value: string) => void;
}

const ProcessingPage: React.FC<ProcessingPageProps> = ({
  method,
  imagePreview,
  processedImage,
  isProcessing,
  hasUploadedImage,
  onBack,
  onOpenPricingModal,
  onProcessImage,
  onDragOver,
  onDrop,
  fileInputRef,
  onFileInputChange,
  errorMessage,
  successMessage,
  accessToken,
  promptInstruction,
  onPromptInstructionChange,
}) => {
  const info = getProcessingMethodInfo(method);
  const [selectedTask, setSelectedTask] = useState<HistoryTask | null>(null);
  const [showImagePreview, setShowImagePreview] = useState(false);
  const isPromptReady = method !== 'prompt_edit' || Boolean(promptInstruction?.trim());
  const isActionDisabled = !hasUploadedImage || isProcessing || !isPromptReady;

  const handlePromptTemplateSelect = (template: string) => {
    if (onPromptInstructionChange) {
      onPromptInstructionChange(template);
    }
  };

  const promptTemplates = [
    '把图中裙子改成白色',
    '调整背景为浅灰色并保留人物',
    '把模特的上衣改成牛仔材质',
    '让图片中的包包换成黑色皮质',
  ];

  const handleTaskSelect = (task: HistoryTask) => {
    setSelectedTask(task);
    setShowImagePreview(true);
  };

  const handleClosePreview = () => {
    setShowImagePreview(false);
    setSelectedTask(null);
  };

  return (
    <div className="h-screen bg-gray-50 flex flex-col">
      <header className="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
        <div className="flex items-center justify-between px-6 py-4">
          <div className="flex items-center space-x-4">
            <button
              onClick={onBack}
              className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 transition"
            >
              <span>←</span>
              <span>返回</span>
            </button>
            <div className="flex items-center space-x-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white shadow-md overflow-hidden">
                <img
                  src={info.icon}
                  alt={info.title}
                  className="h-6 w-6 object-contain"
                />
              </div>
              <h1 className="text-xl font-bold text-gray-900">{info.title}</h1>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <button
              onClick={onOpenPricingModal}
              className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all shadow-sm"
            >
              套餐充值
            </button>
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <div className="w-80 bg-white border-r border-gray-200 p-6 overflow-y-auto">
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">上传图片</h3>
            <div
              className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-blue-400 transition cursor-pointer min-h-[200px] flex items-center justify-center"
              onDragOver={onDragOver}
              onDrop={onDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              {imagePreview ? (
                <div className="space-y-4">
                  <img
                    src={resolveFileUrl(imagePreview)}
                    alt="Preview"
                    className="mx-auto max-h-32 rounded-lg border border-gray-200"
                  />
                  <p className="text-sm text-gray-500">拖拽图片或点击上传</p>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-gray-100 text-gray-400">
                    ⬆
                  </div>
                  <div>
                    <p className="text-base font-medium text-gray-700">拖拽图片或点击上传</p>
                  </div>
                </div>
              )}
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={onFileInputChange}
              className="hidden"
            />
          </div>

          <div className="mb-6">
            <button
              onClick={onProcessImage}
              disabled={isActionDisabled}
              className="w-full bg-gradient-to-r from-pink-500 to-pink-600 hover:from-pink-600 hover:to-pink-700 disabled:from-gray-400 disabled:to-gray-500 text-white font-medium py-4 px-6 rounded-xl text-lg shadow-lg transition-all transform hover:scale-105 disabled:hover:scale-100"
            >
              {isProcessing ? (
                <div className="flex items-center justify-center space-x-2">
                  <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full" />
                  <span>处理中...</span>
                </div>
              ) : (
                '一键生成'
              )}
            </button>
          </div>

          {method === 'prompt_edit' && (
            <div className="mb-6 space-y-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-base font-semibold text-gray-900">输入指令</h4>
                  <div className="relative">
                    <select
                      className="text-xs border border-gray-200 rounded-lg px-2 py-1 text-gray-600 focus:ring-2 focus:ring-blue-400 focus:border-blue-400"
                      defaultValue=""
                      onChange={(event) => {
                        const value = event.target.value;
                        if (value) {
                          handlePromptTemplateSelect(value);
                          event.target.selectedIndex = 0;
                        }
                      }}
                    >
                      <option value="" disabled>
                        指令参考
                      </option>
                      {promptTemplates.map((template) => (
                        <option key={template} value={template}>
                          {template}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                <textarea
                  value={promptInstruction ?? ''}
                  onChange={(event) => onPromptInstructionChange?.(event.target.value)}
                  placeholder="例如：把图中裙子的颜色改成白色"
                  className="w-full min-h-[110px] rounded-xl border border-gray-200 px-4 py-3 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-400 resize-none"
                />
                <p className="text-xs text-gray-500 mt-2">一句话描述想要修改的细节，AI会自动处理。</p>
              </div>
            </div>
          )}

          <div className="mb-6">
            <h4 className="text-base font-semibold text-gray-900 mb-3">使用提示</h4>
            <p className="text-sm text-gray-600 mb-4">{info.description}</p>
          </div>

          <div>
            <h4 className="text-base font-semibold text-gray-900 mb-3">操作要求示例</h4>
            <div className="space-y-2">
              {info.examples.map((example, index) => (
                <div key={index} className="text-sm text-gray-600">
                  <span className="text-red-400">{index + 1}.</span> {example}
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="flex-1 p-8">
          <div className="flex flex-col items-center justify-center h-full space-y-4">
            {errorMessage && (
              <div className="w-full max-w-lg rounded-xl border border-red-200 bg-red-50 px-6 py-4 text-sm text-red-600">
                {errorMessage}
              </div>
            )}
            {successMessage && !errorMessage && (
              <div className="w-full max-w-lg rounded-xl border border-green-200 bg-green-50 px-6 py-4 text-sm text-green-600">
                {successMessage}
              </div>
            )}
            {processedImage ? (
              <div className="text-center w-full h-full flex flex-col items-center justify-center">
                <img
                  src={resolveFileUrl(processedImage)}
                  alt="Processed"
                  className="max-w-full max-h-[80vh] w-auto h-auto object-contain rounded-lg border border-gray-200 shadow-lg mb-6"
                />
                <a
                  className="inline-flex items-center justify-center bg-green-500 hover:bg-green-600 text-white px-8 py-3 rounded-xl font-medium transition shadow-lg"
                  href={resolveFileUrl(processedImage)}
                  download
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  下载结果
                </a>
              </div>
            ) : (
              <div className="text-center">
                <div className="w-32 h-32 mx-auto mb-6 rounded-full bg-gradient-to-br from-blue-400 via-blue-500 to-blue-600 flex items-center justify-center relative overflow-hidden">
                  <div className="relative w-24 h-24">
                    <div className="absolute inset-0 bg-blue-500 rounded-full"></div>
                    <div className="absolute top-2 left-3 w-4 h-3 bg-green-400 rounded-full"></div>
                    <div className="absolute top-4 right-2 w-3 h-2 bg-green-400 rounded-full"></div>
                    <div className="absolute bottom-3 left-2 w-5 h-4 bg-green-400 rounded-full"></div>
                    <div className="absolute top-1 left-8 w-8 h-2 bg-white rounded-full opacity-70"></div>
                    <div className="absolute bottom-6 right-1 w-6 h-2 bg-white rounded-full opacity-50"></div>
                    <div className="absolute -top-4 left-4 w-2 h-4 bg-red-400 transform rotate-12"></div>
                    <div className="absolute -top-2 right-3 w-3 h-6 bg-yellow-400 transform -rotate-12"></div>
                    <div className="absolute -bottom-2 left-6 w-2 h-4 bg-purple-400 transform rotate-45"></div>
                  </div>
                </div>
                <p className="text-gray-400 text-lg">什么都没有呢，赶快开始吧吧</p>
              </div>
            )}
          </div>
        </div>

        <div className="w-80 bg-white border-l border-gray-200 p-6 overflow-y-auto">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <History className="h-5 w-5 mr-2 text-gray-600" />
            历史记录
          </h3>
          {accessToken ? (
            <HistoryList accessToken={accessToken} onTaskSelect={handleTaskSelect} />
          ) : (
            <div className="text-center text-gray-400 py-8">
              <p className="text-sm">请登录后查看历史记录</p>
            </div>
          )}
        </div>
      </div>

      {/* 图片预览弹窗 */}
      {showImagePreview && selectedTask && (
        <ImagePreview
          task={selectedTask}
          onClose={handleClosePreview}
          accessToken={accessToken || ''}
        />
      )}
    </div>
  );
};

export default ProcessingPage;
