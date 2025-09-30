export type ProcessingMethod =
  | 'seamless'
  | 'style'
  | 'embroidery'
  | 'extract_pattern'
  | 'watermark_removal'
  | 'noise_removal';

interface ProcessingMethodInfo {
  title: string;
  description: string;
  icon: string;
  examples: string[];
}

export const processingMethodInfo: Record<ProcessingMethod, ProcessingMethodInfo> = {
  seamless: {
    title: 'AI四方连续转换',
    description: '对独幅矩形图转换成可四方连续的打印图，如需对结果放大请用AI无缝图放大功能。',
    icon: '/AI四方连续转换.png',
    examples: [
      '上传矩形图片',
      '保持原图主体清晰，避免重要元素贴近边缘',
      '系统自动进行无缝拼接处理',
      '调整图案大小和位置',
      '生成可四方连续的打印图案',
    ],
  },
  style: {
    title: 'AI矢量化(转SVG)',
    description: '使用AI一键将图片变成矢量图，线条清晰，图片还原。助力您的产品设计。（100算力）',
    icon: '/AI矢量化转SVG.png',
    examples: [
      '上传需要矢量化的图片',
      '建议使用背景干净、线条清晰的原图',
      '系统自动分析内容并输出矢量图',
      'AI自动矢量化处理',
      '生成高质量SVG矢量图',
    ],
  },
  embroidery: {
    title: 'AI毛线刺绣增强',
    description: '针对毛线刺绣转换的针对处理，转换出的刺绣对原图主体形状保持度高，毛线感的针法。',
    icon: '/AI毛线刺绣增强.png',
    examples: [
      '上传刺绣类图片',
      '保持主体轮廓清晰、色块分明',
      '系统自动增强毛线纹理和细节',
      '生成逼真的毛线刺绣效果',
    ],
  },
  extract_pattern: {
    title: 'AI提取花型',
    description: '需预处理图片，支持用嘴改图。提取图案中的花型元素，适合设计应用。（100算力）',
    icon: '/AI提取花型.png',
    examples: [
      '上传包含花型的图片',
      '确保花型主体清晰、光线均匀',
      '系统自动提取核心花型元素',
      'AI智能提取花型元素',
    ],
  },
  watermark_removal: {
    title: 'AI智能去水印',
    description: '一键去水印。不管是顽固的文字水印、半透明logo水印，都能快捷去除。',
    icon: '/AI智能去水印.png',
    examples: [
      '上传带有水印的图片',
      '保持原图清晰，避免过度裁剪',
      '系统自动识别并去除水印',
      'AI自动识别和去除水印',
      '生成无水印的清洁图片',
    ],
  },
  noise_removal: {
    title: 'AI布纹去噪去',
    description: '使用AI快速的去除图片中的噪点、布纹。还可用于对模糊矢量花的高清重绘。（80算力）',
    icon: '/AI布纹去噪.png',
    examples: [
      '上传有噪点或布纹的图片',
      '请提供分辨率尽量高、压缩少的原图',
      '系统自动判断噪音类型并处理',
      'AI智能去除噪点和布纹',
      '生成清晰的高质量图片',
    ],
  },
};

export const getProcessingMethodInfo = (method: ProcessingMethod) =>
  processingMethodInfo[method];
