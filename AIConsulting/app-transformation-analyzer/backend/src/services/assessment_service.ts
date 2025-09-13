/**
 * Assessment service for handling 12-factor assessments
 * Communicates with the Python analysis engine to perform factor evaluations
 */

import { EventEmitter } from 'events';
import { v4 as uuidv4 } from 'uuid';
import { spawn, ChildProcess } from 'child_process';
import axios from 'axios';
import path from 'path';

import {
  AssessmentJob,
  AssessmentStatus,
  AssessmentRequest,
  TwelveFactorAssessment,
  AssessmentError,
  AssessmentNotFoundError,
  AnalysisNotCompleteError,
  AssessmentTimeoutError,
  estimateAssessmentTime
} from '../models/assessment_model';

import { AnalysisService } from './analysis_service';

export class AssessmentService extends EventEmitter {
  private jobs: Map<string, AssessmentJob> = new Map();
  private runningProcesses: Map<string, ChildProcess> = new Map();
  private analysisService: AnalysisService;
  private engineUrl: string;
  private engineTimeout: number;

  constructor(analysisService: AnalysisService) {
    super();
    this.analysisService = analysisService;
    this.engineUrl = process.env.ANALYSIS_ENGINE_URL || 'http://localhost:8000';
    this.engineTimeout = parseInt(process.env.ASSESSMENT_TIMEOUT_MS || '300000', 10); // 5 minutes
    
    // Cleanup on process exit
    process.on('exit', () => this.cleanup());
    process.on('SIGINT', () => this.cleanup());
    process.on('SIGTERM', () => this.cleanup());
  }

  /**
   * Start a new 12-factor assessment
   */
  async startAssessment(
    request: AssessmentRequest,
    userId: string,
    requestId: string,
    metadata: { userAgent?: string; ipAddress?: string }
  ): Promise<AssessmentJob> {
    const jobId = uuidv4();
    
    // Verify that the referenced analysis job exists and is completed
    const analysisJob = this.analysisService.getAnalysisStatus(request.analysisJobId, userId);
    if (!analysisJob) {
      throw new AssessmentError(`Analysis job not found: ${request.analysisJobId}`, 404, 'ANALYSIS_NOT_FOUND');
    }

    if (analysisJob.status !== 'completed') {
      throw new AnalysisNotCompleteError(request.analysisJobId);
    }

    if (!analysisJob.results) {
      throw new AssessmentError('Analysis results not available', 400, 'ANALYSIS_NO_RESULTS');
    }
    
    const job: AssessmentJob = {
      id: jobId,
      userId,
      analysisJobId: request.analysisJobId,
      repositoryUrl: analysisJob.repositoryUrl,
      options: request.options || {},
      status: AssessmentStatus.PENDING,
      progress: 0,
      createdAt: new Date(),
      metadata: {
        requestId,
        userAgent: metadata.userAgent,
        ipAddress: metadata.ipAddress,
      },
    };

    this.jobs.set(jobId, job);
    console.log(`Created assessment job ${jobId} for user ${userId}`);

    // Start assessment asynchronously
    this.processAssessment(job, analysisJob.results).catch((error) => {
      console.error(`Assessment job ${jobId} failed:`, error);
      this.updateJobStatus(jobId, AssessmentStatus.FAILED, 0, error.message);
    });

    return job;
  }

  /**
   * Get assessment job status
   */
  getAssessmentStatus(jobId: string, userId: string): AssessmentJob | null {
    const job = this.jobs.get(jobId);
    
    if (!job || job.userId !== userId) {
      return null;
    }

    return job;
  }

  /**
   * Cancel an assessment job
   */
  async cancelAssessment(jobId: string, userId: string, force: boolean = false): Promise<boolean> {
    const job = this.jobs.get(jobId);
    
    if (!job || job.userId !== userId) {
      return false;
    }

    if (job.status === AssessmentStatus.COMPLETED) {
      throw new AssessmentError('Cannot cancel completed assessment', 400, 'ASSESSMENT_COMPLETED');
    }

    if (job.status === AssessmentStatus.FAILED) {
      throw new AssessmentError('Cannot cancel failed assessment', 400, 'ASSESSMENT_FAILED');
    }

    // Kill running process if exists
    const process = this.runningProcesses.get(jobId);
    if (process && !process.killed) {
      process.kill(force ? 'SIGKILL' : 'SIGTERM');
      this.runningProcesses.delete(jobId);
    }

    this.updateJobStatus(jobId, AssessmentStatus.CANCELLED, job.progress, 'Assessment cancelled by user');
    
    console.log(`Assessment job ${jobId} cancelled by user ${userId}`);
    return true;
  }

