/**
 * Gap Heatmap Component
 * Interactive D3.js heatmap for visualizing gaps by factor and severity
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
  InputLabel,
  Chip,
  Grid
} from '@mui/material';
import { Download as DownloadIcon } from '@mui/icons-material';

interface GapData {
  factor: string;
  gapType: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  impact: 'low' | 'medium' | 'high';
  description: string;
  effort: number;
}

interface GroupedGapData {
  factor: string;
  gapType: string;
  gaps: GapData[];
}

interface GapHeatmapProps {
  data: GapData[];
  width?: number;
  height?: number;
  showLabels?: boolean;
  showTooltip?: boolean;
  colorScheme?: 'severity' | 'impact' | 'effort';
  onCellClick?: (gap: GapData) => void;
  exportable?: boolean;
  title?: string;
  animated?: boolean;
}

const GapHeatmap: React.FC<GapHeatmapProps> = ({
  data,
  width = 600,
  height = 400,
  showLabels = true,
  showTooltip = true,
  colorScheme = 'severity',
  onCellClick,
  exportable = true,
  title = "Gap Analysis Heatmap",
  animated = true
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  const [animateChart, setAnimateChart] = useState(animated);
  const [selectedColorScheme, setSelectedColorScheme] = useState(colorScheme);
  const [filteredData, setFilteredData] = useState(data);
  const [selectedSeverity, setSelectedSeverity] = useState<string[]>(['low', 'medium', 'high', 'critical']);
  const [hoveredCell, setHoveredCell] = useState<GapData | null>(null);

  const margin = { top: 80, right: 100, bottom: 80, left: 120 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;

  // Get unique factors and gap types
  const factors = Array.from(new Set(filteredData.map(d => d.factor))).sort();
  const gapTypes = Array.from(new Set(filteredData.map(d => d.gapType))).sort();

  // Color scales for different schemes
  const severityColorScale = d3.scaleOrdinal()
    .domain(['low', 'medium', 'high', 'critical'])
    .range(['#4CAF50', '#FF9800', '#FF5722', '#D32F2F']);

  const impactColorScale = d3.scaleOrdinal()
    .domain(['low', 'medium', 'high'])
    .range(['#81C784', '#FFB74D', '#F44336']);

  const effortColorScale = d3.scaleLinear<string>()
    .domain([0, d3.max(filteredData, d => d.effort) || 100])
    .range(['#E3F2FD', '#1565C0']);

  const getColor = (value: any): string => {
    if (selectedColorScheme === 'severity') {
      return String(severityColorScale(value as string) || '#cccccc');
    } else if (selectedColorScheme === 'impact') {
      return String(impactColorScale(value as string) || '#cccccc');
    } else {
      return String(effortColorScale(value as number) || '#cccccc');
    }
  };

  useEffect(() => {
    const filtered = data.filter(d => selectedSeverity.includes(d.severity));
    setFilteredData(filtered);
  }, [data, selectedSeverity]);

  useEffect(() => {
    drawHeatmap();
  }, [filteredData, animateChart, selectedColorScheme, hoveredCell]);

  const drawHeatmap = () => {
    if (!svgRef.current || !filteredData.length) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    // Create main group
    const g = svg
      .append("g")
      .attr("transform", `translate(${margin.left}, ${margin.top})`);

    // Create scales
    const xScale = d3.scaleBand()
      .domain(gapTypes)
      .range([0, innerWidth])
      .padding(0.1);

    const yScale = d3.scaleBand()
      .domain(factors)
      .range([0, innerHeight])
      .padding(0.1);

    // Add background
    svg.append("rect")
      .attr("width", width)
      .attr("height", height)
      .attr("fill", "#fafafa");

    // Draw grid background
    g.selectAll(".grid-line-x")
      .data(gapTypes)
      .enter()
      .append("line")
      .attr("class", "grid-line-x")
      .attr("x1", d => (xScale(d) || 0) + xScale.bandwidth() / 2)
      .attr("x2", d => (xScale(d) || 0) + xScale.bandwidth() / 2)
      .attr("y1", 0)
      .attr("y2", innerHeight)
      .attr("stroke", "#e0e0e0")
      .attr("stroke-width", 1)
      .attr("stroke-dasharray", "2,2");

    g.selectAll(".grid-line-y")
      .data(factors)
      .enter()
      .append("line")
      .attr("class", "grid-line-y")
      .attr("x1", 0)
      .attr("x2", innerWidth)
      .attr("y1", d => (yScale(d) || 0) + yScale.bandwidth() / 2)
      .attr("y2", d => (yScale(d) || 0) + yScale.bandwidth() / 2)
      .attr("stroke", "#e0e0e0")
      .attr("stroke-width", 1)
      .attr("stroke-dasharray", "2,2");

    // Create matrix data
    const matrixData: { factor: string; gapType: string; gaps: GapData[] }[] = [];
    factors.forEach(factor => {
      gapTypes.forEach(gapType => {
        const gaps = filteredData.filter(d => d.factor === factor && d.gapType === gapType);
        matrixData.push({ factor, gapType, gaps });
      });
    });

    // Draw heatmap cells
    const cells = g.selectAll(".heatmap-cell")
      .data(matrixData)
      .enter()
      .append("g")
      .attr("class", "heatmap-cell")
      .attr("transform", d => `translate(${xScale(d.gapType)}, ${yScale(d.factor)})`);

    cells.each(function(d) {
      const cell = d3.select(this);

      if (d.gaps.length === 0) return;

      // Calculate cell color based on most severe gap or aggregate value
      let cellColor: string;
      if (selectedColorScheme === 'severity') {
        const maxSeverity = d.gaps.reduce((max, gap) => {
          const severityOrder = { 'low': 1, 'medium': 2, 'high': 3, 'critical': 4 };
          return severityOrder[gap.severity] > severityOrder[max] ? gap.severity : max;
        }, 'low');
        cellColor = getColor(maxSeverity);
      } else if (selectedColorScheme === 'impact') {
        const maxImpact = d.gaps.reduce((max, gap) => {
          const impactOrder = { 'low': 1, 'medium': 2, 'high': 3 };
          return impactOrder[gap.impact] > impactOrder[max] ? gap.impact : max;
        }, 'low');
        cellColor = getColor(maxImpact);
      } else {
        const totalEffort = d.gaps.reduce((sum, gap) => sum + gap.effort, 0);
        cellColor = getColor(totalEffort);
      }

      // Draw cell rectangle
      const rect = cell.append("rect")
        .attr("width", xScale.bandwidth())
        .attr("height", yScale.bandwidth())
        .attr("fill", cellColor)
        .attr("stroke", "#fff")
        .attr("stroke-width", 2)
        .attr("rx", 4)
        .style("cursor", onCellClick ? "pointer" : "default")
        .style("opacity", hoveredCell && d.gaps.includes(hoveredCell) ? 1 : 0.8);

      if (animateChart) {
        rect
          .style("opacity", 0)
          .transition()
          .delay(Math.random() * 1000)
          .duration(600)
          .style("opacity", hoveredCell && d.gaps.includes(hoveredCell) ? 1 : 0.8);
      }

      // Add gap count badge
      if (d.gaps.length > 1) {
        cell.append("circle")
          .attr("cx", xScale.bandwidth() - 12)
          .attr("cy", 12)
          .attr("r", 8)
          .attr("fill", "#fff")
          .attr("stroke", cellColor)
          .attr("stroke-width", 2);

        cell.append("text")
          .attr("x", xScale.bandwidth() - 12)
          .attr("y", 16)
          .attr("text-anchor", "middle")
          .attr("font-size", "10px")
          .attr("font-weight", "bold")
          .attr("fill", cellColor)
          .text(d.gaps.length);
      }

      // Add cell labels
      if (showLabels && d.gaps.length > 0) {
        const primaryGap = d.gaps[0];
        cell.append("text")
          .attr("x", xScale.bandwidth() / 2)
          .attr("y", yScale.bandwidth() / 2 + 3)
          .attr("text-anchor", "middle")
          .attr("font-size", "10px")
          .attr("font-weight", "bold")
          .attr("fill", "#fff")
          .text(primaryGap.severity.toUpperCase());
      }

      // Add hover effects
      rect
        .on("mouseover", function(event, d) {
          const data = d as GroupedGapData;
          if (data.gaps.length > 0) {
            setHoveredCell(data.gaps[0]);

            d3.select(this)
              .transition()
              .duration(200)
              .style("opacity", 1)
              .attr("stroke-width", 3);

            // Show tooltip
            if (showTooltip && tooltipRef.current) {
              const tooltip = d3.select(tooltipRef.current);
              tooltip
                .style("opacity", 1)
                .style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY - 10) + "px")
                .html(`
                  <div style="font-weight: bold; margin-bottom: 8px;">
                    ${data.factor.replace(/_/g, ' ')} - ${data.gapType}
                  </div>
                  <div>Gaps: ${data.gaps.length}</div>
                  <div>Max Severity: ${data.gaps.reduce((max, gap) => {
                    const order = { 'low': 1, 'medium': 2, 'high': 3, 'critical': 4 };
                    return order[gap.severity] > order[max] ? gap.severity : max;
                  }, 'low')}</div>
                  <div>Total Effort: ${data.gaps.reduce((sum, gap) => sum + gap.effort, 0)}h</div>
                `);
            }
          }
        })
        .on("mouseout", function(event, d) {
          setHoveredCell(null);

          d3.select(this)
            .transition()
            .duration(200)
            .style("opacity", 0.8)
            .attr("stroke-width", 2);

          // Hide tooltip
          if (tooltipRef.current) {
            d3.select(tooltipRef.current).style("opacity", 0);
          }
        })
        .on("click", function(event, d) {
          const data = d as GroupedGapData;
          if (onCellClick && data.gaps.length > 0) {
            onCellClick(data.gaps[0]);
          }
        });
    });

    // Add x-axis labels
    g.selectAll(".x-axis-label")
      .data(gapTypes)
      .enter()
      .append("text")
      .attr("class", "x-axis-label")
      .attr("x", d => (xScale(d) || 0) + xScale.bandwidth() / 2)
      .attr("y", innerHeight + 20)
      .attr("text-anchor", "middle")
      .attr("font-size", "11px")
      .attr("font-weight", "500")
      .attr("fill", "#666")
      .text(d => d.replace(/_/g, ' '))
      .call(wrapText, xScale.bandwidth());

    // Add y-axis labels
    g.selectAll(".y-axis-label")
      .data(factors)
      .enter()
      .append("text")
      .attr("class", "y-axis-label")
      .attr("x", -10)
      .attr("y", d => (yScale(d) || 0) + yScale.bandwidth() / 2 + 3)
      .attr("text-anchor", "end")
      .attr("font-size", "11px")
      .attr("font-weight", "500")
      .attr("fill", "#666")
      .text(d => d.replace(/_/g, ' '));

    // Add title
    svg.append("text")
      .attr("x", width / 2)
      .attr("y", 25)
      .attr("text-anchor", "middle")
      .attr("font-size", "16px")
      .attr("font-weight", "bold")
      .attr("fill", "#333")
      .text(title);

    // Add axis titles
    svg.append("text")
      .attr("x", width / 2)
      .attr("y", height - 20)
      .attr("text-anchor", "middle")
      .attr("font-size", "12px")
      .attr("font-weight", "500")
      .attr("fill", "#666")
      .text("Gap Types");

    svg.append("text")
      .attr("transform", `translate(20, ${height / 2}) rotate(-90)`)
      .attr("text-anchor", "middle")
      .attr("font-size", "12px")
      .attr("font-weight", "500")
      .attr("fill", "#666")
      .text("12-Factor Principles");

    // Add legend
    drawLegend(svg);
  };

  const drawLegend = (svg: d3.Selection<SVGSVGElement, unknown, null, undefined>) => {
    const legend = svg.append("g")
      .attr("class", "legend")
      .attr("transform", `translate(${width - 90}, ${margin.top})`);

    let legendData: Array<{ label: string; color: string }> = [];

    if (selectedColorScheme === 'severity') {
      legendData = [
        { label: "Critical", color: getColor('critical') },
        { label: "High", color: getColor('high') },
        { label: "Medium", color: getColor('medium') },
        { label: "Low", color: getColor('low') }
      ];
    } else if (selectedColorScheme === 'impact') {
      legendData = [
        { label: "High Impact", color: getColor('high') },
        { label: "Medium Impact", color: getColor('medium') },
        { label: "Low Impact", color: getColor('low') }
      ];
    } else {
      const maxEffort = d3.max(filteredData, d => d.effort) || 100;
      legendData = [
        { label: `${maxEffort}+ hours`, color: getColor(maxEffort) },
        { label: `${Math.floor(maxEffort/2)} hours`, color: getColor(maxEffort/2) },
        { label: "0 hours", color: getColor(0) }
      ];
    }

    legendData.forEach((item, i) => {
      const legendItem = legend.append("g")
        .attr("transform", `translate(0, ${i * 25})`);

      legendItem.append("rect")
        .attr("width", 15)
        .attr("height", 15)
        .attr("fill", item.color)
        .attr("stroke", "#fff")
        .attr("stroke-width", 1)
        .attr("rx", 2);

      legendItem.append("text")
        .attr("x", 20)
        .attr("y", 12)
        .attr("font-size", "11px")
        .attr("fill", "#666")
        .text(item.label);
    });
  };

  // Text wrapping utility
  const wrapText = (text: d3.Selection<SVGTextElement, string, SVGGElement, unknown>, width: number) => {
    text.each(function() {
      const text = d3.select(this);
      const words = text.text().split(/\s+/).reverse();
      let word;
      let line: string[] = [];
      let lineNumber = 0;
      const lineHeight = 1.1;
      const y = text.attr("y");
      const dy = 0;
      let tspan = text.text(null).append("tspan").attr("x", text.attr("x")).attr("y", y).attr("dy", dy + "em");

      while ((word = words.pop())) {
        line.push(word);
        tspan.text(line.join(" "));
        if (tspan.node()!.getComputedTextLength() > width) {
          line.pop();
          tspan.text(line.join(" "));
          line = [word];
          tspan = text.append("tspan").attr("x", text.attr("x")).attr("y", y).attr("dy", ++lineNumber * lineHeight + dy + "em").text(word);
        }
      }
    });
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
    link.download = 'gap-heatmap.svg';
    link.click();

    URL.revokeObjectURL(url);
  };

  const toggleSeverityFilter = (severity: string) => {
    setSelectedSeverity(prev =>
      prev.includes(severity)
        ? prev.filter(s => s !== severity)
        : [...prev, severity]
    );
  };

  return (
    <Card>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
          <Typography variant="h6">{title}</Typography>
          <Box display="flex" alignItems="center" gap={1} flexWrap="wrap">
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Color By</InputLabel>
              <Select
                value={selectedColorScheme}
                label="Color By"
                onChange={(e) => setSelectedColorScheme(e.target.value as typeof selectedColorScheme)}
              >
                <MenuItem value="severity">Severity</MenuItem>
                <MenuItem value="impact">Impact</MenuItem>
                <MenuItem value="effort">Effort</MenuItem>
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

        {/* Severity Filters */}
        <Box mb={2}>
          <Typography variant="body2" gutterBottom>
            Filter by Severity:
          </Typography>
          <Box display="flex" gap={1} flexWrap="wrap">
            {['low', 'medium', 'high', 'critical'].map(severity => (
              <Chip
                key={severity}
                label={severity}
                color={selectedSeverity.includes(severity) ? 'primary' : 'default'}
                onClick={() => toggleSeverityFilter(severity)}
                variant={selectedSeverity.includes(severity) ? 'filled' : 'outlined'}
                size="small"
              />
            ))}
          </Box>
        </Box>

        <Box display="flex" justifyContent="center" position="relative">
          <svg
            ref={svgRef}
            width={width}
            height={height}
            style={{ maxWidth: '100%', height: 'auto' }}
          />

          {/* Tooltip */}
          <div
            ref={tooltipRef}
            style={{
              position: 'absolute',
              pointerEvents: 'none',
              background: 'rgba(0, 0, 0, 0.8)',
              color: 'white',
              padding: '8px 12px',
              borderRadius: '4px',
              fontSize: '12px',
              opacity: 0,
              transition: 'opacity 0.2s',
              zIndex: 1000
            }}
          />
        </Box>

        {/* Summary Stats */}
        <Grid container spacing={2} mt={2}>
          <Grid item xs={6} sm={3}>
            <Box textAlign="center" p={1} bgcolor="error.light" borderRadius={1}>
              <Typography variant="h6" color="error.contrastText">
                {filteredData.filter(d => d.severity === 'critical').length}
              </Typography>
              <Typography variant="caption" color="error.contrastText">
                Critical Gaps
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Box textAlign="center" p={1} bgcolor="warning.light" borderRadius={1}>
              <Typography variant="h6" color="warning.contrastText">
                {filteredData.filter(d => d.severity === 'high').length}
              </Typography>
              <Typography variant="caption" color="warning.contrastText">
                High Severity
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Box textAlign="center" p={1} bgcolor="info.light" borderRadius={1}>
              <Typography variant="h6" color="info.contrastText">
                {factors.length}
              </Typography>
              <Typography variant="caption" color="info.contrastText">
                Affected Factors
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Box textAlign="center" p={1} bgcolor="success.light" borderRadius={1}>
              <Typography variant="h6" color="success.contrastText">
                {Math.round(filteredData.reduce((sum, d) => sum + d.effort, 0))}h
              </Typography>
              <Typography variant="caption" color="success.contrastText">
                Total Effort
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

export default GapHeatmap;