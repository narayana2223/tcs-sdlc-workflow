/**
 * Technology Stack Component
 * D3.js visualizations for technology stack analysis with proper TypeScript typing
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
  Tooltip as MuiTooltip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon
} from '@mui/material';
import {
  PieChart as PieIcon,
  AccountTree as DependencyIcon,
  Extension as FrameworkIcon,
  Download as DownloadIcon,
  Info as InfoIcon,
  Security as SecurityIcon,
  Update as UpdateIcon,
  Warning as WarningIcon
} from '@mui/icons-material';

// Proper TypeScript interfaces for D3 data structures
interface PieData {
  name: string;
  value: number;
  percentage?: number;
}

interface PieArcDatum extends d3.PieArcDatum<PieData> {}

interface DependencyNode {
  id: string;
  version: string;
  outdated: boolean;
  vulnerable: boolean;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

interface HierarchyDependencyNode extends d3.HierarchyCircularNode<DependencyNode> {
  r: number;
  x: number;
  y: number;
}

interface TechnologyStackData {
  projectMetrics: {
    total_files: number;
    total_lines_of_code: number;
    languages: Record<string, number>;
  };
  technologyStack: {
    primary_language: string;
    frameworks: string[];
    databases: string[];
    build_tools: string[];
    deployment_tools: string[];
    testing_frameworks: string[];
  };
  dependencyAnalysis: {
    direct_dependencies: Record<string, string>;
    transitive_dependencies: Record<string, string>;
    outdated_dependencies: Record<string, { current: string; latest: string }>;
    security_vulnerabilities: Array<{
      package: string;
      severity: 'low' | 'medium' | 'high' | 'critical';
      description: string;
    }>;
  };
}

interface TechnologyStackProps {
  data: TechnologyStackData;
  height?: number;
  onTechnologyClick?: (technology: any) => void;
  exportFilename?: string;
}

type ViewType = 'languages' | 'dependencies' | 'frameworks' | 'security';

// Color schemes
const colorSchemes = {
  technology: ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F'],
  error: ['#E74C3C', '#C0392B'],
  warning: ['#F39C12', '#E67E22', '#F1C40F'],
  success: ['#27AE60', '#2ECC71'],
  info: ['#3498DB', '#2980B9']
};

const TechnologyStack: React.FC<TechnologyStackProps> = ({
  data,
  height = 400,
  onTechnologyClick,
  exportFilename = 'technology-stack'
}) => {
  const languagesPieRef = useRef<HTMLDivElement>(null);
  const dependencyGraphRef = useRef<HTMLDivElement>(null);
  const frameworksRef = useRef<HTMLDivElement>(null);
  
  const [selectedView, setSelectedView] = useState<ViewType>('languages');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  // Helper functions
  const transformToPieData = (languages: Record<string, number>): PieData[] => {
    return Object.entries(languages)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value);
  };

  const createTooltip = (container: HTMLDivElement): d3.Selection<HTMLDivElement, unknown, null, undefined> => {
    return d3.select(container)
      .append('div')
      .style('position', 'absolute')
      .style('visibility', 'hidden')
      .style('background-color', 'rgba(0, 0, 0, 0.8)')
      .style('color', 'white')
      .style('padding', '8px')
      .style('border-radius', '4px')
      .style('font-size', '12px')
      .style('pointer-events', 'none')
      .style('z-index', '1000');
  };

  useEffect(() => {
    if (selectedView === 'languages' && languagesPieRef.current) {
      createLanguagesPieChart();
    } else if (selectedView === 'dependencies' && dependencyGraphRef.current) {
      createDependencyGraph();
    } else if (selectedView === 'frameworks' && frameworksRef.current) {
      createFrameworksChart();
    }
  }, [data, selectedView, selectedCategory]);

  const createLanguagesPieChart = () => {
    if (!languagesPieRef.current) return;

    const container = languagesPieRef.current;
    d3.select(container).selectAll("*").remove();

    const pieData = transformToPieData(data.projectMetrics.languages);
    const width = 400;
    const height = 400;
    const margin = 40;
    const radius = Math.min(width, height) / 2 - margin;

    const svg = d3.select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height);

    const g = svg.append('g')
      .attr('transform', `translate(${width / 2}, ${height / 2})`);

    const tooltip = createTooltip(container);

    // Create color scale
    const colorScale = d3.scaleOrdinal<string>()
      .domain(pieData.map(d => d.name))
      .range(colorSchemes.technology);

    // Create pie layout
    const pie = d3.pie<PieData>()
      .value(d => d.value)
      .sort((a, b) => b.value - a.value);

    // Create arc generators
    const arc = d3.arc<PieArcDatum>()
      .innerRadius(radius * 0.4)
      .outerRadius(radius);

    const labelArc = d3.arc<PieArcDatum>()
      .innerRadius(radius * 0.8)
      .outerRadius(radius * 0.8);

    const pieSlices = pie(pieData);
    const totalValue = d3.sum(pieData, d => d.value);

    // Create pie slices
    const arcs = g.selectAll('.pie-slice')
      .data(pieSlices)
      .enter().append('g')
      .attr('class', 'pie-slice');

    // Draw pie slices with animation
    arcs.append('path')
      .attr('d', arc)
      .attr('fill', d => colorScale(d.data.name))
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer')
      .on('mouseover', function(event: MouseEvent, d: PieArcDatum) {
        const percentage = ((d.data.value / totalValue) * 100).toFixed(1);
        const content = `<strong>${d.data.name}</strong><br/>Lines: ${d.data.value.toLocaleString()}<br/>Percentage: ${percentage}%`;
        
        tooltip
          .style('visibility', 'visible')
          .html(content)
          .style('left', (event.pageX + 10) + 'px')
          .style('top', (event.pageY - 10) + 'px');
        
        d3.select(this)
          .transition()
          .duration(200)
          .attr('transform', 'scale(1.05)');
      })
      .on('mouseout', function() {
        tooltip.style('visibility', 'hidden');
        d3.select(this)
          .transition()
          .duration(200)
          .attr('transform', 'scale(1)');
      })
      .on('click', function(event: MouseEvent, d: PieArcDatum) {
        if (onTechnologyClick) onTechnologyClick(d.data);
      });

    // Add labels
    arcs.append('text')
      .attr('transform', d => `translate(${labelArc.centroid(d)})`)
      .attr('text-anchor', 'middle')
      .style('font-size', '12px')
      .style('font-weight', 'bold')
      .style('fill', '#333')
      .text(d => {
        const percentage = ((d.data.value / totalValue) * 100);
        return percentage > 5 ? d.data.name : '';
      });

    // Add center label
    g.append('text')
      .attr('text-anchor', 'middle')
      .style('font-size', '16px')
      .style('font-weight', 'bold')
      .style('fill', '#333')
      .text('Languages');

    g.append('text')
      .attr('y', 20)
      .attr('text-anchor', 'middle')
      .style('font-size', '14px')
      .style('fill', '#666')
      .text(`${data.projectMetrics.total_lines_of_code.toLocaleString()} LOC`);
  };

  const createDependencyGraph = () => {
    if (!dependencyGraphRef.current) return;

    const container = dependencyGraphRef.current;
    d3.select(container).selectAll("*").remove();

    const dependencies = { ...data.dependencyAnalysis.direct_dependencies };
    const outdated = data.dependencyAnalysis.outdated_dependencies;
    const vulnerabilities = data.dependencyAnalysis.security_vulnerabilities;

    // Transform dependencies into node data
    const nodeData: DependencyNode[] = Object.keys(dependencies).map(dep => ({
      id: dep,
      version: dependencies[dep],
      outdated: !!outdated[dep],
      vulnerable: vulnerabilities.some(v => v.package === dep),
      severity: vulnerabilities.find(v => v.package === dep)?.severity || 'low'
    }));

    const width = 600;
    const height = 400;

    const svg = d3.select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height);

    const tooltip = createTooltip(container);

    // Create pack layout
    const pack = d3.pack<DependencyNode>()
      .size([width, height])
      .padding(3);

    const root = d3.hierarchy<DependencyNode>({ children: nodeData } as any)
      .sum(() => 1);

    const packedRoot = pack(root);

    const getNodeColor = (d: DependencyNode) => {
      if (d.vulnerable) {
        const severityColors = {
          critical: colorSchemes.error[0],
          high: colorSchemes.error[1],
          medium: colorSchemes.warning[0],
          low: colorSchemes.warning[1]
        };
        return severityColors[d.severity];
      }
      if (d.outdated) return colorSchemes.warning[2];
      return colorSchemes.success[0];
    };

    // Draw dependency nodes
    const nodes = svg.selectAll('.dependency-node')
      .data(packedRoot.children || [])
      .enter().append('g')
      .attr('class', 'dependency-node')
      .attr('transform', d => `translate(${d.x}, ${d.y})`);

    nodes.append('circle')
      .attr('r', d => Math.max(8, Math.min(25, d.r)))
      .attr('fill', d => {
        const data = d.data as DependencyNode;
        return 'children' in data ? '#f0f0f0' : getNodeColor(data);
      })
      .attr('stroke', '#fff')
      .attr('stroke-width', 1)
      .style('cursor', 'pointer')
      .on('mouseover', function(event: MouseEvent, d) {
        const node = d as HierarchyDependencyNode;
        const content = `<strong>${node.data.id}</strong><br/>Version: ${node.data.version}<br/>Status: ${node.data.vulnerable ? 'Vulnerable' : node.data.outdated ? 'Outdated' : 'Current'}`;
        
        tooltip
          .style('visibility', 'visible')
          .html(content)
          .style('left', (event.pageX + 10) + 'px')
          .style('top', (event.pageY - 10) + 'px');
      })
      .on('mouseout', function() {
        tooltip.style('visibility', 'hidden');
      });

    nodes.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '0.3em')
      .style('font-size', d => `${Math.min(10, d.r / 3)}px`)
      .style('fill', '#333')
      .style('pointer-events', 'none')
      .text(d => {
        const data = d.data as DependencyNode;
        if (d.r > 15 && 'id' in data) {
          return data.id.substring(0, 8);
        }
        return '';
      });

    // Add vulnerability indicators
    nodes.filter(d => {
      const data = d.data as DependencyNode;
      return 'vulnerable' in data && data.vulnerable;
    })
      .append('circle')
      .attr('r', 4)
      .attr('cx', d => d.r * 0.7)
      .attr('cy', d => -d.r * 0.7)
      .attr('fill', '#ff0000')
      .style('pointer-events', 'none');
  };

  const createFrameworksChart = () => {
    if (!frameworksRef.current) return;

    const container = frameworksRef.current;
    d3.select(container).selectAll("*").remove();

    const frameworks = data.technologyStack.frameworks;
    const databases = data.technologyStack.databases;
    const buildTools = data.technologyStack.build_tools;
    const testingFrameworks = data.technologyStack.testing_frameworks;

    const categories = [
      { name: 'Frameworks', items: frameworks, color: colorSchemes.technology[0] },
      { name: 'Databases', items: databases, color: colorSchemes.technology[1] },
      { name: 'Build Tools', items: buildTools, color: colorSchemes.technology[2] },
      { name: 'Testing', items: testingFrameworks, color: colorSchemes.technology[3] }
    ];

    const width = 600;
    const height = 400;
    const margin = { top: 20, right: 20, bottom: 60, left: 60 };

    const svg = d3.select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height);

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left}, ${margin.top})`);

    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;

    const xScale = d3.scaleBand()
      .domain(categories.map(d => d.name))
      .range([0, chartWidth])
      .padding(0.2);

    const yScale = d3.scaleLinear()
      .domain([0, d3.max(categories, d => d.items.length) || 0])
      .range([chartHeight, 0]);

    // Draw bars
    g.selectAll('.framework-bar')
      .data(categories)
      .enter().append('rect')
      .attr('class', 'framework-bar')
      .attr('x', d => xScale(d.name) || 0)
      .attr('y', d => yScale(d.items.length))
      .attr('width', xScale.bandwidth())
      .attr('height', d => chartHeight - yScale(d.items.length))
      .attr('fill', d => d.color)
      .style('cursor', 'pointer');

    // Add value labels on bars
    g.selectAll('.bar-label')
      .data(categories)
      .enter().append('text')
      .attr('class', 'bar-label')
      .attr('x', d => (xScale(d.name) || 0) + xScale.bandwidth() / 2)
      .attr('y', d => yScale(d.items.length) - 5)
      .attr('text-anchor', 'middle')
      .style('font-size', '12px')
      .style('font-weight', 'bold')
      .style('fill', '#333')
      .text(d => d.items.length);

    // Add axes
    g.append('g')
      .attr('transform', `translate(0, ${chartHeight})`)
      .call(d3.axisBottom(xScale));

    g.append('g')
      .call(d3.axisLeft(yScale));

    // Add axis labels
    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('y', 0 - margin.left)
      .attr('x', 0 - (chartHeight / 2))
      .attr('dy', '1em')
      .style('text-anchor', 'middle')
      .style('font-size', '12px')
      .text('Count');

    g.append('text')
      .attr('transform', `translate(${chartWidth / 2}, ${chartHeight + margin.bottom - 20})`)
      .style('text-anchor', 'middle')
      .style('font-size', '12px')
      .text('Technology Categories');
  };

  const getSecurityIndicators = () => {
    const vulnerabilities = data.dependencyAnalysis.security_vulnerabilities;
    const outdated = Object.keys(data.dependencyAnalysis.outdated_dependencies);
    
    return {
      critical: vulnerabilities.filter(v => v.severity === 'critical').length,
      high: vulnerabilities.filter(v => v.severity === 'high').length,
      medium: vulnerabilities.filter(v => v.severity === 'medium').length,
      low: vulnerabilities.filter(v => v.severity === 'low').length,
      outdated: outdated.length
    };
  };

  const securityStats = getSecurityIndicators();

  const handleExport = async (format: 'png' | 'svg') => {
    // Implementation would depend on export utilities
    console.log(`Exporting ${selectedView} as ${format}`);
  };

  return (
    <Card>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">Technology Stack Analysis</Typography>
          <Box display="flex" gap={1}>
            <ButtonGroup size="small">
              <Button
                variant={selectedView === 'languages' ? 'contained' : 'outlined'}
                onClick={() => setSelectedView('languages')}
                startIcon={<PieIcon />}
              >
                Languages
              </Button>
              <Button
                variant={selectedView === 'dependencies' ? 'contained' : 'outlined'}
                onClick={() => setSelectedView('dependencies')}
                startIcon={<DependencyIcon />}
              >
                Dependencies
              </Button>
              <Button
                variant={selectedView === 'frameworks' ? 'contained' : 'outlined'}
                onClick={() => setSelectedView('frameworks')}
                startIcon={<FrameworkIcon />}
              >
                Frameworks
              </Button>
              <Button
                variant={selectedView === 'security' ? 'contained' : 'outlined'}
                onClick={() => setSelectedView('security')}
                startIcon={<SecurityIcon />}
              >
                Security
              </Button>
            </ButtonGroup>
            <IconButton size="small" onClick={() => handleExport('png')}>
              <DownloadIcon />
            </IconButton>
          </Box>
        </Box>

        <Grid container spacing={2}>
          <Grid item xs={12} md={8}>
            {selectedView === 'languages' && (
              <Box ref={languagesPieRef} height={height} />
            )}
            {selectedView === 'dependencies' && (
              <Box ref={dependencyGraphRef} height={height} />
            )}
            {selectedView === 'frameworks' && (
              <Box ref={frameworksRef} height={height} />
            )}
            {selectedView === 'security' && (
              <Box p={2}>
                <Typography variant="h6" gutterBottom>Security Overview</Typography>
                <Grid container spacing={2}>
                  <Grid item xs={6} sm={3}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="error">
                        {securityStats.critical}
                      </Typography>
                      <Typography variant="caption">Critical</Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="error">
                        {securityStats.high}
                      </Typography>
                      <Typography variant="caption">High</Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="warning.main">
                        {securityStats.medium}
                      </Typography>
                      <Typography variant="caption">Medium</Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="warning.main">
                        {securityStats.low}
                      </Typography>
                      <Typography variant="caption">Low</Typography>
                    </Box>
                  </Grid>
                </Grid>
                
                {securityStats.outdated > 0 && (
                  <Alert severity="warning" sx={{ mt: 2 }}>
                    {securityStats.outdated} dependencies are outdated and should be updated.
                  </Alert>
                )}
              </Box>
            )}
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Box p={2}>
              <Typography variant="subtitle1" gutterBottom>
                {selectedView === 'languages' && 'Language Statistics'}
                {selectedView === 'dependencies' && 'Dependency Information'}
                {selectedView === 'frameworks' && 'Framework Categories'}
                {selectedView === 'security' && 'Security Details'}
              </Typography>
              
              {selectedView === 'languages' && (
                <List dense>
                  <ListItem>
                    <ListItemText 
                      primary="Total Files" 
                      secondary={data.projectMetrics.total_files.toLocaleString()} 
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary="Lines of Code" 
                      secondary={data.projectMetrics.total_lines_of_code.toLocaleString()} 
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary="Primary Language" 
                      secondary={data.technologyStack.primary_language} 
                    />
                  </ListItem>
                </List>
              )}
              
              {selectedView === 'dependencies' && (
                <List dense>
                  <ListItem>
                    <ListItemText 
                      primary="Direct Dependencies" 
                      secondary={Object.keys(data.dependencyAnalysis.direct_dependencies).length} 
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary="Outdated" 
                      secondary={Object.keys(data.dependencyAnalysis.outdated_dependencies).length} 
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary="Security Issues" 
                      secondary={data.dependencyAnalysis.security_vulnerabilities.length} 
                    />
                  </ListItem>
                </List>
              )}
            </Box>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

export default TechnologyStack;