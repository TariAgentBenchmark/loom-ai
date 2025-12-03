'use client';

import { useState, useCallback } from 'react';
import { ProcessingMethod } from '../lib/processing';
import { createBatchTask, BatchProcessingRequestPayload } from '../lib/api';
import BatchUploadModal from './BatchUploadModal';
import BatchProcessingStatus from './BatchProcessingStatus';

interface BatchProcessingWrapperProps {
    method: ProcessingMethod;
    accessToken: string;
    onBack: () => void;
    promptInstruction?: string;
    patternType?: string;
    patternQuality?: 'standard' | '4k';
    upscaleEngine?: 'meitu_v2' | 'runninghub_vr2';
    aspectRatio?: string;
}

export default function BatchProcessingWrapper({
    method,
    accessToken,
    onBack,
    promptInstruction,
    patternType,
    patternQuality,
    upscaleEngine,
    aspectRatio,
}: BatchProcessingWrapperProps) {
    const [showUploadModal, setShowUploadModal] = useState(true);
    const [batchId, setBatchId] = useState<string | null>(null);
    const [isCreatingBatch, setIsCreatingBatch] = useState(false);
    const [error, setError] = useState<string>('');

    const handleStartBatch = useCallback(async (files: File[]) => {
        setError('');
        setIsCreatingBatch(true);

        try {
            const payload: BatchProcessingRequestPayload = {
                method,
                images: files,
                accessToken,
                instruction: promptInstruction,
                patternType,
                patternQuality,
                upscaleEngine,
                aspectRatio,
            };

            const response = await createBatchTask(payload);
            setBatchId(response.data.batchId);
            setShowUploadModal(false);
        } catch (err) {
            setError((err as Error)?.message ?? '创建批量任务失败');
        } finally {
            setIsCreatingBatch(false);
        }
    }, [method, accessToken, promptInstruction, patternType, patternQuality, upscaleEngine, aspectRatio]);

    const handleComplete = useCallback(() => {
        // Batch processing completed
        console.log('Batch processing completed');
    }, []);

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
            />
        </>
    );
}
