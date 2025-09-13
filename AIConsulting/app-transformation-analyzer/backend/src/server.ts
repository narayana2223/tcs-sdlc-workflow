/**
 * Main Express server setup for the Application Transformation Analyzer API
 * Handles repository analysis and 12-factor assessment requests
 */

import express, { Application, Request, Response, NextFunction } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import dotenv from 'dotenv';
import rateLimit from 'express-rate-limit';
import compression from 'compression';

// Import routes
import analysisRoutes from './routes/analysis';
import assessmentRoutes from './routes/assessment';
import healthRoutes from './routes/health';

// Load environment variables
dotenv.config();

// Types

interface ErrorResponse {
  error: string;
  message: string;
  timestamp: string;
  path: string;
  statusCode: number;
}

class Server {
  private app: Application;
  private port: number;

  constructor() {
    this.app = express();
    this.port = parseInt(process.env.PORT || '5000', 10);
    
    this.setupMiddleware();
    this.setupRoutes();
    this.setupErrorHandling();
  }

  private setupMiddleware(): void {
    // Security middleware
    this.app.use(helmet({
      contentSecurityPolicy: {
        directives: {
          defaultSrc: ["'self'"],
          styleSrc: ["'self'", "'unsafe-inline'"],
          scriptSrc: ["'self'"],
          imgSrc: ["'self'", "data:", "https:"],
        },
      },
    }));

    // CORS configuration
    const corsOptions = {
      origin: process.env.CORS_ORIGIN?.split(',') || ['http://localhost:3000', 'http://localhost:3001'],
      credentials: true,
      methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
      allowedHeaders: ['Content-Type', 'Authorization', 'x-api-key'],
      maxAge: 86400, // 24 hours
    };
    this.app.use(cors(corsOptions));

    // Rate limiting
    const limiter = rateLimit({
      windowMs: 15 * 60 * 1000, // 15 minutes
      max: process.env.NODE_ENV === 'production' ? 100 : 1000, // requests per window
      message: {
        error: 'Too Many Requests',
        message: 'Rate limit exceeded. Please try again later.',
        timestamp: new Date().toISOString(),
        statusCode: 429,
      },
      standardHeaders: true,
      legacyHeaders: false,
    });
    this.app.use('/api', limiter);

    // Compression
    this.app.use(compression());

    // Body parsing
    this.app.use(express.json({ limit: '10mb' }));
    this.app.use(express.urlencoded({ extended: true, limit: '10mb' }));

    // Logging
    const morganFormat = process.env.NODE_ENV === 'production' ? 'combined' : 'dev';
    this.app.use(morgan(morganFormat));

    // Request ID middleware
    this.app.use((req: Request, res: Response, next: NextFunction) => {
      const requestId = Math.random().toString(36).substr(2, 9);
      req.headers['x-request-id'] = requestId;
      res.setHeader('x-request-id', requestId);
      next();
    });

    // Request timeout
    this.app.use((req: Request, res: Response, next: NextFunction) => {
      res.setTimeout(300000, () => { // 5 minutes
        res.status(408).json({
          error: 'Request Timeout',
          message: 'Request took too long to process',
          timestamp: new Date().toISOString(),
          statusCode: 408,
        });
      });
      next();
    });
  }

  private setupRoutes(): void {
    // Health check endpoint
    this.app.use('/health', healthRoutes);

    // API routes - no authentication required
    this.app.use('/api/analysis', analysisRoutes);
    this.app.use('/api/assessment', assessmentRoutes);

    // Root endpoint
    this.app.get('/', (req: Request, res: Response) => {
      res.json({
        message: 'Application Transformation Analyzer API',
        version: process.env.npm_package_version || '1.0.0',
        timestamp: new Date().toISOString(),
        environment: process.env.NODE_ENV || 'development',
        endpoints: {
          health: '/health',
          analysis: '/api/analysis',
          assessment: '/api/assessment',
        },
      });
    });

    // 404 handler
    this.app.use('*', (req: Request, res: Response) => {
      res.status(404).json({
        error: 'Not Found',
        message: `Cannot ${req.method} ${req.originalUrl}`,
        timestamp: new Date().toISOString(),
        statusCode: 404,
      });
    });
  }


  private setupErrorHandling(): void {
    // Global error handler
    this.app.use((
      error: any,
      req: Request,
      res: Response,
      next: NextFunction
    ) => {
      console.error('Global error handler:', {
        error: error.message,
        stack: error.stack,
        url: req.url,
        method: req.method,
        timestamp: new Date().toISOString(),
        requestId: req.headers['x-request-id'],
      });

      // Default error response
      const errorResponse: ErrorResponse = {
        error: error.name || 'Internal Server Error',
        message: error.message || 'An unexpected error occurred',
        timestamp: new Date().toISOString(),
        path: req.path,
        statusCode: error.statusCode || 500,
      };

      // Don't leak error details in production
      if (process.env.NODE_ENV === 'production' && !error.statusCode) {
        errorResponse.message = 'Internal server error';
      }

      res.status(errorResponse.statusCode).json(errorResponse);
    });

    // Unhandled promise rejection handler
    process.on('unhandledRejection', (reason, promise) => {
      console.error('Unhandled Rejection at:', promise, 'reason:', reason);
    });

    // Uncaught exception handler
    process.on('uncaughtException', (error) => {
      console.error('Uncaught Exception:', error);
      process.exit(1);
    });
  }

  public start(): void {
    this.app.listen(this.port, () => {
      console.log(`
🚀 Application Transformation Analyzer API
📡 Server running on port ${this.port}
🌍 Environment: ${process.env.NODE_ENV || 'development'}
⚡ CORS origins: ${process.env.CORS_ORIGIN || 'http://localhost:3000, http://localhost:3001'}
🔐 Authentication: Disabled
📊 Analysis engine: ${process.env.ANALYSIS_ENGINE_URL || 'http://localhost:8000'}
      `);
    });
  }

  public getApp(): Application {
    return this.app;
  }
}

// Create and start server
const server = new Server();

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down gracefully');
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('SIGINT received, shutting down gracefully');
  process.exit(0);
});

// Start the server if this file is executed directly
if (require.main === module) {
  server.start();
}

export default server;