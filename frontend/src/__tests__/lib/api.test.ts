import { splitCombinedImageRefs } from "../../lib/api";

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
