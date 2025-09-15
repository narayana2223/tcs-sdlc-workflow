/**
 * Simplified FactorCards Component - Robust version for 12-factor display
 */

import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  IconButton
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Close as CloseIcon
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
  groupBy?: string;
}

const FactorCardsSimple: React.FC<FactorCardsProps> = ({
  factors,
  onFactorClick,
  showEvidence = true
}) => {
  const [selectedFactor, setSelectedFactor] = useState<string | null>(null);

  // Safety check
  if (!factors || typeof factors !== 'object') {
    return (
      <Box p={3}>
        <Typography variant="h6" color="error">
          Invalid factors data: {JSON.stringify(factors)}
        </Typography>
      </Box>
    );
  }

  const factorEntries = Object.entries(factors);

  if (factorEntries.length === 0) {
    return (
      <Box p={3}>
        <Typography variant="h6" color="text.secondary">
          No factor evaluations available
        </Typography>
      </Box>
    );
  }

  const getScoreColor = (score: number): 'success' | 'warning' | 'error' | 'primary' => {
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

  const handleFactorClick = (factorName: string) => {
    setSelectedFactor(factorName);
    if (onFactorClick) {
      onFactorClick(factorName);
    }
  };

  const renderFactorDialog = () => {
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
              {factor.factor_name} - Detailed Analysis
            </Typography>
            <IconButton onClick={() => setSelectedFactor(null)}>
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Box mb={3}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {factor.factor_description}
            </Typography>
            <Box display="flex" alignItems="center" gap={2} mt={2}>
              {getScoreIcon(factor.score)}
              <Typography variant="h6">
                Score: {factor.score}/5 ({factor.score_name})
              </Typography>
              <Chip label={`${Math.round(factor.confidence * 100)}% confidence`} size="small" />
            </Box>
            <Typography variant="body1" mt={2}>
              {factor.score_reasoning}
            </Typography>
          </Box>

          {showEvidence && factor.evidence && factor.evidence.length > 0 && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Evidence ({factor.evidence.length} items)
              </Typography>
              <List>
                {factor.evidence.map((evidence, index) => (
                  <ListItem key={index}>
                    <Box display="flex" alignItems="flex-start" gap={1} width="100%">
                      {evidence.type === 'positive' && <CheckIcon color="success" />}
                      {evidence.type === 'negative' && <ErrorIcon color="error" />}
                      {evidence.type === 'neutral' && <InfoIcon color="info" />}
                      <Box flex={1}>
                        <ListItemText
                          primary={evidence.description}
                          secondary={
                            evidence.file_path
                              ? `${evidence.file_path}:${evidence.line_number || '?'} (${Math.round(evidence.confidence * 100)}% confidence)`
                              : `${Math.round(evidence.confidence * 100)}% confidence`
                          }
                        />
                        {evidence.code_snippet && (
                          <Box mt={1} p={1} bgcolor="grey.100" borderRadius={1}>
                            <Typography variant="body2" fontFamily="monospace">
                              {evidence.code_snippet}
                            </Typography>
                          </Box>
                        )}
                      </Box>
                    </Box>
                  </ListItem>
                ))}
              </List>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelectedFactor(null)}>Close</Button>
        </DialogActions>
      </Dialog>
    );
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        12-Factor Assessment Results ({factorEntries.length} factors)
      </Typography>

      <Grid container spacing={3}>
        {factorEntries.map(([factorName, evaluation]) => (
          <Grid item xs={12} md={6} lg={4} key={factorName}>
            <Card
              sx={{
                cursor: 'pointer',
                '&:hover': {
                  boxShadow: 3,
                  transform: 'translateY(-2px)',
                  transition: 'all 0.2s'
                }
              }}
              onClick={() => handleFactorClick(factorName)}
            >
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                  <Typography variant="h6" component="h3" sx={{ flex: 1 }}>
                    {factorName.replace(/_/g, ' ').toUpperCase()}
                  </Typography>
                  {getScoreIcon(evaluation.score)}
                </Box>

                <Typography variant="body2" color="text.secondary" mb={2} sx={{ height: 40, overflow: 'hidden' }}>
                  {evaluation.factor_description}
                </Typography>

                <Box mb={2}>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                    <Typography variant="body2">Score</Typography>
                    <Typography variant="body2" fontWeight="bold">
                      {evaluation.score}/5
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={(evaluation.score / 5) * 100}
                    color={getScoreColor(evaluation.score)}
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                  <Box display="flex" justifyContent="space-between" alignItems="center" mt={1}>
                    <Chip
                      label={evaluation.score_name}
                      color={getScoreColor(evaluation.score) === 'primary' ? 'primary' : getScoreColor(evaluation.score) as 'success' | 'warning' | 'error'}
                      size="small"
                    />
                    <Typography variant="caption" color="text.secondary">
                      {Math.round(evaluation.confidence * 100)}% confident
                    </Typography>
                  </Box>
                </Box>

                <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.8rem', height: 40, overflow: 'hidden' }}>
                  {evaluation.score_reasoning}
                </Typography>

                {showEvidence && evaluation.evidence && (
                  <Box mt={2}>
                    <Typography variant="caption" color="text.secondary">
                      {evaluation.evidence.length} evidence items • Click for details
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {renderFactorDialog()}
    </Box>
  );
};

export default FactorCardsSimple;