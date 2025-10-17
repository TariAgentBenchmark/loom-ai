'use client';

import React, { useState, useRef, useCallback, useEffect } from 'react';
import { X, Download, ZoomIn, ZoomOut, RotateCw } from 'lucide-react';
import { resolveFileUrl } from '../lib/api';

interface ProcessedImagePreviewProps {
  image: {
    url: string;
    filename: string;
  } | null;
  onClose: () => void;
}

const ProcessedImagePreview: React.FC<ProcessedImagePreviewProps> = ({ image, onClose }) => {
  const [scale, setScale] = useState(1);
  const [initialScale, setInitialScale] = useState(1);
  const [rotation, setRotation] = useState(0);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const imageContainerRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);

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

  const handleDownload = useCallback(async () => {
    try {
      const response = await fetch(resolveFileUrl(image.url));
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = image.filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('下载失败:', err);
    }
  }, [image?.url, image?.filename]);

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
    if (!container || !img || !img.naturalWidth || !img.naturalHeight) {
      return;
    }

    const widthScale = container.clientWidth / img.naturalWidth;
    const heightScale = container.clientHeight / img.naturalHeight;
    const nextScale = Math.min(widthScale, heightScale, 1);
    const safeScale = nextScale > 0 && Number.isFinite(nextScale) ? nextScale : 1;

    setInitialScale(safeScale);
    setScale(safeScale);
    setPosition({ x: 0, y: 0 });
    setRotation(0);
  }, []);

  useEffect(() => {
    if (!image) {
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
  }, [handleImageLoad, image, initialScale]);

  if (!image) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-90 z-50 flex items-center justify-center">
      <div className="relative w-full h-full flex flex-col">
        {/* 顶部工具栏 */}
        <div className="flex items-center justify-between p-3 md:p-4 bg-black bg-opacity-50">
          <div className="flex items-center space-x-2 md:space-x-4">
            <h3 className="text-white text-sm md:font-medium truncate max-w-[200px] md:max-w-none">
              {image.filename}
            </h3>
          </div>

          <div className="flex items-center space-x-1 md:space-x-2">
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

            <button
              onClick={handleDownload}
              className="p-1.5 md:p-2 text-white hover:bg-white hover:bg-opacity-20 rounded transition"
              title="下载"
            >
              <Download className="h-4 w-4 md:h-5 md:w-5" />
            </button>

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
          className="flex-1 flex items-center justify-center overflow-hidden p-2 md:p-0"
          onWheel={handleWheel}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          ref={imageContainerRef}
          style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
        >
          <div
            className="relative"
            style={{
              transform: `translate(${position.x}px, ${position.y}px) scale(${scale}) rotate(${rotation}deg)`,
              transition: isDragging ? 'none' : 'transform 0.2s ease-in-out',
              transformOrigin: 'center',
            }}
          >
            <img
              ref={imageRef}
              src={resolveFileUrl(image.url)}
              alt={image.filename}
              className="max-w-full max-h-full object-contain"
              draggable={false}
              onDragStart={(e) => e.preventDefault()}
              onLoad={handleImageLoad}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProcessedImagePreview;