'use client';

import { useState, useEffect, useCallback } from 'react';
import { getBatchStatus, downloadBatchResults, BatchTaskStatus } from '../lib/api';

interface BatchProcessingStatusProps {
    batchId: string;
    accessToken: string;
    onComplete: () => void;
    onBack: () => void;
}

const POLLING_INTERVAL = 3000; // 3 seconds

export default function BatchProcessingStatus({
    batchId,
    accessToken,
    onComplete,
    onBack,
}: BatchProcessingStatusProps) {
    const [status, setStatus] = useState<BatchTaskStatus | null>(null);
    const [error, setError] = useState<string>('');
    const [isDownloading, setIsDownloading] = useState(false);

    const fetchStatus = useCallback(async () => {
        try {
            const response = await getBatchStatus(batchId, accessToken);
            setStatus(response.data);

            // Check if batch is complete
            if (response.data.status === 'completed' || response.data.status === 'partial' || response.data.status === 'failed') {
                onComplete();
            }
        } catch (err) {
            setError((err as Error)?.message ?? '获取批量任务状态失败');
        }
    }, [batchId, accessToken, onComplete]);

    useEffect(() => {
        // Initial fetch
        fetchStatus();

        // Set up polling
        const interval = setInterval(fetchStatus, POLLING_INTERVAL);

        return () => {
            clearInterval(interval);
        };
    }, [fetchStatus]);

    const handleDownload = useCallback(async () => {
        if (!status) return;

        setIsDownloading(true);
        setError('');

        try {
            const result = await downloadBatchResults(batchId, accessToken);

            // Create download link
            const url = window.URL.createObjectURL(result.blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = result.filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (err) {
            setError((err as Error)?.message ?? '下载失败');
        } finally {
            setIsDownloading(false);
        }
    }, [batchId, accessToken, status]);

    const getStatusIcon = (taskStatus: string) => {
        switch (taskStatus) {
            case 'completed':
                return (
                    <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                );
            case 'failed':
                return (
                    <svg className="w-5 h-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                );
            case 'processing':
                return (
                    <svg className="w-5 h-5 text-blue-500 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                );
            default:
                return (
                    <svg className="w-5 h-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                    </svg>
                );
        }
    };

    const getStatusText = (batchStatus: string) => {
        switch (batchStatus) {
            case 'queued':
                return '排队中';
            case 'processing':
                return '处理中';
            case 'completed':
                return '全部完成';
            case 'partial':
                return '部分完成';
            case 'failed':
                return '处理失败';
            default:
                return batchStatus;
        }
    };

    if (!status) {
        return (
            <div className="flex items-center justify-center p-12">
                <div className="text-center">
                    <svg className="w-12 h-12 text-blue-500 animate-spin mx-auto" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <p className="mt-4 text-gray-600">加载批量任务状态...</p>
                </div>
            </div>
        );
    }

    const isComplete = status.status === 'completed' || status.status === 'partial';
    const hasResults = status.completedImages > 0;

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <button
                    onClick={onBack}
                    className="flex items-center text-gray-600 hover:text-gray-800"
                >
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                    返回
                </button>
                <div className="text-right">
                    <p className="text-sm text-gray-500">批量任务 ID</p>
                    <p className="text-xs text-gray-400 font-mono">{batchId}</p>
                </div>
            </div>

            {/* Overall Status */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-semibold">批量处理状态</h3>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${status.status === 'completed' ? 'bg-green-100 text-green-800' :
                        status.status === 'partial' ? 'bg-yellow-100 text-yellow-800' :
                            status.status === 'failed' ? 'bg-red-100 text-red-800' :
                                'bg-blue-100 text-blue-800'
                        }`}>
                        {getStatusText(status.status)}
                    </span>
                </div>

                {/* Progress Bar */}
                <div className="mb-4">
                    <div className="flex justify-between text-sm text-gray-600 mb-2">
                        <span>进度</span>
                        <span>{status.completedImages + status.failedImages} / {status.totalImages}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                        <div
                            className={`h-3 rounded-full transition-all duration-300 ${status.failedImages > 0 ? 'bg-yellow-500' : 'bg-blue-600'
                                }`}
                            style={{ width: `${status.progress}%` }}
                        />
                    </div>
                </div>

                {/* Statistics */}
                <div className="grid grid-cols-3 gap-4 text-center">
                    <div className="p-3 bg-green-50 rounded-lg">
                        <p className="text-2xl font-bold text-green-600">{status.completedImages}</p>
                        <p className="text-sm text-gray-600">已完成</p>
                    </div>
                    <div className="p-3 bg-red-50 rounded-lg">
                        <p className="text-2xl font-bold text-red-600">{status.failedImages}</p>
                        <p className="text-sm text-gray-600">失败</p>
                    </div>
                    <div className="p-3 bg-gray-50 rounded-lg">
                        <p className="text-2xl font-bold text-gray-600">
                            {status.totalImages - status.completedImages - status.failedImages}
                        </p>
                        <p className="text-sm text-gray-600">待处理</p>
                    </div>
                </div>

                {/* Download Button */}
                {isComplete && hasResults && (
                    <div className="mt-6">
                        <button
                            onClick={handleDownload}
                            disabled={isDownloading}
                            className="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                        >
                            {isDownloading ? (
                                <>
                                    <svg className="w-5 h-5 mr-2 animate-spin" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                    下载中...
                                </>
                            ) : (
                                <>
                                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                    </svg>
                                    下载全部结果 (ZIP)
                                </>
                            )}
                        </button>
                    </div>
                )}
            </div>

            {/* Error Message */}
            {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <p className="text-red-600 text-sm">{error}</p>
                </div>
            )}

            {/* Individual Task List */}
            <div className="bg-white rounded-lg shadow-sm border">
                <div className="p-4 border-b">
                    <h4 className="font-semibold">图片处理详情</h4>
                </div>
                <div className="divide-y max-h-96 overflow-y-auto">
                    {status.tasks.map((task, index) => (
                        <div key={task.taskId} className="p-4 hover:bg-gray-50">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center flex-1 min-w-0">
                                    <div className="flex-shrink-0 mr-3">
                                        {getStatusIcon(task.status)}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium text-gray-900 truncate">
                                            {index + 1}. {task.filename}
                                        </p>
                                        {task.errorMessage && (
                                            <p className="text-xs text-red-500 mt-1">{task.errorMessage}</p>
                                        )}
                                    </div>
                                </div>
                                <div className="ml-4 flex-shrink-0">
                                    {task.status === 'completed' && task.resultUrl && (
                                        <a
                                            href={task.resultUrl}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-blue-600 hover:text-blue-700 text-sm"
                                        >
                                            查看结果
                                        </a>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
