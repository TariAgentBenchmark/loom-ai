'use client';

import React, { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import { X, Download, ZoomIn, ZoomOut, RotateCw, ChevronLeft, ChevronRight } from 'lucide-react';
import { HistoryTask } from '../lib/api';
import { resolveFileUrl } from '../lib/api';

interface ImagePreviewProps {
  task: HistoryTask | null;
  onClose: () => void;
  accessToken: string;
}

const ImagePreview: React.FC<ImagePreviewProps> = ({ task, onClose, accessToken }) => {
  const [scale, setScale] = useState(1);
  const [initialScale, setInitialScale] = useState(1);
  const [rotation, setRotation] = useState(0);
  const [showOriginal, setShowOriginal] = useState(true);
  const [currentResultIndex, setCurrentResultIndex] = useState(0);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const imageContainerRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);
  const objectRef = useRef<HTMLObjectElement>(null);

  // 处理触控板双指缩放和鼠标滚轮缩放
  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();

    // 触控板双指手势（Ctrl/Cmd + 滚轮）- 精细缩放
    if (e.ctrlKey || e.metaKey) {
      const delta = e.deltaY > 0 ? -0.1 : 0.1;
      setScale(prev => {
        const minScale = Math.min(initialScale, 0.5);
        return Math.min(Math.max(prev + delta, minScale), 3);
      });
    } else {
      // 鼠标滚轮缩放 - 标准缩放
      const delta = e.deltaY > 0 ? -0.25 : 0.25;
      setScale(prev => {
        const minScale = Math.min(initialScale, 0.5);
        return Math.min(Math.max(prev + delta, minScale), 3);
      });
    }
  }, [initialScale]);

  // 处理鼠标拖动
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    // 允许在任何缩放级别下拖动
    setIsDragging(true);
    setDragStart({
      x: e.clientX - position.x,
      y: e.clientY - position.y
    });
  }, [position]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (isDragging) {
      e.preventDefault();
      setPosition({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      });
    }
  }, [isDragging, dragStart]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  const resultUrls = useMemo(() => {
    if (!task?.resultImage?.url) {
      return [];
    }
    return task.resultImage.url.split(',').map(u => u.trim());
  }, [task]);

  const resultFilenames = useMemo(() => {
    if (!task?.resultImage?.filename) {
      return [];
    }
    return task.resultImage.filename.split(',').map(f => f.trim());
  }, [task]);

  const hasMultipleResults = resultUrls.length > 1;

  const handleDownload = useCallback(async (imageUrl: string, filename: string) => {
    try {
      const response = await fetch(resolveFileUrl(imageUrl));
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('下载失败:', err);
    }
  }, []);

  const handleDownloadAll = useCallback(async () => {
    if (!hasMultipleResults) return;

    for (let i = 0; i < resultUrls.length; i++) {
      await handleDownload(resultUrls[i], resultFilenames[i] || `result_${i + 1}.png`);
      if (i < resultUrls.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 500));
      }
    }
  }, [handleDownload, hasMultipleResults, resultFilenames, resultUrls]);

  const handleZoomIn = useCallback(() => {
    setScale(prev => {
      const minScale = Math.min(initialScale, 0.5);
      return Math.min(Math.max(prev + 0.25, minScale), 3);
    });
  }, [initialScale]);

  const handleZoomOut = useCallback(() => {
    setScale(prev => {
      const minScale = Math.min(initialScale, 0.5);
      return Math.min(Math.max(prev - 0.25, minScale), 3);
    });
  }, [initialScale]);

  const handleRotate = () => {
    setRotation(prev => (prev + 90) % 360);
  };

  const handleReset = useCallback(() => {
    setScale(initialScale);
    setRotation(0);
    setPosition({ x: 0, y: 0 });
  }, [initialScale]);

  const handleImageLoad = useCallback(() => {
    const container = imageContainerRef.current;
    const img = imageRef.current;
    const obj = objectRef.current;
    
    // 优先使用img元素，如果不存在则使用object元素
    const element = img || obj;
    if (!container || !element) {
      return;
    }
    
    // 对于SVG文件，使用不同的尺寸获取方式
    let width = 0, height = 0;
    if (img && img.naturalWidth && img.naturalHeight) {
      width = img.naturalWidth;
      height = img.naturalHeight;
    } else if (obj) {
      // 对于object元素，尝试获取SVG的尺寸
      const svgDoc = obj.contentDocument;
      if (svgDoc && svgDoc.documentElement) {
        width = parseFloat(svgDoc.documentElement.getAttribute('width') || '500');
        height = parseFloat(svgDoc.documentElement.getAttribute('height') || '500');
      }
    }
    
    if (!width || !height) {
      // 如果无法获取尺寸，使用默认值
      width = 500;
      height = 500;
    }

    const widthScale = container.clientWidth / width;
    const heightScale = container.clientHeight / height;
    const nextScale = Math.min(widthScale, heightScale, 1);
    const safeScale = nextScale > 0 && Number.isFinite(nextScale) ? nextScale : 1;

    setInitialScale(safeScale);
    setScale(safeScale);
    setPosition({ x: 0, y: 0 });
    setRotation(0);
  }, []);

  // 获取当前显示的图片信息
  const getCurrentResultImage = useCallback(() => {
    if (!task?.resultImage || resultUrls.length === 0) return null;

    return {
      url: resultUrls[currentResultIndex] || resultUrls[0],
      filename: resultFilenames[currentResultIndex] || resultFilenames[0] || 'result.png',
      size: task.resultImage.size,
      dimensions: task.resultImage.dimensions
    };
  }, [currentResultIndex, resultFilenames, resultUrls, task]);

  const currentImage = useMemo(() => {
    if (!task) return null;
    return showOriginal ? task.originalImage : getCurrentResultImage();
  }, [getCurrentResultImage, showOriginal, task]);

  const hasResultImage = !!task?.resultImage;
  const currentImageUrl = currentImage?.url;

  useEffect(() => {
    // 切换任务或结果变化时重置索引，并默认展示结果图（有结果时）
    setCurrentResultIndex(0);
    setShowOriginal(!task?.resultImage);
  }, [task?.resultImage, task?.taskId, resultUrls.length]);

  const handleNavigateResult = useCallback((direction: number) => {
    if (!hasMultipleResults) return;
    setShowOriginal(false);
    setCurrentResultIndex(prev => {
      const next = prev + direction;
      if (next < 0) return resultUrls.length - 1;
      if (next >= resultUrls.length) return 0;
      return next;
    });
  }, [hasMultipleResults, resultUrls.length]);

  useEffect(() => {
    if (!currentImageUrl) {
      setInitialScale(1);
      setScale(1);
      setPosition({ x: 0, y: 0 });
      setRotation(0);
      return;
    }

    setPosition({ x: 0, y: 0 });
    setRotation(0);

    if (!imageRef.current?.complete) {
      setScale(initialScale);
      return;
    }

    handleImageLoad();
  }, [currentImageUrl, handleImageLoad, initialScale]);

  if (!task) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-90 z-50 flex items-center justify-center">
      <div className="relative w-full h-full flex flex-col">
        {/* 顶部工具栏 */}
        <div className="flex flex-col md:flex-row md:items-center justify-between p-3 md:p-4 bg-black bg-opacity-50 gap-2">
          <div className="flex items-center space-x-2 md:space-x-4">
            <h3 className="text-white text-sm md:font-medium truncate max-w-[120px] md:max-w-none">{task.typeName}</h3>
            <div className="flex items-center space-x-1 md:space-x-2">
              <button
                onClick={() => setShowOriginal(false)}
                className={`px-2 py-1 md:px-3 rounded text-xs md:text-sm transition ${
                  !showOriginal
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-600 text-gray-300 hover:bg-gray-500'
                }`}
                disabled={!hasResultImage}
              >
                结果
              </button>
              <button
                onClick={() => setShowOriginal(true)}
                className={`px-2 py-1 md:px-3 rounded text-xs md:text-sm transition ${
                  showOriginal
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-600 text-gray-300 hover:bg-gray-500'
                }`}
                disabled={!hasResultImage}
              >
                原图
              </button>
            </div>
          </div>

          <div className="flex items-center space-x-1 md:space-x-2">
            {/* 多图片切换按钮 */}
            {hasMultipleResults && !showOriginal && (
              <div className="flex items-center space-x-1 border-r border-gray-600 pr-2 mr-2">
              <button
                onClick={() => handleNavigateResult(-1)}
                className="p-1.5 md:p-2 text-white hover:bg-white hover:bg-opacity-20 rounded transition"
                title="上一张"
              >
                <ChevronLeft className="h-4 w-4 md:h-5 md:w-5" />
              </button>
              <span className="text-white text-xs md:text-sm px-2">
                {currentResultIndex + 1}/{resultUrls.length}
              </span>
              <button
                onClick={() => handleNavigateResult(1)}
                className="p-1.5 md:p-2 text-white hover:bg-white hover:bg-opacity-20 rounded transition"
                title="下一张"
              >
                <ChevronRight className="h-4 w-4 md:h-5 md:w-5" />
              </button>
            </div>
          )}
            
            <button
              onClick={handleZoomOut}
              className="p-1.5 md:p-2 text-white hover:bg-white hover:bg-opacity-20 rounded transition"
              title="缩小"
            >
              <ZoomOut className="h-4 w-4 md:h-5 md:w-5" />
            </button>
            <span className="text-white text-xs md:text-sm min-w-[2.5rem] md:min-w-[3rem] text-center">
              {Math.round(scale * 100)}%
            </span>
            <button
              onClick={handleZoomIn}
              className="p-1.5 md:p-2 text-white hover:bg-white hover:bg-opacity-20 rounded transition"
              title="放大"
            >
              <ZoomIn className="h-4 w-4 md:h-5 md:w-5" />
            </button>
            <button
              onClick={handleRotate}
              className="p-1.5 md:p-2 text-white hover:bg-white hover:bg-opacity-20 rounded transition"
              title="旋转"
            >
              <RotateCw className="h-4 w-4 md:h-5 md:w-5" />
            </button>
            <button
              onClick={handleReset}
              className="p-1.5 md:p-2 text-white hover:bg-white hover:bg-opacity-20 rounded transition text-xs md:text-sm"
              title="重置"
            >
              重置
            </button>
            
            {/* 下载按钮 */}
            {hasMultipleResults && !showOriginal ? (
              <div className="flex items-center space-x-1">
                <button
                  onClick={() => currentImage && handleDownload(currentImage.url, currentImage.filename)}
                  className="p-1.5 md:p-2 text-white hover:bg-white hover:bg-opacity-20 rounded transition"
                  title="下载当前图片"
                >
                  <Download className="h-4 w-4 md:h-5 md:w-5" />
                </button>
                <button
                  onClick={handleDownloadAll}
                  className="px-2 py-1.5 md:px-3 md:py-2 text-white hover:bg-white hover:bg-opacity-20 rounded transition text-xs md:text-sm"
                  title="下载全部"
                >
                  全部
                </button>
              </div>
            ) : (
              <button
                onClick={() => currentImage && handleDownload(currentImage.url, currentImage.filename)}
                className="p-1.5 md:p-2 text-white hover:bg-white hover:bg-opacity-20 rounded transition"
                title="下载"
              >
                <Download className="h-4 w-4 md:h-5 md:w-5" />
              </button>
            )}
            
            <button
              onClick={onClose}
              className="p-1.5 md:p-2 text-white hover:bg-white hover:bg-opacity-20 rounded transition"
              title="关闭"
            >
              <X className="h-4 w-4 md:h-5 md:w-5" />
            </button>
          </div>
        </div>

        {/* 图片显示区域 */}
        <div
          className="flex-1 relative flex items-center justify-center overflow-hidden p-2 md:p-0"
          onWheel={handleWheel}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          ref={imageContainerRef}
          style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
        >
          {currentImage && (
            <div className="relative">
              <div
                className="relative"
                style={{
                  transform: `translate(${position.x}px, ${position.y}px) scale(${scale}) rotate(${rotation}deg)`,
                  transition: isDragging ? 'none' : 'transform 0.2s ease-in-out',
                  transformOrigin: 'center',
                }}
              >
                {(() => {
                  const resolvedUrl = resolveFileUrl(currentImage.url);
                  console.log('ImagePreview: Displaying image', {
                    originalUrl: currentImage.url,
                    resolvedUrl,
                    filename: currentImage.filename,
                    isSvg: currentImage.filename.toLowerCase().includes('.svg') || currentImage.url.toLowerCase().includes('.svg')
                  });
                  
                  const isSvg =
                    currentImage.filename.toLowerCase().includes('.svg') ||
                    currentImage.url.toLowerCase().includes('.svg');

                  if (isSvg) {
                    console.log('ImagePreview: Detected SVG file, using <object>');
                    return (
                      <object
                        ref={objectRef}
                        data={resolvedUrl}
                        type="image/svg+xml"
                        className="w-full h-full"
                        style={{ maxWidth: '100%', maxHeight: '100%' }}
                        draggable={false}
                        onLoad={handleImageLoad}
                        onError={(e) => console.error('ImagePreview: SVG failed to load', e)}
                      >
                        <img
                          src={resolvedUrl}
                          alt={currentImage.filename}
                          className="max-w-full max-h-full object-contain"
                          draggable={false}
                          onDragStart={(e) => e.preventDefault()}
                          onError={(e) => console.error('ImagePreview: Fallback img also failed', e)}
                        />
                      </object>
                    );
                  }
                  
                  return (
                    <img
                      ref={imageRef}
                      src={resolvedUrl}
                      alt={currentImage.filename}
                      className="max-w-full max-h-full object-contain"
                      draggable={false}
                      onDragStart={(e) => e.preventDefault()}
                      onLoad={handleImageLoad}
                      onError={(e) => console.error('ImagePreview: Image failed to load', e)}
                    />
                  );
                })()}
                
                {/* 图片信息 */}
                <div className="absolute bottom-2 left-2 md:bottom-4 md:left-4 bg-black bg-opacity-70 text-white p-2 md:p-3 rounded-lg text-xs md:text-sm max-w-[80%] md:max-w-none">
                  <div className="space-y-0.5 md:space-y-1">
                    <div className="truncate">文件名: {currentImage.filename}</div>
                    <div>大小: {(currentImage.size / 1024 / 1024).toFixed(2)} MB</div>
                    {currentImage.dimensions && (
                      <div>
                        尺寸: {currentImage.dimensions.width} × {currentImage.dimensions.height}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {hasMultipleResults && !showOriginal && currentImage && (
            <>
              <button
                type="button"
                onClick={() => handleNavigateResult(-1)}
                className="absolute left-4 top-1/2 -translate-y-1/2 p-2 md:p-3 rounded-full bg-black bg-opacity-50 text-white hover:bg-opacity-80 transition"
                title="上一张"
              >
                <ChevronLeft className="h-5 w-5 md:h-6 md:w-6" />
              </button>
              <button
                type="button"
                onClick={() => handleNavigateResult(1)}
                className="absolute right-4 top-1/2 -translate-y-1/2 p-2 md:p-3 rounded-full bg-black bg-opacity-50 text-white hover:bg-opacity-80 transition"
                title="下一张"
              >
                <ChevronRight className="h-5 w-5 md:h-6 md:w-6" />
              </button>
            </>
          )}
        </div>

        {/* 底部信息栏 */}
        <div className="p-2 md:p-4 bg-black bg-opacity-50">
          <div className="flex flex-col md:flex-row md:items-center justify-between text-white text-xs md:text-sm gap-1 md:gap-0">
            <div className="flex flex-col md:flex-row md:items-center space-y-1 md:space-y-0 md:space-x-4">
              <span className="truncate">任务ID: {task.taskId}</span>
              <span>状态: {task.status === 'completed' ? '已完成' : task.status}</span>
              <span className="truncate">创建时间: {new Date(task.createdAt).toLocaleString('zh-CN')}</span>
            </div>
            {task.completedAt && (
              <span className="truncate">完成时间: {new Date(task.completedAt).toLocaleString('zh-CN')}</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ImagePreview;
