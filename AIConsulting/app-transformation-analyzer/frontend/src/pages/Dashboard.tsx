/**
 * Dashboard Page
 * Main dashboard showing overview of analyses, assessments, and statistics
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Alert,
  LinearProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Tooltip,
  Paper,
} from '@mui/material';
import {
  Analytics as AnalyticsIcon,
  Assessment as AssessmentIcon,
  TrendingUp as TrendingUpIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  PlayArrow as ViewIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../services/api';
import { DashboardData, AnalysisJob, AssessmentJob, LoadingState } from '../types';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState<LoadingState>({ loading: true });

  const loadDashboardData = async () => {
    try {
      setLoading({ loading: true });
      const data = await apiClient.getDashboardData();
      setDashboardData(data);
      setLoading({ loading: false });
    } catch (error: any) {
      setLoading({ loading: false, error: error.message });
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const StatCard: React.FC<{
    title: string;
    value: number | string;
    icon: React.ReactNode;
    color: 'primary' | 'secondary' | 'success' | 'warning';
    subtitle?: string;
  }> = ({ title, value, icon, color, subtitle }) => (
    <Card elevation={2}>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography color="textSecondary" gutterBottom variant="h6">
              {title}
            </Typography>
            <Typography variant="h4" component="div" color={`${color}.main`}>
              {value}
            </Typography>
            {subtitle && (
              <Typography variant="body2" color="textSecondary">
                {subtitle}
              </Typography>
            )}
          </Box>
          <Box color={`${color}.main`} sx={{ fontSize: 40 }}>
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  const RecentJobsList: React.FC<{
    title: string;
    jobs: (AnalysisJob | AssessmentJob)[];
    onViewAll: () => void;
    emptyMessage: string;
  }> = ({ title, jobs, onViewAll, emptyMessage }) => (
    <Card elevation={2}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">{title}</Typography>
          <Button variant="outlined" size="small" onClick={onViewAll}>
            View All
          </Button>
        </Box>
        
        {jobs.length === 0 ? (
          <Typography color="textSecondary" textAlign="center" py={2}>
            {emptyMessage}
          </Typography>
        ) : (
          <List dense>
            {jobs.map((job) => (
              <ListItem
                key={job.id}
                secondaryAction={
                  <Box display="flex" alignItems="center" gap={1}>
                    <Chip
                      label={job.status.toUpperCase()}
                      color={getStatusColor(job.status)}
                      size="small"
                    />
                    <Tooltip title="View details">
                      <IconButton size="small">
                        <ViewIcon />
                      </IconButton>
                    </Tooltip>
                  </Box>
                }
              >
                <ListItemIcon>
                  {job.status === 'completed' ? (
                    <SuccessIcon color="success" />
                  ) : job.status === 'failed' ? (
                    <ErrorIcon color="error" />
                  ) : (
                    <AnalyticsIcon color="primary" />
                  )}
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Typography variant="body2" noWrap>
                      {job.repositoryUrl.split('/').slice(-2).join('/')}
                    </Typography>
                  }
                  secondary={`Created: ${formatDate(job.createdAt)}`}
                />
              </ListItem>
            ))}
          </List>
        )}
      </CardContent>
    </Card>
  );

  if (loading.loading) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Dashboard
        </Typography>
        <LinearProgress />
        <Box mt={2}>
          <Typography color="textSecondary">Loading dashboard data...</Typography>
        </Box>
      </Box>
    );
  }

  if (loading.error) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Dashboard
        </Typography>
        <Alert 
          severity="error" 
          action={
            <Button color="inherit" size="small" onClick={loadDashboardData}>
              <RefreshIcon fontSize="small" sx={{ mr: 1 }} />
              Retry
            </Button>
          }
        >
          Failed to load dashboard data: {loading.error}
        </Alert>
      </Box>
    );
  }

  if (!dashboardData) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Dashboard
        </Typography>
        <Alert severity="warning">
          No dashboard data available
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Typography variant="h4" gutterBottom>
          Dashboard
        </Typography>
        <Button
          variant="contained"
          onClick={() => navigate('/analysis')}
          startIcon={<AnalyticsIcon />}
        >
          New Analysis
        </Button>
      </Box>

      {/* Statistics Cards */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Analyses"
            value={dashboardData.statistics.totalAnalyses}
            icon={<AnalyticsIcon />}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Assessments"
            value={dashboardData.statistics.totalAssessments}
            icon={<AssessmentIcon />}
            color="secondary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Average Score"
            value={dashboardData.statistics.averageScore.toFixed(1)}
            icon={<TrendingUpIcon />}
            color="success"
            subtitle="12-Factor Compliance"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Success Rate"
            value={`${dashboardData.statistics.successRate}%`}
            icon={<SuccessIcon />}
            color="warning"
            subtitle="Analysis Success"
          />
        </Grid>
      </Grid>

      {/* Recent Activity */}
      <Grid container spacing={3}>
        <Grid item xs={12} lg={6}>
          <RecentJobsList
            title="Recent Analyses"
            jobs={dashboardData.recentAnalyses}
            onViewAll={() => navigate('/analysis')}
            emptyMessage="No recent analyses. Start your first repository analysis!"
          />
        </Grid>
        <Grid item xs={12} lg={6}>
          <RecentJobsList
            title="Recent Assessments"
            jobs={dashboardData.recentAssessments}
            onViewAll={() => navigate('/assessment')}
            emptyMessage="No recent assessments. Complete an analysis first to run assessments."
          />
        </Grid>
      </Grid>

      {/* Quick Actions */}
      <Paper elevation={1} sx={{ mt: 4, p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Quick Actions
        </Typography>
        <Box display="flex" flex-wrap="wrap" gap={2}>
          <Button
            variant="outlined"
            onClick={() => navigate('/analysis')}
            startIcon={<AnalyticsIcon />}
          >
            Start New Analysis
          </Button>
          <Button
            variant="outlined"
            onClick={() => navigate('/assessment')}
            startIcon={<AssessmentIcon />}
          >
            View All Assessments
          </Button>
          <Button
            variant="outlined"
            onClick={loadDashboardData}
            startIcon={<RefreshIcon />}
          >
            Refresh Data
          </Button>
        </Box>
      </Paper>

      {/* Welcome Message for New Users */}
      {dashboardData.statistics.totalAnalyses === 0 && (
        <Alert severity="info" sx={{ mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Welcome to Application Transformation Analyzer!
          </Typography>
          <Typography>
            Get started by analyzing your first repository. We'll evaluate your application 
            against the 12-factor methodology and provide recommendations for improvement.
          </Typography>
          <Box mt={2}>
            <Button
              variant="contained"
              onClick={() => navigate('/analysis')}
              startIcon={<AnalyticsIcon />}
            >
              Analyze Your First Repository
            </Button>
          </Box>
        </Alert>
      )}
    </Box>
  );
};

export default Dashboard;