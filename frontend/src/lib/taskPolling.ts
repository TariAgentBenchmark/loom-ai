interface TaskPollingOptions<T> {
  request: (signal: AbortSignal) => Promise<T>;
  onStatus: (value: T) => boolean; // true means the task reached a terminal state
  onError: (error: unknown, retryable: boolean) => void;
  intervalMs?: number;
  requestTimeoutMs?: number;
  maxRetryDelayMs?: number;
}

export const isRetryablePollingError = (error: unknown): boolean => {
  const status = (error as { status?: number } | null)?.status;
  return typeof status !== "number" || status < 400 || status >= 500 ||
    status === 408 || status === 429;
};

// One in-flight status request per task; cancellation also ignores late responses.
export function startTaskPolling<T>({
  request,
  onStatus,
  onError,
  intervalMs = 3000,
  requestTimeoutMs = 20000,
  maxRetryDelayMs = 15000,
}: TaskPollingOptions<T>): () => void {
  let stopped = false;
  let failures = 0;
  let timer: ReturnType<typeof setTimeout> | undefined;
  let controller: AbortController | undefined;

  const poll = async () => {
    if (stopped) return;
    const attemptController = new AbortController();
    controller = attemptController;
    let rejectAborted: () => void = () => {};
    const aborted = new Promise<never>((_, reject) => {
      rejectAborted = () => reject(new Error("状态查询暂时中断"));
      attemptController.signal.addEventListener("abort", rejectAborted, { once: true });
    });
    const timeout = setTimeout(() => attemptController.abort(), requestTimeoutMs);
    let delay = intervalMs;
    try {
      const value = await Promise.race([request(attemptController.signal), aborted]);
      if (stopped) return;
      failures = 0;
      if (onStatus(value)) stopped = true;
    } catch (error) {
      if (stopped) return;
      const retryable = isRetryablePollingError(error);
      if (!retryable) stopped = true;
      onError(error, retryable);
      failures += 1;
      delay = Math.min(maxRetryDelayMs, intervalMs * 2 ** Math.min(failures - 1, 3));
    } finally {
      clearTimeout(timeout);
      attemptController.signal.removeEventListener("abort", rejectAborted);
      if (controller === attemptController) controller = undefined;
      if (!stopped) timer = setTimeout(poll, delay);
    }
  };

  timer = setTimeout(poll, 0);
  return () => {
    stopped = true;
    if (timer !== undefined) clearTimeout(timer);
    controller?.abort();
  };
}
