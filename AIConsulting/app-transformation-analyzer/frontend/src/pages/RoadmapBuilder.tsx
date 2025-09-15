import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Chip,
  Button,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Tooltip,
  LinearProgress,
  Avatar,
  AvatarGroup,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  PlayArrow,
  CheckCircle,
  Schedule,
  Group,
  AttachMoney,
  Code,
  CloudUpload,
  Security,
  Speed,
  GetApp,
  DragIndicator,
  Add,
  Edit,
  Delete,
  Business,
  Engineering,
  Build,
  BugReport,
  TrendingUp,
  Assignment,
  PictureAsPdf,
  TableChart,
  DataObject,
  Description,
  ArrowDropDown,
} from '@mui/icons-material';
import axios from 'axios';

interface Milestone {
  id: string;
  title: string;
  description: string;
  startDate: string;
  endDate: string;
  status: 'not_started' | 'in_progress' | 'completed';
  dependencies: string[];
  resources: {
    teamSize: number;
    budget: number;
    technologies: string[];
  };
  deliverables: string[];
  phaseId: string;
}

interface Phase {
  id: string;
  name: string;
  description: string;
  startDate: string;
  endDate: string;
  color: string;
  milestones: Milestone[];
  totalBudget: number;
  teamAllocation: {
    developers: number;
    architects: number;
    devops: number;
    qa: number;
  };
}

interface TransformationRoadmap {
  id: string;
  title: string;
  description: string;
  phases: Phase[];
  totalBudget: number;
  totalDuration: string;
}

