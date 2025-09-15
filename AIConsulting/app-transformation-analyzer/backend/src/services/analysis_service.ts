/**
 * Analysis service for communicating with the Python analysis engine
 * Handles job management, status tracking, and result processing
 */

import { EventEmitter } from 'events';
import { v4 as uuidv4 } from 'uuid';
import { spawn, ChildProcess } from 'child_process';
import axios from 'axios';
import path from 'path';

import {
  AnalysisJob,
  AnalysisStatus,
  AnalysisRequest,
  AnalysisResult,
  AnalysisError,
  RepositoryNotFoundError,
  AnalysisTimeoutError,
  EngineUnavailableError,
  estimateAnalysisTime
} from '../models/analysis_model';

export class AnalysisService extends EventEmitter {
  private jobs: Map<string, AnalysisJob> = new Map();
  private runningProcesses: Map<string, ChildProcess> = new Map();
  private engineUrl: string;
  private engineTimeout: number;

  constructor() {
    super();
    this.engineUrl = process.env.ANALYSIS_ENGINE_URL || 'http://localhost:8000';
    this.engineTimeout = parseInt(process.env.ANALYSIS_TIMEOUT_MS || '1800000', 10); // 30 minutes
    
    // Cleanup on process exit
    process.on('exit', () => this.cleanup());
    process.on('SIGINT', () => this.cleanup());
    process.on('SIGTERM', () => this.cleanup());
  }

  /**
   * Start a new analysis job
   */
  async startAnalysis(
    request: AnalysisRequest,
    userId: string,
    requestId: string,
    metadata: { userAgent?: string; ipAddress?: string }
  ): Promise<AnalysisJob> {
    const jobId = uuidv4();
    
    const job: AnalysisJob = {
      id: jobId,
      userId,
      repositoryUrl: request.repositoryUrl,
      branchName: request.branchName,
      analysisType: request.analysisType,
      options: request.options || {},
      status: AnalysisStatus.PENDING,
      progress: 0,
      createdAt: new Date(),
      metadata: {
        requestId,
        userAgent: metadata.userAgent,
        ipAddress: metadata.ipAddress,
      },
    };

    this.jobs.set(jobId, job);
    console.log(`Created analysis job ${jobId} for user ${userId}`);

    // Start analysis asynchronously
    this.processAnalysis(job).catch((error) => {
      console.error(`Analysis job ${jobId} failed:`, error);
      this.updateJobStatus(jobId, AnalysisStatus.FAILED, 0, error.message);
    });

    return job;
  }

  /**
   * Get analysis job status
   */
  getAnalysisStatus(jobId: string, userId: string): AnalysisJob | null {
    const job = this.jobs.get(jobId);
    
    if (!job || job.userId !== userId) {
      return null;
    }

    return job;
  }

  /**
   * Cancel an analysis job
   */
  async cancelAnalysis(jobId: string, userId: string, force: boolean = false): Promise<boolean> {
    const job = this.jobs.get(jobId);
    
    if (!job || job.userId !== userId) {
      return false;
    }

    if (job.status === AnalysisStatus.COMPLETED) {
      throw new AnalysisError('Cannot cancel completed analysis', 400, 'ANALYSIS_COMPLETED');
    }

    if (job.status === AnalysisStatus.FAILED) {
      throw new AnalysisError('Cannot cancel failed analysis', 400, 'ANALYSIS_FAILED');
    }

    // Kill running process if exists
    const process = this.runningProcesses.get(jobId);
    if (process && !process.killed) {
      process.kill(force ? 'SIGKILL' : 'SIGTERM');
      this.runningProcesses.delete(jobId);
    }

    this.updateJobStatus(jobId, AnalysisStatus.CANCELLED, job.progress, 'Analysis cancelled by user');
    
    console.log(`Analysis job ${jobId} cancelled by user ${userId}`);
    return true;
  }

