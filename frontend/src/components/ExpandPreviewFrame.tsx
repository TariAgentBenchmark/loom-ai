'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { resolveFileUrl } from '../lib/api';

type ExpandEdgeKey = 'top' | 'bottom' | 'left' | 'right';

interface ExpandPreviewFrameProps {
  imageUrl: string;
  ratio: string;
  edges: Record<ExpandEdgeKey, string>;
  onNormalizedEdgesChange?: (edges: Record<ExpandEdgeKey, number>) => void;
}

const clampEdge = (value: string | undefined) => {
  const parsed = parseFloat(value ?? '0');
  if (!Number.isFinite(parsed) || parsed <= 0) {
    return 0;
  }
  return Math.max(0, parsed);
};

const parseRatio = (value: string) => {
  if (!value || value === 'original') {
    return null;
  }

  const parts = value.split(':').map((part) => Number(part.trim()));
  if (parts.length !== 2) {
    return null;
  }

  const [width, height] = parts;
  if (!Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0) {
    return null;
  }

  return width / height;
};

const ExpandPreviewFrame: React.FC<ExpandPreviewFrameProps> = ({
  imageUrl,
  ratio,
  edges,
  onNormalizedEdgesChange,
}) => {
  const [dimensions, setDimensions] = useState<{ width: number; height: number }>({
    width: 1,
    height: 1,
  });

  const handleImageLoad = useCallback((event: React.SyntheticEvent<HTMLImageElement>) => {
    const { naturalWidth, naturalHeight } = event.currentTarget;
    if (naturalWidth > 0 && naturalHeight > 0) {
      setDimensions({ width: naturalWidth, height: naturalHeight });
    }
  }, []);

  const { finalAspect, originalAreaStyle, canvasStyle, normalizedEdges } = useMemo(() => {
    const { width, height } = dimensions;
    const safeWidth = width > 0 ? width : 1;
    const safeHeight = height > 0 ? height : 1;
    const originalAspect = safeWidth / safeHeight;

    let top = clampEdge(edges.top);
    let bottom = clampEdge(edges.bottom);
    let left = clampEdge(edges.left);
    let right = clampEdge(edges.right);

    const targetAspect = parseRatio(ratio);
    if (targetAspect !== null) {
      if (targetAspect >= originalAspect) {
        const widthMultiplier = targetAspect / originalAspect;
        const horizontalExpansion = Math.max(0, widthMultiplier - 1);
        left = right = horizontalExpansion / 2;
        top = bottom = 0;
      } else {
        const heightMultiplier = originalAspect / targetAspect;
        const verticalExpansion = Math.max(0, heightMultiplier - 1);
        top = bottom = verticalExpansion / 2;
        left = right = 0;
      }
    }

    const safeLeft = Math.max(0, left);
    const safeRight = Math.max(0, right);
    const safeTop = Math.max(0, top);
    const safeBottom = Math.max(0, bottom);

    const totalWidthMultiplier = 1 + safeLeft + safeRight;
    const totalHeightMultiplier = 1 + safeTop + safeBottom;

    const aspect = originalAspect * (totalWidthMultiplier / totalHeightMultiplier);

    const originalWidthPercent = (1 / totalWidthMultiplier) * 100;
    const originalHeightPercent = (1 / totalHeightMultiplier) * 100;
    const offsetTopPercent = (safeTop / totalHeightMultiplier) * 100;
    const offsetLeftPercent = (safeLeft / totalWidthMultiplier) * 100;

    return {
      finalAspect: aspect || 1,
      originalAreaStyle: {
        top: `${offsetTopPercent}%`,
        left: `${offsetLeftPercent}%`,
        width: `${originalWidthPercent}%`,
        height: `${originalHeightPercent}%`,
      } as React.CSSProperties,
      canvasStyle: {
        aspectRatio: aspect || 1,
      } as React.CSSProperties,
      normalizedEdges: {
        top: safeTop,
        bottom: safeBottom,
        left: safeLeft,
        right: safeRight,
      },
    };
  }, [dimensions, edges, ratio]);

  useEffect(() => {
    if (!onNormalizedEdgesChange) {
      return;
    }
    onNormalizedEdgesChange(normalizedEdges);
  }, [normalizedEdges, onNormalizedEdgesChange]);

  const resolvedImageUrl = resolveFileUrl(imageUrl);

  const handles = [
    { key: 'tl', style: { top: 0, left: 0, transform: 'translate(-50%, -50%)' } },
    { key: 'tr', style: { top: 0, right: 0, transform: 'translate(50%, -50%)' } },
    { key: 'bl', style: { bottom: 0, left: 0, transform: 'translate(-50%, 50%)' } },
    { key: 'br', style: { bottom: 0, right: 0, transform: 'translate(50%, 50%)' } },
  ] as const;

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="w-full max-w-[260px] md:max-w-[300px] mx-auto">
        <div
          className="relative w-full border border-dashed border-gray-300/80 bg-white rounded-xl shadow-sm pointer-events-none select-none"
          style={canvasStyle}
        >
          <div className="absolute inset-0 border-2 border-dashed border-blue-400 rounded-xl bg-blue-50/50" />
          <div
            className="absolute rounded-lg shadow-sm overflow-hidden bg-white border border-white/80"
            style={originalAreaStyle}
          >
            <img
              src={resolvedImageUrl}
              alt="待扩展图片预览"
              className="w-full h-full object-contain"
              onLoad={handleImageLoad}
            />
          </div>

          {handles.map((handle) => (
            <div
              key={handle.key}
              className="absolute w-3 h-3 md:w-3.5 md:h-3.5 rounded-full border-2 border-blue-500 bg-white shadow-sm"
              style={handle.style}
            />
          ))}
        </div>
      </div>
      <div className="flex flex-col items-center text-[10px] md:text-xs text-gray-500 leading-relaxed">
        <span>蓝色框代表扩展后的画布范围</span>
        <span>
          上下左右扩展：{normalizedEdges.top.toFixed(2)} / {normalizedEdges.bottom.toFixed(2)} /{' '}
          {normalizedEdges.left.toFixed(2)} / {normalizedEdges.right.toFixed(2)}
        </span>
      </div>
    </div>
  );
};

export default ExpandPreviewFrame;
