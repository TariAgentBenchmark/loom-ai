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
} from 'lucide-react';
import { HistoryTask, getHistoryTasks, getTaskDetail } from '../lib/api';
import { resolveFileUrl } from '../lib/api';

interface HistoryListProps {
  accessToken: string;
  onTaskSelect?: (task: HistoryTask) => void;
}

const HistoryList: React.FC<HistoryListProps> = ({ accessToken, onTaskSelect }) => {
  const [tasks, setTasks] = useState<HistoryTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [showFilters, setShowFilters] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

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
              className="bg-gray-50 rounded-lg p-3 hover:bg-gray-100 transition cursor-pointer"
              onClick={() => onTaskSelect?.(task)}
            >
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
                          handleDownload(task);
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
    </div>
  );
};

export default HistoryList;
