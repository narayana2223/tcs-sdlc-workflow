/**
 * Debug version of FactorCards to test rendering
 */

import React from 'react';
import { Box, Card, CardContent, Typography, Grid } from '@mui/material';

interface FactorCardsDebugProps {
  factors: any;
  onFactorClick?: (factorName: string) => void;
  showEvidence?: boolean;
  groupBy?: string;
}

const FactorCardsDebug: React.FC<FactorCardsDebugProps> = ({ factors, onFactorClick }) => {
  console.log('FactorCardsDebug received factors:', factors);

  if (!factors) {
    return (
      <Box p={3}>
        <Typography variant="h6" color="error">
          No factors data received
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Factor Analysis - Debug Mode ({Object.keys(factors).length} factors)
      </Typography>
      <Grid container spacing={2}>
        {Object.entries(factors).map(([factorName, evaluation]: [string, any]) => (
          <Grid item xs={12} md={6} key={factorName}>
            <Card
              sx={{ cursor: 'pointer' }}
              onClick={() => onFactorClick && onFactorClick(factorName)}
            >
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {factorName}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Score: {evaluation.score}/5 ({evaluation.score_name})
                </Typography>
                <Typography variant="body2" color="text.secondary" mt={1}>
                  {evaluation.factor_description}
                </Typography>
                <Typography variant="body2" mt={1}>
                  {evaluation.score_reasoning}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default FactorCardsDebug;