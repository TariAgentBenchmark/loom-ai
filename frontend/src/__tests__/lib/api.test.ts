import {
  createAdminTaskDownloadUrl,
  createBatchDownloadUrl,
  createBatchTask,
  createProcessingTask,
  createHistoryTaskDownloadUrl,
  createProcessingDownloadUrl,
  splitCombinedImageRefs,
} from "../../lib/api";

describe("splitCombinedImageRefs", () => {
  it("keeps x-oss-process commas inside a single preview URL", () => {
    const value =
      "https://loomai.oss-cn-beijing.aliyuncs.com/results/a.png?x-oss-process=image/resize,m_lfit,w_1600,h_1600/format,webp/quality,q_78&OSSAccessKeyId=1,https://loomai.oss-cn-beijing.aliyuncs.com/results/b.png?x-oss-process=image/resize,m_lfit,w_1600,h_1600/format,webp/quality,q_78&OSSAccessKeyId=2";

    expect(splitCombinedImageRefs(value)).toEqual([
      "https://loomai.oss-cn-beijing.aliyuncs.com/results/a.png?x-oss-process=image/resize,m_lfit,w_1600,h_1600/format,webp/quality,q_78&OSSAccessKeyId=1",
      "https://loomai.oss-cn-beijing.aliyuncs.com/results/b.png?x-oss-process=image/resize,m_lfit,w_1600,h_1600/format,webp/quality,q_78&OSSAccessKeyId=2",
    ]);
  });

  it("supports OSS object keys and local file paths", () => {
    expect(
      splitCombinedImageRefs(
        "results/2026/04/01/a.png,results/2026/04/01/b.png,/files/results/c.png",
      ),
    ).toEqual([
      "results/2026/04/01/a.png",
      "results/2026/04/01/b.png",
      "/files/results/c.png",
    ]);
  });
});

describe("createProcessingDownloadUrl", () => {
  const originalFetch = global.fetch;

  afterEach(() => {
    if (originalFetch) {
      global.fetch = originalFetch;
    } else {
      delete (global as Partial<typeof global>).fetch;
    }
    jest.restoreAllMocks();
  });

  it("creates a short-lived stream download URL for a selected result", async () => {
    const fetchMock = jest.fn().mockResolvedValue({
      ok: true,
      headers: {
        get: (name: string) =>
          name.toLowerCase() === "content-type" ? "application/json" : null,
      },
      json: async () => ({
        success: true,
        data: {
          token: "download-token",
          expiresIn: 300,
        },
        message: "下载链接创建成功",
        timestamp: "2026-05-17T00:00:00Z",
      }),
    });
    global.fetch = fetchMock;

    const url = await createProcessingDownloadUrl(
      "task_1",
      "access-token",
      "png",
      2,
    );

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining(
        "/processing/result/task_1/download-token?format=png&file_index=2",
      ),
      expect.objectContaining({ method: "POST" }),
    );
    const requestOptions = fetchMock.mock.calls[0][1] as RequestInit;
    expect((requestOptions.headers as Headers).get("Authorization")).toBe(
      "Bearer access-token",
    );
    expect(url).toContain(
      "/processing/result/task_1/stream-download?token=download-token",
    );
  });
});

describe("processing task creation", () => {
  const originalFetch = global.fetch;

  afterEach(() => {
    if (originalFetch) {
      global.fetch = originalFetch;
    } else {
      delete (global as Partial<typeof global>).fetch;
    }
    jest.restoreAllMocks();
  });

  const mockSuccessResponse = () => ({
    ok: true,
    headers: {
      get: (name: string) =>
        name.toLowerCase() === "content-type" ? "application/json" : null,
    },
    json: async () => ({
      success: true,
      data: {
        taskId: "task_1",
        batchId: "batch_1",
        status: "queued",
        estimatedTime: 120,
        creditsUsed: 1,
        totalImages: 1,
        createdAt: "2026-06-20T00:00:00Z",
      },
      message: "ok",
      timestamp: "2026-06-20T00:00:00Z",
    }),
  });

  it("defaults extract pattern tasks to the general model", async () => {
    const fetchMock = jest.fn().mockResolvedValue(mockSuccessResponse());
    global.fetch = fetchMock;

    await createProcessingTask({
      method: "extract_pattern",
      image: new File(["image"], "pattern.png", { type: "image/png" }),
      accessToken: "access-token",
    });

    const body = fetchMock.mock.calls[0][1]?.body as FormData;
    expect(body.get("pattern_type")).toBe("general");
  });

  it("defaults batch extract pattern tasks to the general model", async () => {
    const fetchMock = jest.fn().mockResolvedValue(mockSuccessResponse());
    global.fetch = fetchMock;

    await createBatchTask({
      method: "extract_pattern",
      images: [new File(["image"], "pattern.png", { type: "image/png" })],
      accessToken: "access-token",
    });

    const body = fetchMock.mock.calls[0][1]?.body as FormData;
    expect(body.get("pattern_type")).toBe("general");
  });
});

describe("streaming download URL helpers", () => {
  const originalFetch = global.fetch;

  afterEach(() => {
    if (originalFetch) {
      global.fetch = originalFetch;
    } else {
      delete (global as Partial<typeof global>).fetch;
    }
    jest.restoreAllMocks();
  });

  const mockTokenResponse = () => {
    const fetchMock = jest.fn().mockResolvedValue({
      ok: true,
      headers: {
        get: (name: string) =>
          name.toLowerCase() === "content-type" ? "application/json" : null,
      },
      json: async () => ({
        success: true,
        data: {
          token: "download-token",
          expiresIn: 300,
        },
        message: "下载链接创建成功",
        timestamp: "2026-05-17T00:00:00Z",
      }),
    });
    global.fetch = fetchMock;
    return fetchMock;
  };

  it("creates a history task stream download URL", async () => {
    const fetchMock = mockTokenResponse();

    const url = await createHistoryTaskDownloadUrl(
      "task_1",
      "access-token",
      "result",
      1,
    );

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining(
        "/history/tasks/task_1/download-token?file_type=result&file_index=1",
      ),
      expect.objectContaining({ method: "POST" }),
    );
    expect(url).toContain(
      "/history/tasks/task_1/stream-download?token=download-token",
    );
  });

  it("creates an admin task stream download URL", async () => {
    const fetchMock = mockTokenResponse();

    const url = await createAdminTaskDownloadUrl(
      "task_1",
      "admin-token",
      "original",
    );

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining(
        "/admin/tasks/task_1/download-token?file_type=original",
      ),
      expect.objectContaining({ method: "POST" }),
    );
    expect(url).toContain(
      "/admin/tasks/task_1/stream-download?token=download-token",
    );
  });

  it("creates a batch stream download URL", async () => {
    const fetchMock = mockTokenResponse();

    const url = await createBatchDownloadUrl("batch_1", "access-token");

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining(
        "/processing/batch/download/batch_1/download-token",
      ),
      expect.objectContaining({ method: "POST" }),
    );
    expect(url).toContain(
      "/processing/batch/download/batch_1/stream-download?token=download-token",
    );
  });
});
