'use client';

import React from 'react';
import { History } from 'lucide-react';
import {
  ProcessingMethod,
  ProcessingOptions,
  getProcessingMethodInfo,
} from '../lib/processing';
import { resolveFileUrl } from '../lib/api';

interface ProcessingPageProps {
  method: ProcessingMethod;
  imagePreview: string | null;
  processedImage: string | null;
  isProcessing: boolean;
  hasUploadedImage: boolean;
  options: ProcessingOptions;
  updateOptions: <T extends ProcessingMethod>(
    method: T,
    updates: Partial<ProcessingOptions[T]>
  ) => void;
  onBack: () => void;
  onOpenPricingModal: () => void;
  onProcessImage: () => void;
  onDragOver: (event: React.DragEvent<HTMLDivElement>) => void;
  onDrop: (event: React.DragEvent<HTMLDivElement>) => void;
  fileInputRef: React.RefObject<HTMLInputElement>;
  onFileInputChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  errorMessage?: string;
  successMessage?: string;
}

const ProcessingPage: React.FC<ProcessingPageProps> = ({
  method,
  imagePreview,
  processedImage,
  isProcessing,
  hasUploadedImage,
  options,
  updateOptions,
  onBack,
  onOpenPricingModal,
  onProcessImage,
  onDragOver,
  onDrop,
  fileInputRef,
  onFileInputChange,
  errorMessage,
  successMessage,
}) => {
  const info = getProcessingMethodInfo(method);

  const renderOptions = () => {
    switch (method) {
      case 'seamless':
        return (
          <div className="grid grid-cols-2 gap-4">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={options.seamless.removeBackground}
                onChange={(e) =>
                  updateOptions('seamless', { removeBackground: e.target.checked })
                }
                className="rounded border-gray-300"
              />
              <span className="text-sm">去重叠区</span>
            </label>
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={options.seamless.seamlessLoop}
                onChange={(e) =>
                  updateOptions('seamless', { seamlessLoop: e.target.checked })
                }
                className="rounded border-gray-300"
              />
              <span className="text-sm">无缝循环</span>
            </label>
          </div>
        );
      case 'style':
        return (
          <div className="space-y-4">
            <div>
              <p className="text-sm font-medium mb-2">输出风格</p>
              <div className="flex space-x-2">
                <button
                  onClick={() => updateOptions('style', { outputStyle: 'vector' })}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition ${
                    options.style.outputStyle === 'vector'
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  矢量风格
                </button>
                <button
                  onClick={() =>
                    updateOptions('style', { outputStyle: 'seamless' })
                  }
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition ${
                    options.style.outputStyle === 'seamless'
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  无缝循环
                </button>
              </div>
            </div>
            <div>
              <p className="text-sm font-medium mb-2">输出比例</p>
              <div className="flex space-x-2">
                {['1:1', '2:3', '3:2'].map((ratio) => (
                  <button
                    key={ratio}
                    onClick={() =>
                      updateOptions('style', { outputRatio: ratio as '1:1' | '2:3' | '3:2' })
                    }
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition ${
                      options.style.outputRatio === ratio
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    {ratio}
                  </button>
                ))}
              </div>
            </div>
          </div>
        );
      case 'embroidery':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">针线类型</label>
              <div className="flex space-x-2">
                {[
                  { value: 'fine', label: '细针' },
                  { value: 'medium', label: '中等' },
                  { value: 'thick', label: '粗针' },
                ].map((type) => (
                  <button
                    key={type.value}
                    onClick={() =>
                      updateOptions('embroidery', {
                        needleType: type.value as 'fine' | 'medium' | 'thick',
                      })
                    }
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition ${
                      options.embroidery.needleType === type.value
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    {type.label}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">针脚密度</label>
              <div className="flex space-x-2">
                {[
                  { value: 'low', label: '稀疏' },
                  { value: 'medium', label: '中等' },
                  { value: 'high', label: '密集' },
                ].map((type) => (
                  <button
                    key={type.value}
                    onClick={() =>
                      updateOptions('embroidery', {
                        stitchDensity: type.value as 'low' | 'medium' | 'high',
                      })
                    }
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition ${
                      options.embroidery.stitchDensity === type.value
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    {type.label}
                  </button>
                ))}
              </div>
            </div>
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={options.embroidery.enhanceDetails}
                onChange={(e) =>
                  updateOptions('embroidery', { enhanceDetails: e.target.checked })
                }
                className="rounded border-gray-300"
              />
              <span className="text-sm">增强细节纹理</span>
            </label>
          </div>
        );
      case 'extract_edit':
        return (
          <div className="space-y-4">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={options.extract_edit.voiceControl}
                onChange={(e) =>
                  updateOptions('extract_edit', { voiceControl: e.target.checked })
                }
                className="rounded border-gray-300"
              />
              <span className="text-sm">语音控制</span>
            </label>
            <div>
              <label className="block text-sm font-medium mb-2">编辑模式</label>
              <div className="flex space-x-2">
                {[
                  { value: 'smart', label: '智能模式' },
                  { value: 'manual', label: '手动模式' },
                ].map((mode) => (
                  <button
                    key={mode.value}
                    onClick={() =>
                      updateOptions('extract_edit', {
                        editMode: mode.value as 'smart' | 'manual',
                      })
                    }
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition ${
                      options.extract_edit.editMode === mode.value
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    {mode.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        );
      case 'extract_pattern':
        return (
          <div className="space-y-4">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={options.extract_pattern.preprocessing}
                onChange={(e) =>
                  updateOptions('extract_pattern', {
                    preprocessing: e.target.checked,
                  })
                }
                className="rounded border-gray-300"
              />
              <span className="text-sm">启用预处理</span>
            </label>
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={options.extract_pattern.voiceControl}
                onChange={(e) =>
                  updateOptions('extract_pattern', {
                    voiceControl: e.target.checked,
                  })
                }
                className="rounded border-gray-300"
              />
              <span className="text-sm">语音控制</span>
            </label>
            <div>
              <label className="block text-sm font-medium mb-2">花型类型</label>
              <div className="flex space-x-2">
                {[
                  { value: 'floral', label: '花卉' },
                  { value: 'geometric', label: '几何' },
                  { value: 'abstract', label: '抽象' },
                ].map((type) => (
                  <button
                    key={type.value}
                    onClick={() =>
                      updateOptions('extract_pattern', {
                        patternType: type.value as 'floral' | 'geometric' | 'abstract',
                      })
                    }
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition ${
                      options.extract_pattern.patternType === type.value
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    {type.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        );
      case 'watermark_removal':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">水印类型</label>
              <div className="flex space-x-2">
                {[
                  { value: 'auto', label: '自动识别' },
                  { value: 'text', label: '文字水印' },
                  { value: 'logo', label: 'Logo水印' },
                  { value: 'transparent', label: '透明水印' },
                ].map((type) => (
                  <button
                    key={type.value}
                    onClick={() =>
                      updateOptions('watermark_removal', {
                        watermarkType: type.value as 'auto' | 'text' | 'logo' | 'transparent',
                      })
                    }
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition ${
                      options.watermark_removal.watermarkType === type.value
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    {type.label}
                  </button>
                ))}
              </div>
            </div>
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={options.watermark_removal.preserveDetail}
                onChange={(e) =>
                  updateOptions('watermark_removal', {
                    preserveDetail: e.target.checked,
                  })
                }
                className="rounded border-gray-300"
              />
              <span className="text-sm">保留细节</span>
            </label>
          </div>
        );
      case 'noise_removal':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">噪音类型</label>
              <div className="flex space-x-2">
                {[
                  { value: 'fabric', label: '布纹' },
                  { value: 'noise', label: '噪点' },
                  { value: 'blur', label: '模糊' },
                ].map((type) => (
                  <button
                    key={type.value}
                    onClick={() =>
                      updateOptions('noise_removal', {
                        noiseType: type.value as 'fabric' | 'noise' | 'blur',
                      })
                    }
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition ${
                      options.noise_removal.noiseType === type.value
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    {type.label}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">增强模式</label>
              <div className="flex space-x-2">
                <button
                  onClick={() =>
                    updateOptions('noise_removal', { enhanceMode: 'standard' })
                  }
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition ${
                    options.noise_removal.enhanceMode === 'standard'
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  标准模式
                </button>
                <button
                  onClick={() =>
                    updateOptions('noise_removal', { enhanceMode: 'vector_redraw' })
                  }
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition ${
                    options.noise_removal.enhanceMode === 'vector_redraw'
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  矢量重绘
                </button>
              </div>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
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

      <div className="flex">
        <div className="w-80 bg-white border-r border-gray-200 p-6">
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
          <div className="flex flex-col items-center justify-center min-h-[500px] space-y-4">
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
              <div className="text-center">
                <img
                  src={resolveFileUrl(processedImage)}
                  alt="Processed"
                  className="mx-auto max-h-96 rounded-lg border border-gray-200 shadow-lg mb-6"
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

          <div className="mt-8 bg-white rounded-xl border border-gray-200 p-6">
            <h4 className="text-lg font-semibold text-gray-900 mb-4">参数设置</h4>
            {renderOptions()}
          </div>
        </div>

        <div className="w-80 bg-white border-l border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <History className="h-5 w-5 mr-2 text-gray-600" />
            历史记录
          </h3>
          <div className="text-center text-gray-400 py-8">
            <p className="text-sm">暂无历史记录</p>
          </div>
        </div>
      </div>

      <div className="fixed bottom-8 left-1/2 transform -translate-x-1/2">
        <button
          onClick={onProcessImage}
          disabled={!hasUploadedImage || isProcessing}
          className="bg-gradient-to-r from-pink-500 to-pink-600 hover:from-pink-600 hover:to-pink-700 disabled:from-gray-400 disabled:to-gray-500 text-white font-medium py-4 px-12 rounded-full text-lg shadow-2xl transition-all transform hover:scale-105 disabled:hover:scale-100"
        >
          {isProcessing ? (
            <div className="flex items-center space-x-2">
              <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full" />
              <span>处理中...</span>
            </div>
          ) : (
            '一键生成'
          )}
        </button>
      </div>
    </div>
  );
};

export default ProcessingPage;
