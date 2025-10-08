'use client';

import React, { useState, useEffect } from 'react';
import {
  Download,
  Heart,
  Eye,
  Clock,
  CheckCircle,
  XCircle,
  Loader2,
  Filter,
  ChevronDown,
  Check,
  Square,
  Archive,
  X,
} from 'lucide-react';
import { HistoryTask, getHistoryTasks, getTaskDetail, downloadTaskFile } from '../lib/api';
import { resolveFileUrl } from '../lib/api';

interface HistoryListProps {
  accessToken: string;
  onTaskSelect?: (task: HistoryTask) => void;
  showBatchSelection?: boolean;
}

const HistoryList: React.FC<HistoryListProps> = ({ accessToken, onTaskSelect, showBatchSelection = false }) => {
  const [tasks, setTasks] = useState<HistoryTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [showFilters, setShowFilters] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [selectedTasks, setSelectedTasks] = useState<Set<string>>(new Set());
  const [selectAll, setSelectAll] = useState(false);
  const [showDownloadOptions, setShowDownloadOptions] = useState(false);
  const [selectedTaskForDownload, setSelectedTaskForDownload] = useState<HistoryTask | null>(null);

  const typeOptions = [
    { value: 'all', label: '全部类型' },
    { value: 'prompt_edit', label: 'AI用嘴改图' },
    { value: 'vectorize', label: 'AI矢量化(转SVG)' },
    { value: 'extract_pattern', label: 'AI提取花型' },
    { value: 'remove_watermark', label: 'AI智能去水印' },
    { value: 'denoise', label: 'AI布纹去噪' },
    { value: 'embroidery', label: 'AI毛线刺绣增强' },
  ];

  const statusOptions = [
    { value: 'all', label: '全部状态' },
    { value: 'completed', label: '已完成' },
    { value: 'failed', label: '失败' },
    { value: 'processing', label: '处理中' },
    { value: 'queued', label: '排队中' },
  ];

  const fetchTasks = async (pageNum = 1, reset = false) => {
    try {
      setLoading(true);
      const response = await getHistoryTasks(accessToken, {
        type: selectedType === 'all' ? undefined : selectedType,
        status: selectedStatus === 'all' ? undefined : selectedStatus,
        page: pageNum,
        limit: 10,
      });

      if (reset) {
        setTasks(response.data.tasks);
      } else {
        setTasks(prev => [...prev, ...response.data.tasks]);
      }

      setHasMore(pageNum < response.data.pagination.totalPages);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取历史记录失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setPage(1);
    fetchTasks(1, true);
  }, [selectedType, selectedStatus, accessToken]);

  const loadMore = () => {
    if (!loading && hasMore) {
      const nextPage = page + 1;
      setPage(nextPage);
      fetchTasks(nextPage, false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'processing':
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
      case 'queued':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return '已完成';
      case 'failed':
        return '失败';
      case 'processing':
        return '处理中';
      case 'queued':
        return '排队中';
      default:
        return status;
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const handleDownload = async (task: HistoryTask) => {
    if (!task.resultImage) return;

    // 如果任务已完成，显示下载选项
    if (task.status === 'completed') {
      setSelectedTaskForDownload(task);
      setShowDownloadOptions(true);
    } else {
      // 如果任务未完成，直接下载结果图片（如果存在）
      downloadResultImage(task);
    }
  };

  const downloadResultImage = async (task: HistoryTask) => {
    if (!task.resultImage) return;

    try {
      const response = await fetch(resolveFileUrl(task.resultImage.url));
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = task.resultImage.filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('下载失败:', err);
    }
  };

  const downloadOriginalImage = async (task: HistoryTask) => {
    try {
      const { blob, filename } = await downloadTaskFile(task.taskId, accessToken, 'original');
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('下载原图失败:', err);
    }
  };

  const downloadProcessedImage = async (task: HistoryTask) => {
    try {
      const { blob, filename } = await downloadTaskFile(task.taskId, accessToken, 'result');
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('下载处理后的图片失败:', err);
    }
  };

  const handleBatchDownload = async () => {
    if (selectedTasks.size === 0) return;
    
    const selectedTasksData = tasks.filter(task => selectedTasks.has(task.taskId) && task.resultImage);
    
    if (selectedTasksData.length === 0) {
      alert('没有可下载的图片');
      return;
    }

    try {
      // 创建一个临时目录来存储所有下载的文件
      for (const task of selectedTasksData) {
        if (task.resultImage) {
          const response = await fetch(resolveFileUrl(task.resultImage.url));
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = task.resultImage.filename;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);
          
          // 添加延迟以避免浏览器阻止多个下载
          await new Promise(resolve => setTimeout(resolve, 500));
        }
      }
    } catch (err) {
      console.error('批量下载失败:', err);
      alert('批量下载失败，请重试');
    }
  };

  const toggleTaskSelection = (taskId: string) => {
    const newSelectedTasks = new Set(selectedTasks);
    if (newSelectedTasks.has(taskId)) {
      newSelectedTasks.delete(taskId);
    } else {
      newSelectedTasks.add(taskId);
    }
    setSelectedTasks(newSelectedTasks);
    setSelectAll(newSelectedTasks.size === tasks.filter(task => task.resultImage).length);
  };

  const toggleSelectAll = () => {
    if (selectAll) {
      setSelectedTasks(new Set());
      setSelectAll(false);
    } else {
      const completedTasks = tasks.filter(task => task.resultImage);
      const newSelectedTasks = new Set(completedTasks.map(task => task.taskId));
      setSelectedTasks(newSelectedTasks);
      setSelectAll(true);
    }
  };

  if (error) {
    return (
      <div className="text-center py-8">
        <p className="text-red-500 text-sm">{error}</p>
        <button
          onClick={() => fetchTasks(1, true)}
          className="mt-2 text-blue-500 text-sm hover:text-blue-600"
        >
          重试
        </button>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* 批量操作栏 */}
      {showBatchSelection && (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <button
                onClick={toggleSelectAll}
                className="flex items-center space-x-2 text-sm text-blue-600 hover:text-blue-700"
              >
                {selectAll ? <Check className="h-4 w-4" /> : <Square className="h-4 w-4" />}
                <span>全选</span>
              </button>
              <span className="text-sm text-blue-600">
                已选择 {selectedTasks.size} 项
              </span>
            </div>
            <button
              onClick={handleBatchDownload}
              disabled={selectedTasks.size === 0}
              className={`flex items-center space-x-2 px-3 py-1 rounded text-sm font-medium transition-colors ${
                selectedTasks.size > 0
                  ? 'bg-blue-500 hover:bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
              }`}
            >
              <Archive className="h-4 w-4" />
              <span>批量下载</span>
            </button>
          </div>
        </div>
      )}

      {/* 筛选器 */}
      <div className="mb-4">
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center space-x-2 text-sm text-gray-600 hover:text-gray-900 transition mb-3"
        >
          <Filter className="h-4 w-4" />
          <span>筛选</span>
          <ChevronDown className={`h-4 w-4 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
        </button>

        {showFilters && (
          <div className="space-y-3 mb-4">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">类型</label>
              <select
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value)}
                className="w-full text-sm border border-gray-300 rounded-md px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {typeOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">状态</label>
              <select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                className="w-full text-sm border border-gray-300 rounded-md px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {statusOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        )}
      </div>

      {/* 任务列表 */}
      <div className="flex-1 overflow-y-auto space-y-3">
        {tasks.length === 0 && !loading ? (
          <div className="text-center text-gray-400 py-8">
            <p className="text-sm">暂无历史记录</p>
          </div>
        ) : (
          tasks.map((task) => (
            <div
              key={task.taskId}
              className={`bg-gray-50 rounded-lg p-3 hover:bg-gray-100 transition cursor-pointer ${
                showBatchSelection ? 'flex items-start space-x-3' : ''
              }`}
              onClick={() => !showBatchSelection && onTaskSelect?.(task)}
            >
              {showBatchSelection && (
                <div className="flex-shrink-0 mt-1">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleTaskSelection(task.taskId);
                    }}
                    className={`${
                      selectedTasks.has(task.taskId)
                        ? 'text-blue-500'
                        : 'text-gray-400 hover:text-gray-600'
                    } transition`}
                  >
                    {selectedTasks.has(task.taskId) ? (
                      <Check className="h-4 w-4" />
                    ) : (
                      <Square className="h-4 w-4" />
                    )}
                  </button>
                </div>
              )}
              <div className="flex items-start space-x-3">
                {/* 缩略图 */}
                <div className="flex-shrink-0">
                  <img
                    src={resolveFileUrl(task.originalImage.url)}
                    alt={task.originalImage.filename}
                    className="w-12 h-12 object-cover rounded border border-gray-200"
                  />
                </div>

                {/* 任务信息 */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <h4 className="text-sm font-medium text-gray-900 truncate">
                      {task.typeName}
                    </h4>
                    <div className="flex items-center space-x-1">
                      {getStatusIcon(task.status)}
                      <span className="text-xs text-gray-500">
                        {getStatusText(task.status)}
                      </span>
                    </div>
                  </div>

                  <p className="text-xs text-gray-500 mb-2">
                    {formatDate(task.createdAt)}
                  </p>

                  {task.resultImage && (
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Eye className="h-3 w-3 text-gray-400" />
                        <span className="text-xs text-gray-500">
                          {task.resultImage.dimensions 
                            ? `${task.resultImage.dimensions.width}×${task.resultImage.dimensions.height}`
                            : '已处理'
                          }
                        </span>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          if (showBatchSelection) {
                            toggleTaskSelection(task.taskId);
                          } else {
                            handleDownload(task);
                          }
                        }}
                        className="text-blue-500 hover:text-blue-600 transition"
                      >
                        <Download className="h-4 w-4" />
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}

        {loading && (
          <div className="text-center py-4">
            <Loader2 className="h-6 w-6 animate-spin mx-auto text-gray-400" />
            <p className="text-xs text-gray-500 mt-1">加载中...</p>
          </div>
        )}

        {!loading && hasMore && tasks.length > 0 && (
          <button
            onClick={loadMore}
            className="w-full py-2 text-center text-sm text-blue-500 hover:text-blue-600 transition"
          >
            加载更多
          </button>
        )}
      </div>

      {/* 下载选项弹窗 */}
      {showDownloadOptions && selectedTaskForDownload && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-sm w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">选择下载内容</h3>
              <button
                onClick={() => setShowDownloadOptions(false)}
                className="text-gray-400 hover:text-gray-500"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="space-y-3">
              <button
                onClick={() => {
                  downloadOriginalImage(selectedTaskForDownload);
                  setShowDownloadOptions(false);
                }}
                className="w-full flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition"
              >
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <Download className="h-5 w-5 text-blue-600" />
                  </div>
                  <div className="text-left">
                    <p className="text-sm font-medium text-gray-900">下载原图</p>
                    <p className="text-xs text-gray-500">下载未经处理的原始图片</p>
                  </div>
                </div>
              </button>
              
              <button
                onClick={() => {
                  downloadProcessedImage(selectedTaskForDownload);
                  setShowDownloadOptions(false);
                }}
                className="w-full flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition"
              >
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                    <Download className="h-5 w-5 text-green-600" />
                  </div>
                  <div className="text-left">
                    <p className="text-sm font-medium text-gray-900">下载处理后的图</p>
                    <p className="text-xs text-gray-500">下载经过AI处理的图片</p>
                  </div>
                </div>
              </button>
            </div>
            
            <div className="mt-4 flex justify-end">
              <button
                onClick={() => setShowDownloadOptions(false)}
                className="px-4 py-2 text-sm text-gray-700 hover:text-gray-900 transition"
              >
                取消
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HistoryList;
