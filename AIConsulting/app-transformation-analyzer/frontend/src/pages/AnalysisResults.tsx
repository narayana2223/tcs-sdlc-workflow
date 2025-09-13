/**
 * Analysis Results Page - Display comprehensive repository analysis results
 * Shows technology stack, components, architecture patterns, and code quality metrics
 */

import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Card,
  CardContent,
  Grid,
  Box,
  Chip,
  LinearProgress,
  Alert,
  Button,
  Divider,
  Avatar,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  CircularProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  GitHub as GitHubIcon,
  Code as CodeIcon,
  Security as SecurityIcon,
  BugReport as BugIcon,
  Assessment as AssessmentIcon,
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Architecture as ArchitectureIcon,
  Timeline as TimelineIcon,
  Language as LanguageIcon,
  Storage as StorageIcon,
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';

import { apiClient } from '../services/api';
import { AnalysisResults } from '../types';

interface AnalysisResultsPageProps {}

const AnalysisResultsPage: React.FC<AnalysisResultsPageProps> = () => {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();

  const [results, setResults] = useState<AnalysisResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (jobId) {
      loadResults();
    }
  }, [jobId]);

  const loadResults = async () => {
    if (!jobId) return;

    try {
      setLoading(true);
      setError(null);

      const data = await apiClient.getAnalysisResults(jobId, { includeMetadata: true });
      setResults(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load analysis results');
      console.error('Error loading results:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box display="flex" flexDirection="column" alignItems="center" gap={2}>
          <CircularProgress size={48} />
          <Typography variant="h6">Loading analysis results...</Typography>
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert
          severity="error"
          sx={{ mb: 2 }}
          action={
            <Button color="inherit" size="small" onClick={loadResults}>
              Retry
            </Button>
          }
        >
          {error}
        </Alert>
      </Container>
    );
  }

  if (!results) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="warning">
          No analysis results found for this job.
        </Alert>
      </Container>
    );
  }

  // Access mock data structure directly
  const mockResults = results as any;
  const repositoryInfo = mockResults.results?.repository;
  const analysis = mockResults.results?.analysis;
  const insights = mockResults.results?.insights;

  const getLanguageColor = (language: string): string => {
    const colors: { [key: string]: string } = {
      JavaScript: '#f7df1e',
      TypeScript: '#3178c6',
      Python: '#3776ab',
      Java: '#ed8b00',
      Go: '#00add8',
      Rust: '#000000',
      'C#': '#239120',
      CSS: '#1572b6',
      HTML: '#e34f26',
    };
    return colors[language] || '#757575';
  };

  const getSeverityColor = (severity: string): 'error' | 'warning' | 'info' | 'success' => {
    switch (severity) {
      case 'critical': return 'error';
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'info';
      default: return 'info';
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box mb={4}>
        <Box display="flex" alignItems="center" gap={2} mb={2}>
          <GitHubIcon color="primary" />
          <Typography variant="h4" component="h1">
            Analysis Results
          </Typography>
        </Box>
        <Typography variant="body1" color="text.secondary">
          Comprehensive analysis results for {repositoryInfo.fullName}
        </Typography>
      </Box>

      {/* Repository Info Card */}
      <Card elevation={2} sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <Typography variant="h6" gutterBottom>
                {repositoryInfo.name}
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                {repositoryInfo.description}
              </Typography>
              <Box display="flex" flexWrap="wrap" gap={1}>
                <Chip
                  icon={<LanguageIcon />}
                  label={repositoryInfo.language}
                  sx={{
                    backgroundColor: getLanguageColor(repositoryInfo.language),
                    color: 'white'
                  }}
                />
                <Chip icon={<CodeIcon />} label={`${analysis.totalFiles} files`} variant="outlined" />
                <Chip icon={<StorageIcon />} label={`${analysis.totalLinesOfCode.toLocaleString()} lines`} variant="outlined" />
              </Box>
            </Grid>
            <Grid item xs={12} md={4}>
              <Box display="flex" flexDirection="column" gap={1}>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2">Stars:</Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {repositoryInfo.stars.toLocaleString()}
                  </Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2">Forks:</Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {repositoryInfo.forks.toLocaleString()}
                  </Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2">Open Issues:</Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {repositoryInfo.openIssues.toLocaleString()}
                  </Typography>
                </Box>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Grid container spacing={3}>
        {/* Language Breakdown */}
        <Grid item xs={12} md={6}>
          <Card elevation={2}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <LanguageIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Language Breakdown
              </Typography>
              <Box mt={2}>
                {analysis?.languages && Object.entries(analysis.languages).map(([language, data]) => {
                  const languageData = data as any;
                  return (
                    <Box key={language} mb={2}>
                      <Box display="flex" justifyContent="space-between" mb={0.5}>
                        <Typography variant="body2">{language}</Typography>
                        <Typography variant="body2">{languageData.percentage || 0}%</Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={languageData.percentage || 0}
                        sx={{
                          height: 8,
                          borderRadius: 4,
                          backgroundColor: 'grey.200',
                          '& .MuiLinearProgress-bar': {
                            backgroundColor: getLanguageColor(language),
                          },
                        }}
                      />
                      <Typography variant="caption" color="text.secondary">
                        {languageData.files || 0} files, {(languageData.lines || 0).toLocaleString()} lines
                      </Typography>
                    </Box>
                  );
                })}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Code Quality Metrics */}
        <Grid item xs={12} md={6}>
          <Card elevation={2}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <AssessmentIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Code Quality
              </Typography>
              <Box mt={2}>
                <Box mb={2}>
                  <Box display="flex" justifyContent="space-between" mb={0.5}>
                    <Typography variant="body2">Maintainability Index</Typography>
                    <Typography variant="body2" fontWeight="bold">
                      {analysis.codeQuality.maintainabilityIndex}/100
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={analysis.codeQuality.maintainabilityIndex}
                    color={analysis.codeQuality.maintainabilityIndex > 70 ? 'success' : 'warning'}
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                </Box>

                <Box mb={2}>
                  <Box display="flex" justifyContent="space-between" mb={0.5}>
                    <Typography variant="body2">Test Coverage</Typography>
                    <Typography variant="body2" fontWeight="bold">
                      {analysis.codeQuality.testCoverage}%
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={analysis.codeQuality.testCoverage}
                    color={analysis.codeQuality.testCoverage > 70 ? 'success' : 'warning'}
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                </Box>

                <Box mb={2}>
                  <Box display="flex" justifyContent="space-between" mb={0.5}>
                    <Typography variant="body2">Code Duplication</Typography>
                    <Typography variant="body2" fontWeight="bold">
                      {analysis.codeQuality.duplication}%
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={analysis.codeQuality.duplication}
                    color={analysis.codeQuality.duplication < 10 ? 'success' : 'error'}
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                </Box>

                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Typography variant="body2">Technical Debt</Typography>
                  <Chip
                    label={`${analysis.codeQuality.technicalDebt} days`}
                    color={analysis.codeQuality.technicalDebt < 10 ? 'success' : 'warning'}
                    size="small"
                  />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Dependencies */}
        <Grid item xs={12} md={6}>
          <Card elevation={2}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <StorageIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Dependencies
              </Typography>
              <Grid container spacing={2} sx={{ mt: 1 }}>
                <Grid item xs={6}>
                  <Box textAlign="center">
                    <Typography variant="h4" color="primary">
                      {analysis.dependencies.total}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Total
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6}>
                  <Box textAlign="center">
                    <Typography variant="h4" color="success.main">
                      {analysis.dependencies.direct}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Direct
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6}>
                  <Box textAlign="center">
                    <Typography variant="h4" color="warning.main">
                      {analysis.dependencies.outdated}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Outdated
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6}>
                  <Box textAlign="center">
                    <Typography variant="h4" color="error.main">
                      {analysis.dependencies.vulnerable}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Vulnerable
                    </Typography>
                  </Box>
                </Grid>
              </Grid>

              {analysis.dependencies.list.filter(dep => dep.vulnerable).length > 0 && (
                <Box mt={2}>
                  <Typography variant="subtitle2" gutterBottom>
                    Security Vulnerabilities:
                  </Typography>
                  {analysis.dependencies.list
                    .filter(dep => dep.vulnerable)
                    .slice(0, 3)
                    .map((dep, index) => (
                      <Alert key={index} severity={getSeverityColor(dep.severity || 'low')} sx={{ mb: 1 }}>
                        <Typography variant="body2">
                          {dep.name} - {dep.severity} severity
                        </Typography>
                      </Alert>
                    ))}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Architecture Patterns */}
        <Grid item xs={12} md={6}>
          <Card elevation={2}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <ArchitectureIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Architecture & Patterns
              </Typography>
              <Box mt={2}>
                <Typography variant="subtitle2" gutterBottom>
                  Detected Patterns:
                </Typography>
                <Box display="flex" flexWrap="wrap" gap={1} mb={2}>
                  {analysis.architecture.patterns.map((pattern, index) => (
                    <Chip key={index} label={pattern} variant="outlined" />
                  ))}
                </Box>

                <Typography variant="subtitle2" gutterBottom>
                  Frameworks:
                </Typography>
                <Box display="flex" flexWrap="wrap" gap={1} mb={2}>
                  {analysis.architecture.frameworks.map((framework, index) => (
                    <Chip key={index} label={framework} color="primary" variant="outlined" />
                  ))}
                </Box>

                <Typography variant="subtitle2" gutterBottom>
                  Architecture Layers:
                </Typography>
                <List dense>
                  {analysis.architecture.layers.map((layer, index) => (
                    <ListItem key={index} sx={{ py: 0.5 }}>
                      <ListItemIcon sx={{ minWidth: 32 }}>
                        <CheckCircleIcon color="success" fontSize="small" />
                      </ListItemIcon>
                      <ListItemText
                        primary={layer}
                        primaryTypographyProps={{ variant: 'body2' }}
                      />
                    </ListItem>
                  ))}
                </List>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Components */}
        <Grid item xs={12}>
          <Card elevation={2}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <CodeIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Components Analysis
              </Typography>
              <TableContainer component={Paper} variant="outlined" sx={{ mt: 2 }}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Component</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell align="right">Files</TableCell>
                      <TableCell align="right">Complexity</TableCell>
                      <TableCell>Dependencies</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {analysis.components.map((component, index) => (
                      <TableRow key={index}>
                        <TableCell>
                          <Typography variant="body2" fontWeight="medium">
                            {component.name}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={component.type}
                            size="small"
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell align="right">{component.files}</TableCell>
                        <TableCell align="right">
                          <Chip
                            label={component.complexity}
                            size="small"
                            color={component.complexity > 50 ? 'warning' : 'success'}
                          />
                        </TableCell>
                        <TableCell>
                          <Box display="flex" flexWrap="wrap" gap={0.5}>
                            {component.dependencies.slice(0, 3).map((dep, depIndex) => (
                              <Chip
                                key={depIndex}
                                label={dep}
                                size="small"
                                variant="outlined"
                              />
                            ))}
                            {component.dependencies.length > 3 && (
                              <Chip
                                label={`+${component.dependencies.length - 3}`}
                                size="small"
                                variant="outlined"
                              />
                            )}
                          </Box>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Insights */}
        <Grid item xs={12}>
          <Card elevation={2}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <TrendingUpIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Analysis Insights
              </Typography>
              <Grid container spacing={3} sx={{ mt: 1 }}>
                <Grid item xs={12} md={4}>
                  <Typography variant="subtitle1" color="success.main" gutterBottom>
                    <CheckCircleIcon sx={{ mr: 1, verticalAlign: 'middle', fontSize: 20 }} />
                    Strengths
                  </Typography>
                  <List dense>
                    {insights.strengths.map((strength, index) => (
                      <ListItem key={index} sx={{ px: 0 }}>
                        <ListItemText
                          primary={strength}
                          primaryTypographyProps={{ variant: 'body2' }}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Typography variant="subtitle1" color="warning.main" gutterBottom>
                    <WarningIcon sx={{ mr: 1, verticalAlign: 'middle', fontSize: 20 }} />
                    Improvements
                  </Typography>
                  <List dense>
                    {insights.improvements.map((improvement, index) => (
                      <ListItem key={index} sx={{ px: 0 }}>
                        <ListItemText
                          primary={improvement}
                          primaryTypographyProps={{ variant: 'body2' }}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Typography variant="subtitle1" color="primary" gutterBottom>
                    <TrendingUpIcon sx={{ mr: 1, verticalAlign: 'middle', fontSize: 20 }} />
                    Recommendations
                  </Typography>
                  <List dense>
                    {insights.recommendations.map((recommendation, index) => (
                      <ListItem key={index} sx={{ px: 0 }}>
                        <ListItemText
                          primary={recommendation}
                          primaryTypographyProps={{ variant: 'body2' }}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Action Buttons */}
      <Box mt={4} display="flex" gap={2} justifyContent="center">
        <Button
          variant="contained"
          size="large"
          startIcon={<AssessmentIcon />}
          onClick={() => navigate(`/assessment/${jobId}`)}
        >
          Start 12-Factor Assessment
        </Button>
        <Button
          variant="outlined"
          size="large"
          onClick={() => navigate('/analysis')}
        >
          New Analysis
        </Button>
      </Box>
    </Container>
  );
};

export default AnalysisResultsPage;