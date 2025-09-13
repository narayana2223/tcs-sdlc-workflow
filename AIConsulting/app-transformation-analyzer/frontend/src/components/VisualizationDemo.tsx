/**
 * Visualization Demo Component
 * Showcases all visualization components with sample data and export functionality
 */

import React, { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Button,
  ButtonGroup,
  Tab,
  Tabs,
  Card,
  CardContent,
  Grid,
  IconButton,
  Tooltip,
  Alert
} from '@mui/material';
import {
  Architecture as ArchIcon,
  Assessment as GapIcon,
  Memory as TechIcon,
  Download as DownloadIcon,
  PictureAsPdf as PdfIcon,
  Slideshow as PptIcon
} from '@mui/icons-material';

import ArchitectureVisualization from './ArchitectureVisualization';
import GapAnalysis from './GapAnalysis';
import TechnologyStack from './TechnologyStack';
import { AdvancedExporter } from '../utils/exportUtils';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <div role="tabpanel" hidden={value !== index}>
    {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
  </div>
);

// Sample data for demonstrations
const sampleArchitectureData = {
  components: [
    { name: 'API Gateway', type: 'service', complexity: 3, dependencies: ['Auth Service', 'User Service'] },
    { name: 'Auth Service', type: 'service', complexity: 2, dependencies: ['Database'] },
    { name: 'User Service', type: 'service', complexity: 4, dependencies: ['Database', 'Cache'] },
    { name: 'Order Service', type: 'service', complexity: 5, dependencies: ['Database', 'Payment Service'] },
    { name: 'Payment Service', type: 'service', complexity: 3, dependencies: ['External API'] },
    { name: 'Database', type: 'data', complexity: 2, dependencies: [] },
    { name: 'Cache', type: 'data', complexity: 1, dependencies: [] },
    { name: 'External API', type: 'external', complexity: 1, dependencies: [] },
    { name: 'Frontend App', type: 'ui', complexity: 6, dependencies: ['API Gateway'] },
    { name: 'Admin Panel', type: 'ui', complexity: 3, dependencies: ['API Gateway'] }
  ],
  layers: ['ui', 'service', 'data', 'external'],
  patterns: ['Microservices', 'API Gateway', 'Database per Service', 'CQRS'],
  integrationPoints: [
    { source: 'API Gateway', target: 'Auth Service', type: 'sync', protocol: 'HTTPS' },
    { source: 'API Gateway', target: 'User Service', type: 'sync', protocol: 'HTTPS' },
    { source: 'Order Service', target: 'Payment Service', type: 'async', protocol: 'HTTP' }
  ]
};

