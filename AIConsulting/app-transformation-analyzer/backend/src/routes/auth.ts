/**
 * Authentication routes for JWT-based authentication
 * Handles user login, registration, and token management
 */

import { Router, Request, Response, NextFunction } from 'express';
import { body, validationResult } from 'express-validator';
import jwt, { SignOptions } from 'jsonwebtoken';
import bcrypt from 'bcrypt';
import rateLimit from 'express-rate-limit';

const router = Router();

// Mock user store (in production, this would be a database)
interface User {
  id: string;
  email: string;
  password: string;
  role: string;
  createdAt: Date;
  lastLogin?: Date;
}

// In-memory user store for demo purposes
const users: User[] = [
  {
    id: '1',
    email: 'demo@example.com',
    password: '$2b$10$rQj0KRHvjWp6bXQqK5FZ.OvK7YmqOLJ8OJLyL9w9/yK2L7oZV4OzG', // password: 'demo123'
    role: 'user',
    createdAt: new Date('2024-01-01'),
  },
  {
    id: '2',
    email: 'admin@example.com',
    password: '$2b$10$rQj0KRHvjWp6bXQqK5FZ.OvK7YmqOLJ8OJLyL9w9/yK2L7oZV4OzG', // password: 'admin123'
    role: 'admin',
    createdAt: new Date('2024-01-01'),
  },
];

// Rate limiting for auth endpoints
const authRateLimit = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 5, // Maximum 5 auth requests per window per IP
  message: {
    error: 'Rate Limit Exceeded',
    message: 'Too many authentication requests. Please try again later.',
    timestamp: new Date().toISOString(),
    statusCode: 429,
  },
  standardHeaders: true,
  legacyHeaders: false,
});

// Validation middleware
const validateLoginRequest = [
  body('email')
    .isEmail()
    .normalizeEmail()
    .withMessage('Valid email is required'),
  
  body('password')
    .isLength({ min: 6 })
    .withMessage('Password must be at least 6 characters long'),
];

const validateRegisterRequest = [
  body('email')
    .isEmail()
    .normalizeEmail()
    .withMessage('Valid email is required'),
  
  body('password')
    .isLength({ min: 8 })
    .withMessage('Password must be at least 8 characters long')
    .matches(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/)
    .withMessage('Password must contain at least one lowercase letter, one uppercase letter, and one number'),
  
  body('confirmPassword')
    .custom((value, { req }) => {
      if (value !== req.body.password) {
        throw new Error('Password confirmation does not match password');
      }
      return true;
    }),
];

// Helper function to handle validation errors
const handleValidationErrors = (req: Request, res: Response, next: NextFunction) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({
      success: false,
      error: {
        code: 'VALIDATION_ERROR',
        message: 'Validation failed',
        details: errors.array(),
      },
      timestamp: new Date().toISOString(),
      requestId: req.headers['x-request-id'],
    });
  }
  return next();
};

/**
 * POST /api/auth/login
 * Authenticate user and return JWT token
 */
router.post('/login',
  authRateLimit,
  validateLoginRequest,
  handleValidationErrors,
  async (req: Request, res: Response): Promise<any> => {
    try {
      const { email, password } = req.body;

      // Find user
      const user = users.find(u => u.email === email);
      if (!user) {
        return res.status(401).json({
          success: false,
          error: {
            code: 'INVALID_CREDENTIALS',
            message: 'Invalid email or password',
          },
          timestamp: new Date().toISOString(),
          requestId: req.headers['x-request-id'],
        });
      }

      // Verify password
      const isValidPassword = await bcrypt.compare(password, user.password);
      if (!isValidPassword) {
        return res.status(401).json({
          success: false,
          error: {
            code: 'INVALID_CREDENTIALS',
            message: 'Invalid email or password',
          },
          timestamp: new Date().toISOString(),
          requestId: req.headers['x-request-id'],
        });
      }

      // Generate JWT token
      const jwtSecret = process.env.JWT_SECRET;
      if (!jwtSecret) {
        console.error('JWT_SECRET environment variable is not set');
        return res.status(500).json({
          success: false,
          error: {
            code: 'INTERNAL_ERROR',
            message: 'Server configuration error',
          },
          timestamp: new Date().toISOString(),
          requestId: req.headers['x-request-id'],
        });
      }

      const token = jwt.sign(
        {
          id: user.id,
          email: user.email,
          role: user.role,
        },
        jwtSecret as string,
        { expiresIn: '24h' }
      );

      // Update last login (in production, this would update the database)
      user.lastLogin = new Date();

      res.json({
        success: true,
        data: {
          token,
          user: {
            id: user.id,
            email: user.email,
            role: user.role,
            lastLogin: user.lastLogin,
          },
          expiresIn: (process.env.JWT_EXPIRES_IN || '24h') as string | number,
        },
        timestamp: new Date().toISOString(),
        requestId: req.headers['x-request-id'],
      });

    } catch (error) {
      console.error('Login error:', error);
      return res.status(500).json({
        success: false,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Internal server error',
        },
        timestamp: new Date().toISOString(),
        requestId: req.headers['x-request-id'],
      });
    }
  }
);

/**
 * POST /api/auth/register
 * Register a new user account
 */
