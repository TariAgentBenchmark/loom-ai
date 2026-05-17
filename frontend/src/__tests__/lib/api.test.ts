import { downloadTaskFile, splitCombinedImageRefs } from "../../lib/api";

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

describe("downloadTaskFile", () => {
  const originalFetch = global.fetch;

  afterEach(() => {
    if (originalFetch) {
      global.fetch = originalFetch;
    } else {
      delete (global as Partial<typeof global>).fetch;
    }
    jest.restoreAllMocks();
  });

  it("passes a result index when downloading the current image", async () => {
    const fetchMock = jest.fn().mockResolvedValue({
      ok: true,
      url: "http://localhost/api/v1/history/tasks/task_1/download?file_type=result&file_index=2",
      headers: {
        get: (name: string) => {
          if (name.toLowerCase() === "content-disposition") {
            return 'attachment; filename="tuyun.png"';
          }
          return null;
        },
      },
      blob: async () => new Blob(["image"]),
    });
    global.fetch = fetchMock;

    const result = await downloadTaskFile("task_1", "token", "result", 2);

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/history/tasks/task_1/download?file_type=result&file_index=2"),
      expect.objectContaining({ method: "GET" }),
    );
    const requestOptions = fetchMock.mock.calls[0][1] as RequestInit;
    expect((requestOptions.headers as Headers).get("Authorization")).toBe(
      "Bearer token",
    );
    expect(result.filename).toBe("tuyun.png");
  });
});
