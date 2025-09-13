/**
 * API service for communicating with the backend
 * No authentication required - simplified API client
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import {
  ApiResponse,
  AnalysisRequest,
  AnalysisJob,
  AnalysisResults,
  AssessmentRequest,
  AssessmentJob,
  AssessmentResults,
  DashboardData,
  PaginationParams,
  FilterParams,
} from '../types';

class ApiClient {
  private client: AxiosInstance;
  private baseURL: string;

  constructor() {
    this.baseURL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5001';

    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Response interceptor to handle errors
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        return Promise.reject(this.handleError(error));
      }
    );
  }

  private handleError(error: AxiosError): Error {
    if (error.response) {
      // Server responded with error status
      const apiError = error.response.data as ApiResponse;
      const message = apiError.error?.message || `HTTP ${error.response.status}`;
      return new Error(message);
    } else if (error.request) {
      // Network error
      return new Error('Network error. Please check your connection.');
    } else {
      // Request setup error
      return new Error('Request failed. Please try again.');
    }
  }

  private async makeRequest<T>(
    method: 'GET' | 'POST' | 'PUT' | 'DELETE',
    url: string,
    data?: any,
    params?: any
  ): Promise<T> {
    try {
      const response = await this.client.request({
        method,
        url,
        data,
        params,
      });

      const apiResponse = response.data as ApiResponse<T>;

      if (!apiResponse.success) {
        throw new Error(apiResponse.error?.message || 'API request failed');
      }

      return apiResponse.data!;
    } catch (error) {
      throw error;
    }
  }

  // Analysis methods
  async startAnalysis(request: AnalysisRequest): Promise<{ jobId: string; message: string }> {
    return this.makeRequest(
      'POST',
      '/api/analysis/repository',
      request
    );
  }

  async getAnalysisStatus(jobId: string): Promise<AnalysisJob> {
    return this.makeRequest('GET', `/api/analysis/${jobId}/status`);
  }

  async getAnalysisResults(
    jobId: string,
    options?: { includeMetadata?: boolean; format?: string }
  ): Promise<AnalysisResults> {
    return this.makeRequest(
      'GET',
      `/api/analysis/${jobId}/results`,
      null,
      options
    );
  }

  async getUserAnalyses(
    filters: FilterParams & PaginationParams
  ): Promise<{ jobs: AnalysisJob[]; pagination: any }> {
    return this.makeRequest('GET', '/api/analysis/jobs', null, filters);
  }

  async cancelAnalysis(jobId: string, force: boolean = false): Promise<void> {
    await this.makeRequest('DELETE', `/api/analysis/${jobId}`, { force });
  }

  async restartAnalysis(jobId: string): Promise<{ newJobId: string }> {
    return this.makeRequest('POST', `/api/analysis/${jobId}/restart`);
  }

  async validateRepository(repositoryUrl: string): Promise<{ accessible: boolean; error?: string }> {
    return this.makeRequest(
      'POST',
      '/api/analysis/validate',
      { repositoryUrl }
    );
  }

  async getAnalysisStatistics(period: string = '30d'): Promise<any> {
    return this.makeRequest(
      'GET',
      '/api/analysis/statistics',
      null,
      { period }
    );
  }

  // Assessment methods
  async startAssessment(request: AssessmentRequest): Promise<{ jobId: string; message: string }> {
    return this.makeRequest(
      'POST',
      '/api/assessment/12factor',
      request
    );
  }

  async getAssessmentStatus(jobId: string): Promise<AssessmentJob> {
    return this.makeRequest('GET', `/api/assessment/${jobId}/status`);
  }

  async getAssessmentResults(
    jobId: string,
    options?: { format?: string; includeRoadmap?: boolean; includeSummary?: boolean }
  ): Promise<AssessmentResults> {
    return this.makeRequest(
      'GET',
      `/api/assessment/${jobId}/results`,
      null,
      options
    );
  }

  async getUserAssessments(
    filters: FilterParams & PaginationParams
  ): Promise<{ jobs: AssessmentJob[]; pagination: any }> {
    return this.makeRequest('GET', '/api/assessment/jobs', null, filters);
  }

  async cancelAssessment(jobId: string, force: boolean = false): Promise<void> {
    await this.makeRequest('DELETE', `/api/assessment/${jobId}`, { force });
  }

  async compareAssessments(
    currentAssessmentId: string,
    previousAssessmentId: string
  ): Promise<any> {
    return this.makeRequest('POST', '/api/assessment/compare', {
      currentAssessmentId,
      previousAssessmentId,
    });
  }

  async getFactorEvaluations(
    jobId: string,
    filters?: {
      factorName?: string;
      includeEvidence?: boolean;
      minScore?: number;
      maxScore?: number;
    }
  ): Promise<{ factors: any[]; total: number }> {
    return this.makeRequest(
      'GET',
      `/api/assessment/${jobId}/factors`,
      null,
      filters
    );
  }

  async getRecommendations(
    jobId: string,
    filters?: {
      priority?: string;
      factorName?: string;
      complexity?: string;
      limit?: number;
    }
  ): Promise<{ recommendations: any[]; total: number }> {
    return this.makeRequest(
      'GET',
      `/api/assessment/${jobId}/recommendations`,
      null,
      filters
    );
  }

  async getImplementationRoadmap(jobId: string): Promise<{ roadmap: any }> {
    return this.makeRequest('GET', `/api/assessment/${jobId}/roadmap`);
  }

  async getAssessmentStatistics(period: string = '30d'): Promise<any> {
    return this.makeRequest(
      'GET',
      '/api/assessment/statistics',
      null,
      { period }
    );
  }

  async getTwelveFactorDefinitions(): Promise<{ definitions: any; total: number }> {
    return this.makeRequest('GET', '/api/assessment/12factor/definitions');
  }

  // Health and monitoring methods
  async getHealthStatus(): Promise<{ status: string; services: any }> {
    return this.makeRequest('GET', '/health/detailed');
  }

  // Dashboard methods
  async getDashboardData(): Promise<DashboardData> {
    try {
      const [analyses, assessments, analysisStats, assessmentStats] = await Promise.all([
        this.getUserAnalyses({ limit: 5, offset: 0, sortBy: 'createdAt', sortOrder: 'desc' }),
        this.getUserAssessments({ limit: 5, offset: 0, sortBy: 'createdAt', sortOrder: 'desc' }),
        this.getAnalysisStatistics(),
        this.getAssessmentStatistics(),
      ]);

      return {
        recentAnalyses: analyses.jobs,
        recentAssessments: assessments.jobs,
        statistics: {
          totalAnalyses: analysisStats.statistics?.total_analyses || 0,
          totalAssessments: assessmentStats.statistics?.total_assessments || 0,
          averageScore: assessmentStats.statistics?.average_score || 0,
          successRate: analysisStats.statistics?.success_rate || 0,
        },
      };
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      // Return empty dashboard data instead of throwing
      return {
        recentAnalyses: [],
        recentAssessments: [],
        statistics: {
          totalAnalyses: 0,
          totalAssessments: 0,
          averageScore: 0,
          successRate: 0,
        },
      };
    }
  }

  // Utility methods
  setBaseURL(url: string): void {
    this.baseURL = url;
    this.client.defaults.baseURL = url;
  }

  // WebSocket methods (placeholder for future real-time features)
  connectWebSocket(): void {
    // Implementation would go here for real-time updates
    console.log('WebSocket connection placeholder');
  }

  disconnectWebSocket(): void {
    // Implementation would go here
    console.log('WebSocket disconnection placeholder');
  }
}

// Create and export singleton instance
export const apiClient = new ApiClient();

// Export for testing and advanced usage
export { ApiClient };

// Export helper functions
export const isApiError = (error: any): error is ApiResponse => {
  return error && typeof error === 'object' && 'success' in error;
};

export const getErrorMessage = (error: any): string => {
  if (isApiError(error)) {
    return error.error?.message || 'Unknown API error';
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'An unexpected error occurred';
};