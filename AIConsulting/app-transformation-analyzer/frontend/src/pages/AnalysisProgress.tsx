/**
 * Analysis Progress Page - Real-time progress tracking for repository analysis
 * Shows live updates and status of ongoing analysis jobs
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  Container,
  Typography,
  Card,
  CardContent,
  Box,
  LinearProgress,
  CircularProgress,
  Alert,
  Button,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
} from '@mui/material';
import {
  CheckCircle as CheckIcon,
  Schedule as ScheduleIcon,
  Error as ErrorIcon,
  Analytics as AnalyticsIcon,
  Visibility as ViewIcon,
  Refresh as RefreshIcon,
  GitHub as GitHubIcon,
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';

import { apiClient } from '../services/api';
import { AnalysisJob } from '../types';

interface AnalysisStep {
  label: string;
  description: string;
  completed: boolean;
  error?: string;
}

const AnalysisProgress: React.FC = () => {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();

  const [job, setJob] = useState<AnalysisJob | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [steps, setSteps] = useState<AnalysisStep[]>([]);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const analysisSteps = [
    { label: 'Repository Cloning', description: 'Downloading repository content', minProgress: 0 },
    { label: 'File Structure Analysis', description: 'Analyzing project structure', minProgress: 20 },
    { label: 'Code Analysis', description: 'Processing source code', minProgress: 40 },
    { label: 'Dependency Analysis', description: 'Analyzing dependencies and security', minProgress: 60 },
    { label: 'Architecture Detection', description: 'Identifying patterns and frameworks', minProgress: 80 },
    { label: 'Report Generation', description: 'Generating final analysis report', minProgress: 95 }
  ];

  useEffect(() => {
    if (jobId) {
      checkJobStatus();
      startPolling();
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [jobId]);

  const startPolling = () => {
    intervalRef.current = setInterval(() => {
      if (jobId) {
        checkJobStatus();
      }
    }, 2000); // Poll every 2 seconds
  };

  const stopPolling = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  const checkJobStatus = async () => {
    if (!jobId) return;

    try {
      setLoading(false);
      const statusData = await apiClient.getAnalysisStatus(jobId);
      setJob(statusData);

      // Update steps based on progress
      const updatedSteps = analysisSteps.map((step, index) => ({
        ...step,
        completed: statusData.progress >= step.minProgress,
        error: statusData.status === 'failed' && statusData.progress >= step.minProgress ? statusData.error : undefined
      }));
      setSteps(updatedSteps);

      // Stop polling if job is complete or failed
      if (statusData.status === 'completed' || statusData.status === 'failed' || statusData.status === 'cancelled') {
        stopPolling();

        // Auto-redirect to results if completed
        if (statusData.status === 'completed') {
          setTimeout(() => {
            navigate(`/analysis/results/${jobId}`);
          }, 2000);
        }
      }

      setError(null);
    } catch (err: any) {
      console.error('Error checking job status:', err);
      setError(err.message || 'Failed to check analysis status');

      // Don't stop polling on error in case it's temporary
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckIcon color="success" />;
      case 'failed':
        return <ErrorIcon color="error" />;
      case 'cancelled':
        return <ErrorIcon color="warning" />;
      default:
        return <ScheduleIcon color="primary" />;
    }
  };

  const getStatusColor = (status: string): 'success' | 'error' | 'warning' | 'primary' => {
    switch (status) {
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'cancelled': return 'warning';
      default: return 'primary';
    }
  };

  if (loading && !job) {
    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Box display="flex" flexDirection="column" alignItems="center" gap={2}>
          <CircularProgress size={48} />
          <Typography variant="h6">Loading analysis status...</Typography>
        </Box>
      </Container>
    );
  }

  if (error && !job) {
    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Alert
          severity="error"
          action={
            <Button color="inherit" size="small" onClick={checkJobStatus}>
              Retry
            </Button>
          }
        >
          {error}
        </Alert>
      </Container>
    );
  }

  if (!job) {
    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Alert severity="warning">
          Analysis job not found.
        </Alert>
      </Container>
    );
  }

  const currentStep = steps.findIndex(step => !step.completed);
  const activeStep = currentStep >= 0 ? currentStep : steps.length;

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      {/* Header */}
      <Box mb={4}>
        <Box display="flex" alignItems="center" gap={2} mb={2}>
          <AnalyticsIcon color="primary" />
          <Typography variant="h4" component="h1">
            Analysis Progress
          </Typography>
        </Box>
        <Typography variant="body1" color="text.secondary">
          Real-time tracking of repository analysis
        </Typography>
      </Box>

      {/* Job Info Card */}
      <Card elevation={2} sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" alignItems="center" gap={2} mb={2}>
            <GitHubIcon />
            <Typography variant="h6">
              Repository Analysis
            </Typography>
            <Chip
              icon={getStatusIcon(job.status)}
              label={job.status.toUpperCase()}
              color={getStatusColor(job.status)}
              variant="outlined"
            />
          </Box>

          <Box mb={2}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Repository: {job.repositoryUrl}
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Job ID: {job.id}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Started: {job.startedAt ? new Date(job.startedAt).toLocaleString() : 'Not started'}
            </Typography>
          </Box>

          {/* Progress Bar */}
          <Box mb={2}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
              <Typography variant="body2" fontWeight="medium">
                Progress: {job.progress}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {job.message}
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={job.progress}
              sx={{
                height: 8,
                borderRadius: 4,
                backgroundColor: 'grey.200',
                '& .MuiLinearProgress-bar': {
                  borderRadius: 4,
                },
              }}
            />
          </Box>

          {/* Status Message */}
          {job.error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {job.error}
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Progress Steps */}
      <Card elevation={2} sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Analysis Steps
          </Typography>
          <Stepper activeStep={activeStep} orientation="vertical">
            {steps.map((step, index) => (
              <Step key={index}>
                <StepLabel
                  optional={
                    step.error ? (
                      <Typography variant="caption" color="error">
                        {step.error}
                      </Typography>
                    ) : null
                  }
                  error={!!step.error}
                >
                  {step.label}
                </StepLabel>
                <StepContent>
                  <Typography variant="body2" color="text.secondary">
                    {step.description}
                  </Typography>
                  {step.error && (
                    <Alert severity="error" sx={{ mt: 1 }}>
                      {step.error}
                    </Alert>
                  )}
                </StepContent>
              </Step>
            ))}
          </Stepper>
        </CardContent>
      </Card>

      {/* Job Details */}
      <Card elevation={2} sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Job Details
          </Typography>
          <List dense>
            <ListItem>
              <ListItemIcon>
                <AnalyticsIcon />
              </ListItemIcon>
              <ListItemText
                primary="Analysis Type"
                secondary={job.analysisType}
              />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <ScheduleIcon />
              </ListItemIcon>
              <ListItemText
                primary="Created"
                secondary={new Date(job.createdAt).toLocaleString()}
              />
            </ListItem>
            {job.estimatedCompletionTime && (
              <ListItem>
                <ListItemIcon>
                  <ScheduleIcon />
                </ListItemIcon>
                <ListItemText
                  primary="Estimated Completion"
                  secondary={new Date(job.estimatedCompletionTime).toLocaleString()}
                />
              </ListItem>
            )}
            {job.completedAt && (
              <ListItem>
                <ListItemIcon>
                  <CheckIcon />
                </ListItemIcon>
                <ListItemText
                  primary="Completed"
                  secondary={new Date(job.completedAt).toLocaleString()}
                />
              </ListItem>
            )}
          </List>
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <Box display="flex" gap={2} justifyContent="center">
        {job.status === 'completed' && (
          <Button
            variant="contained"
            size="large"
            startIcon={<ViewIcon />}
            onClick={() => navigate(`/analysis/results/${jobId}`)}
          >
            View Results
          </Button>
        )}

        <Button
          variant="outlined"
          size="large"
          startIcon={<RefreshIcon />}
          onClick={checkJobStatus}
          disabled={loading}
        >
          Refresh Status
        </Button>

        <Button
          variant="outlined"
          size="large"
          onClick={() => navigate('/analysis')}
        >
          New Analysis
        </Button>
      </Box>

      {/* Auto-redirect message */}
      {job.status === 'completed' && (
        <Alert severity="success" sx={{ mt: 3 }}>
          <Typography variant="body2">
            Analysis completed successfully! Redirecting to results in 2 seconds...
          </Typography>
        </Alert>
      )}
    </Container>
  );
};

export default AnalysisProgress;