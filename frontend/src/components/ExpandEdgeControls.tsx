"use client";

import React, { forwardRef, useEffect, useImperativeHandle, useMemo, useState } from "react";

export type ExpandEdgeKey = "top" | "bottom" | "left" | "right";

const EDGE_MIN = 0;
const EDGE_MAX_VALUES: Record<ExpandEdgeKey, number> = {
  top: 0.5,
  bottom: 0.5,
  left: 1,
  right: 1,
};
const EDGE_STEP = 0.01;
const EDGE_LARGE_STEP = 0.1;

export interface ExpandEdgeControlsHandle {
  handleNormalizedEdgesChange: (edges: Record<ExpandEdgeKey, number>) => void;
}

interface ExpandEdgeControlsProps {
  expandRatio?: string;
  onExpandRatioChange?: (value: string) => void;
  expandEdges?: Record<ExpandEdgeKey, string>;
  onExpandEdgeChange?: (edge: ExpandEdgeKey, value: string) => void;
  expandPrompt?: string;
  onExpandPromptChange?: (value: string) => void;
  isProcessing?: boolean;
  showPrompt?: boolean;
  showRatio?: boolean;
}

const clampEdgeValue = (edge: ExpandEdgeKey, value: number) =>
  Math.max(EDGE_MIN, Math.min(EDGE_MAX_VALUES[edge], value));

