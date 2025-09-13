/**
 * Recommendations Component
 * Interactive component for displaying actionable 12-factor recommendations
 */

import React, { useState, useMemo } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Grid,
  Avatar,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  IconButton,
  Tooltip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Paper,
  Tabs,
  Tab,
  Checkbox,
  FormControlLabel,
  Rating
} from '@mui/material';
import {
  PlayArrow as StartIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  ExpandMore as ExpandMoreIcon,
  Code as CodeIcon,
  Schedule as ScheduleIcon,
  TrendingUp as BenefitIcon,
  Security as RiskIcon,
  Assignment as TaskIcon,
  Lightbulb as IdeaIcon,
  FilterList as FilterIcon,
  Sort as SortIcon,
  BookmarkBorder as BookmarkIcon,
  BookmarkAdd as BookmarkedIcon,
  ContentCopy as CopyIcon,
  Launch as LaunchIcon,
  Timeline as RoadmapIcon
} from '@mui/icons-material';

interface Recommendation {
  id: string;
  factor_name: string;
  title: string;
  description: string;
  rationale: string;
  implementation_steps: string[];
  priority: 'critical' | 'high' | 'medium' | 'low';
  complexity: 'low' | 'medium' | 'high' | 'very_high';
  estimated_effort: string;
  benefits: string[];
  risks: string[];
  prerequisites: string[];
  resources: string[];
  code_examples: Array<{
    language: string;
    title: string;
    code: string;
  }>;
}

interface RecommendationsProps {
  recommendations: Recommendation[];
  onRecommendationClick?: (recommendation: Recommendation) => void;
  showImplementation?: boolean;
  groupBy?: 'priority' | 'factor' | 'complexity' | 'none';
  filterBy?: {
    priority?: string[];
    complexity?: string[];
    factor?: string[];
  };
}

