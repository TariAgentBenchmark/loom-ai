'use client';

import React, { useState } from 'react';
import { X, Download, ZoomIn, ZoomOut, RotateCw } from 'lucide-react';
import { HistoryTask } from '../lib/api';
import { resolveFileUrl } from '../lib/api';

interface ImagePreviewProps {
  task: HistoryTask | null;
  onClose: () => void;
  accessToken: string;
}

const ImagePreview: React.FC<ImagePreviewProps> = ({ task, onClose, accessToken }) => {
  const [scale, setScale] = useState(1);
  const [rotation, setRotation] = useState(0);
  const [showOriginal, setShowOriginal] = useState(true);

  if (!task) return null;

  const handleDownload = async (imageUrl: string, filename: string) => {
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
  };

  const handleZoomIn = () => {
    setScale(prev => Math.min(prev + 0.25, 3));
  };

  const handleZoomOut = () => {
    setScale(prev => Math.max(prev - 0.25, 0.5));
  };

  const handleRotate = () => {
    setRotation(prev => (prev + 90) % 360);
  };

  const handleReset = () => {
    setScale(1);
    setRotation(0);
  };

  const currentImage = showOriginal ? task.originalImage : task.resultImage;
  const hasResultImage = !!task.resultImage;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-90 z-50 flex items-center justify-center">
      <div className="relative w-full h-full flex flex-col">
        {/* 顶部工具栏 */}
        <div className="flex flex-col md:flex-row md:items-center justify-between p-3 md:p-4 bg-black bg-opacity-50 gap-2">
          <div className="flex items-center space-x-2 md:space-x-4">
            <h3 className="text-white text-sm md:font-medium truncate max-w-[120px] md:max-w-none">{task.typeName}</h3>
            <div className="flex items-center space-x-1 md:space-x-2">
              <button
                onClick={() => setShowOriginal(!showOriginal)}
                className={`px-2 py-1 md:px-3 rounded text-xs md:text-sm transition ${
                  showOriginal
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-600 text-gray-300 hover:bg-gray-500'
                }`}
                disabled={!hasResultImage}
              >
                原图
              </button>
              <button
                onClick={() => setShowOriginal(!showOriginal)}
                className={`px-2 py-1 md:px-3 rounded text-xs md:text-sm transition ${
                  !showOriginal
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-600 text-gray-300 hover:bg-gray-500'
                }`}
                disabled={!hasResultImage}
              >
                结果
              </button>
            </div>
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
              onClick={() => currentImage && handleDownload(currentImage.url, currentImage.filename)}
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
        <div className="flex-1 flex items-center justify-center overflow-hidden p-2 md:p-0">
          {currentImage && (
            <div
              className="relative"
              style={{
                transform: `scale(${scale}) rotate(${rotation}deg)`,
                transition: 'transform 0.2s ease-in-out',
              }}
            >
              <img
                src={resolveFileUrl(currentImage.url)}
                alt={currentImage.filename}
                className="max-w-full max-h-full object-contain"
                draggable={false}
              />
              
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