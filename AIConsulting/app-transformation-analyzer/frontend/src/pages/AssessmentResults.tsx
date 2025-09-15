/**
 * Assessment Results Page
 * Interactive 12-factor assessment results with comprehensive visualizations
 */

import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Alert,
  Tabs,
  Tab,
  LinearProgress,
  Chip,
  IconButton,
  Menu,
  MenuItem,
  Divider,
  Paper
} from '@mui/material';
import {
  Assessment as AssessmentIcon,
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  MoreVert as MoreVertIcon,
  Visibility as ViewIcon,
  Share as ShareIcon
} from '@mui/icons-material';

// Import our new visualization components
import FactorRadarChart from '../components/FactorRadarChart';
import GapHeatmap from '../components/GapHeatmap';
import FactorCards from '../components/FactorCards';
import FactorCardsDebug from '../components/FactorCardsDebug';
import FactorCardsSimple from '../components/FactorCardsSimple';
import Recommendations from '../components/Recommendations';

// Import services and utilities
import { exportAssessmentToPDF } from '../utils/pdfExport';

// Import types
import {
  AssessmentJob,
  AssessmentResults,
  LoadingState,
  PaginationParams,
  Grade,
  TwelveFactorAssessment
} from '../types';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <div role="tabpanel" hidden={value !== index}>
    {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
  </div>
);

