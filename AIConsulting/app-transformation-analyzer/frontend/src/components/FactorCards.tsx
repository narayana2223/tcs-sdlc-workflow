/**
 * Factor Cards Component
 * Interactive cards displaying detailed 12-factor assessment results
 */

import React, { useState } from 'react';
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
  Alert
} from '@mui/material';
import {
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  ExpandMore as ExpandMoreIcon,
  Code as CodeIcon,
  Visibility as ViewIcon,
  TrendingUp as TrendingUpIcon,
  BugReport as BugIcon,
  Security as SecurityIcon,
  Speed as SpeedIcon,
  Assignment as AssignmentIcon,
  FilterList as FilterIcon,
  Sort as SortIcon
} from '@mui/icons-material';

interface Evidence {
  type: 'positive' | 'negative' | 'neutral';
  description: string;
  file_path?: string;
  line_number?: number;
  code_snippet?: string;
  confidence: number;
}

interface FactorEvaluation {
  factor_name: string;
  factor_description: string;
  score: number;
  score_name: string;
  score_reasoning: string;
  evidence: Evidence[];
  confidence: number;
  weight: number;
}

interface FactorCardsProps {
  factors: { [key: string]: FactorEvaluation };
  onFactorClick?: (factorName: string) => void;
  showEvidence?: boolean;
  groupBy?: 'score' | 'category' | 'none';
  sortBy?: 'score' | 'name' | 'confidence';
  sortOrder?: 'asc' | 'desc';
  filterBy?: string[];
}

