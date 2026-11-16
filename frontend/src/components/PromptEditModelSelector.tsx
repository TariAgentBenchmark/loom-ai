"use client";

import { useRef } from "react";
import { PromptEditMode } from "../lib/processing";

interface Props {
  value: PromptEditMode;
  onChange?: (value: PromptEditMode) => void;
  disabled?: boolean;
}

export default function PromptEditModelSelector({ value, onChange, disabled = false }: Props) {
  const legacyMode = useRef<"standard" | "pro_4k">("standard");
  const isPro = value === "seedream_pro";
  if (!isPro) legacyMode.current = value;
  const style = (active: boolean) =>
    `rounded-xl border px-4 py-3 text-sm font-semibold transition-all ${active
      ? "border-blue-500 bg-blue-50 text-blue-600 shadow-sm"
      : "border-gray-200 text-gray-700 hover:border-blue-300"} disabled:opacity-50`;

  return (
    <div className="space-y-3">
      <h4 className="text-sm md:text-base font-semibold text-gray-900">模型选择</h4>
      <div className="grid grid-cols-2 gap-3">
        <button type="button" aria-pressed={!isPro} disabled={disabled}
          className={style(!isPro)} onClick={() => onChange?.(legacyMode.current)}>
          模型1
        </button>
        <button type="button" aria-pressed={isPro} disabled={disabled}
          className={style(isPro)} onClick={() => onChange?.("seedream_pro")}>
          模型pro
        </button>
      </div>
      {isPro ? (
        <p className="text-xs text-gray-500">新模型，当前实测输出2K；积分与模型1的2K模式相同。</p>
      ) : (
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-gray-700">模型1输出模式</h4>
          <div className="grid grid-cols-2 gap-3">
            {(["standard", "pro_4k"] as const).map((mode) => (
              <button key={mode} type="button" aria-pressed={value === mode}
                disabled={disabled} className={style(value === mode)}
                onClick={() => onChange?.(mode)}>
                {mode === "standard" ? "2K" : "4K"}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