  /**
   * Get user's analysis jobs with filtering
   */
  getUserAnalyses(
    userId: string,
    filters: {
      status?: string;
      limit: number;
      offset: number;
      sortBy: string;
      sortOrder: string;
    }
  ): { jobs: AnalysisJob[]; total: number } {
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
   * Validate repository accessibility
   */
  async validateRepository(repositoryUrl: string): Promise<{ accessible: boolean; error?: string }> {
    try {
      // Use the analysis engine to validate repository
      const response = await axios.post(
        `${this.engineUrl}/validate`,
        { repository_url: repositoryUrl },
        { timeout: 10000 }
      );

      return { accessible: response.data.data.accessible, error: response.data.data.error };
    } catch (error) {
      if (axios.isAxiosError(error)) {
        if (error.response?.status === 404) {
          return { accessible: false, error: 'Repository not found or not accessible' };
        } else if (error.code === 'ECONNREFUSED') {
          throw new EngineUnavailableError();
        }
      }
      
      return { accessible: false, error: 'Validation failed' };
    }
  }

  /**
   * Get analysis statistics for a user
   */
  getAnalysisStatistics(userId: string, period: string): any {
    const userJobs = Array.from(this.jobs.values())
      .filter(job => job.userId === userId);

    const now = new Date();
    const periodMs = this.getPeriodInMs(period);
    const cutoffDate = new Date(now.getTime() - periodMs);

    const recentJobs = userJobs.filter(job => job.createdAt >= cutoffDate);

    const stats = {
      total_analyses: recentJobs.length,
      completed: recentJobs.filter(job => job.status === AnalysisStatus.COMPLETED).length,
      failed: recentJobs.filter(job => job.status === AnalysisStatus.FAILED).length,
      in_progress: recentJobs.filter(job => 
        job.status === AnalysisStatus.PENDING || job.status === AnalysisStatus.PROCESSING
      ).length,
      average_completion_time: this.calculateAverageCompletionTime(recentJobs),
      analysis_types: this.getAnalysisTypeDistribution(recentJobs),
      repositories_analyzed: new Set(recentJobs.map(job => job.repositoryUrl)).size,
    };

    return stats;
  }

  /**
   * Process analysis job
   */
  private async processAnalysis(job: AnalysisJob): Promise<void> {
    try {
      this.updateJobStatus(job.id, AnalysisStatus.PROCESSING, 10, 'Starting analysis...');

      // Check if analysis engine is available
      const engineHealth = await this.checkEngineHealth();
      if (!engineHealth) {
        throw new EngineUnavailableError();
      }

      // Validate repository
      this.updateJobStatus(job.id, AnalysisStatus.PROCESSING, 20, 'Validating repository...');
      const validation = await this.validateRepository(job.repositoryUrl);
      if (!validation.accessible) {
        throw new RepositoryNotFoundError(job.repositoryUrl);
      }

      // Start analysis with timeout
      const timeout = (job.options.timeout || 30) * 60 * 1000; // Convert to milliseconds
      const timeoutId = setTimeout(() => {
        const process = this.runningProcesses.get(job.id);
        if (process) {
          process.kill('SIGTERM');
        }
        throw new AnalysisTimeoutError(job.options.timeout || 30);
      }, timeout);

      try {
        const result = await this.runAnalysisEngine(job);
        clearTimeout(timeoutId);
        
        this.updateJobStatus(job.id, AnalysisStatus.COMPLETED, 100, 'Analysis completed successfully');
        
        // Store results
        const updatedJob = this.jobs.get(job.id);
        if (updatedJob) {
          updatedJob.results = result;
          updatedJob.completedAt = new Date();
        }

        this.emit('analysis_completed', job.id, result);
        
      } catch (error) {
        clearTimeout(timeoutId);
        throw error;
      }

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      this.updateJobStatus(job.id, AnalysisStatus.FAILED, job.progress, errorMessage);
      
      // Store error
      const updatedJob = this.jobs.get(job.id);
      if (updatedJob) {
        updatedJob.error = errorMessage;
        updatedJob.completedAt = new Date();
      }

      this.emit('analysis_failed', job.id, error);
    }
  }

  /**
   * Run the analysis engine
   */
  private async runAnalysisEngine(job: AnalysisJob): Promise<AnalysisResult> {
    // Option 1: Use HTTP API if the engine provides one
    if (process.env.ANALYSIS_ENGINE_MODE === 'api') {
      return this.runAnalysisViaAPI(job);
    }
    
    // Option 2: Run as subprocess (default)
    return this.runAnalysisViaSubprocess(job);
  }

  /**
   * Run analysis via HTTP API
   */
  private async runAnalysisViaAPI(job: AnalysisJob): Promise<AnalysisResult> {
    try {
      const response = await axios.post(
        `${this.engineUrl}/analyze`,
        {
          repository_url: job.repositoryUrl,
          branch: job.branchName,
          analysis_type: job.analysisType,
          options: job.options,
        },
        {
          timeout: this.engineTimeout,
          onUploadProgress: (progressEvent) => {
            const progress = Math.round((progressEvent.loaded * 80) / (progressEvent.total || 1)) + 20;
            this.updateJobStatus(job.id, AnalysisStatus.PROCESSING, progress, 'Running analysis...');
          }
        }
      );

      return response.data.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        if (error.code === 'ECONNREFUSED') {
          throw new EngineUnavailableError();
        } else if (error.response?.status === 404) {
          throw new RepositoryNotFoundError(job.repositoryUrl);
        }
      }
      throw error;
    }
  }

