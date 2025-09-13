/**
 * Analysis Status Component
 * Displays progress, status, and controls for analysis jobs
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  LinearProgress,
  Typography,
  Chip,
  Button,
  IconButton,
  Tooltip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Alert,
  Collapse,
} from '@mui/material';
import {
  PlayArrow as StartIcon,
  Pause as PauseIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  AccessTime as PendingIcon,
  Settings as ProcessingIcon,
} from '@mui/icons-material';
import { AnalysisStatusProps, JobStatus } from '../types';

const AnalysisStatus: React.FC<AnalysisStatusProps> = ({
  job,
  onCancel,
  onRestart,
  showActions = true,
}) => {
  const [showCancelDialog, setShowCancelDialog] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const [elapsedTime, setElapsedTime] = useState(0);

  // Calculate elapsed time for running jobs
  useEffect(() => {
    if (job.status === 'processing' && job.startedAt) {
      const startTime = new Date(job.startedAt).getTime();
      const timer = setInterval(() => {
        setElapsedTime(Math.floor((Date.now() - startTime) / 1000));
      }, 1000);

      return () => clearInterval(timer);
    }
  }, [job.status, job.startedAt]);

  const getStatusColor = (status: JobStatus) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'cancelled':
        return 'default';
      case 'processing':
        return 'primary';
      case 'pending':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: JobStatus) => {
    switch (status) {
      case 'completed':
        return <SuccessIcon />;
      case 'failed':
        return <ErrorIcon />;
      case 'processing':
        return <ProcessingIcon />;
      case 'pending':
        return <PendingIcon />;
      default:
        return <PendingIcon />;
    }
  };

  const getProgressText = () => {
    if (job.status === 'pending') {
      return 'Queued for processing...';
    }
    if (job.status === 'processing') {
      if (job.progress < 20) return 'Initializing analysis...';
      if (job.progress < 40) return 'Cloning repository...';
      if (job.progress < 60) return 'Analyzing code structure...';
      if (job.progress < 80) return 'Processing dependencies...';
      if (job.progress < 95) return 'Generating recommendations...';
      return 'Finalizing results...';
    }
    if (job.status === 'completed') {
      return 'Analysis completed successfully';
    }
    if (job.status === 'failed') {
      return 'Analysis failed';
    }
    if (job.status === 'cancelled') {
      return 'Analysis was cancelled';
    }
    return 'Unknown status';
  };

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    if (mins === 0) {
      return `${secs}s`;
    }
    return `${mins}m ${secs}s`;
  };

  const formatDateTime = (dateString: string): string => {
    return new Date(dateString).toLocaleString();
  };

  const handleCancel = () => {
    setShowCancelDialog(false);
    if (onCancel) {
      onCancel(job.id);
    }
  };

  const handleRestart = () => {
    if (onRestart) {
      onRestart(job.id);
    }
  };

  const canCancel = job.status === 'pending' || job.status === 'processing';
  const canRestart = job.status === 'failed';

  return (
    <Card elevation={1}>
      <CardContent>
        <Box display="flex" flexDirection="column" gap={2}>
          {/* Header */}
          <Box display="flex" justifyContent="space-between" alignItems="flex-start">
            <Box flex={1}>
              <Typography variant="h6" gutterBottom>
                Repository Analysis
              </Typography>
              <Typography variant="body2" color="text.secondary" noWrap>
                {job.repositoryUrl}
              </Typography>
            </Box>
            
            <Box display="flex" alignItems="center" gap={1}>
              <Chip
                icon={getStatusIcon(job.status)}
                label={job.status.toUpperCase()}
                color={getStatusColor(job.status)}
                size="small"
              />
              
              {showActions && (
                <>
                  {canCancel && (
                    <Tooltip title="Cancel analysis">
                      <IconButton
                        color="error"
                        onClick={() => setShowCancelDialog(true)}
                        size="small"
                      >
                        <StopIcon />
                      </IconButton>
                    </Tooltip>
                  )}
                  
                  {canRestart && (
                    <Tooltip title="Restart analysis">
                      <IconButton
                        color="primary"
                        onClick={handleRestart}
                        size="small"
                      >
                        <RefreshIcon />
                      </IconButton>
                    </Tooltip>
                  )}
                </>
              )}
            </Box>
          </Box>

          {/* Progress */}
          {job.status === 'processing' && (
            <Box>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                <Typography variant="body2" color="text.secondary">
                  {getProgressText()}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {job.progress}%
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={job.progress}
                sx={{ height: 8, borderRadius: 4 }}
              />
            </Box>
          )}

          {/* Status Message */}
          {job.status !== 'processing' && (
            <Alert 
              severity={
                job.status === 'completed' ? 'success' :
                job.status === 'failed' ? 'error' :
                job.status === 'cancelled' ? 'warning' : 'info'
              }
              variant="outlined"
            >
              {getProgressText()}
            </Alert>
          )}

          {/* Error Details */}
          {job.status === 'failed' && job.error && (
            <Alert severity="error" variant="outlined">
              <Typography variant="body2">
                <strong>Error:</strong> {job.error}
              </Typography>
            </Alert>
          )}

          {/* Timing Information */}
          <Box display="flex" flex-wrap="wrap" gap={2}>
            <Typography variant="body2" color="text.secondary">
              <strong>Created:</strong> {formatDateTime(job.createdAt)}
            </Typography>
            
            {job.startedAt && (
              <Typography variant="body2" color="text.secondary">
                <strong>Started:</strong> {formatDateTime(job.startedAt)}
              </Typography>
            )}
            
            {job.completedAt && (
              <Typography variant="body2" color="text.secondary">
                <strong>Completed:</strong> {formatDateTime(job.completedAt)}
              </Typography>
            )}
            
            {job.status === 'processing' && elapsedTime > 0 && (
              <Typography variant="body2" color="text.secondary">
                <strong>Elapsed:</strong> {formatDuration(elapsedTime)}
              </Typography>
            )}
            
            {job.estimatedCompletionTime && job.status === 'processing' && (
              <Typography variant="body2" color="text.secondary">
                <strong>ETA:</strong> {new Date(job.estimatedCompletionTime).toLocaleTimeString()}
              </Typography>
            )}
          </Box>

          {/* Details Toggle */}
          <Button
            variant="text"
            onClick={() => setShowDetails(!showDetails)}
            endIcon={
              <ExpandMoreIcon 
                sx={{ 
                  transform: showDetails ? 'rotate(180deg)' : 'rotate(0deg)',
                  transition: 'transform 0.2s'
                }} 
              />
            }
            size="small"
          >
            {showDetails ? 'Hide Details' : 'Show Details'}
          </Button>

          {/* Detailed Information */}
          <Collapse in={showDetails}>
            <Box 
              bgcolor="grey.50" 
              borderRadius={1} 
              p={2}
              display="flex" 
              flexDirection="column" 
              gap={1}
            >
              <Typography variant="body2">
                <strong>Job ID:</strong> {job.id}
              </Typography>
              
              <Typography variant="body2">
                <strong>Analysis Type:</strong> {job.analysisType}
              </Typography>
              
              {job.branchName && (
                <Typography variant="body2">
                  <strong>Branch:</strong> {job.branchName}
                </Typography>
              )}
              
              <Typography variant="body2">
                <strong>Has Results:</strong> {job.hasResults ? 'Yes' : 'No'}
              </Typography>
            </Box>
          </Collapse>

          {/* Action Buttons */}
          {showActions && job.status === 'completed' && (
            <Box display="flex" gap={1} mt={1}>
              <Button
                variant="contained"
                color="primary"
                disabled={!job.hasResults}
              >
                View Results
              </Button>
              
              <Button
                variant="outlined"
                color="primary"
                disabled={!job.hasResults}
              >
                Start Assessment
              </Button>
            </Box>
          )}
        </Box>
      </CardContent>

      {/* Cancel Confirmation Dialog */}
      <Dialog
        open={showCancelDialog}
        onClose={() => setShowCancelDialog(false)}
      >
        <DialogTitle>Cancel Analysis</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to cancel this analysis? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowCancelDialog(false)}>
            Keep Running
          </Button>
          <Button onClick={handleCancel} color="error">
            Cancel Analysis
          </Button>
        </DialogActions>
      </Dialog>
    </Card>
  );
};

export default AnalysisStatus;