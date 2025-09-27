'use client';

import React, { useState, useRef } from 'react';
import { Upload, Image as ImageIcon, Settings, Download, History, Star, Grid, Zap, Crown, Search, User, Bell } from 'lucide-react';

type ProcessingMethod = 'seamless' | 'positioning' | 'style' | 'advanced' | 'upscale';

interface ProcessingOptions {
  seamless: {
    removeBackground: boolean;
    seamlessLoop: boolean;
  };
  positioning: {
    precision: 'high' | 'medium' | 'low';
    optimization: boolean;
  };
  style: {
    outputStyle: 'vector' | 'seamless';
    outputRatio: '1:1' | '2:3' | '3:2';
  };
  advanced: {
    customPrompt: string;
  };
  upscale: {
    maintainStyle: boolean;
    maintainColor: boolean;
  };
}

export default function Home() {
  const [uploadedImage, setUploadedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [selectedMethod, setSelectedMethod] = useState<ProcessingMethod | null>(null);
  const [processedImage, setProcessedImage] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [options, setOptions] = useState<ProcessingOptions>({
    seamless: {
      removeBackground: true,
      seamlessLoop: true,
    },
    positioning: {
      precision: 'high',
      optimization: true,
    },
    style: {
      outputStyle: 'vector',
      outputRatio: '1:1',
    },
    advanced: {
      customPrompt: '',
    },
    upscale: {
      maintainStyle: true,
      maintainColor: true,
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

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
        <div className="flex items-center justify-between px-6 py-4">
          {/* Logo and Brand */}
          <div className="flex items-center space-x-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl overflow-hidden shadow-lg">
              <img 
                src="/logo.jpg" 
                alt="Logo" 
                className="h-full w-full object-cover"
              />
            </div>
            <span className="text-xl font-bold text-gray-900">应用中心</span>
          </div>
          
          {/* Right Navigation */}
          <div className="flex items-center space-x-4">
            <button className="text-blue-600 hover:text-blue-700 text-sm font-medium">
              收藏夹项目
            </button>
            <button className="text-blue-600 hover:text-blue-700 text-sm font-medium">
              设计专题
            </button>
            <button className="text-blue-600 hover:text-blue-700 text-sm font-medium">
              联系我们
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
          {/* Hot Tools Section */}
          <section>
            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
              <Star className="h-5 w-5 text-yellow-500 mr-2" />
              热门工具
            </h3>
            <div className="space-y-2">
              <div className="p-3 rounded-lg bg-orange-50 border border-orange-200 cursor-pointer hover:bg-orange-100 transition"
                onClick={() => setSelectedMethod('seamless')}
              >
                <div className="flex items-center space-x-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-orange-400 to-orange-500 text-white shadow-sm">
                    🔄
                  </div>
                  <div>
                    <div className="font-medium text-gray-900 text-sm">循环图</div>
                    <div className="text-xs text-gray-500">将图案处理为四方连续的循环图案，适合大面积印花使用</div>
                    <div className="text-xs text-orange-600 font-medium">推荐功能</div>
                  </div>
                </div>
              </div>
              <div className="p-3 rounded-lg bg-blue-50 border border-blue-200 cursor-pointer hover:bg-blue-100 transition"
                onClick={() => setSelectedMethod('style')}
              >
                <div className="flex items-center space-x-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-purple-400 to-purple-500 text-white shadow-sm">
                    🧩
                  </div>
                  <div>
                    <div className="font-medium text-gray-900 text-sm">通用/矢量风格图案</div>
                    <div className="text-xs text-gray-500">适用于球服、徽章、大牌logo等图案提取</div>
                    <div className="text-xs text-blue-600 font-medium">高质量输出</div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Categories */}
          <section>
            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
              <Grid className="h-5 w-5 text-blue-500 mr-2" />
              功能分类
            </h3>
            <div className="space-y-2 text-sm">
              <button 
                className="w-full text-left px-3 py-2 rounded-lg hover:bg-gray-50 text-gray-700 transition flex items-center space-x-2"
                onClick={() => setSelectedMethod('seamless')}
              >
                <span>🔄</span>
                <span>循环图案</span>
              </button>
              <button 
                className="w-full text-left px-3 py-2 rounded-lg hover:bg-gray-50 text-gray-700 transition flex items-center space-x-2"
                onClick={() => setSelectedMethod('positioning')}
              >
                <span>🎯</span>
                <span>定位印花</span>
              </button>
              <button 
                className="w-full text-left px-3 py-2 rounded-lg hover:bg-gray-50 text-gray-700 transition flex items-center space-x-2"
                onClick={() => setSelectedMethod('style')}
              >
                <span>🧩</span>
                <span>矢量风格</span>
              </button>
              <button 
                className="w-full text-left px-3 py-2 rounded-lg hover:bg-gray-50 text-gray-700 transition flex items-center space-x-2"
                onClick={() => setSelectedMethod('advanced')}
              >
                <span>✨</span>
                <span>进一步处理</span>
              </button>
            </div>
          </section>

          {/* High Resolution Section */}
          <section>
            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
              <span className="h-5 w-5 mr-2">🔍</span>
              图像增强
            </h3>
            <div className="space-y-2 text-sm">
              <button 
                className="w-full text-left px-3 py-2 rounded-lg hover:bg-gray-50 text-gray-700 transition"
                onClick={() => setSelectedMethod('upscale' as any)}
              >
                高清放大
              </button>
            </div>
          </section>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 p-8">
          {/* Search Section */}
          <div className="mb-8">
            <div className="relative max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="搜索工具..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          {/* Main Content Layout - Left: Tools, Right: Upload & Results */}
          <div className="grid grid-cols-1 lg:grid-cols-[2fr,1fr] gap-8">
            {/* Left Side - Tool Selection and Options */}
            <div className="space-y-6">
              {/* Tool Cards Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* 循环图 */}
                <div className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg transition-shadow">
                  <div className="flex items-start space-x-4 mb-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-br from-orange-400 to-orange-500 text-white shadow-sm">
                      🔄
                    </div>
                    <div className="flex-1">
                      <h4 className="font-semibold text-gray-900 mb-2">循环图</h4>
                      <p className="text-sm text-gray-600 mb-2">
                        将图案处理为四方连续的循环图案，适合大面积印花使用，图案可无缝拼接。
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <button
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                        selectedMethod === 'seamless'
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-blue-50'
                      }`}
                      onClick={() => setSelectedMethod('seamless')}
                    >
                      选择此工具
                    </button>
                  </div>
                </div>

                {/* 定位花 */}
                <div className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg transition-shadow">
                  <div className="flex items-start space-x-4 mb-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-br from-blue-400 to-blue-500 text-white shadow-sm">
                      🎯
                    </div>
                    <div className="flex-1">
                      <h4 className="font-semibold text-gray-900 mb-2">定位花</h4>
                      <p className="text-sm text-gray-600 mb-2">
                        精确定位图案主体，优化细节展示，适合需要突出主体图案的定位印花。
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <button
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                        selectedMethod === 'positioning'
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-blue-50'
                      }`}
                      onClick={() => setSelectedMethod('positioning')}
                    >
                      选择此工具
                    </button>
                  </div>
                </div>

                {/* 通用/矢量风格图案 */}
                <div className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg transition-shadow">
                  <div className="flex items-start space-x-4 mb-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-br from-purple-400 to-purple-500 text-white shadow-sm">
                      🧩
                    </div>
                    <div className="flex-1">
                      <h4 className="font-semibold text-gray-900 mb-2">通用/矢量风格图案</h4>
                      <p className="text-sm text-gray-600 mb-2">
                        此方式适用于球服、徽章、大牌logo等图案的提取，可以选择矢量风格输出。按载比例选择输出比例，出图时间会稍慢一些，图案清晰度更上大概3分钟出一张图。
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <button
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                        selectedMethod === 'style'
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-blue-50'
                      }`}
                      onClick={() => setSelectedMethod('style')}
                    >
                      选择此工具
                    </button>
                  </div>
                </div>

                {/* 进一步处理 */}
                <div className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg transition-shadow">
                  <div className="flex items-start space-x-4 mb-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-br from-green-400 to-green-500 text-white shadow-sm">
                      ✨
                    </div>
                    <div className="flex-1">
                      <h4 className="font-semibold text-gray-900 mb-2">进一步处理</h4>
                      <p className="text-sm text-gray-600 mb-2">
                        换背景、去水印、去统花、换风格(3D,刺绣,水彩等)、花型图案换色、服装换色换花型、模特换装试衣等都可以在这个处理方式实现
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <button
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                        selectedMethod === 'advanced'
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-blue-50'
                      }`}
                      onClick={() => setSelectedMethod('advanced')}
                    >
                      选择此工具
                    </button>
                  </div>
                </div>

                {/* 高清放大 */}
                <div className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg transition-shadow">
                  <div className="flex items-start space-x-4 mb-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-400 to-indigo-500 text-white shadow-sm">
                      🔍
                    </div>
                    <div className="flex-1">
                      <h4 className="font-semibold text-gray-900 mb-2">高清放大</h4>
                      <p className="text-sm text-gray-600 mb-2">
                        将图片高清放大，增强图案细节，同时保持原有风格和色彩不变，适合需要高质量大图的场景。
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <button
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                        selectedMethod === 'upscale'
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-blue-50'
                      }`}
                      onClick={() => setSelectedMethod('upscale' as any)}
                    >
                      选择此工具
                    </button>
                  </div>
                </div>
              </div>

              {/* Tool Options */}
              {selectedMethod && (
                <div className="bg-white rounded-xl border border-gray-200 p-6">
                  <h4 className="text-lg font-semibold text-gray-900 mb-4">工具选项</h4>
                  {selectedMethod === 'seamless' && (
                    <div className="space-y-3">
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
                  {selectedMethod === 'positioning' && (
                    <div>
                      <label className="block text-sm font-medium mb-2">精确定位</label>
                      <select
                        value={options.positioning.precision}
                        onChange={(e) => updateOptions('positioning', { precision: e.target.value as any })}
                        className="w-full rounded border-gray-300"
                      >
                        <option value="high">高精度</option>
                        <option value="medium">中精度</option>
                        <option value="low">低精度</option>
                      </select>
                    </div>
                  )}
                  {selectedMethod === 'style' && (
                    <div className="space-y-4">
                      <div>
                        <p className="text-sm font-medium mb-3">输出风格</p>
                        <div className="flex space-x-2">
                          <button
                            onClick={() => updateOptions('style', { outputStyle: 'vector' })}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                              options.style.outputStyle === 'vector'
                                ? 'bg-blue-500 text-white'
                                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                            }`}
                          >
                            矢量风格
                          </button>
                          <button
                            onClick={() => updateOptions('style', { outputStyle: 'seamless' })}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
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
                        <p className="text-sm font-medium mb-3">输出比例</p>
                        <div className="flex space-x-2">
                          {['1:1', '2:3', '3:2'].map((ratio) => (
                            <button
                              key={ratio}
                              onClick={() => updateOptions('style', { outputRatio: ratio as any })}
                              className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
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
                  {selectedMethod === 'advanced' && (
                    <div>
                      <label className="block text-sm font-medium mb-2">请输入处理指令</label>
                      <textarea
                        value={options.advanced.customPrompt}
                        onChange={(e) => updateOptions('advanced', { customPrompt: e.target.value })}
                        placeholder="例如: 提取花卉图案，将背景换成白色/提取花卉图案，去除绿花图案"
                        className="w-full h-24 rounded border-gray-300 text-sm"
                      />
                    </div>
                  )}
                  {selectedMethod === 'upscale' && (
                    <div className="space-y-3">
                      <label className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={options.upscale.maintainStyle}
                          onChange={(e) => updateOptions('upscale', { maintainStyle: e.target.checked })}
                          className="rounded border-gray-300"
                        />
                        <span className="text-sm">保持原有风格</span>
                      </label>
                      <label className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={options.upscale.maintainColor}
                          onChange={(e) => updateOptions('upscale', { maintainColor: e.target.checked })}
                          className="rounded border-gray-300"
                        />
                        <span className="text-sm">保持色彩不变</span>
                      </label>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Right Side - Upload and Results */}
            <div className="space-y-6">
              {/* Upload Section */}
              <div className="bg-white rounded-xl border border-gray-200 p-6">
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
                      <p className="text-sm text-gray-500">点击或拖拽替换图片</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <Upload className="mx-auto h-12 w-12 text-gray-400" />
                      <div>
                        <p className="text-base font-medium text-gray-700">点击或拖拽图片到此处上传</p>
                        <p className="text-sm text-gray-500">支持 JPG、PNG 等格式</p>
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

              {/* Process Button */}
              {uploadedImage && selectedMethod && (
                <button
                  onClick={handleProcessImage}
                  disabled={isProcessing}
                  className="w-full flex items-center justify-center space-x-2 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white font-medium py-3 rounded-lg transition"
                >
                  {isProcessing ? (
                    <>
                      <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                      <span>处理中...</span>
                    </>
                  ) : (
                    <>
                      <Settings className="h-5 w-5" />
                      <span>开始提取图案</span>
                    </>
                  )}
                </button>
              )}

              {/* Results Section */}
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">处理结果</h3>
                <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center min-h-[200px] flex items-center justify-center">
                  {processedImage ? (
                    <div className="space-y-4">
                      <img
                        src={processedImage}
                        alt="Processed"
                        className="mx-auto max-h-32 rounded-lg border border-gray-200"
                      />
                      <button className="bg-green-500 hover:bg-green-600 text-white px-6 py-2 rounded-lg font-medium transition">
                        下载结果
                      </button>
                    </div>
                  ) : (
                    <div className="text-gray-500">
                      <Download className="mx-auto h-12 w-12 mb-2" />
                      <p className="text-sm">处理后的图案将显示在这里</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
