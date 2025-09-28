'use client';

import React, { useState, useRef } from 'react';
import { Upload, Image as ImageIcon, Settings, Download, History, Star, Grid, Zap, Crown, Search, User, Bell } from 'lucide-react';

type ProcessingMethod = 'seamless' | 'style' | 'embroidery' | 'extract_edit' | 'extract_pattern' | 'watermark_removal' | 'noise_removal';

interface ProcessingOptions {
  seamless: {
    removeBackground: boolean;
    seamlessLoop: boolean;
  };
  style: {
    outputStyle: 'vector' | 'seamless';
    outputRatio: '1:1' | '2:3' | '3:2';
  };
  embroidery: {
    needleType: 'fine' | 'medium' | 'thick';
    stitchDensity: 'low' | 'medium' | 'high';
    enhanceDetails: boolean;
  };
  extract_edit: {
    voiceControl: boolean;
    editMode: 'smart' | 'manual';
  };
  extract_pattern: {
    preprocessing: boolean;
    voiceControl: boolean;
    patternType: 'floral' | 'geometric' | 'abstract';
  };
  watermark_removal: {
    watermarkType: 'text' | 'logo' | 'transparent' | 'auto';
    preserveDetail: boolean;
  };
  noise_removal: {
    noiseType: 'fabric' | 'noise' | 'blur';
    enhanceMode: 'standard' | 'vector_redraw';
  };
}

