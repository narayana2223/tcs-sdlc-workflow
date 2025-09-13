/**
 * Assessment routes for 12-factor assessment endpoints
 * Handles 12-factor assessment requests, status tracking, and result retrieval
 */

import { Router, Request, Response, NextFunction } from 'express';
import { body, param, query, validationResult } from 'express-validator';
import rateLimit from 'express-rate-limit';

import { AssessmentController } from '../controllers/assessment_controller';
import { MockAssessmentService } from '../services/mock_assessment_service';
import { 
  AssessmentRequest,
  AssessmentError,
  AssessmentNotFoundError,
  getDefaultAssessmentOptions
} from '../models/assessment_model';

const router = Router();
const assessmentController = new AssessmentController();

// Rate limiting for assessment endpoints
const assessmentRateLimit = rateLimit({
  windowMs: 30 * 60 * 1000, // 30 minutes
  max: 20, // Maximum 20 assessment requests per 30 minutes per user
  message: {
    error: 'Rate Limit Exceeded',
    message: 'Too many assessment requests. Maximum 20 per 30 minutes allowed.',
    timestamp: new Date().toISOString(),
    statusCode: 429,
  },
  standardHeaders: true,
  legacyHeaders: false,
});

// Validation middleware
const validateAssessmentRequest = [
  body('analysisJobId')
    .notEmpty()
    .withMessage('Analysis job ID is required')
    .isUUID()
    .withMessage('Invalid analysis job ID format'),
  
  body('options.includeRecommendations')
    .optional()
    .isBoolean()
    .withMessage('includeRecommendations must be boolean'),
  
  body('options.detailedEvidence')
    .optional()
    .isBoolean()
    .withMessage('detailedEvidence must be boolean'),
  
  body('options.generateRoadmap')
    .optional()
    .isBoolean()
    .withMessage('generateRoadmap must be boolean'),
  
  body('options.customWeights')
    .optional()
    .isObject()
    .withMessage('customWeights must be an object'),
  
  body('options.customWeights.*')
    .optional()
    .isFloat({ min: 0.1, max: 3.0 })
    .withMessage('Custom weights must be between 0.1 and 3.0'),
];

const validateJobId = [
  param('id')
    .notEmpty()
    .withMessage('Job ID is required')
    .isUUID()
    .withMessage('Invalid job ID format'),
];

const validateComparisonRequest = [
  body('currentAssessmentId')
    .notEmpty()
    .withMessage('Current assessment ID is required')
    .isUUID()
    .withMessage('Invalid current assessment ID format'),
  
  body('previousAssessmentId')
    .notEmpty()
    .withMessage('Previous assessment ID is required')
    .isUUID()
    .withMessage('Invalid previous assessment ID format'),
];

// Helper function to handle validation errors
const handleValidationErrors = (req: Request, res: Response, next: NextFunction) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    const error = new AssessmentError(
      `Validation failed: ${errors.array().map(err => err.msg).join(', ')}`,
      400,
      'VALIDATION_ERROR'
    );
    return next(error);
  }
  next();
};

/**
 * POST /api/assessment/12factor
 * Start a new 12-factor assessment
 */