  /**
   * Get user's assessment jobs with filtering
   */
  getUserAssessments(
    userId: string,
    filters: {
      status?: string;
      limit: number;
      offset: number;
      sortBy: string;
      sortOrder: string;
    }
  ): { jobs: AssessmentJob[]; total: number } {
    let userJobs = Array.from(this.jobs.values())
      .filter(job => job.userId === userId);

    // Apply status filter
    if (filters.status) {
      userJobs = userJobs.filter(job => job.status === filters.status);
    }

    // Sort jobs
    userJobs.sort((a, b) => {
      const aValue = this.getJobSortValue(a, filters.sortBy);
      const bValue = this.getJobSortValue(b, filters.sortBy);
      
      if (filters.sortOrder === 'asc') {
        return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
      } else {
        return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
      }
    });

    const total = userJobs.length;
    const paginatedJobs = userJobs.slice(filters.offset, filters.offset + filters.limit);

    return { jobs: paginatedJobs, total };
  }

  /**
   * Get assessment statistics for a user
   */
  getAssessmentStatistics(userId: string, period: string): any {
    const userJobs = Array.from(this.jobs.values())
      .filter(job => job.userId === userId);

    const now = new Date();
    const periodMs = this.getPeriodInMs(period);
    const cutoffDate = new Date(now.getTime() - periodMs);

    const recentJobs = userJobs.filter(job => job.createdAt >= cutoffDate);
    const completedJobs = recentJobs.filter(job => job.status === AssessmentStatus.COMPLETED);

    const stats = {
      total_assessments: recentJobs.length,
      completed: completedJobs.length,
      failed: recentJobs.filter(job => job.status === AssessmentStatus.FAILED).length,
      in_progress: recentJobs.filter(job => 
        job.status === AssessmentStatus.PENDING || job.status === AssessmentStatus.PROCESSING
      ).length,
      average_completion_time: this.calculateAverageCompletionTime(recentJobs),
      grade_distribution: this.getGradeDistribution(completedJobs),
      average_score: this.calculateAverageScore(completedJobs),
      repositories_assessed: new Set(recentJobs.map(job => job.repositoryUrl)).size,
    };

    return stats;
  }

  /**
   * Compare two assessments
   */
  compareAssessments(
    currentJobId: string,
    previousJobId: string,
    userId: string
  ): any {
    const currentJob = this.getAssessmentStatus(currentJobId, userId);
    const previousJob = this.getAssessmentStatus(previousJobId, userId);

    if (!currentJob || !previousJob) {
      throw new AssessmentNotFoundError(currentJobId);
    }

    if (currentJob.status !== AssessmentStatus.COMPLETED || 
        previousJob.status !== AssessmentStatus.COMPLETED) {
      throw new AssessmentError('Both assessments must be completed', 400, 'ASSESSMENT_NOT_COMPLETE');
    }

    if (!currentJob.results || !previousJob.results) {
      throw new AssessmentError('Assessment results not available', 400, 'RESULTS_NOT_AVAILABLE');
    }

    return this.generateAssessmentComparison(currentJob.results, previousJob.results);
  }

  /**
   * Process assessment job
   */
  private async processAssessment(job: AssessmentJob, analysisResult: any): Promise<void> {
    try {
      this.updateJobStatus(job.id, AssessmentStatus.PROCESSING, 10, 'Starting 12-factor assessment...');

      // Check if assessment engine is available
      const engineHealth = await this.checkEngineHealth();
      if (!engineHealth) {
        throw new AssessmentError('Assessment engine is unavailable', 503, 'ENGINE_UNAVAILABLE');
      }

      // Run assessment with timeout
      const timeout = estimateAssessmentTime(job.options) * 60 * 1000; // Convert to milliseconds
      const timeoutId = setTimeout(() => {
        const process = this.runningProcesses.get(job.id);
        if (process) {
          process.kill('SIGTERM');
        }
        throw new AssessmentTimeoutError(timeout / 60000);
      }, timeout);

      try {
        const result = await this.runAssessmentEngine(job, analysisResult);
        clearTimeout(timeoutId);
        
        this.updateJobStatus(job.id, AssessmentStatus.COMPLETED, 100, '12-factor assessment completed successfully');
        
        // Store results
        const updatedJob = this.jobs.get(job.id);
        if (updatedJob) {
          updatedJob.results = result;
          updatedJob.completedAt = new Date();
        }

        this.emit('assessment_completed', job.id, result);
        
      } catch (error) {
        clearTimeout(timeoutId);
        throw error;
      }

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      this.updateJobStatus(job.id, AssessmentStatus.FAILED, job.progress, errorMessage);
      
      // Store error
      const updatedJob = this.jobs.get(job.id);
      if (updatedJob) {
        updatedJob.error = errorMessage;
        updatedJob.completedAt = new Date();
      }

      this.emit('assessment_failed', job.id, error);
    }
  }