  /**
   * Run analysis via subprocess
   */
  private async runAnalysisViaSubprocess(job: AnalysisJob): Promise<AnalysisResult> {
    return new Promise((resolve, reject) => {
      const enginePath = process.env.ANALYSIS_ENGINE_PATH || 
        path.join(__dirname, '../../../analysis-engine/src/main.py');
      
      const args = [
        enginePath,
        job.repositoryUrl,
        '--output', 'json',
        '--analysis-type', job.analysisType,
      ];

      if (job.branchName) {
        args.push('--branch', job.branchName);
      }

      if (job.options.depth) {
        args.push('--depth', job.options.depth.toString());
      }

      const pythonProcess = spawn('python', args, {
        stdio: ['pipe', 'pipe', 'pipe'],
        cwd: path.dirname(enginePath),
      });

      this.runningProcesses.set(job.id, pythonProcess);

      let stdout = '';
      let stderr = '';
      let progress = 30;

      pythonProcess.stdout.on('data', (data) => {
        stdout += data.toString();
        
        // Update progress based on output
        progress = Math.min(90, progress + 5);
        this.updateJobStatus(job.id, AnalysisStatus.PROCESSING, progress, 'Analyzing code...');
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
            reject(new AnalysisError(`Failed to parse analysis results: ${parseError}`));
          }
        } else {
          const errorMessage = stderr || `Analysis process exited with code ${code}`;
          reject(new AnalysisError(errorMessage));
        }
      });

      pythonProcess.on('error', (error) => {
        this.runningProcesses.delete(job.id);
        reject(new AnalysisError(`Failed to start analysis engine: ${error.message}`));
      });
    });
  }

  /**
   * Check if analysis engine is healthy
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
   * Update job status
   */
  private updateJobStatus(
    jobId: string, 
    status: AnalysisStatus, 
    progress: number, 
    message?: string
  ): void {
    const job = this.jobs.get(jobId);
    if (job) {
      job.status = status;
      job.progress = progress;
      
      if (status === AnalysisStatus.PROCESSING && !job.startedAt) {
        job.startedAt = new Date();
      }

      this.emit('status_updated', jobId, status, progress, message);
    }
  }

  /**
   * Helper methods
   */
  private getJobSortValue(job: AnalysisJob, sortBy: string): any {
    switch (sortBy) {
      case 'createdAt':
        return job.createdAt;
      case 'completedAt':
        return job.completedAt || new Date(0);
      case 'repositoryUrl':
        return job.repositoryUrl;
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

  private calculateAverageCompletionTime(jobs: AnalysisJob[]): number {
    const completedJobs = jobs.filter(job => 
      job.status === AnalysisStatus.COMPLETED && job.startedAt && job.completedAt
    );

    if (completedJobs.length === 0) return 0;

    const totalTime = completedJobs.reduce((sum, job) => {
      const duration = job.completedAt!.getTime() - job.startedAt!.getTime();
      return sum + duration;
    }, 0);

    return Math.round(totalTime / completedJobs.length / 1000); // Return in seconds
  }

  private getAnalysisTypeDistribution(jobs: AnalysisJob[]): { [key: string]: number } {
    const distribution: { [key: string]: number } = {};
    
    jobs.forEach(job => {
      distribution[job.analysisType] = (distribution[job.analysisType] || 0) + 1;
    });

    return distribution;
  }

  /**
   * Cleanup running processes
   */
  private cleanup(): void {
    console.log('Cleaning up analysis processes...');
    
    for (const [jobId, process] of this.runningProcesses.entries()) {
      if (!process.killed) {
        console.log(`Terminating analysis process for job ${jobId}`);
        process.kill('SIGTERM');
      }
    }
    
    this.runningProcesses.clear();
  }
}