import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import ProcessingPage from "@/components/ProcessingPage";
import { getServiceCost } from "@/lib/api";

jest.mock("@/components/HistoryList", () => () => null);
jest.mock("@/lib/api", () => ({
  ...jest.requireActual("@/lib/api"),
  getServiceCost: jest.fn().mockResolvedValue({ unit_cost: 1 }),
}));

describe("upscale options", () => {
  const renderPage = (
    upscaleEngine?: "runninghub_vr2" | "runninghub_4k_ultra",
  ) => {
    const onUpscaleEngineChange = jest.fn();
    render(
      <ProcessingPage
        method="upscale"
        imagePreview={null}
        processedImage={null}
        isProcessing={false}
        hasUploadedImage={false}
        onBack={jest.fn()}
        onOpenPricingModal={jest.fn()}
        onProcessImage={jest.fn()}
        onDragOver={jest.fn()}
        onDrop={jest.fn()}
        fileInputRef={React.createRef<HTMLInputElement>()}
        onFileInputChange={jest.fn()}
        accessToken="test-token"
        upscaleEngine={upscaleEngine}
        onUpscaleEngineChange={onUpscaleEngineChange}
      />,
    );
    return onUpscaleEngineChange;
  };

  beforeEach(() => jest.clearAllMocks());

  it("removes HD1, renames HD2 to HD and selects it by default", async () => {
    const onChange = renderPage();
    const hdButton = screen.getByRole("button", { name: "高清", exact: true });
    expect(hdButton).toHaveClass("border-blue-500");
    expect(screen.queryByRole("button", { name: /通用[12]|高清[12]/ })).not.toBeInTheDocument();

    fireEvent.click(hdButton);
    expect(onChange).toHaveBeenCalledWith("runninghub_vr2");
    fireEvent.click(screen.getByRole("button", { name: "4K超清" }));
    expect(onChange).toHaveBeenCalledWith("runninghub_4k_ultra");

    await waitFor(() => {
      expect(getServiceCost).toHaveBeenCalledWith(
        "upscale_runninghub_vr2", "test-token", 1,
        expect.objectContaining({ upscaleEngine: "runninghub_vr2" }),
      );
    });
  });

  it("keeps the 4K selection and its price", async () => {
    renderPage("runninghub_4k_ultra");
    expect(screen.getByRole("button", { name: "4K超清" })).toHaveClass("border-blue-500");
    await waitFor(() => {
      expect(getServiceCost).toHaveBeenCalledWith(
        "upscale_runninghub_4k_ultra", "test-token", 1,
        expect.objectContaining({ upscaleEngine: "runninghub_4k_ultra" }),
      );
    });
  });
});
