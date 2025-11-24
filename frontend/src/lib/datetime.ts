const DEFAULT_LOCALE = "zh-CN";
const BEIJING_TIME_ZONE = "Asia/Shanghai";

type DateInput = string | number | Date | null | undefined;

const toDate = (value: DateInput) => {
  if (value === null || value === undefined) return null;

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
