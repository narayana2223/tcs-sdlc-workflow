/**
 * Analysis controller for handling repository analysis requests
 * Orchestrates analysis workflow and provides API responses
 */

import {
  AnalysisRequest,
  AnalysisResponse,
  AnalysisStatusResponse,
  AnalysisResultsResponse,
  AnalysisError,
  AnalysisNotFoundError,
  estimateAnalysisTime,
} from '../models/analysis_model';
import { AnalysisService } from '../services/analysis_service';
import { MockAnalysisService } from '../services/mock_analysis_service';

export class AnalysisController {
  private analysisService: AnalysisService;
  private useMockService: boolean;
  private mockJobs: Map<string, any> = new Map();

  constructor() {
    this.analysisService = new AnalysisService();
    // Use mock service for demo purposes when analysis engine is not available
    this.useMockService = process.env.USE_MOCK_ANALYSIS === 'true';
  }

  /**
   * Start a new repository analysis
   */
  async startAnalysis(
    request: AnalysisRequest,
    userId: string,
    requestId: string,
    metadata: { userAgent?: string; ipAddress?: string }
  ): Promise<AnalysisResponse> {
    try {
      if (this.useMockService) {
        // Use mock service for demo purposes
        const mockResult = MockAnalysisService.generateMockAnalysis(request.repositoryUrl);
        const jobId = mockResult.jobId;

        // Store mock job with progress simulation
        const mockJob = {
          id: jobId,
          repositoryUrl: request.repositoryUrl,
          branchName: request.branchName || 'main',
          analysisType: request.analysisType,
          status: 'processing' as const,
          progress: 0,
          createdAt: new Date(),
          startedAt: new Date(),
          userId,
          options: request.options,
          result: mockResult
        };

        this.mockJobs.set(jobId, mockJob);

        // Simulate analysis progress
        this.simulateMockAnalysis(jobId);

        const estimatedTime = estimateAnalysisTime(request.analysisType, request.options || {});
        const estimatedCompletion = new Date(Date.now() + estimatedTime * 60 * 1000).toISOString();

        return {
          success: true,
          data: {
            jobId,
            status: 'processing',
            message: 'Analysis started successfully',
            estimatedCompletionTime: estimatedCompletion,
          },
          timestamp: new Date().toISOString(),
          requestId,
        };
      }

      const job = await this.analysisService.startAnalysis(request, userId, requestId, metadata);

      const estimatedTime = estimateAnalysisTime(request.analysisType, request.options || {});
      const estimatedCompletion = new Date(Date.now() + estimatedTime * 60 * 1000).toISOString();

      return {
        success: true,
        data: {
          jobId: job.id,
          status: job.status,
          message: 'Analysis started successfully',
          estimatedCompletionTime: estimatedCompletion,
        },
        timestamp: new Date().toISOString(),
        requestId,
      };

    } catch (error) {
      console.error('Error starting analysis:', error);
      
      if (error instanceof AnalysisError) {
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
          message: 'Failed to start analysis',
          details: process.env.NODE_ENV === 'development' ? error : undefined,
        },
        timestamp: new Date().toISOString(),
        requestId,
      };
    }
  }

  /**
   * Get analysis job status
   */
  async getAnalysisStatus(
    jobId: string,
    userId: string,
    requestId: string
  ): Promise<AnalysisStatusResponse> {
    try {
      if (this.useMockService) {
        // Handle mock job status
        const mockJob = this.mockJobs.get(jobId);
        if (!mockJob) {
          throw new AnalysisNotFoundError(jobId);
        }

        let estimatedCompletionTime: string | undefined;
        if (mockJob.status === 'processing' && mockJob.startedAt) {
          const estimatedDuration = estimateAnalysisTime(mockJob.analysisType, mockJob.options);
          const elapsedMinutes = (Date.now() - mockJob.startedAt.getTime()) / (1000 * 60);
          const remainingMinutes = Math.max(0, estimatedDuration - elapsedMinutes);
          estimatedCompletionTime = new Date(Date.now() + remainingMinutes * 60 * 1000).toISOString();
        }

        return {
          success: true,
          data: {
            jobId: mockJob.id,
            status: mockJob.status,
            progress: mockJob.progress,
            message: this.getStatusMessage(mockJob.status, mockJob.progress),
            createdAt: mockJob.createdAt.toISOString(),
            startedAt: mockJob.startedAt?.toISOString(),
            completedAt: mockJob.completedAt?.toISOString(),
            estimatedCompletionTime,
            error: mockJob.error,
          },
          timestamp: new Date().toISOString(),
          requestId,
        };
      }

      const job = this.analysisService.getAnalysisStatus(jobId, userId);

      if (!job) {
        throw new AnalysisNotFoundError(jobId);
      }

      let estimatedCompletionTime: string | undefined;
      if (job.status === 'processing' && job.startedAt) {
        const estimatedDuration = estimateAnalysisTime(job.analysisType, job.options);
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
      console.error('Error getting analysis status:', error);

      if (error instanceof AnalysisError) {
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
          message: 'Failed to get analysis status',
        },
        timestamp: new Date().toISOString(),
        requestId,
      };
    }
  }

  /**
   * Get analysis results
   */
  async getAnalysisResults(
    jobId: string,
    userId: string,
    requestId: string,
    options: { includeMetadata?: boolean; format?: string } = {}
  ): Promise<AnalysisResultsResponse> {
    try {
      if (this.useMockService) {
        // Handle mock job results
        const mockJob = this.mockJobs.get(jobId);
        if (!mockJob) {
          throw new AnalysisNotFoundError(jobId);
        }

        if (mockJob.status !== 'completed') {
          throw new AnalysisError(
            `Analysis not completed. Current status: ${mockJob.status}`,
            400,
            'ANALYSIS_NOT_COMPLETE'
          );
        }

        const analysisTime = mockJob.completedAt && mockJob.startedAt
          ? (mockJob.completedAt.getTime() - mockJob.startedAt.getTime()) / 1000
          : 0;

        return {
          success: true,
          data: {
            jobId: mockJob.id,
            status: mockJob.status,
            results: mockJob.result.results,
            ...(options.includeMetadata && {
              metadata: {
                analysisTime: Math.round(analysisTime),
                linesAnalyzed: mockJob.result.results.analysis.totalLinesOfCode,
                filesAnalyzed: mockJob.result.results.analysis.totalFiles,
                cacheHit: false,
              },
            }),
          },
          timestamp: new Date().toISOString(),
          requestId,
        };
      }

      const job = this.analysisService.getAnalysisStatus(jobId, userId);

      if (!job) {
        throw new AnalysisNotFoundError(jobId);
      }

      if (job.status !== 'completed') {
        throw new AnalysisError(
          `Analysis not completed. Current status: ${job.status}`,
          400,
          'ANALYSIS_NOT_COMPLETE'
        );
      }

      if (!job.results) {
        throw new AnalysisError('Analysis results not found', 404, 'RESULTS_NOT_FOUND');
      }

      const analysisTime = job.completedAt && job.startedAt
        ? Math.round((job.completedAt.getTime() - job.startedAt.getTime()) / 1000)
        : 0;

      const metadata = {
        analysisTime,
        linesAnalyzed: job.results.code_analysis.project_metrics?.total_lines_of_code || 0,
        filesAnalyzed: job.results.code_analysis.project_metrics?.total_files || 0,
        cacheHit: false, // Would be determined by analysis engine
      };

      return {
        success: true,
        data: {
          jobId: job.id,
          status: job.status,
          results: job.results,
          metadata,
        },
        timestamp: new Date().toISOString(),
        requestId,
      };

    } catch (error) {
      console.error('Error getting analysis results:', error);

      if (error instanceof AnalysisError) {
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
          message: 'Failed to get analysis results',
        },
        timestamp: new Date().toISOString(),
        requestId,
      };
    }
  }

  /**
   * Get user's analysis jobs
   */
  async getUserAnalyses(
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
      const { jobs, total } = this.analysisService.getUserAnalyses(userId, filters);

      // Transform jobs for response
      const transformedJobs = jobs.map(job => ({
        id: job.id,
        repositoryUrl: job.repositoryUrl,
        branchName: job.branchName,
        analysisType: job.analysisType,
        status: job.status,
        progress: job.progress,
        createdAt: job.createdAt.toISOString(),
        startedAt: job.startedAt?.toISOString(),
        completedAt: job.completedAt?.toISOString(),
        error: job.error,
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
      console.error('Error getting user analyses:', error);

      return {
        success: false,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to get user analyses',
        },
        timestamp: new Date().toISOString(),
        requestId,
      };
    }
  }

  /**
   * Cancel analysis job
   */
  async cancelAnalysis(
    jobId: string,
    userId: string,
    force: boolean,
    requestId: string
  ): Promise<any> {
    try {
      const cancelled = await this.analysisService.cancelAnalysis(jobId, userId, force);

      if (!cancelled) {
        throw new AnalysisNotFoundError(jobId);
      }

      return {
        success: true,
        data: {
          jobId,
          status: 'cancelled',
          message: 'Analysis cancelled successfully',
        },
        timestamp: new Date().toISOString(),
        requestId,
      };

    } catch (error) {
      console.error('Error cancelling analysis:', error);

      if (error instanceof AnalysisError) {
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
          message: 'Failed to cancel analysis',
        },
        timestamp: new Date().toISOString(),
        requestId,
      };
    }
  }

  /**
   * Restart failed analysis
   */
  async restartAnalysis(
    jobId: string,
    userId: string,
    requestId: string
  ): Promise<any> {
    try {
      const job = this.analysisService.getAnalysisStatus(jobId, userId);

      if (!job) {
        throw new AnalysisNotFoundError(jobId);
      }

      if (job.status !== 'failed') {
        throw new AnalysisError(
          `Cannot restart analysis with status: ${job.status}`,
          400,
          'INVALID_STATUS'
        );
      }

      // Create new analysis with same parameters
      const newJob = await this.analysisService.startAnalysis(
        {
          repositoryUrl: job.repositoryUrl,
          branchName: job.branchName,
          analysisType: job.analysisType,
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
          message: 'Analysis restarted successfully',
        },
        timestamp: new Date().toISOString(),
        requestId,
      };

    } catch (error) {
      console.error('Error restarting analysis:', error);

      if (error instanceof AnalysisError) {
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
          message: 'Failed to restart analysis',
        },
        timestamp: new Date().toISOString(),
        requestId,
      };
    }
  }

  /**
   * Validate repository
   */
  async validateRepository(repositoryUrl: string, requestId: string): Promise<any> {
    try {
      const validation = await this.analysisService.validateRepository(repositoryUrl);

      return {
        success: true,
        data: {
          repositoryUrl,
          accessible: validation.accessible,
          error: validation.error,
          message: validation.accessible 
            ? 'Repository is accessible'
            : validation.error || 'Repository not accessible',
        },
        timestamp: new Date().toISOString(),
        requestId,
      };

    } catch (error) {
      console.error('Error validating repository:', error);

      if (error instanceof AnalysisError) {
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
          message: 'Failed to validate repository',
        },
        timestamp: new Date().toISOString(),
        requestId,
      };
    }
  }

  /**
   * Get analysis statistics
   */
  async getAnalysisStatistics(
    userId: string,
    period: string,
    requestId: string
  ): Promise<any> {
    try {
      const stats = this.analysisService.getAnalysisStatistics(userId, period);

      return {
        success: true,
        data: {
          period,
          statistics: stats,
          summary: {
            success_rate: stats.total_analyses > 0 
              ? Math.round((stats.completed / stats.total_analyses) * 100)
              : 0,
            most_common_analysis_type: this.getMostCommonAnalysisType(stats.analysis_types),
            average_completion_time_minutes: Math.round(stats.average_completion_time / 60),
          },
        },
        timestamp: new Date().toISOString(),
        requestId,
      };

    } catch (error) {
      console.error('Error getting analysis statistics:', error);

      return {
        success: false,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to get analysis statistics',
        },
        timestamp: new Date().toISOString(),
        requestId,
      };
    }
  }

  /**
   * Get analysis logs (placeholder for debugging)
   */
  async getAnalysisLogs(
    jobId: string,
    userId: string,
    options: { level?: string; limit: number },
    requestId: string
  ): Promise<any> {
    try {
      const job = this.analysisService.getAnalysisStatus(jobId, userId);

      if (!job) {
        throw new AnalysisNotFoundError(jobId);
      }

      // In a real implementation, this would fetch logs from storage
      const mockLogs = [
        {
          timestamp: job.createdAt.toISOString(),
          level: 'info',
          message: 'Analysis job created',
        },
        {
          timestamp: job.startedAt?.toISOString() || job.createdAt.toISOString(),
          level: 'info',
          message: 'Analysis started',
        },
      ];

      if (job.error) {
        mockLogs.push({
          timestamp: job.completedAt?.toISOString() || new Date().toISOString(),
          level: 'error',
          message: job.error,
        });
      } else if (job.completedAt) {
        mockLogs.push({
          timestamp: job.completedAt.toISOString(),
          level: 'info',
          message: 'Analysis completed successfully',
        });
      }

      const filteredLogs = options.level
        ? mockLogs.filter(log => log.level === options.level)
        : mockLogs;

      return {
        success: true,
        data: {
          jobId,
          logs: filteredLogs.slice(0, options.limit),
          total: filteredLogs.length,
        },
        timestamp: new Date().toISOString(),
        requestId,
      };

    } catch (error) {
      console.error('Error getting analysis logs:', error);

      if (error instanceof AnalysisError) {
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
          message: 'Failed to get analysis logs',
        },
        timestamp: new Date().toISOString(),
        requestId,
      };
    }
  }

  /**
   * Simulate analysis progress for mock jobs
   */
  private simulateMockAnalysis(jobId: string): void {
    const mockJob = this.mockJobs.get(jobId);
    if (!mockJob) return;

    MockAnalysisService.simulateAnalysisProgress((progress, message) => {
      const job = this.mockJobs.get(jobId);
      if (job) {
        job.progress = progress;
        job.currentStep = message;

        if (progress >= 100) {
          job.status = 'completed';
          job.completedAt = new Date();
        }
      }
    });
  }

  /**
   * Helper methods
   */
  private getStatusMessage(status: string, progress: number): string {
    switch (status) {
      case 'pending':
        return 'Analysis queued for processing';
      case 'processing':
        if (progress < 20) return 'Initializing analysis...';
        if (progress < 40) return 'Cloning repository...';
        if (progress < 60) return 'Analyzing code structure...';
        if (progress < 80) return 'Processing dependencies...';
        if (progress < 95) return 'Generating recommendations...';
        return 'Finalizing results...';
      case 'completed':
        return 'Analysis completed successfully';
      case 'failed':
        return 'Analysis failed';
      case 'cancelled':
        return 'Analysis was cancelled';
      default:
        return 'Unknown status';
    }
  }

  private getMostCommonAnalysisType(analysisTypes: { [key: string]: number }): string {
    let maxCount = 0;
    let mostCommon = 'full';

    for (const [type, count] of Object.entries(analysisTypes)) {
      if (count > maxCount) {
        maxCount = count;
        mostCommon = type;
      }
    }

    return mostCommon;
  }
}

// Export a singleton instance
export const analysisController = new AnalysisController();