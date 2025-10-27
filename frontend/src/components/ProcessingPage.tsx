'use client';

import React, { useEffect, useState } from 'react';
import { History, Eye } from 'lucide-react';
import { ProcessingMethod, getProcessingMethodInfo, canAdjustResolution } from '../lib/processing';
import { resolveFileUrl, HistoryTask, getServiceCost } from '../lib/api';
import HistoryList from './HistoryList';
import ImagePreview from './ImagePreview';
import ProcessedImagePreview from './ProcessedImagePreview';

const SERVICE_PRICE_FALLBACKS: Record<ProcessingMethod, number> = {
  prompt_edit: 0.5,
  style: 2.5,
  embroidery: 0.7,
  extract_pattern: 1.5,
  watermark_removal: 0.9,
  noise_removal: 0.5,
  upscale: 0.9,
};

const formatCredits = (value: number) => {
  if (Number.isInteger(value)) {
    return value.toString();
  }

  const formatted = value.toFixed(2).replace(/\.00$/, '');
  return formatted.replace(/(\.\d*[1-9])0$/, '$1');
};

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
  patternType?: string;
  onPatternTypeChange?: (value: string) => void;
  upscaleEngine?: 'meitu_v2';
  onUpscaleEngineChange?: (value: 'meitu_v2') => void;
  aspectRatio?: string;
  onAspectRatioChange?: (value: string) => void;
  historyRefreshToken?: number;
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
  patternType,
  onPatternTypeChange,
  upscaleEngine,
  onUpscaleEngineChange,
  aspectRatio,
  onAspectRatioChange,
  historyRefreshToken = 0,
}) => {
  const info = getProcessingMethodInfo(method);
  const [selectedTask, setSelectedTask] = useState<HistoryTask | null>(null);
  const [showImagePreview, setShowImagePreview] = useState(false);
  const [processedImagePreview, setProcessedImagePreview] = useState<{url: string, filename: string} | null>(null);
  const isPromptReady = method !== 'prompt_edit' || Boolean(promptInstruction?.trim());
  const isActionDisabled = !hasUploadedImage || isProcessing || !isPromptReady;
  const fallbackCredits = SERVICE_PRICE_FALLBACKS[method];
  const [serviceCredits, setServiceCredits] = useState<number | null>(fallbackCredits ?? null);
  const [isLoadingServiceCost, setIsLoadingServiceCost] = useState(false);
  const upscaleOptions: { value: 'meitu_v2'; label: string; description: string }[] = [
    {
      value: 'meitu_v2',
      label: '通用',
      description: '超清V2模式，追求稳定还原与高保真，适合对原图还原度要求高的场景。',
    },
  ];

  useEffect(() => {
    let isMounted = true;
    setServiceCredits(fallbackCredits ?? null);

    if (!accessToken) {
      setIsLoadingServiceCost(false);
      return () => {
        isMounted = false;
      };
    }

    setIsLoadingServiceCost(true);
    getServiceCost(method, accessToken)
      .then((response) => {
        if (!isMounted) return;
        const resolved = response.unit_cost ?? response.total_cost ?? fallbackCredits ?? null;
        setServiceCredits(resolved);
      })
      .catch((error) => {
        if (!isMounted) return;
        console.warn(`获取服务价格失败: ${method}`, error);
        setServiceCredits((prev) => prev ?? fallbackCredits ?? null);
      })
      .finally(() => {
        if (isMounted) {
          setIsLoadingServiceCost(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [method, accessToken, fallbackCredits]);

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

  const handleProcessedImagePreview = (url: string, index?: number) => {
    const filename = index !== undefined ? `result_${index + 1}.png` : 'result.png';
    setProcessedImagePreview({ url, filename });
  };

  const handleCloseProcessedImagePreview = () => {
    setProcessedImagePreview(null);
  };

  return (
    <div className="h-screen bg-gray-50 flex flex-col">
      <header className="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
        <div className="flex items-center justify-between px-4 md:px-6 py-3 md:py-4">
          <div className="flex items-center space-x-2 md:space-x-4">
            <button
              onClick={onBack}
              className="flex items-center space-x-1 md:space-x-2 text-gray-600 hover:text-gray-900 transition"
            >
              <span>←</span>
              <span className="hidden sm:inline">返回</span>
            </button>
            <div className="flex items-center space-x-2 md:space-x-3">
              <div className="flex h-6 w-6 md:h-8 md:w-8 items-center justify-center rounded-lg bg-white shadow-md overflow-hidden">
                <img
                  src={info.icon}
                  alt={info.title}
                  className="h-4 w-4 md:h-6 md:w-6 object-contain"
                />
              </div>
              <h1 className="text-base md:text-xl font-bold text-gray-900">{info.title}</h1>
            </div>
          </div>

          <div className="flex items-center space-x-2 md:space-x-4">
            {accessToken && (
              <button
                onClick={onOpenPricingModal}
                className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white px-3 py-1.5 md:px-4 md:py-2 rounded-lg text-xs md:text-sm font-medium transition-all shadow-sm"
              >
                套餐充值
              </button>
            )}
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden flex-col md:flex-row">
        <div className="w-full md:w-80 bg-white border-r border-gray-200 p-4 md:p-6 overflow-y-auto order-2 md:order-1">
          <div className="mb-4 md:mb-6">
            <h3 className="text-base md:text-lg font-semibold text-gray-900 mb-3 md:mb-4">上传图片</h3>
            <div
              className="border-2 border-dashed border-gray-300 rounded-lg md:rounded-xl p-4 md:p-8 text-center hover:border-blue-400 transition cursor-pointer min-h-[150px] md:min-h-[200px] flex items-center justify-center"
              onDragOver={onDragOver}
              onDrop={onDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              {imagePreview ? (
                <div className="space-y-2 md:space-y-4">
                  <img
                    src={resolveFileUrl(imagePreview)}
                    alt="Preview"
                    className="mx-auto max-h-24 md:max-h-32 rounded-lg border border-gray-200"
                  />
                  <p className="text-xs md:text-sm text-gray-500">拖拽图片或点击上传</p>
                </div>
              ) : (
                <div className="space-y-2 md:space-y-4">
                  <div className="mx-auto flex h-10 w-10 md:h-12 md:w-12 items-center justify-center rounded-lg md:rounded-xl bg-gray-100 text-gray-400">
                    ⬆
                  </div>
                  <div>
                    <p className="text-sm md:text-base font-medium text-gray-700">拖拽图片或点击上传</p>
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

          <div className="mb-4 md:mb-6">
            <div className="mb-3">
              <div className="w-full rounded-lg md:rounded-xl border border-blue-100 bg-blue-50 px-3 py-2 text-center text-xs md:text-sm text-blue-700">
                {isLoadingServiceCost
                  ? '价格加载中…'
                  : serviceCredits !== null
                    ? `${formatCredits(serviceCredits)} 积分/次（失败不扣积分）`
                    : '价格暂不可用，请稍后重试'}
              </div>
            </div>
            <button
              onClick={onProcessImage}
              disabled={isActionDisabled}
              className="w-full bg-gradient-to-r from-pink-500 to-pink-600 hover:from-pink-600 hover:to-pink-700 disabled:from-gray-400 disabled:to-gray-500 text-white font-medium py-3 px-4 md:py-4 md:px-6 rounded-lg md:rounded-xl text-base md:text-lg shadow-lg transition-all transform hover:scale-105 disabled:hover:scale-100"
            >
              {isProcessing ? (
                <div className="flex items-center justify-center space-x-2">
                  <div className="animate-spin h-4 w-4 md:h-5 md:w-5 border-2 border-white border-t-transparent rounded-full" />
                  <span>处理中...</span>
                </div>
              ) : (
                '一键生成'
              )}
            </button>
          </div>

          {method === 'extract_pattern' && (
            <div className="mb-4 md:mb-6">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm md:text-base font-semibold text-gray-900">花型类型</h4>
              </div>
              <select
                value={patternType || 'general'}
                onChange={(event) => onPatternTypeChange?.(event.target.value)}
                className="w-full rounded-lg md:rounded-xl border border-gray-200 px-3 py-2 md:px-4 md:py-3 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-400"
              >
                <option value="general">通用</option>
                <option value="positioning">定位花</option>
                <option value="fine">精细效果</option>
              </select>
              <p className="text-xs text-gray-500 mt-2">选择不同的花型类型，AI会使用相应的处理方式。</p>
            </div>
          )}

          {method === 'upscale' && (
            <div className="mb-4 md:mb-6">
              <h4 className="text-sm md:text-base font-semibold text-gray-900 mb-2">高清算法</h4>
              <div className="space-y-2">
                {upscaleOptions.map((option) => {
                  const isActive = (upscaleEngine || 'meitu_v2') === option.value;
                  return (
                    <button
                      type="button"
                      key={option.value}
                      onClick={() => onUpscaleEngineChange?.(option.value)}
                      className={`w-full text-left border rounded-lg md:rounded-xl px-3 py-2 md:px-4 md:py-3 transition-all ${
                        isActive
                          ? 'border-blue-500 bg-blue-50 shadow-sm'
                          : 'border-gray-200 hover:border-blue-300 hover:bg-blue-50/60'
                      }`}
                    >
                      <p className={`text-sm md:text-base font-semibold ${isActive ? 'text-blue-600' : 'text-gray-800'}`}>
                        {option.label}
                      </p>
                      <p className="text-xs md:text-sm text-gray-500 mt-1 leading-snug">
                        {option.description}
                      </p>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* 分辨率选择 - 仅在允许自定义分辨率的方法中显示 */}
          {canAdjustResolution(method) && (
            <div className="mb-4 md:mb-6">
              <h4 className="text-sm md:text-base font-semibold text-gray-900 mb-2">分辨率设置</h4>

              {/* 预设比例选择 */}
              <div>
                <label className="text-xs text-gray-600 mb-1 block">选择比例</label>
                <select
                  value={aspectRatio || ''}
                  onChange={(event) => onAspectRatioChange?.(event.target.value)}
                  className="w-full rounded-lg md:rounded-xl border border-gray-200 px-3 py-2 md:px-4 md:py-3 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-400"
                >
                  <option value="">自动（保持原图比例）</option>
                  <option value="21:9">21:9 超宽屏</option>
                  <option value="16:9">16:9 宽屏</option>
                  <option value="4:3">4:3 标准</option>
                  <option value="3:2">3:2 经典</option>
                  <option value="1:1">1:1 正方形</option>
                  <option value="9:16">9:16 竖屏</option>
                  <option value="3:4">3:4 竖屏</option>
                  <option value="2:3">2:3 竖屏</option>
                  <option value="5:4">5:4 特殊</option>
                  <option value="4:5">4:5 特殊</option>
                </select>
                <p className="text-xs text-gray-500 mt-2">选择预设比例，AI将按选定比例生成图片</p>
              </div>
            </div>
          )}

          {method === 'prompt_edit' && (
            <div className="mb-4 md:mb-6 space-y-3 md:space-y-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm md:text-base font-semibold text-gray-900">输入指令</h4>
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
                  className="w-full min-h-[90px] md:min-h-[110px] rounded-lg md:rounded-xl border border-gray-200 px-3 py-2 md:px-4 md:py-3 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-400 resize-none"
                />
                <p className="text-xs text-gray-500 mt-2">一句话描述想要修改的细节，AI会自动处理。</p>
              </div>
            </div>
          )}

          <div className="mb-4 md:mb-6">
            <h4 className="text-sm md:text-base font-semibold text-gray-900 mb-2 md:mb-3">使用提示</h4>
            <p className="text-xs md:text-sm text-gray-600 mb-3 md:mb-4">{info.description}</p>
          </div>

          <div>
            <h4 className="text-sm md:text-base font-semibold text-gray-900 mb-2 md:mb-3">操作要求示例</h4>
            <div className="space-y-1 md:space-y-2">
              {info.examples.map((example, index) => (
                <div key={index} className="text-xs md:text-sm text-gray-600">
                  <span className="text-red-400">{index + 1}.</span> {example}
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="flex-1 p-4 md:p-8 order-1 md:order-2">
          <div className="flex flex-col items-center justify-center h-full space-y-3 md:space-y-4">
            {errorMessage && (
              <div className="w-full max-w-md md:max-w-lg rounded-lg md:rounded-xl border border-red-200 bg-red-50 px-4 py-3 md:px-6 md:py-4 text-xs md:text-sm text-red-600">
                {errorMessage}
              </div>
            )}
            {successMessage && !errorMessage && (
              <div className="w-full max-w-md md:max-w-lg rounded-lg md:rounded-xl border border-green-200 bg-green-50 px-4 py-3 md:px-6 md:py-4 text-xs md:text-sm text-green-600">
                {successMessage}
              </div>
            )}
            {processedImage ? (
              <div className="text-center w-full h-full flex flex-col items-center justify-center">
                {(() => {
                  const imageUrls = processedImage.split(',');
                  if (imageUrls.length > 1) {
                    // 多张图片，使用网格布局
                    return (
                      <>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4 md:mb-6 w-full max-w-4xl">
                          {imageUrls.map((url, index) => (
                            <div key={index} className="flex flex-col items-center">
                              <div className="relative group">
                                <img
                                  src={resolveFileUrl(url.trim())}
                                  alt={`Processed ${index + 1}`}
                                  className="max-w-full max-h-[40vh] w-auto h-auto object-contain rounded-lg border border-gray-200 shadow-lg mb-2 cursor-pointer hover:shadow-xl transition-shadow"
                                  onClick={() => handleProcessedImagePreview(url.trim(), index)}
                                />
                                <button
                                  onClick={() => handleProcessedImagePreview(url.trim(), index)}
                                  className="absolute top-2 right-2 p-2 bg-black bg-opacity-50 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity hover:bg-opacity-70"
                                  title="放大查看"
                                >
                                  <Eye className="h-4 w-4" />
                                </button>
                              </div>
                              <a
                                className="inline-flex items-center justify-center bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition shadow-lg"
                                href={resolveFileUrl(url.trim())}
                                download
                                target="_blank"
                                rel="noopener noreferrer"
                              >
                                下载图片 {index + 1}
                              </a>
                            </div>
                          ))}
                        </div>
                        <button
                          onClick={() => {
                            imageUrls.forEach((url, index) => {
                              const link = document.createElement('a');
                              link.href = resolveFileUrl(url.trim());
                              link.download = `result_${index + 1}.png`;
                              document.body.appendChild(link);
                              link.click();
                              document.body.removeChild(link);
                            });
                          }}
                          className="inline-flex items-center justify-center bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 md:px-8 md:py-3 rounded-lg md:rounded-xl font-medium transition shadow-lg"
                        >
                          批量下载全部
                        </button>
                      </>
                    );
                  } else {
                    // 单张图片
                    return (
                      <>
                        <div className="relative group mb-4 md:mb-6">
                          {(() => {
                            const resolvedUrl = resolveFileUrl(processedImage);
                            console.log('ProcessingPage: Displaying processed image', {
                              originalUrl: processedImage,
                              resolvedUrl,
                              isSvg: processedImage.toLowerCase().includes('.svg')
                            });
                            
                            // 检查是否是SVG文件
                            if (processedImage.toLowerCase().includes('.svg')) {
                              console.log('ProcessingPage: Detected SVG file, using special handling');
                              return (
                                <div
                                  className="max-w-full max-h-[60vh] md:max-h-[80vh] w-auto h-auto object-contain rounded-lg border border-gray-200 shadow-lg cursor-pointer hover:shadow-xl transition-shadow overflow-hidden"
                                  onClick={() => handleProcessedImagePreview(processedImage)}
                                >
                                  <object
                                    data={resolvedUrl}
                                    type="image/svg+xml"
                                    className="w-full h-full"
                                    style={{ maxHeight: '60vh', maxWidth: '100%' }}
                                    onLoad={() => console.log('ProcessingPage: SVG loaded successfully')}
                                    onError={(e) => console.error('ProcessingPage: SVG failed to load', e)}
                                  >
                                    <img
                                      src={resolvedUrl}
                                      alt="Processed"
                                      className="w-full h-full object-contain"
                                      onError={(e) => console.error('ProcessingPage: Fallback img also failed', e)}
                                    />
                                  </object>
                                </div>
                              );
                            }
                            
                            return (
                              <img
                                src={resolvedUrl}
                                alt="Processed"
                                className="max-w-full max-h-[60vh] md:max-h-[80vh] w-auto h-auto object-contain rounded-lg border border-gray-200 shadow-lg cursor-pointer hover:shadow-xl transition-shadow"
                                onClick={() => handleProcessedImagePreview(processedImage)}
                                onLoad={() => console.log('ProcessingPage: Image loaded successfully')}
                                onError={(e) => console.error('ProcessingPage: Image failed to load', e)}
                              />
                            );
                          })()}
                          <button
                            onClick={() => handleProcessedImagePreview(processedImage)}
                            className="absolute top-2 right-2 p-2 bg-black bg-opacity-50 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity hover:bg-opacity-70"
                            title="放大查看"
                          >
                            <Eye className="h-4 w-4" />
                          </button>
                        </div>
                        <a
                          className="inline-flex items-center justify-center bg-green-500 hover:bg-green-600 text-white px-6 py-2 md:px-8 md:py-3 rounded-lg md:rounded-xl font-medium transition shadow-lg"
                          href={resolveFileUrl(processedImage)}
                          download
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          下载结果
                        </a>
                      </>
                    );
                  }
                })()}
              </div>
            ) : (
              <div className="text-center">
                <div className="w-24 h-24 md:w-32 md:h-32 mx-auto mb-4 md:mb-6 rounded-full bg-gradient-to-br from-blue-400 via-blue-500 to-blue-600 flex items-center justify-center relative overflow-hidden">
                  <div className="relative w-20 h-20 md:w-24 md:h-24">
                    <div className="absolute inset-0 bg-blue-500 rounded-full"></div>
                    <div className="absolute top-2 left-3 w-3 h-2 md:w-4 md:h-3 bg-green-400 rounded-full"></div>
                    <div className="absolute top-4 right-2 w-2 h-1 md:w-3 md:h-2 bg-green-400 rounded-full"></div>
                    <div className="absolute bottom-3 left-2 w-4 h-3 md:w-5 md:h-4 bg-green-400 rounded-full"></div>
                    <div className="absolute top-1 left-8 w-6 h-1 md:w-8 md:h-2 bg-white rounded-full opacity-70"></div>
                    <div className="absolute bottom-6 right-1 w-4 h-1 md:w-6 md:h-2 bg-white rounded-full opacity-50"></div>
                    <div className="absolute -top-4 left-4 w-2 h-3 md:w-2 md:h-4 bg-red-400 transform rotate-12"></div>
                    <div className="absolute -top-2 right-3 w-2 h-4 md:w-3 md:h-6 bg-yellow-400 transform -rotate-12"></div>
                    <div className="absolute -bottom-2 left-6 w-2 h-3 md:w-2 md:h-4 bg-purple-400 transform rotate-45"></div>
                  </div>
                </div>
                <p className="text-gray-400 text-sm md:text-lg">什么都没有呢，赶快开始吧吧</p>
              </div>
            )}
          </div>
        </div>

        <div className="w-full md:w-80 bg-white border-l border-gray-200 p-4 md:p-6 overflow-y-auto order-3">
          <h3 className="text-base md:text-lg font-semibold text-gray-900 mb-3 md:mb-4 flex items-center">
            <History className="h-4 w-4 md:h-5 md:w-5 mr-2 text-gray-600" />
            历史记录
          </h3>
          {accessToken ? (
            <HistoryList
              accessToken={accessToken}
              onTaskSelect={handleTaskSelect}
              refreshToken={historyRefreshToken}
            />
          ) : (
            <div className="text-center text-gray-400 py-6 md:py-8">
              <p className="text-xs md:text-sm">请登录后查看历史记录</p>
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

      {/* 处理结果图片预览弹窗 */}
      {processedImagePreview && (
        <ProcessedImagePreview
          image={processedImagePreview}
          onClose={handleCloseProcessedImagePreview}
        />
      )}
    </div>
  );
};

export default ProcessingPage;
