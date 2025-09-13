/**
 * Analysis routes for repository analysis endpoints
 * Handles repository analysis requests, status tracking, and result retrieval
 */

import { Router, Request, Response, NextFunction } from 'express';
import { body, param, query, validationResult } from 'express-validator';
import rateLimit from 'express-rate-limit';

import { AnalysisController } from '../controllers/analysis_controller';
import { 
  AnalysisType, 
  AnalysisRequest,
  ValidationError,
  isValidRepositoryUrl,
  sanitizeRepositoryUrl,
  getDefaultAnalysisOptions
} from '../models/analysis_model';

const router = Router();
const analysisController = new AnalysisController();

// Rate limiting for analysis endpoints
const analysisRateLimit = rateLimit({
  windowMs: 60 * 60 * 1000, // 1 hour
  max: 10, // Maximum 10 analysis requests per hour per user
  message: {
    error: 'Rate Limit Exceeded',
    message: 'Too many analysis requests. Maximum 10 per hour allowed.',
    timestamp: new Date().toISOString(),
    statusCode: 429,
  },
  standardHeaders: true,
  legacyHeaders: false,
});

// Validation middleware
const validateAnalysisRequest = [
  body('repositoryUrl')
    .notEmpty()
    .withMessage('Repository URL is required')
    .isLength({ max: 500 })
    .withMessage('Repository URL too long')
    .custom((value) => {
      if (!isValidRepositoryUrl(value)) {
        throw new Error('Invalid repository URL format. Supported: GitHub, GitLab, Bitbucket');
      }
      return true;
    }),
  
  body('branchName')
    .optional()
    .isLength({ max: 100 })
    .withMessage('Branch name too long')
    .matches(/^[a-zA-Z0-9_.-]+$/)
    .withMessage('Invalid branch name format'),
  
  body('analysisType')
    .notEmpty()
    .withMessage('Analysis type is required')
    .isIn(Object.values(AnalysisType))
    .withMessage('Invalid analysis type'),
  
  body('options.includeTests')
    .optional()
    .isBoolean()
    .withMessage('includeTests must be boolean'),
  
  body('options.includeDependencies')
    .optional()
    .isBoolean()
    .withMessage('includeDependencies must be boolean'),
  
  body('options.performanceMetrics')
    .optional()
    .isBoolean()
    .withMessage('performanceMetrics must be boolean'),
  
  body('options.securityScan')
    .optional()
    .isBoolean()
    .withMessage('securityScan must be boolean'),
  
  body('options.codeQuality')
    .optional()
    .isBoolean()
    .withMessage('codeQuality must be boolean'),
  
  body('options.depth')
    .optional()
    .isInt({ min: 1, max: 1000 })
    .withMessage('Depth must be between 1 and 1000'),
  
  body('options.timeout')
    .optional()
    .isInt({ min: 1, max: 120 })
    .withMessage('Timeout must be between 1 and 120 minutes'),
];

const validateJobId = [
  param('id')
    .notEmpty()
    .withMessage('Job ID is required')
    .isUUID()
    .withMessage('Invalid job ID format'),
];

// Helper function to handle validation errors
const handleValidationErrors = (req: Request, res: Response, next: NextFunction) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    const validationError = new ValidationError(
      `Validation failed: ${errors.array().map(err => err.msg).join(', ')}`
    );
    return next(validationError);
  }
  next();
};

/**
 * POST /api/analysis/repository
 * Start a new repository analysis
 */
router.post('/repository', 
  analysisRateLimit,
  validateAnalysisRequest,
  handleValidationErrors,
  async (req: any, res: Response, next: NextFunction) => {
    try {
      const analysisRequest: AnalysisRequest = {
        repositoryUrl: sanitizeRepositoryUrl(req.body.repositoryUrl),
        branchName: req.body.branchName,
        analysisType: req.body.analysisType,
        options: {
          ...getDefaultAnalysisOptions(),
          ...req.body.options
        }
      };

      const response = await analysisController.startAnalysis(
        analysisRequest,
        'demo-user',
        req.headers['x-request-id'] as string,
        {
          userAgent: req.headers['user-agent'],
          ipAddress: req.ip
        }
      );

      res.status(201).json(response);
    } catch (error) {
      next(error);
    }
  }
);

/**
 * GET /api/analysis/:id/status
 * Check the status of an analysis job
 */
router.get('/:id/status',
  validateJobId,
  handleValidationErrors,
  async (req: any, res: Response, next: NextFunction) => {
    try {
      const response = await analysisController.getAnalysisStatus(
        req.params.id,
        'demo-user',
        req.headers['x-request-id'] as string
      );

      res.json(response);
    } catch (error) {
      next(error);
    }
  }
);

/**
 * GET /api/analysis/:id/results
 * Get the results of a completed analysis
 */
