'use client';

interface BidirectionalArrowProps {
  direction?: 'horizontal' | 'vertical';
}

export function BidirectionalArrow({ direction = 'horizontal' }: BidirectionalArrowProps) {
  if (direction === 'horizontal') {
    return (
      <div className="flex items-center px-2">
        <svg width="60" height="24" viewBox="0 0 60 24" fill="none">
          {/* Left arrow */}
          <polygon points="0,12 8,8 8,16" fill="#666" />
          {/* Line */}
          <line x1="8" y1="12" x2="52" y2="12" stroke="#666" strokeWidth="2" />
          {/* Right arrow */}
          <polygon points="60,12 52,8 52,16" fill="#666" />
        </svg>
      </div>
    );
  }

  return (
    <div className="flex justify-center py-1">
      <svg width="24" height="60" viewBox="0 0 24 60" fill="none">
        {/* Up arrow */}
        <polygon points="12,0 8,8 16,8" fill="#666" />
        {/* Line */}
        <line x1="12" y1="8" x2="12" y2="52" stroke="#666" strokeWidth="2" />
        {/* Down arrow */}
        <polygon points="12,60 8,52 16,52" fill="#666" />
      </svg>
    </div>
  );
}