export default function Home() {
  const [uploadedImage, setUploadedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [selectedMethod, setSelectedMethod] = useState<ProcessingMethod | null>(null);
  const [processedImage, setProcessedImage] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showPricingModal, setShowPricingModal] = useState(false);
  const [activeTab, setActiveTab] = useState<'优惠套餐' | '包月会员' | '季度会员' | '包年会员' | '算力充值'>('包月会员');
  const [currentPage, setCurrentPage] = useState<'home' | ProcessingMethod>('home');
  const [options, setOptions] = useState<ProcessingOptions>({
    seamless: {
      removeBackground: true,
      seamlessLoop: true,
    },
    style: {
      outputStyle: 'vector',
      outputRatio: '1:1',
    },
    embroidery: {
      needleType: 'medium',
      stitchDensity: 'medium',
      enhanceDetails: true,
    },
    extract_edit: {
      voiceControl: true,
      editMode: 'smart',
    },
    extract_pattern: {
      preprocessing: true,
      voiceControl: true,
      patternType: 'floral',
    },
    watermark_removal: {
      watermarkType: 'auto',
      preserveDetail: true,
    },
    noise_removal: {
      noiseType: 'fabric',
      enhanceMode: 'standard',
    },
  });

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setUploadedImage(file);
      const reader = new FileReader();
      reader.onload = (e) => {
        setImagePreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      setUploadedImage(file);
      const reader = new FileReader();
      reader.onload = (e) => {
        setImagePreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleProcessImage = () => {
    if (!uploadedImage || !selectedMethod) return;
    
    setIsProcessing(true);
    // 模拟处理过程
    setTimeout(() => {
      setProcessedImage(imagePreview); // 暂时使用原图作为处理结果
      setIsProcessing(false);
    }, 2000);
  };

  const updateOptions = <T extends ProcessingMethod>(
    method: T,
    updates: Partial<ProcessingOptions[T]>
  ) => {
    setOptions(prev => ({
      ...prev,
      [method]: { ...prev[method], ...updates }
    }));
  };

  const getMethodInfo = (method: ProcessingMethod) => {
    const methodInfo = {
      seamless: {
        title: 'AI四方连续转换',
        description: '对独幅矩形图转换成可四方连续的打印图，如需对结果放大请用AI无缝图放大功能。',
        icon: '/AI四方连续转换.png',
        examples: [
          '上传矩形图片',
          '选择去重叠区选项，避免边界重叠',
          '启用无缝循环功能，确保完美拼接',
          '调整图案大小和位置',
          '生成可四方连续的打印图案'
        ]
      },
      style: {
        title: 'AI矢量化(转SVG)',
        description: '使用AI一键将图片变成矢量图，线条清晰，图片还原。助力您的产品设计。（100算力）',
        icon: '/AI矢量化转SVG.png',
        examples: [
          '上传需要矢量化的图片',
          '选择输出风格（矢量/无缝循环）',
          '设置输出比例（1:1, 2:3, 3:2）',
          'AI自动矢量化处理',
          '生成高质量SVG矢量图'
        ]
      },
      embroidery: {
        title: 'AI毛线刺绣增强',
        description: '针对毛线刺绣转换的针对处理，转换出的刺绣对原图主体形状保持度高，毛线感的针法。',
        icon: '/AI毛线刺绣增强.png',
        examples: [
          '上传刺绣类图片',
          '选择针线类型（细针/中等/粗针）',
          '设置针脚密度（稀疏/中等/密集）',
          '启用增强细节纹理',
          '生成逼真的毛线刺绣效果'
        ]
      },
      extract_edit: {
        title: 'AI提取编辑',
        description: '使用AI提取和编辑图片内容，支持语音控制进行智能编辑。',
        icon: '/AI提取编辑.png',
        examples: [
          '上传需要编辑的图片',
          '启用语音控制功能',
          '选择智能编辑模式',
          '通过语音描述编辑需求',
          'AI智能完成图片编辑'
        ]
      },
      extract_pattern: {
        title: 'AI提取花型',
        description: '需预处理图片，支持用嘴改图。提取图案中的花型元素，适合设计应用。（100算力）',
        icon: '/AI提取花型.png',
        examples: [
          '上传包含花型的图片',
          '启用预处理功能',
          '选择花型类型（花卉/几何/抽象）',
          '通过语音控制调整提取',
          'AI智能提取花型元素'
        ]
      },
      watermark_removal: {
        title: 'AI智能去水印',
        description: '一键去水印。不管是顽固的文字水印、半透明logo水印，都能快捷去除。',
        icon: '/AI智能去水印.png',
        examples: [
          '上传带有水印的图片',
          '选择水印类型（文字/Logo/透明/自动）',
          '启用保留细节功能',
          'AI自动识别和去除水印',
          '生成无水印的清洁图片'
        ]
      },
      noise_removal: {
        title: 'AI布纹去噪去',
        description: '使用AI快速的去除图片中的噪点、布纹。还可用于对模糊矢量花的高清重绘。（80算力）',
        icon: '/AI布纹去噪.png',
        examples: [
          '上传有噪点或布纹的图片',
          '选择噪音类型（布纹/噪点/模糊）',
          '选择增强模式（标准/矢量重绘）',
          'AI智能去除噪点和布纹',
          '生成清晰的高质量图片'
        ]
      }
    };
    return methodInfo[method];
  };

  const renderFunctionPage = (method: ProcessingMethod) => {
    const info = getMethodInfo(method);

  return (
      <div className="min-h-screen bg-gray-50">
      {/* Header */}
        <header className="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
          <div className="flex items-center justify-between px-6 py-4">
            <div className="flex items-center space-x-4">
              <button 
                onClick={() => setCurrentPage('home')}
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
                onClick={() => setShowPricingModal(true)}
                className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all shadow-sm"
              >
                套餐充值
          </button>
            </div>
        </div>
      </header>

        <div className="flex">
          {/* Left Sidebar */}
          <div className="w-80 bg-white border-r border-gray-200 p-6">
            {/* Upload Area */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">上传图片</h3>
              <div
                className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-blue-400 transition cursor-pointer min-h-[200px] flex items-center justify-center"
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                {imagePreview ? (
                  <div className="space-y-4">
                    <img
                      src={imagePreview}
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
                onChange={handleImageUpload}
                className="hidden"
              />
            </div>

            {/* Usage Tips */}
            <div className="mb-6">
              <h4 className="text-base font-semibold text-gray-900 mb-3">使用提示</h4>
              <p className="text-sm text-gray-600 mb-4">{info.description}</p>
          </div>

            {/* Examples */}
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

          {/* Main Content Area */}
          <div className="flex-1 p-8">
            <div className="flex flex-col items-center justify-center min-h-[500px]">
              {processedImage ? (
                <div className="text-center">
                  <img
                    src={processedImage}
                    alt="Processed"
                    className="mx-auto max-h-96 rounded-lg border border-gray-200 shadow-lg mb-6"
                  />
                  <button className="bg-green-500 hover:bg-green-600 text-white px-8 py-3 rounded-xl font-medium transition shadow-lg">
                    下载结果
                  </button>
                    </div>
              ) : (
                <div className="text-center">
                  <div className="w-32 h-32 mx-auto mb-6 rounded-full bg-gradient-to-br from-blue-400 via-blue-500 to-blue-600 flex items-center justify-center relative overflow-hidden">
                    {/* Earth-like illustration */}
                    <div className="relative w-24 h-24">
                      <div className="absolute inset-0 bg-blue-500 rounded-full"></div>
                      <div className="absolute top-2 left-3 w-4 h-3 bg-green-400 rounded-full"></div>
                      <div className="absolute top-4 right-2 w-3 h-2 bg-green-400 rounded-full"></div>
                      <div className="absolute bottom-3 left-2 w-5 h-4 bg-green-400 rounded-full"></div>
                      <div className="absolute top-1 left-8 w-8 h-2 bg-white rounded-full opacity-70"></div>
                      <div className="absolute bottom-6 right-1 w-6 h-2 bg-white rounded-full opacity-50"></div>
                      {/* Small decorative elements */}
                      <div className="absolute -top-4 left-4 w-2 h-4 bg-red-400 transform rotate-12"></div>
                      <div className="absolute -top-2 right-3 w-3 h-6 bg-yellow-400 transform -rotate-12"></div>
                      <div className="absolute -bottom-2 left-6 w-2 h-4 bg-purple-400 transform rotate-45"></div>
                    </div>
                  </div>
                  <p className="text-gray-400 text-lg">什么都没有呢，赶快开始吧吧</p>
                </div>
              )}
            </div>

            {/* Tool Options */}
            {method && (
              <div className="mt-8 bg-white rounded-xl border border-gray-200 p-6">
                <h4 className="text-lg font-semibold text-gray-900 mb-4">参数设置</h4>
                {method === 'seamless' && (
                  <div className="grid grid-cols-2 gap-4">
                    <label className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={options.seamless.removeBackground}
                          onChange={(e) => updateOptions('seamless', { removeBackground: e.target.checked })}
                        className="rounded border-gray-300"
                        />
                      <span className="text-sm">去重叠区</span>
                      </label>
                    <label className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                        checked={options.seamless.seamlessLoop}
                        onChange={(e) => updateOptions('seamless', { seamlessLoop: e.target.checked })}
                        className="rounded border-gray-300"
                      />
                      <span className="text-sm">无缝循环</span>
                      </label>
                    </div>
                  )}
                {method === 'style' && (
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
                          onClick={() => updateOptions('style', { outputStyle: 'seamless' })}
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
                            onClick={() => updateOptions('style', { outputRatio: ratio as any })}
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
                  )}
                {method === 'embroidery' && (
                  <div className="grid grid-cols-2 gap-4">
                      <div>
                      <label className="block text-sm font-medium mb-2">针线类型</label>
                      <select
                        value={options.embroidery.needleType}
                        onChange={(e) => updateOptions('embroidery', { needleType: e.target.value as any })}
                        className="w-full rounded border-gray-300"
                      >
                        <option value="fine">细针</option>
                        <option value="medium">中等</option>
                        <option value="thick">粗针</option>
                      </select>
                  </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">针脚密度</label>
                      <select
                        value={options.embroidery.stitchDensity}
                        onChange={(e) => updateOptions('embroidery', { stitchDensity: e.target.value as any })}
                        className="w-full rounded border-gray-300"
                      >
                        <option value="low">稀疏</option>
                        <option value="medium">中等</option>
                        <option value="high">密集</option>
                      </select>
                    </div>
                    <label className="flex items-center space-x-2 col-span-2">
                        <input
                          type="checkbox"
                        checked={options.embroidery.enhanceDetails}
                        onChange={(e) => updateOptions('embroidery', { enhanceDetails: e.target.checked })}
                        className="rounded border-gray-300"
                      />
                      <span className="text-sm">增强细节纹理</span>
                      </label>
                      </div>
                )}
                {method === 'extract_edit' && (
                  <div className="grid grid-cols-2 gap-4">
                    <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={options.extract_edit.voiceControl}
                        onChange={(e) => updateOptions('extract_edit', { voiceControl: e.target.checked })}
                        className="rounded border-gray-300"
                      />
                      <span className="text-sm">启用语音控制</span>
                    </label>
                    <div>
                      <label className="block text-sm font-medium mb-2">编辑模式</label>
                      <select
                        value={options.extract_edit.editMode}
                        onChange={(e) => updateOptions('extract_edit', { editMode: e.target.value as any })}
                        className="w-full rounded border-gray-300"
                      >
                        <option value="smart">智能模式</option>
                        <option value="manual">手动模式</option>
                      </select>
                    </div>
                  </div>
                )}
                {method === 'extract_pattern' && (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <label className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={options.extract_pattern.preprocessing}
                          onChange={(e) => updateOptions('extract_pattern', { preprocessing: e.target.checked })}
                          className="rounded border-gray-300"
                        />
                        <span className="text-sm">预处理图片</span>
                      </label>
                      <label className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={options.extract_pattern.voiceControl}
                          onChange={(e) => updateOptions('extract_pattern', { voiceControl: e.target.checked })}
                          className="rounded border-gray-300"
                        />
                        <span className="text-sm">语音控制</span>
                      </label>
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">花型类型</label>
                      <div className="flex space-x-2">
                        {['floral', 'geometric', 'abstract'].map((type) => (
                          <button
                            key={type}
                            onClick={() => updateOptions('extract_pattern', { patternType: type as any })}
                            className={`px-3 py-2 rounded-lg text-sm font-medium transition ${
                              options.extract_pattern.patternType === type
                                ? 'bg-blue-500 text-white'
                                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                            }`}
                          >
                            {type === 'floral' ? '花卉' : type === 'geometric' ? '几何' : '抽象'}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
                {method === 'watermark_removal' && (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">水印类型</label>
                      <div className="flex space-x-2">
                        {[
                          { value: 'auto', label: '自动识别' },
                          { value: 'text', label: '文字水印' },
                          { value: 'logo', label: 'Logo水印' },
                          { value: 'transparent', label: '透明水印' }
                        ].map((type) => (
                          <button
                            key={type.value}
                            onClick={() => updateOptions('watermark_removal', { watermarkType: type.value as any })}
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
                        onChange={(e) => updateOptions('watermark_removal', { preserveDetail: e.target.checked })}
                        className="rounded border-gray-300"
                      />
                      <span className="text-sm">保留细节</span>
                    </label>
                  </div>
                )}
                {method === 'noise_removal' && (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">噪音类型</label>
                      <div className="flex space-x-2">
                        {[
                          { value: 'fabric', label: '布纹' },
                          { value: 'noise', label: '噪点' },
                          { value: 'blur', label: '模糊' }
                        ].map((type) => (
                          <button
                            key={type.value}
                            onClick={() => updateOptions('noise_removal', { noiseType: type.value as any })}
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
                          onClick={() => updateOptions('noise_removal', { enhanceMode: 'standard' })}
                          className={`px-3 py-2 rounded-lg text-sm font-medium transition ${
                            options.noise_removal.enhanceMode === 'standard'
                              ? 'bg-blue-500 text-white'
                              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                          }`}
                        >
                          标准模式
                        </button>
                        <button
                          onClick={() => updateOptions('noise_removal', { enhanceMode: 'vector_redraw' })}
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
                )}
                    </div>
                  )}
              </div>

          {/* Right Sidebar - History */}
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

        {/* Bottom Generate Button */}
        <div className="fixed bottom-8 left-1/2 transform -translate-x-1/2">
          {uploadedImage && (
            <button
              onClick={handleProcessImage}
              disabled={isProcessing}
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
          )}
        </div>
      </div>
    );
  };

  // Check if we should render a function page
  if (currentPage !== 'home') {
    return renderFunctionPage(currentPage);
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
        <div className="flex items-center justify-between px-6 py-4">
          {/* Logo and Brand */}
          <div className="flex items-center space-x-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl overflow-hidden">
              <img 
                src="/logo.png" 
                alt="Logo" 
                className="h-full w-full object-cover"
              />
            </div>
            <span className="text-xl font-bold text-gray-900">应用中心</span>
            </div>
          
          {/* Right Navigation */}
          <div className="flex items-center space-x-4">
            <button 
              onClick={() => setShowPricingModal(true)}
              className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all shadow-sm"
            >
              套餐充值
            </button>
            <div className="flex items-center space-x-2">
              <Bell className="h-5 w-5 text-gray-600" />
              <User className="h-5 w-5 text-gray-600" />
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Left Sidebar */}
        <aside className="w-64 bg-white border-r border-gray-200 p-6 space-y-8">
          {/* User Stats */}
          <section>
            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
              <User className="h-5 w-5 text-blue-500 mr-2" />
              我的账户
            </h3>
            <div className="space-y-3">
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-600">剩余算力</span>
                  <span className="text-lg font-bold text-blue-600">2,580</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-gradient-to-r from-blue-500 to-indigo-500 h-2 rounded-full" style={{width: '65%'}}></div>
                </div>
                <div className="text-xs text-gray-500 mt-1">本月已使用 35%</div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <div className="text-lg font-bold text-gray-900">156</div>
                  <div className="text-xs text-gray-500">本月处理</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <div className="text-lg font-bold text-gray-900">1,247</div>
                  <div className="text-xs text-gray-500">总计处理</div>
                </div>
              </div>
            </div>
          </section>

          {/* Quick Actions */}
          <section>
            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
              <Zap className="h-5 w-5 text-yellow-500 mr-2" />
              快捷操作
            </h3>
            <div className="space-y-2">
              <button 
                onClick={() => setShowPricingModal(true)}
                className="w-full bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white p-3 rounded-lg text-sm font-medium transition-all flex items-center justify-center space-x-2"
              >
                <Crown className="h-4 w-4" />
                <span>充值算力</span>
              </button>
              <button className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 p-3 rounded-lg text-sm font-medium transition-all flex items-center justify-center space-x-2">
                <History className="h-4 w-4" />
                <span>查看历史</span>
              </button>
              <button className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 p-3 rounded-lg text-sm font-medium transition-all flex items-center justify-center space-x-2">
                <Download className="h-4 w-4" />
                <span>批量下载</span>
              </button>
            </div>
          </section>

          {/* Usage Tips */}
          <section>
            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
              <span className="h-5 w-5 mr-2">💡</span>
              使用技巧
            </h3>
            <div className="space-y-3">
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                <div className="text-sm font-medium text-yellow-800 mb-1">💰 节省算力</div>
                <div className="text-xs text-yellow-700">上传前先裁剪图片，可节省20%算力消耗</div>
              </div>
              <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                <div className="text-sm font-medium text-green-800 mb-1">🎯 最佳效果</div>
                <div className="text-xs text-green-700">图片分辨率建议在1024-2048px之间</div>
              </div>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <div className="text-sm font-medium text-blue-800 mb-1">⚡ 处理速度</div>
                <div className="text-xs text-blue-700">会员用户享受优先处理队列</div>
              </div>
            </div>
          </section>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 p-8">
          {/* Tool Cards Grid - Full Width */}
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8">
                {/* AI四方连续转换 */}
                <div className="bg-white rounded-2xl border border-gray-200 p-8 hover:shadow-xl transition-all hover:scale-105 cursor-pointer group"
                     onClick={() => setCurrentPage('seamless')}>
                  <div className="text-center mb-6">
                    <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-50 to-indigo-50 shadow-lg mx-auto mb-4 group-hover:shadow-xl transition-all">
                      <img
                        src="/AI四方连续转换.png"
                        alt="四方连续转换"
                        className="h-12 w-12 object-contain"
                      />
                    </div>
                    <h4 className="text-xl font-bold text-gray-900 mb-3">AI四方连续转换</h4>
                    <p className="text-gray-600 leading-relaxed">
                      对独幅矩形图转换成可四方连续的打印图，如需对结果放大请用AI无缝图放大功能。
                    </p>
                  </div>
                  <div className="bg-gradient-to-r from-blue-500 to-indigo-500 text-white py-3 px-6 rounded-xl text-center font-medium hover:from-blue-600 hover:to-indigo-600 transition-all">
                    立即使用
                  </div>
                </div>


                {/* AI矢量化(转SVG) */}
                <div className="bg-white rounded-2xl border border-gray-200 p-8 hover:shadow-xl transition-all hover:scale-105 cursor-pointer group"
                     onClick={() => setCurrentPage('style')}>
                  <div className="text-center mb-6">
                    <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-purple-50 to-pink-50 shadow-lg mx-auto mb-4 group-hover:shadow-xl transition-all">
                      <img
                        src="/AI矢量化转SVG.png"
                        alt="矢量化"
                        className="h-12 w-12 object-contain"
                      />
                    </div>
                    <h4 className="text-xl font-bold text-gray-900 mb-3">AI矢量化(转SVG)</h4>
                    <p className="text-gray-600 leading-relaxed">
                      使用AI一键将图片变成矢量图，线条清晰，图片还原。助力您的产品设计。
                    </p>
                    <div className="inline-block bg-orange-100 text-orange-600 px-3 py-1 rounded-full text-sm font-medium mt-2">
                      100算力
                    </div>
                  </div>
                  <div className="bg-gradient-to-r from-purple-500 to-pink-500 text-white py-3 px-6 rounded-xl text-center font-medium hover:from-purple-600 hover:to-pink-600 transition-all">
                    立即使用
                  </div>
                </div>

                {/* AI提取编辑*/}
                <div className="bg-white rounded-2xl border border-gray-200 p-8 hover:shadow-xl transition-all hover:scale-105 cursor-pointer group"
                     onClick={() => setCurrentPage('extract_edit')}>
                  <div className="text-center mb-6">
                    <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-green-50 to-emerald-50 shadow-lg mx-auto mb-4 group-hover:shadow-xl transition-all">
                      <img
                        src="/AI提取编辑.png"
                        alt="提取编辑"
                        className="h-12 w-12 object-contain"
                      />
                    </div>
                    <h4 className="text-xl font-bold text-gray-900 mb-3">AI提取编辑</h4>
                    <p className="text-gray-600 leading-relaxed">
                      使用AI提取和编辑图片内容，支持语音控制进行智能编辑。
                    </p>
                    <div className="inline-block bg-green-100 text-green-600 px-3 py-1 rounded-full text-sm font-medium mt-2">
                      智能语音
                    </div>
                  </div>
                  <div className="bg-gradient-to-r from-green-500 to-emerald-500 text-white py-3 px-6 rounded-xl text-center font-medium hover:from-green-600 hover:to-emerald-600 transition-all">
                    立即使用
                  </div>
                </div>

                {/* AI提取花型 */}
                <div className="bg-white rounded-2xl border border-gray-200 p-8 hover:shadow-xl transition-all hover:scale-105 cursor-pointer group"
                     onClick={() => setCurrentPage('extract_pattern')}>
                  <div className="text-center mb-6">
                    <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-rose-50 to-pink-50 shadow-lg mx-auto mb-4 group-hover:shadow-xl transition-all">
                      <img
                        src="/AI提取花型.png"
                        alt="提取花型"
                        className="h-12 w-12 object-contain"
                      />
                    </div>
                    <h4 className="text-xl font-bold text-gray-900 mb-3">AI提取花型</h4>
                    <p className="text-gray-600 leading-relaxed">
                      需预处理图片，支持用嘴改图。提取图案中的花型元素，适合设计应用。
                    </p>
                    <div className="inline-block bg-orange-100 text-orange-600 px-3 py-1 rounded-full text-sm font-medium mt-2">
                      100算力
                    </div>
                  </div>
                  <div className="bg-gradient-to-r from-rose-500 to-pink-500 text-white py-3 px-6 rounded-xl text-center font-medium hover:from-rose-600 hover:to-pink-600 transition-all">
                    立即使用
                  </div>
                </div>

                {/* AI智能去水印 */}
                <div className="bg-white rounded-2xl border border-gray-200 p-8 hover:shadow-xl transition-all hover:scale-105 cursor-pointer group"
                     onClick={() => setCurrentPage('watermark_removal')}>
                  <div className="text-center mb-6">
                    <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-50 to-blue-50 shadow-lg mx-auto mb-4 group-hover:shadow-xl transition-all">
                      <img
                        src="/AI智能去水印.png"
                        alt="智能去水印"
                        className="h-12 w-12 object-contain"
                      />
                    </div>
                    <h4 className="text-xl font-bold text-gray-900 mb-3">AI智能去水印</h4>
                    <p className="text-gray-600 leading-relaxed">
                      一键去水印。不管是顽固的文字水印、半透明logo水印，都能快捷去除。
                    </p>
                  </div>
                  <div className="bg-gradient-to-r from-cyan-500 to-blue-500 text-white py-3 px-6 rounded-xl text-center font-medium hover:from-cyan-600 hover:to-blue-600 transition-all">
                    立即使用
                  </div>
                </div>

                {/* AI布纹去噪去 */}
                <div className="bg-white rounded-2xl border border-gray-200 p-8 hover:shadow-xl transition-all hover:scale-105 cursor-pointer group"
                     onClick={() => setCurrentPage('noise_removal')}>
                  <div className="text-center mb-6">
                    <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-50 to-yellow-50 shadow-lg mx-auto mb-4 group-hover:shadow-xl transition-all">
                      <img
                        src="/AI布纹去噪.png"
                        alt="布纹去噪"
                        className="h-12 w-12 object-contain"
                      />
                    </div>
                    <h4 className="text-xl font-bold text-gray-900 mb-3">AI布纹去噪去</h4>
                    <p className="text-gray-600 leading-relaxed">
                      使用AI快速的去除图片中的噪点、布纹。还可用于对模糊矢量花的高清重绘。
                    </p>
                    <div className="inline-block bg-amber-100 text-amber-600 px-3 py-1 rounded-full text-sm font-medium mt-2">
                      80算力
                    </div>
                  </div>
                  <div className="bg-gradient-to-r from-amber-500 to-yellow-500 text-white py-3 px-6 rounded-xl text-center font-medium hover:from-amber-600 hover:to-yellow-600 transition-all">
                    立即使用
                  </div>
                </div>



                {/* AI毛线刺绣增强 */}
                <div className="bg-white rounded-2xl border border-gray-200 p-8 hover:shadow-xl transition-all hover:scale-105 cursor-pointer group"
                     onClick={() => setCurrentPage('embroidery')}>
                  <div className="text-center mb-6">
                    <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-50 to-purple-50 shadow-lg mx-auto mb-4 group-hover:shadow-xl transition-all">
                      <img
                        src="/AI毛线刺绣增强.png"
                        alt="AI毛线刺绣增强"
                        className="h-12 w-12 object-contain"
                      />
                    </div>
                    <h4 className="text-xl font-bold text-gray-900 mb-3">AI毛线刺绣增强</h4>
                    <p className="text-gray-600 leading-relaxed">
                      针对毛线刺绣转换的针对处理，转换出的刺绣对原图主体形状保持度高，毛线感的针法。
                    </p>
                  </div>
                  <div className="bg-gradient-to-r from-indigo-500 to-purple-500 text-white py-3 px-6 rounded-xl text-center font-medium hover:from-indigo-600 hover:to-purple-600 transition-all">
                    立即使用
                  </div>
                </div>
          </div>
        </main>
      </div>

      {/* Pricing Modal */}
      {showPricingModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-6xl max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="sticky top-0 bg-white border-b border-gray-200 px-8 py-6 rounded-t-2xl">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-gray-900">选择套餐</h2>
                <button 
                  onClick={() => setShowPricingModal(false)}
                  className="text-gray-400 hover:text-gray-600 text-2xl font-light"
                >
                  ×
                </button>
        </div>
              
              {/* Tab Navigation */}
              <div className="flex space-x-8 mt-6">
                <button 
                  onClick={() => setActiveTab('优惠套餐')}
                  className={`pb-2 border-b-2 transition ${
                    activeTab === '优惠套餐'
                      ? 'text-blue-600 border-blue-600 font-medium'
                      : 'text-gray-600 hover:text-blue-600 border-transparent hover:border-blue-600'
                  }`}
                >
                  优惠套餐
                </button>
                <button 
                  onClick={() => setActiveTab('包月会员')}
                  className={`pb-2 border-b-2 transition ${
                    activeTab === '包月会员'
                      ? 'text-blue-600 border-blue-600 font-medium'
                      : 'text-gray-600 hover:text-blue-600 border-transparent hover:border-blue-600'
                  }`}
                >
                  包月会员
                </button>
                <button 
                  onClick={() => setActiveTab('季度会员')}
                  className={`pb-2 border-b-2 transition ${
                    activeTab === '季度会员'
                      ? 'text-blue-600 border-blue-600 font-medium'
                      : 'text-gray-600 hover:text-blue-600 border-transparent hover:border-blue-600'
                  }`}
                >
                  季度会员
                </button>
                <button 
                  onClick={() => setActiveTab('包年会员')}
                  className={`pb-2 border-b-2 transition ${
                    activeTab === '包年会员'
                      ? 'text-blue-600 border-blue-600 font-medium'
                      : 'text-gray-600 hover:text-blue-600 border-transparent hover:border-blue-600'
                  }`}
                >
                  包年会员
                </button>
                <button 
                  onClick={() => setActiveTab('算力充值')}
                  className={`pb-2 border-b-2 transition ${
                    activeTab === '算力充值'
                      ? 'text-blue-600 border-blue-600 font-medium'
                      : 'text-gray-600 hover:text-blue-600 border-transparent hover:border-blue-600'
                  }`}
                >
                  算力充值
                </button>
                <button className="ml-auto text-blue-600 hover:text-blue-700 text-sm">
                  联系方式
                </button>
              </div>
            </div>

            {/* Pricing Plans */}
            <div className="px-8 py-8">
              {activeTab === '包月会员' && (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
                {/* 试用体验 */}
                <div className="bg-gray-50 rounded-2xl p-6 relative">
                  <div className="text-center mb-6">
                    <h3 className="text-xl font-bold text-gray-900 mb-2">试用体验</h3>
                    <div className="text-4xl font-bold text-gray-900 mb-1">
                      <span className="text-xl">¥</span>0
                    </div>
                    <p className="text-sm text-gray-500">免费试用高级智能设计体验</p>
                  </div>
                  
                  <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-medium mb-6 transition">
                    立即开通
                  </button>
                  
                  <div className="space-y-3 text-sm">
                    <div className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      <span className="text-gray-700">赠送200算力积分</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      <span className="text-gray-700">7天内有效</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      <span className="text-gray-700">循环图案处理</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      <span className="text-gray-700">定位花提取</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      <span className="text-gray-700">高清放大</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      <span className="text-gray-700">毛线刺绣增强</span>
                    </div>
                  </div>
                </div>

                {/* 轻享版 */}
                <div className="bg-white rounded-2xl p-6 border-2 border-blue-200 relative">
                  <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                    <span className="bg-red-500 text-white px-4 py-1 rounded-full text-sm font-medium">限时优惠</span>
                  </div>
                  
                  <div className="text-center mb-6">
                    <h3 className="text-xl font-bold text-gray-900 mb-2">轻享版</h3>
                    <div className="text-4xl font-bold text-gray-900 mb-1">
                      <span className="text-xl">¥</span>29
                    </div>
                    <p className="text-sm text-gray-400 line-through">原价49</p>
                  </div>
                  
                  <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-medium mb-6 transition">
                    立即开通
                  </button>
                  
                  <div className="space-y-3 text-sm">
                    <div className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      <span className="text-gray-700">每月3000算力积分</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      <span className="text-gray-700">AI应用高速队列</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      <span className="text-gray-700">循环图案处理</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      <span className="text-gray-700">定位花提取</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      <span className="text-gray-700">高清放大</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      <span className="text-gray-700">矢量风格转换(会员专享)</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      <span className="text-gray-700">毛线刺绣增强</span>
                    </div>
                  </div>
                </div>

                {/* 基础版 */}
                <div className="bg-white rounded-2xl p-6 border-2 border-blue-200 relative">
                  <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                    <span className="bg-red-500 text-white px-4 py-1 rounded-full text-sm font-medium">限时优惠</span>
                  </div>
                  
                  <div className="text-center mb-6">
                    <h3 className="text-xl font-bold text-gray-900 mb-2">基础版</h3>
                    <div className="text-4xl font-bold text-gray-900 mb-1">
                      <span className="text-xl">¥</span>69
                    </div>
                    <p className="text-sm text-gray-400 line-through">原价89</p>
                  </div>
                  
                  <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-medium mb-6 transition">
                    立即开通
                  </button>
                  
                  <div className="space-y-3 text-sm">
                    <div className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      <span className="text-gray-700">每月7500算力积分</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      <span className="text-gray-700">AI应用高速队列</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      <span className="text-gray-700">循环图案处理</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      <span className="text-gray-700">定位花提取</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      <span className="text-gray-700">矢量风格转换(会员专享)</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      <span className="text-gray-700">高清放大</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      <span className="text-gray-700">优先处理队列</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      <span className="text-gray-700">毛线刺绣增强</span>
                    </div>
                  </div>
                </div>

                {/* 高级版 */}
                <div className="bg-white rounded-2xl p-6 border-2 border-blue-200 relative">
                  <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                    <span className="bg-red-500 text-white px-4 py-1 rounded-full text-sm font-medium">限时优惠</span>
                  </div>
                  
                  <div className="text-center mb-6">
                    <h3 className="text-xl font-bold text-gray-900 mb-2">高级版</h3>
                    <div className="text-4xl font-bold text-gray-900 mb-1">
                      <span className="text-xl">¥</span>99
                    </div>
                    <p className="text-sm text-gray-400 line-through">原价149</p>
                  </div>
                  
                  <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-medium mb-6 transition">
                    立即开通
                  </button>
                  
                  <div className="space-y-3 text-sm">
                    <div className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      <span className="text-gray-700">每月11000算力积分</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      <span className="text-gray-700">AI应用高速队列</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      <span className="text-gray-700">循环图案处理</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      <span className="text-gray-700">定位花提取</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      <span className="text-gray-700">矢量风格转换(会员专享)</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      <span className="text-gray-700">进一步处理(会员专享)</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      <span className="text-gray-700">高清放大</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      <span className="text-gray-700">超级高速队列</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      <span className="text-gray-700">自定义处理指令</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      <span className="text-gray-700">毛线刺绣增强</span>
                    </div>
                  </div>
                </div>
                </div>
              )}

              {activeTab === '优惠套餐' && (
                <div className="text-center py-16">
                  <div className="text-6xl mb-4">🎁</div>
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">优惠套餐</h3>
                  <p className="text-gray-600">特价优惠套餐即将推出，敬请期待！</p>
                </div>
              )}

              {activeTab === '季度会员' && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="bg-white rounded-2xl p-6 border-2 border-blue-200 relative">
                    <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                      <span className="bg-green-500 text-white px-4 py-1 rounded-full text-sm font-medium">季度优惠</span>
                    </div>
                    
                    <div className="text-center mb-6">
                      <h3 className="text-xl font-bold text-gray-900 mb-2">轻享季度版</h3>
                      <div className="text-4xl font-bold text-gray-900 mb-1">
                        <span className="text-xl">¥</span>79
                      </div>
                      <p className="text-sm text-gray-400 line-through">原价129</p>
                      <p className="text-xs text-gray-500 mt-1">3个月套餐</p>
                    </div>
                    
                    <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-medium mb-6 transition">
                      立即开通
              </button>
                    
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center">
                        <span className="text-green-500 mr-2">✓</span>
                        <span className="text-gray-700">每月8000算力积分</span>
                      </div>
                      <div className="flex items-center">
                        <span className="text-green-500 mr-2">✓</span>
                        <span className="text-gray-700">所有基础功能</span>
                      </div>
                      <div className="flex items-center">
                        <span className="text-green-500 mr-2">✓</span>
                        <span className="text-gray-700">矢量风格转换</span>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white rounded-2xl p-6 border-2 border-blue-200 relative">
                    <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                      <span className="bg-green-500 text-white px-4 py-1 rounded-full text-sm font-medium">最受欢迎</span>
                    </div>
                    
                    <div className="text-center mb-6">
                      <h3 className="text-xl font-bold text-gray-900 mb-2">标准季度版</h3>
                      <div className="text-4xl font-bold text-gray-900 mb-1">
                        <span className="text-xl">¥</span>179
                      </div>
                      <p className="text-sm text-gray-400 line-through">原价239</p>
                      <p className="text-xs text-gray-500 mt-1">3个月套餐</p>
                    </div>
                    
                    <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-medium mb-6 transition">
                      立即开通
                    </button>
                    
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center">
                        <span className="text-green-500 mr-2">✓</span>
                        <span className="text-gray-700">每月20000算力积分</span>
                      </div>
                      <div className="flex items-center">
                        <span className="text-green-500 mr-2">✓</span>
                        <span className="text-gray-700">所有功能无限制</span>
                      </div>
                      <div className="flex items-center">
                        <span className="text-green-500 mr-2">✓</span>
                        <span className="text-gray-700">优先处理队列</span>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white rounded-2xl p-6 border-2 border-blue-200 relative">
                    <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                      <span className="bg-purple-500 text-white px-4 py-1 rounded-full text-sm font-medium">专业版</span>
                    </div>
                    
                    <div className="text-center mb-6">
                      <h3 className="text-xl font-bold text-gray-900 mb-2">专业季度版</h3>
                      <div className="text-4xl font-bold text-gray-900 mb-1">
                        <span className="text-xl">¥</span>259
                      </div>
                      <p className="text-sm text-gray-400 line-through">原价359</p>
                      <p className="text-xs text-gray-500 mt-1">3个月套餐</p>
                    </div>
                    
                    <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-medium mb-6 transition">
                      立即开通
                    </button>
                    
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center">
                        <span className="text-green-500 mr-2">✓</span>
                        <span className="text-gray-700">每月30000算力积分</span>
                      </div>
                      <div className="flex items-center">
                        <span className="text-green-500 mr-2">✓</span>
                        <span className="text-gray-700">专业功能全解锁</span>
                      </div>
                      <div className="flex items-center">
                        <span className="text-green-500 mr-2">✓</span>
                        <span className="text-gray-700">超级高速队列</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === '包年会员' && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="bg-white rounded-2xl p-6 border-2 border-blue-200 relative">
                    <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                      <span className="bg-yellow-500 text-white px-4 py-1 rounded-full text-sm font-medium">超值年费</span>
                    </div>
                    
                    <div className="text-center mb-6">
                      <h3 className="text-xl font-bold text-gray-900 mb-2">标准年费版</h3>
                      <div className="text-4xl font-bold text-gray-900 mb-1">
                        <span className="text-xl">¥</span>299
                      </div>
                      <p className="text-sm text-gray-400 line-through">原价588</p>
                      <p className="text-xs text-gray-500 mt-1">12个月套餐</p>
                    </div>
                    
                    <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-medium mb-6 transition">
                      立即开通
                    </button>
                    
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center">
                        <span className="text-green-500 mr-2">✓</span>
                        <span className="text-gray-700">每月10000算力积分</span>
                  </div>
                      <div className="flex items-center">
                        <span className="text-green-500 mr-2">✓</span>
                        <span className="text-gray-700">全功能访问</span>
                    </div>
                      <div className="flex items-center">
                        <span className="text-green-500 mr-2">✓</span>
                        <span className="text-gray-700">年费专享特权</span>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white rounded-2xl p-6 border-2 border-purple-200 relative">
                    <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                      <span className="bg-purple-500 text-white px-4 py-1 rounded-full text-sm font-medium">企业首选</span>
                    </div>
                    
                    <div className="text-center mb-6">
                      <h3 className="text-xl font-bold text-gray-900 mb-2">专业年费版</h3>
                      <div className="text-4xl font-bold text-gray-900 mb-1">
                        <span className="text-xl">¥</span>599
                      </div>
                      <p className="text-sm text-gray-400 line-through">原价1188</p>
                      <p className="text-xs text-gray-500 mt-1">12个月套餐</p>
                    </div>
                    
                    <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-medium mb-6 transition">
                      立即开通
                    </button>
                    
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center">
                        <span className="text-green-500 mr-2">✓</span>
                        <span className="text-gray-700">每月25000算力积分</span>
                      </div>
                      <div className="flex items-center">
                        <span className="text-green-500 mr-2">✓</span>
                        <span className="text-gray-700">企业级服务</span>
                      </div>
                      <div className="flex items-center">
                        <span className="text-green-500 mr-2">✓</span>
                        <span className="text-gray-700">专属技术支持</span>
                      </div>
                    </div>
                  </div>

                  <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-2xl p-6 border-2 border-purple-300 relative">
                    <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                      <span className="bg-gradient-to-r from-purple-500 to-blue-500 text-white px-4 py-1 rounded-full text-sm font-medium">至尊版</span>
                    </div>
                    
                    <div className="text-center mb-6">
                      <h3 className="text-xl font-bold text-gray-900 mb-2">至尊年费版</h3>
                      <div className="text-4xl font-bold text-gray-900 mb-1">
                        <span className="text-xl">¥</span>999
                      </div>
                      <p className="text-sm text-gray-400 line-through">原价1788</p>
                      <p className="text-xs text-gray-500 mt-1">12个月套餐</p>
                    </div>
                    
                    <button className="w-full bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white py-3 rounded-xl font-medium mb-6 transition">
                      立即开通
                    </button>
                    
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center">
                        <span className="text-green-500 mr-2">✓</span>
                        <span className="text-gray-700">无限算力积分</span>
                      </div>
                      <div className="flex items-center">
                        <span className="text-green-500 mr-2">✓</span>
                        <span className="text-gray-700">全功能无限制</span>
                      </div>
                      <div className="flex items-center">
                        <span className="text-green-500 mr-2">✓</span>
                        <span className="text-gray-700">VIP专属服务</span>
                      </div>
                    </div>
                  </div>
                  </div>
                )}

              {activeTab === '算力充值' && (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
                  <div className="bg-white rounded-2xl p-6 border border-gray-200">
                    <div className="text-center mb-6">
                      <h3 className="text-xl font-bold text-gray-900 mb-2">基础算力包</h3>
                      <div className="text-4xl font-bold text-gray-900 mb-1">
                        <span className="text-xl">¥</span>19
              </div>
                      <p className="text-sm text-gray-500">1000算力积分</p>
          </div>
                    
                    <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-medium mb-4 transition">
                      立即购买
                    </button>
                    
                    <div className="text-xs text-gray-500 text-center">
                      适合偶尔使用
        </div>
                  </div>

                  <div className="bg-white rounded-2xl p-6 border-2 border-blue-200 relative">
                    <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                      <span className="bg-blue-500 text-white px-4 py-1 rounded-full text-sm font-medium">推荐</span>
        </div>
                    
                    <div className="text-center mb-6">
                      <h3 className="text-xl font-bold text-gray-900 mb-2">标准算力包</h3>
                      <div className="text-4xl font-bold text-gray-900 mb-1">
                        <span className="text-xl">¥</span>49
                      </div>
                      <p className="text-sm text-gray-500">3000算力积分</p>
                    </div>
                    
                    <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-medium mb-4 transition">
                      立即购买
                    </button>
                    
                    <div className="text-xs text-gray-500 text-center">
                      性价比最高
                    </div>
                  </div>

                  <div className="bg-white rounded-2xl p-6 border border-gray-200">
                    <div className="text-center mb-6">
                      <h3 className="text-xl font-bold text-gray-900 mb-2">专业算力包</h3>
                      <div className="text-4xl font-bold text-gray-900 mb-1">
                        <span className="text-xl">¥</span>99
                      </div>
                      <p className="text-sm text-gray-500">7000算力积分</p>
                    </div>
                    
                    <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-medium mb-4 transition">
                      立即购买
                    </button>
                    
                    <div className="text-xs text-gray-500 text-center">
                      适合专业用户
                    </div>
                  </div>

                  <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-2xl p-6 border-2 border-purple-200 relative">
                    <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                      <span className="bg-purple-500 text-white px-4 py-1 rounded-full text-sm font-medium">超值</span>
                    </div>
                    
                    <div className="text-center mb-6">
                      <h3 className="text-xl font-bold text-gray-900 mb-2">企业算力包</h3>
                      <div className="text-4xl font-bold text-gray-900 mb-1">
                        <span className="text-xl">¥</span>199
                      </div>
                      <p className="text-sm text-gray-500">15000算力积分</p>
                    </div>
                    
                    <button className="w-full bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white py-3 rounded-xl font-medium mb-4 transition">
                      立即购买
                    </button>
                    
                    <div className="text-xs text-gray-500 text-center">
                      企业团队首选
                    </div>
                  </div>
                </div>
              )}

              {/* Footer Notes */}
              {(activeTab === '包月会员' || activeTab === '季度会员' || activeTab === '包年会员') && (
                <div className="mt-8 text-xs text-gray-500 space-y-2">
                  <p>1. 算力积分有效期：包套餐购买的算力积分，有效期为一年，如果有效期内未使用算力积分，将自动失效。</p>
                  <p>2. 取消续费：第三方支付的套餐，用户可在支付管理中心，取消自动续费。</p>
                </div>
              )}

              {activeTab === '算力充值' && (
                <div className="mt-8 text-xs text-gray-500 space-y-2">
                  <p>1. 算力积分永久有效：单独购买的算力积分永久有效，不会过期。</p>
                  <p>2. 支付方式：支持微信支付、支付宝等多种支付方式。</p>
                  <p>3. 发票服务：企业用户可联系客服开具发票。</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
