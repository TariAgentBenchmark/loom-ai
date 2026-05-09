"use client";

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { History, Eye, ChevronLeft, ChevronRight, X, CheckCircle } from "lucide-react";
import {
  ProcessingMethod,
  getProcessingMethodInfo,
  resolvePricingServiceKey,
} from "../lib/processing";
import {
  resolveFileUrl,
  HistoryTask,
  getServiceCost,
  downloadProcessingResult,
  getPublicServicePrices,
  splitCombinedImageRefs,
} from "../lib/api";
import HistoryList from "./HistoryList";
import ImagePreview from "./ImagePreview";
import ProcessedImagePreview from "./ProcessedImagePreview";
import ExpandPreviewFrame from "./ExpandPreviewFrame";
import ExpandEdgeControls, {
  ExpandEdgeControlsHandle,
  ExpandEdgeKey,
} from "./ExpandEdgeControls";

const formatCredits = (value: number) => {
  if (Number.isInteger(value)) {
    return value.toString();
  }

  const formatted = value.toFixed(2).replace(/\.00$/, "");
  return formatted.replace(/(\.\d*[1-9])0$/, "$1");
};

const CLOUD_KEYFRAMES = `
@keyframes loomCloudFloat {
  0% { transform: translateY(0px); }
  50% { transform: translateY(-12px); }
  100% { transform: translateY(0px); }
}
@keyframes loomCloudDraw {
  0% { stroke-dashoffset: 620; }
  50% { stroke-dashoffset: 0; }
  100% { stroke-dashoffset: -620; }
}
@keyframes loomCloudShadow {
  0% { transform: translateX(-50%) scale(1); opacity: 0.35; }
  50% { transform: translateX(-50%) scale(0.9); opacity: 0.15; }
  100% { transform: translateX(-50%) scale(1); opacity: 0.35; }
}
`;

interface CloudLoaderProps {
  message?: string;
  animated?: boolean;
}

const CloudLoader: React.FC<CloudLoaderProps> = ({
  message = "处理中...",
  animated = true,
}) => (
  <>
    {animated && <style>{CLOUD_KEYFRAMES}</style>}
    <div className="flex flex-col items-center justify-center gap-4 text-center">
      <div className="relative w-48 max-w-[70vw]">
        <svg
          className="w-full h-auto drop-shadow-[0_14px_24px_rgba(59,130,246,0.25)]"
          style={
            animated
              ? { animation: "loomCloudFloat 3.2s ease-in-out infinite" }
              : undefined
          }
          viewBox="0 0 200 120"
          role="img"
          aria-label="cloud loading"
        >
          <defs>
            <linearGradient
              id="loomCloudGradient"
              x1="0%"
              y1="50%"
              x2="100%"
              y2="50%"
            >
              <stop offset="0%" stopColor="#bfdbfe">
                {animated && (
                  <animate
                    attributeName="offset"
                    values="0;0.4;0"
                    dur="4s"
                    repeatCount="indefinite"
                  />
                )}
              </stop>
              <stop offset="50%" stopColor="#93c5fd">
                {animated && (
                  <animate
                    attributeName="offset"
                    values="0.3;0.7;0.3"
                    dur="4s"
                    repeatCount="indefinite"
                  />
                )}
              </stop>
              <stop offset="100%" stopColor="#bfdbfe">
                {animated && (
                  <animate
                    attributeName="offset"
                    values="0.6;1;0.6"
                    dur="4s"
                    repeatCount="indefinite"
                  />
                )}
              </stop>
            </linearGradient>
          </defs>
          <path
            d="M147 68c11.6 0 21-9.4 21-21s-9.4-21-21-21c-2.9 0-5.7.6-8.3 1.6C134.7 15.3 122.1 6 107.5 6 89 6 73.7 20.6 73 39c-1.8-.4-3.6-.6-5.5-.6-17.7 0-32 14.3-32 32s14.3 32 32 32H147c14.4 0 26-11.6 26-26s-11.6-26-26-26z"
            fill="url(#loomCloudGradient)"
            opacity={0.85}
          />
          <path
            d="M147 68c11.6 0 21-9.4 21-21s-9.4-21-21-21c-2.9 0-5.7.6-8.3 1.6C134.7 15.3 122.1 6 107.5 6 89 6 73.7 20.6 73 39c-1.8-.4-3.6-.6-5.5-.6-17.7 0-32 14.3-32 32s14.3 32 32 32H147c14.4 0 26-11.6 26-26s-11.6-26-26-26z"
            fill="none"
            stroke="#3b82f6"
            strokeWidth="5"
            strokeLinecap="round"
            strokeLinejoin="round"
            style={
              animated
                ? {
                  strokeDasharray: 620,
                  strokeDashoffset: 620,
                  animation: "loomCloudDraw 3s ease-in-out infinite",
                }
                : undefined
            }
          />
        </svg>
        <div
          className="absolute left-1/2 bottom-[-16px] h-4 w-3/5 rounded-full"
          style={{
            background:
              "radial-gradient(circle, rgba(148,163,184,0.35) 0%, rgba(148,163,184,0.05) 70%, transparent 100%)",
            transform: "translateX(-50%)",
            animation: animated
              ? "loomCloudShadow 3.2s ease-in-out infinite"
              : "none",
          }}
        />
      </div>
      <p className="text-base md:text-lg tracking-[0.15em] text-gray-600">
        {message}
      </p>
    </div>
  </>
);

interface ResultComparisonPanelProps {
  originalUrl: string | null;
  resultUrl: string;
  resultAlt: string;
  resultIndex?: number;
  resultDownloadUrl: string;
  totalResults?: number;
  thumbnailItems?: Array<{
    index: number;
    previewUrl: string;
    label: string;
  }>;
  onPreviewResult: (url: string, index?: number, downloadUrl?: string) => void;
  onNavigateResult?: (direction: number) => void;
  onSelectResult?: (index: number) => void;
}

