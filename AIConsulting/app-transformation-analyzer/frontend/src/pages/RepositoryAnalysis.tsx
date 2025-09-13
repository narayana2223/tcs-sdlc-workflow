/**
 * Repository Analysis Page
 * Interface for starting repository analyses and viewing results
 */

import React, { useState, useEffect } from 'react';
import {
  Container,
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  LinearProgress,
  CircularProgress,
  Tabs,
  Tab,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  PlayArrow as StartIcon,
  Visibility as ViewIcon,
  Assessment as AssessIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  Download as DownloadIcon,
  Code as CodeIcon,
  Security as SecurityIcon,
  Architecture as ArchitectureIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

// Import components
import RepositoryInput from '../components/RepositoryInput';
import AnalysisStatus from '../components/AnalysisStatus';

// Import services and types
import { apiClient } from '../services/api';
import {
  AnalysisRequest,
  AnalysisJob,
  AnalysisResults,
  LoadingState,
  PaginationParams,
} from '../types';

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

const RepositoryAnalysis: React.FC = () => {
  const navigate = useNavigate();
  const [tabValue, setTabValue] = useState(0);
  const [analyses, setAnalyses] = useState<AnalysisJob[]>([]);
  const [loading, setLoading] = useState<LoadingState>({ loading: false });
  const [selectedAnalysis, setSelectedAnalysis] = useState<AnalysisJob | null>(null);
  const [analysisResults, setAnalysisResults] = useState<AnalysisResults | null>(null);
  const [showResults, setShowResults] = useState(false);
  const [pagination, setPagination] = useState<PaginationParams>({
    limit: 10,
    offset: 0,
    sortBy: 'createdAt',
    sortOrder: 'desc',
  });

  const loadAnalyses = async () => {
    try {
      setLoading({ loading: true });
      const response = await apiClient.getUserAnalyses({
        ...pagination,
        status: undefined,
      });
      setAnalyses(response.jobs);
      setLoading({ loading: false });
    } catch (error: any) {
      setLoading({ loading: false, error: error.message });
    }
  };

  useEffect(() => {
    if (tabValue === 1) {
      loadAnalyses();
    }
  }, [tabValue, pagination]);

  const handleStartAnalysis = async (request: AnalysisRequest) => {
    try {
      setLoading({ loading: true });
      const response = await apiClient.startAnalysis(request);

      // Navigate to a progress page to track the analysis
      navigate(`/analysis/progress/${response.jobId}`);

      setLoading({ loading: false });
    } catch (error: any) {
      setLoading({ loading: false, error: error.message });
    }
  };

  const handleViewResults = async (job: AnalysisJob) => {
    if (job.status === 'completed') {
      navigate(`/analysis/results/${job.id}`);
    }
  };

  const handleViewProgress = (job: AnalysisJob) => {
    navigate(`/analysis/progress/${job.id}`);
  };

  const handleOldViewResults = async (job: AnalysisJob) => {
    try {
      setLoading({ loading: true });
      const results = await apiClient.getAnalysisResults(job.id, {
        includeMetadata: true,
      });
      setAnalysisResults(results);
      setSelectedAnalysis(job);
      setShowResults(true);
      setLoading({ loading: false });
    } catch (error: any) {
      setLoading({ loading: false, error: error.message });
    }
  };

  const handleStartAssessment = async (job: AnalysisJob) => {
    try {
      setLoading({ loading: true });
      await apiClient.startAssessment({ analysisJobId: job.id });
      navigate('/assessment');
    } catch (error: any) {
      setLoading({ loading: false, error: error.message });
    }
  };

  const handleCancelAnalysis = async (jobId: string) => {
    try {
      await apiClient.cancelAnalysis(jobId);
      await loadAnalyses();
    } catch (error: any) {
      console.error('Failed to cancel analysis:', error);
    }
  };

  const handleRestartAnalysis = async (jobId: string) => {
    try {
      await apiClient.restartAnalysis(jobId);
      await loadAnalyses();
    } catch (error: any) {
      console.error('Failed to restart analysis:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'processing':
        return 'primary';
      case 'pending':
        return 'warning';
      default:
        return 'default';
    }
  };

  const ResultsDialog: React.FC = () => {
    if (!analysisResults || !selectedAnalysis) return null;

    const results = analysisResults.results;

    return (
      <Dialog
        open={showResults}
        onClose={() => setShowResults(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h6">
              Analysis Results - {selectedAnalysis.repositoryUrl.split('/').pop()}
            </Typography>
            <IconButton onClick={() => setShowResults(false)}>
              ×
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Box mb={3}>
            <Grid container spacing={2}>
              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Project Metrics
                    </Typography>
                    <Typography>
                      <strong>Files:</strong> {results.code_analysis.project_metrics.total_files}
                    </Typography>
                    <Typography>
                      <strong>Lines of Code:</strong> {results.code_analysis.project_metrics.total_lines_of_code.toLocaleString()}
                    </Typography>
                    <Typography>
                      <strong>Primary Language:</strong> {results.technology_stack.primary_language}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Languages
                    </Typography>
                    {Object.entries(results.code_analysis.project_metrics.languages)
                      .slice(0, 5)
                      .map(([lang, count]) => (
                        <Box key={lang} display="flex" justifyContent="space-between">
                          <Typography>{lang}</Typography>
                          <Typography>{count}</Typography>
                        </Box>
                      ))}
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Technology Stack
                    </Typography>
                    <Box mb={1}>
                      <Typography variant="body2" color="textSecondary">
                        Frameworks:
                      </Typography>
                      {results.technology_stack.frameworks.map((fw) => (
                        <Chip key={fw} label={fw} size="small" sx={{ mr: 0.5, mb: 0.5 }} />
                      ))}
                    </Box>
                    <Box>
                      <Typography variant="body2" color="textSecondary">
                        Build Tools:
                      </Typography>
                      {results.technology_stack.build_tools.map((tool) => (
                        <Chip key={tool} label={tool} size="small" sx={{ mr: 0.5, mb: 0.5 }} />
                      ))}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>

          {/* Security Vulnerabilities */}
          {results.code_analysis.dependency_analysis.security_vulnerabilities.length > 0 && (
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box display="flex" alignItems="center" gap={1}>
                  <SecurityIcon color="error" />
                  <Typography variant="h6">
                    Security Vulnerabilities ({results.code_analysis.dependency_analysis.security_vulnerabilities.length})
                  </Typography>
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Package</TableCell>
                        <TableCell>Severity</TableCell>
                        <TableCell>Description</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {results.code_analysis.dependency_analysis.security_vulnerabilities.map((vuln, index) => (
                        <TableRow key={index}>
                          <TableCell>{vuln.package}</TableCell>
                          <TableCell>
                            <Chip
                              label={vuln.severity.toUpperCase()}
                              color={
                                vuln.severity === 'critical' ? 'error' :
                                vuln.severity === 'high' ? 'error' :
                                vuln.severity === 'medium' ? 'warning' : 'info'
                              }
                              size="small"
                            />
                          </TableCell>
                          <TableCell>{vuln.description}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </AccordionDetails>
            </Accordion>
          )}

          {/* Architecture */}
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Box display="flex" alignItems="center" gap={1}>
                <ArchitectureIcon color="primary" />
                <Typography variant="h6">
                  Architecture Analysis
                </Typography>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle1" gutterBottom>
                    Components ({results.code_analysis.architecture_analysis.components.length})
                  </Typography>
                  {results.code_analysis.architecture_analysis.components.slice(0, 10).map((comp, index) => (
                    <Box key={index} mb={1}>
                      <Typography variant="body2">
                        <strong>{comp.name}</strong> ({comp.type})
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Complexity: {comp.complexity}
                      </Typography>
                    </Box>
                  ))}
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle1" gutterBottom>
                    Patterns
                  </Typography>
                  {results.code_analysis.architecture_analysis.patterns.map((pattern) => (
                    <Chip key={pattern} label={pattern} sx={{ mr: 0.5, mb: 0.5 }} />
                  ))}
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowResults(false)}>Close</Button>
          <Button
            variant="contained"
            onClick={() => handleStartAssessment(selectedAnalysis)}
            startIcon={<AssessIcon />}
          >
            Start 12-Factor Assessment
          </Button>
        </DialogActions>
      </Dialog>
    );
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Repository Analysis
      </Typography>

      {loading.error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {loading.error}
        </Alert>
      )}

      {loading.loading && <LinearProgress sx={{ mb: 2 }} />}

      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
          <Tab label="New Analysis" icon={<StartIcon />} iconPosition="start" />
          <Tab label="My Analyses" icon={<ViewIcon />} iconPosition="start" />
        </Tabs>
      </Box>

      <TabPanel value={tabValue} index={0}>
        <Grid container spacing={3}>
          <Grid item xs={12} lg={8}>
            <RepositoryInput
              onSubmit={handleStartAnalysis}
              loading={loading.loading}
              error={loading.error}
            />
          </Grid>
          <Grid item xs={12} lg={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  What We Analyze
                </Typography>
                <Box display="flex" flexDirection="column" gap={2}>
                  <Box display="flex" alignItems="center" gap={1}>
                    <CodeIcon color="primary" />
                    <Typography variant="body2">
                      Code quality metrics and complexity
                    </Typography>
                  </Box>
                  <Box display="flex" alignItems="center" gap={1}>
                    <SecurityIcon color="primary" />
                    <Typography variant="body2">
                      Security vulnerabilities in dependencies
                    </Typography>
                  </Box>
                  <Box display="flex" alignItems="center" gap={1}>
                    <ArchitectureIcon color="primary" />
                    <Typography variant="body2">
                      Architecture patterns and structure
                    </Typography>
                  </Box>
                  <Alert severity="info" sx={{ mt: 2 }}>
                    After analysis completes, you can run a 12-factor assessment 
                    to evaluate your application's cloud-readiness.
                  </Alert>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">
            Analysis History ({analyses.length})
          </Typography>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={loadAnalyses}
            disabled={loading.loading}
          >
            Refresh
          </Button>
        </Box>

        {analyses.length === 0 ? (
          <Card>
            <CardContent>
              <Typography color="textSecondary" textAlign="center" py={4}>
                No analyses found. Start your first repository analysis!
              </Typography>
              <Box textAlign="center">
                <Button
                  variant="contained"
                  onClick={() => setTabValue(0)}
                  startIcon={<StartIcon />}
                >
                  Start New Analysis
                </Button>
              </Box>
            </CardContent>
          </Card>
        ) : (
          <Grid container spacing={2}>
            {analyses.map((job) => (
              <Grid item xs={12} key={job.id}>
                <AnalysisStatus
                  job={job}
                  onCancel={handleCancelAnalysis}
                  onRestart={handleRestartAnalysis}
                  showActions={true}
                />
                {job.status === 'completed' && (
                  <Box mt={1} display="flex" gap={1}>
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<ViewIcon />}
                      onClick={() => handleViewResults(job)}
                    >
                      View Results
                    </Button>
                    <Button
                      size="small"
                      variant="contained"
                      startIcon={<AssessIcon />}
                      onClick={() => handleStartAssessment(job)}
                      disabled={loading.loading}
                    >
                      Start Assessment
                    </Button>
                  </Box>
                )}
              </Grid>
            ))}
          </Grid>
        )}
      </TabPanel>

      <ResultsDialog />
    </Box>
  );
};

export default RepositoryAnalysis;