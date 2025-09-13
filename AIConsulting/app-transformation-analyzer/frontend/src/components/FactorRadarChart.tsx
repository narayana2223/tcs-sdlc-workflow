/**
 * Factor Radar Chart Component
 * Interactive D3.js radar chart for 12-factor assessment visualization
 */

import React, { useRef, useEffect, useState } from 'react';
import * as d3 from 'd3';
import {
  Box,
  Card,
  CardContent,
  Typography,
  FormControlLabel,
  Switch,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel
} from '@mui/material';
import { Download as DownloadIcon } from '@mui/icons-material';

interface FactorData {
  factor: string;
  score: number;
  maxScore: number;
  color?: string;
}

interface FactorRadarChartProps {
  data: FactorData[];
  width?: number;
  height?: number;
  showLabels?: boolean;
  showGrid?: boolean;
  showLegend?: boolean;
  colorScheme?: string[];
  onFactorClick?: (factor: string) => void;
  exportable?: boolean;
  title?: string;
  animated?: boolean;
}

const FactorRadarChart: React.FC<FactorRadarChartProps> = ({
  data,
  width = 400,
  height = 400,
  showLabels = true,
  showGrid = true,
  showLegend = true,
  colorScheme = ['#2196F3', '#4CAF50', '#FF9800', '#F44336', '#9C27B0'],
  onFactorClick,
  exportable = true,
  title = "12-Factor Compliance Radar",
  animated = true
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [animateChart, setAnimateChart] = useState(animated);
  const [chartTheme, setChartTheme] = useState('default');
  const [hoveredFactor, setHoveredFactor] = useState<string | null>(null);

  const margin = { top: 40, right: 80, bottom: 40, left: 80 };
  const radius = Math.min(width - margin.left - margin.right, height - margin.top - margin.bottom) / 2;
  const centerX = width / 2;
  const centerY = height / 2;

  const themes = {
    default: {
      background: '#ffffff',
      gridColor: '#e0e0e0',
      textColor: '#333333',
      colors: colorScheme
    },
    dark: {
      background: '#2c2c2c',
      gridColor: '#555555',
      textColor: '#ffffff',
      colors: ['#64B5F6', '#81C784', '#FFB74D', '#E57373', '#BA68C8']
    },
    professional: {
      background: '#f8f9fa',
      gridColor: '#dee2e6',
      textColor: '#495057',
      colors: ['#007bff', '#28a745', '#ffc107', '#dc3545', '#6f42c1']
    }
  };

  const currentTheme = themes[chartTheme as keyof typeof themes] || themes.default;

  useEffect(() => {
    drawRadarChart();
  }, [data, animateChart, chartTheme, hoveredFactor]);

  const drawRadarChart = () => {
    if (!svgRef.current || !data.length) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    // Create main group
    const g = svg
      .append("g")
      .attr("transform", `translate(${centerX}, ${centerY})`);

    // Add background
    svg
      .append("rect")
      .attr("width", width)
      .attr("height", height)
      .attr("fill", currentTheme.background);

    // Create scales
    const angleScale = d3.scaleLinear()
      .domain([0, data.length])
      .range([0, 2 * Math.PI]);

    const radiusScale = d3.scaleLinear()
      .domain([0, 5])
      .range([0, radius]);

    // Draw grid circles
    if (showGrid) {
      const gridLevels = [1, 2, 3, 4, 5];
      gridLevels.forEach(level => {
        g.append("circle")
          .attr("cx", 0)
          .attr("cy", 0)
          .attr("r", radiusScale(level))
          .attr("fill", "none")
          .attr("stroke", currentTheme.gridColor)
          .attr("stroke-width", level === 5 ? 2 : 1)
          .attr("stroke-dasharray", level === 5 ? "none" : "2,2");

        // Add level labels
        g.append("text")
          .attr("x", 5)
          .attr("y", -radiusScale(level) + 4)
          .attr("font-size", "10px")
          .attr("fill", currentTheme.textColor)
          .attr("opacity", 0.7)
          .text(level.toString());
      });
    }

    // Draw grid lines (spokes)
    if (showGrid) {
      data.forEach((d, i) => {
        const angle = angleScale(i) - Math.PI / 2;
        const x1 = 0;
        const y1 = 0;
        const x2 = radius * Math.cos(angle);
        const y2 = radius * Math.sin(angle);

        g.append("line")
          .attr("x1", x1)
          .attr("y1", y1)
          .attr("x2", x2)
          .attr("y2", y2)
          .attr("stroke", currentTheme.gridColor)
          .attr("stroke-width", 1);
      });
    }

    // Create line generator for radar path
    const line = d3.lineRadial<FactorData>()
      .angle((d, i) => angleScale(i))
      .radius(d => radiusScale(d.score))
      .curve(d3.curveLinearClosed);

    // Draw radar area
    const radarPath = g.append("path")
      .datum(data)
      .attr("fill", currentTheme.colors[0])
      .attr("fill-opacity", 0.1)
      .attr("stroke", currentTheme.colors[0])
      .attr("stroke-width", 2);

    if (animateChart) {
      radarPath
        .attr("d", line.radius(() => 0)(data))
        .transition()
        .duration(1000)
        .ease(d3.easeBackOut)
        .attr("d", line);
    } else {
      radarPath.attr("d", line);
    }

    // Draw data points
    const points = g.selectAll(".radar-point")
      .data(data)
      .enter()
      .append("g")
      .attr("class", "radar-point");

    points.each(function(d, i) {
      const point = d3.select(this);
      const angle = angleScale(i) - Math.PI / 2;
      const pointRadius = radiusScale(d.score);
      const x = pointRadius * Math.cos(angle);
      const y = pointRadius * Math.sin(angle);

      // Create point circle
      const circle = point.append("circle")
        .attr("cx", x)
        .attr("cy", y)
        .attr("r", hoveredFactor === d.factor ? 8 : 5)
        .attr("fill", d.color || currentTheme.colors[i % currentTheme.colors.length])
        .attr("stroke", "#fff")
        .attr("stroke-width", 2)
        .style("cursor", onFactorClick ? "pointer" : "default");

      if (animateChart) {
        circle
          .attr("cx", 0)
          .attr("cy", 0)
          .transition()
          .delay(i * 100)
          .duration(600)
          .ease(d3.easeBackOut)
          .attr("cx", x)
          .attr("cy", y);
      }

      // Add hover effects
      circle
        .on("mouseover", function(event: any, d: any) {
          setHoveredFactor((d as FactorData).factor);
          d3.select(this)
            .transition()
            .duration(200)
            .attr("r", 8);
        })
        .on("mouseout", function(event: any, d: any) {
          setHoveredFactor(null);
          d3.select(this)
            .transition()
            .duration(200)
            .attr("r", 5);
        })
        .on("click", function(event: any, d: any) {
          if (onFactorClick) {
            onFactorClick((d as FactorData).factor);
          }
        });

      // Add score label on point
      point.append("text")
        .attr("x", x + (x > 0 ? 10 : -10))
        .attr("y", y - 10)
        .attr("text-anchor", x > 0 ? "start" : "end")
        .attr("font-size", "12px")
        .attr("font-weight", "bold")
        .attr("fill", currentTheme.textColor)
        .text(d.score.toFixed(1))
        .style("opacity", hoveredFactor === d.factor ? 1 : 0)
        .transition()
        .duration(200);
    });

    // Draw factor labels
    if (showLabels) {
      const labels = g.selectAll(".factor-label")
        .data(data)
        .enter()
        .append("g")
        .attr("class", "factor-label");

      labels.each(function(d, i) {
        const label = d3.select(this);
        const angle = angleScale(i) - Math.PI / 2;
        const labelRadius = radius + 20;
        const x = labelRadius * Math.cos(angle);
        const y = labelRadius * Math.sin(angle);

        const text = label.append("text")
          .attr("x", x)
          .attr("y", y)
          .attr("text-anchor", x > 10 ? "start" : x < -10 ? "end" : "middle")
          .attr("dominant-baseline", "middle")
          .attr("font-size", "11px")
          .attr("font-weight", hoveredFactor === d.factor ? "bold" : "normal")
          .attr("fill", currentTheme.textColor)
          .style("cursor", onFactorClick ? "pointer" : "default");

        // Break long labels
        const words = d.factor.replace(/_/g, ' ').split(' ');
        if (words.length > 2) {
          text.append("tspan")
            .attr("x", x)
            .attr("dy", "-0.3em")
            .text(words.slice(0, 2).join(' '));
          text.append("tspan")
            .attr("x", x)
            .attr("dy", "1.2em")
            .text(words.slice(2).join(' '));
        } else {
          text.text(words.join(' '));
        }

        text.on("click", function(event: any, d: any) {
          if (onFactorClick) {
            onFactorClick((d as FactorData).factor);
          }
        });
      });
    }

    // Add title
    svg.append("text")
      .attr("x", width / 2)
      .attr("y", 20)
      .attr("text-anchor", "middle")
      .attr("font-size", "16px")
      .attr("font-weight", "bold")
      .attr("fill", currentTheme.textColor)
      .text(title);

    // Add legend
    if (showLegend) {
      const legend = svg.append("g")
        .attr("class", "legend")
        .attr("transform", `translate(${width - 70}, 40)`);

      const legendItems = [
        { label: "Excellent (5)", color: currentTheme.colors[0], score: 5 },
        { label: "Good (4)", color: currentTheme.colors[1], score: 4 },
        { label: "Fair (3)", color: currentTheme.colors[2], score: 3 },
        { label: "Poor (2)", color: currentTheme.colors[3], score: 2 },
        { label: "Missing (1)", color: currentTheme.colors[4], score: 1 }
      ];

      legendItems.forEach((item, i) => {
        const legendItem = legend.append("g")
          .attr("transform", `translate(0, ${i * 20})`);

        legendItem.append("circle")
          .attr("r", 4)
          .attr("fill", item.color);

        legendItem.append("text")
          .attr("x", 10)
          .attr("y", 4)
          .attr("font-size", "10px")
          .attr("fill", currentTheme.textColor)
          .text(item.label);
      });
    }
  };

  const exportChart = () => {
    if (!svgRef.current) return;

    const svgElement = svgRef.current;
    const serializer = new XMLSerializer();
    const svgString = serializer.serializeToString(svgElement);
    const blob = new Blob([svgString], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = url;
    link.download = 'factor-radar-chart.svg';
    link.click();

    URL.revokeObjectURL(url);
  };

  return (
    <Card>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">{title}</Typography>
          <Box display="flex" alignItems="center" gap={1}>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Theme</InputLabel>
              <Select
                value={chartTheme}
                label="Theme"
                onChange={(e) => setChartTheme(e.target.value)}
              >
                <MenuItem value="default">Default</MenuItem>
                <MenuItem value="dark">Dark</MenuItem>
                <MenuItem value="professional">Professional</MenuItem>
              </Select>
            </FormControl>

            <FormControlLabel
              control={
                <Switch
                  checked={animateChart}
                  onChange={(e) => setAnimateChart(e.target.checked)}
                  size="small"
                />
              }
              label="Animate"
            />

            {exportable && (
              <Button
                variant="outlined"
                size="small"
                startIcon={<DownloadIcon />}
                onClick={exportChart}
              >
                Export
              </Button>
            )}
          </Box>
        </Box>

        <Box display="flex" justifyContent="center">
          <svg
            ref={svgRef}
            width={width}
            height={height}
            style={{ maxWidth: '100%', height: 'auto' }}
          />
        </Box>

        {hoveredFactor && (
          <Box mt={2}>
            <Typography variant="body2" color="text.secondary">
              <strong>{hoveredFactor.replace(/_/g, ' ')}</strong>
              {' - '}
              Score: {data.find(d => d.factor === hoveredFactor)?.score || 0}/5
            </Typography>
          </Box>
        )}

        {/* Quick stats */}
        <Box mt={2} p={2} bgcolor="grey.50" borderRadius={1}>
          <Typography variant="subtitle2" gutterBottom>
            Quick Stats
          </Typography>
          <Box display="flex" justifyContent="space-between" flexWrap="wrap" gap={2}>
            <Box textAlign="center">
              <Typography variant="h6" color="success.main">
                {data.filter(d => d.score >= 4).length}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Excellent/Good
              </Typography>
            </Box>
            <Box textAlign="center">
              <Typography variant="h6" color="warning.main">
                {data.filter(d => d.score === 3).length}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Fair
              </Typography>
            </Box>
            <Box textAlign="center">
              <Typography variant="h6" color="error.main">
                {data.filter(d => d.score <= 2).length}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Poor/Missing
              </Typography>
            </Box>
            <Box textAlign="center">
              <Typography variant="h6" color="primary.main">
                {(data.reduce((sum, d) => sum + d.score, 0) / data.length).toFixed(1)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Average Score
              </Typography>
            </Box>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

export default FactorRadarChart;