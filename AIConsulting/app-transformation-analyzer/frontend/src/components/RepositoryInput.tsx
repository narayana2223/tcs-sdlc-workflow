/**
 * Repository Input Component
 * Form for entering repository details and analysis options
 */

import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Checkbox,
  Button,
  Typography,
  Alert,
  CircularProgress,
  Chip,
  Collapse,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Help as HelpIcon,
  GitHub as GitHubIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { AnalysisRequest, RepositoryInputProps, AnalysisType } from '../types';

const RepositoryInput: React.FC<RepositoryInputProps> = ({
  onSubmit,
  loading = false,
  error,
}) => {
  const [formData, setFormData] = useState<AnalysisRequest>({
    repositoryUrl: '',
    branchName: 'main',
    analysisType: 'full',
    options: {
      depth: 5,
      includeTests: true,
      timeout: 30,
    },
  });

  const [expanded, setExpanded] = useState(false);
  const [validating, setValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<{
    valid: boolean;
    message?: string;
  } | null>(null);

  const analysisTypes: Array<{ value: AnalysisType; label: string; description: string }> = [
    {
      value: 'full',
      label: 'Full Analysis',
      description: 'Complete analysis including code quality, dependencies, and architecture'
    },
    {
      value: 'quick',
      label: 'Quick Analysis',
      description: 'Basic metrics and technology stack detection'
    },
    {
      value: 'dependencies',
      label: 'Dependencies Only',
      description: 'Focus on dependency analysis and security vulnerabilities'
    },
    {
      value: 'security',
      label: 'Security Focus',
      description: 'Security-focused analysis with vulnerability scanning'
    },
    {
      value: 'quality',
      label: 'Code Quality',
      description: 'Code quality metrics, complexity, and maintainability'
    },
  ];

  const handleInputChange = (field: keyof AnalysisRequest, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
    
    // Clear validation result when repository URL changes
    if (field === 'repositoryUrl') {
      setValidationResult(null);
    }
  };

  const handleOptionsChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      options: {
        ...prev.options,
        [field]: value,
      },
    }));
  };

  const validateRepository = async () => {
    if (!formData.repositoryUrl.trim()) {
      setValidationResult({
        valid: false,
        message: 'Please enter a repository URL',
      });
      return;
    }

    setValidating(true);
    try {
      // In a real implementation, this would call the API
      // For now, we'll do basic URL validation
      const urlPattern = /^https?:\/\/(github\.com|gitlab\.com|bitbucket\.org)\/.+\/.+$/;
      const isValid = urlPattern.test(formData.repositoryUrl);
      
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate API call
      
      setValidationResult({
        valid: isValid,
        message: isValid 
          ? 'Repository is accessible' 
          : 'Invalid repository URL format or repository not accessible',
      });
    } catch (error) {
      setValidationResult({
        valid: false,
        message: 'Failed to validate repository',
      });
    } finally {
      setValidating(false);
    }
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    
    if (!formData.repositoryUrl.trim()) {
      return;
    }
    
    onSubmit(formData);
  };

  const isFormValid = () => {
    return formData.repositoryUrl.trim() !== '' && !loading;
  };

  const getEstimatedTime = (type: AnalysisType): string => {
    const times = {
      full: '10-15 minutes',
      quick: '2-3 minutes',
      dependencies: '3-5 minutes',
      security: '5-8 minutes',
      quality: '8-12 minutes',
    };
    return times[type] || '5-10 minutes';
  };

  return (
    <Card elevation={2}>
      <CardContent>
        <Box display="flex" alignItems="center" gap={1} mb={3}>
          <GitHubIcon color="primary" />
          <Typography variant="h6" component="h2">
            Repository Analysis
          </Typography>
        </Box>

        <form onSubmit={handleSubmit}>
          <Box display="flex" flexDirection="column" gap={3}>
            {/* Repository URL */}
            <Box>
              <TextField
                fullWidth
                label="Repository URL"
                placeholder="https://github.com/username/repository"
                value={formData.repositoryUrl}
                onChange={(e) => handleInputChange('repositoryUrl', e.target.value)}
                disabled={loading}
                error={validationResult?.valid === false}
                helperText={
                  validationResult?.message ||
                  'Enter the URL of your GitHub, GitLab, or Bitbucket repository'
                }
                InputProps={{
                  endAdornment: (
                    <IconButton
                      onClick={validateRepository}
                      disabled={loading || validating || !formData.repositoryUrl.trim()}
                      size="small"
                    >
                      {validating ? (
                        <CircularProgress size={20} />
                      ) : (
                        <Tooltip title="Validate repository">
                          <RefreshIcon />
                        </Tooltip>
                      )}
                    </IconButton>
                  ),
                }}
              />

              {/* Sample Repository URLs */}
              <Box mt={1}>
                <Typography variant="caption" color="text.secondary" gutterBottom>
                  Try these sample repositories:
                </Typography>
                <Box display="flex" flexWrap="wrap" gap={1} mt={0.5}>
                  {[
                    { url: 'https://github.com/facebook/react', name: 'React' },
                    { url: 'https://github.com/expressjs/express', name: 'Express.js' },
                    { url: 'https://github.com/microsoft/vscode', name: 'VS Code' },
                    { url: 'https://github.com/vercel/next.js', name: 'Next.js' }
                  ].map((sample) => (
                    <Chip
                      key={sample.url}
                      label={sample.name}
                      size="small"
                      variant="outlined"
                      clickable
                      disabled={loading}
                      onClick={() => handleInputChange('repositoryUrl', sample.url)}
                      sx={{
                        fontSize: '0.7rem',
                        height: '24px',
                        '&:hover': {
                          backgroundColor: 'primary.light',
                          color: 'white'
                        }
                      }}
                    />
                  ))}
                </Box>
              </Box>
            </Box>

            {/* Branch Name */}
            <TextField
              fullWidth
              label="Branch Name"
              value={formData.branchName}
              onChange={(e) => handleInputChange('branchName', e.target.value)}
              disabled={loading}
              helperText="The branch to analyze (default: main)"
            />

            {/* Analysis Type */}
            <FormControl fullWidth>
              <InputLabel>Analysis Type</InputLabel>
              <Select
                value={formData.analysisType}
                onChange={(e) => handleInputChange('analysisType', e.target.value as AnalysisType)}
                disabled={loading}
                label="Analysis Type"
              >
                {analysisTypes.map((type) => (
                  <MenuItem key={type.value} value={type.value}>
                    <Box>
                      <Typography variant="body1">{type.label}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {type.description}
                      </Typography>
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {/* Estimated Time */}
            <Box display="flex" alignItems="center" gap={1}>
              <Chip 
                label={`Estimated time: ${getEstimatedTime(formData.analysisType)}`}
                color="primary"
                variant="outlined"
                size="small"
              />
            </Box>

            {/* Advanced Options */}
            <Box>
              <Button
                variant="text"
                onClick={() => setExpanded(!expanded)}
                endIcon={
                  <ExpandMoreIcon 
                    sx={{ 
                      transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
                      transition: 'transform 0.2s'
                    }} 
                  />
                }
                disabled={loading}
              >
                Advanced Options
              </Button>
              
              <Collapse in={expanded}>
                <Box display="flex" flexDirection="column" gap={2} mt={2} pl={2}>
                  <TextField
                    label="Analysis Depth"
                    type="number"
                    value={formData.options?.depth || 5}
                    onChange={(e) => handleOptionsChange('depth', parseInt(e.target.value))}
                    disabled={loading}
                    inputProps={{ min: 1, max: 10 }}
                    helperText="How deep to analyze nested structures (1-10)"
                    sx={{ width: 200 }}
                  />

                  <TextField
                    label="Timeout (minutes)"
                    type="number"
                    value={formData.options?.timeout || 30}
                    onChange={(e) => handleOptionsChange('timeout', parseInt(e.target.value))}
                    disabled={loading}
                    inputProps={{ min: 5, max: 120 }}
                    helperText="Maximum time to spend on analysis"
                    sx={{ width: 200 }}
                  />

                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={formData.options?.includeTests ?? true}
                        onChange={(e) => handleOptionsChange('includeTests', e.target.checked)}
                        disabled={loading}
                      />
                    }
                    label={
                      <Box display="flex" alignItems="center" gap={0.5}>
                        <span>Include test files in analysis</span>
                        <Tooltip title="When enabled, test files will be included in metrics and analysis">
                          <HelpIcon fontSize="small" />
                        </Tooltip>
                      </Box>
                    }
                  />
                </Box>
              </Collapse>
            </Box>

            {/* Error Display */}
            {error && (
              <Alert severity="error" sx={{ mt: 1 }}>
                {error}
              </Alert>
            )}

            {/* Submit Button */}
            <Button
              type="submit"
              variant="contained"
              size="large"
              disabled={!isFormValid()}
              sx={{ py: 1.5 }}
            >
              {loading ? (
                <Box display="flex" alignItems="center" gap={1}>
                  <CircularProgress size={20} color="inherit" />
                  Starting Analysis...
                </Box>
              ) : (
                'Start Analysis'
              )}
            </Button>

            {/* Info */}
            <Alert severity="info" sx={{ mt: 1 }}>
              <Typography variant="body2">
                Your repository will be analyzed for code quality, architecture patterns, 
                dependencies, and 12-factor app compliance. No code will be stored permanently.
              </Typography>
            </Alert>
          </Box>
        </form>
      </CardContent>
    </Card>
  );
};

export default RepositoryInput;