const RoadmapBuilder: React.FC = () => {
  const [roadmap, setRoadmap] = useState<TransformationRoadmap | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedMilestone, setSelectedMilestone] = useState<Milestone | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [draggedMilestone, setDraggedMilestone] = useState<string | null>(null);
  const [exportAnchorEl, setExportAnchorEl] = useState<null | HTMLElement>(null);
  const timelineRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadRoadmap();
  }, []);

  const loadRoadmap = async () => {
    try {
      const response = await axios.get('http://localhost:5001/api/roadmap/sample');
      if (response.data && response.data.data) {
        setRoadmap(response.data.data);
      } else {
        throw new Error('Invalid response data');
      }
    } catch (error) {
      console.error('Failed to load roadmap:', error);
      setRoadmap(generateSampleRoadmap());
    } finally {
      setLoading(false);
    }
  };

  const generateSampleRoadmap = (): TransformationRoadmap => {
    return {
      id: 'roadmap-1',
      title: 'Enterprise 12-Factor Transformation',
      description: 'Complete transformation to cloud-native 12-factor application architecture',
      totalBudget: 850000,
      totalDuration: '18 months',
      phases: [
        {
          id: 'phase-1',
          name: 'Foundation & Assessment',
          description: 'Initial codebase analysis and infrastructure setup',
          startDate: '2024-01-01',
          endDate: '2024-03-31',
          color: '#2196F3',
          totalBudget: 180000,
          teamAllocation: { developers: 4, architects: 2, devops: 2, qa: 2 },
          milestones: [
            {
              id: 'ms-1',
              title: 'Codebase Analysis',
              description: 'Complete assessment of current application architecture',
              startDate: '2024-01-01',
              endDate: '2024-01-31',
              status: 'completed' as const,
              dependencies: [],
              phaseId: 'phase-1',
              resources: { teamSize: 3, budget: 45000, technologies: ['Static Analysis', 'Architecture Review'] },
              deliverables: ['Architecture Assessment Report', 'Technology Audit']
            },
            {
              id: 'ms-2',
              title: 'CI/CD Pipeline Setup',
              description: 'Implement continuous integration and deployment',
              startDate: '2024-02-01',
              endDate: '2024-03-15',
              status: 'in_progress' as const,
              dependencies: ['ms-1'],
              phaseId: 'phase-1',
              resources: { teamSize: 4, budget: 75000, technologies: ['Jenkins', 'Docker', 'Kubernetes'] },
              deliverables: ['CI/CD Pipeline', 'Automated Testing Framework']
            }
          ]
        },
        {
          id: 'phase-2',
          name: 'Core Transformation',
          description: 'Implementation of 12-factor principles',
          startDate: '2024-04-01',
          endDate: '2024-10-31',
          color: '#4CAF50',
          totalBudget: 420000,
          teamAllocation: { developers: 8, architects: 3, devops: 4, qa: 4 },
          milestones: [
            {
              id: 'ms-3',
              title: 'Configuration Externalization',
              description: 'Move all configuration to environment variables',
              startDate: '2024-04-01',
              endDate: '2024-05-15',
              status: 'not_started' as const,
              dependencies: ['ms-2'],
              phaseId: 'phase-2',
              resources: { teamSize: 5, budget: 95000, technologies: ['ConfigMaps', 'Secrets', 'Vault'] },
              deliverables: ['Configuration Management System', 'Security Policies']
            },
            {
              id: 'ms-4',
              title: 'Stateless Services',
              description: 'Refactor services to be completely stateless',
              startDate: '2024-05-16',
              endDate: '2024-07-31',
              status: 'not_started' as const,
              dependencies: ['ms-3'],
              phaseId: 'phase-2',
              resources: { teamSize: 8, budget: 180000, technologies: ['Redis', 'PostgreSQL', 'Microservices'] },
              deliverables: ['Stateless Application Architecture', 'Data Migration Scripts']
            }
          ]
        },
        {
          id: 'phase-3',
          name: 'Production Deployment',
          description: 'Full production deployment and optimization',
          startDate: '2024-11-01',
          endDate: '2024-12-31',
          color: '#FF9800',
          totalBudget: 250000,
          teamAllocation: { developers: 6, architects: 2, devops: 6, qa: 3 },
          milestones: [
            {
              id: 'ms-5',
              title: 'Production Launch',
              description: 'Deploy to production environment',
              startDate: '2024-11-01',
              endDate: '2024-11-30',
              status: 'not_started' as const,
              dependencies: ['ms-4'],
              phaseId: 'phase-3',
              resources: { teamSize: 10, budget: 150000, technologies: ['AWS', 'Monitoring', 'Load Balancing'] },
              deliverables: ['Production Environment', 'Monitoring Dashboard']
            }
          ]
        }
      ]
    };
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle sx={{ color: '#4CAF50' }} />;
      case 'in_progress':
        return <PlayArrow sx={{ color: '#FF9800' }} />;
      default:
        return <Schedule sx={{ color: '#9E9E9E' }} />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return '#4CAF50';
      case 'in_progress':
        return '#FF9800';
      default:
        return '#9E9E9E';
    }
  };

  const handleDragStart = (milestoneId: string) => {
    setDraggedMilestone(milestoneId);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent, targetPhaseId: string) => {
    e.preventDefault();
    if (!draggedMilestone || !roadmap) return;

    const updatedPhases = roadmap.phases.map(phase => {
      if (phase.id === targetPhaseId) {
        const draggedMs = roadmap.phases
          .flatMap(p => p.milestones)
          .find(m => m.id === draggedMilestone);

        if (draggedMs && draggedMs.phaseId !== targetPhaseId) {
          return {
            ...phase,
            milestones: [...phase.milestones, { ...draggedMs, phaseId: targetPhaseId }]
          };
        }
      }
      return {
        ...phase,
        milestones: phase.milestones.filter(m => m.id !== draggedMilestone)
      };
    });

    setRoadmap({ ...roadmap, phases: updatedPhases });
    setDraggedMilestone(null);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const exportRoadmap = (format: 'json' | 'csv' | 'pdf' | 'xlsx' = 'json') => {
    if (!roadmap) return;

    const timestamp = new Date().toISOString().split('T')[0];

    if (format === 'json') {
      const dataStr = JSON.stringify(roadmap, null, 2);
      const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
      const linkElement = document.createElement('a');
      linkElement.setAttribute('href', dataUri);
      linkElement.setAttribute('download', `transformation-roadmap-${timestamp}.json`);
      linkElement.click();
    } else if (format === 'csv') {
      // Export as CSV with milestone details
      const csvRows: (string | number)[][] = [];
      csvRows.push(['Phase', 'Milestone', 'Start Date', 'End Date', 'Status', 'Team Size', 'Budget', 'Technologies', 'Deliverables']);

      roadmap.phases.forEach(phase => {
        (phase.milestones || []).forEach(milestone => {
          csvRows.push([
            phase.name,
            milestone.title,
            milestone.startDate,
            milestone.endDate,
            milestone.status,
            milestone.resources?.teamSize || 0,
            milestone.resources?.budget || 0,
            (milestone.resources?.technologies || []).join('; '),
            (milestone.deliverables || []).join('; ')
          ]);
        });
      });

      const csvContent = csvRows.map(row =>
        row.map(cell => `"${cell}"`).join(',')
      ).join('\n');

      const dataUri = 'data:text/csv;charset=utf-8,\uFEFF' + encodeURIComponent(csvContent);
      const linkElement = document.createElement('a');
      linkElement.setAttribute('href', dataUri);
      linkElement.setAttribute('download', `transformation-roadmap-${timestamp}.csv`);
      linkElement.click();
    } else if (format === 'pdf') {
      // Generate comprehensive PDF report
      generatePDFReport();
    } else if (format === 'xlsx') {
      // Generate Excel workbook with multiple sheets
      generateExcelWorkbook();
    }
  };

  const generatePDFReport = () => {
    if (!roadmap) return;

    // Create comprehensive PDF report
    window.print(); // Simple print for now - could be enhanced with jsPDF
  };

  const generateExcelWorkbook = () => {
    if (!roadmap) return;

    // Create Excel-compatible tab-separated format
    const sheets = [];

    // Overview Sheet
    const overviewData = [
      ['Transformation Roadmap Overview'],
      [''],
      ['Title:', roadmap.title],
      ['Description:', roadmap.description],
      ['Total Budget:', formatCurrency(roadmap.totalBudget)],
      ['Duration:', roadmap.totalDuration],
      ['Total Phases:', roadmap.phases.length],
      ['Total Milestones:', roadmap.phases.reduce((acc, phase) => acc + (phase.milestones || []).length, 0)],
      ['']
    ];

    // Phases Sheet
    const phasesData = [
      ['Phase', 'Description', 'Start Date', 'End Date', 'Budget', 'Team Size', 'Milestones Count'],
      ...roadmap.phases.map(phase => [
        phase.name,
        phase.description,
        phase.startDate,
        phase.endDate,
        formatCurrency(phase.totalBudget),
        phase.teamAllocation ? Object.values(phase.teamAllocation).reduce((a, b) => a + b, 0) : 0,
(phase.milestones || []).length
      ])
    ];

    // Combine all sheets
    const workbookContent = [
      '=== OVERVIEW ===',
      ...overviewData.map(row => row.join('\t')),
      '',
      '=== PHASES ===',
      ...phasesData.map(row => row.join('\t'))
    ].join('\n');

    const dataUri = 'data:text/tab-separated-values;charset=utf-8,\uFEFF' + encodeURIComponent(workbookContent);
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', `transformation-roadmap-${new Date().toISOString().split('T')[0]}.xlsx`);
    linkElement.click();
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <LinearProgress />
        <Typography variant="h6" sx={{ mt: 2, textAlign: 'center' }}>
          Loading transformation roadmap...
        </Typography>
      </Container>
    );
  }

  if (!roadmap) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Typography variant="h6" color="error" sx={{ textAlign: 'center' }}>
          Failed to load roadmap data
        </Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          {roadmap.title}
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<GetApp />}
            endIcon={<ArrowDropDown />}
            onClick={(e) => setExportAnchorEl(e.currentTarget)}
          >
            Export Roadmap
          </Button>
          <Menu
            anchorEl={exportAnchorEl}
            open={Boolean(exportAnchorEl)}
            onClose={() => setExportAnchorEl(null)}
            anchorOrigin={{
              vertical: 'bottom',
              horizontal: 'left',
            }}
          >
            <MenuItem onClick={() => { exportRoadmap('json'); setExportAnchorEl(null); }}>
              <ListItemIcon>
                <DataObject fontSize="small" />
              </ListItemIcon>
              <ListItemText primary="JSON Format" secondary="Complete data structure" />
            </MenuItem>
            <MenuItem onClick={() => { exportRoadmap('csv'); setExportAnchorEl(null); }}>
              <ListItemIcon>
                <TableChart fontSize="small" />
              </ListItemIcon>
              <ListItemText primary="CSV Format" secondary="Spreadsheet compatible" />
            </MenuItem>
            <MenuItem onClick={() => { exportRoadmap('xlsx'); setExportAnchorEl(null); }}>
              <ListItemIcon>
                <Description fontSize="small" />
              </ListItemIcon>
              <ListItemText primary="Excel Format" secondary="Multi-sheet workbook" />
            </MenuItem>
            <MenuItem onClick={() => { exportRoadmap('pdf'); setExportAnchorEl(null); }}>
              <ListItemIcon>
                <PictureAsPdf fontSize="small" />
              </ListItemIcon>
              <ListItemText primary="PDF Report" secondary="Executive summary" />
            </MenuItem>
          </Menu>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => setEditDialogOpen(true)}
          >
            Add Milestone
          </Button>
        </Box>
      </Box>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <AttachMoney sx={{ mr: 1, verticalAlign: 'middle' }} />
                Total Budget
              </Typography>
              <Typography variant="h4" color="primary">
                {formatCurrency(roadmap.totalBudget)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <Schedule sx={{ mr: 1, verticalAlign: 'middle' }} />
                Duration
              </Typography>
              <Typography variant="h4" color="primary">
                {roadmap.totalDuration}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <Group sx={{ mr: 1, verticalAlign: 'middle' }} />
                Total Phases
              </Typography>
              <Typography variant="h4" color="primary">
                {roadmap.phases.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
          Transformation Timeline
        </Typography>

        <Grid container spacing={4}>
          {roadmap.phases.map((phase) => (
            <Grid item xs={12} lg={4} key={phase.id}>
              <Card
                sx={{
                  border: `2px solid ${phase.color}`,
                  minHeight: '600px',
                }}
                onDragOver={handleDragOver}
                onDrop={(e) => handleDrop(e, phase.id)}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Box
                      sx={{
                        width: 16,
                        height: 16,
                        borderRadius: '50%',
                        backgroundColor: phase.color,
                        mr: 2,
                      }}
                    />
                    <Typography variant="h6">{phase.name}</Typography>
                  </Box>

                  <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                    {phase.description}
                  </Typography>

                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                    <Typography variant="body2">
                      <strong>Budget:</strong> {formatCurrency(phase.totalBudget)}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Team:</strong> {phase.teamAllocation ? Object.values(phase.teamAllocation).reduce((a, b) => a + b, 0) : 0}
                    </Typography>
                  </Box>

                  <Box sx={{ mb: 3 }}>
                    <Typography variant="body2" sx={{ mb: 1 }}>
                      <strong>Team Allocation:</strong>
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      <Chip size="small" label={`Dev: ${phase.teamAllocation.developers}`} />
                      <Chip size="small" label={`Arch: ${phase.teamAllocation.architects}`} />
                      <Chip size="small" label={`DevOps: ${phase.teamAllocation.devops}`} />
                      <Chip size="small" label={`QA: ${phase.teamAllocation.qa}`} />
                    </Box>
                  </Box>

                  <Typography variant="h6" sx={{ mb: 2 }}>
                    Milestones
                  </Typography>

                  <Box sx={{ pl: 2 }}>
                    {(phase.milestones || []).map((milestone, index) => (
                      <Box key={milestone.id} sx={{ mb: 3, position: 'relative' }}>
                        <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 1 }}>
                          <Box sx={{ mr: 2, mt: 0.5 }}>
                            <Box
                              sx={{
                                width: 12,
                                height: 12,
                                borderRadius: '50%',
                                backgroundColor: getStatusColor(milestone.status),
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                              }}
                            >
                              {milestone.status === 'completed' && (
                                <CheckCircle sx={{ width: 8, height: 8, color: 'white' }} />
                              )}
                            </Box>
                            {index < phase.milestones.length - 1 && (
                              <Box
                                sx={{
                                  width: 2,
                                  height: 40,
                                  backgroundColor: '#e0e0e0',
                                  ml: 1,
                                  mt: 1,
                                }}
                              />
                            )}
                          </Box>
                          <Box sx={{ flex: 1 }}>
                            <Typography variant="caption" color="textSecondary">
                              {new Date(milestone.startDate).toLocaleDateString()}
                            </Typography>
                            <Card
                              sx={{
                                cursor: 'grab',
                                '&:hover': {
                                  boxShadow: 3,
                                },
                              }}
                              draggable
                              onDragStart={() => handleDragStart(milestone.id)}
                              onClick={() => setSelectedMilestone(milestone)}
                            >
                              <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                  <DragIndicator sx={{ mr: 1, color: 'text.secondary' }} />
                                  <Typography variant="subtitle2">
                                    {milestone.title}
                                  </Typography>
                                </Box>
                                <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                                  {milestone.description}
                                </Typography>
                                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                  <Typography variant="caption">
                                    Team: {milestone.resources?.teamSize || 0}
                                  </Typography>
                                  <Typography variant="caption">
                                    {formatCurrency(milestone.resources?.budget || 0)}
                                  </Typography>
                                </Box>
                                <Box sx={{ mt: 1 }}>
                                  {(milestone.resources?.technologies || []).slice(0, 2).map((tech) => (
                                    <Chip
                                      key={tech}
                                      size="small"
                                      label={tech}
                                      sx={{ mr: 0.5, fontSize: '0.7rem', height: '20px' }}
                                    />
                                  ))}
                                  {(milestone.resources?.technologies || []).length > 2 && (
                                    <Chip
                                      size="small"
                                      label={`+${(milestone.resources?.technologies || []).length - 2}`}
                                      sx={{ fontSize: '0.7rem', height: '20px' }}
                                    />
                                  )}
                                </Box>
                              </CardContent>
                            </Card>
                          </Box>
                        </Box>
                      </Box>
                    ))}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Paper>

      {/* Resource Planning Section */}
      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12}>
          <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
            Resource Planning & Allocation
          </Typography>
        </Grid>

        {/* Overall Resource Summary */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              <Group sx={{ mr: 1, verticalAlign: 'middle' }} />
              Overall Team Allocation
            </Typography>

            <Box sx={{ mt: 3 }}>
              {roadmap.phases.map((phase, index) => {
                const totalTeam = phase.teamAllocation ? Object.values(phase.teamAllocation).reduce((a, b) => a + b, 0) : 0;
                const maxTeam = Math.max(...roadmap.phases.map(p => p.teamAllocation ? Object.values(p.teamAllocation).reduce((a, b) => a + b, 0) : 0));

                return (
                  <Box key={phase.id} sx={{ mb: 3 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2" fontWeight="medium">
                        {phase.name}
                      </Typography>
                      <Typography variant="body2">
                        {totalTeam} people
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={(totalTeam / maxTeam) * 100}
                      sx={{
                        height: 8,
                        borderRadius: 4,
                        backgroundColor: '#e0e0e0',
                        '& .MuiLinearProgress-bar': {
                          backgroundColor: phase.color,
                        },
                      }}
                    />

                    <Box sx={{ display: 'flex', gap: 1, mt: 1, flexWrap: 'wrap' }}>
                      <Chip
                        size="small"
                        icon={<Engineering />}
                        label={`${phase.teamAllocation?.developers || 0} Dev`}
                        sx={{ fontSize: '0.7rem' }}
                      />
                      <Chip
                        size="small"
                        icon={<Business />}
                        label={`${phase.teamAllocation?.architects || 0} Arch`}
                        sx={{ fontSize: '0.7rem' }}
                      />
                      <Chip
                        size="small"
                        icon={<Build />}
                        label={`${phase.teamAllocation?.devops || 0} DevOps`}
                        sx={{ fontSize: '0.7rem' }}
                      />
                      <Chip
                        size="small"
                        icon={<BugReport />}
                        label={`${phase.teamAllocation?.qa || 0} QA`}
                        sx={{ fontSize: '0.7rem' }}
                      />
                    </Box>
                  </Box>
                );
              })}
            </Box>
          </Paper>
        </Grid>

        {/* Budget Breakdown */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              <AttachMoney sx={{ mr: 1, verticalAlign: 'middle' }} />
              Budget Distribution
            </Typography>

            <Box sx={{ mt: 3 }}>
              {roadmap.phases.map((phase, index) => {
                const budgetPercentage = (phase.totalBudget / roadmap.totalBudget) * 100;

                return (
                  <Box key={phase.id} sx={{ mb: 3 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2" fontWeight="medium">
                        {phase.name}
                      </Typography>
                      <Typography variant="body2">
                        {formatCurrency(phase.totalBudget)} ({budgetPercentage.toFixed(1)}%)
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={budgetPercentage}
                      sx={{
                        height: 8,
                        borderRadius: 4,
                        backgroundColor: '#e0e0e0',
                        '& .MuiLinearProgress-bar': {
                          backgroundColor: phase.color,
                        },
                      }}
                    />

                    <Typography variant="caption" color="textSecondary" sx={{ mt: 0.5, display: 'block' }}>
                      Average per milestone: {formatCurrency(phase.totalBudget / ((phase.milestones || []).length || 1))}
                    </Typography>
                  </Box>
                );
              })}
            </Box>

            <Box sx={{ mt: 3, p: 2, bgcolor: 'primary.main', color: 'primary.contrastText', borderRadius: 2 }}>
              <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center' }}>
                <TrendingUp sx={{ mr: 1 }} />
                Total Investment: {formatCurrency(roadmap.totalBudget)}
              </Typography>
            </Box>
          </Paper>
        </Grid>

        {/* Resource Timeline Chart */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              <Assignment sx={{ mr: 1, verticalAlign: 'middle' }} />
              Resource Timeline & Skills Required
            </Typography>

            <Box sx={{ overflowX: 'auto', mt: 3 }}>
              <Box sx={{ minWidth: 800 }}>
                {roadmap.phases.map((phase, phaseIndex) => (
                  <Box key={phase.id} sx={{ mb: 4 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <Box
                        sx={{
                          width: 12,
                          height: 12,
                          borderRadius: '50%',
                          backgroundColor: phase.color,
                          mr: 2,
                        }}
                      />
                      <Typography variant="subtitle1" fontWeight="medium">
                        {phase.name}
                      </Typography>
                      <Typography variant="body2" color="textSecondary" sx={{ ml: 2 }}>
                        ({new Date(phase.startDate).toLocaleDateString()} - {new Date(phase.endDate).toLocaleDateString()})
                      </Typography>
                    </Box>

                    <Grid container spacing={2}>
                      {(phase.milestones || []).map((milestone) => (
                        <Grid item xs={12} sm={6} lg={4} key={milestone.id}>
                          <Card
                            sx={{
                              border: `1px solid ${phase.color}`,
                              position: 'relative',
                              '&:hover': {
                                boxShadow: 3,
                              },
                            }}
                          >
                            <CardContent sx={{ p: 2 }}>
                              <Typography variant="subtitle2" gutterBottom>
                                {milestone.title}
                              </Typography>

                              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                                <Typography variant="body2" color="textSecondary">
                                  Team: {milestone.resources?.teamSize || 0}
                                </Typography>
                                <Typography variant="body2" color="textSecondary">
                                  {formatCurrency(milestone.resources?.budget || 0)}
                                </Typography>
                              </Box>

                              <Box sx={{ mb: 2 }}>
                                <Typography variant="caption" color="textSecondary" gutterBottom>
                                  Skills Required:
                                </Typography>
                                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                                  {(milestone.resources?.technologies || []).map((tech) => (
                                    <Chip
                                      key={tech}
                                      size="small"
                                      label={tech}
                                      sx={{ fontSize: '0.65rem', height: '18px' }}
                                    />
                                  ))}
                                </Box>
                              </Box>

                              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <Typography variant="caption" color="textSecondary">
                                  Duration: {Math.ceil((new Date(milestone.endDate).getTime() - new Date(milestone.startDate).getTime()) / (1000 * 3600 * 24 * 7))} weeks
                                </Typography>
                                <Box
                                  sx={{
                                    width: 8,
                                    height: 8,
                                    borderRadius: '50%',
                                    backgroundColor: getStatusColor(milestone.status),
                                  }}
                                />
                              </Box>
                            </CardContent>
                          </Card>
                        </Grid>
                      ))}
                    </Grid>
                  </Box>
                ))}
              </Box>
            </Box>
          </Paper>
        </Grid>

        {/* Resource Utilization Matrix */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Resource Utilization Matrix
            </Typography>

            <Box sx={{ overflowX: 'auto', mt: 3 }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr>
                    <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #e0e0e0' }}>
                      Phase
                    </th>
                    <th style={{ padding: '12px', textAlign: 'center', borderBottom: '2px solid #e0e0e0' }}>
                      Developers
                    </th>
                    <th style={{ padding: '12px', textAlign: 'center', borderBottom: '2px solid #e0e0e0' }}>
                      Architects
                    </th>
                    <th style={{ padding: '12px', textAlign: 'center', borderBottom: '2px solid #e0e0e0' }}>
                      DevOps
                    </th>
                    <th style={{ padding: '12px', textAlign: 'center', borderBottom: '2px solid #e0e0e0' }}>
                      QA
                    </th>
                    <th style={{ padding: '12px', textAlign: 'center', borderBottom: '2px solid #e0e0e0' }}>
                      Total
                    </th>
                    <th style={{ padding: '12px', textAlign: 'center', borderBottom: '2px solid #e0e0e0' }}>
                      Budget
                    </th>
                    <th style={{ padding: '12px', textAlign: 'center', borderBottom: '2px solid #e0e0e0' }}>
                      Duration
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {roadmap.phases.map((phase) => {
                    const totalTeam = phase.teamAllocation ? Object.values(phase.teamAllocation).reduce((a, b) => a + b, 0) : 0;
                    const duration = Math.ceil((new Date(phase.endDate).getTime() - new Date(phase.startDate).getTime()) / (1000 * 3600 * 24));

                    return (
                      <tr key={phase.id}>
                        <td style={{ padding: '12px', borderBottom: '1px solid #e0e0e0' }}>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Box
                              sx={{
                                width: 8,
                                height: 8,
                                borderRadius: '50%',
                                backgroundColor: phase.color,
                                mr: 1,
                              }}
                            />
                            {phase.name}
                          </Box>
                        </td>
                        <td style={{ padding: '12px', textAlign: 'center', borderBottom: '1px solid #e0e0e0' }}>
                          {phase.teamAllocation?.developers || 0}
                        </td>
                        <td style={{ padding: '12px', textAlign: 'center', borderBottom: '1px solid #e0e0e0' }}>
                          {phase.teamAllocation?.architects || 0}
                        </td>
                        <td style={{ padding: '12px', textAlign: 'center', borderBottom: '1px solid #e0e0e0' }}>
                          {phase.teamAllocation?.devops || 0}
                        </td>
                        <td style={{ padding: '12px', textAlign: 'center', borderBottom: '1px solid #e0e0e0' }}>
                          {phase.teamAllocation?.qa || 0}
                        </td>
                        <td style={{ padding: '12px', textAlign: 'center', borderBottom: '1px solid #e0e0e0', fontWeight: 'medium' }}>
                          {totalTeam}
                        </td>
                        <td style={{ padding: '12px', textAlign: 'center', borderBottom: '1px solid #e0e0e0', fontWeight: 'medium' }}>
                          {formatCurrency(phase.totalBudget)}
                        </td>
                        <td style={{ padding: '12px', textAlign: 'center', borderBottom: '1px solid #e0e0e0' }}>
                          {duration} days
                        </td>
                      </tr>
                    );
                  })}

                  {/* Totals Row */}
                  <tr style={{ backgroundColor: '#f5f5f5', fontWeight: 'bold' }}>
                    <td style={{ padding: '12px', borderTop: '2px solid #e0e0e0' }}>
                      <strong>TOTALS</strong>
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center', borderTop: '2px solid #e0e0e0' }}>
                      {roadmap.phases.reduce((sum, phase) => sum + (phase.teamAllocation?.developers || 0), 0)}
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center', borderTop: '2px solid #e0e0e0' }}>
                      {roadmap.phases.reduce((sum, phase) => sum + (phase.teamAllocation?.architects || 0), 0)}
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center', borderTop: '2px solid #e0e0e0' }}>
                      {roadmap.phases.reduce((sum, phase) => sum + (phase.teamAllocation?.devops || 0), 0)}
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center', borderTop: '2px solid #e0e0e0' }}>
                      {roadmap.phases.reduce((sum, phase) => sum + (phase.teamAllocation?.qa || 0), 0)}
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center', borderTop: '2px solid #e0e0e0' }}>
                      {roadmap.phases.reduce((sum, phase) => sum + (phase.teamAllocation ? Object.values(phase.teamAllocation).reduce((a, b) => a + b, 0) : 0), 0)}
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center', borderTop: '2px solid #e0e0e0' }}>
                      {formatCurrency(roadmap.totalBudget)}
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center', borderTop: '2px solid #e0e0e0' }}>
                      {roadmap.totalDuration}
                    </td>
                  </tr>
                </tbody>
              </table>
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Milestone Details Dialog */}
      <Dialog
        open={Boolean(selectedMilestone)}
        onClose={() => setSelectedMilestone(null)}
        maxWidth="md"
        fullWidth
      >
        {selectedMilestone && (
          <>
            <DialogTitle>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Typography variant="h6">{selectedMilestone.title}</Typography>
                <Chip
                  label={selectedMilestone.status.replace('_', ' ')}
                  color={selectedMilestone.status === 'completed' ? 'success' :
                         selectedMilestone.status === 'in_progress' ? 'warning' : 'default'}
                />
              </Box>
            </DialogTitle>
            <DialogContent>
              <Typography variant="body1" sx={{ mb: 2 }}>
                {selectedMilestone.description}
              </Typography>

              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>Timeline</Typography>
                  <Typography variant="body2">
                    Start: {new Date(selectedMilestone.startDate).toLocaleDateString()}
                  </Typography>
                  <Typography variant="body2">
                    End: {new Date(selectedMilestone.endDate).toLocaleDateString()}
                  </Typography>
                </Grid>

                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>Resources</Typography>
                  <Typography variant="body2">
                    Team Size: {selectedMilestone.resources?.teamSize || 0}
                  </Typography>
                  <Typography variant="body2">
                    Budget: {formatCurrency(selectedMilestone.resources?.budget || 0)}
                  </Typography>
                </Grid>

                <Grid item xs={12}>
                  <Typography variant="subtitle2" gutterBottom>Technologies</Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {(selectedMilestone.resources?.technologies || []).map((tech) => (
                      <Chip key={tech} label={tech} size="small" />
                    ))}
                  </Box>
                </Grid>

                <Grid item xs={12}>
                  <Typography variant="subtitle2" gutterBottom>Deliverables</Typography>
                  {(selectedMilestone.deliverables || []).map((deliverable, index) => (
                    <Typography key={index} variant="body2" sx={{ ml: 2 }}>
                      • {deliverable}
                    </Typography>
                  ))}
                </Grid>
              </Grid>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setSelectedMilestone(null)}>
                Close
              </Button>
              <Button variant="contained" startIcon={<Edit />}>
                Edit Milestone
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Container>
  );
};

export default RoadmapBuilder;