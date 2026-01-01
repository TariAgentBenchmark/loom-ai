'use client';

import { useState, useCallback, useEffect } from 'react';
import { ProcessingMethod, resolvePricingServiceKey } from '../lib/processing';
import {
    createBatchTask,
    BatchProcessingRequestPayload,
    getPublicServicePrices,
    getServiceCost,
} from '../lib/api';
import BatchUploadModal from './BatchUploadModal';
import BatchProcessingStatus from './BatchProcessingStatus';

interface BatchProcessingWrapperProps {
    method: ProcessingMethod;
    accessToken: string;
    onBack: () => void;
    onHistoryRefresh?: () => void;
    promptInstruction?: string;
    patternType?: string;
    onPatternTypeChange?: (value: string) => void;
    denimAspectRatio?: string;
    onDenimAspectRatioChange?: (value: string) => void;
    denimImageCount?: number;
    upscaleEngine?: 'meitu_v2' | 'runninghub_vr2';
    expandRatio?: string;
    expandEdges?: { top: string; bottom: string; left: string; right: string };
    expandPrompt?: string;
    onExpandRatioChange?: (value: string) => void;
    onExpandEdgeChange?: (key: 'top' | 'bottom' | 'left' | 'right', value: string) => void;
    onExpandPromptChange?: (value: string) => void;
    seamDirection?: number;
    seamFit?: number;
    onSeamDirectionChange?: (value: number) => void;
    onSeamFitChange?: (value: number) => void;
}

