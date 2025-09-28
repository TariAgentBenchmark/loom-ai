export type ProcessingMethod =
  | 'seamless'
  | 'style'
  | 'embroidery'
  | 'extract_edit'
  | 'extract_pattern'
  | 'watermark_removal'
  | 'noise_removal';

export interface ProcessingOptions {
  seamless: {
    removeBackground: boolean;
    seamlessLoop: boolean;
  };
  style: {
    outputStyle: 'vector' | 'seamless';
    outputRatio: '1:1' | '2:3' | '3:2';
  };
  embroidery: {
    needleType: 'fine' | 'medium' | 'thick';
    stitchDensity: 'low' | 'medium' | 'high';
    enhanceDetails: boolean;
  };
  extract_edit: {
    voiceControl: boolean;
    editMode: 'smart' | 'manual';
  };
  extract_pattern: {
    preprocessing: boolean;
    voiceControl: boolean;
    patternType: 'floral' | 'geometric' | 'abstract';
  };
  watermark_removal: {
    watermarkType: 'text' | 'logo' | 'transparent' | 'auto';
    preserveDetail: boolean;
  };
  noise_removal: {
    noiseType: 'fabric' | 'noise' | 'blur';
    enhanceMode: 'standard' | 'vector_redraw';
  };
}

export const defaultProcessingOptions: ProcessingOptions = {
  seamless: {
    removeBackground: true,
    seamlessLoop: true,
  },
  style: {
    outputStyle: 'vector',
    outputRatio: '1:1',
  },
  embroidery: {
    needleType: 'medium',
    stitchDensity: 'medium',
    enhanceDetails: true,
  },
  extract_edit: {
    voiceControl: true,
    editMode: 'smart',
  },
  extract_pattern: {
    preprocessing: true,
    voiceControl: true,
    patternType: 'floral',
  },
  watermark_removal: {
    watermarkType: 'auto',
    preserveDetail: true,
  },
  noise_removal: {
    noiseType: 'fabric',
    enhanceMode: 'standard',
  },
};

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
      '选择去重叠区选项，避免边界重叠',
      '启用无缝循环功能，确保完美拼接',
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
      '选择输出风格（矢量/无缝循环）',
      '设置输出比例（1:1, 2:3, 3:2）',
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
      '选择针线类型（细针/中等/粗针）',
      '设置针脚密度（稀疏/中等/密集）',
      '启用增强细节纹理',
      '生成逼真的毛线刺绣效果',
    ],
  },
  extract_edit: {
    title: 'AI提取编辑',
    description: '使用AI提取和编辑图片内容，支持语音控制进行智能编辑。',
    icon: '/AI提取编辑.png',
    examples: [
      '上传需要编辑的图片',
      '启用语音控制功能',
      '选择智能编辑模式',
      '通过语音描述编辑需求',
      'AI智能完成图片编辑',
    ],
  },
  extract_pattern: {
    title: 'AI提取花型',
    description: '需预处理图片，支持用嘴改图。提取图案中的花型元素，适合设计应用。（100算力）',
    icon: '/AI提取花型.png',
    examples: [
      '上传包含花型的图片',
      '启用预处理功能',
      '选择花型类型（花卉/几何/抽象）',
      '通过语音控制调整提取',
      'AI智能提取花型元素',
    ],
  },
  watermark_removal: {
    title: 'AI智能去水印',
    description: '一键去水印。不管是顽固的文字水印、半透明logo水印，都能快捷去除。',
    icon: '/AI智能去水印.png',
    examples: [
      '上传带有水印的图片',
      '选择水印类型（文字/Logo/透明/自动）',
      '启用保留细节功能',
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
      '选择噪音类型（布纹/噪点/模糊）',
      '选择增强模式（标准/矢量重绘）',
      'AI智能去除噪点和布纹',
      '生成清晰的高质量图片',
    ],
  },
};

export const getProcessingMethodInfo = (method: ProcessingMethod) =>
  processingMethodInfo[method];
