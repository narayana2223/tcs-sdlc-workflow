/**
 * Prototype Viewer
 * Interactive viewer for transformation prototypes with code examples and architecture diagrams
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  Button,
  IconButton,
  Tabs,
  Tab,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert,
  LinearProgress,
  Tooltip,
  Badge,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material';
import {
  Code as CodeIcon,
  Architecture as ArchitectureIcon,
  PlayArrow as PlayArrowIcon,
  CompareArrows as CompareIcon,
  Timeline as TimelineIcon,
  Assessment as TestIcon,
  Speed as PerformanceIcon,
  ExpandMore as ExpandMoreIcon,
  Lightbulb as BulbIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Category as CategoryIcon,
  Functions as FactorIcon,
  Close as CloseIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { parseDiff, Diff, Hunk } from 'react-diff-view';

interface CodeExample {
  id: string;
  title: string;
  description: string;
  language: string;
  beforeCode: string;
  afterCode: string;
  explanation: string;
  benefits: string[];
  complexity: 'low' | 'medium' | 'high';
  estimatedTime: string;
}

interface ArchitectureDiagram {
  id: string;
  title: string;
  type: 'before' | 'after' | 'comparison';
  description: string;
  components: {
    id: string;
    name: string;
    type: string;
    position: { x: number; y: number };
    connections: string[];
  }[];
  improvements: string[];
}

interface ImplementationStep {
  id: string;
  title: string;
  description: string;
  codeChanges?: string;
  configChanges?: string;
  testingNotes?: string;
  estimatedTime: string;
  prerequisites: string[];
}

interface TransformationPrototype {
  id: string;
  title: string;
  description: string;
  category: 'microservices' | 'containerization' | 'configuration' | 'logging' | 'scaling' | 'security';
  factor: string;
  codeExamples: CodeExample[];
  architectureDiagrams: ArchitectureDiagram[];
  implementationSteps: ImplementationStep[];
  performanceMetrics: {
    before: { [key: string]: number | string };
    after: { [key: string]: number | string };
    improvement: string;
  };
  testCases: {
    id: string;
    name: string;
    input: any;
    expectedOutput: any;
    testCode: string;
  }[];
}

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

const PrototypeViewer: React.FC = () => {
  const [prototypes, setPrototypes] = useState<TransformationPrototype[]>([]);
  const [selectedPrototype, setSelectedPrototype] = useState<TransformationPrototype | null>(null);
  const [loading, setLoading] = useState(true);
  const [tabValue, setTabValue] = useState(0);
  const [selectedCodeExample, setSelectedCodeExample] = useState<CodeExample | null>(null);
  const [codeViewMode, setCodeViewMode] = useState<'before' | 'after' | 'diff'>('before');
  const [playgroundOpen, setPlaygroundOpen] = useState(false);
  const [playgroundCode, setPlaygroundCode] = useState('');

  useEffect(() => {
    loadPrototypes();
  }, []);

  const loadPrototypes = async () => {
    try {
      const response = await fetch('http://localhost:5001/api/prototypes');
      const data = await response.json();

      if (data.success) {
        setPrototypes(data.data.prototypes);
        if (data.data.prototypes.length > 0) {
          setSelectedPrototype(data.data.prototypes[0]);
        }
      }
    } catch (error) {
      console.error('Failed to load prototypes:', error);
    } finally {
      setLoading(false);
    }
  };

  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'low': return 'success';
      case 'medium': return 'warning';
      case 'high': return 'error';
      default: return 'primary';
    }
  };

  const getCategoryIcon = (category: string) => {
    const icons: { [key: string]: React.ReactElement } = {
      microservices: <ArchitectureIcon />,
      containerization: <CategoryIcon />,
      configuration: <CodeIcon />,
      logging: <TimelineIcon />,
      scaling: <PerformanceIcon />,
      security: <CheckIcon />
    };
    return icons[category] || <CodeIcon />;
  };

  const generateDiffString = (beforeCode: string, afterCode: string): string => {
    const beforeLines = beforeCode.split('\n');
    const afterLines = afterCode.split('\n');

    let diffString = '--- before.js\n+++ after.js\n@@ -1,' + beforeLines.length + ' +1,' + afterLines.length + ' @@\n';

    const maxLines = Math.max(beforeLines.length, afterLines.length);
    for (let i = 0; i < maxLines; i++) {
      const beforeLine = beforeLines[i] || '';
      const afterLine = afterLines[i] || '';

      if (beforeLine !== afterLine) {
        if (beforeLines[i] !== undefined) {
          diffString += '-' + beforeLine + '\n';
        }
        if (afterLines[i] !== undefined) {
          diffString += '+' + afterLine + '\n';
        }
      } else {
        diffString += ' ' + beforeLine + '\n';
      }
    }

    return diffString;
  };

  const renderCodeViewer = (codeExample: CodeExample) => {
    if (codeViewMode === 'diff') {
      const diffText = generateDiffString(codeExample.beforeCode, codeExample.afterCode);

      try {
        const files = parseDiff(diffText);
        return (
          <Box sx={{ border: 1, borderColor: 'divider', borderRadius: 1 }}>
            {files.map((file, index) => (
              <Diff key={index} viewType="unified" diffType={file.type} hunks={file.hunks}>
                {(hunks) => hunks.map((hunk) => <Hunk key={hunk.content} hunk={hunk} />)}
              </Diff>
            ))}
          </Box>
        );
      } catch (error) {
        // Fallback to side-by-side view if diff parsing fails
        return (
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Typography variant="subtitle2" gutterBottom color="error">Before</Typography>
              <SyntaxHighlighter
                language={codeExample.language}
                style={tomorrow}
                customStyle={{ fontSize: '12px', maxHeight: '400px' }}
              >
                {codeExample.beforeCode}
              </SyntaxHighlighter>
            </Grid>
            <Grid item xs={6}>
              <Typography variant="subtitle2" gutterBottom color="success.main">After</Typography>
              <SyntaxHighlighter
                language={codeExample.language}
                style={tomorrow}
                customStyle={{ fontSize: '12px', maxHeight: '400px' }}
              >
                {codeExample.afterCode}
              </SyntaxHighlighter>
            </Grid>
          </Grid>
        );
      }
    }

    const code = codeViewMode === 'before' ? codeExample.beforeCode : codeExample.afterCode;
    const color = codeViewMode === 'before' ? 'error' : 'success.main';
    const title = codeViewMode === 'before' ? 'Before Transformation' : 'After Transformation';

    return (
      <Box>
        <Typography variant="subtitle2" gutterBottom sx={{ color }}>
          {title}
        </Typography>
        <SyntaxHighlighter
          language={codeExample.language}
          style={tomorrow}
          customStyle={{ fontSize: '12px', maxHeight: '500px' }}
        >
          {code}
        </SyntaxHighlighter>
      </Box>
    );
  };

  const renderArchitectureDiagram = (diagram: ArchitectureDiagram) => {
    return (
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            {diagram.title}
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            {diagram.description}
          </Typography>

          {/* Simple architecture diagram representation */}
          <Box
            sx={{
              position: 'relative',
              height: 300,
              border: 1,
              borderColor: 'divider',
              borderRadius: 1,
              p: 2,
              bgcolor: 'grey.50'
            }}
          >
            {diagram.components.map((component) => (
              <Box
                key={component.id}
                sx={{
                  position: 'absolute',
                  left: component.position.x,
                  top: component.position.y,
                  minWidth: 100,
                  p: 1,
                  bgcolor: component.type === 'database' ? 'info.light' :
                           component.type === 'service' ? 'success.light' :
                           component.type === 'config' ? 'warning.light' : 'primary.light',
                  borderRadius: 1,
                  textAlign: 'center',
                  fontSize: '12px',
                  color: 'white',
                  fontWeight: 'bold'
                }}
              >
                {component.name}
              </Box>
            ))}
          </Box>

          {diagram.improvements.length > 0 && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Key Improvements:
              </Typography>
              <List dense>
                {diagram.improvements.map((improvement, index) => (
                  <ListItem key={index} sx={{ py: 0.5 }}>
                    <ListItemIcon sx={{ minWidth: 30 }}>
                      <CheckIcon color="success" fontSize="small" />
                    </ListItemIcon>
                    <ListItemText primary={improvement} />
                  </ListItem>
                ))}
              </List>
            </Box>
          )}
        </CardContent>
      </Card>
    );
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <LinearProgress />
        <Typography variant="h6" sx={{ mt: 2, textAlign: 'center' }}>
          Loading transformation prototypes...
        </Typography>
      </Container>
    );
  }

  if (!selectedPrototype) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="info">
          No prototypes available. Please check your backend connection.
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Transformation Prototypes
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Interactive examples and implementation guides
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={loadPrototypes}
        >
          Refresh
        </Button>
      </Box>

      <Grid container spacing={3}>
        {/* Prototype List */}
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 2, maxHeight: 600, overflow: 'auto' }}>
            <Typography variant="h6" gutterBottom>
              Available Prototypes
            </Typography>
            <List>
              {prototypes.map((prototype) => (
                <ListItem
                  key={prototype.id}
                  button
                  selected={selectedPrototype.id === prototype.id}
                  onClick={() => setSelectedPrototype(prototype)}
                  sx={{ borderRadius: 1, mb: 1 }}
                >
                  <ListItemIcon>
                    {getCategoryIcon(prototype.category)}
                  </ListItemIcon>
                  <ListItemText
                    primary={prototype.title}
                    secondary={
                      <Box>
                        <Typography variant="caption" display="block">
                          {prototype.category}
                        </Typography>
                        <Chip
                          label={prototype.factor}
                          size="small"
                          variant="outlined"
                          sx={{ mt: 0.5 }}
                        />
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>

        {/* Main Content */}
        <Grid item xs={12} md={9}>
          <Paper sx={{ width: '100%' }}>
            {/* Prototype Header */}
            <Box sx={{ p: 3, borderBottom: 1, borderColor: 'divider' }}>
              <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                <Typography variant="h5">{selectedPrototype.title}</Typography>
                <Box display="flex" gap={1}>
                  <Chip
                    icon={getCategoryIcon(selectedPrototype.category)}
                    label={selectedPrototype.category}
                    color="primary"
                    variant="outlined"
                  />
                  <Chip
                    icon={<FactorIcon />}
                    label={`12-Factor: ${selectedPrototype.factor}`}
                    color="secondary"
                    variant="outlined"
                  />
                </Box>
              </Box>
              <Typography variant="body1" color="text.secondary">
                {selectedPrototype.description}
              </Typography>
            </Box>

            {/* Tabs */}
            <Tabs
              value={tabValue}
              onChange={(_, newValue) => setTabValue(newValue)}
              variant="fullWidth"
              sx={{ borderBottom: 1, borderColor: 'divider' }}
            >
              <Tab icon={<CodeIcon />} label="Code Examples" />
              <Tab icon={<ArchitectureIcon />} label="Architecture" />
              <Tab icon={<TimelineIcon />} label="Implementation" />
              <Tab icon={<TestIcon />} label="Testing" />
              <Tab icon={<PerformanceIcon />} label="Metrics" />
            </Tabs>

            {/* Tab Content */}
            <TabPanel value={tabValue} index={0}>
              {/* Code Examples Tab */}
              {selectedPrototype.codeExamples.map((example, index) => (
                <Accordion key={example.id} defaultExpanded={index === 0}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Box display="flex" alignItems="center" gap={2}>
                      <Typography variant="h6">{example.title}</Typography>
                      <Chip
                        label={example.complexity}
                        color={getComplexityColor(example.complexity)}
                        size="small"
                      />
                      <Chip
                        label={example.estimatedTime}
                        variant="outlined"
                        size="small"
                      />
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Typography variant="body2" color="text.secondary" paragraph>
                      {example.description}
                    </Typography>

                    {/* Code View Controls */}
                    <Box display="flex" gap={1} mb={2}>
                      <Button
                        variant={codeViewMode === 'before' ? 'contained' : 'outlined'}
                        size="small"
                        onClick={() => setCodeViewMode('before')}
                        color="error"
                      >
                        Before
                      </Button>
                      <Button
                        variant={codeViewMode === 'after' ? 'contained' : 'outlined'}
                        size="small"
                        onClick={() => setCodeViewMode('after')}
                        color="success"
                      >
                        After
                      </Button>
                      <Button
                        variant={codeViewMode === 'diff' ? 'contained' : 'outlined'}
                        size="small"
                        onClick={() => setCodeViewMode('diff')}
                        startIcon={<CompareIcon />}
                      >
                        Compare
                      </Button>
                      <Button
                        variant="outlined"
                        size="small"
                        startIcon={<PlayArrowIcon />}
                        onClick={() => {
                          setPlaygroundCode(example.afterCode);
                          setPlaygroundOpen(true);
                        }}
                      >
                        Try in Playground
                      </Button>
                    </Box>

                    {renderCodeViewer(example)}

                    {/* Explanation and Benefits */}
                    <Box sx={{ mt: 3 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Explanation:
                      </Typography>
                      <Typography variant="body2" paragraph>
                        {example.explanation}
                      </Typography>

                      <Typography variant="subtitle2" gutterBottom>
                        Benefits:
                      </Typography>
                      <List dense>
                        {example.benefits.map((benefit, idx) => (
                          <ListItem key={idx} sx={{ py: 0.5 }}>
                            <ListItemIcon sx={{ minWidth: 30 }}>
                              <CheckIcon color="success" fontSize="small" />
                            </ListItemIcon>
                            <ListItemText primary={benefit} />
                          </ListItem>
                        ))}
                      </List>
                    </Box>
                  </AccordionDetails>
                </Accordion>
              ))}
            </TabPanel>

            <TabPanel value={tabValue} index={1}>
              {/* Architecture Tab */}
              {selectedPrototype.architectureDiagrams.map((diagram) => (
                renderArchitectureDiagram(diagram)
              ))}
            </TabPanel>

            <TabPanel value={tabValue} index={2}>
              {/* Implementation Tab */}
              <Typography variant="h6" gutterBottom>
                Implementation Steps
              </Typography>
              {selectedPrototype.implementationSteps.map((step, index) => (
                <Accordion key={step.id}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Box display="flex" alignItems="center" gap={2}>
                      <Chip label={index + 1} color="primary" size="small" />
                      <Typography variant="subtitle1">{step.title}</Typography>
                      <Chip label={step.estimatedTime} variant="outlined" size="small" />
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Typography variant="body2" paragraph>
                      {step.description}
                    </Typography>

                    {step.prerequisites.length > 0 && (
                      <Alert severity="info" sx={{ mb: 2 }}>
                        <Typography variant="subtitle2">Prerequisites:</Typography>
                        {step.prerequisites.join(', ')}
                      </Alert>
                    )}

                    {step.codeChanges && (
                      <Box>
                        <Typography variant="subtitle2" gutterBottom>
                          Code Changes:
                        </Typography>
                        <SyntaxHighlighter
                          language="bash"
                          style={tomorrow}
                          customStyle={{ fontSize: '12px' }}
                        >
                          {step.codeChanges}
                        </SyntaxHighlighter>
                      </Box>
                    )}
                  </AccordionDetails>
                </Accordion>
              ))}
            </TabPanel>

            <TabPanel value={tabValue} index={3}>
              {/* Testing Tab */}
              <Typography variant="h6" gutterBottom>
                Test Cases
              </Typography>
              {selectedPrototype.testCases.map((testCase) => (
                <Card key={testCase.id} sx={{ mb: 2 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      {testCase.name}
                    </Typography>

                    <Grid container spacing={2}>
                      <Grid item xs={6}>
                        <Typography variant="subtitle2" gutterBottom>
                          Input:
                        </Typography>
                        <SyntaxHighlighter
                          language="json"
                          style={tomorrow}
                          customStyle={{ fontSize: '12px' }}
                        >
                          {JSON.stringify(testCase.input, null, 2)}
                        </SyntaxHighlighter>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="subtitle2" gutterBottom>
                          Expected Output:
                        </Typography>
                        <SyntaxHighlighter
                          language="json"
                          style={tomorrow}
                          customStyle={{ fontSize: '12px' }}
                        >
                          {JSON.stringify(testCase.expectedOutput, null, 2)}
                        </SyntaxHighlighter>
                      </Grid>
                    </Grid>

                    <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
                      Test Code:
                    </Typography>
                    <SyntaxHighlighter
                      language="javascript"
                      style={tomorrow}
                      customStyle={{ fontSize: '12px' }}
                    >
                      {testCase.testCode}
                    </SyntaxHighlighter>
                  </CardContent>
                </Card>
              ))}
            </TabPanel>

            <TabPanel value={tabValue} index={4}>
              {/* Performance Metrics Tab */}
              <Typography variant="h6" gutterBottom>
                Performance Comparison
              </Typography>

              <TableContainer component={Paper} variant="outlined">
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Metric</TableCell>
                      <TableCell>Before</TableCell>
                      <TableCell>After</TableCell>
                      <TableCell>Improvement</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {Object.keys(selectedPrototype.performanceMetrics.before).map((key) => (
                      <TableRow key={key}>
                        <TableCell>{key}</TableCell>
                        <TableCell>
                          <Chip
                            label={selectedPrototype.performanceMetrics.before[key]}
                            color="error"
                            variant="outlined"
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={selectedPrototype.performanceMetrics.after[key]}
                            color="success"
                            variant="outlined"
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <CheckIcon color="success" />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>

              <Alert severity="success" sx={{ mt: 2 }}>
                <Typography variant="subtitle2">Overall Improvement:</Typography>
                {selectedPrototype.performanceMetrics.improvement}
              </Alert>
            </TabPanel>
          </Paper>
        </Grid>
      </Grid>

      {/* Code Playground Dialog */}
      <Dialog
        open={playgroundOpen}
        onClose={() => setPlaygroundOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h6">Code Playground</Typography>
            <IconButton onClick={() => setPlaygroundOpen(false)}>
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Edit and experiment with the transformation code:
          </Typography>
          <SyntaxHighlighter
            language="javascript"
            style={tomorrow}
            customStyle={{ fontSize: '12px', maxHeight: '400px' }}
          >
            {playgroundCode}
          </SyntaxHighlighter>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPlaygroundOpen(false)}>Close</Button>
          <Button variant="contained" startIcon={<PlayArrowIcon />}>
            Run Code
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default PrototypeViewer;