export default function BatchProcessingWrapper({
    method,
    accessToken,
    onBack,
    onHistoryRefresh,
    promptInstruction,
    patternType,
    onPatternTypeChange,
    denimAspectRatio,
    onDenimAspectRatioChange,
    denimImageCount,
    upscaleEngine,
    expandRatio,
    expandEdges,
    expandPrompt,
    onExpandRatioChange,
    onExpandEdgeChange,
    onExpandPromptChange,
    seamDirection,
    seamFit,
    onSeamDirectionChange,
    onSeamFitChange,
}: BatchProcessingWrapperProps) {
    const [showUploadModal, setShowUploadModal] = useState(true);
    const [batchId, setBatchId] = useState<string | null>(null);
    const [isCreatingBatch, setIsCreatingBatch] = useState(false);
    const [error, setError] = useState<string>('');
    const [serviceCredits, setServiceCredits] = useState<number | null>(null);
    const [isLoadingServiceCost, setIsLoadingServiceCost] = useState(false);
    const [batchInstruction, setBatchInstruction] = useState(promptInstruction ?? '');
    const maxFileSizeMB = 15;

    useEffect(() => {
        setBatchInstruction(promptInstruction ?? '');
    }, [promptInstruction]);

    useEffect(() => {
        let isMounted = true;
        setIsLoadingServiceCost(true);
        setServiceCredits(null);

        const fetchPrice = async () => {
            let resolvedCost: number | null = null;
            const pricingKey = resolvePricingServiceKey(method, {
                patternType,
                upscaleEngine,
            });

            if (accessToken) {
                try {
                    const response = await getServiceCost(pricingKey, accessToken, 1, {
                        patternType,
                        upscaleEngine,
                    });
                    resolvedCost = response.unit_cost ?? response.total_cost ?? null;
                } catch (err) {
                    console.warn(`获取服务价格失败（需登录接口）: ${pricingKey}`, err);
                }
            }

            if (resolvedCost === null) {
                try {
                    const response = await getPublicServicePrices();
                    const matched = response.data.find((item) => item.service_key === pricingKey);
                    resolvedCost = matched ? (matched.price_credits ?? null) : null;
                } catch (err) {
                    console.warn(`获取服务价格失败（公开接口）: ${pricingKey}`, err);
                }
            }

            if (!isMounted) {
                return;
            }

            setServiceCredits(resolvedCost);
            setIsLoadingServiceCost(false);
        };

        fetchPrice();

        return () => {
            isMounted = false;
        };
    }, [method, accessToken, patternType, upscaleEngine]);

    const handleStartBatch = useCallback(async (files: File[], referenceImage: File | null) => {
        setError('');
        setIsCreatingBatch(true);

        try {
            if (method === 'prompt_edit' && !batchInstruction.trim()) {
                setError('请填写修改指令');
                return;
            }

            const payload: BatchProcessingRequestPayload = {
                method,
                images: files,
                referenceImage: referenceImage || undefined,
                accessToken,
            };

            if (method === 'prompt_edit') {
                payload.instruction = batchInstruction;
            }

            if (method === 'extract_pattern') {
                payload.patternType = patternType;
                if (patternType === 'denim') {
                    if (denimAspectRatio) {
                        payload.aspectRatio = denimAspectRatio;
                    }
                    if (typeof denimImageCount === 'number') {
                        payload.numImages = denimImageCount;
                    }
                }
            }

            if (method === 'upscale') {
                payload.upscaleEngine = upscaleEngine;
            }

            if (method === 'expand_image') {
                payload.expandRatio = expandRatio;
                payload.expandTop = expandEdges?.top;
                payload.expandBottom = expandEdges?.bottom;
                payload.expandLeft = expandEdges?.left;
                payload.expandRight = expandEdges?.right;
                payload.expandPrompt = expandPrompt;
            }

            if (method === 'seamless_loop') {
                payload.seamDirection = seamDirection;
                payload.seamFit = seamFit;
            }

            const response = await createBatchTask(payload);
            setBatchId(response.data.batchId);
            setShowUploadModal(false);
            onHistoryRefresh?.();
        } catch (err) {
            setError((err as Error)?.message ?? '创建批量任务失败');
        } finally {
            setIsCreatingBatch(false);
        }
    }, [method, accessToken, batchInstruction, patternType, denimAspectRatio, denimImageCount, upscaleEngine, expandRatio, expandEdges, expandPrompt, seamDirection, seamFit]);

    const handleComplete = useCallback(() => {
        // Batch processing completed
        onHistoryRefresh?.();
    }, [onHistoryRefresh]);

    const handleBackToUpload = useCallback(() => {
        setBatchId(null);
        setShowUploadModal(true);
    }, []);

    // Show processing status modal
    if (batchId) {
        return (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
                <div className="bg-white rounded-lg w-full max-w-6xl h-[90vh] flex flex-col m-4">
                    <div className="flex items-center justify-between p-4 md:p-6 border-b">
                        <h2 className="text-xl font-bold text-gray-900">批量处理状态</h2>
                        <button
                            onClick={onBack}
                            className="text-gray-500 hover:text-gray-700"
                        >
                            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>
                    <div className="flex-1 overflow-y-auto p-4 md:p-6">
                        <BatchProcessingStatus
                            batchId={batchId}
                            accessToken={accessToken}
                            onComplete={handleComplete}
                            onBack={handleBackToUpload}
                        />
                    </div>
                </div>
            </div>
        );
    }

    // Show upload modal with error message if any
    return (
        <>
            {error && (
                <div className="fixed top-4 left-1/2 transform -translate-x-1/2 z-[60] max-w-md">
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4 shadow-lg">
                        <p className="text-red-600 text-sm">{error}</p>
                    </div>
                </div>
            )}
            <BatchUploadModal
                isOpen={showUploadModal}
                onClose={onBack}
                onStartBatch={handleStartBatch}
                isProcessing={isCreatingBatch}
                serviceCredits={serviceCredits}
                isLoadingServiceCost={isLoadingServiceCost}
                showReferenceImage={method === 'prompt_edit'}
                instruction={batchInstruction}
                onInstructionChange={setBatchInstruction}
                patternType={patternType}
                onPatternTypeChange={onPatternTypeChange}
                denimAspectRatio={denimAspectRatio}
                onDenimAspectRatioChange={onDenimAspectRatioChange}
                maxFileSizeMB={maxFileSizeMB}
                method={method}
                expandRatio={expandRatio}
                onExpandRatioChange={onExpandRatioChange}
                expandEdges={expandEdges}
                onExpandEdgeChange={onExpandEdgeChange}
                expandPrompt={expandPrompt}
                onExpandPromptChange={onExpandPromptChange}
                seamDirection={seamDirection}
                onSeamDirectionChange={onSeamDirectionChange}
                seamFit={seamFit}
                onSeamFitChange={onSeamFitChange}
            />
        </>
    );
}