const ResultComparisonPanel: React.FC<ResultComparisonPanelProps> = ({
  originalUrl,
  resultUrl,
  resultAlt,
  resultIndex,
  resultDownloadUrl,
  totalResults = 1,
  thumbnailItems = [],
  onPreviewResult,
  onNavigateResult,
  onSelectResult,
}) => {
  const resolvedOriginalUrl = originalUrl ? resolveFileUrl(originalUrl) : "";
  const resolvedResultUrl = resolveFileUrl(resultUrl);
  const canNavigate = totalResults > 1 && Boolean(onNavigateResult);
  const showThumbnailOverlay =
    thumbnailItems.length > 1 && resultIndex !== undefined && Boolean(onSelectResult);

  return (
    <div className="grid w-full grid-cols-1 gap-3 md:gap-4 lg:h-full lg:min-h-0 lg:grid-cols-2">
      <div className="flex min-h-[240px] flex-col overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm md:min-h-[420px] lg:h-full lg:min-h-0">
        <div className="flex items-center justify-between border-b border-gray-100 px-3 py-2">
          <span className="text-sm font-semibold text-gray-900">原图</span>
        </div>
        <div className="flex min-h-0 flex-1 items-center justify-center bg-gray-50 p-2 md:p-3">
          {resolvedOriginalUrl ? (
            <img
              src={resolvedOriginalUrl}
              alt="原图"
              className="h-auto max-h-[58vh] w-auto max-w-full rounded-lg border border-gray-200 bg-white object-contain shadow lg:h-full lg:max-h-none lg:w-full"
            />
          ) : (
            <div className="flex h-full min-h-[180px] w-full items-center justify-center rounded-lg border border-dashed border-gray-200 bg-white text-sm text-gray-400">
              暂无原图
            </div>
          )}
        </div>
      </div>

      <div className="flex min-h-[240px] flex-col overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm md:min-h-[420px] lg:h-full lg:min-h-0">
        <div className="flex items-center justify-between border-b border-gray-100 px-3 py-2">
          <span className="text-sm font-semibold text-gray-900">
            {totalResults > 1 && resultIndex !== undefined
              ? `结果图 ${resultIndex + 1}`
              : "结果图"}
          </span>
          {totalResults > 1 && (
            <span className="text-xs text-gray-500">
              {resultIndex !== undefined ? resultIndex + 1 : 1}/{totalResults}
            </span>
          )}
        </div>
        <div className="flex min-h-0 flex-1 items-center justify-center bg-gray-50 p-2 md:p-3">
          <div className="relative group flex h-full w-full items-center justify-center">
            <img
              src={resolvedResultUrl}
              alt={resultAlt}
              className="h-auto max-h-[58vh] w-auto max-w-full cursor-pointer rounded-lg border border-gray-200 bg-white object-contain shadow-md transition-shadow hover:shadow-lg lg:h-full lg:max-h-none lg:w-full"
              onClick={() =>
                onPreviewResult(resultUrl, resultIndex, resultDownloadUrl)
              }
            />
            <button
              onClick={() =>
                onPreviewResult(resultUrl, resultIndex, resultDownloadUrl)
              }
              className="absolute top-2 right-2 p-2 bg-black bg-opacity-50 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity hover:bg-opacity-70"
              title="放大查看"
            >
              <Eye className="h-4 w-4" />
            </button>
            {canNavigate && (
              <>
                <button
                  type="button"
                  onClick={(event) => {
                    event.stopPropagation();
                    onNavigateResult?.(-1);
                  }}
                  className="absolute left-2 top-1/2 -translate-y-1/2 p-2 rounded-full bg-black bg-opacity-40 text-white hover:bg-opacity-70 transition"
                  title="上一张"
                >
                  <ChevronLeft className="h-5 w-5" />
                </button>
                <button
                  type="button"
                  onClick={(event) => {
                    event.stopPropagation();
                    onNavigateResult?.(1);
                  }}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-full bg-black bg-opacity-40 text-white hover:bg-opacity-70 transition"
                  title="下一张"
                >
                  <ChevronRight className="h-5 w-5" />
                </button>
              </>
            )}
            {showThumbnailOverlay && (
              <div className="absolute bottom-3 left-1/2 z-10 flex max-w-[calc(100%-1.5rem)] -translate-x-1/2 gap-2 overflow-x-auto">
                {thumbnailItems.map((item) => {
                  const isActive = item.index === resultIndex;
                  return (
                    <button
                      key={`${item.previewUrl}-${item.index}`}
                      type="button"
                      onClick={(event) => {
                        event.stopPropagation();
                        onSelectResult?.(item.index);
                      }}
                      className={`flex shrink-0 flex-col items-center rounded-lg border px-1.5 py-1 text-[10px] transition ${
                        isActive
                          ? "border-blue-500 bg-blue-50 shadow-sm"
                          : "border-gray-200 bg-white/90 hover:border-blue-300 hover:bg-gray-50"
                      }`}
                      title={`查看${item.label}`}
                    >
                      <div className="h-12 w-12 overflow-hidden rounded border border-dashed border-gray-200 bg-white">
                        <img
                          src={resolveFileUrl(item.previewUrl)}
                          alt={`${item.label}缩略图`}
                          className="h-full w-full object-cover"
                        />
                      </div>
                      <span className="mt-0.5 font-medium text-gray-700">
                        {item.label}
                      </span>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

interface ProcessingPageProps {
  method: ProcessingMethod;
  imagePreview: string | null;
  secondaryImagePreview?: string | null;
  processedImage: string | null;
  processedImageDisplay?: string | null;
  processedImageThumbnail?: string | null;
  comparisonOriginalImage?: string | null;
  currentTaskId?: string;
  isProcessing: boolean;
  hasUploadedImage: boolean;
  onBack: () => void;
  onOpenPricingModal: () => void;
  onProcessImage: () => void;
  onDragOver: (event: React.DragEvent<HTMLDivElement>) => void;
  onDrop: (event: React.DragEvent<HTMLDivElement>) => void;
  fileInputRef: React.RefObject<HTMLInputElement>;
  secondaryFileInputRef?: React.RefObject<HTMLInputElement>;
  onFileInputChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onSecondaryFileInputChange?: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onSecondaryDragOver?: (event: React.DragEvent<HTMLDivElement>) => void;
  onSecondaryDrop?: (event: React.DragEvent<HTMLDivElement>) => void;
  onClearPrimaryImage?: () => void;
  onClearSecondaryImage?: () => void;
  errorMessage?: string;
  successMessage?: string;
  accessToken?: string;
  promptInstruction?: string;
  onPromptInstructionChange?: (value: string) => void;
  embroideryMode?: "yarn" | "embroidery";
  onEmbroideryModeChange?: (value: "yarn" | "embroidery") => void;
  patternType?: string;
  onPatternTypeChange?: (value: string) => void;
  denimAspectRatio?: string;
  onDenimAspectRatioChange?: (value: string) => void;
  generalImageCount?: number;
  onGeneralImageCountChange?: (value: number) => void;
  upscaleEngine?: "meitu_v2" | "runninghub_vr2" | "runninghub_4k_ultra";
  onUpscaleEngineChange?: (value: "meitu_v2" | "runninghub_vr2" | "runninghub_4k_ultra") => void;
  expandRatio?: string;
  onExpandRatioChange?: (value: string) => void;
  expandEdges?: Record<ExpandEdgeKey, string>;
  onExpandEdgeChange?: (edge: ExpandEdgeKey, value: string) => void;
  expandPrompt?: string;
  onExpandPromptChange?: (value: string) => void;
  seamDirection?: number;
  onSeamDirectionChange?: (value: number) => void;
  seamFit?: number;
  onSeamFitChange?: (value: number) => void;
  denoise?: number;
  onDenoiseChange?: (value: number) => void;
  historyRefreshToken?: number;
  // Batch mode props
  batchMode?: boolean;
  onBatchModeChange?: (enabled: boolean) => void;
  batchId?: string | null;
  onBatchComplete?: () => void;
}

const ProcessingPage: React.FC<ProcessingPageProps> = ({
  method,
  imagePreview,
  secondaryImagePreview,
  processedImage,
  processedImageDisplay = null,
  processedImageThumbnail = null,
  comparisonOriginalImage = null,
  currentTaskId,
  isProcessing,
  hasUploadedImage,
  onBack,
  onOpenPricingModal,
  onProcessImage,
  onDragOver,
  onDrop,
  fileInputRef,
  secondaryFileInputRef,
  onFileInputChange,
  onSecondaryFileInputChange,
  onSecondaryDragOver,
  onSecondaryDrop,
  onClearPrimaryImage,
  onClearSecondaryImage,
  errorMessage,
  successMessage,
  accessToken,
  promptInstruction,
  onPromptInstructionChange,
  embroideryMode = "embroidery",
  onEmbroideryModeChange,
  patternType,
  onPatternTypeChange,
  denimAspectRatio,
  onDenimAspectRatioChange,
  generalImageCount = 4,
  onGeneralImageCountChange,
  upscaleEngine,
  onUpscaleEngineChange,
  expandRatio,
  onExpandRatioChange,
  expandEdges,
  onExpandEdgeChange,
  expandPrompt,
  onExpandPromptChange,
  seamDirection = 0,
  onSeamDirectionChange,
  seamFit = 0.7,
  onSeamFitChange,
  denoise = 0.7,
  onDenoiseChange,
  historyRefreshToken = 0,
  batchMode,
  onBatchModeChange,
}) => {
  const info = getProcessingMethodInfo(method);
  const [selectedTask, setSelectedTask] = useState<HistoryTask | null>(null);
  const [showImagePreview, setShowImagePreview] = useState(false);
  const [processedImagePreview, setProcessedImagePreview] = useState<{
    url: string;
    filename: string;
    downloadUrl: string;
  } | null>(null);
  const [isDownloadingResult, setIsDownloadingResult] = useState(false);
  const [selectedResultIndex, setSelectedResultIndex] = useState(0);
  const [showWechatModal, setShowWechatModal] = useState(false);
  const [showSuccessToast, setShowSuccessToast] = useState(false);
  const [isHistoryCollapsed, setIsHistoryCollapsed] = useState(true);

  // 成功消息出现时显示 toast，手动关闭
  useEffect(() => {
    if (successMessage && !errorMessage) {
      setShowSuccessToast(true);
    } else {
      setShowSuccessToast(false);
    }
  }, [successMessage, errorMessage]);
  const isPromptReady =
    method !== "prompt_edit" || Boolean(promptInstruction?.trim());
  const isActionDisabled = !hasUploadedImage || isProcessing || !isPromptReady;
  const [serviceCredits, setServiceCredits] = useState<number | null>(null);
  const [isLoadingServiceCost, setIsLoadingServiceCost] = useState(true);
  const processedImageUrls = useMemo(
    () => splitCombinedImageRefs(processedImage),
    [processedImage],
  );
  const processedDisplayUrls = useMemo(
    () => splitCombinedImageRefs(processedImageDisplay || processedImage),
    [processedImage, processedImageDisplay],
  );
  const processedThumbnailUrls = useMemo(
    () =>
      splitCombinedImageRefs(
        processedImageThumbnail || processedImageDisplay || processedImage,
      ),
    [processedImage, processedImageDisplay, processedImageThumbnail],
  );
  const comparisonOriginalUrl = comparisonOriginalImage || imagePreview;
  const upscaleOptions: {
    value: "meitu_v2" | "runninghub_vr2" | "runninghub_4k_ultra";
    label: string;
    description: string;
  }[] = [
    {
        value: "meitu_v2",
        label: "通用1",
        description:
          "基础高清模式，追求稳定还原与高保真，适合模糊或噪点较多的图片。",
      },
      {
        value: "runninghub_vr2",
        label: "通用2",
        description: "锐化高清模式，突出细节与纹理锐度，适合较高清的原图。",
      },
      {
        value: "runninghub_4k_ultra",
        label: "4K超清",
        description: "超高清4K放大模式，极致细节还原，适合需要大幅面输出的场景。",
      },
    ];
  const patternTypeOptions: { value: string; label: string; hint?: string }[] =
    [
      { value: "general", label: "通用模型" },
      { value: "combined", label: "综合模型" },
      { value: "denim", label: "牛仔风格专用" },
    ];
  const embroideryModeOptions: {
    value: "yarn" | "embroidery";
    label: string;
    description: string;
  }[] = [
    {
      value: "yarn",
      label: "毛线效果",
      description: "保留现有毛线质感与手工编织纹理表现。",
    },
    {
      value: "embroidery",
      label: "刺绣效果",
      description: "使用新刺绣模型，突出精致针脚与原图细节保留。",
    },
  ];
  const denimSizeOptions: { value: string; label: string }[] = [
    { value: "1:1", label: "方形 1:1" },
    { value: "2:3", label: "竖版 2:3" },
    { value: "3:2", label: "横版 3:2" },
  ];
  const generalImageCountOptions: { value: number; label: string }[] = [
    { value: 1, label: "1张图" },
    { value: 2, label: "2张图" },
    { value: 4, label: "4张图" },
  ];
  const effectivePatternType = patternType ?? "combined";
  const effectiveGeneralImageCount = generalImageCount ?? 4;
  const effectiveDenimAspectRatio = denimAspectRatio ?? "1:1";
  const selectedUpscaleOption =
    upscaleOptions.find(
      (option) => option.value === (upscaleEngine || "meitu_v2"),
    ) ?? upscaleOptions[0];
  const effectiveExpandRatio = expandRatio ?? "original";
  useEffect(() => {
    // 新结果返回时重置预览索引
    setSelectedResultIndex(0);
  }, [processedImage]);

  const handleNavigateResult = useCallback(
    (direction: number, total: number) => {
      if (total <= 1) return;
      setSelectedResultIndex((prev) => {
        const next = prev + direction;
        if (next < 0) return total - 1;
        if (next >= total) return 0;
        return next;
      });
    },
    [],
  );
  const edgeValues = useMemo(
    () =>
      expandEdges ?? {
        top: "0.00",
        bottom: "0.00",
        left: "0.00",
        right: "0.00",
      },
    [expandEdges],
  );
  const expandEdgeControlsRef = useRef<ExpandEdgeControlsHandle>(null);
  const isSeamlessLoop = method === "seamless_loop";
  const isExpandImage = method === "expand_image";
  const serviceCostHint =
    method === "extract_pattern"
      ? "失败不扣积分，少于3张少扣0.5积分"
      : "失败不扣积分";
  const handleClearPrimaryImage = useCallback(
    (event: React.MouseEvent<HTMLButtonElement>) => {
      event.stopPropagation();
      if (isProcessing) {
        return;
      }
      onClearPrimaryImage?.();
    },
    [isProcessing, onClearPrimaryImage],
  );
  const handleClearSecondaryImage = useCallback(
    (event: React.MouseEvent<HTMLButtonElement>) => {
      event.stopPropagation();
      if (isProcessing) {
        return;
      }
      onClearSecondaryImage?.();
    },
    [isProcessing, onClearSecondaryImage],
  );
  const denoiseValue = Math.max(0, Math.min(1, denoise));
  const uploadZoneClasses = `border-2 border-dashed rounded-lg md:rounded-xl p-4 md:p-8 text-center transition flex items-center justify-center ${isProcessing
    ? "cursor-not-allowed opacity-60 pointer-events-none"
    : "cursor-pointer"
    } ${isSeamlessLoop
      ? "border-blue-300 hover:border-blue-400 bg-blue-50/70 min-h-[220px] md:min-h-[260px]"
      : isExpandImage
        ? "border-gray-300 hover:border-blue-400 bg-white min-h-[210px] md:min-h-[260px]"
        : "border-gray-300 hover:border-blue-400 min-h-[150px] md:min-h-[200px]"
    }`;
  const promptUploadBase = `border-2 border-dashed rounded-lg md:rounded-xl p-4 md:p-6 text-center transition flex items-center justify-center min-h-[170px] md:min-h-[200px] ${isProcessing
    ? "cursor-not-allowed opacity-60 pointer-events-none"
    : "cursor-pointer"
    }`;
  const promptPrimaryClasses = `${promptUploadBase} border-gray-300 hover:border-blue-400 bg-white`;
  const promptSecondaryClasses = `${promptUploadBase} border-amber-300 hover:border-amber-400 bg-amber-50/60`;

  const handleNormalizedEdgesChange = useCallback(
    (edges: Record<ExpandEdgeKey, number>) => {
      expandEdgeControlsRef.current?.handleNormalizedEdgesChange(edges);
    },
    [],
  );

  useEffect(() => {
    let isMounted = true;
    setIsLoadingServiceCost(true);
    setServiceCredits(null);

    const fetchPrice = async () => {
      let resolvedCost: number | null = null;
      const numImages =
        method === "extract_pattern" && patternType === "general"
          ? effectiveGeneralImageCount
          : undefined;
      const pricingKey = resolvePricingServiceKey(method, {
        patternType,
        upscaleEngine,
        numImages,
      });

      if (accessToken) {
        try {
          const response = await getServiceCost(pricingKey, accessToken, 1, {
            patternType,
            numImages,
            upscaleEngine,
          });
          resolvedCost = response.unit_cost ?? response.total_cost ?? null;
        } catch (error) {
          console.warn(`获取服务价格失败（需登录接口）: ${pricingKey}`, error);
        }
      }

      if (resolvedCost === null) {
        try {
          const response = await getPublicServicePrices();
          const matched = response.data.find(
            (item) => item.service_key === pricingKey,
          );
          resolvedCost = matched ? (matched.price_credits ?? null) : null;
        } catch (error) {
          console.warn(`获取服务价格失败（公开接口）: ${pricingKey}`, error);
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
  }, [method, accessToken, patternType, upscaleEngine, effectiveGeneralImageCount]);

  useEffect(() => {
    setSelectedResultIndex(0);
  }, [processedImage, method, patternType, embroideryMode]);

  const handlePromptTemplateSelect = (template: string) => {
    if (onPromptInstructionChange) {
      onPromptInstructionChange(template);
    }
  };

  const promptTemplates = [
    "把图中裙子改成白色",
    "调整背景为浅灰色并保留人物",
    "把模特的上衣改成牛仔材质",
    "让图片中的包包换成黑色皮质",
  ];

  const handleTaskSelect = (task: HistoryTask) => {
    setSelectedTask(task);
    setShowImagePreview(true);
  };

  const handleClosePreview = () => {
    setShowImagePreview(false);
    setSelectedTask(null);
  };

  const handleProcessedImagePreview = (
    url: string,
    index?: number,
    downloadUrl?: string,
  ) => {
    // 从URL中提取文件扩展名，先去除查询参数
    const cleanUrl = (downloadUrl || url).split("?")[0];
    const urlParts = cleanUrl.split("/");
    const urlFilename = urlParts[urlParts.length - 1];
    const extensionMatch = urlFilename.match(/\.[^.]+$/);
    const extension = extensionMatch ? extensionMatch[0] : ".png";

    const filename =
      index !== undefined
        ? `result_${index + 1}${extension}`
        : `result${extension}`;
    setProcessedImagePreview({
      url,
      filename,
      downloadUrl: downloadUrl || url,
    });
  };

  const handleCloseProcessedImagePreview = () => {
    setProcessedImagePreview(null);
  };

  const handlePreviewNavigation = (direction: "prev" | "next") => {
    if (!processedDisplayUrls.length || !processedImagePreview) return;

    const currentIndex = processedDisplayUrls.findIndex(
      (url) => url === processedImagePreview.url,
    );

    if (currentIndex === -1) return;

    const newIndex = direction === "prev" ? currentIndex - 1 : currentIndex + 1;

    if (newIndex >= 0 && newIndex < processedDisplayUrls.length) {
      handleProcessedImagePreview(
        processedDisplayUrls[newIndex],
        newIndex,
        processedImageUrls[newIndex] || processedDisplayUrls[newIndex],
      );
    }
  };

  const extractExtension = (value: string): string => {
    const sanitized = value.split(/[?#]/)[0] ?? value;
    const parts = sanitized.split(".");
    if (parts.length < 2) {
      return "png";
    }
    const rawExt = parts.pop() ?? "png";
    return rawExt.toLowerCase();
  };

  const buildDownloadName = (extension: string, index?: number) => {
    const normalizedExt = extension.replace(/^\./, "").toLowerCase();
    const effectiveExt =
      normalizedExt === "jpeg" ? "jpg" : normalizedExt || "png";
    const cleanExt = effectiveExt.replace(/[^a-z0-9]/g, "") || "png";
    if (typeof index === "number") {
      return `tuyun_${index + 1}.${cleanExt}`;
    }
    return `tuyun.${cleanExt}`;
  };

  const downloadBlob = (blob: Blob, filename: string) => {
    const url = window.URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
    window.URL.revokeObjectURL(url);
  };

  const fetchAndDownload = async (url: string, filename: string) => {
    const response = await fetch(resolveFileUrl(url));
    if (!response.ok) {
      throw new Error(`下载失败，状态码: ${response.status}`);
    }
    const blob = await response.blob();
    downloadBlob(blob, filename);
  };

  const normalizeFormat = (
    extension: string,
  ): "png" | "jpg" | "svg" | "zip" => {
    const normalized = extension.replace(/^\./, "").toLowerCase();
    if (normalized === "svg") return "svg";
    if (normalized === "jpg" || normalized === "jpeg") return "jpg";
    if (normalized === "zip") return "zip";
    return "png";
  };

  const handleDownloadProcessedResult = async () => {
    if (!processedImageUrls.length) return;

    const primaryUrl = processedImageUrls[0];
    const extension = extractExtension(primaryUrl);
    const fallbackName = buildDownloadName(extension);

    try {
      setIsDownloadingResult(true);
      if (accessToken && currentTaskId) {
        const format = normalizeFormat(extension);
        const { blob, filename } = await downloadProcessingResult(
          currentTaskId,
          accessToken,
          format,
        );
        downloadBlob(blob, filename);
      } else {
        await fetchAndDownload(primaryUrl, fallbackName);
      }
    } catch (error) {
      console.error("下载结果失败:", error);
    } finally {
      setIsDownloadingResult(false);
    }
  };

  const handleDownloadSingleImage = async (url: string, index: number) => {
    const extension = extractExtension(url);
    const filename = buildDownloadName(extension, index);
    try {
      setIsDownloadingResult(true);
      await fetchAndDownload(url, filename);
    } catch (error) {
      console.error("下载图片失败:", error);
    } finally {
      setIsDownloadingResult(false);
    }
  };

  const handleBatchDownload = async () => {
    if (!processedImageUrls.length) return;

    try {
      setIsDownloadingResult(true);
      if (accessToken && currentTaskId) {
        const { blob, filename } = await downloadProcessingResult(
          currentTaskId,
          accessToken,
          "zip",
        );
        downloadBlob(blob, filename);
      } else {
        for (let i = 0; i < processedImageUrls.length; i += 1) {
          const extension = extractExtension(processedImageUrls[i]);
          const filename = buildDownloadName(extension, i);
          await fetchAndDownload(processedImageUrls[i], filename);
          if (i < processedImageUrls.length - 1) {
            await new Promise((resolve) => setTimeout(resolve, 400));
          }
        }
      }
    } catch (error) {
      console.error("批量下载失败:", error);
    } finally {
      setIsDownloadingResult(false);
    }
  };

  return (
    <div className="h-screen bg-gray-50 flex flex-col">
      <header className="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
        <div className="flex items-center justify-between px-4 md:px-6 py-3 md:py-4">
          <div className="flex items-center space-x-2 md:space-x-4">
            <button
              onClick={onBack}
              className="flex items-center space-x-1 md:space-x-2 text-gray-600 hover:text-gray-900 transition"
            >
              <span>←</span>
              <span className="hidden sm:inline">返回</span>
            </button>
            <div className="flex items-center space-x-2 md:space-x-3">
              <div className="flex h-6 w-6 md:h-8 md:w-8 items-center justify-center rounded-lg bg-white shadow-md overflow-hidden">
                <img
                  src={info.icon}
                  alt={info.title}
                  className="h-4 w-4 md:h-6 md:w-6 object-contain"
                />
              </div>
              <h1 className="text-base md:text-xl font-bold text-gray-900">
                {info.title}
              </h1>
            </div>
          </div>

          <div className="flex items-center space-x-2 md:space-x-4">
            {accessToken && (
              <button
                onClick={onOpenPricingModal}
                className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white px-3 py-1.5 md:px-4 md:py-2 rounded-lg text-xs md:text-sm font-medium transition-all shadow-sm"
              >
                套餐充值
              </button>
            )}
          </div>
        </div>
      </header>

      {/* 提示横幅 */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-blue-100 px-4 py-2">
        <div className="flex items-center justify-center gap-2 text-sm">
          <span className="text-gray-600">出图效果不好或有任何问题请联系管理员（免费重跑出图  解答任何网站内问题）</span>
          <button
            onClick={() => setShowWechatModal(true)}
            className="text-blue-600 hover:text-blue-700 font-medium underline"
          >
            联系管理员
          </button>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden flex-col md:flex-row">
        <div className="w-full md:w-96 bg-white border-r border-gray-200 p-4 md:p-6 overflow-y-auto order-2 md:order-1">
          <div className="mb-4 md:mb-6">
            <h3 className="text-base md:text-lg font-semibold text-gray-900 mb-3 md:mb-4">
              上传图片
            </h3>
            {method === "prompt_edit" ? (
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2 md:gap-4">
                <div
                  className={promptPrimaryClasses}
                  onDragOver={onDragOver}
                  onDrop={onDrop}
                  onClick={() => {
                    if (isProcessing) return;
                    fileInputRef.current?.click();
                  }}
                  role="button"
                  aria-disabled={isProcessing}
                >
                  {imagePreview ? (
                    <div className="relative space-y-2 md:space-y-4">
                      <button
                        type="button"
                        onClick={handleClearPrimaryImage}
                        className="absolute -top-2 -right-2 z-10 inline-flex h-7 w-7 items-center justify-center rounded-full border border-white bg-white/95 text-gray-500 shadow-sm transition hover:text-red-500"
                        aria-label="删除已上传图片"
                        title="删除已上传图片"
                      >
                        <X className="h-4 w-4" />
                      </button>
                      <img
                        src={resolveFileUrl(imagePreview)}
                        alt="Preview"
                        className="mx-auto max-h-28 md:max-h-32 rounded-lg border border-gray-200"
                      />
                      <p className="text-xs md:text-sm text-gray-500">
                        点击或拖拽图片到此处上传
                      </p>
                    </div>
                  ) : (
                        <div className="space-y-2 md:space-y-3">
                          <div className="mx-auto flex h-10 w-10 md:h-12 md:w-12 items-center justify-center rounded-lg md:rounded-xl bg-gray-100 text-gray-400">
                            ⬆
                          </div>
                          <div>
                            <p className="text-sm md:text-base font-semibold text-gray-800">
                          上传图片1（待修改图）
                            </p>
                            <p className="text-xs md:text-sm text-gray-500">
                              支持 JPG、PNG 等格式
                            </p>
                          </div>
                    </div>
                  )}
                </div>

                <div
                  className={promptSecondaryClasses}
                  onDragOver={onSecondaryDragOver || onDragOver}
                  onDrop={onSecondaryDrop || onDrop}
                  onClick={() => {
                    if (isProcessing) return;
                    secondaryFileInputRef?.current?.click();
                  }}
                  role="button"
                  aria-disabled={isProcessing}
                >
                  {secondaryImagePreview ? (
                    <div className="relative space-y-2 md:space-y-4">
                      <button
                        type="button"
                        onClick={handleClearSecondaryImage}
                        className="absolute -top-2 -right-2 z-10 inline-flex h-7 w-7 items-center justify-center rounded-full border border-white bg-white/95 text-gray-500 shadow-sm transition hover:text-red-500"
                        aria-label="删除参考图片"
                        title="删除参考图片"
                      >
                        <X className="h-4 w-4" />
                      </button>
                      <img
                        src={resolveFileUrl(secondaryImagePreview)}
                        alt="Preview"
                        className="mx-auto max-h-28 md:max-h-32 rounded-lg border border-amber-200"
                      />
                      <p className="text-xs md:text-sm text-amber-700">
                        可选：点击或拖拽替换第二张图
                      </p>
                    </div>
                  ) : (
                        <div className="space-y-2 md:space-y-3">
                          <div className="mx-auto flex h-10 w-10 md:h-12 md:w-12 items-center justify-center rounded-lg md:rounded-xl bg-amber-100 text-amber-500">
                            ⬆
                          </div>
                          <div>
                            <p className="text-sm md:text-base font-semibold text-gray-800">
                          上传图片2（参考图，可选）
                            </p>
                            <p className="text-xs md:text-sm text-gray-600">
                              支持 JPG、PNG 等格式
                            </p>
                          </div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div
                className={uploadZoneClasses}
                onDragOver={onDragOver}
                onDrop={onDrop}
                onClick={() => {
                  if (isProcessing) {
                    return;
                  }
                  fileInputRef.current?.click();
                }}
                role="button"
                aria-disabled={isProcessing}
              >
                {imagePreview ? (
                  isExpandImage ? (
                    <div className="relative">
                      <button
                        type="button"
                        onClick={handleClearPrimaryImage}
                        className="absolute -top-3 -right-3 z-10 inline-flex h-7 w-7 items-center justify-center rounded-full border border-white bg-white/95 text-gray-500 shadow-sm transition hover:text-red-500"
                        aria-label="删除已上传图片"
                        title="删除已上传图片"
                      >
                        <X className="h-4 w-4" />
                      </button>
                      <ExpandPreviewFrame
                        imageUrl={imagePreview}
                        ratio={effectiveExpandRatio}
                        edges={edgeValues}
                        onNormalizedEdgesChange={handleNormalizedEdgesChange}
                      />
                    </div>
                  ) : (
                    <div className="relative space-y-2 md:space-y-4">
                      <button
                        type="button"
                        onClick={handleClearPrimaryImage}
                        className="absolute -top-2 -right-2 z-10 inline-flex h-7 w-7 items-center justify-center rounded-full border border-white bg-white/95 text-gray-500 shadow-sm transition hover:text-red-500"
                        aria-label="删除已上传图片"
                        title="删除已上传图片"
                      >
                        <X className="h-4 w-4" />
                      </button>
                      <img
                        src={resolveFileUrl(imagePreview)}
                        alt="Preview"
                        className="mx-auto max-h-24 md:max-h-32 rounded-lg border border-gray-200"
                      />
                      <p className="text-xs md:text-sm text-gray-500">
                        拖拽图片或点击上传
                      </p>
                    </div>
                  )
                ) : isSeamlessLoop ? (
                  <div className="flex flex-col items-center gap-2 md:gap-3">
                    <span className="text-4xl md:text-5xl font-semibold text-blue-500">
                      +
                    </span>
                    <p className="text-sm md:text-base font-medium text-gray-700">
                      点击上传图片
                    </p>
                    <p className="text-xs md:text-sm text-gray-500">
                      支持 JPG/PNG，建议尺寸 ≥ 1024px
                    </p>
                  </div>
                ) : (
                  <div className="space-y-2 md:space-y-4">
                    <div className="mx-auto flex h-10 w-10 md:h-12 md:w-12 items-center justify-center rounded-lg md:rounded-xl bg-gray-100 text-gray-400">
                      ⬆
                    </div>
                    <div>
                      <p className="text-sm md:text-base font-medium text-gray-700">
                        拖拽图片或点击上传
                      </p>
                    </div>
                  </div>
                )}
              </div>
            )}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={onFileInputChange}
              className="hidden"
              disabled={isProcessing}
            />
            <input
              ref={secondaryFileInputRef}
              type="file"
              accept="image/*"
              onChange={onSecondaryFileInputChange}
              className="hidden"
              disabled={isProcessing}
            />
          </div>

          <div className="mb-4 md:mb-6">
            <div className="mb-3">
              <div className="w-full rounded-lg md:rounded-xl border border-blue-100 bg-blue-50 px-3 py-2 text-center text-xs md:text-sm text-blue-700">
                {isLoadingServiceCost
                  ? "价格加载中…"
                  : serviceCredits !== null
                    ? `${formatCredits(serviceCredits)} 积分/次（${serviceCostHint}）`
                    : "价格暂不可用，请稍后重试"}
              </div>
            </div>
            <button
              onClick={onProcessImage}
              disabled={isActionDisabled}
              className="w-full bg-gradient-to-r from-pink-500 to-pink-600 hover:from-pink-600 hover:to-pink-700 disabled:from-gray-400 disabled:to-gray-500 text-white font-medium py-3 px-4 md:py-4 md:px-6 rounded-lg md:rounded-xl text-base md:text-lg shadow-lg transition-all transform hover:scale-105 disabled:hover:scale-100"
            >
              {isProcessing ? (
                <div className="flex items-center justify-center space-x-2">
                  <div className="animate-spin h-4 w-4 md:h-5 md:w-5 border-2 border-white border-t-transparent rounded-full" />
                  <span>处理中...</span>
                </div>
              ) : (
                "一键生成"
              )}
            </button>

            {/* Batch Processing Button */}
            {onBatchModeChange && !batchMode && (
              <button
                onClick={() => onBatchModeChange(true)}
                className="mt-3 md:mt-4 w-full bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white font-medium py-3 px-4 md:py-3.5 md:px-6 rounded-lg md:rounded-xl text-sm md:text-base shadow-md transition-all transform hover:scale-105"
              >
                批量处理
              </button>
            )}
          </div>

          {method === "expand_image" && (
            <div className="mb-4 md:mb-6">
              <ExpandEdgeControls
                ref={expandEdgeControlsRef}
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

          {method === "similar_image" && (
            <div className="mb-4 md:mb-6">
              <h4 className="text-sm md:text-base font-semibold text-gray-900 mb-2">
                相似强度
              </h4>
              <div className="flex items-center gap-3">
                <input
                  type="range"
                  min={0}
                  max={1}
                  step={0.05}
                  value={denoiseValue}
                  onChange={(event) =>
                    onDenoiseChange?.(Number(event.target.value))
                  }
                  disabled={isProcessing}
                  className="w-full accent-blue-500 disabled:opacity-60"
                />
                <span className="text-xs md:text-sm text-gray-600 w-12 text-right">
                  {denoiseValue.toFixed(2)}
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                数值越高越接近参考图，数值越低变化越明显。
              </p>
            </div>
          )}

          {method === "embroidery" && (
            <div className="mb-4 md:mb-6 space-y-4">
              <div>
                <h4 className="text-sm md:text-base font-semibold text-gray-900 mb-2">
                  效果模式
                </h4>
                <div className="grid grid-cols-1 gap-3">
                  {embroideryModeOptions.map((option) => {
                    const isActive = embroideryMode === option.value;
                    return (
                      <button
                        type="button"
                        key={option.value}
                        onClick={() => onEmbroideryModeChange?.(option.value)}
                        className={`rounded-xl border p-3 text-left transition-all ${
                          isActive
                            ? "border-blue-500 bg-blue-50 shadow-sm"
                            : "border-gray-200 hover:border-blue-300 hover:bg-blue-50/60"
                        }`}
                      >
                        <div className="text-sm md:text-base font-semibold text-gray-900">
                          {option.label}
                        </div>
                        <p className="mt-1 text-xs md:text-sm text-gray-600">
                          {option.description}
                        </p>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {method === "extract_pattern" && (
            <div className="mb-4 md:mb-6">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm md:text-base font-semibold text-gray-900">
                  模型
                </h4>
              </div>
              <div className="grid grid-cols-2 gap-3">
                {patternTypeOptions.map((option) => {
                  const isActive = effectivePatternType === option.value;
                  return (
                    <button
                      type="button"
                      key={option.value}
                      onClick={() => onPatternTypeChange?.(option.value)}
                      className={`flex flex-col items-start gap-1 rounded-xl border p-3 text-left transition-all ${isActive
                        ? "border-blue-500 bg-blue-50 shadow-sm"
                        : "border-gray-200 hover:border-blue-300 hover:bg-blue-50/60"
                        }`}
                    >
                      <span className="text-sm md:text-base font-semibold text-gray-900">
                        {option.label}
                      </span>
                    </button>
                  );
                })}
              </div>
              {effectivePatternType === "general" && (
                <div className="mt-4 space-y-4">
                  <div>
                    <h4 className="text-sm md:text-base font-semibold text-gray-900 mb-2">
                      出图数量
                    </h4>
                    <div className="grid grid-cols-3 gap-2">
                      {generalImageCountOptions.map((option) => {
                        const isActive =
                          effectiveGeneralImageCount === option.value;
                        return (
                          <button
                            type="button"
                            key={option.value}
                            onClick={() =>
                              onGeneralImageCountChange?.(option.value)
                            }
                            className={`rounded-lg border px-3 py-2 text-xs md:text-sm font-medium transition ${isActive
                              ? "border-blue-500 bg-blue-50 text-blue-600 shadow-sm"
                              : "border-gray-200 text-gray-600 hover:border-blue-300 hover:bg-blue-50/60"
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
              {effectivePatternType === "denim" && (
                <div className="mt-4 space-y-4">
                  <div>
                    <h4 className="text-sm md:text-base font-semibold text-gray-900 mb-2">
                      图片尺寸
                    </h4>
                    <div className="grid grid-cols-3 gap-2">
                      {denimSizeOptions.map((option) => {
                        const isActive =
                          effectiveDenimAspectRatio === option.value;
                        return (
                          <button
                            type="button"
                            key={option.value}
                            onClick={() =>
                              onDenimAspectRatioChange?.(option.value)
                            }
                            className={`rounded-lg border px-3 py-2 text-xs md:text-sm font-medium transition ${isActive
                              ? "border-blue-500 bg-blue-50 text-blue-600 shadow-sm"
                              : "border-gray-200 text-gray-600 hover:border-blue-300 hover:bg-blue-50/60"
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

          {method === "upscale" && (
            <div className="mb-4 md:mb-6">
              <h4 className="text-sm md:text-base font-semibold text-gray-900 mb-2">
                高清算法
              </h4>
              <div className="grid grid-cols-2 gap-3">
                {upscaleOptions.map((option) => {
                  const isActive =
                    (upscaleEngine || "meitu_v2") === option.value;
                  return (
                    <button
                      type="button"
                      key={option.value}
                      onClick={() =>
                        onUpscaleEngineChange?.(option.value)
                      }
                      className={`flex flex-col items-start gap-1 rounded-xl border p-3 text-left transition-all ${isActive
                        ? "border-blue-500 bg-blue-50 shadow-sm"
                        : "border-gray-200 hover:border-blue-300 hover:bg-blue-50/60"
                        }`}
                    >
                      <span className="text-sm md:text-base font-semibold text-gray-900">
                        {option.label}
                      </span>
                    </button>
                  );
                })}
              </div>
              <p className="text-xs md:text-sm text-gray-500 mt-2 leading-snug">
                {selectedUpscaleOption.description}
              </p>
            </div>
          )}

          {method === "prompt_edit" && (
            <div className="mb-4 md:mb-6 space-y-3 md:space-y-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm md:text-base font-semibold text-gray-900">
                    输入指令
                  </h4>
                  <div className="relative">
                    <select
                      className="text-xs border border-gray-200 rounded-lg px-2 py-1 text-gray-600 focus:ring-2 focus:ring-blue-400 focus:border-blue-400"
                      defaultValue=""
                      onChange={(event) => {
                        const value = event.target.value;
                        if (value) {
                          handlePromptTemplateSelect(value);
                          event.target.selectedIndex = 0;
                        }
                      }}
                    >
                      <option value="" disabled>
                        指令参考
                      </option>
                      {promptTemplates.map((template) => (
                        <option key={template} value={template}>
                          {template}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                <textarea
                  value={promptInstruction ?? ""}
                  onChange={(event) =>
                    onPromptInstructionChange?.(event.target.value)
                  }
                  placeholder="例如：把图中裙子的颜色改成白色"
                  className="w-full min-h-[90px] md:min-h-[110px] rounded-lg md:rounded-xl border border-gray-200 px-3 py-2 md:px-4 md:py-3 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-400 resize-none"
                />
                <p className="text-xs text-gray-500 mt-2">
                  一句话描述想要修改的细节，AI会自动处理。
                </p>
              </div>
            </div>
          )}

          <div>
            <h4 className="text-sm md:text-base font-semibold text-gray-900 mb-2 md:mb-3">
              操作要求示例
            </h4>
            <div className="space-y-1 md:space-y-2">
              {info.examples.map((example, index) => (
                <div key={index} className="text-xs md:text-sm text-gray-600">
                  <span className="text-red-400">{index + 1}.</span> {example}
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="flex-1 p-4 md:p-8 order-1 md:order-2 relative overflow-y-auto">
          {/* 成功消息 toast 通知 */}
          {showSuccessToast && successMessage && !errorMessage && (
            <div className="absolute top-2 left-1/2 -translate-x-1/2 z-20 flex items-center gap-2 rounded-lg border border-green-200 bg-green-50 px-4 py-2 shadow-lg text-xs md:text-sm text-green-600 fade-in">
              <CheckCircle className="h-4 w-4 shrink-0" />
              <span>{successMessage}</span>
              <button
                type="button"
                onClick={() => setShowSuccessToast(false)}
                className="ml-1 p-0.5 rounded hover:bg-green-100 transition-colors"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          )}
          <div className="flex flex-col items-center justify-center h-full space-y-3 md:space-y-4">
            {errorMessage && (
              <div className="w-full max-w-md md:max-w-lg mx-auto rounded-lg md:rounded-xl border border-red-200 bg-red-50 px-4 py-3 md:px-6 md:py-4 text-xs md:text-sm text-red-600 text-center">
                {errorMessage}
              </div>
            )}
            {isProcessing ? (
              <div className="text-center w-full flex flex-col items-center justify-center gap-4 md:gap-6">
                <CloudLoader />
                <p className="text-gray-500 text-xs md:text-sm">
                  AI 正在处理您的图片，请稍等片刻～
                </p>
              </div>
            ) : processedImage ? (
              <div className="w-full h-full flex flex-col items-center justify-center">
                {(() => {
                  const imageUrls = processedDisplayUrls;
                  const thumbnailUrls = processedThumbnailUrls;
                  const useResultGallery =
                    method === "extract_pattern" && imageUrls.length > 1;

                  if (useResultGallery) {
                    const galleryUrls = imageUrls;
                    const safeIndex = Math.min(
                      Math.max(selectedResultIndex, 0),
                      galleryUrls.length - 1,
                    );
                    const activeUrl = galleryUrls[safeIndex];

                    return (
                      <div
                        className="flex h-full w-full flex-col gap-3 md:gap-4"
                      >
                        <div className="order-1 flex-1 flex flex-col items-center justify-center gap-3 min-h-0">
                          <ResultComparisonPanel
                            originalUrl={comparisonOriginalUrl}
                            resultUrl={activeUrl}
                            resultAlt={`处理结果图 ${safeIndex + 1}`}
                            resultIndex={safeIndex}
                            resultDownloadUrl={processedImageUrls[safeIndex] || activeUrl}
                            totalResults={galleryUrls.length}
                            thumbnailItems={galleryUrls.map((url, index) => ({
                              index,
                              previewUrl: thumbnailUrls[index] || url,
                              label: `图 ${index + 1}`,
                            }))}
                            onPreviewResult={handleProcessedImagePreview}
                            onNavigateResult={(direction) =>
                              handleNavigateResult(direction, galleryUrls.length)
                            }
                            onSelectResult={setSelectedResultIndex}
                          />
                          <div className="flex flex-wrap items-center justify-center gap-2 shrink-0">
                            <button
                              type="button"
                              onClick={() =>
                                handleDownloadSingleImage(
                                  processedImageUrls[safeIndex] || activeUrl,
                                  safeIndex,
                                )
                              }
                              disabled={isDownloadingResult}
                              className="inline-flex items-center justify-center bg-green-500 hover:bg-green-600 disabled:bg-green-400 text-white px-4 py-2 rounded-lg text-sm font-medium transition shadow disabled:opacity-70 disabled:cursor-not-allowed"
                            >
                              {isDownloadingResult
                                ? "下载中…"
                                : `下载图 ${safeIndex + 1}`}
                            </button>
                            <button
                              type="button"
                              onClick={handleBatchDownload}
                              disabled={isDownloadingResult}
                              className="inline-flex items-center justify-center bg-blue-500 hover:bg-blue-600 disabled:bg-blue-400 text-white px-5 py-2 rounded-lg text-sm font-medium transition shadow disabled:opacity-70 disabled:cursor-not-allowed"
                            >
                              {isDownloadingResult ? "下载中…" : "下载全部结果"}
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  }

                  if (imageUrls.length > 1) {
                    const safeIndex = Math.min(
                      Math.max(selectedResultIndex, 0),
                      imageUrls.length - 1,
                    );
                    const activeUrl = imageUrls[safeIndex];

                    return (
                      <div
                        className="flex h-full w-full flex-col gap-3 md:gap-4"
                      >
                        <div className="order-1 flex-1 flex flex-col items-center justify-center gap-3 min-h-0">
                          <ResultComparisonPanel
                            originalUrl={comparisonOriginalUrl}
                            resultUrl={activeUrl}
                            resultAlt={`处理结果图 ${safeIndex + 1}`}
                            resultIndex={safeIndex}
                            resultDownloadUrl={processedImageUrls[safeIndex] || activeUrl}
                            totalResults={imageUrls.length}
                            thumbnailItems={imageUrls.map((url, index) => ({
                              index,
                              previewUrl: thumbnailUrls[index] || url,
                              label: `图 ${index + 1}`,
                            }))}
                            onPreviewResult={handleProcessedImagePreview}
                            onNavigateResult={(direction) =>
                              handleNavigateResult(direction, imageUrls.length)
                            }
                            onSelectResult={setSelectedResultIndex}
                          />
                          <div className="flex flex-wrap items-center justify-center gap-2">
                            <button
                              type="button"
                              onClick={() =>
                                handleDownloadSingleImage(
                                  processedImageUrls[safeIndex] || activeUrl,
                                  safeIndex,
                                )
                              }
                              disabled={isDownloadingResult}
                              className="inline-flex items-center justify-center bg-green-500 hover:bg-green-600 disabled:bg-green-400 text-white px-3 py-1.5 rounded-md text-sm font-medium transition shadow disabled:opacity-70 disabled:cursor-not-allowed"
                            >
                              {isDownloadingResult
                                ? "下载中…"
                                : `下载图 ${safeIndex + 1}`}
                            </button>
                            <button
                              type="button"
                              onClick={handleBatchDownload}
                              disabled={isDownloadingResult}
                              className="inline-flex items-center justify-center bg-blue-500 hover:bg-blue-600 disabled:bg-blue-400 text-white px-4 py-1.5 rounded-md text-sm font-medium transition shadow disabled:opacity-70 disabled:cursor-not-allowed"
                            >
                              {isDownloadingResult ? "下载中…" : "批量下载全部"}
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  }

                  // 单张图片
                  const displayUrl = processedImageDisplay || processedImage;
                  const downloadUrl = processedImageUrls[0] || displayUrl;
                  return (
                    <div className="flex h-full w-full flex-col items-center justify-center gap-3 md:gap-4">
                      <ResultComparisonPanel
                        originalUrl={comparisonOriginalUrl}
                        resultUrl={displayUrl}
                        resultAlt="处理结果图"
                        resultDownloadUrl={downloadUrl}
                        onPreviewResult={handleProcessedImagePreview}
                      />
                      <button
                        type="button"
                        onClick={handleDownloadProcessedResult}
                        disabled={isDownloadingResult}
                        className="inline-flex items-center justify-center bg-green-500 hover:bg-green-600 disabled:bg-green-400 text-white px-6 py-2 md:px-8 md:py-3 rounded-lg md:rounded-xl font-medium transition shadow-lg disabled:opacity-70 disabled:cursor-not-allowed"
                      >
                        {isDownloadingResult ? "下载中…" : "下载结果"}
                      </button>
                    </div>
                  );
                })()}
              </div>
            ) : method === "extract_pattern" ? (
              <div className="text-center w-full flex flex-col items-center justify-center gap-4 md:gap-5">
                <picture>
                  <source
                    type="image/webp"
                    srcSet={[
                      "/optimized/tutorials/AI提取花型用法说明-768.webp 768w",
                      "/optimized/tutorials/AI提取花型用法说明-1280.webp 1280w",
                    ].join(", ")}
                    sizes="(max-width: 768px) 100vw, 1280px"
                  />
                  <img
                    src="/AI提取花型用法说明.jpg"
                    alt="AI提取花型用法说明"
                    width={1801}
                    height={1082}
                    loading="lazy"
                    decoding="async"
                    className="w-full max-w-5xl max-h-[75vh] object-contain"
                  />
                </picture>
              </div>
            ) : (
              <div className="text-center w-full flex flex-col items-center justify-center gap-4 md:gap-5">
                <CloudLoader
                  message="暂时没有任务，赶快开始吧"
                  animated={false}
                />
              </div>
            )}
          </div>
        </div>

        <div
          className={`order-3 border-l border-gray-200 bg-white transition-all duration-200 ${
            isHistoryCollapsed
              ? "w-full overflow-hidden p-2 md:w-14"
              : "w-full overflow-y-auto p-4 md:w-80 md:p-6"
          }`}
        >
          {isHistoryCollapsed ? (
            <button
              type="button"
              onClick={() => setIsHistoryCollapsed(false)}
              className="flex w-full items-center justify-center gap-2 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm font-medium text-gray-600 transition hover:border-blue-300 hover:bg-blue-50 hover:text-blue-600 md:h-full md:min-h-[140px] md:flex-col md:px-0 md:py-4"
              title="展开历史记录"
              aria-label="展开历史记录"
            >
              <ChevronLeft className="h-4 w-4" />
              <span className="md:hidden">历史记录</span>
              <span className="hidden text-xs leading-tight tracking-widest text-gray-500 [writing-mode:vertical-rl] md:inline">
                历史记录
              </span>
            </button>
          ) : (
            <>
              <div className="mb-3 flex items-center justify-between md:mb-4">
                <h3 className="flex items-center text-base font-semibold text-gray-900 md:text-lg">
                  <History className="mr-2 h-4 w-4 text-gray-600 md:h-5 md:w-5" />
                  历史记录
                </h3>
                <button
                  type="button"
                  onClick={() => setIsHistoryCollapsed(true)}
                  className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-gray-200 text-gray-500 transition hover:border-blue-300 hover:bg-blue-50 hover:text-blue-600"
                  title="收起历史记录"
                  aria-label="收起历史记录"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
              {accessToken ? (
                <HistoryList
                  accessToken={accessToken}
                  onTaskSelect={handleTaskSelect}
                  refreshToken={historyRefreshToken}
                />
              ) : (
                <div className="text-center text-gray-400 py-6 md:py-8">
                  <p className="text-xs md:text-sm">请登录后查看历史记录</p>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* 图片预览弹窗 */}
      {showImagePreview && selectedTask && (
        <ImagePreview
          task={selectedTask}
          onClose={handleClosePreview}
          accessToken={accessToken || ""}
        />
      )}

      {/* 处理结果图片预览弹窗 */}
      {processedImagePreview && (
        <ProcessedImagePreview
          image={processedImagePreview}
          onClose={handleCloseProcessedImagePreview}
          onPrev={() => handlePreviewNavigation("prev")}
          onNext={() => handlePreviewNavigation("next")}
          hasPrev={(() => {
            if (!processedDisplayUrls.length || !processedImagePreview) return false;
            const currentIndex = processedDisplayUrls.findIndex(
              (url) => url === processedImagePreview.url,
            );
            return currentIndex > 0;
          })()}
          hasNext={(() => {
            if (!processedDisplayUrls.length || !processedImagePreview) return false;
            const currentIndex = processedDisplayUrls.findIndex(
              (url) => url === processedImagePreview.url,
            );
            return (
              currentIndex !== -1 &&
              currentIndex < processedDisplayUrls.length - 1
            );
          })()}
        />
      )}

      {/* 微信二维码弹窗 */}
      {showWechatModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-lg w-80 max-w-sm shadow-2xl p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold text-gray-900">添加微信</h3>
              <button
                onClick={() => setShowWechatModal(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <p className="text-sm text-gray-600 mb-3">扫码添加微信，获取快速支持。</p>
            <div className="w-full flex justify-center">
              <img
                src="/qrcode.png"
                alt="微信二维码"
                className="w-48 h-48 object-contain"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProcessingPage;