router.get('/:id/results',
  validateJobId,
  handleValidationErrors,
  async (req: any, res: Response, next: NextFunction) => {
    try {
      const includeMetadata = req.query.includeMetadata === 'true';
      const format = req.query.format as string || 'json';

      const response = await analysisController.getAnalysisResults(
        req.params.id,
        'demo-user',
        req.headers['x-request-id'] as string,
        { includeMetadata, format }
      );

      // Handle different response formats
      if (format === 'json') {
        res.json(response);
      } else if (format === 'csv') {
        res.setHeader('Content-Type', 'text/csv');
        res.setHeader('Content-Disposition', `attachment; filename="analysis-${req.params.id}.csv"`);
        res.send(response.data);
      } else {
        res.json(response);
      }
    } catch (error) {
      next(error);
    }
  }
);

/**
 * GET /api/analysis/jobs
 * Get all analysis jobs for the current user
 */
router.get('/jobs',
  [
    query('status')
      .optional()
      .isIn(['pending', 'processing', 'completed', 'failed', 'cancelled'])
      .withMessage('Invalid status filter'),
    
    query('limit')
      .optional()
      .isInt({ min: 1, max: 100 })
      .withMessage('Limit must be between 1 and 100'),
    
    query('offset')
      .optional()
      .isInt({ min: 0 })
      .withMessage('Offset must be non-negative'),
    
    query('sortBy')
      .optional()
      .isIn(['createdAt', 'completedAt', 'repositoryUrl'])
      .withMessage('Invalid sort field'),
    
    query('sortOrder')
      .optional()
      .isIn(['asc', 'desc'])
      .withMessage('Sort order must be asc or desc'),
  ],
  handleValidationErrors,
  async (req: any, res: Response, next: NextFunction) => {
    try {
      const filters = {
        status: req.query.status,
        limit: parseInt(req.query.limit as string) || 20,
        offset: parseInt(req.query.offset as string) || 0,
        sortBy: req.query.sortBy || 'createdAt',
        sortOrder: req.query.sortOrder || 'desc',
      };

      const response = await analysisController.getUserAnalyses(
        'demo-user', // No authentication required - use demo user
        filters,
        req.headers['x-request-id'] as string
      );

      res.json(response);
    } catch (error) {
      next(error);
    }
  }
);

/**
 * DELETE /api/analysis/:id
 * Cancel or delete an analysis job
 */
router.delete('/:id',
  validateJobId,
  handleValidationErrors,
  async (req: any, res: Response, next: NextFunction) => {
    try {
      const force = req.query.force === 'true';

      const response = await analysisController.cancelAnalysis(
        req.params.id,
        'demo-user',
        force,
        req.headers['x-request-id'] as string
      );

      res.json(response);
    } catch (error) {
      next(error);
    }
  }
);

/**
 * POST /api/analysis/:id/restart
 * Restart a failed analysis job
 */
router.post('/:id/restart',
  validateJobId,
  handleValidationErrors,
  async (req: any, res: Response, next: NextFunction) => {
    try {
      const response = await analysisController.restartAnalysis(
        req.params.id,
        'demo-user',
        req.headers['x-request-id'] as string
      );

      res.json(response);
    } catch (error) {
      next(error);
    }
  }
);

/**
 * GET /api/analysis/:id/logs
 * Get analysis logs for debugging
 */
router.get('/:id/logs',
  validateJobId,
  [
    query('level')
      .optional()
      .isIn(['debug', 'info', 'warn', 'error'])
      .withMessage('Invalid log level'),
    
    query('limit')
      .optional()
      .isInt({ min: 1, max: 1000 })
      .withMessage('Limit must be between 1 and 1000'),
  ],
  handleValidationErrors,
  async (req: any, res: Response, next: NextFunction) => {
    try {
      const options = {
        level: req.query.level as string,
        limit: parseInt(req.query.limit as string) || 100,
      };

      const response = await analysisController.getAnalysisLogs(
        req.params.id,
        'demo-user',
        options,
        req.headers['x-request-id'] as string
      );

      res.json(response);
    } catch (error) {
      next(error);
    }
  }
);

/**
 * GET /api/analysis/stats
 * Get analysis statistics for the current user
 */
router.get('/stats',
  [
    query('period')
      .optional()
      .isIn(['7d', '30d', '90d', '1y'])
      .withMessage('Invalid period. Use: 7d, 30d, 90d, or 1y'),
  ],
  handleValidationErrors,
  async (req: any, res: Response, next: NextFunction) => {
    try {
      const period = req.query.period as string || '30d';

      const response = await analysisController.getAnalysisStatistics(
        'demo-user',
        period,
        req.headers['x-request-id'] as string
      );

      res.json(response);
    } catch (error) {
      next(error);
    }
  }
);

/**
 * POST /api/analysis/validate
 * Validate repository URL without starting analysis
 */
router.post('/validate',
  [
    body('repositoryUrl')
      .notEmpty()
      .withMessage('Repository URL is required')
      .custom((value) => {
        if (!isValidRepositoryUrl(value)) {
          throw new Error('Invalid repository URL format');
        }
        return true;
      }),
  ],
  handleValidationErrors,
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const repositoryUrl = sanitizeRepositoryUrl(req.body.repositoryUrl);

      const response = await analysisController.validateRepository(
        repositoryUrl,
        req.headers['x-request-id'] as string
      );

      res.json(response);
    } catch (error) {
      next(error);
    }
  }
);

export default router;