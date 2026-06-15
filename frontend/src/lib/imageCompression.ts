const MB = 1024 * 1024;

export const IMAGE_UPLOAD_HARD_LIMIT_MB = 100;
export const IMAGE_UPLOAD_TARGET_MB = 20;
export const IMAGE_UPLOAD_TARGET_MAX_DIMENSION = 4000;

export const IMAGE_UPLOAD_HARD_LIMIT_BYTES = IMAGE_UPLOAD_HARD_LIMIT_MB * MB;
export const IMAGE_UPLOAD_TARGET_BYTES = IMAGE_UPLOAD_TARGET_MB * MB;

export interface PreparedImageUpload {
  file: File;
  dimensions: { width: number; height: number } | null;
  compressed: boolean;
  originalSize: number;
}

type LoadedImage = {
  image: HTMLImageElement;
  width: number;
  height: number;
};

const loadImage = (file: File): Promise<LoadedImage> =>
  new Promise((resolve, reject) => {
    const image = new Image();
    const objectUrl = URL.createObjectURL(file);

    image.onload = () => {
      URL.revokeObjectURL(objectUrl);
      resolve({
        image,
        width: image.naturalWidth,
        height: image.naturalHeight,
      });
    };

    image.onerror = () => {
      URL.revokeObjectURL(objectUrl);
      reject(new Error("图片读取失败，请更换图片后重试"));
    };

    image.src = objectUrl;
  });

const canvasToBlob = (
  canvas: HTMLCanvasElement,
  type: string,
  quality?: number,
): Promise<Blob> =>
  new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => {
        if (!blob) {
          reject(new Error("图片压缩失败，请更换图片后重试"));
          return;
        }
        resolve(blob);
      },
      type,
      quality,
    );
  });

const hasAlphaPixels = (
  ctx: CanvasRenderingContext2D,
  width: number,
  height: number,
) => {
  try {
    const chunkHeight = 256;
    for (let y = 0; y < height; y += chunkHeight) {
      const currentHeight = Math.min(chunkHeight, height - y);
      const data = ctx.getImageData(0, y, width, currentHeight).data;
      for (let index = 3; index < data.length; index += 4) {
        if (data[index] < 255) {
          return true;
        }
      }
    }
  } catch {
    return true;
  }

  return false;
};

const filenameWithExtension = (filename: string, extension: string) => {
  const dotIndex = filename.lastIndexOf(".");
  const stem = dotIndex > 0 ? filename.slice(0, dotIndex) : filename;
  return `${stem || "image"}.${extension}`;
};

const drawImageToCanvas = (
  image: HTMLImageElement,
  width: number,
  height: number,
) => {
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;

  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  if (!ctx) {
    throw new Error("浏览器不支持图片压缩，请更换浏览器后重试");
  }

  ctx.drawImage(image, 0, 0, width, height);
  return { canvas, ctx };
};

const encodeCompressedImage = async (
  loaded: LoadedImage,
  initialScale: number,
  outputType: string,
) => {
  let scale = initialScale;
  let lastBlob: Blob | null = null;

  for (let attempt = 0; attempt < 8; attempt += 1) {
    const width = Math.max(1, Math.round(loaded.width * scale));
    const height = Math.max(1, Math.round(loaded.height * scale));
    const { canvas } = drawImageToCanvas(loaded.image, width, height);

    if (outputType === "image/png") {
      const blob = await canvasToBlob(canvas, outputType);
      lastBlob = blob;
      if (blob.size <= IMAGE_UPLOAD_TARGET_BYTES) {
        return { blob, width, height, type: blob.type || outputType };
      }
    } else {
      let bestBlob: Blob | null = null;
      let low = 0.55;
      let high = 0.92;

      for (let i = 0; i < 7; i += 1) {
        const quality = (low + high) / 2;
        const blob = await canvasToBlob(canvas, outputType, quality);
        lastBlob = blob;

        if (blob.size <= IMAGE_UPLOAD_TARGET_BYTES) {
          bestBlob = blob;
          low = quality;
        } else {
          high = quality;
        }
      }

      if (bestBlob) {
        return { blob: bestBlob, width, height, type: bestBlob.type || outputType };
      }
    }

    scale *= 0.85;
  }

  if (lastBlob && lastBlob.size <= IMAGE_UPLOAD_TARGET_BYTES) {
    return {
      blob: lastBlob,
      width: Math.max(1, Math.round(loaded.width * scale)),
      height: Math.max(1, Math.round(loaded.height * scale)),
      type: lastBlob.type || outputType,
    };
  }

  throw new Error(`图片压缩后仍超过${IMAGE_UPLOAD_TARGET_MB}MB，请换用更小的图片`);
};

export const prepareImageForUpload = async (
  file: File,
): Promise<PreparedImageUpload> => {
  if (!file.type.startsWith("image/")) {
    throw new Error("请上传有效的图片文件");
  }

  if (file.size > IMAGE_UPLOAD_HARD_LIMIT_BYTES) {
    throw new Error(`图片大小不能超过${IMAGE_UPLOAD_HARD_LIMIT_MB}MB，请重新上传。`);
  }

  if (file.type === "image/svg+xml") {
    return {
      file,
      dimensions: null,
      compressed: false,
      originalSize: file.size,
    };
  }

  const loaded = await loadImage(file);
  const dimensions = { width: loaded.width, height: loaded.height };
  const longestSide = Math.max(loaded.width, loaded.height);
  const dimensionScale = Math.min(1, IMAGE_UPLOAD_TARGET_MAX_DIMENSION / longestSide);

  if (file.size <= IMAGE_UPLOAD_TARGET_BYTES && dimensionScale >= 1) {
    return {
      file,
      dimensions,
      compressed: false,
      originalSize: file.size,
    };
  }

  const initialWidth = Math.max(1, Math.round(loaded.width * dimensionScale));
  const initialHeight = Math.max(1, Math.round(loaded.height * dimensionScale));
  const { ctx } = drawImageToCanvas(loaded.image, initialWidth, initialHeight);
  const hasAlpha = hasAlphaPixels(ctx, initialWidth, initialHeight);
  const preferredType = hasAlpha ? "image/webp" : "image/jpeg";

  let encoded = await encodeCompressedImage(loaded, dimensionScale, preferredType);
  if (preferredType === "image/webp" && encoded.blob.type !== "image/webp") {
    encoded = await encodeCompressedImage(loaded, dimensionScale, "image/png");
  }

  const extension = encoded.type === "image/webp" ? "webp" : encoded.type === "image/png" ? "png" : "jpg";
  const compressedFile = new File(
    [encoded.blob],
    filenameWithExtension(file.name, extension),
    {
      type: encoded.type,
      lastModified: Date.now(),
    },
  );

  return {
    file: compressedFile,
    dimensions: { width: encoded.width, height: encoded.height },
    compressed: true,
    originalSize: file.size,
  };
};
