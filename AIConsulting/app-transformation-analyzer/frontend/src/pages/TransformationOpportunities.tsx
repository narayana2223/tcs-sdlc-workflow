/**
 * Transformation Opportunities Page
 * Comprehensive opportunity explorer with impact vs effort matrix, filtering, and detailed views
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Paper,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  InputAdornment,
  Slider,
  Switch,
  FormControlLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  LinearProgress,
  Alert,
  Tooltip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Fab
} from '@mui/material';

import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  ExpandMore as ExpandMoreIcon,
  TrendingUp as TrendingUpIcon,
  Schedule as ScheduleIcon,
  AttachMoney as MoneyIcon,
  Assessment as AssessmentIcon,
  Code as CodeIcon,
  Business as BusinessIcon,
  Security as SecurityIcon,
  Speed as SpeedIcon,
  AutoAwesome as AIIcon,
  Timeline as TimelineIcon,
  Group as GroupIcon,
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Close as CloseIcon,
  Visibility as ViewIcon,
  GetApp as ExportIcon
} from '@mui/icons-material';

import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Cell } from 'recharts';

// Mock data interfaces (these would typically come from a service)
interface TransformationOpportunity {
  id: string;
  title: string;
  description: string;
  category: string;
  type: string;
  businessValue: string;
  impactScore: number;
  effortScore: number;
  roiScore: number;
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH';
  implementationTimeline: string;
  estimatedCost: string;
  estimatedSavings: string;
  priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  relatedFactors: string[];
  businessMetrics: BusinessMetric[];
  stakeholders: string[];
  successCriteria: string[];
  potentialChallenges: string[];
}

interface BusinessMetric {
  name: string;
  current: string;
  target: string;
  improvement: string;
  timeframe: string;
}

const mockOpportunities: TransformationOpportunity[] = [
  {
    id: 'nlp-doc-automation',
    title: 'Automated Document Processing with NLP',
    description: 'Implement intelligent document processing to extract, classify, and route documents automatically using natural language processing.',
    category: 'NLP',
    type: 'STRATEGIC',
    businessValue: 'Reduce manual document processing by 80%, improve accuracy by 95%, and enable 24/7 processing capability.',
    impactScore: 9,
    effortScore: 6,
    roiScore: 135,
    riskLevel: 'MEDIUM',
    implementationTimeline: '6-8 months',
    estimatedCost: '$120,000 - $180,000',
    estimatedSavings: '$450,000 annually',
    priority: 'HIGH',
    relatedFactors: ['Factor VI: Processes', 'Factor XII: Admin processes', 'Factor IV: Backing services'],
    businessMetrics: [
      { name: 'Processing Time', current: '4-6 hours', target: '15-30 minutes', improvement: '85% faster', timeframe: '3 months' },
      { name: 'Accuracy Rate', current: '87%', target: '99.5%', improvement: '+12.5%', timeframe: '4 months' }
    ],
    stakeholders: ['Chief Technology Officer', 'Data Science Team', 'Business Process Owners'],
    successCriteria: ['Achieve 95%+ accuracy in document classification', 'Reduce processing time by 80%'],
    potentialChallenges: ['Data quality and availability', 'Technical integration complexity']
  },
  {
    id: 'intelligent-chatbot',
    title: 'Intelligent Customer Support Chatbot',
    description: 'Deploy an AI-powered chatbot to handle 70% of customer inquiries automatically with natural language understanding.',
    category: 'NLP',
    type: 'QUICK_WIN',
    businessValue: 'Reduce support costs by 60%, improve response times to <30 seconds, and increase customer satisfaction scores.',
    impactScore: 8,
    effortScore: 4,
    roiScore: 160,
    riskLevel: 'LOW',
    implementationTimeline: '3-4 months',
    estimatedCost: '$80,000 - $120,000',
    estimatedSavings: '$280,000 annually',
    priority: 'HIGH',
    relatedFactors: ['Factor III: Config', 'Factor IV: Backing services', 'Factor XI: Logs'],
    businessMetrics: [
      { name: 'Response Time', current: '2-4 hours', target: '<30 seconds', improvement: '95% faster', timeframe: '2 months' },
      { name: 'Cost per Ticket', current: '$15.50', target: '$3.20', improvement: '79% reduction', timeframe: '3 months' }
    ],
    stakeholders: ['Customer Success Team', 'IT Support', 'Customer Experience'],
    successCriteria: ['Handle 70%+ of inquiries automatically', 'Achieve 90%+ customer satisfaction'],
    potentialChallenges: ['Integration with existing systems', 'Training data quality']
  },
  {
    id: 'predictive-analytics',
    title: 'Predictive Analytics for Business Decisions',
    description: 'Implement machine learning models to predict customer behavior, sales trends, and operational issues before they occur.',
    category: 'DECISION',
    type: 'STRATEGIC',
    businessValue: 'Improve forecast accuracy by 40%, reduce operational issues by 50%, and increase revenue by 15% through better targeting.',
    impactScore: 9,
    effortScore: 7,
    roiScore: 115,
    riskLevel: 'MEDIUM',
    implementationTimeline: '8-12 months',
    estimatedCost: '$200,000 - $300,000',
    estimatedSavings: '$800,000 annually',
    priority: 'CRITICAL',
    relatedFactors: ['Factor I: Codebase', 'Factor IV: Backing services', 'Factor XI: Logs'],
    businessMetrics: [
      { name: 'Forecast Accuracy', current: '65%', target: '91%', improvement: '+40%', timeframe: '6 months' },
      { name: 'Revenue Impact', current: 'Baseline', target: '+15%', improvement: '$2.1M annually', timeframe: '12 months' }
    ],
    stakeholders: ['Chief Executive Officer', 'Business Intelligence Team', 'Data Analysts'],
    successCriteria: ['Improve forecast accuracy by 40%', 'Increase revenue by 15%'],
    potentialChallenges: ['Data quality and integration', 'Model complexity and validation']
  },
  {
    id: 'workflow-automation',
    title: 'Intelligent Process Automation',
    description: 'Automate repetitive business processes using RPA and AI to reduce manual work and improve consistency.',
    category: 'AUTOMATION',
    type: 'QUICK_WIN',
    businessValue: 'Eliminate 90% of manual data entry, reduce processing time by 75%, and improve accuracy to 99.5%.',
    impactScore: 8,
    effortScore: 5,
    roiScore: 128,
    riskLevel: 'LOW',
    implementationTimeline: '4-6 months',
    estimatedCost: '$100,000 - $150,000',
    estimatedSavings: '$350,000 annually',
    priority: 'HIGH',
    relatedFactors: ['Factor VI: Processes', 'Factor XII: Admin processes', 'Factor VIII: Concurrency'],
    businessMetrics: [
      { name: 'Manual Work', current: '40 hours/day', target: '4 hours/day', improvement: '90% reduction', timeframe: '4 months' },
      { name: 'Processing Time', current: '4 hours', target: '1 hour', improvement: '75% faster', timeframe: '3 months' }
    ],
    stakeholders: ['Chief Operations Officer', 'Business Process Owners', 'IT Operations'],
    successCriteria: ['Eliminate 90%+ manual tasks', 'Achieve 99.5% process accuracy'],
    potentialChallenges: ['Process mapping complexity', 'Change management']
  },
  {
    id: 'cloud-cost-optimization',
    title: 'Intelligent Cloud Cost Optimization',
    description: 'Implement automated cloud resource optimization to reduce infrastructure costs while maintaining performance.',
    category: 'COST_OPTIMIZATION',
    type: 'QUICK_WIN',
    businessValue: 'Reduce cloud costs by 40%, improve resource utilization by 60%, and eliminate waste through automation.',
    impactScore: 7,
    effortScore: 3,
    roiScore: 163,
    riskLevel: 'LOW',
    implementationTimeline: '2-3 months',
    estimatedCost: '$50,000 - $80,000',
    estimatedSavings: '$300,000 annually',
    priority: 'HIGH',
    relatedFactors: ['Factor VII: Port binding', 'Factor VIII: Concurrency', 'Factor IX: Disposability'],
    businessMetrics: [
      { name: 'Cloud Costs', current: '$750K/year', target: '$450K/year', improvement: '40% reduction', timeframe: '3 months' },
      { name: 'Resource Utilization', current: '35%', target: '85%', improvement: '+143%', timeframe: '2 months' }
    ],
    stakeholders: ['Chief Financial Officer', 'IT Operations', 'DevOps Team'],
    successCriteria: ['Reduce cloud costs by 40%', 'Improve resource utilization by 60%'],
    potentialChallenges: ['Performance impact monitoring', 'Team training']
  },
  {
    id: 'microservices-migration',
    title: 'Microservices Architecture Migration',
    description: 'Transform monolithic applications into microservices architecture for improved scalability and maintainability.',
    category: 'INFRASTRUCTURE',
    type: 'FOUNDATIONAL',
    businessValue: 'Improve deployment frequency by 10x, reduce downtime by 80%, and enable independent team scaling.',
    impactScore: 8,
    effortScore: 9,
    riskLevel: 'HIGH',
    roiScore: 71,
    implementationTimeline: '12-18 months',
    estimatedCost: '$400,000 - $600,000',
    estimatedSavings: '$500,000 annually',
    priority: 'MEDIUM',
    relatedFactors: ['Factor I: Codebase', 'Factor VI: Processes', 'Factor VIII: Concurrency'],
    businessMetrics: [
      { name: 'Deployment Frequency', current: '1/month', target: '10/month', improvement: '10x faster', timeframe: '12 months' },
      { name: 'System Downtime', current: '4 hours/month', target: '0.8 hours/month', improvement: '80% reduction', timeframe: '18 months' }
    ],
    stakeholders: ['Chief Technology Officer', 'Development Teams', 'DevOps Team'],
    successCriteria: ['Achieve 10x deployment frequency', 'Reduce downtime by 80%'],
    potentialChallenges: ['Complex system architecture changes', 'Team coordination', 'Legacy system integration']
  }
];

const categoryColors: { [key: string]: string } = {
  NLP: '#9C27B0',
  AUTOMATION: '#FF9800',
  DECISION: '#2196F3',
  DATA: '#4CAF50',
  INFRASTRUCTURE: '#607D8B',
  SECURITY: '#F44336',
  PERFORMANCE: '#00BCD4',
  COST_OPTIMIZATION: '#FFC107'
};

const categoryIcons: { [key: string]: React.ReactElement } = {
  NLP: <AIIcon />,
  AUTOMATION: <SpeedIcon />,
  DECISION: <AssessmentIcon />,
  DATA: <TimelineIcon />,
  INFRASTRUCTURE: <BusinessIcon />,
  SECURITY: <SecurityIcon />,
  PERFORMANCE: <TrendingUpIcon />,
  COST_OPTIMIZATION: <MoneyIcon />
};

const TransformationOpportunities: React.FC = () => {
  const [opportunities, setOpportunities] = useState<TransformationOpportunity[]>(mockOpportunities);
  const [filteredOpportunities, setFilteredOpportunities] = useState<TransformationOpportunity[]>(mockOpportunities);
  const [selectedOpportunity, setSelectedOpportunity] = useState<TransformationOpportunity | null>(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  const [priorityFilter, setPriorityFilter] = useState('ALL');
  const [riskFilter, setRiskFilter] = useState('ALL');
  const [impactRange, setImpactRange] = useState<number[]>([1, 10]);
  const [effortRange, setEffortRange] = useState<number[]>([1, 10]);
  const [showMatrix, setShowMatrix] = useState(true);
  const [selectedForComparison, setSelectedForComparison] = useState<string[]>([]);

  useEffect(() => {
    filterOpportunities();
  }, [searchTerm, categoryFilter, priorityFilter, riskFilter, impactRange, effortRange, opportunities]);

  const filterOpportunities = () => {
    let filtered = opportunities.filter(opp => {
      const matchesSearch = opp.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           opp.description.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesCategory = categoryFilter === 'ALL' || opp.category === categoryFilter;
      const matchesPriority = priorityFilter === 'ALL' || opp.priority === priorityFilter;
      const matchesRisk = riskFilter === 'ALL' || opp.riskLevel === riskFilter;
      const matchesImpact = opp.impactScore >= impactRange[0] && opp.impactScore <= impactRange[1];
      const matchesEffort = opp.effortScore >= effortRange[0] && opp.effortScore <= effortRange[1];

      return matchesSearch && matchesCategory && matchesPriority && matchesRisk && matchesImpact && matchesEffort;
    });

    setFilteredOpportunities(filtered);
  };

  const getPriorityColor = (priority: string): string => {
    switch (priority) {
      case 'CRITICAL': return '#D32F2F';
      case 'HIGH': return '#F57C00';
      case 'MEDIUM': return '#388E3C';
      case 'LOW': return '#1976D2';
      default: return '#757575';
    }
  };

  const getRiskColor = (risk: string): string => {
    switch (risk) {
      case 'HIGH': return '#F44336';
      case 'MEDIUM': return '#FF9800';
      case 'LOW': return '#4CAF50';
      default: return '#757575';
    }
  };

  const getQuadrantLabel = (impact: number, effort: number): string => {
    if (impact >= 7 && effort <= 4) return 'Quick Wins';
    if (impact >= 7 && effort >= 7) return 'Major Projects';
    if (impact <= 4 && effort <= 4) return 'Fill-ins';
    return 'Questionable';
  };

  const getQuadrantColor = (impact: number, effort: number): string => {
    if (impact >= 7 && effort <= 4) return '#4CAF50'; // Quick Wins - Green
    if (impact >= 7 && effort >= 7) return '#2196F3'; // Major Projects - Blue
    if (impact <= 4 && effort <= 4) return '#FFC107'; // Fill-ins - Yellow
    return '#FF5722'; // Questionable - Red
  };

  const handleOpportunityClick = (opportunity: TransformationOpportunity) => {
    setSelectedOpportunity(opportunity);
    setDetailDialogOpen(true);
  };

  const toggleComparison = (opportunityId: string) => {
    if (selectedForComparison.includes(opportunityId)) {
      setSelectedForComparison(selectedForComparison.filter(id => id !== opportunityId));
    } else if (selectedForComparison.length < 3) {
      setSelectedForComparison([...selectedForComparison, opportunityId]);
    }
  };

  const scatterData = filteredOpportunities.map(opp => ({
    x: opp.effortScore,
    y: opp.impactScore,
    opportunity: opp,
    color: getQuadrantColor(opp.impactScore, opp.effortScore)
  }));

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 600, color: 'primary.main' }}>
          🚀 Transformation Opportunities
        </Typography>
        <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 2 }}>
          Discover AI-powered transformation opportunities with concrete business impact and implementation roadmaps
        </Typography>

        {/* Key Metrics Cards */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'success.light', color: 'success.contrastText' }}>
              <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                {filteredOpportunities.length}
              </Typography>
              <Typography variant="body2">Total Opportunities</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'warning.light', color: 'warning.contrastText' }}>
              <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                ${Math.round(filteredOpportunities.reduce((sum, opp) => sum + parseFloat(opp.estimatedSavings.replace(/[^\d]/g, '')) / 1000, 0))}K
              </Typography>
              <Typography variant="body2">Total Annual Savings</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'info.light', color: 'info.contrastText' }}>
              <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                {Math.round(filteredOpportunities.reduce((sum, opp) => sum + opp.roiScore, 0) / filteredOpportunities.length)}%
              </Typography>
              <Typography variant="body2">Average ROI</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'secondary.light', color: 'secondary.contrastText' }}>
              <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                {filteredOpportunities.filter(opp => opp.priority === 'CRITICAL' || opp.priority === 'HIGH').length}
              </Typography>
              <Typography variant="body2">High Priority</Typography>
            </Paper>
          </Grid>
        </Grid>
      </Box>

      {/* Filters */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <FilterIcon />
          Filters & Controls
        </Typography>

        <Grid container spacing={2} alignItems="center">
          {/* Search */}
          <Grid item xs={12} md={3}>
            <TextField
              fullWidth
              placeholder="Search opportunities..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
              size="small"
            />
          </Grid>

          {/* Category Filter */}
          <Grid item xs={12} sm={6} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>Category</InputLabel>
              <Select
                value={categoryFilter}
                label="Category"
                onChange={(e) => setCategoryFilter(e.target.value)}
              >
                <MenuItem value="ALL">All Categories</MenuItem>
                <MenuItem value="NLP">NLP</MenuItem>
                <MenuItem value="AUTOMATION">Automation</MenuItem>
                <MenuItem value="DECISION">Decision</MenuItem>
                <MenuItem value="DATA">Data</MenuItem>
                <MenuItem value="INFRASTRUCTURE">Infrastructure</MenuItem>
                <MenuItem value="COST_OPTIMIZATION">Cost Optimization</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          {/* Priority Filter */}
          <Grid item xs={12} sm={6} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>Priority</InputLabel>
              <Select
                value={priorityFilter}
                label="Priority"
                onChange={(e) => setPriorityFilter(e.target.value)}
              >
                <MenuItem value="ALL">All Priorities</MenuItem>
                <MenuItem value="CRITICAL">Critical</MenuItem>
                <MenuItem value="HIGH">High</MenuItem>
                <MenuItem value="MEDIUM">Medium</MenuItem>
                <MenuItem value="LOW">Low</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          {/* Risk Filter */}
          <Grid item xs={12} sm={6} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>Risk Level</InputLabel>
              <Select
                value={riskFilter}
                label="Risk Level"
                onChange={(e) => setRiskFilter(e.target.value)}
              >
                <MenuItem value="ALL">All Risk Levels</MenuItem>
                <MenuItem value="LOW">Low</MenuItem>
                <MenuItem value="MEDIUM">Medium</MenuItem>
                <MenuItem value="HIGH">High</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          {/* Matrix Toggle */}
          <Grid item xs={12} sm={6} md={3}>
            <FormControlLabel
              control={<Switch checked={showMatrix} onChange={(e) => setShowMatrix(e.target.checked)} />}
              label="Show Impact vs Effort Matrix"
            />
          </Grid>

          {/* Impact Range */}
          <Grid item xs={12} md={6}>
            <Typography gutterBottom>Impact Score Range</Typography>
            <Slider
              value={impactRange}
              onChange={(e, newValue) => setImpactRange(newValue as number[])}
              valueLabelDisplay="auto"
              min={1}
              max={10}
              marks={[
                { value: 1, label: '1' },
                { value: 5, label: '5' },
                { value: 10, label: '10' }
              ]}
            />
          </Grid>

          {/* Effort Range */}
          <Grid item xs={12} md={6}>
            <Typography gutterBottom>Effort Score Range</Typography>
            <Slider
              value={effortRange}
              onChange={(e, newValue) => setEffortRange(newValue as number[])}
              valueLabelDisplay="auto"
              min={1}
              max={10}
              marks={[
                { value: 1, label: '1 (Low)' },
                { value: 5, label: '5' },
                { value: 10, label: '10 (High)' }
              ]}
            />
          </Grid>
        </Grid>
      </Paper>

      {/* Impact vs Effort Matrix */}
      {showMatrix && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AssessmentIcon />
            Impact vs Effort Matrix
          </Typography>

          <Box sx={{ height: 400, mb: 2 }}>
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart data={scatterData} margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                <CartesianGrid />
                <XAxis
                  type="number"
                  dataKey="x"
                  domain={[0, 11]}
                  name="Effort Score"
                  label={{ value: 'Effort Score →', position: 'bottom' }}
                />
                <YAxis
                  type="number"
                  dataKey="y"
                  domain={[0, 11]}
                  name="Impact Score"
                  label={{ value: 'Impact Score ↑', angle: -90, position: 'insideLeft' }}
                />
                <RechartsTooltip
                  content={({ payload }) => {
                    if (payload && payload[0] && payload[0].payload) {
                      const opp = payload[0].payload.opportunity;
                      return (
                        <Paper sx={{ p: 2, maxWidth: 300 }}>
                          <Typography variant="subtitle2" fontWeight="bold">
                            {opp.title}
                          </Typography>
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                            {opp.category} • {opp.priority}
                          </Typography>
                          <Typography variant="body2">
                            Impact: {opp.impactScore}/10 | Effort: {opp.effortScore}/10
                          </Typography>
                          <Typography variant="body2">
                            ROI: {opp.roiScore}% | Risk: {opp.riskLevel}
                          </Typography>
                          <Typography variant="body2" sx={{ mt: 1 }}>
                            Savings: {opp.estimatedSavings}
                          </Typography>
                        </Paper>
                      );
                    }
                    return null;
                  }}
                />
                <Scatter dataKey="y">
                  {scatterData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.color}
                      stroke={selectedForComparison.includes(entry.opportunity.id) ? '#000' : entry.color}
                      strokeWidth={selectedForComparison.includes(entry.opportunity.id) ? 3 : 1}
                      style={{ cursor: 'pointer' }}
                      onClick={() => handleOpportunityClick(entry.opportunity)}
                    />
                  ))}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          </Box>

          {/* Quadrant Legend */}
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Box sx={{ width: 16, height: 16, bgcolor: '#4CAF50', borderRadius: '50%' }} />
                <Typography variant="body2">Quick Wins (High Impact, Low Effort)</Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Box sx={{ width: 16, height: 16, bgcolor: '#2196F3', borderRadius: '50%' }} />
                <Typography variant="body2">Major Projects (High Impact, High Effort)</Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Box sx={{ width: 16, height: 16, bgcolor: '#FFC107', borderRadius: '50%' }} />
                <Typography variant="body2">Fill-ins (Low Impact, Low Effort)</Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Box sx={{ width: 16, height: 16, bgcolor: '#FF5722', borderRadius: '50%' }} />
                <Typography variant="body2">Questionable (Low Impact, High Effort)</Typography>
              </Box>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* Selected for Comparison */}
      {selectedForComparison.length > 0 && (
        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography variant="body2">
            Selected {selectedForComparison.length} opportunities for comparison.
            <Button size="small" sx={{ ml: 2 }}>
              Compare Selected
            </Button>
            <Button size="small" onClick={() => setSelectedForComparison([])}>
              Clear Selection
            </Button>
          </Typography>
        </Alert>
      )}

      {/* Opportunities Grid */}
      <Grid container spacing={3}>
        {filteredOpportunities.map((opportunity) => (
          <Grid item xs={12} md={6} lg={4} key={opportunity.id}>
            <Card
              sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                position: 'relative',
                '&:hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: 4,
                  transition: 'all 0.2s ease-in-out'
                },
                border: selectedForComparison.includes(opportunity.id) ? '2px solid' : '1px solid',
                borderColor: selectedForComparison.includes(opportunity.id) ? 'primary.main' : 'divider'
              }}
            >
              {/* Category Header */}
              <Box
                sx={{
                  bgcolor: categoryColors[opportunity.category] || '#757575',
                  color: 'white',
                  p: 1,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {categoryIcons[opportunity.category]}
                  <Typography variant="caption" fontWeight="bold">
                    {opportunity.category}
                  </Typography>
                </Box>
                <Chip
                  label={opportunity.priority}
                  size="small"
                  sx={{
                    bgcolor: getPriorityColor(opportunity.priority),
                    color: 'white',
                    fontWeight: 'bold',
                    fontSize: '0.7rem'
                  }}
                />
              </Box>

              <CardContent sx={{ flexGrow: 1, pb: 1 }}>
                <Typography variant="h6" component="h3" gutterBottom sx={{ fontWeight: 600 }}>
                  {opportunity.title}
                </Typography>

                <Typography variant="body2" color="text.secondary" sx={{ mb: 2, height: 60, overflow: 'hidden' }}>
                  {opportunity.description}
                </Typography>

                {/* Key Metrics */}
                <Grid container spacing={2} sx={{ mb: 2 }}>
                  <Grid item xs={6}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h6" color="success.main" fontWeight="bold">
                        {opportunity.roiScore}%
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Expected ROI
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h6" color="info.main" fontWeight="bold">
                        {opportunity.implementationTimeline}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Timeline
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>

                {/* Impact vs Effort */}
                <Grid container spacing={1} sx={{ mb: 2 }}>
                  <Grid item xs={6}>
                    <Typography variant="caption" gutterBottom display="block">
                      Impact Score
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={(opportunity.impactScore / 10) * 100}
                      sx={{
                        height: 8,
                        borderRadius: 4,
                        backgroundColor: 'grey.200',
                        '& .MuiLinearProgress-bar': {
                          backgroundColor: opportunity.impactScore >= 7 ? '#4CAF50' : opportunity.impactScore >= 5 ? '#FF9800' : '#F44336'
                        }
                      }}
                    />
                    <Typography variant="caption" color="text.secondary">
                      {opportunity.impactScore}/10
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" gutterBottom display="block">
                      Effort Score
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={(opportunity.effortScore / 10) * 100}
                      sx={{
                        height: 8,
                        borderRadius: 4,
                        backgroundColor: 'grey.200',
                        '& .MuiLinearProgress-bar': {
                          backgroundColor: opportunity.effortScore <= 4 ? '#4CAF50' : opportunity.effortScore <= 7 ? '#FF9800' : '#F44336'
                        }
                      }}
                    />
                    <Typography variant="caption" color="text.secondary">
                      {opportunity.effortScore}/10
                    </Typography>
                  </Grid>
                </Grid>

                {/* Risk and Savings */}
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Chip
                    label={`${opportunity.riskLevel} Risk`}
                    size="small"
                    sx={{
                      bgcolor: getRiskColor(opportunity.riskLevel),
                      color: 'white',
                      fontWeight: 'bold'
                    }}
                  />
                  <Typography variant="body2" color="success.main" fontWeight="bold">
                    {opportunity.estimatedSavings}
                  </Typography>
                </Box>

                {/* Related Factors */}
                <Typography variant="caption" color="text.secondary" gutterBottom display="block">
                  Related 12-Factor Principles:
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
                  {opportunity.relatedFactors.slice(0, 2).map((factor, index) => (
                    <Chip
                      key={index}
                      label={factor.replace('Factor ', '')}
                      size="small"
                      variant="outlined"
                      sx={{ fontSize: '0.7rem', height: 20 }}
                    />
                  ))}
                  {opportunity.relatedFactors.length > 2 && (
                    <Chip
                      label={`+${opportunity.relatedFactors.length - 2}`}
                      size="small"
                      variant="outlined"
                      sx={{ fontSize: '0.7rem', height: 20 }}
                    />
                  )}
                </Box>
              </CardContent>

              <CardActions sx={{ p: 2, pt: 0 }}>
                <Button
                  size="small"
                  onClick={() => handleOpportunityClick(opportunity)}
                  startIcon={<ViewIcon />}
                  variant="outlined"
                  sx={{ mr: 1 }}
                >
                  View Details
                </Button>
                <Tooltip title={selectedForComparison.length >= 3 && !selectedForComparison.includes(opportunity.id) ? "Maximum 3 opportunities can be selected" : "Add to comparison"}>
                  <span>
                    <IconButton
                      size="small"
                      onClick={() => toggleComparison(opportunity.id)}
                      disabled={selectedForComparison.length >= 3 && !selectedForComparison.includes(opportunity.id)}
                      color={selectedForComparison.includes(opportunity.id) ? "primary" : "default"}
                    >
                      <CheckIcon />
                    </IconButton>
                  </span>
                </Tooltip>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Opportunity Detail Dialog */}
      <Dialog
        open={detailDialogOpen}
        onClose={() => setDetailDialogOpen(false)}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: { minHeight: '80vh' }
        }}
      >
        {selectedOpportunity && (
          <>
            <DialogTitle sx={{ pb: 1 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <Box>
                  <Typography variant="h5" component="h2" gutterBottom sx={{ fontWeight: 600 }}>
                    {selectedOpportunity.title}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                    <Chip
                      label={selectedOpportunity.category}
                      sx={{
                        bgcolor: categoryColors[selectedOpportunity.category],
                        color: 'white',
                        fontWeight: 'bold'
                      }}
                    />
                    <Chip
                      label={selectedOpportunity.priority}
                      sx={{
                        bgcolor: getPriorityColor(selectedOpportunity.priority),
                        color: 'white',
                        fontWeight: 'bold'
                      }}
                    />
                    <Chip
                      label={`${selectedOpportunity.riskLevel} Risk`}
                      sx={{
                        bgcolor: getRiskColor(selectedOpportunity.riskLevel),
                        color: 'white',
                        fontWeight: 'bold'
                      }}
                    />
                  </Box>
                </Box>
                <IconButton onClick={() => setDetailDialogOpen(false)}>
                  <CloseIcon />
                </IconButton>
              </Box>
            </DialogTitle>

            <DialogContent>
              {/* Key Metrics */}
              <Grid container spacing={3} sx={{ mb: 3 }}>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'success.light' }}>
                    <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'success.main' }}>
                      {selectedOpportunity.roiScore}%
                    </Typography>
                    <Typography variant="body2">Expected ROI</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'info.light' }}>
                    <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'info.main' }}>
                      {selectedOpportunity.impactScore}/10
                    </Typography>
                    <Typography variant="body2">Impact Score</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'warning.light' }}>
                    <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'warning.main' }}>
                      {selectedOpportunity.effortScore}/10
                    </Typography>
                    <Typography variant="body2">Effort Score</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'secondary.light' }}>
                    <Typography variant="h6" sx={{ fontWeight: 'bold', color: 'secondary.main' }}>
                      {selectedOpportunity.implementationTimeline}
                    </Typography>
                    <Typography variant="body2">Timeline</Typography>
                  </Paper>
                </Grid>
              </Grid>

              {/* Description and Business Value */}
              <Typography variant="h6" gutterBottom sx={{ mt: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
                <InfoIcon />
                Description & Business Value
              </Typography>
              <Typography variant="body1" paragraph>
                {selectedOpportunity.description}
              </Typography>
              <Typography variant="body1" paragraph sx={{ bgcolor: 'success.light', p: 2, borderRadius: 1 }}>
                <strong>Business Value:</strong> {selectedOpportunity.businessValue}
              </Typography>

              {/* Financial Impact */}
              <Typography variant="h6" gutterBottom sx={{ mt: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
                <MoneyIcon />
                Financial Impact
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Estimated Cost
                  </Typography>
                  <Typography variant="h6" color="error.main">
                    {selectedOpportunity.estimatedCost}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Estimated Annual Savings
                  </Typography>
                  <Typography variant="h6" color="success.main">
                    {selectedOpportunity.estimatedSavings}
                  </Typography>
                </Grid>
              </Grid>

              {/* Business Metrics */}
              {selectedOpportunity.businessMetrics.length > 0 && (
                <>
                  <Typography variant="h6" gutterBottom sx={{ mt: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
                    <TrendingUpIcon />
                    Expected Business Metrics Improvements
                  </Typography>
                  <Grid container spacing={2}>
                    {selectedOpportunity.businessMetrics.map((metric, index) => (
                      <Grid item xs={12} sm={6} key={index}>
                        <Paper sx={{ p: 2, bgcolor: 'background.default' }}>
                          <Typography variant="subtitle2" fontWeight="bold">
                            {metric.name}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Current: {metric.current} → Target: {metric.target}
                          </Typography>
                          <Typography variant="body2" color="success.main" fontWeight="bold">
                            {metric.improvement} ({metric.timeframe})
                          </Typography>
                        </Paper>
                      </Grid>
                    ))}
                  </Grid>
                </>
              )}

              {/* Stakeholders */}
              <Typography variant="h6" gutterBottom sx={{ mt: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
                <GroupIcon />
                Key Stakeholders
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {selectedOpportunity.stakeholders.map((stakeholder, index) => (
                  <Chip key={index} label={stakeholder} variant="outlined" />
                ))}
              </Box>

              {/* Success Criteria */}
              <Typography variant="h6" gutterBottom sx={{ mt: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
                <CheckIcon />
                Success Criteria
              </Typography>
              <List dense>
                {selectedOpportunity.successCriteria.map((criterion, index) => (
                  <ListItem key={index} sx={{ pl: 0 }}>
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      <CheckIcon color="success" fontSize="small" />
                    </ListItemIcon>
                    <ListItemText primary={criterion} />
                  </ListItem>
                ))}
              </List>

              {/* Potential Challenges */}
              <Typography variant="h6" gutterBottom sx={{ mt: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
                <WarningIcon />
                Potential Challenges
              </Typography>
              <List dense>
                {selectedOpportunity.potentialChallenges.map((challenge, index) => (
                  <ListItem key={index} sx={{ pl: 0 }}>
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      <WarningIcon color="warning" fontSize="small" />
                    </ListItemIcon>
                    <ListItemText primary={challenge} />
                  </ListItem>
                ))}
              </List>

              {/* Related 12-Factor Principles */}
              <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
                Related 12-Factor Principles
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {selectedOpportunity.relatedFactors.map((factor, index) => (
                  <Chip
                    key={index}
                    label={factor}
                    color="primary"
                    variant="outlined"
                  />
                ))}
              </Box>
            </DialogContent>

            <DialogActions sx={{ p: 3, pt: 0 }}>
              <Button
                onClick={() => toggleComparison(selectedOpportunity.id)}
                variant="outlined"
                disabled={selectedForComparison.length >= 3 && !selectedForComparison.includes(selectedOpportunity.id)}
              >
                {selectedForComparison.includes(selectedOpportunity.id) ? 'Remove from Comparison' : 'Add to Comparison'}
              </Button>
              <Button
                variant="contained"
                startIcon={<ExportIcon />}
              >
                Export Details
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>

      {/* Floating Action Button for Export */}
      <Fab
        color="primary"
        aria-label="export"
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
        onClick={() => {}}
      >
        <ExportIcon />
      </Fab>
    </Box>
  );
};

export default TransformationOpportunities;