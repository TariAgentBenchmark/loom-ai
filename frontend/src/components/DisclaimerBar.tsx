'use client';

import React from 'react';
import { AlertTriangle } from 'lucide-react';

const DisclaimerBar: React.FC = () => {
  return (
    <div className="w-full border-t border-gray-200/80 bg-gray-50/50">
      <div className="mx-auto flex max-w-6xl items-start gap-3 px-4 py-3 text-xs text-gray-600 md:px-6 md:py-3.5 md:text-sm">
        <AlertTriangle className="mt-[2px] h-4 w-4 flex-shrink-0 text-amber-500 md:mt-[3px] md:h-5 md:w-5" />
        <p className="leading-relaxed">
          免责声明：本站仅提供AI图片生成工具服务，用户需遵守相关法律法规，不得生成违法违规内容。
          生成的图片版权归用户所有，本站不承担任何法律责任。
        </p>
      </div>
    </div>
  );
};

export default DisclaimerBar;
