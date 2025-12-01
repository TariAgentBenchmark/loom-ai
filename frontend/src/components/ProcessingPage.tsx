"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { History, Eye, ChevronLeft, ChevronRight } from "lucide-react";
import {
  ProcessingMethod,
  getProcessingMethodInfo,
  canAdjustResolution,
  resolvePricingServiceKey,
} from "../lib/processing";
import {
  resolveFileUrl,
  HistoryTask,
  getServiceCost,
  downloadProcessingResult,
  getPublicServicePrices,
} from "../lib/api";
import HistoryList from "./HistoryList";
import ImagePreview from "./ImagePreview";
import ProcessedImagePreview from "./ProcessedImagePreview";
import ExpandPreviewFrame from "./ExpandPreviewFrame";

type ExpandEdgeKey = "top" | "bottom" | "left" | "right";

const EDGE_MIN = 0;
const EDGE_MAX_VALUES: Record<ExpandEdgeKey, number> = {
  top: 0.5,
  bottom: 0.5,
  left: 1,
  right: 1,
};
const EDGE_STEP = 0.01;
const EDGE_LARGE_STEP = 0.1;

const clampEdgeValue = (edge: ExpandEdgeKey, value: number) =>
  Math.max(EDGE_MIN, Math.min(EDGE_MAX_VALUES[edge], value));

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

interface ProcessingPageProps {
  method: ProcessingMethod;
  imagePreview: string | null;
  secondaryImagePreview?: string | null;
  processedImage: string | null;
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
  errorMessage?: string;
  successMessage?: string;
  accessToken?: string;
  promptInstruction?: string;
  onPromptInstructionChange?: (value: string) => void;
  patternType?: string;
  onPatternTypeChange?: (value: string) => void;
  patternQuality?: "standard" | "4k";
  onPatternQualityChange?: (value: "standard" | "4k") => void;
  upscaleEngine?: "meitu_v2" | "runninghub_vr2";
  onUpscaleEngineChange?: (value: "meitu_v2" | "runninghub_vr2") => void;
  aspectRatio?: string;
  onAspectRatioChange?: (value: string) => void;
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
  historyRefreshToken?: number;
}

