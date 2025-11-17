export type ProcessingMethod =
  | 'prompt_edit'
  | 'style'
  | 'embroidery'
  | 'flat_to_3d'
  | 'extract_pattern'
  | 'watermark_removal'
  | 'noise_removal'
  | 'upscale'
  | 'expand_image'
  | 'seamless_loop';

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
  flat_to_3d: {
    title: 'AI平面转3D',
    description: '一键将平面花型转换为立体3D效果，鲜艳配色与精致细节同步增强，适用于布料、家居等场景展示。',
    icon: '/optimized/AI提取花型.webp',
    examples: [
      '上传需要立体化的平面图案或花型',
      '确保主体图案清晰、构图完整，避免严重压缩的图片',
      'AI自动重建立体光影与材质细节',
      '生成鲜艳色彩与精致纹理的3D视觉效果',
      '适合制作产品展示图或效果稿',
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
    title: 'AI高清',
    description: '提供双引擎高清工作流，保持图片细节并增强纹理。',
    icon: '/optimized/AI布纹去噪.webp',
    examples: [
      '上传需要放大的图片',
      '在通用1与通用2之间选择算法',
      'AI智能分析并放大图片',
      '保持原始清晰度和细节',
      '生成高质量高清图片',
    ],
  },
  expand_image: {
    title: 'AI扩图',
    description: '智能延展图片边缘，自动生成符合原图风格的内容，适合尺寸延展与电商主图设计。',
    icon: '/optimized/AI智能去水印.webp',
    examples: [
      '上传需要扩展的原图',
      '默认四个方向扩展比例为0，可按需调整至30%以内',
      '可填写提示词，引导AI生成扩展部分的风格与内容',
      '等待处理完成，下载扩展后的高清图像',
    ],
  },
  seamless_loop: {
    title: 'AI接循环',
    description: '将单张图片转换为可无缝平铺的循环图案，并生成网格预览图，便于布料与壁纸设计。',
    icon: '/optimized/AI提取花型.webp',
    examples: [
      '上传需要接循环的图片',
      '可设置拼合度与方向（四周、上下或左右）',
      '支持与扩图组合使用，扩展画布后自动接循环',
      '处理完成后可下载无缝图与网格效果图',
    ],
  },
};

export const getProcessingMethodInfo = (method: ProcessingMethod) =>
  processingMethodInfo[method];

// 定义哪些处理方法使用AI模型（支持分辨率设置）
export const AI_MODEL_METHODS: ProcessingMethod[] = [
  'prompt_edit',      // AI用嘴改图 - 使用Gemini
  'embroidery',       // AI刺绣 - 使用Gemini
  'flat_to_3d',       // AI平面转3D - 使用即梦
  'extract_pattern',  // AI提取花型 - 使用Gemini/GPT-4o
  'noise_removal',    // AI布纹去噪 - 使用Gemini
];

// 检查方法是否使用AI模型
export const isAIModelMethod = (method: ProcessingMethod): boolean => {
  return AI_MODEL_METHODS.includes(method);
};

// 允许用户自定义分辨率的处理方法
const RESOLUTION_ENABLED_METHODS: ProcessingMethod[] = ['extract_pattern'];

export const canAdjustResolution = (method: ProcessingMethod): boolean => {
  return RESOLUTION_ENABLED_METHODS.includes(method);
};