const ExpandEdgeControls = forwardRef<ExpandEdgeControlsHandle, ExpandEdgeControlsProps>(
  (
    {
      expandRatio,
      onExpandRatioChange,
      expandEdges,
      onExpandEdgeChange,
      expandPrompt,
      onExpandPromptChange,
      isProcessing,
      showPrompt = true,
      showRatio = true,
    },
    ref,
  ) => {
    const expandEdgeItems: { key: ExpandEdgeKey; label: string }[] = [
      { key: "top", label: "上" },
      { key: "bottom", label: "下" },
      { key: "left", label: "左" },
      { key: "right", label: "右" },
    ];
    const expandRatioOptions: { value: string; label: string }[] = [
      { value: "original", label: "原图" },
      { value: "1:1", label: "1:1" },
      { value: "3:4", label: "3:4" },
      { value: "4:3", label: "4:3" },
      { value: "16:9", label: "16:9" },
      { value: "9:16", label: "9:16" },
    ];

    const [computedPresetEdges, setComputedPresetEdges] = useState<Record<ExpandEdgeKey, string> | null>(null);
    const effectiveExpandRatio = expandRatio ?? "original";

    useEffect(() => {
      if (effectiveExpandRatio === "original") {
        setComputedPresetEdges(null);
      }
    }, [effectiveExpandRatio]);

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

    const formatEdgeValue = (edge: ExpandEdgeKey, value: number) => clampEdgeValue(edge, value).toFixed(2);

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

    const handleNormalizedEdgesChange = (edges: Record<ExpandEdgeKey, number>) => {
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
        (['top', 'bottom', 'left', 'right'] as const).forEach((edgeKey) => {
          const currentValue = edgeValues[edgeKey] ?? "0.00";
          const formattedValue = formattedValues[edgeKey];

          if (currentValue !== formattedValue) {
            onExpandEdgeChange(edgeKey, formattedValue);
          }
        });
      }
    };

    useImperativeHandle(ref, () => ({ handleNormalizedEdgesChange }));

    return (
      <div className="space-y-4">
        {showRatio && (
          <div className="space-y-3 md:space-y-4">
            <div className="flex flex-col gap-2 md:flex-row md:items-center md:gap-4">
              <h4 className="text-sm md:text-base font-semibold text-gray-900">扩图比例</h4>
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
                    disabled={isProcessing}
                    className={`px-3 py-1.5 md:px-4 md:py-2 rounded-lg border text-xs md:text-sm font-medium whitespace-nowrap flex-shrink-0 transition-all ${isActive
                      ? "border-blue-500 bg-blue-50 text-blue-600 shadow-sm"
                      : "border-gray-200 text-gray-600 hover:border-blue-300 hover:bg-blue-50/60"
                      } ${isProcessing ? "opacity-60 cursor-not-allowed" : ""}`}
                  >
                    {option.label}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        <div className="space-y-3">
          <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <h4 className="text-sm md:text-base font-semibold text-gray-900">扩展边距</h4>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs md:text-sm text-gray-600">
              {expandEdgeItems.map((edge) => {
                const displayValue = getDisplayEdgeValue(edge.key);
                return (
                  <span key={edge.key} className="flex items-center gap-1">
                    {edge.label}:
                    <span className="font-medium text-blue-600">{displayValue}</span>
                  </span>
                );
              })}
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 md:gap-4">
            {expandEdgeItems.map((edge) => {
              const parsedValue = parseEdgeValue(edge.key);
              const displayValue = getDisplayEdgeValue(edge.key);
              const canIncreaseSmall = parsedValue + EDGE_STEP <= EDGE_MAX_VALUES[edge.key] + 1e-6;
              const canDecreaseSmall = parsedValue - EDGE_STEP >= EDGE_MIN - 1e-6;
              const canIncreaseLarge = parsedValue + EDGE_LARGE_STEP <= EDGE_MAX_VALUES[edge.key] + 1e-6;
              const canDecreaseLarge = parsedValue - EDGE_LARGE_STEP >= EDGE_MIN - 1e-6;

              return (
                <div key={edge.key} className="flex flex-col gap-2">
                  <label className="text-xs md:text-sm font-medium text-gray-700">{edge.label}方向</label>
                  <div className="flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 md:px-4">
                    <span className="text-sm md:text-base font-semibold text-gray-800">{displayValue}</span>
                    <div className="flex items-center gap-3">
                      <div className="flex flex-col items-center gap-1">
                        <span className="text-[10px] leading-none text-gray-400">0.10</span>
                        <div className="flex flex-col gap-1">
                          <button
                            type="button"
                            onClick={() => adjustEdgeValue(edge.key, EDGE_LARGE_STEP)}
                            disabled={!canIncreaseLarge || isProcessing}
                            className="flex h-6 w-6 items-center justify-center rounded-full border border-blue-400 bg-white text-xs text-blue-600 hover:bg-blue-50 disabled:border-gray-200 disabled:text-gray-300 disabled:hover:bg-white transition"
                            aria-label={`${edge.label}方向增加0.10`}
                            title="增加0.10"
                          >
                            ▲
                          </button>
                          <button
                            type="button"
                            onClick={() => adjustEdgeValue(edge.key, -EDGE_LARGE_STEP)}
                            disabled={!canDecreaseLarge || isProcessing}
                            className="flex h-6 w-6 items-center justify-center rounded-full border border-blue-400 bg-white text-xs text-blue-600 hover:bg-blue-50 disabled:border-gray-200 disabled:text-gray-300 disabled:hover:bg-white transition"
                            aria-label={`${edge.label}方向减少0.10`}
                            title="减少0.10"
                          >
                            ▼
                          </button>
                        </div>
                      </div>
                      <div className="flex flex-col items-center gap-1">
                        <span className="text-[10px] leading-none text-gray-400">0.01</span>
                        <div className="flex flex-col gap-1">
                          <button
                            type="button"
                            onClick={() => adjustEdgeValue(edge.key, EDGE_STEP)}
                            disabled={!canIncreaseSmall || isProcessing}
                            className="flex h-6 w-6 items-center justify-center rounded-full border border-blue-400 bg-white text-xs text-blue-600 hover:bg-blue-50 disabled:border-gray-200 disabled:text-gray-300 disabled:hover:bg-white transition"
                            aria-label={`${edge.label}方向增加0.01`}
                            title="增加0.01"
                          >
                            ▲
                          </button>
                          <button
                            type="button"
                            onClick={() => adjustEdgeValue(edge.key, -EDGE_STEP)}
                            disabled={!canDecreaseSmall || isProcessing}
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
            上/下取值范围 0.00 - 0.50，左/右取值范围 0.00 - 1.00，表示在该方向上扩展原图边长的百分比。
          </p>
        </div>

        {showPrompt && (
          <div>
            <h4 className="text-sm md:text-base font-semibold text-gray-900 mb-2">扩图提示词（可选）</h4>
            <textarea
              value={expandPrompt ?? ""}
              onChange={(event) => onExpandPromptChange?.(event.target.value)}
              placeholder="输入希望扩展区域呈现的内容，例如：花朵、叶子、植物等"
              className="w-full min-h-[80px] md:min-h-[96px] rounded-lg md:rounded-xl border border-gray-200 px-3 py-2 md:px-4 md:py-3 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-400 resize-none"
              disabled={isProcessing}
            />
            <p className="text-xs text-gray-500 mt-2">提示词会引导AI生成扩展区域的细节，可留空以保持原图风格。</p>
          </div>
        )}
      </div>
    );
  },
);

ExpandEdgeControls.displayName = "ExpandEdgeControls";

export default ExpandEdgeControls;