  /**
   * Run the assessment engine
   */
  private async runAssessmentEngine(job: AssessmentJob, analysisResult: any): Promise<TwelveFactorAssessment> {
    // Option 1: Use HTTP API if the engine provides one
    if (process.env.ANALYSIS_ENGINE_MODE === 'api') {
      return this.runAssessmentViaAPI(job, analysisResult);
    }
    
    // Option 2: Run as subprocess (default)
    return this.runAssessmentViaSubprocess(job, analysisResult);
  }

  /**
   * Run assessment via HTTP API
   */
  private async runAssessmentViaAPI(job: AssessmentJob, analysisResult: any): Promise<TwelveFactorAssessment> {
    try {
      const response = await axios.post(
        `${this.engineUrl}/assess`,
        {
          analysis_result: analysisResult,
          assessment_options: job.options,
        },
        {
          timeout: this.engineTimeout,
          onUploadProgress: (progressEvent) => {
            const progress = Math.round((progressEvent.loaded * 80) / (progressEvent.total || 1)) + 20;
            this.updateJobStatus(job.id, AssessmentStatus.PROCESSING, progress, 'Running 12-factor evaluation...');
          }
        }
      );

      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        if (error.code === 'ECONNREFUSED') {
          throw new AssessmentError('Assessment engine is unavailable', 503, 'ENGINE_UNAVAILABLE');
        }
      }
      throw error;
    }
  }

  /**
   * Run assessment via subprocess
   */
  private async runAssessmentViaSubprocess(job: AssessmentJob, analysisResult: any): Promise<TwelveFactorAssessment> {
    return new Promise((resolve, reject) => {
      const enginePath = process.env.ANALYSIS_ENGINE_PATH || 
        path.join(__dirname, '../../../analysis-engine/src/evaluators/twelve_factor_assessor.py');
      
      const args = [
        '-c',
        `
import sys
import json
sys.path.insert(0, '${path.dirname(enginePath)}')
from twelve_factor_assessor import assess_repository_twelve_factor
from ..analyzers.repository_analyzer import RepositoryAnalysisResult

# Load analysis result from stdin
analysis_data = json.loads(input())
analysis_result = RepositoryAnalysisResult(**analysis_data)

# Perform assessment
assessment = assess_repository_twelve_factor(analysis_result)

# Output results
print(json.dumps(assessment.to_dict()))
        `
      ];

      const pythonProcess = spawn('python', args, {
        stdio: ['pipe', 'pipe', 'pipe'],
        cwd: path.dirname(enginePath),
      });

      this.runningProcesses.set(job.id, pythonProcess);

      // Send analysis result to Python process
      pythonProcess.stdin.write(JSON.stringify(analysisResult));
      pythonProcess.stdin.end();

      let stdout = '';
      let stderr = '';
      let progress = 30;

      pythonProcess.stdout.on('data', (data) => {
        stdout += data.toString();
        
        // Update progress based on output
        progress = Math.min(90, progress + 10);
        this.updateJobStatus(job.id, AssessmentStatus.PROCESSING, progress, 'Evaluating factors...');
      });

      pythonProcess.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      pythonProcess.on('close', (code) => {
        this.runningProcesses.delete(job.id);

        if (code === 0) {
          try {
            const result = JSON.parse(stdout);
            resolve(result);
          } catch (parseError) {
            reject(new AssessmentError(`Failed to parse assessment results: ${parseError}`));
          }
        } else {
          const errorMessage = stderr || `Assessment process exited with code ${code}`;
          reject(new AssessmentError(errorMessage));
        }
      });

      pythonProcess.on('error', (error) => {
        this.runningProcesses.delete(job.id);
        reject(new AssessmentError(`Failed to start assessment engine: ${error.message}`));
      });
    });
  }

  /**
   * Check if assessment engine is healthy
   */
  private async checkEngineHealth(): Promise<boolean> {
    try {
      if (process.env.ANALYSIS_ENGINE_MODE === 'api') {
        const response = await axios.get(`${this.engineUrl}/health`, { timeout: 5000 });
        return response.status === 200;
      }
      return true; // Assume subprocess mode is always available
    } catch {
      return false;
    }
  }

  /**
   * Generate assessment comparison
   */
  private generateAssessmentComparison(
    current: TwelveFactorAssessment,
    previous: TwelveFactorAssessment
  ): any {
    const scoreDelta = current.weighted_score - previous.weighted_score;
    const gradeChanged = current.grade !== previous.grade;

    // Factor-level changes
    const factorChanges: { [key: string]: any } = {};
    for (const factorName in current.factor_evaluations) {
      if (previous.factor_evaluations[factorName]) {
        const currentScore = current.factor_evaluations[factorName].score;
        const previousScore = previous.factor_evaluations[factorName].score;
        
        if (currentScore !== previousScore) {
          factorChanges[factorName] = {
            previous: previousScore,
            current: currentScore,
            change: currentScore - previousScore,
          };
        }
      }
    }

    // Generate progress summary
    let summary: string;
    if (Math.abs(scoreDelta) < 0.1 && Object.keys(factorChanges).length === 0) {
      summary = "No significant changes detected since last assessment";
    } else if (scoreDelta > 0.5) {
      summary = "Significant improvement in 12-factor compliance";
    } else if (scoreDelta > 0.1) {
      summary = "Moderate improvement detected";
    } else if (scoreDelta < -0.1) {
      summary = "Some regression in compliance scores";
    } else {
      summary = "Minimal overall score change";
    }

    if (gradeChanged) {
      summary += " with grade improvement";
    }

    if (Object.keys(factorChanges).length > 0) {
      const improvedFactors = Object.keys(factorChanges).filter(
        name => factorChanges[name].change > 0
      );
      if (improvedFactors.length > 0) {
        summary += `. ${improvedFactors.length} factors showed improvement`;
      }
    }

    return {
      overall_progress: {
        score_change: scoreDelta,
        grade_changed: gradeChanged,
        previous_grade: previous.grade,
        current_grade: current.grade,
      },
      factor_changes: factorChanges,
      recommendations: {
        previous_count: previous.recommendations.length,
        current_count: current.recommendations.length,
        change: current.recommendations.length - previous.recommendations.length,
      },
      assessment_dates: {
        previous: previous.timestamp,
        current: current.timestamp,
      },
      summary,
    };
  }

  /**
   * Update job status
   */
  private updateJobStatus(
    jobId: string, 
    status: AssessmentStatus, 
    progress: number, 
    message?: string
  ): void {
    const job = this.jobs.get(jobId);
    if (job) {
      job.status = status;
      job.progress = progress;
      
      if (status === AssessmentStatus.PROCESSING && !job.startedAt) {
        job.startedAt = new Date();
      }

      this.emit('status_updated', jobId, status, progress, message);
    }
  }

  /**
   * Helper methods
   */
  private getJobSortValue(job: AssessmentJob, sortBy: string): any {
    switch (sortBy) {
      case 'createdAt':
        return job.createdAt;
      case 'completedAt':
        return job.completedAt || new Date(0);
      case 'grade':
        return job.results?.grade || 'Z';
      case 'overall_score':
        return job.results?.overall_score || 0;
      default:
        return job.createdAt;
    }
  }

  private getPeriodInMs(period: string): number {
    switch (period) {
      case '7d': return 7 * 24 * 60 * 60 * 1000;
      case '30d': return 30 * 24 * 60 * 60 * 1000;
      case '90d': return 90 * 24 * 60 * 60 * 1000;
      case '1y': return 365 * 24 * 60 * 60 * 1000;
      default: return 30 * 24 * 60 * 60 * 1000;
    }
  }

  private calculateAverageCompletionTime(jobs: AssessmentJob[]): number {
    const completedJobs = jobs.filter(job => 
      job.status === AssessmentStatus.COMPLETED && job.startedAt && job.completedAt
    );

    if (completedJobs.length === 0) return 0;

    const totalTime = completedJobs.reduce((sum, job) => {
      const duration = job.completedAt!.getTime() - job.startedAt!.getTime();
      return sum + duration;
    }, 0);

    return Math.round(totalTime / completedJobs.length / 1000); // Return in seconds
  }

  private getGradeDistribution(jobs: AssessmentJob[]): { [key: string]: number } {
    const distribution: { [key: string]: number } = {};
    
    jobs.forEach(job => {
      if (job.results?.grade) {
        distribution[job.results.grade] = (distribution[job.results.grade] || 0) + 1;
      }
    });

    return distribution;
  }

  private calculateAverageScore(jobs: AssessmentJob[]): number {
    const jobsWithScores = jobs.filter(job => job.results?.overall_score !== undefined);
    
    if (jobsWithScores.length === 0) return 0;

    const totalScore = jobsWithScores.reduce((sum, job) => sum + (job.results?.overall_score || 0), 0);
    return totalScore / jobsWithScores.length;
  }

  /**
   * Cleanup running processes
   */
  private cleanup(): void {
    console.log('Cleaning up assessment processes...');
    
    for (const [jobId, process] of this.runningProcesses.entries()) {
      if (!process.killed) {
        console.log(`Terminating assessment process for job ${jobId}`);
        process.kill('SIGTERM');
      }
    }
    
    this.runningProcesses.clear();
  }
}