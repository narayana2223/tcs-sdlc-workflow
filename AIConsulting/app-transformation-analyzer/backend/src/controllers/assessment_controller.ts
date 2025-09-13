/**
 * Assessment controller for handling 12-factor assessment requests
 * Orchestrates assessment workflow and provides API responses
 */

import {
  AssessmentRequest,
  AssessmentResponse,
  AssessmentStatusResponse,
  AssessmentResultsResponse,
  AssessmentError,
  AssessmentNotFoundError,
  TWELVE_FACTOR_DEFINITIONS,
  estimateAssessmentTime,
} from '../models/assessment_model';
import { AssessmentService } from '../services/assessment_service';
import { AnalysisService } from '../services/analysis_service';

export class AssessmentController {
  private assessmentService: AssessmentService;
  private analysisService: AnalysisService;

  constructor() {
    this.analysisService = new AnalysisService();
    this.assessmentService = new AssessmentService(this.analysisService);
  }

  /**
   * Start a new 12-factor assessment
   */
  async startAssessment(
    request: AssessmentRequest,
    userId: string,
    requestId: string,
    metadata: { userAgent?: string; ipAddress?: string }
  ): Promise<AssessmentResponse> {
    try {
      const job = await this.assessmentService.startAssessment(request, userId, requestId, metadata);
      
      const estimatedTime = estimateAssessmentTime(request.options || {});
      const estimatedCompletion = new Date(Date.now() + estimatedTime * 60 * 1000).toISOString();

      return {
        success: true,
        data: {
          jobId: job.id,
          status: job.status,
          message: '12-factor assessment started successfully',
          estimatedCompletionTime: estimatedCompletion,
        },
        timestamp: new Date().toISOString(),
        requestId,
      };

    } catch (error) {
      console.error('Error starting assessment:', error);
      
      if (error instanceof AssessmentError) {
        return {
          success: false,
          error: {
            code: error.code,
            message: error.message,
            details: error.statusCode >= 500 ? undefined : error.message,
          },
          timestamp: new Date().toISOString(),
          requestId,
        };
      }

      return {
        success: false,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to start assessment',
          details: process.env.NODE_ENV === 'development' ? error : undefined,
        },
        timestamp: new Date().toISOString(),
        requestId,
      };
    }
  }

  /**
   * Get assessment job status
   */
  async getAssessmentStatus(
    jobId: string,
    userId: string,
    requestId: string
  ): Promise<AssessmentStatusResponse> {
    try {
      const job = this.assessmentService.getAssessmentStatus(jobId, userId);

      if (!job) {
        throw new AssessmentNotFoundError(jobId);
      }

      let estimatedCompletionTime: string | undefined;
      if (job.status === 'processing' && job.startedAt) {
        const estimatedDuration = estimateAssessmentTime(job.options);
        const elapsedMinutes = (Date.now() - job.startedAt.getTime()) / (1000 * 60);
        const remainingMinutes = Math.max(0, estimatedDuration - elapsedMinutes);
        estimatedCompletionTime = new Date(Date.now() + remainingMinutes * 60 * 1000).toISOString();
      }

      return {
        success: true,
        data: {
          jobId: job.id,
          status: job.status,
          progress: job.progress,
          message: this.getStatusMessage(job.status, job.progress),
          createdAt: job.createdAt.toISOString(),
          startedAt: job.startedAt?.toISOString(),
          completedAt: job.completedAt?.toISOString(),
          estimatedCompletionTime,
          error: job.error,
        },
        timestamp: new Date().toISOString(),
        requestId,
      };

    } catch (error) {
      console.error('Error getting assessment status:', error);

      if (error instanceof AssessmentError) {
        return {
          success: false,
          error: {
            code: error.code,
            message: error.message,
          },
          timestamp: new Date().toISOString(),
          requestId,
        };
      }

      return {
        success: false,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to get assessment status',
        },
        timestamp: new Date().toISOString(),
        requestId,
      };
    }
  }

  /**
   * Get assessment results
   */
  async getAssessmentResults(
    jobId: string,
    userId: string,
    options: { format?: string; includeRoadmap?: boolean; includeSummary?: boolean },
    requestId: string
  ): Promise<AssessmentResultsResponse> {
    try {
      const job = this.assessmentService.getAssessmentStatus(jobId, userId);

      if (!job) {
        throw new AssessmentNotFoundError(jobId);
      }

      if (job.status !== 'completed') {
        throw new AssessmentError(
          `Assessment not completed. Current status: ${job.status}`,
          400,
          'ASSESSMENT_NOT_COMPLETE'
        );
      }

      if (!job.results) {
        throw new AssessmentError('Assessment results not found', 404, 'RESULTS_NOT_FOUND');
      }

      const assessmentTime = job.completedAt && job.startedAt
        ? Math.round((job.completedAt.getTime() - job.startedAt.getTime()) / 1000)
        : 0;

      // Generate summary if requested
      const summary = options.includeSummary ? this.generateAssessmentSummary(job.results) : undefined;
      
      // Generate roadmap if requested
      const roadmap = options.includeRoadmap ? this.generateImplementationRoadmap(job.results) : undefined;

      const metadata = {
        assessmentTime,
        factorsEvaluated: Object.keys(job.results.factor_evaluations).length,
        evidenceCount: Object.values(job.results.factor_evaluations).reduce(
          (total, factor) => total + factor.evidence.length, 0
        ),
      };

      return {
        success: true,
        data: {
          jobId: job.id,
          status: job.status,
          assessment: job.results,
          summary,
          roadmap,
          metadata,
        },
        timestamp: new Date().toISOString(),
        requestId,
      };

    } catch (error) {
      console.error('Error getting assessment results:', error);

      if (error instanceof AssessmentError) {
        return {
          success: false,
          error: {
            code: error.code,
            message: error.message,
          },
          timestamp: new Date().toISOString(),
          requestId,
        };
      }

      return {
        success: false,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to get assessment results',
        },
        timestamp: new Date().toISOString(),
        requestId,
      };
    }
  }

  /**
   * Get user's assessment jobs
   */
  async getUserAssessments(
    userId: string,
    filters: {
      status?: string;
      limit: number;
      offset: number;
      sortBy: string;
      sortOrder: string;
    },
    requestId: string
  ): Promise<any> {
    try {
      const { jobs, total } = this.assessmentService.getUserAssessments(userId, filters);

      // Transform jobs for response
      const transformedJobs = jobs.map(job => ({
        id: job.id,
        analysisJobId: job.analysisJobId,
        repositoryUrl: job.repositoryUrl,
        status: job.status,
        progress: job.progress,
        createdAt: job.createdAt.toISOString(),
        startedAt: job.startedAt?.toISOString(),
        completedAt: job.completedAt?.toISOString(),
        error: job.error,
        grade: job.results?.grade,
        overall_score: job.results?.overall_score,
        hasResults: !!job.results,
      }));

      return {
        success: true,
        data: {
          jobs: transformedJobs,
          pagination: {
            total,
            limit: filters.limit,
            offset: filters.offset,
            hasMore: filters.offset + filters.limit < total,
          },
        },
        timestamp: new Date().toISOString(),
        requestId,
      };

    } catch (error) {
      console.error('Error getting user assessments:', error);

      return {
        success: false,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to get user assessments',
        },
        timestamp: new Date().toISOString(),
        requestId,
      };
    }
  }

  /**
   * Cancel assessment job
   */
  async cancelAssessment(
    jobId: string,
    userId: string,
    force: boolean,
    requestId: string
  ): Promise<any> {
    try {
      const cancelled = await this.assessmentService.cancelAssessment(jobId, userId, force);

      if (!cancelled) {
        throw new AssessmentNotFoundError(jobId);
      }

      return {
        success: true,
        data: {
          jobId,
          status: 'cancelled',
          message: 'Assessment cancelled successfully',
        },
        timestamp: new Date().toISOString(),
        requestId,
      };

    } catch (error) {
      console.error('Error cancelling assessment:', error);

      if (error instanceof AssessmentError) {
        return {
          success: false,
          error: {
            code: error.code,
            message: error.message,
          },
          timestamp: new Date().toISOString(),
          requestId,
        };
      }

      return {
        success: false,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to cancel assessment',
        },
        timestamp: new Date().toISOString(),
        requestId,
      };
    }
  }

  /**
   * Compare two assessments
   */
  async compareAssessments(
    currentAssessmentId: string,
    previousAssessmentId: string,
    userId: string,
    requestId: string
  ): Promise<any> {
    try {
      const comparison = this.assessmentService.compareAssessments(
        currentAssessmentId,
        previousAssessmentId,
        userId
      );

      return {
        success: true,
        data: {
          comparison,
          message: 'Assessment comparison completed',
        },
        timestamp: new Date().toISOString(),
        requestId,
      };

    } catch (error) {
      console.error('Error comparing assessments:', error);

      if (error instanceof AssessmentError) {
        return {
          success: false,
          error: {
            code: error.code,
            message: error.message,
          },
          timestamp: new Date().toISOString(),
          requestId,
        };
      }

      return {
        success: false,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to compare assessments',
        },
        timestamp: new Date().toISOString(),
        requestId,
      };
    }
  }

  /**
   * Get factor evaluations with filtering
   */
  async getFactorEvaluations(
    jobId: string,
    userId: string,
    filters: {
      factorName?: string;
      includeEvidence: boolean;
      minScore?: number;
      maxScore?: number;
    },
    requestId: string
  ): Promise<any> {
    try {
      const job = this.assessmentService.getAssessmentStatus(jobId, userId);

      if (!job || !job.results) {
        throw new AssessmentNotFoundError(jobId);
      }

      let factors = Object.entries(job.results.factor_evaluations);

      // Apply filters
      if (filters.factorName) {
        factors = factors.filter(([name]) => name === filters.factorName);
      }

      if (filters.minScore !== undefined) {
        factors = factors.filter(([, evaluation]) => evaluation.score >= filters.minScore!);
      }

      if (filters.maxScore !== undefined) {
        factors = factors.filter(([, evaluation]) => evaluation.score <= filters.maxScore!);
      }

      // Transform for response
      const transformedFactors = factors.map(([name, evaluation]) => ({
        factor_name: name,
        title: TWELVE_FACTOR_DEFINITIONS[name]?.title || name,
        score: evaluation.score,
        score_name: evaluation.score_name,
        reasoning: evaluation.score_reasoning,
        confidence: evaluation.confidence,
        weight: evaluation.weight,
        evidence: filters.includeEvidence ? evaluation.evidence : undefined,
      }));

      return {
        success: true,
        data: {
          jobId,
          factors: transformedFactors,
          total: transformedFactors.length,
        },
        timestamp: new Date().toISOString(),
        requestId,
      };

    } catch (error) {
      console.error('Error getting factor evaluations:', error);

      if (error instanceof AssessmentError) {
        return {
          success: false,
          error: {
            code: error.code,
            message: error.message,
          },
          timestamp: new Date().toISOString(),
          requestId,
        };
      }

      return {
        success: false,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to get factor evaluations',
        },
        timestamp: new Date().toISOString(),
        requestId,
      };
    }
  }

  /**
   * Get recommendations with filtering
   */
  async getRecommendations(
    jobId: string,
    userId: string,
    filters: {
      priority?: string;
      factorName?: string;
      complexity?: string;
      limit: number;
    },
    requestId: string
  ): Promise<any> {
    try {
      const job = this.assessmentService.getAssessmentStatus(jobId, userId);

      if (!job || !job.results) {
        throw new AssessmentNotFoundError(jobId);
      }

      let recommendations = job.results.recommendations;

      // Apply filters
      if (filters.priority) {
        recommendations = recommendations.filter(rec => rec.priority === filters.priority);
      }

      if (filters.factorName) {
        recommendations = recommendations.filter(rec => rec.factor_name === filters.factorName);
      }

      if (filters.complexity) {
        recommendations = recommendations.filter(rec => rec.complexity === filters.complexity);
      }

      // Apply limit
      recommendations = recommendations.slice(0, filters.limit);

      return {
        success: true,
        data: {
          jobId,
          recommendations,
          total: recommendations.length,
        },
        timestamp: new Date().toISOString(),
        requestId,
      };

    } catch (error) {
      console.error('Error getting recommendations:', error);

      if (error instanceof AssessmentError) {
        return {
          success: false,
          error: {
            code: error.code,
            message: error.message,
          },
          timestamp: new Date().toISOString(),
          requestId,
        };
      }

      return {
        success: false,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to get recommendations',
        },
        timestamp: new Date().toISOString(),
        requestId,
      };
    }
  }

  /**
   * Get implementation roadmap
   */
  async getImplementationRoadmap(
    jobId: string,
    userId: string,
    requestId: string
  ): Promise<any> {
    try {
      const job = this.assessmentService.getAssessmentStatus(jobId, userId);

      if (!job || !job.results) {
        throw new AssessmentNotFoundError(jobId);
      }

      const roadmap = this.generateImplementationRoadmap(job.results);

      return {
        success: true,
        data: {
          jobId,
          roadmap,
        },
        timestamp: new Date().toISOString(),
        requestId,
      };

    } catch (error) {
      console.error('Error getting implementation roadmap:', error);

      if (error instanceof AssessmentError) {
        return {
          success: false,
          error: {
            code: error.code,
            message: error.message,
          },
          timestamp: new Date().toISOString(),
          requestId,
        };
      }

      return {
        success: false,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to get implementation roadmap',
        },
        timestamp: new Date().toISOString(),
        requestId,
      };
    }
  }

  /**
   * Get assessment statistics
   */
  async getAssessmentStatistics(
    userId: string,
    period: string,
    requestId: string
  ): Promise<any> {
    try {
      const stats = this.assessmentService.getAssessmentStatistics(userId, period);

      return {
        success: true,
        data: {
          period,
          statistics: stats,
          summary: {
            success_rate: stats.total_assessments > 0 
              ? Math.round((stats.completed / stats.total_assessments) * 100)
              : 0,
            most_common_grade: this.getMostCommonGrade(stats.grade_distribution),
            average_score: Math.round(stats.average_score * 10) / 10,
            improvement_trend: this.calculateImprovementTrend(stats),
          },
        },
        timestamp: new Date().toISOString(),
        requestId,
      };

    } catch (error) {
      console.error('Error getting assessment statistics:', error);

      return {
        success: false,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to get assessment statistics',
        },
        timestamp: new Date().toISOString(),
        requestId,
      };
    }
  }

  /**
   * Get 12-factor definitions
   */
  async getTwelveFactorDefinitions(requestId: string): Promise<any> {
    try {
      return {
        success: true,
        data: {
          definitions: TWELVE_FACTOR_DEFINITIONS,
          total: Object.keys(TWELVE_FACTOR_DEFINITIONS).length,
        },
        timestamp: new Date().toISOString(),
        requestId,
      };

    } catch (error) {
      console.error('Error getting 12-factor definitions:', error);

      return {
        success: false,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to get 12-factor definitions',
        },
        timestamp: new Date().toISOString(),
        requestId,
      };
    }
  }

  /**
   * Restart failed assessment
   */
  async restartAssessment(
    jobId: string,
    userId: string,
    requestId: string
  ): Promise<any> {
    try {
      const job = this.assessmentService.getAssessmentStatus(jobId, userId);

      if (!job) {
        throw new AssessmentNotFoundError(jobId);
      }

      if (job.status !== 'failed') {
        throw new AssessmentError(
          `Cannot restart assessment with status: ${job.status}`,
          400,
          'INVALID_STATUS'
        );
      }

      // Create new assessment with same parameters
      const newJob = await this.assessmentService.startAssessment(
        {
          analysisJobId: job.analysisJobId,
          options: job.options,
        },
        userId,
        requestId,
        {
          userAgent: job.metadata.userAgent,
          ipAddress: job.metadata.ipAddress,
        }
      );

      return {
        success: true,
        data: {
          originalJobId: jobId,
          newJobId: newJob.id,
          status: newJob.status,
          message: 'Assessment restarted successfully',
        },
        timestamp: new Date().toISOString(),
        requestId,
      };

    } catch (error) {
      console.error('Error restarting assessment:', error);

      if (error instanceof AssessmentError) {
        return {
          success: false,
          error: {
            code: error.code,
            message: error.message,
          },
          timestamp: new Date().toISOString(),
          requestId,
        };
      }

      return {
        success: false,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to restart assessment',
        },
        timestamp: new Date().toISOString(),
        requestId,
      };
    }
  }

  /**
   * Get assessment summary
   */
  async getAssessmentSummary(
    jobId: string,
    userId: string,
    requestId: string
  ): Promise<any> {
    try {
      const job = this.assessmentService.getAssessmentStatus(jobId, userId);

      if (!job || !job.results) {
        throw new AssessmentNotFoundError(jobId);
      }

      const summary = this.generateAssessmentSummary(job.results);

      return {
        success: true,
        data: {
          jobId,
          summary,
        },
        timestamp: new Date().toISOString(),
        requestId,
      };

    } catch (error) {
      console.error('Error getting assessment summary:', error);

      if (error instanceof AssessmentError) {
        return {
          success: false,
          error: {
            code: error.code,
            message: error.message,
          },
          timestamp: new Date().toISOString(),
          requestId,
        };
      }

      return {
        success: false,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to get assessment summary',
        },
        timestamp: new Date().toISOString(),
        requestId,
      };
    }
  }

  /**
   * Helper methods
   */
  private getStatusMessage(status: string, progress: number): string {
    switch (status) {
      case 'pending':
        return 'Assessment queued for processing';
      case 'processing':
        if (progress < 20) return 'Initializing 12-factor assessment...';
        if (progress < 40) return 'Evaluating factor compliance...';
        if (progress < 60) return 'Analyzing code patterns...';
        if (progress < 80) return 'Identifying gaps and issues...';
        if (progress < 95) return 'Generating recommendations...';
        return 'Finalizing assessment results...';
      case 'completed':
        return '12-factor assessment completed successfully';
      case 'failed':
        return 'Assessment failed';
      case 'cancelled':
        return 'Assessment was cancelled';
      default:
        return 'Unknown status';
    }
  }

  private generateAssessmentSummary(assessment: any): any {
    // Implementation would generate comprehensive summary
    return {
      overview: {
        grade: assessment.grade,
        overall_score: assessment.overall_score,
        weighted_score: assessment.weighted_score,
        confidence: assessment.confidence,
        coverage: assessment.coverage,
      },
      // Additional summary logic would be implemented here
    };
  }

  private generateImplementationRoadmap(assessment: any): any {
    // Implementation would generate roadmap based on recommendations
    return {
      total_recommendations: assessment.recommendations.length,
      phases: {
        phase_1_immediate: {
          description: 'Critical fixes with immediate impact',
          timeline: '2-4 weeks',
          recommendations: [],
          count: 0,
        },
        // Additional phases would be generated here
      },
    };
  }

  private getMostCommonGrade(gradeDistribution: { [key: string]: number }): string {
    let maxCount = 0;
    let mostCommon = 'C';

    for (const [grade, count] of Object.entries(gradeDistribution)) {
      if (count > maxCount) {
        maxCount = count;
        mostCommon = grade;
      }
    }

    return mostCommon;
  }

  private calculateImprovementTrend(stats: any): string {
    // Simple implementation - would be more sophisticated in production
    if (stats.average_score >= 4) return 'excellent';
    if (stats.average_score >= 3) return 'improving';
    if (stats.average_score >= 2) return 'needs_work';
    return 'poor';
  }
}

// Export a singleton instance
export const assessmentController = new AssessmentController();