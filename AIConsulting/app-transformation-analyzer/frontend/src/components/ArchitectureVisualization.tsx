/**
 * Architecture Visualization Component
 * D3.js-based visualization for component relationships, technology stack, and integration points
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
  FormControl,
  Select,
  MenuItem,
  InputLabel,
  Chip,
  Tooltip,
  IconButton,
  Alert
} from '@mui/material';
import {
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  CenterFocusStrong as CenterIcon,
  Download as DownloadIcon,
  FilterList as FilterIcon
} from '@mui/icons-material';
import { colorSchemes, createChart, tooltip, exportUtils, transformData } from '../utils/visualization';

interface ArchitectureData {
  components: Array<{
    name: string;
    type: string;
    complexity: number;
    dependencies: string[];
    integrations?: string[];
  }>;
  layers: string[];
  patterns: string[];
  integrationPoints?: Array<{
    source: string;
    target: string;
    type: string;
    protocol?: string;
  }>;
}

interface ArchitectureVisualizationProps {
  data: ArchitectureData;
  height?: number;
  onComponentClick?: (component: any) => void;
  exportFilename?: string;
}

type ViewMode = 'dependency' | 'layers' | 'integrations';

const ArchitectureVisualization: React.FC<ArchitectureVisualizationProps> = ({
  data,
  height = 600,
  onComponentClick,
  exportFilename = 'architecture-diagram'
}) => {
  const svgRef = useRef<HTMLDivElement>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('dependency');
  const [selectedLayer, setSelectedLayer] = useState<string>('all');
  const [zoomLevel, setZoomLevel] = useState(1);
  const [simulation, setSimulation] = useState<d3.Simulation<any, any> | null>(null);

  useEffect(() => {
    if (svgRef.current && data.components.length > 0) {
      createVisualization();
    }

    return () => {
      if (simulation) {
        simulation.stop();
      }
    };
  }, [data, viewMode, selectedLayer]);

  const createVisualization = () => {
    if (!svgRef.current) return;

    const container = svgRef.current;
    const width = container.clientWidth;
    const dimensions = { width, height, margin: { top: 20, right: 20, bottom: 20, left: 20 } };
    const { svg, g } = createChart.responsiveSvg(container, dimensions);

    // Create tooltip
    const tooltipDiv = tooltip.create(container);

    // Process data based on view mode
    const processedData = processDataForView(data, viewMode, selectedLayer);
    
    if (viewMode === 'dependency') {
      renderDependencyGraph(g, processedData, dimensions, tooltipDiv);
    } else if (viewMode === 'layers') {
      renderLayerDiagram(g, processedData, dimensions, tooltipDiv);
    } else if (viewMode === 'integrations') {
      renderIntegrationMap(g, processedData, dimensions, tooltipDiv);
    }

    // Add zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
        setZoomLevel(event.transform.k);
      });

    svg.call(zoom as any);

    // Store reference to cleanup simulation
    if ((window as any).currentSimulation) {
      (window as any).currentSimulation.stop();
    }
    (window as any).currentSimulation = simulation;
  };

  const processDataForView = (data: ArchitectureData, mode: ViewMode, layer: string) => {
    let filteredComponents = data.components;
    
    if (layer !== 'all') {
      filteredComponents = data.components.filter(comp => 
        comp.type === layer || comp.name.toLowerCase().includes(layer.toLowerCase())
      );
    }

    switch (mode) {
      case 'dependency':
        return transformData.componentsToDependencyGraph(filteredComponents);
      case 'layers':
        return groupComponentsByLayer(filteredComponents, data.layers);
      case 'integrations':
        return processIntegrationData(filteredComponents, data.integrationPoints || []);
      default:
        return { nodes: [], links: [] };
    }
  };

  const groupComponentsByLayer = (components: any[], layers: string[]) => {
    const layerGroups = layers.map(layer => ({
      id: layer,
      components: components.filter(comp => comp.type === layer || comp.name.includes(layer))
    }));

    const nodes = components.map(comp => ({
      id: comp.name,
      group: comp.type,
      layer: findComponentLayer(comp, layers),
      complexity: comp.complexity,
      dependencies: comp.dependencies?.length || 0
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

    return { nodes, links, layers: layerGroups };
  };

  const processIntegrationData = (components: any[], integrations: any[]) => {
    const nodes = components.map(comp => ({
      id: comp.name,
      type: comp.type,
      complexity: comp.complexity,
      integrations: integrations.filter(int => int.source === comp.name || int.target === comp.name).length
    }));

    const links = integrations.map(int => ({
      source: int.source,
      target: int.target,
      type: int.type,
      protocol: int.protocol || 'HTTP'
    }));

    return { nodes, links };
  };

  const findComponentLayer = (component: any, layers: string[]): string => {
    return layers.find(layer => 
      component.type === layer || 
      component.name.toLowerCase().includes(layer.toLowerCase())
    ) || 'unknown';
  };

  const renderDependencyGraph = (g: any, data: any, dimensions: any, tooltipDiv: any) => {
    const { width, height } = dimensions;
    const { nodes, links } = data;

    // Create force simulation
    const sim = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id((d: any) => d.id).distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(30));

    setSimulation(sim);

    // Create color scale
    const groupNames: string[] = nodes.map((d: any) => String(d.group));
    const uniqueGroups = Array.from(new Set(groupNames));
    const colorScale = d3.scaleOrdinal<string>()
      .domain(uniqueGroups)
      .range(colorSchemes.technology);

    // Draw links
    const link = g.selectAll('.link')
      .data(links)
      .enter().append('line')
      .attr('class', 'link')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', 2);

    // Draw nodes
    const node = g.selectAll('.node')
      .data(nodes)
      .enter().append('circle')
      .attr('class', 'node')
      .attr('r', (d: any) => Math.max(10, Math.min(30, d.complexity * 5)))
      .attr('fill', (d: any) => colorScale(d.group))
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer')
      .call(d3.drag<SVGCircleElement, any>()
        .on('start', dragStarted)
        .on('drag', dragged)
        .on('end', dragEnded) as any);

    // Add labels
    const labels = g.selectAll('.label')
      .data(nodes)
      .enter().append('text')
      .attr('class', 'label')
      .attr('dy', -35)
      .attr('text-anchor', 'middle')
      .style('font-size', '12px')
      .style('font-weight', 'bold')
      .style('fill', '#333')
      .style('pointer-events', 'none')
      .text((d: any) => d.id.length > 15 ? d.id.substr(0, 12) + '...' : d.id);

    // Add interactions
    node
      .on('mouseover', (event: MouseEvent, d: any) => {
        const content = `
          <strong>${d.id}</strong><br/>
          Type: ${d.group}<br/>
          Complexity: ${d.complexity}<br/>
          Dependencies: ${d.dependencies}
        `;
        tooltip.show(tooltipDiv, content, event);
        
        // Highlight connected nodes
        highlightConnections(d, node, link);
      })
      .on('mouseout', () => {
        tooltip.hide(tooltipDiv);
        resetHighlights(node, link);
      })
      .on('click', (event: MouseEvent, d: any) => {
        if (onComponentClick) {
          onComponentClick(d);
        }
      });

    // Update positions on simulation tick
    sim.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      node
        .attr('cx', (d: any) => d.x)
        .attr('cy', (d: any) => d.y);

      labels
        .attr('x', (d: any) => d.x)
        .attr('y', (d: any) => d.y);
    });

    // Drag functions
    function dragStarted(event: any, d: any) {
      if (!event.active) sim.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event: any, d: any) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragEnded(event: any, d: any) {
      if (!event.active) sim.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }
  };

  const renderLayerDiagram = (g: any, data: any, dimensions: any, tooltipDiv: any) => {
    const { width, height } = dimensions;
    const { nodes, layers } = data;

    const layerHeight = height / Math.max(layers.length, 1);
    const colorScale = d3.scaleOrdinal<string>()
      .domain(layers.map((l: any) => l.id))
      .range(colorSchemes.primary);

    // Draw layer backgrounds
    layers.forEach((layer: any, i: number) => {
      g.append('rect')
        .attr('x', 0)
        .attr('y', i * layerHeight)
        .attr('width', width)
        .attr('height', layerHeight)
        .attr('fill', colorScale(layer.id))
        .attr('opacity', 0.1)
        .attr('stroke', colorScale(layer.id))
        .attr('stroke-width', 2);

      g.append('text')
        .attr('x', 10)
        .attr('y', i * layerHeight + 20)
        .style('font-size', '14px')
        .style('font-weight', 'bold')
        .style('fill', colorScale(layer.id))
        .text(layer.id);
    });

    // Position components within layers
    layers.forEach((layer: any, layerIndex: number) => {
      const layerComponents = nodes.filter((n: any) => n.layer === layer.id);
      const componentsPerRow = Math.ceil(Math.sqrt(layerComponents.length));
      
      layerComponents.forEach((comp: any, compIndex: number) => {
        const row = Math.floor(compIndex / componentsPerRow);
        const col = compIndex % componentsPerRow;
        
        const x = (col + 1) * (width / (componentsPerRow + 1));
        const y = layerIndex * layerHeight + (row + 1) * (layerHeight / (Math.ceil(layerComponents.length / componentsPerRow) + 1));
        
        // Draw component
        g.append('circle')
          .attr('cx', x)
          .attr('cy', y)
          .attr('r', Math.max(8, Math.min(20, comp.complexity * 3)))
          .attr('fill', colorScale(layer.id))
          .attr('stroke', '#fff')
          .attr('stroke-width', 2)
          .style('cursor', 'pointer')
          .on('mouseover', (event: MouseEvent) => {
            const content = `
              <strong>${comp.id}</strong><br/>
              Layer: ${comp.layer}<br/>
              Complexity: ${comp.complexity}<br/>
              Dependencies: ${comp.dependencies}
            `;
            tooltip.show(tooltipDiv, content, event);
          })
          .on('mouseout', () => tooltip.hide(tooltipDiv))
          .on('click', () => onComponentClick && onComponentClick(comp));

        // Add label
        g.append('text')
          .attr('x', x)
          .attr('y', y - 25)
          .attr('text-anchor', 'middle')
          .style('font-size', '10px')
          .style('fill', '#333')
          .style('pointer-events', 'none')
          .text(comp.id.length > 10 ? comp.id.substr(0, 8) + '...' : comp.id);
      });
    });
  };

  const renderIntegrationMap = (g: any, data: any, dimensions: any, tooltipDiv: any) => {
    const { width, height } = dimensions;
    const { nodes, links } = data;

    // Create force simulation optimized for integration visualization
    const sim = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id((d: any) => d.id).distance(120))
      .force('charge', d3.forceManyBody().strength(-400))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(40));

    setSimulation(sim);

    const nodeTypes: string[] = nodes.map((d: any) => String(d.type));
    const uniqueTypes = Array.from(new Set(nodeTypes));
    const colorScale = d3.scaleOrdinal<string>()
      .domain(uniqueTypes)
      .range(colorSchemes.technology);

    // Draw integration links with different styles for different protocols
    const link = g.selectAll('.integration-link')
      .data(links)
      .enter().append('line')
      .attr('class', 'integration-link')
      .attr('stroke', (d: any) => d.protocol === 'HTTP' ? '#2196f3' : d.protocol === 'HTTPS' ? '#4caf50' : '#ff9800')
      .attr('stroke-width', 3)
      .attr('stroke-dasharray', (d: any) => d.type === 'async' ? '5,5' : 'none')
      .attr('opacity', 0.7);

    // Draw nodes with size based on integration count
    const node = g.selectAll('.integration-node')
      .data(nodes)
      .enter().append('circle')
      .attr('class', 'integration-node')
      .attr('r', (d: any) => Math.max(15, Math.min(40, 15 + d.integrations * 3)))
      .attr('fill', (d: any) => colorScale(d.type))
      .attr('stroke', '#fff')
      .attr('stroke-width', 3)
      .style('cursor', 'pointer')
      .call(d3.drag<SVGCircleElement, any>()
        .on('start', dragStarted)
        .on('drag', dragged)
        .on('end', dragEnded) as any);

    // Add integration count badges
    const badges = g.selectAll('.integration-badge')
      .data(nodes)
      .enter().append('circle')
      .attr('class', 'integration-badge')
      .attr('r', 8)
      .attr('fill', '#f44336')
      .attr('stroke', '#fff')
      .attr('stroke-width', 1);

    const badgeText = g.selectAll('.badge-text')
      .data(nodes)
      .enter().append('text')
      .attr('class', 'badge-text')
      .attr('text-anchor', 'middle')
      .attr('dy', 4)
      .style('font-size', '10px')
      .style('font-weight', 'bold')
      .style('fill', '#fff')
      .style('pointer-events', 'none')
      .text((d: any) => d.integrations);

    // Add labels
    const labels = g.selectAll('.integration-label')
      .data(nodes)
      .enter().append('text')
      .attr('class', 'integration-label')
      .attr('dy', -50)
      .attr('text-anchor', 'middle')
      .style('font-size', '12px')
      .style('font-weight', 'bold')
      .style('fill', '#333')
      .style('pointer-events', 'none')
      .text((d: any) => d.id);

    // Add interactions
    node
      .on('mouseover', (event: MouseEvent, d: any) => {
        const content = `
          <strong>${d.id}</strong><br/>
          Type: ${d.type}<br/>
          Integrations: ${d.integrations}<br/>
          Complexity: ${d.complexity}
        `;
        tooltip.show(tooltipDiv, content, event);
      })
      .on('mouseout', () => tooltip.hide(tooltipDiv))
      .on('click', (event: MouseEvent, d: any) => {
        if (onComponentClick) onComponentClick(d);
      });

    // Update positions on simulation tick
    sim.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      node
        .attr('cx', (d: any) => d.x)
        .attr('cy', (d: any) => d.y);

      badges
        .attr('cx', (d: any) => d.x + 20)
        .attr('cy', (d: any) => d.y - 20);

      badgeText
        .attr('x', (d: any) => d.x + 20)
        .attr('y', (d: any) => d.y - 20);

      labels
        .attr('x', (d: any) => d.x)
        .attr('y', (d: any) => d.y);
    });

    function dragStarted(event: any, d: any) {
      if (!event.active) sim.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event: any, d: any) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragEnded(event: any, d: any) {
      if (!event.active) sim.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }
  };

  const highlightConnections = (d: any, nodes: any, links: any) => {
    const connectedNodes = new Set([d.id]);
    links.each((l: any) => {
      if (l.source.id === d.id) connectedNodes.add(l.target.id);
      if (l.target.id === d.id) connectedNodes.add(l.source.id);
    });

    nodes.attr('opacity', (n: any) => connectedNodes.has(n.id) ? 1 : 0.3);
    links.attr('opacity', (l: any) => l.source.id === d.id || l.target.id === d.id ? 1 : 0.1);
  };

  const resetHighlights = (nodes: any, links: any) => {
    nodes.attr('opacity', 1);
    links.attr('opacity', 0.6);
  };

  const handleZoom = (direction: 'in' | 'out' | 'reset') => {
    if (!svgRef.current) return;
    
    const svg = d3.select(svgRef.current).select('svg');
    const zoom = d3.zoom<SVGSVGElement, unknown>();
    
    if (direction === 'in') {
      svg.transition().call(zoom.scaleBy as any, 1.5);
    } else if (direction === 'out') {
      svg.transition().call(zoom.scaleBy as any, 0.75);
    } else {
      svg.transition().call(zoom.transform as any, d3.zoomIdentity);
    }
  };

  const handleExport = () => {
    if (!svgRef.current) return;
    
    const svg = svgRef.current.querySelector('svg') as SVGElement;
    if (svg) {
      exportUtils.downloadAsPng(svg, `${exportFilename}-${viewMode}`, 1200, 800);
    }
  };

  const getViewModeDescription = (mode: ViewMode): string => {
    switch (mode) {
      case 'dependency':
        return 'Shows component dependencies and relationships in a force-directed layout';
      case 'layers':
        return 'Displays components organized by architectural layers';
      case 'integrations':
        return 'Visualizes integration points and communication patterns';
      default:
        return '';
    }
  };

  if (!data || !data.components || data.components.length === 0) {
    return (
      <Card>
        <CardContent>
          <Alert severity="info">
            No architecture data available. Complete a repository analysis to see component relationships and structure.
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Box>
            <Typography variant="h6" gutterBottom>
              Architecture Visualization
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {getViewModeDescription(viewMode)}
            </Typography>
          </Box>
          
          <Box display="flex" gap={1}>
            <IconButton onClick={() => handleZoom('out')} size="small">
              <ZoomOutIcon />
            </IconButton>
            <IconButton onClick={() => handleZoom('reset')} size="small">
              <CenterIcon />
            </IconButton>
            <IconButton onClick={() => handleZoom('in')} size="small">
              <ZoomInIcon />
            </IconButton>
            <IconButton onClick={handleExport} size="small">
              <DownloadIcon />
            </IconButton>
          </Box>
        </Box>

        {/* Controls */}
        <Box display="flex" gap={2} mb={3} flexWrap="wrap">
          <ButtonGroup size="small">
            <Button
              variant={viewMode === 'dependency' ? 'contained' : 'outlined'}
              onClick={() => setViewMode('dependency')}
            >
              Dependencies
            </Button>
            <Button
              variant={viewMode === 'layers' ? 'contained' : 'outlined'}
              onClick={() => setViewMode('layers')}
            >
              Layers
            </Button>
            <Button
              variant={viewMode === 'integrations' ? 'contained' : 'outlined'}
              onClick={() => setViewMode('integrations')}
            >
              Integrations
            </Button>
          </ButtonGroup>

          <FormControl size="small" style={{ minWidth: 120 }}>
            <InputLabel>Filter Layer</InputLabel>
            <Select
              value={selectedLayer}
              onChange={(e) => setSelectedLayer(e.target.value)}
              label="Filter Layer"
            >
              <MenuItem value="all">All Layers</MenuItem>
              {data.layers.map(layer => (
                <MenuItem key={layer} value={layer}>{layer}</MenuItem>
              ))}
            </Select>
          </FormControl>

          <Chip
            label={`Zoom: ${Math.round(zoomLevel * 100)}%`}
            variant="outlined"
            size="small"
          />
        </Box>

        {/* Stats */}
        <Box display="flex" gap={2} mb={2}>
          <Chip label={`${data.components.length} Components`} size="small" />
          <Chip label={`${data.layers.length} Layers`} size="small" />
          {data.patterns && <Chip label={`${data.patterns.length} Patterns`} size="small" />}
        </Box>

        {/* Visualization */}
        <Box
          ref={svgRef}
          sx={{
            width: '100%',
            height: `${height}px`,
            border: '1px solid',
            borderColor: 'divider',
            borderRadius: 1,
            overflow: 'hidden',
            '& svg': {
              cursor: 'grab',
              '&:active': {
                cursor: 'grabbing'
              }
            }
          }}
        />

        {/* Legend */}
        {data.patterns && data.patterns.length > 0 && (
          <Box mt={2}>
            <Typography variant="subtitle2" gutterBottom>
              Detected Patterns:
            </Typography>
            <Box display="flex" gap={1} flexWrap="wrap">
              {data.patterns.map(pattern => (
                <Chip key={pattern} label={pattern} size="small" variant="outlined" />
              ))}
            </Box>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default ArchitectureVisualization;