/**
 * Opportunities routes for transformation opportunity endpoints
 * Handles opportunity generation, filtering, and detailed views
 */

import { Router, Request, Response, NextFunction } from 'express';
import { body, param, query, validationResult } from 'express-validator';
import rateLimit from 'express-rate-limit';

import { MockOpportunityService, OpportunityCategory, OpportunityType } from '../services/mock_opportunity_service';

const router = Router();

// Rate limiting for opportunity endpoints
const opportunityRateLimit = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 50, // Maximum 50 requests per 15 minutes per user
  message: {
    error: 'Rate Limit Exceeded',
    message: 'Too many opportunity requests. Maximum 50 per 15 minutes allowed.',
    timestamp: new Date().toISOString(),
    statusCode: 429,
  },
  standardHeaders: true,
  legacyHeaders: false,
});

// Validation middleware
const validateOpportunityRequest = [
  query('category')
    .optional()
    .isIn(Object.values(OpportunityCategory))
    .withMessage('Invalid opportunity category'),

  query('type')
    .optional()
    .isIn(Object.values(OpportunityType))
    .withMessage('Invalid opportunity type'),

  query('minImpact')
    .optional()
    .isInt({ min: 1, max: 10 })
    .withMessage('minImpact must be between 1 and 10'),

  query('maxImpact')
    .optional()
    .isInt({ min: 1, max: 10 })
    .withMessage('maxImpact must be between 1 and 10'),

  query('minEffort')
    .optional()
    .isInt({ min: 1, max: 10 })
    .withMessage('minEffort must be between 1 and 10'),

  query('maxEffort')
    .optional()
    .isInt({ min: 1, max: 10 })
    .withMessage('maxEffort must be between 1 and 10'),

  query('priority')
    .optional()
    .isIn(['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'])
    .withMessage('Invalid priority level'),

  query('riskLevel')
    .optional()
    .isIn(['LOW', 'MEDIUM', 'HIGH'])
    .withMessage('Invalid risk level'),

  query('limit')
    .optional()
    .isInt({ min: 1, max: 100 })
    .withMessage('limit must be between 1 and 100'),
];

const validateOpportunityId = [
  param('opportunityId')
    .notEmpty()
    .withMessage('Opportunity ID is required')
    .isLength({ min: 1, max: 100 })
    .withMessage('Invalid opportunity ID format'),
];

// Error handling middleware
const handleValidationErrors = (req: Request, res: Response, next: NextFunction) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({
      success: false,
      error: {
        code: 'VALIDATION_ERROR',
        message: 'Request validation failed',
        details: errors.array().map(error => ({
          field: error.type === 'field' ? (error as any).path : 'unknown',
          message: error.msg,
          value: error.type === 'field' ? (error as any).value : undefined
        }))
      },
      timestamp: new Date().toISOString(),
      requestId: res.locals.requestId
    });
  }
  next();
};

/**
 * @route GET /api/opportunities
 * @desc Get all transformation opportunities with optional filtering
 * @access Public (demo mode)
 */
