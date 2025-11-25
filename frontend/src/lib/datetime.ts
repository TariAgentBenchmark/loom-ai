const DEFAULT_LOCALE = "zh-CN";
const BEIJING_TIME_ZONE = "Asia/Shanghai";

type DateInput = string | number | Date | null | undefined;

// 后端返回的时间字符串可能缺少时区信息，这里将其按 UTC 解析，再统一转换为东八区时间
const parseUtcDateString = (value: string) => {
  const trimmed = value.trim();
  if (!trimmed) return null;

  // 已包含时区信息的字符串直接交给默认解析
  const hasTimezone = /([zZ]|[+-]\d{2}:?\d{2})$/.test(trimmed);
  // 仅包含日期或日期时间（无时区）的格式，按 UTC 处理
  const isBasicDateTime = /^\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?)?$/.test(trimmed);

  if (!hasTimezone && isBasicDateTime) {
    const normalized = trimmed.replace(" ", "T") + "Z";
    const date = new Date(normalized);
    return Number.isNaN(date.getTime()) ? null : date;
  }

  return null;
};

const toDate = (value: DateInput) => {
  if (value === null || value === undefined) return null;

  if (typeof value === "string") {
    const parsedUtc = parseUtcDateString(value);
    if (parsedUtc) return parsedUtc;
  }

  const date = value instanceof Date ? value : new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
};

export const formatDateTime = (value: DateInput, options?: Intl.DateTimeFormatOptions) => {
  const date = toDate(value);
  if (!date) return typeof value === "string" && value ? value : "--";

  return date.toLocaleString(DEFAULT_LOCALE, {
    ...(options || {}),
    timeZone: BEIJING_TIME_ZONE,
  });
};