const ProcessingPage: React.FC<ProcessingPageProps> = ({
  method,
  imagePreview,
  secondaryImagePreview,
  processedImage,
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
  errorMessage,
  successMessage,
  accessToken,
  promptInstruction,
  onPromptInstructionChange,
  patternType,
  onPatternTypeChange,
  patternQuality,
  onPatternQualityChange,
  upscaleEngine,
  onUpscaleEngineChange,
  aspectRatio,
  onAspectRatioChange,
  expandRatio,
  onExpandRatioChange,
  expandEdges,
  onExpandEdgeChange,
  expandPrompt,
  onExpandPromptChange,
  seamDirection = 0,
  onSeamDirectionChange,
  seamFit = 0.5,
  onSeamFitChange,
  historyRefreshToken = 0,
}) => {
  const info = getProcessingMethodInfo(method);
  const [selectedTask, setSelectedTask] = useState<HistoryTask | null>(null);
  const [showImagePreview, setShowImagePreview] = useState(false);
  const [processedImagePreview, setProcessedImagePreview] = useState<{
    url: string;
    filename: string;
  } | null>(null);
  const [isDownloadingResult, setIsDownloadingResult] = useState(false);
  const [selectedResultIndex, setSelectedResultIndex] = useState(0);
  const isPromptReady =
    method !== "prompt_edit" || Boolean(promptInstruction?.trim());
  const isActionDisabled = !hasUploadedImage || isProcessing || !isPromptReady;
  const [serviceCredits, setServiceCredits] = useState<number | null>(null);
  const [isLoadingServiceCost, setIsLoadingServiceCost] = useState(true);
  const upscaleOptions: {
    value: "meitu_v2" | "runninghub_vr2";
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
    ];
  const patternQualityOptions: { value: "standard" | "4k"; label: string }[] = [
    {
      value: "standard",
      label: "普通",
    },
    {
      value: "4k",
      label: "4K",
    },
  ];
  const effectivePatternQuality = patternQuality ?? "standard";
  const selectedUpscaleOption =
    upscaleOptions.find(
      (option) => option.value === (upscaleEngine || "meitu_v2"),
    ) ?? upscaleOptions[0];
  const expandRatioOptions: { value: string; label: string }[] = [
    { value: "original", label: "原图" },
    { value: "1:1", label: "1:1" },
    { value: "3:4", label: "3:4" },
    { value: "4:3", label: "4:3" },
    { value: "16:9", label: "16:9" },
    { value: "9:16", label: "9:16" },
  ];
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
  const expandPromptValue = expandPrompt ?? "";
  const expandEdgeItems: { key: ExpandEdgeKey; label: string }[] = [
    { key: "top", label: "上" },
    { key: "bottom", label: "下" },
    { key: "left", label: "左" },
    { key: "right", label: "右" },
  ];
  const [computedPresetEdges, setComputedPresetEdges] = useState<Record<
    ExpandEdgeKey,
    string
  > | null>(null);
  const seamDirectionOptions: { value: number; label: string }[] = [
    { value: 0, label: "四周拼接" },
    { value: 1, label: "上下拼接" },
    { value: 2, label: "左右拼接" },
  ];
  const isSeamlessLoop = method === "seamless_loop";
  const isExpandImage = method === "expand_image";
  const seamFitValue = Math.max(0, Math.min(1, seamFit));
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

  useEffect(() => {
    if (effectiveExpandRatio === "original") {
      setComputedPresetEdges(null);
    }
  }, [effectiveExpandRatio]);

  const resetManualEdges = () => {
    if (!onExpandEdgeChange) return;
    onExpandEdgeChange("top", "0.00");
    onExpandEdgeChange("bottom", "0.00");
    onExpandEdgeChange("left", "0.00");
    onExpandEdgeChange("right", "0.00");
  };

  const handlePresetRatioSelect = (value: string) => {
    setComputedPresetEdges(null);
    if (value === "original") {
      onExpandRatioChange?.("original");
      resetManualEdges();
      return;
    }

    onExpandRatioChange?.(value);
    resetManualEdges();
  };
  const formatEdgeValue = (edge: ExpandEdgeKey, value: number) =>
    clampEdgeValue(edge, value).toFixed(2);

  const parseEdgeValue = (edge: ExpandEdgeKey) => {
    const parsed = parseFloat(edgeValues[edge] ?? "0");
    return Number.isFinite(parsed) ? parsed : 0;
  };

  const getDisplayEdgeValue = (edge: ExpandEdgeKey) => {
    if (effectiveExpandRatio !== "original" && computedPresetEdges) {
      return computedPresetEdges[edge] ?? "0.00";
    }
    return formatEdgeValue(edge, parseEdgeValue(edge));
  };

  const adjustEdgeValue = (edge: ExpandEdgeKey, delta: number) => {
    if (!onExpandEdgeChange) return;

    const current = parseEdgeValue(edge);
    const next = clampEdgeValue(edge, Number((current + delta).toFixed(2)));
    if (Math.abs(next - current) < 0.0001) {
      return;
    }
    onExpandEdgeChange(edge, next.toFixed(2));

    if (onExpandRatioChange && effectiveExpandRatio !== "original") {
      onExpandRatioChange("original");
      setComputedPresetEdges(null);
    }
  };

  const handleNormalizedEdgesChange = useCallback(
    (edges: Record<ExpandEdgeKey, number>) => {
      if (effectiveExpandRatio === "original") {
        return;
      }

      const formattedValues: Record<ExpandEdgeKey, string> = {
        top: clampEdgeValue("top", edges.top).toFixed(2),
        bottom: clampEdgeValue("bottom", edges.bottom).toFixed(2),
        left: clampEdgeValue("left", edges.left).toFixed(2),
        right: clampEdgeValue("right", edges.right).toFixed(2),
      };

      setComputedPresetEdges((prev) => {
        if (
          prev &&
          prev.top === formattedValues.top &&
          prev.bottom === formattedValues.bottom &&
          prev.left === formattedValues.left &&
          prev.right === formattedValues.right
        ) {
          return prev;
        }
        return formattedValues;
      });

      if (onExpandEdgeChange) {
        (["top", "bottom", "left", "right"] as const).forEach((edgeKey) => {
          const currentValue = edgeValues[edgeKey] ?? "0.00";
          const formattedValue = formattedValues[edgeKey];

          if (currentValue !== formattedValue) {
            onExpandEdgeChange(edgeKey, formattedValue);
          }
        });
      }
    },
    [effectiveExpandRatio, edgeValues, onExpandEdgeChange],
  );

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
  }, [method, accessToken, patternType, upscaleEngine]);

  useEffect(() => {
    setSelectedResultIndex(0);
  }, [processedImage, method, patternType]);

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

  const handleProcessedImagePreview = (url: string, index?: number) => {
    // 从URL中提取文件扩展名，先去除查询参数
    const cleanUrl = url.split("?")[0];
    const urlParts = cleanUrl.split("/");
    const urlFilename = urlParts[urlParts.length - 1];
    const extensionMatch = urlFilename.match(/\.[^.]+$/);
    const extension = extensionMatch ? extensionMatch[0] : ".png";

    const filename =
      index !== undefined
        ? `result_${index + 1}${extension}`
        : `result${extension}`;
    setProcessedImagePreview({ url, filename });
  };

  const handleCloseProcessedImagePreview = () => {
    setProcessedImagePreview(null);
  };

  const handlePreviewNavigation = (direction: "prev" | "next") => {
    if (!processedImage || !processedImagePreview) return;

    const urls = processedImage
      .split(",")
      .map((u) => u.trim())
      .filter(Boolean);
    const currentIndex = urls.findIndex((u) => u === processedImagePreview.url);

    if (currentIndex === -1) return;

    const newIndex = direction === "prev" ? currentIndex - 1 : currentIndex + 1;

    if (newIndex >= 0 && newIndex < urls.length) {
      handleProcessedImagePreview(urls[newIndex], newIndex);
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
    if (!processedImage) return;
    const urls = processedImage
      .split(",")
      .map((value) => value.trim())
      .filter(Boolean);
    if (!urls.length) return;

    const primaryUrl = urls[0];
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
    if (!processedImage) return;
    const urls = processedImage
      .split(",")
      .map((value) => value.trim())
      .filter(Boolean);
    if (!urls.length) return;

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
        for (let i = 0; i < urls.length; i += 1) {
          const extension = extractExtension(urls[i]);
          const filename = buildDownloadName(extension, i);
          await fetchAndDownload(urls[i], filename);
          if (i < urls.length - 1) {
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
                    <div className="space-y-2 md:space-y-4">
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
                          上传图片1
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
                    <div className="space-y-2 md:space-y-4">
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
                          上传图片2（可选）
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
                    <ExpandPreviewFrame
                      imageUrl={imagePreview}
                      ratio={effectiveExpandRatio}
                      edges={edgeValues}
                      onNormalizedEdgesChange={handleNormalizedEdgesChange}
                    />
                  ) : (
                    <div className="space-y-2 md:space-y-4">
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
                    ? `${formatCredits(serviceCredits)} 积分/次（失败不扣积分）`
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
          </div>

          {method === "expand_image" && (
            <div className="mb-4 md:mb-6 space-y-4">
              <div className="space-y-3 md:space-y-4">
                <div className="flex flex-col gap-2 md:flex-row md:items-center md:gap-4">
                  <h4 className="text-sm md:text-base font-semibold text-gray-900">
                    扩图比例
                  </h4>
                  <p className="text-xs md:text-sm text-gray-500 md:flex-1 md:text-left">
                    选择预设比例快速调整扩展框，也可手动输入边距比例。
                  </p>
                </div>
                <div className="flex items-center gap-2 md:gap-2 overflow-x-auto pb-1">
                  {expandRatioOptions.map((option) => {
                    const isActive = effectiveExpandRatio === option.value;
                    return (
                      <button
                        type="button"
                        key={option.value}
                        onClick={() => handlePresetRatioSelect(option.value)}
                        className={`px-3 py-1.5 md:px-4 md:py-2 rounded-lg border text-xs md:text-sm font-medium whitespace-nowrap flex-shrink-0 transition-all ${isActive
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

              <div className="space-y-3">
                <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                  <h4 className="text-sm md:text-base font-semibold text-gray-900">
                    扩展边距
                  </h4>
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs md:text-sm text-gray-600">
                    {expandEdgeItems.map((edge) => {
                      const displayValue = getDisplayEdgeValue(edge.key);
                      return (
                        <span
                          key={edge.key}
                          className="flex items-center gap-1"
                        >
                          {edge.label}:
                          <span className="font-medium text-blue-600">
                            {displayValue}
                          </span>
                        </span>
                      );
                    })}
                  </div>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 md:gap-4">
                  {expandEdgeItems.map((edge) => {
                    const parsedValue = parseEdgeValue(edge.key);
                    const displayValue = getDisplayEdgeValue(edge.key);
                    const canIncreaseSmall =
                      parsedValue + EDGE_STEP <=
                      EDGE_MAX_VALUES[edge.key] + 1e-6;
                    const canDecreaseSmall =
                      parsedValue - EDGE_STEP >= EDGE_MIN - 1e-6;
                    const canIncreaseLarge =
                      parsedValue + EDGE_LARGE_STEP <=
                      EDGE_MAX_VALUES[edge.key] + 1e-6;
                    const canDecreaseLarge =
                      parsedValue - EDGE_LARGE_STEP >= EDGE_MIN - 1e-6;

                    return (
                      <div key={edge.key} className="flex flex-col gap-2">
                        <label className="text-xs md:text-sm font-medium text-gray-700">
                          {edge.label}方向
                        </label>
                        <div className="flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 md:px-4">
                          <span className="text-sm md:text-base font-semibold text-gray-800">
                            {displayValue}
                          </span>
                          <div className="flex items-center gap-3">
                            <div className="flex flex-col items-center gap-1">
                              <span className="text-[10px] leading-none text-gray-400">
                                0.10
                              </span>
                              <div className="flex flex-col gap-1">
                                <button
                                  type="button"
                                  onClick={() =>
                                    adjustEdgeValue(edge.key, EDGE_LARGE_STEP)
                                  }
                                  disabled={!canIncreaseLarge}
                                  className="flex h-6 w-6 items-center justify-center rounded-full border border-blue-400 bg-white text-xs text-blue-600 hover:bg-blue-50 disabled:border-gray-200 disabled:text-gray-300 disabled:hover:bg-white transition"
                                  aria-label={`${edge.label}方向增加0.10`}
                                  title="增加0.10"
                                >
                                  ▲
                                </button>
                                <button
                                  type="button"
                                  onClick={() =>
                                    adjustEdgeValue(edge.key, -EDGE_LARGE_STEP)
                                  }
                                  disabled={!canDecreaseLarge}
                                  className="flex h-6 w-6 items-center justify-center rounded-full border border-blue-400 bg-white text-xs text-blue-600 hover:bg-blue-50 disabled:border-gray-200 disabled:text-gray-300 disabled:hover:bg-white transition"
                                  aria-label={`${edge.label}方向减少0.10`}
                                  title="减少0.10"
                                >
                                  ▼
                                </button>
                              </div>
                            </div>
                            <div className="flex flex-col items-center gap-1">
                              <span className="text-[10px] leading-none text-gray-400">
                                0.01
                              </span>
                              <div className="flex flex-col gap-1">
                                <button
                                  type="button"
                                  onClick={() =>
                                    adjustEdgeValue(edge.key, EDGE_STEP)
                                  }
                                  disabled={!canIncreaseSmall}
                                  className="flex h-6 w-6 items-center justify-center rounded-full border border-blue-400 bg-white text-xs text-blue-600 hover:bg-blue-50 disabled:border-gray-200 disabled:text-gray-300 disabled:hover:bg-white transition"
                                  aria-label={`${edge.label}方向增加0.01`}
                                  title="增加0.01"
                                >
                                  ▲
                                </button>
                                <button
                                  type="button"
                                  onClick={() =>
                                    adjustEdgeValue(edge.key, -EDGE_STEP)
                                  }
                                  disabled={!canDecreaseSmall}
                                  className="flex h-6 w-6 items-center justify-center rounded-full border border-blue-400 bg-white text-xs text-blue-600 hover:bg-blue-50 disabled:border-gray-200 disabled:text-gray-300 disabled:hover:bg-white transition"
                                  aria-label={`${edge.label}方向减少0.01`}
                                  title="减少0.01"
                                >
                                  ▼
                                </button>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
                <p className="text-xs text-gray-500">
                  上/下取值范围 0.00 - 0.50，左/右取值范围 0.00 -
                  1.00，表示在该方向上扩展原图边长的百分比。
                </p>
              </div>

              <div>
                <h4 className="text-sm md:text-base font-semibold text-gray-900 mb-2">
                  扩图提示词（可选）
                </h4>
                <textarea
                  value={expandPromptValue}
                  onChange={(event) =>
                    onExpandPromptChange?.(event.target.value)
                  }
                  placeholder="输入希望扩展区域呈现的内容，例如：花朵、叶子、植物等"
                  className="w-full min-h-[80px] md:min-h-[96px] rounded-lg md:rounded-xl border border-gray-200 px-3 py-2 md:px-4 md:py-3 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-400 resize-none"
                />
                <p className="text-xs text-gray-500 mt-2">
                  提示词会引导AI生成扩展区域的细节，可留空以保持原图风格。
                </p>
              </div>
            </div>
          )}

          {method === "seamless_loop" && (
            <div className="mb-4 md:mb-6 space-y-4">
              <div>
                <h4 className="text-sm md:text-base font-semibold text-gray-900 mb-2">
                  拼接方向
                </h4>
                <div className="flex flex-wrap gap-2">
                  {seamDirectionOptions.map((option) => {
                    const isActive = seamDirection === option.value;
                    return (
                      <button
                        type="button"
                        key={option.value}
                        onClick={() => onSeamDirectionChange?.(option.value)}
                        className={`px-3 py-1.5 md:px-4 md:py-2 rounded-full border text-xs md:text-sm font-medium transition-all ${isActive
                          ? "border-blue-500 bg-blue-50 text-blue-600 shadow-sm"
                          : "border-gray-200 text-gray-600 hover:border-blue-300 hover:bg-blue-50/60"
                          }`}
                      >
                        {option.label}
                      </button>
                    );
                  })}
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  选择需要保持无缝的方向，默认处理四周接缝，也可仅调整单向拼接效果。
                </p>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm md:text-base font-semibold text-gray-900">
                    接缝拟合度
                  </h4>
                  <span className="text-xs md:text-sm font-medium text-blue-600">
                    {seamFitValue.toFixed(2)}
                  </span>
                </div>
                <input
                  type="range"
                  min={0}
                  max={1}
                  step={0.05}
                  value={seamFitValue}
                  onChange={(event) =>
                    onSeamFitChange?.(parseFloat(event.target.value))
                  }
                  className="w-full accent-blue-500"
                />
                <p className="text-xs text-gray-500 mt-2">
                  当原图拼合差异较大时，可以调大此参数加强过渡；若需要保留细节，可适当调小。
                </p>
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
              <select
                value={patternType || "general1"}
                onChange={(event) => onPatternTypeChange?.(event.target.value)}
                className="w-full rounded-lg md:rounded-xl border border-gray-200 px-3 py-2 md:px-4 md:py-3 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-400"
              >
                <option value="general1">通用1</option>
                <option value="general2">通用2</option>
                <option value="positioning">线条/矢量</option>
                <option value="fine">烫画/胸前花</option>
              </select>
            </div>
          )}

          {method === "extract_pattern" && patternType === "general2" && (
            <div className="mb-4 md:mb-6">
              <h4 className="text-sm md:text-base font-semibold text-gray-900 mb-2">
                清晰度模式
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {patternQualityOptions.map((option) => {
                  const isActive = effectivePatternQuality === option.value;
                  return (
                    <button
                      type="button"
                      key={option.value}
                      onClick={() => onPatternQualityChange?.(option.value)}
                      className={`flex flex-col items-start gap-1 rounded-xl border p-3 text-left transition-all ${isActive
                        ? "border-blue-500 bg-blue-50 shadow-sm"
                        : "border-gray-200 hover:border-blue-300 hover:bg-blue-50/60"
                        }`}
                    >
                      <span className="text-sm md:text-base font-semibold text-gray-900 flex items-center gap-2">
                        {option.label}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {method === "upscale" && (
            <div className="mb-4 md:mb-6">
              <h4 className="text-sm md:text-base font-semibold text-gray-900 mb-2">
                高清算法
              </h4>
              <select
                value={upscaleEngine || "meitu_v2"}
                onChange={(event) =>
                  onUpscaleEngineChange?.(
                    event.target.value as "meitu_v2" | "runninghub_vr2",
                  )
                }
                className="w-full rounded-lg md:rounded-xl border border-gray-200 px-3 py-2 md:px-4 md:py-3 text-sm md:text-base text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-400"
              >
                {upscaleOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <p className="text-xs md:text-sm text-gray-500 mt-2 leading-snug">
                {selectedUpscaleOption.description}
              </p>
            </div>
          )}

          {/* 分辨率选择 - 仅在AI提取花型的通用2模式下显示 */}
          {canAdjustResolution(method) && patternType === "general2" && (
            <div className="mb-4 md:mb-6">
              <h4 className="text-sm md:text-base font-semibold text-gray-900 mb-2">
                分辨率设置
              </h4>

              {/* 预设比例选择 */}
              <div>
                <label className="text-xs text-gray-600 mb-1 block">
                  选择比例
                </label>
                <select
                  value={aspectRatio || ""}
                  onChange={(event) =>
                    onAspectRatioChange?.(event.target.value)
                  }
                  className="w-full rounded-lg md:rounded-xl border border-gray-200 px-3 py-2 md:px-4 md:py-3 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-400"
                >
                  <option value="">自动（保持原图比例）</option>
                  <option value="21:9">21:9 超宽屏</option>
                  <option value="16:9">16:9 宽屏</option>
                  <option value="4:3">4:3 标准</option>
                  <option value="3:2">3:2 经典</option>
                  <option value="1:1">1:1 正方形</option>
                  <option value="9:16">9:16 竖屏</option>
                  <option value="3:4">3:4 竖屏</option>
                  <option value="2:3">2:3 竖屏</option>
                  <option value="5:4">5:4 特殊</option>
                  <option value="4:5">4:5 特殊</option>
                </select>
                <p className="text-xs text-gray-500 mt-2">
                  选择预设比例，AI将按选定比例生成图片
                </p>
              </div>
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

          <div className="mb-4 md:mb-6">
            <h4 className="text-sm md:text-base font-semibold text-gray-900 mb-2 md:mb-3">
              使用提示
            </h4>
            <p className="text-xs md:text-sm text-gray-600 mb-3 md:mb-4">
              {info.description}
            </p>
          </div>

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

        <div className="flex-1 p-4 md:p-8 order-1 md:order-2">
          <div className="flex flex-col items-center justify-center h-full space-y-3 md:space-y-4">
            {errorMessage && (
              <div className="w-full max-w-md md:max-w-lg rounded-lg md:rounded-xl border border-red-200 bg-red-50 px-4 py-3 md:px-6 md:py-4 text-xs md:text-sm text-red-600">
                {errorMessage}
              </div>
            )}
            {successMessage && !errorMessage && (
              <div className="w-full max-w-md md:max-w-lg rounded-lg md:rounded-xl border border-green-200 bg-green-50 px-4 py-3 md:px-6 md:py-4 text-xs md:text-sm text-green-600">
                {successMessage}
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
              <div className="text-center w-full h-full flex flex-col items-center justify-center">
                {(() => {
                  const imageUrls = processedImage
                    .split(",")
                    .map((value) => value.trim())
                    .filter(Boolean);
                  const useGeneralGallery =
                    method === "extract_pattern" &&
                    patternType === "general1" &&
                    imageUrls.length > 0;

                  const shouldOffsetPreview = Boolean(
                    successMessage && !errorMessage,
                  );
                  if (useGeneralGallery) {
                    const galleryUrls = imageUrls.slice(0, 4);
                    const safeIndex = Math.min(
                      Math.max(selectedResultIndex, 0),
                      galleryUrls.length - 1,
                    );
                    const activeUrl = galleryUrls[safeIndex];

                    return (
                      <div
                        className={`flex flex-col md:flex-row gap-4 md:gap-6 w-full max-w-5xl ${shouldOffsetPreview ? "mt-4 md:mt-6" : ""
                          }`}
                      >
                        <div className="flex md:flex-col gap-3 md:w-32 w-full md:flex-none overflow-x-auto md:overflow-visible">
                          {galleryUrls.map((url, index) => {
                            const isActive = index === safeIndex;
                            return (
                              <button
                                key={url + index}
                                type="button"
                                onClick={() => setSelectedResultIndex(index)}
                                className={`flex flex-col items-center rounded-lg border px-2 py-2 text-xs md:text-sm transition ${isActive
                                  ? "border-blue-500 bg-blue-50 shadow-sm"
                                  : "border-gray-200 hover:border-blue-300 hover:bg-gray-50"
                                  }`}
                                title={`查看图 ${index + 1}`}
                              >
                                <div className="w-16 h-24 md:w-20 md:h-28 rounded-md overflow-hidden border border-dashed border-gray-200 bg-white flex items-center justify-center mb-1">
                                  <img
                                    src={resolveFileUrl(url)}
                                    alt={`图 ${index + 1} 缩略图`}
                                    className="w-full h-full object-cover"
                                  />
                                </div>
                                <span className="font-medium text-gray-700">
                                  图 {index + 1}
                                </span>
                              </button>
                            );
                          })}
                        </div>

                        <div className="flex-1 flex flex-col items-center justify-center gap-4">
                          <div className="relative group w-full flex justify-center">
                            <img
                              src={resolveFileUrl(activeUrl)}
                              alt={`处理结果图 ${safeIndex + 1}`}
                              className="max-w-[95%] max-h-[75vh] w-auto h-auto object-contain rounded-xl border border-gray-200 shadow-lg cursor-pointer hover:shadow-xl transition-shadow"
                              onClick={() =>
                                handleProcessedImagePreview(
                                  activeUrl,
                                  safeIndex,
                                )
                              }
                            />
                            <button
                              onClick={() =>
                                handleProcessedImagePreview(
                                  activeUrl,
                                  safeIndex,
                                )
                              }
                              className="absolute top-2 right-2 p-2 bg-black bg-opacity-50 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity hover:bg-opacity-70"
                              title="放大查看"
                            >
                              <Eye className="h-4 w-4" />
                            </button>
                            {galleryUrls.length > 1 && (
                              <>
                                <button
                                  type="button"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleNavigateResult(-1, galleryUrls.length);
                                  }}
                                  className="absolute left-2 top-1/2 -translate-y-1/2 p-2 rounded-full bg-black bg-opacity-40 text-white hover:bg-opacity-70 transition"
                                  title="上一张"
                                >
                                  <ChevronLeft className="h-5 w-5" />
                                </button>
                                <button
                                  type="button"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleNavigateResult(1, galleryUrls.length);
                                  }}
                                  className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-full bg-black bg-opacity-40 text-white hover:bg-opacity-70 transition"
                                  title="下一张"
                                >
                                  <ChevronRight className="h-5 w-5" />
                                </button>
                              </>
                            )}
                          </div>
                          <div className="flex flex-wrap items-center justify-center gap-3">
                            <button
                              type="button"
                              onClick={() =>
                                handleDownloadSingleImage(activeUrl, safeIndex)
                              }
                              disabled={isDownloadingResult}
                              className="inline-flex items-center justify-center bg-green-500 hover:bg-green-600 disabled:bg-green-400 text-white px-4 py-2 rounded-lg text-sm font-medium transition shadow-lg disabled:opacity-70 disabled:cursor-not-allowed"
                            >
                              {isDownloadingResult
                                ? "下载中…"
                                : `下载图 ${safeIndex + 1}`}
                            </button>
                            <button
                              type="button"
                              onClick={handleBatchDownload}
                              disabled={isDownloadingResult}
                              className="inline-flex items-center justify-center bg-blue-500 hover:bg-blue-600 disabled:bg-blue-400 text-white px-5 py-2 rounded-lg text-sm font-medium transition shadow-lg disabled:opacity-70 disabled:cursor-not-allowed"
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
                        className={`flex flex-col md:flex-row gap-4 md:gap-6 w-full max-w-5xl ${shouldOffsetPreview ? "mt-4 md:mt-6" : ""
                          }`}
                      >
                        <div className="flex md:flex-col gap-3 md:w-32 w-full md:flex-none overflow-x-auto md:overflow-visible">
                          {imageUrls.map((url, index) => {
                            const isActive = index === safeIndex;
                            return (
                              <button
                                key={url + index}
                                type="button"
                                onClick={() => setSelectedResultIndex(index)}
                                className={`flex flex-col items-center rounded-lg border px-2 py-2 text-xs md:text-sm transition ${isActive
                                  ? "border-blue-500 bg-blue-50 shadow-sm"
                                  : "border-gray-200 hover:border-blue-300 hover:bg-gray-50"
                                  }`}
                                title={`查看图 ${index + 1}`}
                              >
                                <div className="w-16 h-24 md:w-20 md:h-28 rounded-md overflow-hidden border border-dashed border-gray-200 bg-white flex items-center justify-center mb-1">
                                  <img
                                    src={resolveFileUrl(url)}
                                    alt={`图 ${index + 1} 缩略图`}
                                    className="w-full h-full object-cover"
                                  />
                                </div>
                                <span className="font-medium text-gray-700">
                                  图 {index + 1}
                                </span>
                              </button>
                            );
                          })}
                        </div>

                        <div className="flex-1 flex flex-col items-center justify-center gap-4">
                          <div className="relative group w-full flex justify-center">
                            <img
                              src={resolveFileUrl(activeUrl)}
                              alt={`处理结果图 ${safeIndex + 1}`}
                              className="max-w-[95%] max-h-[75vh] w-auto h-auto object-contain rounded-xl border border-gray-200 shadow-lg cursor-pointer hover:shadow-xl transition-shadow"
                              onClick={() =>
                                handleProcessedImagePreview(
                                  activeUrl,
                                  safeIndex,
                                )
                              }
                            />
                            <button
                              onClick={() =>
                                handleProcessedImagePreview(
                                  activeUrl,
                                  safeIndex,
                                )
                              }
                              className="absolute top-2 right-2 p-2 bg-black bg-opacity-50 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity hover:bg-opacity-70"
                              title="放大查看"
                            >
                              <Eye className="h-4 w-4" />
                            </button>
                            {imageUrls.length > 1 && (
                              <>
                                <button
                                  type="button"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleNavigateResult(-1, imageUrls.length);
                                  }}
                                  className="absolute left-2 top-1/2 -translate-y-1/2 p-2 rounded-full bg-black bg-opacity-40 text-white hover:bg-opacity-70 transition"
                                  title="上一张"
                                >
                                  <ChevronLeft className="h-5 w-5" />
                                </button>
                                <button
                                  type="button"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleNavigateResult(1, imageUrls.length);
                                  }}
                                  className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-full bg-black bg-opacity-40 text-white hover:bg-opacity-70 transition"
                                  title="下一张"
                                >
                                  <ChevronRight className="h-5 w-5" />
                                </button>
                              </>
                            )}
                          </div>
                          <div className="flex flex-wrap items-center justify-center gap-3">
                            <button
                              type="button"
                              onClick={() =>
                                handleDownloadSingleImage(activeUrl, safeIndex)
                              }
                              disabled={isDownloadingResult}
                              className="inline-flex items-center justify-center bg-green-500 hover:bg-green-600 disabled:bg-green-400 text-white px-4 py-2 rounded-lg text-sm font-medium transition shadow-lg disabled:opacity-70 disabled:cursor-not-allowed"
                            >
                              {isDownloadingResult
                                ? "下载中…"
                                : `下载图 ${safeIndex + 1}`}
                            </button>
                            <button
                              type="button"
                              onClick={handleBatchDownload}
                              disabled={isDownloadingResult}
                              className="inline-flex items-center justify-center bg-blue-500 hover:bg-blue-600 disabled:bg-blue-400 text-white px-6 py-2 md:px-8 md:py-3 rounded-lg md:rounded-xl font-medium transition shadow-lg disabled:opacity-70 disabled:cursor-not-allowed"
                            >
                              {isDownloadingResult ? "下载中…" : "批量下载全部"}
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  }

                  // 单张图片
                  return (
                    <>
                      <div className="relative group mb-4 md:mb-6 w-full flex justify-center">
                        <div className="w-full max-w-5xl h-[60vh] md:h-[70vh] flex items-center justify-center">
                          {(() => {
                            const resolvedUrl = resolveFileUrl(processedImage);
                            console.log(
                              "ProcessingPage: Displaying processed image",
                              {
                                originalUrl: processedImage,
                                resolvedUrl,
                                isSvg: processedImage
                                  .toLowerCase()
                                  .includes(".svg"),
                              },
                            );

                            // 检查是否是SVG文件
                            if (processedImage.toLowerCase().includes(".svg")) {
                              console.log(
                                "ProcessingPage: Detected SVG file, using <img> tag",
                              );
                              return (
                                <img
                                  src={resolvedUrl}
                                  alt="Processed SVG"
                                  className="w-auto h-auto max-w-full max-h-full object-contain rounded-lg border border-gray-200 shadow-lg cursor-pointer hover:shadow-xl transition-shadow"
                                  onClick={() =>
                                    handleProcessedImagePreview(processedImage)
                                  }
                                  onLoad={() =>
                                    console.log(
                                      "ProcessingPage: SVG loaded successfully",
                                    )
                                  }
                                  onError={(e) =>
                                    console.error(
                                      "ProcessingPage: SVG failed to load",
                                      e,
                                    )
                                  }
                                />
                              );
                            }

                            return (
                              <img
                                src={resolvedUrl}
                                alt="Processed"
                                className="w-full h-full object-contain rounded-lg border border-gray-200 shadow-lg cursor-pointer hover:shadow-xl transition-shadow"
                                onClick={() =>
                                  handleProcessedImagePreview(processedImage)
                                }
                                onLoad={() =>
                                  console.log(
                                    "ProcessingPage: Image loaded successfully",
                                  )
                                }
                                onError={(e) =>
                                  console.error(
                                    "ProcessingPage: Image failed to load",
                                    e,
                                  )
                                }
                              />
                            );
                          })()}
                        </div>
                        <button
                          onClick={() =>
                            handleProcessedImagePreview(processedImage)
                          }
                          className="absolute top-2 right-2 p-2 bg-black bg-opacity-50 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity hover:bg-opacity-70"
                          title="放大查看"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                      </div>
                      <button
                        type="button"
                        onClick={handleDownloadProcessedResult}
                        disabled={isDownloadingResult}
                        className="inline-flex items-center justify-center bg-green-500 hover:bg-green-600 disabled:bg-green-400 text-white px-6 py-2 md:px-8 md:py-3 rounded-lg md:rounded-xl font-medium transition shadow-lg disabled:opacity-70 disabled:cursor-not-allowed"
                      >
                        {isDownloadingResult ? "下载中…" : "下载结果"}
                      </button>
                    </>
                  );
                })()}
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

        <div className="w-full md:w-80 bg-white border-l border-gray-200 p-4 md:p-6 overflow-y-auto order-3">
          <h3 className="text-base md:text-lg font-semibold text-gray-900 mb-3 md:mb-4 flex items-center">
            <History className="h-4 w-4 md:h-5 md:w-5 mr-2 text-gray-600" />
            历史记录
          </h3>
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
            if (!processedImage || !processedImagePreview) return false;
            const urls = processedImage
              .split(",")
              .map((u) => u.trim())
              .filter(Boolean);
            const currentIndex = urls.findIndex(
              (u) => u === processedImagePreview.url,
            );
            return currentIndex > 0;
          })()}
          hasNext={(() => {
            if (!processedImage || !processedImagePreview) return false;
            const urls = processedImage
              .split(",")
              .map((u) => u.trim())
              .filter(Boolean);
            const currentIndex = urls.findIndex(
              (u) => u === processedImagePreview.url,
            );
            return currentIndex !== -1 && currentIndex < urls.length - 1;
          })()}
        />
      )}
    </div>
  );
};

export default ProcessingPage;
