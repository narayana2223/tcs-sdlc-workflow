/**
 * Health check routes for monitoring API status
 * Provides endpoints for health monitoring and service status
 */

import { Router, Request, Response } from 'express';
import { execSync } from 'child_process';
import { readFileSync } from 'fs';
import { join } from 'path';

const router = Router();

interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  uptime: number;
  version: string;
  environment: string;
  services: {
    api: ServiceStatus;
    database: ServiceStatus;
    analysisEngine: ServiceStatus;
  };
  system: {
    memory: {
      used: number;
      free: number;
      total: number;
      percentage: number;
    };
    cpu: {
      loadAverage: number[];
    };
    disk: {
      free: string;
      percentage: string;
    };
  };
}

interface ServiceStatus {
  status: 'up' | 'down' | 'degraded';
  responseTime?: number;
  lastCheck: string;
  error?: string;
}

// Get package version
const getVersion = (): string => {
  try {
    const packageJson = JSON.parse(readFileSync(join(__dirname, '../../package.json'), 'utf8'));
    return packageJson.version || '1.0.0';
  } catch {
    return '1.0.0';
  }
};

// Check analysis engine health
const checkAnalysisEngine = async (): Promise<ServiceStatus> => {
  const startTime = Date.now();
  try {
    const engineUrl = process.env.ANALYSIS_ENGINE_URL || 'http://localhost:8000';
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);
    
    const response = await fetch(`${engineUrl}/health`, {
      method: 'GET',
      signal: controller.signal,
    });
    
    clearTimeout(timeoutId);
    
    const responseTime = Date.now() - startTime;
    
    if (response.ok) {
      return {
        status: 'up',
        responseTime,
        lastCheck: new Date().toISOString(),
      };
    } else {
      return {
        status: 'down',
        responseTime,
        lastCheck: new Date().toISOString(),
        error: `HTTP ${response.status}`,
      };
    }
  } catch (error) {
    return {
      status: 'down',
      responseTime: Date.now() - startTime,
      lastCheck: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
};

// Check database health (mock implementation)
const checkDatabase = async (): Promise<ServiceStatus> => {
  try {
    // In a real application, this would check database connectivity
    // For now, we'll simulate a database check
    const startTime = Date.now();
    
    // Simulate database query
    await new Promise(resolve => setTimeout(resolve, 10));
    
    return {
      status: 'up',
      responseTime: Date.now() - startTime,
      lastCheck: new Date().toISOString(),
    };
  } catch (error) {
    return {
      status: 'down',
      lastCheck: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
};

// Get system metrics
const getSystemMetrics = () => {
  const memUsage = process.memoryUsage();
  const totalMemory = require('os').totalmem();
  const freeMemory = require('os').freemem();
  
  // Get disk usage (Unix-like systems)
  let diskFree = 'N/A';
  let diskPercentage = 'N/A';
  try {
    if (process.platform !== 'win32') {
      const diskUsage = execSync('df -h / | tail -1 | awk \'{print $4 ":" $5}\'', { encoding: 'utf8' }).trim();
      const [free, percentage] = diskUsage.split(':');
      diskFree = free;
      diskPercentage = percentage;
    }
  } catch {
    // Ignore disk check errors on unsupported platforms
  }

  return {
    memory: {
      used: memUsage.heapUsed,
      free: freeMemory,
      total: totalMemory,
      percentage: Math.round((memUsage.heapUsed / totalMemory) * 100),
    },
    cpu: {
      loadAverage: require('os').loadavg(),
    },
    disk: {
      free: diskFree,
      percentage: diskPercentage,
    },
  };
};

/**
 * GET /health
 * Basic health check endpoint
 */
router.get('/', (req: Request, res: Response) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    version: getVersion(),
    environment: process.env.NODE_ENV || 'development',
    message: 'Application Transformation Analyzer API is running',
  });
});

/**
 * GET /health/detailed
 * Detailed health check with service dependencies
 */