const sampleGapAnalysisData = {
  factorEvaluations: {
    codebase: { factor: 'codebase', title: 'Codebase', score: 0.9, compliant: true, confidence: 0.95 },
    dependencies: { factor: 'dependencies', title: 'Dependencies', score: 0.7, compliant: true, confidence: 0.8 },
    config: { factor: 'config', title: 'Config', score: 0.4, compliant: false, confidence: 0.9 },
    backing_services: { factor: 'backing_services', title: 'Backing Services', score: 0.8, compliant: true, confidence: 0.85 },
    build_release_run: { factor: 'build_release_run', title: 'Build, Release, Run', score: 0.3, compliant: false, confidence: 0.7 },
    processes: { factor: 'processes', title: 'Processes', score: 0.6, compliant: false, confidence: 0.8 },
    port_binding: { factor: 'port_binding', title: 'Port Binding', score: 0.9, compliant: true, confidence: 0.95 },
    concurrency: { factor: 'concurrency', title: 'Concurrency', score: 0.5, compliant: false, confidence: 0.75 },
    disposability: { factor: 'disposability', title: 'Disposability', score: 0.4, compliant: false, confidence: 0.8 },
    dev_prod_parity: { factor: 'dev_prod_parity', title: 'Dev/Prod Parity', score: 0.6, compliant: false, confidence: 0.9 },
    logs: { factor: 'logs', title: 'Logs', score: 0.8, compliant: true, confidence: 0.85 },
    admin_processes: { factor: 'admin_processes', title: 'Admin Processes', score: 0.7, compliant: true, confidence: 0.8 }
  },
  gaps: [
    { factor_name: 'Config', severity: 'high' as const, impact: 'high' as const, description: 'Configuration stored in code, not environment', effort_estimate: 16 },
    { factor_name: 'Build/Release/Run', severity: 'critical' as const, impact: 'high' as const, description: 'Manual deployment process', effort_estimate: 40 },
    { factor_name: 'Processes', severity: 'medium' as const, impact: 'medium' as const, description: 'Not fully stateless', effort_estimate: 24 },
    { factor_name: 'Concurrency', severity: 'medium' as const, impact: 'medium' as const, description: 'Limited horizontal scaling', effort_estimate: 32 },
    { factor_name: 'Disposability', severity: 'high' as const, impact: 'medium' as const, description: 'Slow startup and shutdown', effort_estimate: 20 }
  ],
  recommendations: [
    { title: 'Externalize Configuration', priority: 'high' as const, complexity: 'low' as const, estimated_effort_hours: 16, factor_name: 'Config' },
    { title: 'Implement CI/CD Pipeline', priority: 'critical' as const, complexity: 'high' as const, estimated_effort_hours: 40, factor_name: 'Build/Release/Run' },
    { title: 'Refactor to Stateless Design', priority: 'medium' as const, complexity: 'medium' as const, estimated_effort_hours: 24, factor_name: 'Processes' },
    { title: 'Add Horizontal Scaling', priority: 'medium' as const, complexity: 'high' as const, estimated_effort_hours: 32, factor_name: 'Concurrency' },
    { title: 'Optimize Startup Time', priority: 'high' as const, complexity: 'low' as const, estimated_effort_hours: 20, factor_name: 'Disposability' },
    { title: 'Standardize Logging', priority: 'low' as const, complexity: 'low' as const, estimated_effort_hours: 8, factor_name: 'Logs' }
  ]
};

const sampleTechStackData = {
  projectMetrics: {
    total_files: 1247,
    total_lines_of_code: 84532,
    languages: {
      'TypeScript': 45230,
      'JavaScript': 18765,
      'Python': 12450,
      'CSS': 4587,
      'HTML': 2890,
      'JSON': 610
    }
  },
  technologyStack: {
    primary_language: 'TypeScript',
    frameworks: ['React', 'Express.js', 'FastAPI', 'Material-UI'],
    databases: ['PostgreSQL', 'Redis', 'MongoDB'],
    build_tools: ['Webpack', 'Babel', 'TypeScript Compiler'],
    deployment_tools: ['Docker', 'Kubernetes', 'GitHub Actions'],
    testing_frameworks: ['Jest', 'React Testing Library', 'Pytest']
  },
  dependencyAnalysis: {
    direct_dependencies: {
      'react': '18.2.0',
      'express': '4.18.2',
      'fastapi': '0.104.0',
      'axios': '1.6.0',
      'lodash': '4.17.20',
      'moment': '2.29.0'
    },
    transitive_dependencies: {
      'prop-types': '15.8.1',
      'js-tokens': '4.0.0',
      'loose-envify': '1.4.0'
    },
    outdated_dependencies: {
      'moment': { current: '2.29.0', latest: '2.30.1' },
      'lodash': { current: '4.17.20', latest: '4.17.21' }
    },
    security_vulnerabilities: [
      { package: 'moment', severity: 'medium' as const, description: 'Inefficient Regular Expression Complexity' },
      { package: 'lodash', severity: 'high' as const, description: 'Prototype Pollution vulnerability' }
    ]
  }
};