router.get(
  '/',
  opportunityRateLimit,
  validateOpportunityRequest,
  handleValidationErrors,
  async (req: Request, res: Response) => {
    try {
      const {
        category,
        type,
        minImpact,
        maxImpact,
        minEffort,
        maxEffort,
        priority,
        riskLevel,
        limit
      } = req.query;

      // Generate all opportunities
      let opportunities = MockOpportunityService.generateOpportunities('demo-assessment');

      // Apply filters
      if (category) {
        opportunities = opportunities.filter(opp => opp.category === category);
      }

      if (type) {
        opportunities = opportunities.filter(opp => opp.type === type);
      }

      if (minImpact) {
        opportunities = opportunities.filter(opp => opp.impactScore >= parseInt(minImpact as string));
      }

      if (maxImpact) {
        opportunities = opportunities.filter(opp => opp.impactScore <= parseInt(maxImpact as string));
      }

      if (minEffort) {
        opportunities = opportunities.filter(opp => opp.effortScore >= parseInt(minEffort as string));
      }

      if (maxEffort) {
        opportunities = opportunities.filter(opp => opp.effortScore <= parseInt(maxEffort as string));
      }

      if (priority) {
        opportunities = opportunities.filter(opp => opp.priority === priority);
      }

      if (riskLevel) {
        opportunities = opportunities.filter(opp => opp.riskLevel === riskLevel);
      }

      // Apply limit
      if (limit) {
        opportunities = opportunities.slice(0, parseInt(limit as string));
      }

      // Calculate summary statistics
      const totalOpportunities = opportunities.length;
      const totalSavings = opportunities.reduce((sum, opp) => {
        const savings = parseFloat(opp.estimatedSavings.replace(/[^\d]/g, ''));
        return sum + (isNaN(savings) ? 0 : savings);
      }, 0);
      const averageROI = totalOpportunities > 0
        ? Math.round(opportunities.reduce((sum, opp) => sum + opp.roiScore, 0) / totalOpportunities)
        : 0;
      const highPriorityCount = opportunities.filter(opp =>
        opp.priority === 'CRITICAL' || opp.priority === 'HIGH'
      ).length;

      res.json({
        success: true,
        data: {
          opportunities,
          summary: {
            totalOpportunities,
            totalSavings,
            averageROI,
            highPriorityCount,
            categories: Object.values(OpportunityCategory).map(cat => ({
              name: cat,
              count: opportunities.filter(opp => opp.category === cat).length
            })).filter(cat => cat.count > 0)
          }
        },
        timestamp: new Date().toISOString(),
        requestId: res.locals.requestId
      });

    } catch (error) {
      console.error('Error getting opportunities:', error);
      res.status(500).json({
        success: false,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to retrieve transformation opportunities',
          details: error instanceof Error ? error.message : 'Unknown error occurred'
        },
        timestamp: new Date().toISOString(),
        requestId: res.locals.requestId
      });
    }
  }
);

/**
 * @route GET /api/opportunities/matrix
 * @desc Get impact vs effort matrix data
 * @access Public (demo mode)
 */
router.get(
  '/matrix',
  opportunityRateLimit,
  async (req: Request, res: Response) => {
    try {
      const matrixData = MockOpportunityService.generateOpportunityMatrix();

      res.json({
        success: true,
        data: matrixData,
        timestamp: new Date().toISOString(),
        requestId: res.locals.requestId
      });

    } catch (error) {
      console.error('Error getting opportunity matrix:', error);
      res.status(500).json({
        success: false,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to retrieve opportunity matrix',
          details: error instanceof Error ? error.message : 'Unknown error occurred'
        },
        timestamp: new Date().toISOString(),
        requestId: res.locals.requestId
      });
    }
  }
);

/**
 * @route GET /api/opportunities/categories/:category
 * @desc Get opportunities by category
 * @access Public (demo mode)
 */
router.get(
  '/categories/:category',
  opportunityRateLimit,
  [
    param('category')
      .isIn(Object.values(OpportunityCategory))
      .withMessage('Invalid opportunity category')
  ],
  handleValidationErrors,
  async (req: Request, res: Response) => {
    try {
      const { category } = req.params;
      const opportunities = MockOpportunityService.getOpportunitiesByCategory(category as OpportunityCategory);

      res.json({
        success: true,
        data: {
          category,
          opportunities,
          count: opportunities.length
        },
        timestamp: new Date().toISOString(),
        requestId: res.locals.requestId
      });

    } catch (error) {
      console.error('Error getting opportunities by category:', error);
      res.status(500).json({
        success: false,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to retrieve opportunities by category',
          details: error instanceof Error ? error.message : 'Unknown error occurred'
        },
        timestamp: new Date().toISOString(),
        requestId: res.locals.requestId
      });
    }
  }
);

/**
 * @route GET /api/opportunities/prioritized
 * @desc Get prioritized opportunities (high impact, manageable effort)
 * @access Public (demo mode)
 */
router.get(
  '/prioritized',
  opportunityRateLimit,
  [
    query('limit')
      .optional()
      .isInt({ min: 1, max: 20 })
      .withMessage('limit must be between 1 and 20')
  ],
  handleValidationErrors,
  async (req: Request, res: Response) => {
    try {
      const { limit } = req.query;
      const maxCount = limit ? parseInt(limit as string) : undefined;
      const opportunities = MockOpportunityService.getPrioritizedOpportunities(maxCount);

      res.json({
        success: true,
        data: {
          opportunities,
          count: opportunities.length,
          criteria: {
            sortedBy: ['priority', 'roiScore'],
            description: 'Opportunities sorted by priority and ROI score'
          }
        },
        timestamp: new Date().toISOString(),
        requestId: res.locals.requestId
      });

    } catch (error) {
      console.error('Error getting prioritized opportunities:', error);
      res.status(500).json({
        success: false,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to retrieve prioritized opportunities',
          details: error instanceof Error ? error.message : 'Unknown error occurred'
        },
        timestamp: new Date().toISOString(),
        requestId: res.locals.requestId
      });
    }
  }
);

