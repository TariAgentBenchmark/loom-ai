import { DEFAULT_UPSCALE_ENGINE, resolvePricingServiceKey } from "@/lib/processing";

describe("upscale pricing", () => {
  it("defaults to the remaining HD algorithm", () => {
    expect(DEFAULT_UPSCALE_ENGINE).toBe("runninghub_vr2");
    expect(resolvePricingServiceKey("upscale")).toBe("upscale_runninghub_vr2");
  });

  it("preserves the 4K algorithm price", () => {
    expect(resolvePricingServiceKey("upscale", {
      upscaleEngine: "runninghub_4k_ultra",
    })).toBe("upscale_runninghub_4k_ultra");
  });
});
