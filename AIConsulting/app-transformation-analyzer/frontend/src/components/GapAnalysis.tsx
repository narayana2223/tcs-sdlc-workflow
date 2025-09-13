/**
 * Gap Analysis Component
 * D3.js visualizations for 12-factor radar chart, gap heatmap, and priority matrix
 */

import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  ButtonGroup,
  Grid,
  Chip,
  IconButton,
  FormControl,
  Select,
  MenuItem,
  InputLabel,
  Alert,
  Tooltip as MuiTooltip
} from '@mui/material';
import {
  Radar as RadarIcon,
  GridView as HeatmapIcon,
  ScatterPlot as MatrixIcon,
  Download as DownloadIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import { colorSchemes, createChart, tooltip, exportUtils, transformData } from '../utils/visualization';

interface GapAnalysisData {
  factorEvaluations: Record<string, {
    factor: string;
    title: string;
    score: number;
    compliant: boolean;
    confidence: number;
  }>;
  gaps: Array<{
    factor_name: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    impact: 'low' | 'medium' | 'high';
    description: string;
    effort_estimate: number;
  }>;
  recommendations: Array<{
    title: string;
    priority: 'low' | 'medium' | 'high' | 'critical';
    complexity: 'low' | 'medium' | 'high';
    estimated_effort_hours: number;
    factor_name: string;
  }>;
}

interface GapAnalysisProps {
  data: GapAnalysisData;
  height?: number;
  onGapClick?: (gap: any) => void;
  onRecommendationClick?: (recommendation: any) => void;
  exportFilename?: string;
}

type ViewType = 'radar' | 'heatmap' | 'matrix';

const GapAnalysis: React.FC<GapAnalysisProps> = ({
  data,
  height = 400,
  onGapClick,
  onRecommendationClick,
  exportFilename = 'gap-analysis'
}) => {
  const radarRef = useRef<HTMLDivElement>(null);
  const heatmapRef = useRef<HTMLDivElement>(null);
  const matrixRef = useRef<HTMLDivElement>(null);
  
  const [selectedView, setSelectedView] = useState<ViewType>('radar');
  const [selectedPriority, setSelectedPriority] = useState<string>('all');
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all');

  useEffect(() => {
    if (selectedView === 'radar' && radarRef.current) {
      createRadarChart();
    } else if (selectedView === 'heatmap' && heatmapRef.current) {
      createHeatmap();
    } else if (selectedView === 'matrix' && matrixRef.current) {
      createPriorityMatrix();
    }
  }, [data, selectedView, selectedPriority, selectedSeverity]);

  const createRadarChart = () => {
    if (!radarRef.current) return;

    const container = radarRef.current;
    const radarData = transformData.factorsToRadar(data.factorEvaluations);
    
    const dimensions = { width: 400, height: 400, margin: { top: 50, right: 50, bottom: 50, left: 50 } };
    const { svg, g } = createChart.responsiveSvg(container, dimensions);
    
    const tooltipDiv = tooltip.create(container);

    // Radar chart configuration
    const radius = Math.min(dimensions.width, dimensions.height) / 2 - 50;
    const levels = 5;
    const angleSlice = (Math.PI * 2) / radarData.length;

    // Create scales
    const rScale = d3.scaleLinear()
      .domain([0, 100])
      .range([0, radius]);

    // Draw circular grid lines
    for (let level = 0; level < levels; level++) {
      const levelRadius = (radius / levels) * (level + 1);
      
      g.append('circle')
        .attr('cx', dimensions.width / 2)
        .attr('cy', dimensions.height / 2)
        .attr('r', levelRadius)
        .attr('fill', 'none')
        .attr('stroke', '#CDCDCD')
        .attr('stroke-width', 1);

      // Add level labels
      g.append('text')
        .attr('x', dimensions.width / 2 + 5)
        .attr('y', dimensions.height / 2 - levelRadius - 5)
        .style('font-size', '10px')
        .style('fill', '#737373')
        .text(`${((level + 1) * 20)}%`);
    }

    // Draw axis lines
    radarData.forEach((d, i) => {
      const angle = angleSlice * i - Math.PI / 2;
      const lineX = dimensions.width / 2 + Math.cos(angle) * radius;
      const lineY = dimensions.height / 2 + Math.sin(angle) * radius;

      g.append('line')
        .attr('x1', dimensions.width / 2)
        .attr('y1', dimensions.height / 2)
        .attr('x2', lineX)
        .attr('y2', lineY)
        .attr('stroke', '#CDCDCD')
        .attr('stroke-width', 1);

      // Add axis labels
      const labelX = dimensions.width / 2 + Math.cos(angle) * (radius + 25);
      const labelY = dimensions.height / 2 + Math.sin(angle) * (radius + 25);

      g.append('text')
        .attr('x', labelX)
        .attr('y', labelY)
        .attr('text-anchor', 'middle')
        .attr('dy', '0.35em')
        .style('font-size', '12px')
        .style('font-weight', 'bold')
        .style('fill', '#333')
        .text(d.axis.length > 15 ? d.axis.substring(0, 12) + '...' : d.axis);
    });

    // Create path generator for radar area
    const radarLine = d3.lineRadial<any>()
      .angle((d, i) => angleSlice * i)
      .radius(d => rScale(d.value))
      .curve(d3.curveLinearClosed);

    // Draw radar area
    g.append('path')
      .datum(radarData)
      .attr('d', radarLine)
      .attr('transform', `translate(${dimensions.width / 2}, ${dimensions.height / 2})`)
      .attr('fill', colorSchemes.primary[0])
      .attr('fill-opacity', 0.3)
      .attr('stroke', colorSchemes.primary[0])
      .attr('stroke-width', 2);

    // Draw data points
    radarData.forEach((d, i) => {
      const angle = angleSlice * i - Math.PI / 2;
      const pointRadius = rScale(d.value);
      const x = dimensions.width / 2 + Math.cos(angle) * pointRadius;
      const y = dimensions.height / 2 + Math.sin(angle) * pointRadius;

      g.append('circle')
        .attr('cx', x)
        .attr('cy', y)
        .attr('r', 5)
        .attr('fill', d.compliant ? colorSchemes.success[0] : colorSchemes.error[0])
        .attr('stroke', '#fff')
        .attr('stroke-width', 2)
        .style('cursor', 'pointer')
        .on('mouseover', (event: MouseEvent) => {
          const content = `
            <strong>${d.axis}</strong><br/>
            Score: ${d.value}%<br/>
            Status: ${d.compliant ? 'Compliant' : 'Non-compliant'}<br/>
            Confidence: ${d.confidence}%
          `;
          tooltip.show(tooltipDiv, content, event);
        })
        .on('mouseout', () => tooltip.hide(tooltipDiv));
    });

    // Add center score
    const averageScore = radarData.reduce((sum, d) => sum + d.value, 0) / radarData.length;
    g.append('circle')
      .attr('cx', dimensions.width / 2)
      .attr('cy', dimensions.height / 2)
      .attr('r', 25)
      .attr('fill', averageScore >= 70 ? colorSchemes.success[0] : averageScore >= 50 ? colorSchemes.warning[0] : colorSchemes.error[0])
      .attr('opacity', 0.8);

    g.append('text')
      .attr('x', dimensions.width / 2)
      .attr('y', dimensions.height / 2)
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .style('font-size', '14px')
      .style('font-weight', 'bold')
      .style('fill', '#fff')
      .text(`${Math.round(averageScore)}%`);
  };

  const createHeatmap = () => {
    if (!heatmapRef.current) return;

    const container = heatmapRef.current;
    const heatmapData = transformData.gapsToHeatmap(data.gaps);
    
    // Filter data based on selected severity
    const filteredData = selectedSeverity === 'all' 
      ? heatmapData 
      : heatmapData.filter(d => d.severity === getSeverityNumber(selectedSeverity));

    const dimensions = { width: 600, height: 400, margin: { top: 40, right: 120, bottom: 60, left: 150 } };
    const { svg, g, width, height } = createChart.responsiveSvg(container, dimensions);
    
    const tooltipDiv = tooltip.create(container);

    // Get unique factors and create scales
    const factors = [...new Set(filteredData.map(d => d.factor))];
    const severityLevels = [1, 2, 3, 4]; // low, medium, high, critical
    const impactLevels = [1, 2, 3]; // low, medium, high

    const xScale = d3.scaleBand()
      .domain(severityLevels.map(String))
      .range([0, width])
      .padding(0.05);

    const yScale = d3.scaleBand()
      .domain(factors)
      .range([0, height])
      .padding(0.05);

    const colorScale = d3.scaleSequential(d3.interpolateReds)
      .domain([1, 4]);

    // Create heatmap cells
    const cells = g.selectAll('.heatmap-cell')
      .data(filteredData)
      .enter().append('rect')
      .attr('class', 'heatmap-cell')
      .attr('x', d => xScale(d.severity.toString()) || 0)
      .attr('y', d => yScale(d.factor) || 0)
      .attr('width', xScale.bandwidth())
      .attr('height', yScale.bandwidth())
      .attr('fill', d => colorScale(d.severity * d.impact))
      .attr('stroke', '#fff')
      .attr('stroke-width', 1)
      .style('cursor', 'pointer')
      .on('mouseover', (event: MouseEvent, d: any) => {
        const content = `
          <strong>${d.factor}</strong><br/>
          Severity: ${getSeverityLabel(d.severity)}<br/>
          Impact: ${getImpactLabel(d.impact)}<br/>
          Effort: ${d.effort} hours<br/>
          ${d.description}
        `;
        tooltip.show(tooltipDiv, content, event);
      })
      .on('mouseout', () => tooltip.hide(tooltipDiv))
      .on('click', (event: MouseEvent, d: any) => {
        if (onGapClick) onGapClick(d);
      });

    // Add axes
    const xAxis = d3.axisBottom(xScale)
      .tickFormat(d => getSeverityLabel(parseInt(d)));

    const yAxis = d3.axisLeft(yScale);

    g.append('g')
      .attr('transform', `translate(0, ${height})`)
      .call(xAxis)
      .append('text')
      .attr('x', width / 2)
      .attr('y', 40)
      .attr('text-anchor', 'middle')
      .style('font-size', '12px')
      .style('fill', '#333')
      .text('Severity Level');

    g.append('g')
      .call(yAxis);

    // Add color legend
    const legendWidth = 20;
    const legendHeight = height;
    const legendScale = d3.scaleLinear()
      .domain([1, 4])
      .range([legendHeight, 0]);

    const legend = g.append('g')
      .attr('transform', `translate(${width + 20}, 0)`);

    const legendData = d3.range(1, 5, 0.1);
    legend.selectAll('.legend-rect')
      .data(legendData)
      .enter().append('rect')
      .attr('class', 'legend-rect')
      .attr('x', 0)
      .attr('y', d => legendScale(d))
      .attr('width', legendWidth)
      .attr('height', legendHeight / legendData.length + 1)
      .attr('fill', d => colorScale(d));

    legend.append('text')
      .attr('x', legendWidth + 10)
      .attr('y', 0)
      .style('font-size', '12px')
      .text('High Risk');

    legend.append('text')
      .attr('x', legendWidth + 10)
      .attr('y', legendHeight)
      .style('font-size', '12px')
      .text('Low Risk');
  };

  const createPriorityMatrix = () => {
    if (!matrixRef.current) return;

    const container = matrixRef.current;
    const matrixData = transformData.recommendationsToPriorityMatrix(data.recommendations);
    
    // Filter data based on selected priority
    const filteredData = selectedPriority === 'all'
      ? matrixData
      : matrixData.filter(d => d.priority === getPriorityNumber(selectedPriority));

    const dimensions = { width: 500, height: 400, margin: { top: 40, right: 40, bottom: 60, left: 60 } };
    const { svg, g, width, height } = createChart.responsiveSvg(container, dimensions);
    
    const tooltipDiv = tooltip.create(container);

    // Create scales
    const xScale = d3.scaleLinear()
      .domain([0.5, 3.5])
      .range([0, width]);

    const yScale = d3.scaleLinear()
      .domain([0.5, 4.5])
      .range([height, 0]);

    const sizeScale = d3.scaleLinear()
      .domain(d3.extent(filteredData, d => d.effort) as [number, number])
      .range([5, 25]);

    const colorScale = d3.scaleOrdinal<string>()
      .domain(['1', '2', '3', '4'])
      .range(colorSchemes.technology);

    // Add quadrant backgrounds
    const quadrants = [
      { x: 0, y: 0, width: width / 2, height: height / 2, label: 'High Priority\nLow Complexity', color: colorSchemes.success[6] },
      { x: width / 2, y: 0, width: width / 2, height: height / 2, label: 'High Priority\nHigh Complexity', color: colorSchemes.warning[6] },
      { x: 0, y: height / 2, width: width / 2, height: height / 2, label: 'Low Priority\nLow Complexity', color: colorSchemes.neutral[6] },
      { x: width / 2, y: height / 2, width: width / 2, height: height / 2, label: 'Low Priority\nHigh Complexity', color: colorSchemes.error[6] }
    ];

    quadrants.forEach(quad => {
      g.append('rect')
        .attr('x', quad.x)
        .attr('y', quad.y)
        .attr('width', quad.width)
        .attr('height', quad.height)
        .attr('fill', quad.color)
        .attr('opacity', 0.1);

      g.append('text')
        .attr('x', quad.x + quad.width / 2)
        .attr('y', quad.y + quad.height / 2)
        .attr('text-anchor', 'middle')
        .style('font-size', '10px')
        .style('font-weight', 'bold')
        .style('fill', '#666')
        .style('opacity', 0.7)
        .selectAll('tspan')
        .data(quad.label.split('\n'))
        .enter().append('tspan')
        .attr('x', quad.x + quad.width / 2)
        .attr('dy', (d, i) => i === 0 ? '0em' : '1.2em')
        .text(d => d);
    });

    // Draw data points
    g.selectAll('.matrix-point')
      .data(filteredData)
      .enter().append('circle')
      .attr('class', 'matrix-point')
      .attr('cx', d => xScale(d.complexity))
      .attr('cy', d => yScale(d.priority))
      .attr('r', d => sizeScale(d.effort))
      .attr('fill', d => colorScale(d.priority.toString()))
      .attr('opacity', 0.7)
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer')
      .on('mouseover', (event: MouseEvent, d: any) => {
        const content = `
          <strong>${d.title}</strong><br/>
          Priority: ${getPriorityLabel(d.priority)}<br/>
          Complexity: ${getComplexityLabel(d.complexity)}<br/>
          Effort: ${d.effort} hours<br/>
          Factor: ${d.factor}
        `;
        tooltip.show(tooltipDiv, content, event);
      })
      .on('mouseout', () => tooltip.hide(tooltipDiv))
      .on('click', (event: MouseEvent, d: any) => {
        if (onRecommendationClick) onRecommendationClick(d);
      });

    // Add axes
    const xAxis = d3.axisBottom(xScale)
      .ticks(3)
      .tickFormat(d => getComplexityLabel(d.valueOf()));

    const yAxis = d3.axisLeft(yScale)
      .ticks(4)
      .tickFormat(d => getPriorityLabel(d.valueOf()));

    g.append('g')
      .attr('transform', `translate(0, ${height})`)
      .call(xAxis)
      .append('text')
      .attr('x', width / 2)
      .attr('y', 40)
      .attr('text-anchor', 'middle')
      .style('font-size', '12px')
      .style('fill', '#333')
      .text('Implementation Complexity');

    g.append('g')
      .call(yAxis)
      .append('text')
      .attr('transform', 'rotate(-90)')
      .attr('y', -40)
      .attr('x', -height / 2)
      .attr('text-anchor', 'middle')
      .style('font-size', '12px')
      .style('fill', '#333')
      .text('Business Priority');

    // Add grid lines
    g.append('line')
      .attr('x1', width / 2)
      .attr('x2', width / 2)
      .attr('y1', 0)
      .attr('y2', height)
      .attr('stroke', '#ccc')
      .attr('stroke-dasharray', '3,3');

    g.append('line')
      .attr('x1', 0)
      .attr('x2', width)
      .attr('y1', height / 2)
      .attr('y2', height / 2)
      .attr('stroke', '#ccc')
      .attr('stroke-dasharray', '3,3');
  };

  // Helper functions
  const getSeverityNumber = (severity: string): number => {
    const map: Record<string, number> = { low: 1, medium: 2, high: 3, critical: 4 };
    return map[severity] || 1;
  };

  const getSeverityLabel = (severity: number): string => {
    const map: Record<number, string> = { 1: 'Low', 2: 'Medium', 3: 'High', 4: 'Critical' };
    return map[severity] || 'Low';
  };

  const getImpactLabel = (impact: number): string => {
    const map: Record<number, string> = { 1: 'Low', 2: 'Medium', 3: 'High' };
    return map[impact] || 'Low';
  };

  const getPriorityNumber = (priority: string): number => {
    const map: Record<string, number> = { low: 1, medium: 2, high: 3, critical: 4 };
    return map[priority] || 1;
  };

  const getPriorityLabel = (priority: number): string => {
    const map: Record<number, string> = { 1: 'Low', 2: 'Medium', 3: 'High', 4: 'Critical' };
    return map[priority] || 'Low';
  };

  const getComplexityLabel = (complexity: number): string => {
    const map: Record<number, string> = { 1: 'Low', 2: 'Medium', 3: 'High' };
    return map[complexity] || 'Low';
  };

  const handleExport = () => {
    const refs = { radar: radarRef, heatmap: heatmapRef, matrix: matrixRef };
    const ref = refs[selectedView];
    
    if (ref.current) {
      const svg = ref.current.querySelector('svg') as SVGElement;
      if (svg) {
        exportUtils.downloadAsPng(svg, `${exportFilename}-${selectedView}`, 800, 600);
      }
    }
  };

  const getViewDescription = (view: ViewType): string => {
    switch (view) {
      case 'radar':
        return '12-factor compliance radar chart showing overall assessment scores';
      case 'heatmap':
        return 'Gap heatmap showing severity and impact of identified issues';
      case 'matrix':
        return 'Priority matrix plotting recommendations by complexity and business value';
      default:
        return '';
    }
  };

  if (!data || Object.keys(data.factorEvaluations).length === 0) {
    return (
      <Card>
        <CardContent>
          <Alert severity="info">
            No gap analysis data available. Complete a 12-factor assessment to see compliance gaps and recommendations.
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Box>
      <Grid container spacing={3}>
        {/* Radar Chart */}
        <Grid item xs={12} lg={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Box>
                  <Typography variant="h6">12-Factor Radar</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Compliance overview
                  </Typography>
                </Box>
                <MuiTooltip title="Shows compliance scores for each 12-factor principle">
                  <IconButton size="small">
                    <InfoIcon />
                  </IconButton>
                </MuiTooltip>
              </Box>
              
              <Box ref={radarRef} sx={{ height: 350, width: '100%' }} />
              
              <Box mt={2} display="flex" justifyContent="space-between">
                <Chip 
                  label={`${Object.keys(data.factorEvaluations).length} Factors`} 
                  size="small" 
                />
                <IconButton onClick={handleExport} size="small">
                  <DownloadIcon />
                </IconButton>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Gap Heatmap */}
        <Grid item xs={12} lg={8}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Box>
                  <Typography variant="h6">Gap Heatmap</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Issue severity and impact analysis
                  </Typography>
                </Box>
                <Box display="flex" gap={1}>
                  <FormControl size="small" style={{ minWidth: 100 }}>
                    <InputLabel>Severity</InputLabel>
                    <Select
                      value={selectedSeverity}
                      onChange={(e) => setSelectedSeverity(e.target.value)}
                      label="Severity"
                    >
                      <MenuItem value="all">All</MenuItem>
                      <MenuItem value="low">Low</MenuItem>
                      <MenuItem value="medium">Medium</MenuItem>
                      <MenuItem value="high">High</MenuItem>
                      <MenuItem value="critical">Critical</MenuItem>
                    </Select>
                  </FormControl>
                  <IconButton onClick={handleExport} size="small">
                    <DownloadIcon />
                  </IconButton>
                </Box>
              </Box>
              
              <Box ref={heatmapRef} sx={{ height: 350, width: '100%' }} />
              
              <Box mt={2}>
                <Chip label={`${data.gaps.length} Gaps Identified`} size="small" />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Priority Matrix */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Box>
                  <Typography variant="h6">Priority Matrix</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Recommendations plotted by priority and complexity
                  </Typography>
                </Box>
                <Box display="flex" gap={1}>
                  <FormControl size="small" style={{ minWidth: 100 }}>
                    <InputLabel>Priority</InputLabel>
                    <Select
                      value={selectedPriority}
                      onChange={(e) => setSelectedPriority(e.target.value)}
                      label="Priority"
                    >
                      <MenuItem value="all">All</MenuItem>
                      <MenuItem value="low">Low</MenuItem>
                      <MenuItem value="medium">Medium</MenuItem>
                      <MenuItem value="high">High</MenuItem>
                      <MenuItem value="critical">Critical</MenuItem>
                    </Select>
                  </FormControl>
                  <IconButton onClick={handleExport} size="small">
                    <DownloadIcon />
                  </IconButton>
                </Box>
              </Box>
              
              <Box ref={matrixRef} sx={{ height: 400, width: '100%' }} />
              
              <Box mt={2} display="flex" gap={1}>
                <Chip label={`${data.recommendations.length} Recommendations`} size="small" />
                <Chip 
                  label={`${data.recommendations.reduce((sum, rec) => sum + rec.estimated_effort_hours, 0)} Total Hours`} 
                  size="small" 
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default GapAnalysis;