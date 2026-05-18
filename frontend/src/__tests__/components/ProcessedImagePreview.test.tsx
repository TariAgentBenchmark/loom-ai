import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import ProcessedImagePreview from "@/components/ProcessedImagePreview";

describe("ProcessedImagePreview", () => {
  it("delegates downloads to the streaming download handler", async () => {
    const image = {
      url: "/files/results/preview.png",
      filename: "result_2.png",
      downloadUrl: "results/source.png",
      index: 1,
    };
    const onDownload = jest.fn().mockResolvedValue(undefined);

    render(
      <ProcessedImagePreview
        image={image}
        onClose={jest.fn()}
        onDownload={onDownload}
      />,
    );

    fireEvent.click(screen.getByTitle("下载"));

    await waitFor(() => {
      expect(onDownload).toHaveBeenCalledWith(image);
    });
  });

  it("disables the download button when no streaming handler is provided", () => {
    render(
      <ProcessedImagePreview
        image={{
          url: "/files/results/preview.png",
          filename: "result.png",
        }}
        onClose={jest.fn()}
      />,
    );

    expect(screen.getByTitle("下载")).toBeDisabled();
  });
});
