import { isRetryablePollingError, startTaskPolling } from "@/lib/taskPolling";

describe("task status polling", () => {
  beforeEach(() => jest.useFakeTimers());
  afterEach(() => {
    jest.clearAllTimers();
    jest.useRealTimers();
  });

  it("retries transient failures and displays the later completed result", async () => {
    const request = jest.fn()
      .mockRejectedValueOnce(new Error("Failed to fetch"))
      .mockRejectedValueOnce({ status: 503 })
      .mockResolvedValueOnce({ status: "processing" })
      .mockResolvedValueOnce({ status: "completed", image: "result.png" });
    const onStatus = jest.fn((data) => data.status === "completed");
    const onError = jest.fn();
    const stop = startTaskPolling({ request, onStatus, onError, intervalMs: 10 });
    await jest.advanceTimersByTimeAsync(0);
    expect(onError).toHaveBeenLastCalledWith(expect.any(Error), true);
    await jest.advanceTimersByTimeAsync(100);
    expect(onStatus).toHaveBeenLastCalledWith({ status: "completed", image: "result.png" });
    expect(request).toHaveBeenCalledTimes(4);
    await jest.advanceTimersByTimeAsync(1000);
    expect(request).toHaveBeenCalledTimes(4);
    stop();
  });

  it.each([401, 403, 404])("stops on a definitive HTTP %s", async (status) => {
    const request = jest.fn().mockRejectedValue({ status });
    const onError = jest.fn();
    const stop = startTaskPolling({ request, onStatus: jest.fn(), onError });
    await jest.advanceTimersByTimeAsync(10000);
    expect(onError).toHaveBeenCalledWith({ status }, false);
    expect(request).toHaveBeenCalledTimes(1);
    stop();
  });

  it("does not overlap requests or deliver late responses after cancellation", async () => {
    let finish!: (value: string) => void;
    const request = jest.fn((_signal: AbortSignal) => new Promise<string>((resolve) => { finish = resolve; }));
    const onStatus = jest.fn();
    const stop = startTaskPolling({ request, onStatus, onError: jest.fn(), intervalMs: 10 });
    await jest.advanceTimersByTimeAsync(1000);
    expect(request).toHaveBeenCalledTimes(1);
    const signal = request.mock.calls[0][0];
    stop();
    expect(signal.aborted).toBe(true);
    finish("late-result");
    await jest.advanceTimersByTimeAsync(1000);
    expect(onStatus).not.toHaveBeenCalled();
    expect(request).toHaveBeenCalledTimes(1);
  });

  it("recovers even when a timed-out fetch ignores abort", async () => {
    const request = jest.fn()
      .mockImplementationOnce(() => new Promise(() => {}))
      .mockResolvedValueOnce("completed");
    const onStatus = jest.fn(() => true);
    const onError = jest.fn();
    const stop = startTaskPolling({
      request, onStatus, onError, intervalMs: 10, requestTimeoutMs: 20,
    });
    await jest.advanceTimersByTimeAsync(40);
    expect(request).toHaveBeenCalledTimes(2);
    expect(onError).toHaveBeenCalledWith(expect.any(Error), true);
    expect(onStatus).toHaveBeenCalledWith("completed");
    stop();
  });

  it.each([408, 429, 500, 502, 504])("retries HTTP %s", (status) => {
    expect(isRetryablePollingError({ status })).toBe(true);
  });
});
