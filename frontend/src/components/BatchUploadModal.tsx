'use client';

import { useState, useCallback, DragEvent, ChangeEvent, useRef } from 'react';

interface BatchUploadModalProps {
    isOpen: boolean;
    onClose: () => void;
    onStartBatch: (files: File[]) => void;
    maxFiles?: number;
    isProcessing?: boolean;
    serviceCredits?: number | null;
    isLoadingServiceCost?: boolean;
}

interface FileWithPreview {
    file: File;
    preview: string;
    id: string;
}

const formatCredits = (value: number) => {
    if (Number.isInteger(value)) {
        return value.toString();
    }

    const formatted = value.toFixed(2).replace(/\.00$/, '');
    return formatted.replace(/(\.\d*[1-9])0$/, '$1');
};

export default function BatchUploadModal({
    isOpen,
    onClose,
    onStartBatch,
    maxFiles = 10,
    isProcessing = false,
    serviceCredits = null,
    isLoadingServiceCost = false,
}: BatchUploadModalProps) {
    const [files, setFiles] = useState<FileWithPreview[]>([]);
    const [isDragging, setIsDragging] = useState(false);
    const [error, setError] = useState<string>('');
    const fileInputRef = useRef<HTMLInputElement>(null);

    const generatePreview = useCallback((file: File): Promise<string> => {
        return new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                resolve(e.target?.result as string);
            };
            reader.readAsDataURL(file);
        });
    }, []);

    const addFiles = useCallback(async (newFiles: File[]) => {
        setError('');

        // Validate file count
        const totalFiles = files.length + newFiles.length;
        if (totalFiles > maxFiles) {
            setError(`最多只能上传 ${maxFiles} 张图片`);
            return;
        }

        // Validate file types
        const validFiles = newFiles.filter(file => {
            if (!file.type.startsWith('image/')) {
                setError(`${file.name} 不是有效的图片文件`);
                return false;
            }
            return true;
        });

        // Generate previews and add to list
        const filesWithPreviews = await Promise.all(
            validFiles.map(async (file) => ({
                file,
                preview: await generatePreview(file),
                id: `${file.name}-${Date.now()}-${Math.random()}`,
            }))
        );

        setFiles(prev => [...prev, ...filesWithPreviews]);
    }, [files.length, maxFiles, generatePreview]);

    const handleDragOver = useCallback((e: DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e: DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        setIsDragging(false);
    }, []);

    const handleDrop = useCallback(async (e: DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        setIsDragging(false);

        const droppedFiles = Array.from(e.dataTransfer.files);
        await addFiles(droppedFiles);
    }, [addFiles]);

    const handleFileInput = useCallback(async (e: ChangeEvent<HTMLInputElement>) => {
        const selectedFiles = e.target.files ? Array.from(e.target.files) : [];
        await addFiles(selectedFiles);

        // Reset input
        if (e.target) {
            e.target.value = '';
        }
    }, [addFiles]);

    const removeFile = useCallback((id: string) => {
        setFiles(prev => prev.filter(f => f.id !== id));
        setError('');
    }, []);

    const handleStartBatch = useCallback(() => {
        if (files.length === 0) {
            setError('请至少上传一张图片');
            return;
        }
        onStartBatch(files.map(f => f.file));
    }, [files, onStartBatch]);

    const handleClose = useCallback(() => {
        if (!isProcessing) {
            setFiles([]);
            setError('');
            onClose();
        }
    }, [isProcessing, onClose]);

    const estimatedCredits = serviceCredits !== null ? serviceCredits * files.length : null;

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
            <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] flex flex-col">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b">
                    <h2 className="text-2xl font-bold">批量上传图片</h2>
                    <button
                        onClick={handleClose}
                        disabled={isProcessing}
                        className="text-gray-500 hover:text-gray-700 disabled:opacity-50"
                    >
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6">
                    {/* Upload Zone */}
                    <div
                        onDragOver={handleDragOver}
                        onDragLeave={handleDragLeave}
                        onDrop={handleDrop}
                        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${isDragging
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-300 hover:border-gray-400'
                            }`}
                    >
                        <input
                            ref={fileInputRef}
                            type="file"
                            multiple
                            accept="image/*"
                            onChange={handleFileInput}
                            className="hidden"
                            disabled={isProcessing}
                        />

                        <svg
                            className="mx-auto h-12 w-12 text-gray-400"
                            stroke="currentColor"
                            fill="none"
                            viewBox="0 0 48 48"
                        >
                            <path
                                d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                                strokeWidth={2}
                                strokeLinecap="round"
                                strokeLinejoin="round"
                            />
                        </svg>

                        <p className="mt-4 text-lg text-gray-600">
                            拖拽图片到此处，或
                            <button
                                onClick={() => fileInputRef.current?.click()}
                                disabled={isProcessing}
                                className="text-blue-600 hover:text-blue-700 font-medium ml-1 disabled:opacity-50"
                            >
                                点击选择
                            </button>
                        </p>
                        <p className="mt-2 text-sm text-gray-500">
                            支持 JPG、PNG 等格式，最多 {maxFiles} 张图片
                        </p>
                    </div>

                    {/* Error Message */}
                    {error && (
                        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                            <p className="text-red-600 text-sm">{error}</p>
                        </div>
                    )}

                    {/* File List */}
                    {files.length > 0 && (
                        <div className="mt-6">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-lg font-semibold">
                                    已选择 {files.length} 张图片
                                </h3>
                                <button
                                    onClick={() => setFiles([])}
                                    disabled={isProcessing}
                                    className="text-sm text-red-600 hover:text-red-700 disabled:opacity-50"
                                >
                                    清空全部
                                </button>
                            </div>

                            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
                                {files.map((fileWithPreview) => (
                                    <div
                                        key={fileWithPreview.id}
                                        className="relative group border rounded-lg overflow-hidden"
                                    >
                                        <img
                                            src={fileWithPreview.preview}
                                            alt={fileWithPreview.file.name}
                                            className="w-full h-32 object-cover"
                                        />
                                        <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-50 transition-opacity flex items-center justify-center">
                                            <button
                                                onClick={() => removeFile(fileWithPreview.id)}
                                                disabled={isProcessing}
                                                className="opacity-0 group-hover:opacity-100 bg-red-600 text-white rounded-full p-2 hover:bg-red-700 transition-opacity disabled:opacity-50"
                                            >
                                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                                </svg>
                                            </button>
                                        </div>
                                        <div className="p-2 bg-gray-50">
                                            <p className="text-xs text-gray-600 truncate">
                                                {fileWithPreview.file.name}
                                            </p>
                                            <p className="text-xs text-gray-400">
                                                {(fileWithPreview.file.size / 1024 / 1024).toFixed(2)} MB
                                            </p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 p-6 border-t bg-gray-50">
                    <div className="space-y-1">
                        <p className="text-sm text-gray-600">
                            {files.length > 0 ? `共 ${files.length} 张图片` : '还未选择图片'}
                        </p>
                        <p className="text-sm text-blue-700">
                            {isLoadingServiceCost
                                ? '价格加载中…'
                                : serviceCredits === null
                                    ? '价格暂不可用，预计积分无法计算'
                                    : files.length > 0
                                        ? `单张 ${formatCredits(serviceCredits ?? 0)} 积分，预计消耗 ${formatCredits(estimatedCredits ?? 0)} 积分`
                                        : `单张 ${formatCredits(serviceCredits ?? 0)} 积分`}
                        </p>
                    </div>
                    <div className="flex gap-3">
                        <button
                            onClick={handleClose}
                            disabled={isProcessing}
                            className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-100 disabled:opacity-50"
                        >
                            取消
                        </button>
                        <button
                            onClick={handleStartBatch}
                            disabled={files.length === 0 || isProcessing}
                            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {isProcessing ? '处理中...' : '开始批量处理'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