/**
 * @route GET /api/opportunities/:opportunityId
 * @desc Get detailed information for a specific opportunity
 * @access Public (demo mode)
 */
router.get(
  '/:opportunityId',
  opportunityRateLimit,
  validateOpportunityId,
  handleValidationErrors,
  async (req: Request, res: Response) => {
    try {
      const { opportunityId } = req.params;
      const opportunity = MockOpportunityService.getOpportunityById(opportunityId);

      if (!opportunity) {
        return res.status(404).json({
          success: false,
          error: {
            code: 'OPPORTUNITY_NOT_FOUND',
            message: `Opportunity not found: ${opportunityId}`,
            details: `No opportunity exists with ID: ${opportunityId}`
          },
          timestamp: new Date().toISOString(),
          requestId: res.locals.requestId
        });
      }

      res.json({
        success: true,
        data: {
          opportunity,
          relatedOpportunities: MockOpportunityService.getOpportunitiesByCategory(opportunity.category)
            .filter(opp => opp.id !== opportunityId)
            .slice(0, 3) // Get up to 3 related opportunities
        },
        timestamp: new Date().toISOString(),
        requestId: res.locals.requestId
      });

    } catch (error) {
      console.error('Error getting opportunity details:', error);
      res.status(500).json({
        success: false,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to retrieve opportunity details',
          details: error instanceof Error ? error.message : 'Unknown error occurred'
        },
        timestamp: new Date().toISOString(),
        requestId: res.locals.requestId
      });
    }
  }
);

/**
 * @route POST /api/opportunities/compare
 * @desc Compare multiple opportunities
 * @access Public (demo mode)
 */
router.post(
  '/compare',
  opportunityRateLimit,
  [
    body('opportunityIds')
      .isArray({ min: 2, max: 5 })
      .withMessage('Must provide 2-5 opportunity IDs for comparison'),
    body('opportunityIds.*')
      .notEmpty()
      .withMessage('Opportunity ID cannot be empty')
  ],
  handleValidationErrors,
  async (req: Request, res: Response) => {
    try {
      const { opportunityIds } = req.body;

      const opportunities = opportunityIds
        .map((id: string) => MockOpportunityService.getOpportunityById(id))
        .filter((opp: any) => opp !== null);

      if (opportunities.length !== opportunityIds.length) {
        return res.status(400).json({
          success: false,
          error: {
            code: 'INVALID_OPPORTUNITY_IDS',
            message: 'One or more opportunity IDs not found',
            details: 'Some of the provided opportunity IDs do not exist'
          },
          timestamp: new Date().toISOString(),
          requestId: res.locals.requestId
        });
      }

      // Generate comparison analysis
      const comparison = {
        opportunities,
        analysis: {
          highestROI: opportunities.reduce((max, opp) => opp.roiScore > max.roiScore ? opp : max),
          lowestEffort: opportunities.reduce((min, opp) => opp.effortScore < min.effortScore ? opp : min),
          highestImpact: opportunities.reduce((max, opp) => opp.impactScore > max.impactScore ? opp : max),
          quickestImplementation: opportunities.reduce((min, opp) => {
            const parseTimeline = (timeline: string) => {
              const match = timeline.match(/(\d+)/);
              return match ? parseInt(match[1]) : 12;
            };
            return parseTimeline(opp.implementationTimeline) < parseTimeline(min.implementationTimeline) ? opp : min;
          }),
          totalSavings: opportunities.reduce((sum, opp) => {
            const savings = parseFloat(opp.estimatedSavings.replace(/[^\d]/g, ''));
            return sum + (isNaN(savings) ? 0 : savings);
          }, 0),
          averageROI: Math.round(opportunities.reduce((sum, opp) => sum + opp.roiScore, 0) / opportunities.length)
        }
      };

      res.json({
        success: true,
        data: comparison,
        timestamp: new Date().toISOString(),
        requestId: res.locals.requestId
      });

    } catch (error) {
      console.error('Error comparing opportunities:', error);
      res.status(500).json({
        success: false,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to compare opportunities',
          details: error instanceof Error ? error.message : 'Unknown error occurred'
        },
        timestamp: new Date().toISOString(),
        requestId: res.locals.requestId
      });
    }
  }
);

export default router;