const FactorCards: React.FC<FactorCardsProps> = ({
  factors,
  onFactorClick,
  showEvidence = true,
  groupBy = 'none',
  sortBy = 'score',
  sortOrder = 'desc',
  filterBy = []
}) => {
  const [selectedFactor, setSelectedFactor] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [localGroupBy, setLocalGroupBy] = useState(groupBy);
  const [localSortBy, setLocalSortBy] = useState(sortBy);
  const [localSortOrder, setLocalSortOrder] = useState(sortOrder);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedScores, setSelectedScores] = useState<number[]>([1, 2, 3, 4, 5]);

  const getScoreColor = (score: number): 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info' => {
    if (score >= 4) return 'success';
    if (score >= 3) return 'warning';
    if (score >= 2) return 'error';
    return 'primary';
  };

  const getScoreIcon = (score: number) => {
    if (score >= 4) return <CheckIcon color="success" />;
    if (score >= 3) return <WarningIcon color="warning" />;
    return <ErrorIcon color="error" />;
  };

  const getEvidenceIcon = (type: string) => {
    switch (type) {
      case 'positive': return <CheckIcon color="success" />;
      case 'negative': return <ErrorIcon color="error" />;
      default: return <InfoIcon color="info" />;
    }
  };

  const getCategoryIcon = (factorName: string) => {
    const categoryIcons: { [key: string]: React.ReactElement } = {
      'codebase': <CodeIcon />,
      'dependencies': <SecurityIcon />,
      'config': <SettingsIcon />,
      'backing_services': <CloudIcon />,
      'build_release_run': <BuildIcon />,
      'processes': <SpeedIcon />,
      'port_binding': <NetworkIcon />,
      'concurrency': <GroupWorkIcon />,
      'disposability': <RestartIcon />,
      'dev_prod_parity': <SyncIcon />,
      'logs': <AssignmentIcon />,
      'admin_processes': <AdminIcon />
    };
    return categoryIcons[factorName] || <InfoIcon />;
  };

  const formatFactorName = (name: string): string => {
    return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const filterAndSortFactors = () => {
    let filteredFactors = Object.entries(factors);

    // Apply search filter
    if (searchTerm) {
      filteredFactors = filteredFactors.filter(([name, factor]) =>
        name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        factor.factor_description.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Apply score filter
    if (selectedScores.length < 5) {
      filteredFactors = filteredFactors.filter(([_, factor]) =>
        selectedScores.includes(factor.score)
      );
    }

    // Apply custom filters
    if (filterBy.length > 0) {
      filteredFactors = filteredFactors.filter(([name, _]) =>
        filterBy.includes(name)
      );
    }

    // Sort factors
    filteredFactors.sort(([nameA, factorA], [nameB, factorB]) => {
      let valueA: any, valueB: any;

      switch (localSortBy) {
        case 'score':
          valueA = factorA.score;
          valueB = factorB.score;
          break;
        case 'confidence':
          valueA = factorA.confidence;
          valueB = factorB.confidence;
          break;
        case 'name':
        default:
          valueA = nameA;
          valueB = nameB;
      }

      if (localSortOrder === 'asc') {
        return valueA < valueB ? -1 : valueA > valueB ? 1 : 0;
      } else {
        return valueA > valueB ? -1 : valueA < valueB ? 1 : 0;
      }
    });

    return filteredFactors;
  };

  const groupFactors = (filteredFactors: [string, FactorEvaluation][]) => {
    if (localGroupBy === 'none') {
      return { 'All Factors': filteredFactors };
    }

    if (localGroupBy === 'score') {
      const groups: { [key: string]: [string, FactorEvaluation][] } = {};

      filteredFactors.forEach(([name, factor]) => {
        // Create dynamic group key based on actual score and score_name
        const groupKey = `${factor.score_name} (${factor.score})`;

        // Initialize group if it doesn't exist
        if (!groups[groupKey]) {
          groups[groupKey] = [];
        }

        groups[groupKey].push([name, factor]);
      });

      return groups;
    }

    if (localGroupBy === 'category') {
      const groups: { [key: string]: [string, FactorEvaluation][] } = {
        'Configuration & Dependencies': [],
        'Development & Deployment': [],
        'Runtime & Processes': [],
        'Infrastructure & Services': []
      };

      const categoryMapping: { [key: string]: string } = {
        'codebase': 'Development & Deployment',
        'dependencies': 'Configuration & Dependencies',
        'config': 'Configuration & Dependencies',
        'backing_services': 'Infrastructure & Services',
        'build_release_run': 'Development & Deployment',
        'processes': 'Runtime & Processes',
        'port_binding': 'Runtime & Processes',
        'concurrency': 'Runtime & Processes',
        'disposability': 'Runtime & Processes',
        'dev_prod_parity': 'Development & Deployment',
        'logs': 'Infrastructure & Services',
        'admin_processes': 'Runtime & Processes'
      };

      filteredFactors.forEach(([name, factor]) => {
        const category = categoryMapping[name] || 'Configuration & Dependencies';
        groups[category].push([name, factor]);
      });

      return groups;
    }

    return { 'All Factors': filteredFactors };
  };

  const FactorCard: React.FC<{ name: string; factor: FactorEvaluation }> = ({ name, factor }) => (
    <Card
      elevation={selectedFactor === name ? 8 : 2}
      sx={{
        height: '100%',
        transition: 'all 0.3s ease',
        cursor: onFactorClick ? 'pointer' : 'default',
        '&:hover': {
          elevation: 4,
          transform: 'translateY(-2px)'
        }
      }}
      onClick={() => {
        if (onFactorClick) onFactorClick(name);
        setSelectedFactor(name);
      }}
    >
      <CardContent>
        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
          <Box display="flex" alignItems="center" gap={1} flex={1}>
            <Avatar sx={{ bgcolor: getScoreColor(factor.score) + '.main', width: 32, height: 32 }}>
              {getCategoryIcon(name)}
            </Avatar>
            <Box>
              <Typography variant="h6" component="div" noWrap>
                {formatFactorName(name)}
              </Typography>
              <Typography variant="body2" color="text.secondary" noWrap>
                Factor {Object.keys(factors).indexOf(name) + 1} of {Object.keys(factors).length}
              </Typography>
            </Box>
          </Box>
          <Box display="flex" flexDirection="column" alignItems="flex-end" gap={1}>
            <Chip
              label={factor.score_name}
              color={getScoreColor(factor.score)}
              size="small"
              icon={getScoreIcon(factor.score)}
            />
            <Typography variant="h5" color="primary.main" fontWeight="bold">
              {factor.score}/5
            </Typography>
          </Box>
        </Box>

        {/* Score Progress */}
        <Box mb={2}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="body2" color="text.secondary">
              Compliance Score
            </Typography>
            <Typography variant="body2" fontWeight="bold">
              {Math.round(factor.score * 20)}%
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={factor.score * 20}
            color={getScoreColor(factor.score)}
            sx={{ height: 8, borderRadius: 4 }}
          />
        </Box>

        {/* Description */}
        <Typography variant="body2" color="text.secondary" mb={2} sx={{ minHeight: 40 }}>
          {factor.factor_description}
        </Typography>

        {/* Reasoning */}
        <Box mb={2}>
          <Typography variant="body2" fontWeight="medium" gutterBottom>
            Assessment Reasoning:
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {factor.score_reasoning}
          </Typography>
        </Box>

        {/* Confidence and Weight */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Box>
            <Typography variant="caption" color="text.secondary">
              Confidence
            </Typography>
            <Typography variant="body2" fontWeight="bold">
              {Math.round(factor.confidence * 100)}%
            </Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">
              Weight
            </Typography>
            <Typography variant="body2" fontWeight="bold">
              {factor.weight.toFixed(1)}x
            </Typography>
          </Box>
        </Box>

        {/* Evidence Summary */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="body2" fontWeight="medium">
            Evidence ({factor.evidence.length})
          </Typography>
          <Box display="flex" gap={0.5}>
            <Chip
              label={`${factor.evidence.filter(e => e.type === 'positive').length} +`}
              size="small"
              color="success"
              variant="outlined"
            />
            <Chip
              label={`${factor.evidence.filter(e => e.type === 'negative').length} -`}
              size="small"
              color="error"
              variant="outlined"
            />
            <Chip
              label={`${factor.evidence.filter(e => e.type === 'neutral').length} ~`}
              size="small"
              color="default"
              variant="outlined"
            />
          </Box>
        </Box>

        {/* Evidence Details */}
        {showEvidence && factor.evidence.length > 0 && (
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="body2">View Evidence Details</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <List dense>
                {factor.evidence.slice(0, 3).map((evidence, idx) => (
                  <ListItem key={idx} divider={idx < 2}>
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      {getEvidenceIcon(evidence.type)}
                    </ListItemIcon>
                    <ListItemText
                      primary={evidence.description}
                      secondary={
                        evidence.file_path && (
                          <Typography variant="caption" color="text.secondary">
                            {evidence.file_path}
                            {evidence.line_number && `:${evidence.line_number}`}
                            {' '}(Confidence: {Math.round(evidence.confidence * 100)}%)
                          </Typography>
                        )
                      }
                    />
                  </ListItem>
                ))}
                {factor.evidence.length > 3 && (
                  <ListItem>
                    <ListItemText>
                      <Typography variant="body2" color="primary">
                        +{factor.evidence.length - 3} more evidence items...
                      </Typography>
                    </ListItemText>
                  </ListItem>
                )}
              </List>
            </AccordionDetails>
          </Accordion>
        )}

        {/* Actions */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mt={2}>
          <Button
            size="small"
            startIcon={<ViewIcon />}
            onClick={(e) => {
              e.stopPropagation();
              setSelectedFactor(name);
            }}
          >
            View Details
          </Button>
          <Box display="flex" alignItems="center" gap={1}>
            {factor.score >= 4 && <TrendingUpIcon color="success" />}
            {factor.score <= 2 && <BugIcon color="error" />}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  const FactorDetailDialog: React.FC = () => {
    const factor = selectedFactor ? factors[selectedFactor] : null;

    if (!factor) return null;

    return (
      <Dialog
        open={!!selectedFactor}
        onClose={() => setSelectedFactor(null)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h6">
              {formatFactorName(selectedFactor!)} - Detailed Analysis
            </Typography>
            <Chip
              label={`${factor.score}/5 - ${factor.score_name}`}
              color={getScoreColor(factor.score)}
              icon={getScoreIcon(factor.score)}
            />
          </Box>
        </DialogTitle>
        <DialogContent>
          <Typography variant="body1" paragraph>
            {factor.factor_description}
          </Typography>

          <Alert severity={factor.score >= 4 ? 'success' : factor.score >= 3 ? 'warning' : 'error'} sx={{ mb: 2 }}>
            <Typography variant="body2">
              <strong>Assessment Result:</strong> {factor.score_reasoning}
            </Typography>
          </Alert>

          <Typography variant="h6" gutterBottom>
            Evidence Analysis ({factor.evidence.length} items)
          </Typography>

          <List>
            {factor.evidence.map((evidence, idx) => (
              <ListItem key={idx} divider>
                <ListItemIcon>
                  {getEvidenceIcon(evidence.type)}
                </ListItemIcon>
                <ListItemText
                  primary={evidence.description}
                  secondary={
                    <Box mt={1}>
                      {evidence.file_path && (
                        <Typography variant="caption" display="block" color="text.secondary">
                          File: {evidence.file_path}
                          {evidence.line_number && ` (Line ${evidence.line_number})`}
                        </Typography>
                      )}
                      <Typography variant="caption" color="text.secondary">
                        Confidence: {Math.round(evidence.confidence * 100)}%
                      </Typography>
                      {evidence.code_snippet && (
                        <Box
                          component="pre"
                          sx={{
                            mt: 1,
                            p: 1,
                            bgcolor: 'grey.100',
                            borderRadius: 1,
                            fontSize: '0.8rem',
                            overflow: 'auto'
                          }}
                        >
                          {evidence.code_snippet}
                        </Box>
                      )}
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelectedFactor(null)}>Close</Button>
        </DialogActions>
      </Dialog>
    );
  };

  const FilterDialog: React.FC = () => (
    <Dialog open={showFilters} onClose={() => setShowFilters(false)} maxWidth="sm" fullWidth>
      <DialogTitle>Filter & Sort Factors</DialogTitle>
      <DialogContent>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Search factors"
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
                <MenuItem value="score">Score Level</MenuItem>
                <MenuItem value="category">Category</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} sm={6}>
            <FormControl fullWidth size="small">
              <InputLabel>Sort By</InputLabel>
              <Select
                value={localSortBy}
                label="Sort By"
                onChange={(e) => setLocalSortBy(e.target.value as any)}
              >
                <MenuItem value="score">Score</MenuItem>
                <MenuItem value="name">Name</MenuItem>
                <MenuItem value="confidence">Confidence</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12}>
            <Typography variant="body2" gutterBottom>
              Filter by Scores:
            </Typography>
            <Box display="flex" gap={1} flexWrap="wrap">
              {[1, 2, 3, 4, 5].map(score => (
                <Chip
                  key={score}
                  label={`${score} Star`}
                  color={selectedScores.includes(score) ? 'primary' : 'default'}
                  onClick={() => {
                    setSelectedScores(prev =>
                      prev.includes(score)
                        ? prev.filter(s => s !== score)
                        : [...prev, score]
                    );
                  }}
                  variant={selectedScores.includes(score) ? 'filled' : 'outlined'}
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
            setSelectedScores([1, 2, 3, 4, 5]);
            setLocalGroupBy('none');
            setLocalSortBy('score');
            setLocalSortOrder('desc');
          }}
        >
          Reset
        </Button>
      </DialogActions>
    </Dialog>
  );

  const filteredFactors = filterAndSortFactors();
  const groupedFactors = groupFactors(filteredFactors);

  return (
    <Box>
      {/* Controls */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h6">
          Factor Analysis ({filteredFactors.length} factors)
        </Typography>
        <Box display="flex" gap={1}>
          <IconButton onClick={() => setShowFilters(true)}>
            <FilterIcon />
          </IconButton>
          <IconButton
            onClick={() => setLocalSortOrder(localSortOrder === 'asc' ? 'desc' : 'asc')}
          >
            <SortIcon />
          </IconButton>
        </Box>
      </Box>

      {/* Factor Groups */}
      {Object.entries(groupedFactors).map(([groupName, groupFactors]) => (
        <Box key={groupName} mb={4}>
          {localGroupBy !== 'none' && (
            <Typography variant="h6" gutterBottom color="primary">
              {groupName} ({groupFactors.length})
            </Typography>
          )}

          <Grid container spacing={3}>
            {groupFactors.map(([name, factor]) => (
              <Grid item xs={12} md={6} lg={4} key={name}>
                <FactorCard name={name} factor={factor} />
              </Grid>
            ))}
          </Grid>

          {localGroupBy !== 'none' && <Divider sx={{ mt: 3 }} />}
        </Box>
      ))}

      {filteredFactors.length === 0 && (
        <Box textAlign="center" py={6}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No factors match your filters
          </Typography>
          <Button onClick={() => setShowFilters(true)}>
            Adjust Filters
          </Button>
        </Box>
      )}

      <FactorDetailDialog />
      <FilterDialog />
    </Box>
  );
};

// Additional icon components for completeness
const SettingsIcon = () => <InfoIcon />;
const CloudIcon = () => <InfoIcon />;
const BuildIcon = () => <InfoIcon />;
const NetworkIcon = () => <InfoIcon />;
const GroupWorkIcon = () => <InfoIcon />;
const RestartIcon = () => <InfoIcon />;
const SyncIcon = () => <InfoIcon />;
const AdminIcon = () => <InfoIcon />;

export default FactorCards;