const VisualizationDemo: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [exporting, setExporting] = useState(false);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleExportPDF = async () => {
    setExporting(true);
    try {
      const elements = [
        document.querySelector('[data-viz="architecture"]') as HTMLElement,
        document.querySelector('[data-viz="gap-analysis"]') as HTMLElement,
        document.querySelector('[data-viz="tech-stack"]') as HTMLElement
      ].filter(Boolean);

      await AdvancedExporter.exportToPDF(elements, {
        title: 'Application Analysis Report',
        author: 'App Transformation Analyzer',
        subject: 'Comprehensive Technical Analysis',
        keywords: ['architecture', 'gap analysis', '12-factor', 'technology stack']
      });
    } catch (error) {
      console.error('PDF export failed:', error);
    } finally {
      setExporting(false);
    }
  };

  const handleExportPPT = async () => {
    setExporting(true);
    try {
      const slides = [
        {
          title: 'Architecture Overview',
          content: document.querySelector('[data-viz="architecture"]') as HTMLElement,
          notes: 'Component relationships and integration patterns analysis'
        },
        {
          title: '12-Factor Gap Analysis',
          content: document.querySelector('[data-viz="gap-analysis"]') as HTMLElement,
          notes: 'Compliance assessment and recommendations for cloud readiness'
        },
        {
          title: 'Technology Stack Analysis',
          content: document.querySelector('[data-viz="tech-stack"]') as HTMLElement,
          notes: 'Language distribution, dependencies, and security assessment'
        }
      ];

      await AdvancedExporter.exportToPowerPoint(slides, {
        title: 'Application Analysis Presentation',
        author: 'App Transformation Analyzer'
      });
    } catch (error) {
      console.error('PowerPoint export failed:', error);
    } finally {
      setExporting(false);
    }
  };

  const handleExportInteractive = async () => {
    setExporting(true);
    try {
      const elements = [
        document.querySelector('[data-viz="architecture"]') as HTMLElement,
        document.querySelector('[data-viz="gap-analysis"]') as HTMLElement,
        document.querySelector('[data-viz="tech-stack"]') as HTMLElement
      ].filter(Boolean);

      const data = {
        architecture: sampleArchitectureData,
        gapAnalysis: sampleGapAnalysisData,
        technologyStack: sampleTechStackData
      };

      await AdvancedExporter.exportInteractiveReport(elements, data, {
        title: 'Interactive Analysis Report',
        author: 'App Transformation Analyzer'
      });
    } catch (error) {
      console.error('Interactive export failed:', error);
    } finally {
      setExporting(false);
    }
  };

  return (
    <Container maxWidth="xl">
      {/* Header */}
      <Box py={4}>
        <Typography variant="h3" gutterBottom align="center">
          Visualization Demo
        </Typography>
        <Typography variant="h6" color="text.secondary" align="center" mb={4}>
          Interactive D3.js visualizations for application transformation analysis
        </Typography>

        {/* Export Controls */}
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center">
              <Typography variant="h6">
                Export Options
              </Typography>
              <ButtonGroup disabled={exporting}>
                <Button
                  startIcon={<PdfIcon />}
                  onClick={handleExportPDF}
                  variant="outlined"
                >
                  Export PDF Report
                </Button>
                <Button
                  startIcon={<PptIcon />}
                  onClick={handleExportPPT}
                  variant="outlined"
                >
                  Export Slides
                </Button>
                <Button
                  startIcon={<DownloadIcon />}
                  onClick={handleExportInteractive}
                  variant="contained"
                >
                  Interactive Report
                </Button>
              </ButtonGroup>
            </Box>
            {exporting && (
              <Alert severity="info" sx={{ mt: 2 }}>
                Generating export... This may take a few moments.
              </Alert>
            )}
          </CardContent>
        </Card>

        {/* Tabs */}
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} centered>
            <Tab icon={<ArchIcon />} label="Architecture" />
            <Tab icon={<GapIcon />} label="Gap Analysis" />
            <Tab icon={<TechIcon />} label="Technology Stack" />
          </Tabs>
        </Box>

        {/* Tab Panels */}
        <TabPanel value={tabValue} index={0}>
          <Box data-viz="architecture">
            <ArchitectureVisualization
              data={sampleArchitectureData}
              height={600}
              onComponentClick={(component) => {
                console.log('Component clicked:', component);
                alert(`Component: ${component.id || component.name}\nType: ${component.group || component.type}\nComplexity: ${component.complexity}`);
              }}
              exportFilename="architecture-demo"
            />
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Box data-viz="gap-analysis">
            <GapAnalysis
              data={sampleGapAnalysisData}
              height={400}
              onGapClick={(gap) => {
                console.log('Gap clicked:', gap);
                alert(`Gap: ${gap.factor}\nSeverity: ${gap.severity}\nDescription: ${gap.description}`);
              }}
              onRecommendationClick={(recommendation) => {
                console.log('Recommendation clicked:', recommendation);
                alert(`Recommendation: ${recommendation.title}\nPriority: ${recommendation.priority}\nEffort: ${recommendation.effort} hours`);
              }}
              exportFilename="gap-analysis-demo"
            />
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Box data-viz="tech-stack">
            <TechnologyStack
              data={sampleTechStackData}
              height={400}
              onTechnologyClick={(technology) => {
                console.log('Technology clicked:', technology);
                alert(`Technology: ${technology.name || technology.id}\nCategory: ${technology.category || technology.group}`);
              }}
              exportFilename="tech-stack-demo"
            />
          </Box>
        </TabPanel>

        {/* Features Overview */}
        <Card sx={{ mt: 4 }}>
          <CardContent>
            <Typography variant="h5" gutterBottom>
              Visualization Features
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} md={4}>
                <Card variant="outlined">
                  <CardContent>
                    <ArchIcon color="primary" sx={{ fontSize: 40, mb: 2 }} />
                    <Typography variant="h6" gutterBottom>
                      Architecture Visualization
                    </Typography>
                    <Typography variant="body2">
                      • Interactive component dependency graphs<br/>
                      • Layer-based architecture diagrams<br/>
                      • Integration point mapping<br/>
                      • Force-directed layouts<br/>
                      • Zoom and pan navigation
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={4}>
                <Card variant="outlined">
                  <CardContent>
                    <GapIcon color="primary" sx={{ fontSize: 40, mb: 2 }} />
                    <Typography variant="h6" gutterBottom>
                      Gap Analysis
                    </Typography>
                    <Typography variant="body2">
                      • 12-factor compliance radar charts<br/>
                      • Gap severity heatmaps<br/>
                      • Priority vs complexity matrices<br/>
                      • Executive-friendly visualizations<br/>
                      • Filtering and sorting options
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={4}>
                <Card variant="outlined">
                  <CardContent>
                    <TechIcon color="primary" sx={{ fontSize: 40, mb: 2 }} />
                    <Typography variant="h6" gutterBottom>
                      Technology Stack
                    </Typography>
                    <Typography variant="body2">
                      • Language distribution pie charts<br/>
                      • Dependency security analysis<br/>
                      • Framework usage overview<br/>
                      • Vulnerability assessments<br/>
                      • Package update tracking
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {/* Export Formats */}
        <Card sx={{ mt: 4 }}>
          <CardContent>
            <Typography variant="h5" gutterBottom>
              Export Formats
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={4}>
                <Box display="flex" alignItems="center" gap={2}>
                  <PdfIcon color="error" />
                  <Box>
                    <Typography variant="subtitle1">PDF Reports</Typography>
                    <Typography variant="body2" color="text.secondary">
                      Executive summaries with title pages, TOC, and appendix
                    </Typography>
                  </Box>
                </Box>
              </Grid>
              <Grid item xs={12} md={4}>
                <Box display="flex" alignItems="center" gap={2}>
                  <PptIcon color="warning" />
                  <Box>
                    <Typography variant="subtitle1">PowerPoint Slides</Typography>
                    <Typography variant="body2" color="text.secondary">
                      Presentation-ready slides with speaker notes
                    </Typography>
                  </Box>
                </Box>
              </Grid>
              <Grid item xs={12} md={4}>
                <Box display="flex" alignItems="center" gap={2}>
                  <DownloadIcon color="primary" />
                  <Box>
                    <Typography variant="subtitle1">Interactive HTML</Typography>
                    <Typography variant="body2" color="text.secondary">
                      Self-contained reports with navigation and interactivity
                    </Typography>
                  </Box>
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Box>
    </Container>
  );
};

export default VisualizationDemo;