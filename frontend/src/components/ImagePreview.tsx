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
        <div className="flex items-center justify-between p-4 bg-black bg-opacity-50">
          <div className="flex items-center space-x-4">
            <h3 className="text-white font-medium">{task.typeName}</h3>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setShowOriginal(!showOriginal)}
                className={`px-3 py-1 rounded text-sm transition ${
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
                className={`px-3 py-1 rounded text-sm transition ${
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

          <div className="flex items-center space-x-2">
            <button
              onClick={handleZoomOut}
              className="p-2 text-white hover:bg-white hover:bg-opacity-20 rounded transition"
              title="缩小"
            >
              <ZoomOut className="h-5 w-5" />
            </button>
            <span className="text-white text-sm min-w-[3rem] text-center">
              {Math.round(scale * 100)}%
            </span>
            <button
              onClick={handleZoomIn}
              className="p-2 text-white hover:bg-white hover:bg-opacity-20 rounded transition"
              title="放大"
            >
              <ZoomIn className="h-5 w-5" />
            </button>
            <button
              onClick={handleRotate}
              className="p-2 text-white hover:bg-white hover:bg-opacity-20 rounded transition"
              title="旋转"
            >
              <RotateCw className="h-5 w-5" />
            </button>
            <button
              onClick={handleReset}
              className="p-2 text-white hover:bg-white hover:bg-opacity-20 rounded transition text-sm"
              title="重置"
            >
              重置
            </button>
            <button
              onClick={() => currentImage && handleDownload(currentImage.url, currentImage.filename)}
              className="p-2 text-white hover:bg-white hover:bg-opacity-20 rounded transition"
              title="下载"
            >
              <Download className="h-5 w-5" />
            </button>
            <button
              onClick={onClose}
              className="p-2 text-white hover:bg-white hover:bg-opacity-20 rounded transition"
              title="关闭"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* 图片显示区域 */}
        <div className="flex-1 flex items-center justify-center overflow-hidden">
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
              <div className="absolute bottom-4 left-4 bg-black bg-opacity-70 text-white p-3 rounded-lg text-sm">
                <div className="space-y-1">
                  <div>文件名: {currentImage.filename}</div>
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
        <div className="p-4 bg-black bg-opacity-50">
          <div className="flex items-center justify-between text-white text-sm">
            <div className="flex items-center space-x-4">
              <span>任务ID: {task.taskId}</span>
              <span>状态: {task.status === 'completed' ? '已完成' : task.status}</span>
              <span>创建时间: {new Date(task.createdAt).toLocaleString('zh-CN')}</span>
            </div>
            {task.completedAt && (
              <span>完成时间: {new Date(task.completedAt).toLocaleString('zh-CN')}</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ImagePreview;