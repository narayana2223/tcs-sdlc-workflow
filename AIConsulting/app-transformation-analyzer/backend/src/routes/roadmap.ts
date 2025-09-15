/**
 * Roadmap routes for transformation planning endpoints
 * Handles roadmap generation, timeline management, and resource planning
 */

import { Router, Request, Response, NextFunction } from 'express';
import { body, param, query, validationResult } from 'express-validator';
import rateLimit from 'express-rate-limit';

import { MockRoadmapService } from '../services/mock_roadmap_service';

const router = Router();

// Rate limiting for roadmap endpoints
const roadmapRateLimit = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 30, // Maximum 30 requests per 15 minutes per user
  message: {
    error: 'Rate Limit Exceeded',
    message: 'Too many roadmap requests. Maximum 30 per 15 minutes allowed.',
    timestamp: new Date().toISOString(),
    statusCode: 429,
  },
  standardHeaders: true,
  legacyHeaders: false,
});

// Validation middleware
const validateRoadmapRequest = [
  param('assessmentId')
    .optional()
    .notEmpty()
    .withMessage('Assessment ID cannot be empty')
    .isLength({ min: 1, max: 100 })
    .withMessage('Invalid assessment ID format'),
];

const validateMilestoneUpdate = [
  param('roadmapId')
    .notEmpty()
    .withMessage('Roadmap ID is required'),
  param('milestoneId')
    .notEmpty()
    .withMessage('Milestone ID is required'),
  body('status')
    .optional()
    .isIn(['NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'BLOCKED', 'AT_RISK'])
    .withMessage('Invalid status'),
  body('completionPercentage')
    .optional()
    .isInt({ min: 0, max: 100 })
    .withMessage('Completion percentage must be between 0 and 100'),
];

const validateExportRequest = [
  param('roadmapId')
    .notEmpty()
    .withMessage('Roadmap ID is required'),
  query('format')
    .isIn(['MS_PROJECT', 'JIRA', 'ASANA', 'EXCEL', 'PDF', 'POWERPOINT'])
    .withMessage('Invalid export format'),
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
 * @route GET /api/roadmap/sample
 * @desc Get sample transformation roadmap for demo
 * @access Public (demo mode)
 */
router.get(
  '/sample',
  roadmapRateLimit,
  async (req: Request, res: Response) => {
    try {
      const roadmap = MockRoadmapService.generateComprehensiveRoadmap('demo-assessment-id');

      res.json({
        success: true,
        data: roadmap,
        metadata: {
          generatedAt: new Date().toISOString(),
          totalPhases: roadmap.phases.length,
          totalMilestones: roadmap.phases.reduce((acc, phase) => acc + phase.milestones.length, 0),
          estimatedDuration: roadmap.totalDuration
        },
        timestamp: new Date().toISOString(),
        requestId: res.locals.requestId
      });

    } catch (error) {
      console.error('Error generating sample roadmap:', error);
      res.status(500).json({
        success: false,
        error: {
          code: 'SAMPLE_ROADMAP_ERROR',
          message: 'Failed to generate sample roadmap',
          details: error instanceof Error ? error.message : 'Unknown error occurred'
        },
        timestamp: new Date().toISOString(),
        requestId: res.locals.requestId
      });
    }
  }
);

/**
 * @route POST /api/roadmap/generate/:assessmentId
 * @desc Generate comprehensive transformation roadmap
 * @access Public (demo mode)
 */
router.post(
  '/generate/:assessmentId',
  roadmapRateLimit,
  validateRoadmapRequest,
  handleValidationErrors,
  async (req: Request, res: Response) => {
    try {
      const { assessmentId } = req.params;
      const roadmap = MockRoadmapService.generateComprehensiveRoadmap(assessmentId);

      res.json({
        success: true,
        data: {
          roadmap,
          message: 'Transformation roadmap generated successfully',
          generationTime: new Date().toISOString()
        },
        timestamp: new Date().toISOString(),
        requestId: res.locals.requestId
      });

    } catch (error) {
      console.error('Error generating roadmap:', error);
      res.status(500).json({
        success: false,
        error: {
          code: 'ROADMAP_GENERATION_ERROR',
          message: 'Failed to generate transformation roadmap',
          details: error instanceof Error ? error.message : 'Unknown error occurred'
        },
        timestamp: new Date().toISOString(),
        requestId: res.locals.requestId
      });
    }
  }
);

/**
 * @route GET /api/roadmap/:roadmapId
 * @desc Get roadmap by ID
 * @access Public (demo mode)
 */
router.get(
  '/:roadmapId',
  roadmapRateLimit,
  [
    param('roadmapId')
      .notEmpty()
      .withMessage('Roadmap ID is required')
  ],
  handleValidationErrors,
  async (req: Request, res: Response) => {
    try {
      const { roadmapId } = req.params;
      const roadmap = MockRoadmapService.getRoadmapById(roadmapId);

      if (!roadmap) {
        return res.status(404).json({
          success: false,
          error: {
            code: 'ROADMAP_NOT_FOUND',
            message: `Roadmap not found: ${roadmapId}`,
            details: `No roadmap exists with ID: ${roadmapId}`
          },
          timestamp: new Date().toISOString(),
          requestId: res.locals.requestId
        });
      }

      res.json({
        success: true,
        data: roadmap,
        timestamp: new Date().toISOString(),
        requestId: res.locals.requestId
      });

    } catch (error) {
      console.error('Error retrieving roadmap:', error);
      res.status(500).json({
        success: false,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to retrieve roadmap',
          details: error instanceof Error ? error.message : 'Unknown error occurred'
        },
        timestamp: new Date().toISOString(),
        requestId: res.locals.requestId
      });
    }
  }
);

/**
 * @route PUT /api/roadmap/:roadmapId/milestones/:milestoneId
 * @desc Update milestone status and progress
 * @access Public (demo mode)
 */
router.put(
  '/:roadmapId/milestones/:milestoneId',
  roadmapRateLimit,
  validateMilestoneUpdate,
  handleValidationErrors,
  async (req: Request, res: Response) => {
    try {
      const { roadmapId, milestoneId } = req.params;
      const updates = req.body;

      const updatedMilestone = MockRoadmapService.updateMilestone(roadmapId, milestoneId, updates);

      if (!updatedMilestone) {
        return res.status(404).json({
          success: false,
          error: {
            code: 'MILESTONE_NOT_FOUND',
            message: `Milestone not found: ${milestoneId}`,
            details: `No milestone exists with ID: ${milestoneId} in roadmap: ${roadmapId}`
          },
          timestamp: new Date().toISOString(),
          requestId: res.locals.requestId
        });
      }

      res.json({
        success: true,
        data: {
          milestone: updatedMilestone,
          message: 'Milestone updated successfully'
        },
        timestamp: new Date().toISOString(),
        requestId: res.locals.requestId
      });

    } catch (error) {
      console.error('Error updating milestone:', error);
      res.status(500).json({
        success: false,
        error: {
          code: 'MILESTONE_UPDATE_ERROR',
          message: 'Failed to update milestone',
          details: error instanceof Error ? error.message : 'Unknown error occurred'
        },
        timestamp: new Date().toISOString(),
        requestId: res.locals.requestId
      });
    }
  }
);

/**
 * @route GET /api/roadmap/:roadmapId/resources
 * @desc Get resource allocation and planning data
 * @access Public (demo mode)
 */
router.get(
  '/:roadmapId/resources',
  roadmapRateLimit,
  [
    param('roadmapId')
      .notEmpty()
      .withMessage('Roadmap ID is required')
  ],
  handleValidationErrors,
  async (req: Request, res: Response) => {
    try {
      const { roadmapId } = req.params;
      const resourceAllocation = MockRoadmapService.getResourceAllocation(roadmapId);

      if (!resourceAllocation) {
        return res.status(404).json({
          success: false,
          error: {
            code: 'ROADMAP_NOT_FOUND',
            message: `Roadmap not found: ${roadmapId}`,
            details: `No roadmap exists with ID: ${roadmapId}`
          },
          timestamp: new Date().toISOString(),
          requestId: res.locals.requestId
        });
      }

      res.json({
        success: true,
        data: resourceAllocation,
        timestamp: new Date().toISOString(),
        requestId: res.locals.requestId
      });

    } catch (error) {
      console.error('Error retrieving resource allocation:', error);
      res.status(500).json({
        success: false,
        error: {
          code: 'RESOURCE_ALLOCATION_ERROR',
          message: 'Failed to retrieve resource allocation',
          details: error instanceof Error ? error.message : 'Unknown error occurred'
        },
        timestamp: new Date().toISOString(),
        requestId: res.locals.requestId
      });
    }
  }
);

/**
 * @route GET /api/roadmap/:roadmapId/export
 * @desc Export roadmap to various project management formats
 * @access Public (demo mode)
 */
router.get(
  '/:roadmapId/export',
  roadmapRateLimit,
  validateExportRequest,
  handleValidationErrors,
  async (req: Request, res: Response) => {
    try {
      const { roadmapId } = req.params;
      const { format } = req.query as { format: 'MS_PROJECT' | 'JIRA' | 'ASANA' | 'EXCEL' | 'PDF' | 'POWERPOINT' };

      if (['PDF', 'POWERPOINT'].includes(format)) {
        // For PDF and PowerPoint, we'll generate download URLs
        const roadmap = MockRoadmapService.getRoadmapById(roadmapId);
        if (!roadmap) {
          return res.status(404).json({
            success: false,
            error: {
              code: 'ROADMAP_NOT_FOUND',
              message: `Roadmap not found: ${roadmapId}`,
            },
            timestamp: new Date().toISOString(),
            requestId: res.locals.requestId
          });
        }

        res.json({
          success: true,
          data: {
            format,
            downloadUrl: `/api/roadmap/${roadmapId}/download/${format.toLowerCase()}`,
            fileName: `${roadmap.title.replace(/\s+/g, '_')}_roadmap.${format === 'PDF' ? 'pdf' : 'pptx'}`,
            expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString() // 24 hours
          },
          timestamp: new Date().toISOString(),
          requestId: res.locals.requestId
        });
      } else {
        // For project management formats, return structured data
        const exportData = MockRoadmapService.generateProjectExport(roadmapId, format);

        if (!exportData) {
          return res.status(404).json({
            success: false,
            error: {
              code: 'EXPORT_GENERATION_ERROR',
              message: `Failed to generate export for roadmap: ${roadmapId}`,
            },
            timestamp: new Date().toISOString(),
            requestId: res.locals.requestId
          });
        }

        res.json({
          success: true,
          data: {
            format,
            exportData,
            instructions: {
              MS_PROJECT: 'Import the XML data into Microsoft Project',
              JIRA: 'Use the epic and story structure to create Jira items',
              EXCEL: 'Import the sheet data into Excel workbook',
              ASANA: 'Create projects and tasks using the provided structure'
            }[format]
          },
          timestamp: new Date().toISOString(),
          requestId: res.locals.requestId
        });
      }

    } catch (error) {
      console.error('Error exporting roadmap:', error);
      res.status(500).json({
        success: false,
        error: {
          code: 'EXPORT_ERROR',
          message: 'Failed to export roadmap',
          details: error instanceof Error ? error.message : 'Unknown error occurred'
        },
        timestamp: new Date().toISOString(),
        requestId: res.locals.requestId
      });
    }
  }
);

/**
 * @route GET /api/roadmap/:roadmapId/timeline
 * @desc Get timeline view with critical path
 * @access Public (demo mode)
 */
router.get(
  '/:roadmapId/timeline',
  roadmapRateLimit,
  [
    param('roadmapId')
      .notEmpty()
      .withMessage('Roadmap ID is required')
  ],
  handleValidationErrors,
  async (req: Request, res: Response) => {
    try {
      const { roadmapId } = req.params;
      const roadmap = MockRoadmapService.getRoadmapById(roadmapId);

      if (!roadmap) {
        return res.status(404).json({
          success: false,
          error: {
            code: 'ROADMAP_NOT_FOUND',
            message: `Roadmap not found: ${roadmapId}`,
          },
          timestamp: new Date().toISOString(),
          requestId: res.locals.requestId
        });
      }

      // Generate timeline view optimized for visualization
      const timeline = {
        projectStart: roadmap.startDate,
        projectEnd: roadmap.endDate,
        totalDuration: roadmap.totalDuration,
        phases: roadmap.phases.map(phase => ({
          id: phase.id,
          name: phase.name,
          startDate: phase.startDate,
          endDate: phase.endDate,
          duration: phase.duration,
          status: phase.status,
          criticalPath: phase.criticalPath,
          progress: phase.milestones.reduce((sum, m) => sum + m.completionPercentage, 0) / phase.milestones.length,
          milestones: phase.milestones.map(milestone => ({
            id: milestone.id,
            title: milestone.title,
            startDate: milestone.startDate,
            endDate: milestone.endDate,
            status: milestone.status,
            priority: milestone.priority,
            completionPercentage: milestone.completionPercentage,
            dependencies: milestone.dependencies
          }))
        })),
        criticalPath: roadmap.phases
          .filter(p => p.criticalPath)
          .flatMap(p => p.milestones)
          .map(m => ({ id: m.id, title: m.title, startDate: m.startDate, endDate: m.endDate })),
        dependencies: roadmap.dependencies
      };

      res.json({
        success: true,
        data: timeline,
        timestamp: new Date().toISOString(),
        requestId: res.locals.requestId
      });

    } catch (error) {
      console.error('Error retrieving timeline:', error);
      res.status(500).json({
        success: false,
        error: {
          code: 'TIMELINE_ERROR',
          message: 'Failed to retrieve timeline',
          details: error instanceof Error ? error.message : 'Unknown error occurred'
        },
        timestamp: new Date().toISOString(),
        requestId: res.locals.requestId
      });
    }
  }
);

/**
 * @route GET /api/roadmap/:roadmapId/summary
 * @desc Get executive summary and business case
 * @access Public (demo mode)
 */
router.get(
  '/:roadmapId/summary',
  roadmapRateLimit,
  [
    param('roadmapId')
      .notEmpty()
      .withMessage('Roadmap ID is required')
  ],
  handleValidationErrors,
  async (req: Request, res: Response) => {
    try {
      const { roadmapId } = req.params;
      const roadmap = MockRoadmapService.getRoadmapById(roadmapId);

      if (!roadmap) {
        return res.status(404).json({
          success: false,
          error: {
            code: 'ROADMAP_NOT_FOUND',
            message: `Roadmap not found: ${roadmapId}`,
          },
          timestamp: new Date().toISOString(),
          requestId: res.locals.requestId
        });
      }

      const summary = {
        title: roadmap.title,
        executiveSummary: roadmap.executiveSummary,
        businessCase: roadmap.businessCase,
        keyObjectives: roadmap.keyObjectives,
        successMetrics: roadmap.successMetrics,
        investment: {
          totalBudget: roadmap.totalBudget,
          duration: roadmap.totalDuration,
          teamSize: roadmap.totalTeamSize,
          roi: roadmap.businessCase.roi,
          paybackPeriod: roadmap.businessCase.paybackPeriod
        },
        riskSummary: {
          totalRisks: roadmap.risks.length,
          highRisks: roadmap.risks.filter(r => r.impact === 'HIGH' || r.impact === 'CRITICAL').length,
          topRisks: roadmap.risks.slice(0, 3)
        }
      };

      res.json({
        success: true,
        data: summary,
        timestamp: new Date().toISOString(),
        requestId: res.locals.requestId
      });

    } catch (error) {
      console.error('Error retrieving summary:', error);
      res.status(500).json({
        success: false,
        error: {
          code: 'SUMMARY_ERROR',
          message: 'Failed to retrieve roadmap summary',
          details: error instanceof Error ? error.message : 'Unknown error occurred'
        },
        timestamp: new Date().toISOString(),
        requestId: res.locals.requestId
      });
    }
  }
);

export default router;