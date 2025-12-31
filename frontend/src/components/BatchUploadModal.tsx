'use client';

import { useState, useCallback, DragEvent, ChangeEvent, useRef } from 'react';
import { ProcessingMethod } from '../lib/processing';
import ExpandEdgeControls from './ExpandEdgeControls';

interface BatchUploadModalProps {
    isOpen: boolean;
    onClose: () => void;
    onStartBatch: (files: File[], referenceImage: File | null) => void;
    maxFiles?: number;
    isProcessing?: boolean;
    serviceCredits?: number | null;
    isLoadingServiceCost?: boolean;
    showReferenceImage?: boolean;  // 是否显示基准图上传（仅用于 prompt_edit）
    instruction?: string; // prompt_edit 的修改指令
    onInstructionChange?: (value: string) => void;
    patternType?: string;
    onPatternTypeChange?: (value: string) => void;
    denimAspectRatio?: string;
    onDenimAspectRatioChange?: (value: string) => void;
    maxFileSizeMB?: number; // 单文件大小上限（可选）
    method: ProcessingMethod;
    expandRatio?: string;
    onExpandRatioChange?: (value: string) => void;
    expandEdges?: { top: string; bottom: string; left: string; right: string };
    onExpandEdgeChange?: (key: 'top' | 'bottom' | 'left' | 'right', value: string) => void;
    expandPrompt?: string;
    onExpandPromptChange?: (value: string) => void;
    seamDirection?: number;
    onSeamDirectionChange?: (value: number) => void;
    seamFit?: number;
    onSeamFitChange?: (value: number) => void;
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
    showReferenceImage = false,
    instruction,
    onInstructionChange,
    patternType,
    onPatternTypeChange,
    denimAspectRatio,
    onDenimAspectRatioChange,
    maxFileSizeMB,
    method,
    expandRatio,
    onExpandRatioChange,
    expandEdges,
    onExpandEdgeChange,
    expandPrompt,
    onExpandPromptChange,
    seamDirection,
    onSeamDirectionChange,
    seamFit,
    onSeamFitChange,
}: BatchUploadModalProps) {
    const [files, setFiles] = useState<FileWithPreview[]>([]);
    const [referenceImage, setReferenceImage] = useState<FileWithPreview | null>(null);
    const [isDragging, setIsDragging] = useState(false);
    const [error, setError] = useState<string>('');
    const fileInputRef = useRef<HTMLInputElement>(null);
    const referenceInputRef = useRef<HTMLInputElement>(null);
    const patternTypeOptions: { value: string; label: string }[] = [
        { value: 'combined', label: '综合模型' },
        { value: 'general', label: '通用模型' },
        { value: 'denim', label: '牛仔风格专用' },
    ];
    const denimSizeOptions: { value: string; label: string }[] = [
        { value: '1:1', label: '方形 1:1' },
        { value: '2:3', label: '竖版 2:3' },
        { value: '3:2', label: '横版 3:2' },
    ];
    const effectivePatternType = patternType ?? 'combined';
    const effectiveDenimAspectRatio = denimAspectRatio ?? '1:1';

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

        const sizeLimitBytes = maxFileSizeMB ? maxFileSizeMB * 1024 * 1024 : null;

        // Validate file types and size
        const validFiles = newFiles.filter(file => {
            if (!file.type.startsWith('image/')) {
                setError(`${file.name} 不是有效的图片文件`);
                return false;
            }
            if (sizeLimitBytes && file.size > sizeLimitBytes) {
                setError(`${file.name} 超过大小限制（最大 ${maxFileSizeMB}MB）`);
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
    }, [files.length, maxFiles, maxFileSizeMB, generatePreview]);

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

    const handleReferenceImageInput = useCallback(async (e: ChangeEvent<HTMLInputElement>) => {
        const selectedFile = e.target.files?.[0];
        if (!selectedFile) return;

        setError('');

        // Validate file type
        if (!selectedFile.type.startsWith('image/')) {
            setError(`${selectedFile.name} 不是有效的图片文件`);
            return;
        }

        // Generate preview
        const preview = await generatePreview(selectedFile);
        setReferenceImage({
            file: selectedFile,
            preview,
            id: `reference-${Date.now()}`,
        });

        // Reset input
        if (e.target) {
            e.target.value = '';
        }
    }, [generatePreview]);

    const removeReferenceImage = useCallback(() => {
        setReferenceImage(null);
        setError('');
    }, []);

    const handleStartBatch = useCallback(() => {
        if (files.length === 0) {
            setError('请至少上传一张图片');
            return;
        }
        if (showReferenceImage && !(instruction ?? '').trim()) {
            setError('请填写修改指令');
            return;
        }
        onStartBatch(files.map(f => f.file), referenceImage?.file || null);
    }, [files, referenceImage, onStartBatch, showReferenceImage, instruction]);

    const handleClose = useCallback(() => {
        if (!isProcessing) {
            setFiles([]);
            setReferenceImage(null);
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
                    {/* Reference Image Upload (仅用于 prompt_edit) */}
                    {showReferenceImage && (
                        <div className="mb-6">
                            <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                                <span>参考图（可选）</span>
                                <span className="text-red-500 text-sm font-semibold">图2</span>
                            </h3>
                            <p className="text-sm text-gray-600 mb-3">
                                上传一张参考图，将与每张批量图片组合处理
                            </p>

                            {referenceImage ? (
                                <div className="relative border-2 border-blue-500 rounded-lg overflow-hidden">
                                    <img
                                        src={referenceImage.preview}
                                        alt="参考图"
                                        className="w-full h-48 object-cover"
                                    />
                                    <div className="absolute inset-0 bg-black bg-opacity-0 hover:bg-opacity-50 transition-opacity flex items-center justify-center group">
                                        <button
                                            onClick={removeReferenceImage}
                                            disabled={isProcessing}
                                            className="opacity-0 group-hover:opacity-100 bg-red-600 text-white rounded-full p-3 hover:bg-red-700 transition-opacity disabled:opacity-50"
                                        >
                                            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                            </svg>
                                        </button>
                                    </div>
                                    <div className="p-3 bg-blue-50 border-t border-blue-200">
                                        <p className="text-sm text-gray-700 font-medium truncate">
                                            {referenceImage.file.name}
                                        </p>
                                        <p className="text-xs text-gray-500">
                                            {(referenceImage.file.size / 1024 / 1024).toFixed(2)} MB
                                        </p>
                                    </div>
                                </div>
                            ) : (
                                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-gray-400 transition-colors">
                                    <input
                                        ref={referenceInputRef}
                                        type="file"
                                        accept="image/*"
                                        onChange={handleReferenceImageInput}
                                        className="hidden"
                                        disabled={isProcessing}
                                    />
                                    <svg
                                        className="mx-auto h-10 w-10 text-gray-400"
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
                                    <p className="mt-3 text-sm text-gray-600">
                                        <button
                                            onClick={() => referenceInputRef.current?.click()}
                                            disabled={isProcessing}
                                            className="text-blue-600 hover:text-blue-700 font-medium disabled:opacity-50"
                                        >
                                            点击上传参考图（对应图片2）
                                        </button>
                                    </p>
                                </div>
                            )}
                        </div>
                    )}

                    {method === 'extract_pattern' && (
                        <div className="mb-6 space-y-4">
                            <div>
                                <h3 className="text-sm md:text-base font-semibold text-gray-900 mb-2">模型</h3>
                                <div className="grid grid-cols-2 gap-3">
                                    {patternTypeOptions.map((option) => {
                                        const isActive = effectivePatternType === option.value;
                                        return (
                                            <button
                                                key={option.value}
                                                type="button"
                                                onClick={() => onPatternTypeChange?.(option.value)}
                                                disabled={isProcessing}
                                                className={`flex flex-col items-start gap-1 rounded-xl border p-3 text-left transition-all ${isActive
                                                    ? 'border-blue-500 bg-blue-50 shadow-sm'
                                                    : 'border-gray-200 hover:border-blue-300 hover:bg-blue-50/60'
                                                    }`}
                                            >
                                                <span className="text-sm md:text-base font-semibold text-gray-900">
                                                    {option.label}
                                                </span>
                                            </button>
                                        );
                                    })}
                                </div>
                            </div>
                            {effectivePatternType === 'denim' && (
                                <div className="space-y-4">
                                    <div>
                                        <h4 className="text-sm md:text-base font-semibold text-gray-900 mb-2">图片尺寸</h4>
                                        <div className="grid grid-cols-3 gap-2">
                                            {denimSizeOptions.map((option) => {
                                                const isActive =
                                                    effectiveDenimAspectRatio === option.value;
                                                return (
                                                    <button
                                                        key={option.value}
                                                        type="button"
                                                        onClick={() =>
                                                            onDenimAspectRatioChange?.(option.value)
                                                        }
                                                        disabled={isProcessing}
                                                        className={`rounded-lg border px-3 py-2 text-xs md:text-sm font-medium transition ${isActive
                                                            ? 'border-blue-500 bg-blue-50 text-blue-600 shadow-sm'
                                                            : 'border-gray-200 text-gray-600 hover:border-blue-300 hover:bg-blue-50/60'
                                                            }`}
                                                    >
                                                        {option.label}
                                                    </button>
                                                );
                                            })}
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Upload Zone */}
                    <div>
                        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                            <span>批量图片</span>
                            {method === 'prompt_edit' && (
                                <span className="text-red-500 text-sm font-semibold">图1</span>
                            )}
                            </h3>
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

                    {/* Expand image options */}
                    {method === 'expand_image' && (
                        <div className="mt-6">
                            <ExpandEdgeControls
                                expandRatio={expandRatio}
                                onExpandRatioChange={onExpandRatioChange}
                                expandEdges={expandEdges}
                                onExpandEdgeChange={onExpandEdgeChange}
                                expandPrompt={expandPrompt}
                                onExpandPromptChange={onExpandPromptChange}
                                isProcessing={isProcessing}
                            />
                        </div>
                    )}

                    {/* Seamless loop options */}
                    {method === 'seamless_loop' && (
                        <div className="mt-6 space-y-4">
                            <div>
                                <h4 className="text-md font-semibold text-gray-900 mb-2">接缝方向</h4>
                                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                                    {[
                                        { value: 0, label: '四周拼接' },
                                        { value: 1, label: '上下拼接' },
                                        { value: 2, label: '左右拼接' },
                                    ].map((item) => (
                                        <button
                                            key={item.value}
                                            type="button"
                                            onClick={() => onSeamDirectionChange?.(item.value)}
                                            disabled={isProcessing}
                                            className={`w-full rounded-lg border px-3 py-2 text-sm font-medium transition ${seamDirection === item.value
                                                ? 'border-blue-500 bg-blue-50 text-blue-600'
                                                : 'border-gray-200 text-gray-700 hover:border-blue-300 hover:bg-blue-50/60'
                                                }`}
                                        >
                                            {item.label}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Instruction for prompt_edit - bottom */}
                    {showReferenceImage && (
                        <div className="mt-6">
                            <h3 className="text-lg font-semibold mb-2">输入指令</h3>
                            <p className="text-sm text-gray-600 mb-3">
                                请输入希望修改的描述，将应用于所有批量图片
                            </p>
                            <textarea
                                value={instruction ?? ''}
                                onChange={(event) =>
                                    onInstructionChange?.(event.target.value)
                                }
                                placeholder="例如：把图中裙子的颜色改成白色"
                                className="w-full min-h-[100px] rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-400 resize-none"
                                disabled={isProcessing}
                            />
                            <p className="text-xs text-gray-500 mt-2">
                                一句话描述想要修改的细节，AI 会自动处理。批量任务会使用这里的指令。
                            </p>
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