const AssessmentResultsPage: React.FC = () => {
  const { jobId } = useParams<{ jobId: string }>();
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState<LoadingState>({ loading: false });
  const [assessment, setAssessment] = useState<TwelveFactorAssessment | null>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [exportLoading, setExportLoading] = useState(false);

  // Load real assessment data from API based on jobId
  useEffect(() => {
    const loadAssessment = async () => {
      setLoading({ loading: true });

      try {
        // If no jobId, redirect to repository analysis instead of showing mock data
        if (!jobId) {
          setLoading({ loading: false, error: 'No assessment ID provided. Please start a repository analysis first.' });
          return;
        }

        // Load real assessment results for the specific jobId
        const response = await fetch(`http://localhost:5001/api/assessment/${jobId}/results`);
        const data = await response.json();

        if (data.success) {
          setAssessment(data.data.assessment);
          setLoading({ loading: false });
        } else {
          setLoading({ loading: false, error: data.error?.message || 'Failed to load assessment data' });
        }
      } catch (error: any) {
        setLoading({ loading: false, error: 'Failed to connect to backend API' });
      }
    };

    loadAssessment();
  }, [jobId]);

  const handleExportPDF = async () => {
    if (!assessment) return;

    setExportLoading(true);
    try {
      // Create a simple summary for PDF export
      const summary = {
        overview: {
          grade: assessment.grade,
          overall_score: assessment.overall_score,
          weighted_score: assessment.weighted_score,
          confidence: assessment.confidence,
          coverage: assessment.coverage
        },
        insights: ['Assessment completed successfully with interactive visualizations'],
        next_steps: ['Review factor details', 'Implement recommendations', 'Schedule follow-up assessment']
      };

      await exportAssessmentToPDF(assessment, summary as any, {
        includeCharts: true,
        includeRecommendations: true,
        includeExecutiveSummary: true,
        theme: 'professional'
      });
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setExportLoading(false);
      setAnchorEl(null);
    }
  };

  const handleFactorClick = (factorName: string) => {
    console.log('Factor clicked:', factorName);
  };

  const handleRecommendationClick = (recommendation: any) => {
    console.log('Recommendation clicked:', recommendation);
  };

  const getGradeColor = (grade: string): 'success' | 'warning' | 'error' => {
    if (grade === 'A' || grade === 'B') return 'success';
    if (grade === 'C' || grade === 'D') return 'warning';
    return 'error';
  };

  // Convert assessment data for radar chart
  const getRadarChartData = () => {
    if (!assessment) return [];

    return Object.entries(assessment.factor_evaluations).map(([name, evaluation]) => ({
      factor: name,
      score: evaluation.score,
      maxScore: 5,
      color: evaluation.score >= 4 ? '#4CAF50' : evaluation.score >= 3 ? '#FF9800' : '#F44336'
    }));
  };

  // Convert gaps data for heatmap
  const getHeatmapData = () => {
    if (!assessment) return [];

    return assessment.gaps.map(gap => ({
      factor: gap.factor_name,
      gapType: gap.gap_type,
      severity: gap.severity as 'low' | 'medium' | 'high' | 'critical',
      impact: gap.impact as 'low' | 'medium' | 'high',
      description: gap.description,
      effort: 40 // Mock effort hours
    }));
  };

  if (loading.loading) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Assessment Results
        </Typography>
        <LinearProgress sx={{ mb: 2 }} />
        <Typography>Loading assessment data...</Typography>
      </Box>
    );
  }

  if (loading.error) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Assessment Results
        </Typography>
        <Alert severity="warning" sx={{ mb: 2 }}>
          {loading.error}
        </Alert>
        <Card>
          <CardContent>
            <Box textAlign="center" py={4}>
              <AssessmentIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                Start Repository Analysis
              </Typography>
              <Typography color="text.secondary" mb={3}>
                To view assessment results, you need to analyze a repository first.
              </Typography>
              <Button
                variant="contained"
                onClick={() => window.location.href = '/repository-analysis'}
                sx={{ mr: 2 }}
              >
                Analyze Repository
              </Button>
              <Button
                variant="outlined"
                onClick={() => window.location.href = '/'}
              >
                Go to Dashboard
              </Button>
            </Box>
          </CardContent>
        </Card>
      </Box>
    );
  }

  if (!assessment) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Assessment Results
        </Typography>
        <Card>
          <CardContent>
            <Box textAlign="center" py={6}>
              <AssessmentIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No assessment data available
              </Typography>
              <Typography color="text.secondary" mb={3}>
                Please run a 12-factor assessment first.
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </Box>
    );
  }




  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" gutterBottom>
            12-Factor Assessment Results
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Interactive analysis of {assessment.repository_url}
          </Typography>
        </Box>
        <Box display="flex" alignItems="center" gap={1}>
          <IconButton
            onClick={(e) => setAnchorEl(e.currentTarget)}
            disabled={exportLoading}
          >
            <MoreVertIcon />
          </IconButton>
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={() => setAnchorEl(null)}
          >
            <MenuItem onClick={handleExportPDF} disabled={exportLoading}>
              <DownloadIcon sx={{ mr: 1 }} />
              Export PDF Report
            </MenuItem>
            <MenuItem onClick={() => setAnchorEl(null)}>
              <ShareIcon sx={{ mr: 1 }} />
              Share Results
            </MenuItem>
          </Menu>
        </Box>
      </Box>

      {/* Overview Cards */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3" color="primary" gutterBottom>
                {assessment.grade}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Overall Grade
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3" color="primary" gutterBottom>
                {Math.round(assessment.overall_score * 20)}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Compliance Score
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3" color="success.main" gutterBottom>
                {assessment.summary.excellent_factors}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Excellent Factors
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3" color="error.main" gutterBottom>
                {assessment.summary.critical_issues}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Critical Issues
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Main Content Tabs */}
      <Paper sx={{ width: '100%' }}>
        <Tabs
          value={tabValue}
          onChange={(_, newValue) => setTabValue(newValue)}
          variant="fullWidth"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="Overview" />
          <Tab label="Factor Analysis" />
          <Tab label="Recommendations" />
          <Tab label="Visualizations" />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          {/* Overview Tab */}
          <Grid container spacing={3}>
            <Grid item xs={12} lg={8}>
              <FactorRadarChart
                data={getRadarChartData()}
                onFactorClick={handleFactorClick}
                title="12-Factor Compliance Radar"
              />
            </Grid>
            <Grid item xs={12} lg={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Assessment Summary
                  </Typography>
                  <Box mb={2}>
                    <Typography variant="body2" color="text.secondary">
                      Repository: {assessment.repository_url}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Date: {new Date(assessment.timestamp).toLocaleDateString()}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Confidence: {Math.round(assessment.confidence * 100)}%
                    </Typography>
                  </Box>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="body2" gutterBottom>
                    <strong>Quick Stats:</strong>
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    • {assessment.summary.total_factors} factors evaluated
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    • {assessment.summary.total_recommendations} recommendations
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    • {assessment.summary.total_gaps} gaps identified
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          {/* Factor Analysis Tab */}
          <FactorCards
            factors={assessment.factor_evaluations}
            onFactorClick={handleFactorClick}
            showEvidence={true}
            groupBy="score"
          />
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          {/* Recommendations Tab */}
          <Recommendations
            recommendations={assessment.recommendations}
            onRecommendationClick={handleRecommendationClick}
            groupBy="priority"
          />
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          {/* Visualizations Tab */}
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <GapHeatmap
                data={getHeatmapData()}
                title="Gap Analysis Heatmap"
                colorScheme="severity"
                onCellClick={(gap) => console.log('Gap clicked:', gap)}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FactorRadarChart
                data={getRadarChartData()}
                onFactorClick={handleFactorClick}
                title="Factor Compliance Radar"
                width={500}
                height={400}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Score Distribution
                  </Typography>
                  {Object.entries(assessment.score_distribution || {}).map(([scoreName, count]) => {
                    const total = assessment.summary.total_factors;
                    const percentage = (count / total * 100).toFixed(1);
                    return (
                      <Box key={scoreName} mb={1}>
                        <Box display="flex" justifyContent="space-between" mb={0.5}>
                          <Typography variant="body2">{scoreName}</Typography>
                          <Typography variant="body2">{count} ({percentage}%)</Typography>
                        </Box>
                        <LinearProgress
                          variant="determinate"
                          value={count / total * 100}
                          sx={{ height: 6, borderRadius: 3 }}
                        />
                      </Box>
                    );
                  })}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
      </Paper>
    </Box>
  );
};

export default AssessmentResultsPage;