router.post('/12factor', 
  assessmentRateLimit,
  validateAssessmentRequest,
  handleValidationErrors,
  async (req: any, res: Response, next: NextFunction) => {
    try {
      const assessmentRequest: AssessmentRequest = {
        analysisJobId: req.body.analysisJobId,
        options: {
          ...getDefaultAssessmentOptions(),
          ...req.body.options
        }
      };

      const response = await assessmentController.startAssessment(
        assessmentRequest,
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
 * GET /api/assessment/:id/status
 * Check the status of an assessment job
 */
router.get('/:id/status',
  validateJobId,
  handleValidationErrors,
  async (req: any, res: Response, next: NextFunction) => {
    try {
      const response = await assessmentController.getAssessmentStatus(
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
 * GET /api/assessment/:id/results
 * Get the results of a completed assessment
 */
router.get('/:id/results',
  validateJobId,
  [
    query('format')
      .optional()
      .isIn(['json', 'pdf', 'csv'])
      .withMessage('Format must be json, pdf, or csv'),
    
    query('includeRoadmap')
      .optional()
      .isBoolean()
      .withMessage('includeRoadmap must be boolean'),
    
    query('includeSummary')
      .optional()
      .isBoolean()
      .withMessage('includeSummary must be boolean'),
  ],
  handleValidationErrors,
  async (req: any, res: Response, next: NextFunction) => {
    try {
      const options = {
        format: req.query.format as string || 'json',
        includeRoadmap: req.query.includeRoadmap !== 'false',
        includeSummary: req.query.includeSummary !== 'false',
      };

      const response = await assessmentController.getAssessmentResults(
        req.params.id,
        'demo-user',
        options,
        req.headers['x-request-id'] as string
      );

      // Handle different response formats
      if (options.format === 'json') {
        res.json(response);
      } else if (options.format === 'pdf') {
        res.setHeader('Content-Type', 'application/pdf');
        res.setHeader('Content-Disposition', `attachment; filename="assessment-${req.params.id}.pdf"`);
        res.send(response.data);
      } else if (options.format === 'csv') {
        res.setHeader('Content-Type', 'text/csv');
        res.setHeader('Content-Disposition', `attachment; filename="assessment-${req.params.id}.csv"`);
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
 * GET /api/assessment/jobs
 * Get all assessment jobs for the current user
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
      .isIn(['createdAt', 'completedAt', 'grade', 'overall_score'])
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

      const response = await assessmentController.getUserAssessments(
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
 * DELETE /api/assessment/:id
 * Cancel or delete an assessment job
 */
router.delete('/:id',
  validateJobId,
  handleValidationErrors,
  async (req: any, res: Response, next: NextFunction) => {
    try {
      const force = req.query.force === 'true';

      const response = await assessmentController.cancelAssessment(
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
 * POST /api/assessment/compare
 * Compare two assessments to show progress
 */
router.post('/compare',
  validateComparisonRequest,
  handleValidationErrors,
  async (req: any, res: Response, next: NextFunction) => {
    try {
      const response = await assessmentController.compareAssessments(
        req.body.currentAssessmentId,
        req.body.previousAssessmentId,
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
 * GET /api/assessment/:id/factors
 * Get detailed factor evaluations
 */
router.get('/:id/factors',
  validateJobId,
  [
    query('factorName')
      .optional()
      .isLength({ min: 1, max: 100 })
      .withMessage('Invalid factor name'),
    
    query('includeEvidence')
      .optional()
      .isBoolean()
      .withMessage('includeEvidence must be boolean'),
    
    query('minScore')
      .optional()
      .isInt({ min: 0, max: 5 })
      .withMessage('minScore must be between 0 and 5'),
    
    query('maxScore')
      .optional()
      .isInt({ min: 0, max: 5 })
      .withMessage('maxScore must be between 0 and 5'),
  ],
  handleValidationErrors,
  async (req: any, res: Response, next: NextFunction) => {
    try {
      const filters = {
        factorName: req.query.factorName as string,
        includeEvidence: req.query.includeEvidence !== 'false',
        minScore: req.query.minScore ? parseInt(req.query.minScore as string) : undefined,
        maxScore: req.query.maxScore ? parseInt(req.query.maxScore as string) : undefined,
      };

      const response = await assessmentController.getFactorEvaluations(
        req.params.id,
        'demo-user',
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
 * GET /api/assessment/:id/recommendations
 * Get assessment recommendations with filtering
 */
router.get('/:id/recommendations',
  validateJobId,
  [
    query('priority')
      .optional()
      .isIn(['critical', 'high', 'medium', 'low'])
      .withMessage('Invalid priority filter'),
    
    query('factorName')
      .optional()
      .isLength({ min: 1, max: 100 })
      .withMessage('Invalid factor name'),
    
    query('complexity')
      .optional()
      .isIn(['low', 'medium', 'high', 'very_high'])
      .withMessage('Invalid complexity filter'),
    
    query('limit')
      .optional()
      .isInt({ min: 1, max: 50 })
      .withMessage('Limit must be between 1 and 50'),
  ],
  handleValidationErrors,
  async (req: any, res: Response, next: NextFunction) => {
    try {
      const filters = {
        priority: req.query.priority as string,
        factorName: req.query.factorName as string,
        complexity: req.query.complexity as string,
        limit: parseInt(req.query.limit as string) || 20,
      };

      const response = await assessmentController.getRecommendations(
        req.params.id,
        'demo-user',
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
 * GET /api/assessment/:id/roadmap
 * Get implementation roadmap
 */
router.get('/:id/roadmap',
  validateJobId,
  handleValidationErrors,
  async (req: any, res: Response, next: NextFunction) => {
    try {
      const response = await assessmentController.getImplementationRoadmap(
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
 * GET /api/assessment/stats
 * Get assessment statistics for the current user
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

      const response = await assessmentController.getAssessmentStatistics(
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
 * GET /api/assessment/definitions
 * Get 12-factor definitions and criteria
 */
router.get('/definitions',
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const response = await assessmentController.getTwelveFactorDefinitions(
        req.headers['x-request-id'] as string
      );

      res.json(response);
    } catch (error) {
      next(error);
    }
  }
);

/**
 * POST /api/assessment/:id/restart
 * Restart a failed assessment job
 */
router.post('/:id/restart',
  validateJobId,
  handleValidationErrors,
  async (req: any, res: Response, next: NextFunction) => {
    try {
      const response = await assessmentController.restartAssessment(
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
 * GET /api/assessment/:id/summary
 * Get assessment summary with insights
 */
router.get('/:id/summary',
  validateJobId,
  handleValidationErrors,
  async (req: any, res: Response, next: NextFunction) => {
    try {
      const response = await assessmentController.getAssessmentSummary(
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
 * GET /api/assessment/mock
 * Get a mock 12-factor assessment for demonstration
 */
router.get('/mock',
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const repositoryUrl = req.query.repo as string || 'demo-repository';

      // Generate mock assessment data
      const assessment = MockAssessmentService.generateMockAssessment(repositoryUrl);
      const summary = MockAssessmentService.generateAssessmentSummary(assessment);

      const response = {
        success: true,
        data: {
          assessment,
          summary,
        },
        timestamp: new Date().toISOString(),
        requestId: req.headers['x-request-id'] || 'mock-request'
      };

      res.json(response);
    } catch (error) {
      next(error);
    }
  }
);

export default router;