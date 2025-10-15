'use client';

interface ArrowProps {
  direction?: 'down' | 'right' | 'down-right';
  animated?: boolean;
  dashed?: boolean;
}

export function Arrow({ direction = 'down', animated = false, dashed = false }: ArrowProps) {
  if (direction === 'down') {
    return (
      <div className="flex justify-center py-2">
        <svg width="24" height="40" viewBox="0 0 24 40" fill="none">
          <line
            x1="12"
            y1="0"
            x2="12"
            y2="35"
            stroke="#333"
            strokeWidth="2"
            strokeDasharray={dashed ? '4 4' : '0'}
            className={animated ? 'animate-pulse' : ''}
          />
          <polygon points="12,40 8,32 16,32" fill="#333" />
        </svg>
      </div>
    );
  }

  if (direction === 'right') {
    return (
      <div className="flex items-center px-3">
        <svg width="40" height="24" viewBox="0 0 40 24" fill="none">
          <line
            x1="0"
            y1="12"
            x2="35"
            y2="12"
            stroke="#333"
            strokeWidth="2"
            strokeDasharray={dashed ? '4 4' : '0'}
            className={animated ? 'animate-pulse' : ''}
          />
          <polygon points="40,12 32,8 32,16" fill="#333" />
        </svg>
      </div>
    );
  }

  // down-right diagonal
  return (
    <div className="flex justify-center py-2">
      <svg width="60" height="60" viewBox="0 0 60 60" fill="none">
        <line
          x1="10"
          y1="10"
          x2="50"
          y2="50"
          stroke="#333"
          strokeWidth="2"
          strokeDasharray={dashed ? '4 4' : '0'}
          className={animated ? 'animate-pulse' : ''}
        />
        <polygon points="50,50 42,48 48,42" fill="#333" />
      </svg>
    </div>
  );
}
