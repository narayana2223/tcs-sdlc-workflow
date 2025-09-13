/**
 * Visualization Utilities
 * Helper functions for D3.js charts and data transformations
 */

import * as d3 from 'd3';

// Color Schemes
export const colorSchemes = {
  primary: [
    '#1976d2', '#1565c0', '#0d47a1', '#42a5f5', '#64b5f6',
    '#90caf9', '#bbdefb', '#e3f2fd'
  ],
  success: [
    '#4caf50', '#388e3c', '#2e7d32', '#1b5e20', '#66bb6a',
    '#81c784', '#a5d6a7', '#c8e6c9'
  ],
  warning: [
    '#ff9800', '#f57c00', '#ef6c00', '#e65100', '#ffb74d',
    '#ffcc02', '#ffd54f', '#ffe082'
  ],
  error: [
    '#f44336', '#d32f2f', '#c62828', '#b71c1c', '#ef5350',
    '#e57373', '#ef9a9a', '#ffcdd2'
  ],
  neutral: [
    '#9e9e9e', '#757575', '#616161', '#424242', '#bdbdbd',
    '#e0e0e0', '#eeeeee', '#f5f5f5'
  ],
  technology: [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57',
    '#FF9FF3', '#54A0FF', '#5F27CD', '#00D2D3', '#FF9F43',
    '#10AC84', '#EE5A24', '#0ABDE3', '#C44569', '#FD79A8'
  ]
};

// Chart Dimensions and Margins
export const chartDimensions = {
  small: { width: 300, height: 200, margin: { top: 20, right: 20, bottom: 30, left: 40 } },
  medium: { width: 500, height: 350, margin: { top: 30, right: 30, bottom: 50, left: 60 } },
  large: { width: 800, height: 500, margin: { top: 40, right: 40, bottom: 80, left: 80 } },
  radar: { width: 400, height: 400, margin: { top: 50, right: 50, bottom: 50, left: 50 } }
};

// Data Transformation Functions
export const transformData = {
  /**
   * Transform technology stack data for pie chart
   */
  technologyStackToPie: (technologies: Record<string, number>) => {
    return Object.entries(technologies)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value);
  },

  /**
   * Transform factor evaluations to radar chart data
   */
  factorsToRadar: (factors: Record<string, any>) => {
    return Object.entries(factors).map(([key, factor]) => ({
      axis: factor.title || key.replace(/_/g, ' ').toUpperCase(),
      value: factor.score * 100,
      compliant: factor.compliant,
      confidence: factor.confidence * 100
    }));
  },

  /**
   * Transform gaps data for heatmap
   */
  gapsToHeatmap: (gaps: any[]) => {
    const severityMap = { low: 1, medium: 2, high: 3, critical: 4 };
    const impactMap = { low: 1, medium: 2, high: 3 };
    
    return gaps.map(gap => ({
      factor: gap.factor_name,
      severity: severityMap[gap.severity as keyof typeof severityMap] || 1,
      impact: impactMap[gap.impact as keyof typeof impactMap] || 1,
      description: gap.description,
      effort: gap.effort_estimate
    }));
  },

  /**
   * Transform components for dependency graph
   */
  componentsToDependencyGraph: (components: any[]) => {
    const nodes = components.map((comp, index) => ({
      id: comp.name,
      group: comp.type,
      complexity: comp.complexity,
      dependencies: comp.dependencies?.length || 0,
      index
    }));

    const links: any[] = [];
    components.forEach(comp => {
      comp.dependencies?.forEach((dep: string) => {
        const target = components.find(c => c.name === dep);
        if (target) {
          links.push({
            source: comp.name,
            target: target.name,
            value: 1
          });
        }
      });
    });

    return { nodes, links };
  },

  /**
   * Transform recommendations for priority matrix
   */
  recommendationsToPriorityMatrix: (recommendations: any[]) => {
    const priorityMap = { low: 1, medium: 2, high: 3, critical: 4 };
    const complexityMap = { low: 1, medium: 2, high: 3 };
    
    return recommendations.map(rec => ({
      title: rec.title,
      priority: priorityMap[rec.priority as keyof typeof priorityMap] || 1,
      complexity: complexityMap[rec.complexity as keyof typeof complexityMap] || 1,
      effort: rec.estimated_effort_hours || 0,
      factor: rec.factor_name
    }));
  }
};

// Chart Creation Helpers
export const createChart = {
  /**
   * Create base SVG element with proper dimensions and margins
   */
  baseSvg: (container: HTMLElement, dimensions: any) => {
    const { width, height, margin } = dimensions;
    
    d3.select(container).selectAll("*").remove();
    
    const svg = d3.select(container)
      .append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .style("background", "transparent");

    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    return { svg, g, width, height };
  },

  /**
   * Create responsive SVG that maintains aspect ratio
   */
  responsiveSvg: (container: HTMLElement, dimensions: any) => {
    const { width, height, margin } = dimensions;
    const totalWidth = width + margin.left + margin.right;
    const totalHeight = height + margin.top + margin.bottom;
    
    d3.select(container).selectAll("*").remove();
    
    const svg = d3.select(container)
      .append("svg")
      .attr("viewBox", `0 0 ${totalWidth} ${totalHeight}`)
      .attr("preserveAspectRatio", "xMidYMid meet")
      .style("width", "100%")
      .style("height", "auto")
      .style("background", "transparent");

    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    return { svg, g, width, height };
  }
};

// Tooltip Utilities
export const tooltip = {
  create: (container: HTMLElement) => {
    return d3.select(container)
      .append("div")
      .style("position", "absolute")
      .style("visibility", "hidden")
      .style("background", "rgba(0, 0, 0, 0.8)")
      .style("color", "white")
      .style("padding", "8px")
      .style("border-radius", "4px")
      .style("font-size", "12px")
      .style("pointer-events", "none")
      .style("z-index", "1000");
  },

  show: (tooltip: d3.Selection<HTMLDivElement, unknown, null, undefined>, content: string, event: MouseEvent) => {
    tooltip.html(content)
      .style("visibility", "visible")
      .style("left", (event.pageX + 10) + "px")
      .style("top", (event.pageY - 10) + "px");
  },

  hide: (tooltip: d3.Selection<HTMLDivElement, unknown, null, undefined>) => {
    tooltip.style("visibility", "hidden");
  }
};

// Export Utilities
export const exportUtils = {
  /**
   * Convert SVG to data URL for export
   */
  svgToDataUrl: (svg: SVGElement): string => {
    const serializer = new XMLSerializer();
    const svgString = serializer.serializeToString(svg);
    const base64 = btoa(unescape(encodeURIComponent(svgString)));
    return `data:image/svg+xml;base64,${base64}`;
  },

  /**
   * Download SVG as PNG
   */
  downloadAsPng: (svg: SVGElement, filename: string, width: number = 800, height: number = 600) => {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();
    
    canvas.width = width;
    canvas.height = height;
    
    img.onload = () => {
      if (ctx) {
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, width, height);
        ctx.drawImage(img, 0, 0, width, height);
        
        canvas.toBlob((blob) => {
          if (blob) {
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${filename}.png`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
          }
        });
      }
    };
    
    img.src = exportUtils.svgToDataUrl(svg);
  }
};

export default {
  colorSchemes,
  chartDimensions,
  transformData,
  createChart,
  tooltip,
  exportUtils
};