router.get('/detailed', async (req: Request, res: Response) => {
  const startTime = Date.now();
  
  try {
    // Check all services
    const [databaseStatus, analysisEngineStatus] = await Promise.all([
      checkDatabase(),
      checkAnalysisEngine(),
    ]);

    const apiStatus: ServiceStatus = {
      status: 'up',
      responseTime: Date.now() - startTime,
      lastCheck: new Date().toISOString(),
    };

    // Determine overall health
    const services = {
      api: apiStatus,
      database: databaseStatus,
      analysisEngine: analysisEngineStatus,
    };

    let overallStatus: 'healthy' | 'degraded' | 'unhealthy' = 'healthy';
    
    if (services.database.status === 'down' || services.api.status === 'down') {
      overallStatus = 'unhealthy';
    } else if (services.analysisEngine.status === 'down') {
      overallStatus = 'degraded';
    }

    const healthStatus: HealthStatus = {
      status: overallStatus,
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      version: getVersion(),
      environment: process.env.NODE_ENV || 'development',
      services,
      system: getSystemMetrics(),
    };

    // Set appropriate status code
    const statusCode = overallStatus === 'healthy' ? 200 : 
                      overallStatus === 'degraded' ? 200 : 503;

    res.status(statusCode).json(healthStatus);

  } catch (error) {
    console.error('Health check error:', error);
    
    res.status(503).json({
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      version: getVersion(),
      environment: process.env.NODE_ENV || 'development',
      error: 'Health check failed',
      services: {
        api: {
          status: 'down',
          lastCheck: new Date().toISOString(),
          error: error instanceof Error ? error.message : 'Unknown error',
        },
        database: {
          status: 'down',
          lastCheck: new Date().toISOString(),
          error: 'Health check failed',
        },
        analysisEngine: {
          status: 'down',
          lastCheck: new Date().toISOString(),
          error: 'Health check failed',
        },
      },
    });
  }
});

/**
 * GET /health/ready
 * Kubernetes readiness probe endpoint
 */
router.get('/ready', async (req: Request, res: Response) => {
  try {
    // Check critical dependencies for readiness
    const databaseStatus = await checkDatabase();
    
    if (databaseStatus.status === 'up') {
      res.json({
        status: 'ready',
        timestamp: new Date().toISOString(),
        checks: {
          database: 'ok',
        },
      });
    } else {
      res.status(503).json({
        status: 'not ready',
        timestamp: new Date().toISOString(),
        checks: {
          database: 'failed',
        },
        error: databaseStatus.error,
      });
    }
  } catch (error) {
    res.status(503).json({
      status: 'not ready',
      timestamp: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Unknown error',
    });
  }
});

/**
 * GET /health/live
 * Kubernetes liveness probe endpoint
 */
router.get('/live', (req: Request, res: Response) => {
  // Simple liveness check - if the process is running, it's alive
  res.json({
    status: 'alive',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
  });
});

/**
 * GET /health/metrics
 * Prometheus-style metrics endpoint
 */
router.get('/metrics', (req: Request, res: Response) => {
  const metrics = getSystemMetrics();
  const uptime = process.uptime();
  
  // Simple Prometheus-style metrics
  const prometheusMetrics = `
# HELP nodejs_process_uptime_seconds Process uptime in seconds
# TYPE nodejs_process_uptime_seconds counter
nodejs_process_uptime_seconds ${uptime}

# HELP nodejs_heap_size_used_bytes Process heap space size used
# TYPE nodejs_heap_size_used_bytes gauge
nodejs_heap_size_used_bytes ${metrics.memory.used}

# HELP nodejs_heap_size_total_bytes Process heap space size total
# TYPE nodejs_heap_size_total_bytes gauge
nodejs_heap_size_total_bytes ${metrics.memory.total}

# HELP nodejs_external_memory_bytes Nodejs external memory size in bytes
# TYPE nodejs_external_memory_bytes gauge
nodejs_external_memory_bytes ${process.memoryUsage().external}

# HELP system_load_average_1m System load average over 1 minute
# TYPE system_load_average_1m gauge
system_load_average_1m ${metrics.cpu.loadAverage[0]}

# HELP system_load_average_5m System load average over 5 minutes
# TYPE system_load_average_5m gauge
system_load_average_5m ${metrics.cpu.loadAverage[1]}

# HELP system_load_average_15m System load average over 15 minutes
# TYPE system_load_average_15m gauge
system_load_average_15m ${metrics.cpu.loadAverage[2]}
  `.trim();

  res.setHeader('Content-Type', 'text/plain');
  res.send(prometheusMetrics);
});

export default router;