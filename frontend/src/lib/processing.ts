export type ProcessingMethod =
  | 'prompt_edit'
  | 'style'
  | 'embroidery'
  | 'extract_pattern'
  | 'watermark_removal'
  | 'noise_removal'
  | 'upscale';

interface ProcessingMethodInfo {
  title: string;
  description: string;
  icon: string;
  examples: string[];
}

export const processingMethodInfo: Record<ProcessingMethod, ProcessingMethodInfo> = {
  prompt_edit: {
    title: 'AI用嘴改图',
    description: '上传需要修改的图片，输入一句中文指令即可完成智能修图，快速得到前后对比效果。',
    icon: '/optimized/AI用嘴改图.webp',
    examples: [
      '上传需要修改的图片（支持JPG/PNG，推荐小于5MB）',
      '确保图片主体清晰，避免重要元素被裁切',
      '用一句话描述想要修改的细节，例如“把裙子换成白色”',
      '点击开始处理，等待AI返回修改后的图片',
      '下载或查看处理前后的对比效果',
    ],
  },
  style: {
    title: 'AI矢量化(转SVG)',
    description: '使用AI一键将图片变成矢量图，线条清晰，图片还原。助力您的产品设计。',
    icon: '/optimized/AI矢量化转SVG.webp',
    examples: [
      '上传需要矢量化的图片',
      '建议使用背景干净、线条清晰的原图',
      '系统自动分析内容并输出矢量图',
      'AI自动矢量化处理',
      '生成高质量SVG矢量图',
    ],
  },
  embroidery: {
    title: 'AI刺绣',
    description: '使用AI技术进行刺绣增强，支持4K超高清输出，提供更真实的质感和精细的针脚效果。',
    icon: '/optimized/AI毛线刺绣增强.webp',
    examples: [
      '上传需要刺绣增强的图片',
      '支持多种图片格式，建议使用高分辨率图片',
      'AI智能分析图片内容',
      '生成高质量刺绣效果图',
      '支持4K超高清输出，细节更丰富',
    ],
  },
  extract_pattern: {
    title: 'AI提取花型',
    description: '自动提取花型并进行高清增强，适合设计应用。',
    icon: '/optimized/AI提取花型.webp',
    examples: [
      '上传包含花型的图片',
      '确保花型主体清晰、光线均匀',
      '系统自动提取核心花型元素并生成高清增强图案',
      'AI智能提取花型元素',
    ],
  },
  watermark_removal: {
    title: 'AI智能去水印',
    description: '一键去水印。不管是顽固的文字水印、半透明logo水印，都能快捷去除。',
    icon: '/optimized/AI智能去水印.webp',
    examples: [
      '上传带有水印的图片',
      '保持原图清晰，避免过度裁剪',
      '系统自动识别并去除水印',
      'AI自动识别和去除水印',
      '生成无水印的清洁图片',
    ],
  },
  noise_removal: {
    title: 'AI布纹去噪',
    description: '使用AI快速的去除图片中的噪点、布纹。还可用于对模糊矢量花的高清重绘。',
    icon: '/optimized/进一步处理.webp',
    examples: [
      '上传有噪点或布纹的图片',
      '请提供分辨率尽量高、压缩少的原图',
      '系统自动判断噪音类型并处理',
      'AI智能去除噪点和布纹',
      '生成清晰的高质量图片',
    ],
  },
  upscale: {
    title: 'AI无损放大',
    description: '使用AI技术对图片进行无损放大，最高支持8K分辨率，保持图片清晰度和细节。',
    icon: '/optimized/AI布纹去噪.webp',
    examples: [
      '上传需要放大的图片',
      '选择放大倍数或自定义尺寸',
      'AI智能分析并放大图片',
      '保持原始清晰度和细节',
      '生成高质量放大图片',
    ],
  },
};

export const getProcessingMethodInfo = (method: ProcessingMethod) =>
  processingMethodInfo[method];
