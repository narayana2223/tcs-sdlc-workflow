'use client';

interface LabeledConnectionProps {
  start: { x: number; y: number };
  end: { x: number; y: number };
  label?: string;
  type?: 'solid' | 'dashed' | 'dotted' | 'bidirectional';
  color?: string;
  animated?: boolean;
  curve?: 'straight' | 'smooth' | 'step';
}

export function LabeledConnection({
  start,
  end,
  label,
  type = 'solid',
  color = '#333',
  animated = false,
  curve = 'smooth'
}: LabeledConnectionProps) {
  // Calculate path
  const midX = (start.x + end.x) / 2;
  const midY = (start.y + end.y) / 2;

  let pathD = '';

  if (curve === 'straight') {
    pathD = `M ${start.x},${start.y} L ${end.x},${end.y}`;
  } else if (curve === 'smooth') {
    // Smooth curve with control points
    const dx = end.x - start.x;
    const dy = end.y - start.y;
    const controlOffset = Math.abs(dx) * 0.5;

    pathD = `M ${start.x},${start.y} C ${start.x + controlOffset},${start.y} ${end.x - controlOffset},${end.y} ${end.x},${end.y}`;
  } else if (curve === 'step') {
    // Step curve (right-angle)
    pathD = `M ${start.x},${start.y} L ${midX},${start.y} L ${midX},${end.y} L ${end.x},${end.y}`;
  }

  // Stroke styles
  let strokeDasharray = '0';
  if (type === 'dashed') strokeDasharray = '8,4';
  if (type === 'dotted') strokeDasharray = '2,4';

  // Arrow markers
  const markerId = `arrow-${start.x}-${start.y}-${end.x}-${end.y}`.replace(/\./g, '_');
  const markerStartId = type === 'bidirectional' ? `arrow-start-${markerId}` : undefined;

  return (
    <g className={animated ? 'animate-pulse' : ''}>
      {/* Define arrow markers */}
      <defs>
        <marker
          id={markerId}
          markerWidth="10"
          markerHeight="10"
          refX="9"
          refY="3"
          orient="auto"
          markerUnits="strokeWidth"
        >
          <path d="M0,0 L0,6 L9,3 z" fill={color} />
        </marker>
        {type === 'bidirectional' && (
          <marker
            id={markerStartId}
            markerWidth="10"
            markerHeight="10"
            refX="1"
            refY="3"
            orient="auto"
            markerUnits="strokeWidth"
          >
            <path d="M9,0 L9,6 L0,3 z" fill={color} />
          </marker>
        )}
      </defs>

      {/* Connection path */}
      <path
        d={pathD}
        fill="none"
        stroke={color}
        strokeWidth="2"
        strokeDasharray={strokeDasharray}
        markerEnd={`url(#${markerId})`}
        markerStart={type === 'bidirectional' ? `url(#${markerStartId})` : undefined}
      />

      {/* Label */}
      {label && (
        <g>
          {/* White background for label */}
          <rect
            x={midX - (label.length * 3.5)}
            y={midY - 10}
            width={label.length * 7}
            height={18}
            fill="white"
            fillOpacity="0.9"
            rx="3"
          />
          {/* Label text */}
          <text
            x={midX}
            y={midY + 4}
            textAnchor="middle"
            fontSize="11"
            fontWeight="600"
            fill={color}
            className="select-none"
          >
            {label}
          </text>
        </g>
      )}
    </g>
  );
}