const Recommendations: React.FC<RecommendationsProps> = ({
  recommendations,
  onRecommendationClick,
  showImplementation = true,
  groupBy = 'priority',
  filterBy = {}
}) => {
  const [selectedRecommendation, setSelectedRecommendation] = useState<Recommendation | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const [bookmarkedIds, setBookmarkedIds] = useState<string[]>([]);
  const [completedSteps, setCompletedSteps] = useState<{ [key: string]: number[] }>({});
  const [searchTerm, setSearchTerm] = useState('');

  // Filtering state
  const [selectedPriorities, setSelectedPriorities] = useState<string[]>(['critical', 'high', 'medium', 'low']);
  const [selectedComplexities, setSelectedComplexities] = useState<string[]>(['low', 'medium', 'high', 'very_high']);
  const [selectedFactors, setSelectedFactors] = useState<string[]>([]);

  const [localGroupBy, setLocalGroupBy] = useState(groupBy);
  const [sortBy, setSortBy] = useState<'priority' | 'complexity' | 'effort' | 'factor'>('priority');

  const priorityOrder = { 'critical': 4, 'high': 3, 'medium': 2, 'low': 1 };
  const complexityOrder = { 'low': 1, 'medium': 2, 'high': 3, 'very_high': 4 };

  const getPriorityColor = (priority: string): 'error' | 'warning' | 'info' | 'success' => {
    switch (priority) {
      case 'critical': return 'error';
      case 'high': return 'warning';
      case 'medium': return 'info';
      default: return 'success';
    }
  };

  const getComplexityColor = (complexity: string): 'success' | 'info' | 'warning' | 'error' => {
    switch (complexity) {
      case 'low': return 'success';
      case 'medium': return 'info';
      case 'high': return 'warning';
      default: return 'error';
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'critical': return <ErrorIcon color="error" />;
      case 'high': return <WarningIcon color="warning" />;
      case 'medium': return <InfoIcon color="info" />;
      default: return <CheckIcon color="success" />;
    }
  };

  const formatFactorName = (name: string): string => {
    return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const toggleBookmark = (id: string) => {
    setBookmarkedIds(prev =>
      prev.includes(id)
        ? prev.filter(bookmarkId => bookmarkId !== id)
        : [...prev, id]
    );
  };

  const toggleStepCompletion = (recommendationId: string, stepIndex: number) => {
    setCompletedSteps(prev => {
      const current = prev[recommendationId] || [];
      const updated = current.includes(stepIndex)
        ? current.filter(i => i !== stepIndex)
        : [...current, stepIndex];

      return { ...prev, [recommendationId]: updated };
    });
  };

  const filteredRecommendations = useMemo(() => {
    let filtered = recommendations;

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(rec =>
        rec.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        rec.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        rec.factor_name.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Apply priority filter
    filtered = filtered.filter(rec => selectedPriorities.includes(rec.priority));

    // Apply complexity filter
    filtered = filtered.filter(rec => selectedComplexities.includes(rec.complexity));

    // Apply factor filter
    if (selectedFactors.length > 0) {
      filtered = filtered.filter(rec => selectedFactors.includes(rec.factor_name));
    }

    // Apply external filters
    if (filterBy.priority) {
      filtered = filtered.filter(rec => filterBy.priority!.includes(rec.priority));
    }
    if (filterBy.complexity) {
      filtered = filtered.filter(rec => filterBy.complexity!.includes(rec.complexity));
    }
    if (filterBy.factor) {
      filtered = filtered.filter(rec => filterBy.factor!.includes(rec.factor_name));
    }

    // Sort recommendations
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'priority':
          return priorityOrder[b.priority] - priorityOrder[a.priority];
        case 'complexity':
          return complexityOrder[a.complexity] - complexityOrder[b.complexity];
        case 'factor':
          return a.factor_name.localeCompare(b.factor_name);
        case 'effort':
          // Simple effort comparison based on string
          return a.estimated_effort.localeCompare(b.estimated_effort);
        default:
          return 0;
      }
    });

    return filtered;
  }, [recommendations, searchTerm, selectedPriorities, selectedComplexities, selectedFactors, filterBy, sortBy]);

  const groupedRecommendations = useMemo(() => {
    if (localGroupBy === 'none') {
      return { 'All Recommendations': filteredRecommendations };
    }

    const groups: { [key: string]: Recommendation[] } = {};

    filteredRecommendations.forEach(rec => {
      let groupKey: string;

      switch (localGroupBy) {
        case 'priority':
          groupKey = `${rec.priority.charAt(0).toUpperCase() + rec.priority.slice(1)} Priority`;
          break;
        case 'factor':
          groupKey = formatFactorName(rec.factor_name);
          break;
        case 'complexity':
          groupKey = `${rec.complexity.charAt(0).toUpperCase() + rec.complexity.slice(1)} Complexity`;
          break;
        default:
          groupKey = 'Other';
      }

      if (!groups[groupKey]) {
        groups[groupKey] = [];
      }
      groups[groupKey].push(rec);
    });

    return groups;
  }, [filteredRecommendations, localGroupBy]);

  const RecommendationCard: React.FC<{ recommendation: Recommendation }> = ({ recommendation }) => {
    const isBookmarked = bookmarkedIds.includes(recommendation.id);
    const completedStepsCount = completedSteps[recommendation.id]?.length || 0;
    const progressPercent = (completedStepsCount / recommendation.implementation_steps.length) * 100;

    return (
      <Card
        elevation={2}
        sx={{
          height: '100%',
          transition: 'all 0.3s ease',
          cursor: 'pointer',
          '&:hover': {
            elevation: 6,
            transform: 'translateY(-2px)'
          }
        }}
        onClick={() => {
          setSelectedRecommendation(recommendation);
          if (onRecommendationClick) onRecommendationClick(recommendation);
        }}
      >
        <CardContent>
          {/* Header */}
          <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
            <Box display="flex" alignItems="center" gap={1} flex={1}>
              <Avatar sx={{ bgcolor: getPriorityColor(recommendation.priority) + '.main', width: 32, height: 32 }}>
                {getPriorityIcon(recommendation.priority)}
              </Avatar>
              <Box>
                <Typography variant="h6" component="div" noWrap>
                  {recommendation.title}
                </Typography>
                <Typography variant="body2" color="text.secondary" noWrap>
                  {formatFactorName(recommendation.factor_name)}
                </Typography>
              </Box>
            </Box>
            <Box display="flex" alignItems="center" gap={1}>
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  toggleBookmark(recommendation.id);
                }}
              >
                {isBookmarked ? <BookmarkedIcon color="primary" /> : <BookmarkIcon />}
              </IconButton>
            </Box>
          </Box>

          {/* Priority and Complexity Chips */}
          <Box display="flex" gap={1} mb={2}>
            <Chip
              label={recommendation.priority.toUpperCase()}
              color={getPriorityColor(recommendation.priority)}
              size="small"
            />
            <Chip
              label={`${recommendation.complexity} complexity`}
              color={getComplexityColor(recommendation.complexity)}
              variant="outlined"
              size="small"
            />
            <Chip
              label={recommendation.estimated_effort}
              variant="outlined"
              size="small"
              icon={<ScheduleIcon />}
            />
          </Box>

          {/* Description */}
          <Typography variant="body2" color="text.secondary" mb={2} sx={{
            display: '-webkit-box',
            WebkitLineClamp: 3,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden'
          }}>
            {recommendation.description}
          </Typography>

          {/* Progress */}
          <Box mb={2}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
              <Typography variant="body2" color="text.secondary">
                Implementation Progress
              </Typography>
              <Typography variant="body2" fontWeight="bold">
                {completedStepsCount}/{recommendation.implementation_steps.length} steps
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={progressPercent}
              color={progressPercent === 100 ? 'success' : 'primary'}
              sx={{ height: 6, borderRadius: 3 }}
            />
          </Box>

          {/* Benefits and Risks Summary */}
          <Box display="flex" justifyContent="space-between" mb={2}>
            <Box display="flex" alignItems="center" gap={0.5}>
              <BenefitIcon color="success" fontSize="small" />
              <Typography variant="body2" color="text.secondary">
                {recommendation.benefits.length} benefits
              </Typography>
            </Box>
            <Box display="flex" alignItems="center" gap={0.5}>
              <RiskIcon color="warning" fontSize="small" />
              <Typography variant="body2" color="text.secondary">
                {recommendation.risks.length} risks
              </Typography>
            </Box>
          </Box>

          {/* Action Buttons */}
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Button
              size="small"
              startIcon={<StartIcon />}
              variant={progressPercent > 0 ? 'outlined' : 'contained'}
              onClick={(e) => {
                e.stopPropagation();
                setSelectedRecommendation(recommendation);
              }}
            >
              {progressPercent > 0 ? 'Continue' : 'Start'}
            </Button>

            <Box display="flex" alignItems="center" gap={1}>
              <Rating
                size="small"
                value={priorityOrder[recommendation.priority]}
                max={4}
                readOnly
              />
            </Box>
          </Box>
        </CardContent>
      </Card>
    );
  };

  const RecommendationDetailDialog: React.FC = () => {
    if (!selectedRecommendation) return null;

    const rec = selectedRecommendation;
    const stepsCompleted = completedSteps[rec.id] || [];

    return (
      <Dialog
        open={!!selectedRecommendation}
        onClose={() => setSelectedRecommendation(null)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h6">
              {rec.title}
            </Typography>
            <Box display="flex" gap={1}>
              <Chip
                label={rec.priority.toUpperCase()}
                color={getPriorityColor(rec.priority)}
                size="small"
              />
              <Chip
                label={`${rec.complexity} complexity`}
                color={getComplexityColor(rec.complexity)}
                variant="outlined"
                size="small"
              />
            </Box>
          </Box>
        </DialogTitle>

        <DialogContent>
          <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)} sx={{ mb: 2 }}>
            <Tab label="Overview" icon={<InfoIcon />} />
            <Tab label="Implementation" icon={<TaskIcon />} />
            <Tab label="Code Examples" icon={<CodeIcon />} />
            <Tab label="Resources" icon={<LaunchIcon />} />
          </Tabs>

          {/* Overview Tab */}
          {activeTab === 0 && (
            <Box>
              <Typography variant="body1" paragraph>
                {rec.description}
              </Typography>

              <Alert severity="info" sx={{ mb: 2 }}>
                <Typography variant="body2">
                  <strong>Rationale:</strong> {rec.rationale}
                </Typography>
              </Alert>

              <Grid container spacing={2}>
                <Grid item xs={12} md={4}>
                  <Paper sx={{ p: 2, bgcolor: 'success.light' }}>
                    <Typography variant="h6" color="success.contrastText" gutterBottom>
                      Benefits
                    </Typography>
                    <List dense>
                      {rec.benefits.map((benefit, idx) => (
                        <ListItem key={idx} sx={{ py: 0.5 }}>
                          <ListItemIcon sx={{ minWidth: 32 }}>
                            <BenefitIcon color="success" />
                          </ListItemIcon>
                          <ListItemText
                            primary={benefit}
                            primaryTypographyProps={{ variant: 'body2' }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Paper>
                </Grid>

                <Grid item xs={12} md={4}>
                  <Paper sx={{ p: 2, bgcolor: 'warning.light' }}>
                    <Typography variant="h6" color="warning.contrastText" gutterBottom>
                      Risks
                    </Typography>
                    <List dense>
                      {rec.risks.map((risk, idx) => (
                        <ListItem key={idx} sx={{ py: 0.5 }}>
                          <ListItemIcon sx={{ minWidth: 32 }}>
                            <RiskIcon color="warning" />
                          </ListItemIcon>
                          <ListItemText
                            primary={risk}
                            primaryTypographyProps={{ variant: 'body2' }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Paper>
                </Grid>

                <Grid item xs={12} md={4}>
                  <Paper sx={{ p: 2, bgcolor: 'info.light' }}>
                    <Typography variant="h6" color="info.contrastText" gutterBottom>
                      Prerequisites
                    </Typography>
                    <List dense>
                      {rec.prerequisites.map((prereq, idx) => (
                        <ListItem key={idx} sx={{ py: 0.5 }}>
                          <ListItemIcon sx={{ minWidth: 32 }}>
                            <CheckIcon color="info" />
                          </ListItemIcon>
                          <ListItemText
                            primary={prereq}
                            primaryTypographyProps={{ variant: 'body2' }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Paper>
                </Grid>
              </Grid>

              <Box mt={2} p={2} bgcolor="grey.50" borderRadius={1}>
                <Typography variant="h6" gutterBottom>
                  Estimated Effort: {rec.estimated_effort}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Factor: {formatFactorName(rec.factor_name)}
                </Typography>
              </Box>
            </Box>
          )}

          {/* Implementation Tab */}
          {activeTab === 1 && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Implementation Steps
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Track your progress by checking off completed steps:
              </Typography>

              <Stepper orientation="vertical">
                {rec.implementation_steps.map((step, index) => {
                  const isCompleted = stepsCompleted.includes(index);

                  return (
                    <Step key={index} active={true}>
                      <StepLabel
                        StepIconComponent={() => (
                          <Checkbox
                            checked={isCompleted}
                            onChange={() => toggleStepCompletion(rec.id, index)}
                            color="primary"
                          />
                        )}
                      >
                        <Typography
                          variant="body2"
                          sx={{
                            textDecoration: isCompleted ? 'line-through' : 'none',
                            color: isCompleted ? 'text.secondary' : 'text.primary'
                          }}
                        >
                          {step}
                        </Typography>
                      </StepLabel>
                    </Step>
                  );
                })}
              </Stepper>

              <Box mt={3}>
                <LinearProgress
                  variant="determinate"
                  value={(stepsCompleted.length / rec.implementation_steps.length) * 100}
                  sx={{ height: 8, borderRadius: 4 }}
                />
                <Typography variant="body2" color="text.secondary" textAlign="center" mt={1}>
                  {stepsCompleted.length} of {rec.implementation_steps.length} steps completed
                </Typography>
              </Box>
            </Box>
          )}

          {/* Code Examples Tab */}
          {activeTab === 2 && (
            <Box>
              {rec.code_examples.length > 0 ? (
                <Box>
                  {rec.code_examples.map((example, idx) => (
                    <Box key={idx} mb={3}>
                      <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                        <Typography variant="h6">
                          {example.title}
                        </Typography>
                        <Box display="flex" gap={1}>
                          <Chip label={example.language} variant="outlined" size="small" />
                          <IconButton size="small" onClick={() => navigator.clipboard.writeText(example.code)}>
                            <CopyIcon />
                          </IconButton>
                        </Box>
                      </Box>
                      <Paper sx={{ p: 2, bgcolor: 'grey.100' }}>
                        <Box
                          component="pre"
                          sx={{
                            fontFamily: 'monospace',
                            fontSize: '0.875rem',
                            overflow: 'auto',
                            margin: 0
                          }}
                        >
                          {example.code}
                        </Box>
                      </Paper>
                    </Box>
                  ))}
                </Box>
              ) : (
                <Box textAlign="center" py={4}>
                  <CodeIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" color="text.secondary">
                    No code examples available
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Implementation details may be added in future updates.
                  </Typography>
                </Box>
              )}
            </Box>
          )}

          {/* Resources Tab */}
          {activeTab === 3 && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Additional Resources
              </Typography>
              {rec.resources.length > 0 ? (
                <List>
                  {rec.resources.map((resource, idx) => (
                    <ListItem key={idx} divider>
                      <ListItemIcon>
                        <LaunchIcon />
                      </ListItemIcon>
                      <ListItemText
                        primary={resource}
                        primaryTypographyProps={{
                          component: 'a',
                          href: resource.startsWith('http') ? resource : `https://${resource}`,
                          target: '_blank',
                          rel: 'noopener noreferrer',
                          color: 'primary',
                          sx: { textDecoration: 'none', '&:hover': { textDecoration: 'underline' } }
                        }}
                      />
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Box textAlign="center" py={4}>
                  <LaunchIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" color="text.secondary">
                    No additional resources provided
                  </Typography>
                </Box>
              )}
            </Box>
          )}
        </DialogContent>

        <DialogActions>
          <Button onClick={() => setSelectedRecommendation(null)}>
            Close
          </Button>
          <Button
            variant="contained"
            startIcon={bookmarkedIds.includes(rec.id) ? <BookmarkedIcon /> : <BookmarkIcon />}
            onClick={() => toggleBookmark(rec.id)}
          >
            {bookmarkedIds.includes(rec.id) ? 'Bookmarked' : 'Bookmark'}
          </Button>
        </DialogActions>
      </Dialog>
    );
  };

  const FilterDialog: React.FC = () => (
    <Dialog open={showFilters} onClose={() => setShowFilters(false)} maxWidth="sm" fullWidth>
      <DialogTitle>Filter Recommendations</DialogTitle>
      <DialogContent>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Search recommendations"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              size="small"
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <FormControl fullWidth size="small">
              <InputLabel>Group By</InputLabel>
              <Select
                value={localGroupBy}
                label="Group By"
                onChange={(e) => setLocalGroupBy(e.target.value as any)}
              >
                <MenuItem value="none">No Grouping</MenuItem>
                <MenuItem value="priority">Priority</MenuItem>
                <MenuItem value="factor">Factor</MenuItem>
                <MenuItem value="complexity">Complexity</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} sm={6}>
            <FormControl fullWidth size="small">
              <InputLabel>Sort By</InputLabel>
              <Select
                value={sortBy}
                label="Sort By"
                onChange={(e) => setSortBy(e.target.value as any)}
              >
                <MenuItem value="priority">Priority</MenuItem>
                <MenuItem value="complexity">Complexity</MenuItem>
                <MenuItem value="effort">Effort</MenuItem>
                <MenuItem value="factor">Factor</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12}>
            <Typography variant="body2" gutterBottom>
              Priority Filter:
            </Typography>
            <Box display="flex" gap={1} flexWrap="wrap">
              {['critical', 'high', 'medium', 'low'].map(priority => (
                <Chip
                  key={priority}
                  label={priority}
                  color={selectedPriorities.includes(priority) ? getPriorityColor(priority) : 'default'}
                  onClick={() => {
                    setSelectedPriorities(prev =>
                      prev.includes(priority)
                        ? prev.filter(p => p !== priority)
                        : [...prev, priority]
                    );
                  }}
                  variant={selectedPriorities.includes(priority) ? 'filled' : 'outlined'}
                  size="small"
                />
              ))}
            </Box>
          </Grid>

          <Grid item xs={12}>
            <Typography variant="body2" gutterBottom>
              Complexity Filter:
            </Typography>
            <Box display="flex" gap={1} flexWrap="wrap">
              {['low', 'medium', 'high', 'very_high'].map(complexity => (
                <Chip
                  key={complexity}
                  label={complexity.replace('_', ' ')}
                  color={selectedComplexities.includes(complexity) ? getComplexityColor(complexity) : 'default'}
                  onClick={() => {
                    setSelectedComplexities(prev =>
                      prev.includes(complexity)
                        ? prev.filter(c => c !== complexity)
                        : [...prev, complexity]
                    );
                  }}
                  variant={selectedComplexities.includes(complexity) ? 'filled' : 'outlined'}
                  size="small"
                />
              ))}
            </Box>
          </Grid>
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setShowFilters(false)}>Close</Button>
        <Button
          onClick={() => {
            setSearchTerm('');
            setSelectedPriorities(['critical', 'high', 'medium', 'low']);
            setSelectedComplexities(['low', 'medium', 'high', 'very_high']);
            setSelectedFactors([]);
            setLocalGroupBy('priority');
            setSortBy('priority');
          }}
        >
          Reset
        </Button>
      </DialogActions>
    </Dialog>
  );

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h6">
            Recommendations ({filteredRecommendations.length})
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {bookmarkedIds.length} bookmarked • {Object.keys(completedSteps).length} in progress
          </Typography>
        </Box>
        <Box display="flex" gap={1}>
          <IconButton onClick={() => setShowFilters(true)}>
            <FilterIcon />
          </IconButton>
          <Button
            variant="outlined"
            startIcon={<RoadmapIcon />}
            size="small"
          >
            Roadmap
          </Button>
        </Box>
      </Box>

      {/* Quick Stats */}
      <Grid container spacing={2} mb={3}>
        <Grid item xs={6} sm={3}>
          <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'error.light' }}>
            <Typography variant="h6" color="error.contrastText">
              {filteredRecommendations.filter(r => r.priority === 'critical').length}
            </Typography>
            <Typography variant="caption" color="error.contrastText">
              Critical
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'warning.light' }}>
            <Typography variant="h6" color="warning.contrastText">
              {filteredRecommendations.filter(r => r.priority === 'high').length}
            </Typography>
            <Typography variant="caption" color="warning.contrastText">
              High Priority
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'success.light' }}>
            <Typography variant="h6" color="success.contrastText">
              {filteredRecommendations.filter(r => r.complexity === 'low').length}
            </Typography>
            <Typography variant="caption" color="success.contrastText">
              Quick Wins
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'info.light' }}>
            <Typography variant="h6" color="info.contrastText">
              {new Set(filteredRecommendations.map(r => r.factor_name)).size}
            </Typography>
            <Typography variant="caption" color="info.contrastText">
              Factors Covered
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* Grouped Recommendations */}
      {Object.entries(groupedRecommendations).map(([groupName, groupRecommendations]) => (
        <Box key={groupName} mb={4}>
          {localGroupBy !== 'none' && (
            <Typography variant="h6" gutterBottom color="primary">
              {groupName} ({groupRecommendations.length})
            </Typography>
          )}

          <Grid container spacing={3}>
            {groupRecommendations.map((recommendation) => (
              <Grid item xs={12} md={6} lg={4} key={recommendation.id}>
                <RecommendationCard recommendation={recommendation} />
              </Grid>
            ))}
          </Grid>

          {localGroupBy !== 'none' && <Divider sx={{ mt: 3 }} />}
        </Box>
      ))}

      {filteredRecommendations.length === 0 && (
        <Box textAlign="center" py={6}>
          <IdeaIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No recommendations match your filters
          </Typography>
          <Button onClick={() => setShowFilters(true)}>
            Adjust Filters
          </Button>
        </Box>
      )}

      <RecommendationDetailDialog />
      <FilterDialog />
    </Box>
  );
};

export default Recommendations;