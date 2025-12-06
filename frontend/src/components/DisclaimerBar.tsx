'use client';

import React from 'react';
import { AlertTriangle } from 'lucide-react';

const DisclaimerBar: React.FC = () => {
  return (
    <div className="fixed inset-x-0 bottom-0 z-30">
      <div className="border-t border-gray-200/80 bg-transparent backdrop-blur-[1px]">
        <div className="mx-auto flex max-w-6xl items-start gap-3 px-4 py-3 text-xs text-gray-800 md:px-6 md:py-3.5 md:text-sm">
          <AlertTriangle className="mt-[2px] h-4 w-4 flex-shrink-0 text-amber-500 md:mt-[3px] md:h-5 md:w-5" />
          <p className="leading-relaxed">
            免责声明：本站仅提供AI图片生成工具服务，用户需遵守相关法律法规，不得生成违法违规内容。
            生成的图片版权归用户所有，本站不承担任何法律责任。
          </p>
        </div>
      </div>
    </div>
  );
};

export default DisclaimerBar;