router.post('/register',
  authRateLimit,
  validateRegisterRequest,
  handleValidationErrors,
  async (req: Request, res: Response): Promise<any> => {
    try {
      const { email, password } = req.body;

      // Check if user already exists
      const existingUser = users.find(u => u.email === email);
      if (existingUser) {
        return res.status(409).json({
          success: false,
          error: {
            code: 'USER_EXISTS',
            message: 'User with this email already exists',
          },
          timestamp: new Date().toISOString(),
          requestId: req.headers['x-request-id'],
        });
      }

      // Hash password
      const saltRounds = 10;
      const hashedPassword = await bcrypt.hash(password, saltRounds);

      // Create new user
      const newUser: User = {
        id: (users.length + 1).toString(),
        email,
        password: hashedPassword,
        role: 'user',
        createdAt: new Date(),
      };

      users.push(newUser);

      // Generate JWT token
      const jwtSecret = process.env.JWT_SECRET;
      if (!jwtSecret) {
        console.error('JWT_SECRET environment variable is not set');
        return res.status(500).json({
          success: false,
          error: {
            code: 'INTERNAL_ERROR',
            message: 'Server configuration error',
          },
          timestamp: new Date().toISOString(),
          requestId: req.headers['x-request-id'],
        });
      }

      const token = jwt.sign(
        {
          id: newUser.id,
          email: newUser.email,
          role: newUser.role,
        },
        jwtSecret as string,
        { expiresIn: '24h' }
      );

      return res.status(201).json({
        success: true,
        data: {
          token,
          user: {
            id: newUser.id,
            email: newUser.email,
            role: newUser.role,
            createdAt: newUser.createdAt,
          },
          expiresIn: (process.env.JWT_EXPIRES_IN || '24h') as string | number,
        },
        message: 'User registered successfully',
        timestamp: new Date().toISOString(),
        requestId: req.headers['x-request-id'],
      });

    } catch (error) {
      console.error('Registration error:', error);
      return res.status(500).json({
        success: false,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Internal server error',
        },
        timestamp: new Date().toISOString(),
        requestId: req.headers['x-request-id'],
      });
    }
  }
);

/**
 * POST /api/auth/refresh
 * Refresh JWT token
 */
router.post('/refresh',
  authRateLimit,
  body('token').notEmpty().withMessage('Token is required'),
  handleValidationErrors,
  async (req: Request, res: Response): Promise<any> => {
    try {
      const { token } = req.body;

      const jwtSecret = process.env.JWT_SECRET;
      if (!jwtSecret) {
        console.error('JWT_SECRET environment variable is not set');
        return res.status(500).json({
          success: false,
          error: {
            code: 'INTERNAL_ERROR',
            message: 'Server configuration error',
          },
          timestamp: new Date().toISOString(),
          requestId: req.headers['x-request-id'],
        });
      }

      // Verify token (allow expired tokens for refresh)
      let decoded: any;
      try {
        decoded = jwt.verify(token, jwtSecret as string, { ignoreExpiration: true });
      } catch (error) {
        return res.status(401).json({
          success: false,
          error: {
            code: 'INVALID_TOKEN',
            message: 'Invalid token',
          },
          timestamp: new Date().toISOString(),
          requestId: req.headers['x-request-id'],
        });
      }

      // Check if user still exists
      const user = users.find(u => u.id === decoded.id);
      if (!user) {
        return res.status(401).json({
          success: false,
          error: {
            code: 'USER_NOT_FOUND',
            message: 'User not found',
          },
          timestamp: new Date().toISOString(),
          requestId: req.headers['x-request-id'],
        });
      }

      // Generate new token
      const newToken = jwt.sign(
        {
          id: user.id,
          email: user.email,
          role: user.role,
        },
        jwtSecret as string,
        { expiresIn: '24h' }
      );

      res.json({
        success: true,
        data: {
          token: newToken,
          user: {
            id: user.id,
            email: user.email,
            role: user.role,
            lastLogin: user.lastLogin,
          },
          expiresIn: (process.env.JWT_EXPIRES_IN || '24h') as string | number,
        },
        timestamp: new Date().toISOString(),
        requestId: req.headers['x-request-id'],
      });

    } catch (error) {
      console.error('Token refresh error:', error);
      return res.status(500).json({
        success: false,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Internal server error',
        },
        timestamp: new Date().toISOString(),
        requestId: req.headers['x-request-id'],
      });
    }
  }
);

/**
 * GET /api/auth/me
 * Get current user information
 */
router.get('/me',
  (req: any, res: Response, next: NextFunction) => {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];

    if (!token) {
      return res.status(401).json({
        success: false,
        error: {
          code: 'UNAUTHORIZED',
          message: 'Access token is required',
        },
        timestamp: new Date().toISOString(),
        requestId: req.headers['x-request-id'],
      });
    }

    const jwtSecret = process.env.JWT_SECRET;
    if (!jwtSecret) {
      console.error('JWT_SECRET environment variable is not set');
      return res.status(500).json({
        success: false,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Server configuration error',
        },
        timestamp: new Date().toISOString(),
        requestId: req.headers['x-request-id'],
      });
    }

    jwt.verify(token, jwtSecret as string, (err: any, user: any): any => {
      if (err) {
        return res.status(403).json({
          success: false,
          error: {
            code: 'FORBIDDEN',
            message: 'Invalid or expired token',
          },
          timestamp: new Date().toISOString(),
          requestId: req.headers['x-request-id'],
        });
      }

      const userData = users.find(u => u.id === user.id);
      if (!userData) {
        return res.status(404).json({
          success: false,
          error: {
            code: 'USER_NOT_FOUND',
            message: 'User not found',
          },
          timestamp: new Date().toISOString(),
          requestId: req.headers['x-request-id'],
        });
      }

      res.json({
        success: true,
        data: {
          user: {
            id: userData.id,
            email: userData.email,
            role: userData.role,
            createdAt: userData.createdAt,
            lastLogin: userData.lastLogin,
          },
        },
        timestamp: new Date().toISOString(),
        requestId: req.headers['x-request-id'],
      });
    });
  }
);

export default router;