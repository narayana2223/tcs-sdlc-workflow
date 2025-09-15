/**
 * Mock Prototype Service
 * Generates working transformation examples and prototypes
 */

interface CodeExample {
  id: string;
  title: string;
  description: string;
  language: string;
  beforeCode: string;
  afterCode: string;
  explanation: string;
  benefits: string[];
  complexity: 'low' | 'medium' | 'high';
  estimatedTime: string;
}

interface ArchitectureDiagram {
  id: string;
  title: string;
  type: 'before' | 'after' | 'comparison';
  description: string;
  components: {
    id: string;
    name: string;
    type: string;
    position: { x: number; y: number };
    connections: string[];
  }[];
  improvements: string[];
}

interface ImplementationStep {
  id: string;
  title: string;
  description: string;
  codeChanges?: string;
  configChanges?: string;
  testingNotes?: string;
  estimatedTime: string;
  prerequisites: string[];
}

interface TransformationPrototype {
  id: string;
  title: string;
  description: string;
  category: 'microservices' | 'containerization' | 'configuration' | 'logging' | 'scaling' | 'security';
  factor: string;
  codeExamples: CodeExample[];
  architectureDiagrams: ArchitectureDiagram[];
  implementationSteps: ImplementationStep[];
  performanceMetrics: {
    before: { [key: string]: number | string };
    after: { [key: string]: number | string };
    improvement: string;
  };
  testCases: {
    id: string;
    name: string;
    input: any;
    expectedOutput: any;
    testCode: string;
  }[];
}

export class MockPrototypeService {
  private prototypes: TransformationPrototype[] = [];

  constructor() {
    this.generatePrototypes();
  }

  private generatePrototypes(): void {
    this.prototypes = [
      {
        id: 'config-externalization',
        title: 'Configuration Externalization',
        description: 'Transform hardcoded configuration to environment-based external configuration',
        category: 'configuration',
        factor: 'config',
        codeExamples: [
          {
            id: 'config-before-after',
            title: 'Database Configuration',
            description: 'Move database configuration from hardcoded values to environment variables',
            language: 'javascript',
            beforeCode: `// Before: Hardcoded configuration
class DatabaseConfig {
  constructor() {
    this.host = 'localhost';
    this.port = 5432;
    this.database = 'myapp';
    this.username = 'admin';
    this.password = 'secret123';
    this.ssl = false;
    this.pool = {
      min: 2,
      max: 10
    };
  }

  getConnectionString() {
    return \`postgresql://\${this.username}:\${this.password}@\${this.host}:\${this.port}/\${this.database}\`;
  }
}

// Usage
const dbConfig = new DatabaseConfig();
const connection = createConnection(dbConfig.getConnectionString());`,
            afterCode: `// After: Environment-based configuration
class DatabaseConfig {
  constructor() {
    this.host = process.env.DB_HOST || 'localhost';
    this.port = parseInt(process.env.DB_PORT) || 5432;
    this.database = process.env.DB_NAME || 'myapp';
    this.username = process.env.DB_USERNAME;
    this.password = process.env.DB_PASSWORD;
    this.ssl = process.env.DB_SSL === 'true';
    this.pool = {
      min: parseInt(process.env.DB_POOL_MIN) || 2,
      max: parseInt(process.env.DB_POOL_MAX) || 10
    };

    this.validateConfig();
  }

  validateConfig() {
    const required = ['DB_USERNAME', 'DB_PASSWORD'];
    const missing = required.filter(key => !process.env[key]);

    if (missing.length > 0) {
      throw new Error(\`Missing required environment variables: \${missing.join(', ')}\`);
    }
  }

  getConnectionString() {
    return \`postgresql://\${this.username}:\${this.password}@\${this.host}:\${this.port}/\${this.database}\`;
  }
}

// Usage with environment validation
const dbConfig = new DatabaseConfig();
const connection = createConnection(dbConfig.getConnectionString());`,
            explanation: 'This transformation moves all configuration values to environment variables, making the application configurable without code changes and more secure by keeping secrets out of the codebase.',
            benefits: [
              'No secrets in code',
              'Environment-specific configuration',
              'Easy deployment across environments',
              'Better security practices',
              'Configuration validation'
            ],
            complexity: 'low',
            estimatedTime: '2-4 hours'
          },
          {
            id: 'config-validation',
            title: 'Configuration Schema Validation',
            description: 'Add comprehensive configuration validation and schema enforcement',
            language: 'javascript',
            beforeCode: `// Before: No validation
const config = {
  port: process.env.PORT,
  apiKey: process.env.API_KEY,
  timeout: process.env.TIMEOUT
};

app.listen(config.port);`,
            afterCode: `// After: Schema validation with Joi
const Joi = require('joi');

const configSchema = Joi.object({
  port: Joi.number().port().default(3000),
  apiKey: Joi.string().required().min(20),
  timeout: Joi.number().min(1000).max(30000).default(5000),
  environment: Joi.string().valid('development', 'staging', 'production').default('development'),
  logLevel: Joi.string().valid('debug', 'info', 'warn', 'error').default('info')
});

class ConfigManager {
  constructor() {
    this.config = this.loadAndValidateConfig();
  }

  loadAndValidateConfig() {
    const rawConfig = {
      port: process.env.PORT,
      apiKey: process.env.API_KEY,
      timeout: process.env.TIMEOUT,
      environment: process.env.NODE_ENV,
      logLevel: process.env.LOG_LEVEL
    };

    const { error, value } = configSchema.validate(rawConfig, {
      allowUnknown: false,
      stripUnknown: true
    });

    if (error) {
      throw new Error(\`Configuration validation failed: \${error.details.map(d => d.message).join(', ')}\`);
    }

    return value;
  }

  get(key) {
    return this.config[key];
  }
}

const configManager = new ConfigManager();
app.listen(configManager.get('port'));`,
            explanation: 'Adding schema validation ensures configuration integrity and provides clear error messages for misconfigurations.',
            benefits: [
              'Early error detection',
              'Clear validation messages',
              'Type coercion and defaults',
              'Documented configuration schema',
              'Prevents runtime configuration errors'
            ],
            complexity: 'medium',
            estimatedTime: '4-6 hours'
          }
        ],
        architectureDiagrams: [
          {
            id: 'config-before',
            title: 'Before: Hardcoded Configuration',
            type: 'before',
            description: 'Configuration is hardcoded in the application, making it inflexible and insecure',
            components: [
              { id: 'app', name: 'Application', type: 'service', position: { x: 200, y: 150 }, connections: ['db'] },
              { id: 'db', name: 'Database\n(hardcoded connection)', type: 'database', position: { x: 400, y: 150 }, connections: [] },
              { id: 'config', name: 'Hardcoded Config\n(in source code)', type: 'config', position: { x: 200, y: 50 }, connections: ['app'] }
            ],
            improvements: []
          },
          {
            id: 'config-after',
            title: 'After: External Configuration',
            type: 'after',
            description: 'Configuration is externalized to environment variables and config files',
            components: [
              { id: 'app', name: 'Application', type: 'service', position: { x: 200, y: 200 }, connections: ['db'] },
              { id: 'db', name: 'Database', type: 'database', position: { x: 400, y: 200 }, connections: [] },
              { id: 'env', name: 'Environment\nVariables', type: 'config', position: { x: 50, y: 100 }, connections: ['app'] },
              { id: 'configmap', name: 'Config Maps', type: 'config', position: { x: 200, y: 100 }, connections: ['app'] },
              { id: 'secrets', name: 'Secrets Store', type: 'security', position: { x: 350, y: 100 }, connections: ['app'] }
            ],
            improvements: [
              'Secrets stored securely',
              'Environment-specific configuration',
              'No configuration in source code',
              'Runtime configuration validation'
            ]
          }
        ],
        implementationSteps: [
          {
            id: 'step-1',
            title: 'Audit Current Configuration',
            description: 'Identify all hardcoded configuration values in the codebase',
            codeChanges: `grep -r "localhost\\|127.0.0.1\\|hardcoded" src/
find src/ -name "*.js" -exec grep -l "password.*=" {} \\;`,
            estimatedTime: '1-2 hours',
            prerequisites: []
          },
          {
            id: 'step-2',
            title: 'Create Configuration Schema',
            description: 'Define configuration schema with validation rules',
            codeChanges: `// config/schema.js
const configSchema = {
  database: {
    host: { type: 'string', required: false, default: 'localhost' },
    port: { type: 'number', required: false, default: 5432 },
    // ... other fields
  }
};`,
            estimatedTime: '2-3 hours',
            prerequisites: ['step-1']
          },
          {
            id: 'step-3',
            title: 'Implement Configuration Manager',
            description: 'Create centralized configuration management with validation',
            codeChanges: 'See code examples above for ConfigManager implementation',
            estimatedTime: '3-4 hours',
            prerequisites: ['step-2']
          },
          {
            id: 'step-4',
            title: 'Update Application Code',
            description: 'Replace hardcoded values with configuration manager calls',
            codeChanges: `// Replace hardcoded values
- const dbHost = 'localhost';
+ const dbHost = configManager.get('database.host');`,
            estimatedTime: '4-6 hours',
            prerequisites: ['step-3']
          },
          {
            id: 'step-5',
            title: 'Create Environment Templates',
            description: 'Create environment-specific configuration templates',
            codeChanges: `# .env.development
DB_HOST=localhost
DB_PORT=5432

# .env.production
DB_HOST=prod-db.example.com
DB_PORT=5432`,
            estimatedTime: '1-2 hours',
            prerequisites: ['step-4']
          }
        ],
        performanceMetrics: {
          before: {
            'Configuration Errors': '15 per month',
            'Deployment Time': '45 minutes',
            'Environment Setup': '2 hours',
            'Security Score': '6/10'
          },
          after: {
            'Configuration Errors': '2 per month',
            'Deployment Time': '15 minutes',
            'Environment Setup': '20 minutes',
            'Security Score': '9/10'
          },
          improvement: '87% reduction in configuration errors, 67% faster deployments'
        },
        testCases: [
          {
            id: 'test-validation',
            name: 'Configuration Validation Test',
            input: { port: 'invalid', apiKey: 'short' },
            expectedOutput: { error: 'Configuration validation failed' },
            testCode: `test('should validate configuration', () => {
  process.env.PORT = 'invalid';
  process.env.API_KEY = 'short';

  expect(() => new ConfigManager()).toThrow('Configuration validation failed');
});`
          },
          {
            id: 'test-defaults',
            name: 'Default Values Test',
            input: {},
            expectedOutput: { port: 3000, timeout: 5000 },
            testCode: `test('should apply default values', () => {
  delete process.env.PORT;
  delete process.env.TIMEOUT;

  const config = new ConfigManager();
  expect(config.get('port')).toBe(3000);
  expect(config.get('timeout')).toBe(5000);
});`
          }
        ]
      },
      {
        id: 'microservices-decomposition',
        title: 'Microservices Decomposition',
        description: 'Break down monolithic application into microservices architecture',
        category: 'microservices',
        factor: 'processes',
        codeExamples: [
          {
            id: 'monolith-to-microservices',
            title: 'User Service Extraction',
            description: 'Extract user management functionality from monolith to separate microservice',
            language: 'javascript',
            beforeCode: `// Before: Monolithic application
class MonolithicApp {
  constructor() {
    this.userService = new UserService();
    this.orderService = new OrderService();
    this.paymentService = new PaymentService();
    this.notificationService = new NotificationService();
  }

  // User management endpoints
  async createUser(userData) {
    const user = await this.userService.create(userData);
    await this.notificationService.sendWelcomeEmail(user);
    return user;
  }

  async getUser(userId) {
    return await this.userService.findById(userId);
  }

  // Order management endpoints
  async createOrder(orderData) {
    const user = await this.userService.findById(orderData.userId);
    if (!user) throw new Error('User not found');

    const order = await this.orderService.create(orderData);
    await this.paymentService.processPayment(order);
    await this.notificationService.sendOrderConfirmation(user, order);

    return order;
  }
}

// Single database for all services
class Database {
  constructor() {
    this.users = [];
    this.orders = [];
    this.payments = [];
  }
}`,
            afterCode: `// After: Microservices architecture
// User Service (separate service)
class UserMicroservice {
  constructor() {
    this.database = new UserDatabase();
    this.eventBus = new EventBus();
  }

  async createUser(userData) {
    const user = await this.database.users.create(userData);

    // Publish event for other services
    await this.eventBus.publish('user.created', {
      userId: user.id,
      email: user.email,
      name: user.name
    });

    return user;
  }

  async getUser(userId) {
    return await this.database.users.findById(userId);
  }
}

// Order Service (separate service)
class OrderMicroservice {
  constructor() {
    this.database = new OrderDatabase();
    this.eventBus = new EventBus();
    this.userServiceClient = new UserServiceClient();
  }

  async createOrder(orderData) {
    // Call User Service via API
    const user = await this.userServiceClient.getUser(orderData.userId);
    if (!user) throw new Error('User not found');

    const order = await this.database.orders.create(orderData);

    // Publish events
    await this.eventBus.publish('order.created', {
      orderId: order.id,
      userId: order.userId,
      amount: order.total
    });

    return order;
  }
}

// API Gateway for routing
class APIGateway {
  constructor() {
    this.userService = new UserServiceProxy();
    this.orderService = new OrderServiceProxy();
    this.paymentService = new PaymentServiceProxy();
  }

  route(request) {
    const { path, method } = request;

    if (path.startsWith('/api/users')) {
      return this.userService.handle(request);
    } else if (path.startsWith('/api/orders')) {
      return this.orderService.handle(request);
    } else if (path.startsWith('/api/payments')) {
      return this.paymentService.handle(request);
    }

    throw new Error('Route not found');
  }
}`,
            explanation: 'This transformation breaks the monolith into focused microservices, each with its own database and clear boundaries. Services communicate via events and APIs.',
            benefits: [
              'Independent deployment',
              'Technology diversity',
              'Fault isolation',
              'Team autonomy',
              'Scalability per service'
            ],
            complexity: 'high',
            estimatedTime: '3-6 months'
          }
        ],
        architectureDiagrams: [
          {
            id: 'monolith-before',
            title: 'Before: Monolithic Architecture',
            type: 'before',
            description: 'Single application with all functionality coupled together',
            components: [
              { id: 'monolith', name: 'Monolithic App\n(Users, Orders, Payments)', type: 'service', position: { x: 200, y: 150 }, connections: ['db'] },
              { id: 'db', name: 'Single Database', type: 'database', position: { x: 200, y: 300 }, connections: [] },
              { id: 'client', name: 'Client Applications', type: 'client', position: { x: 200, y: 50 }, connections: ['monolith'] }
            ],
            improvements: []
          },
          {
            id: 'microservices-after',
            title: 'After: Microservices Architecture',
            type: 'after',
            description: 'Decomposed into independent services with clear boundaries',
            components: [
              { id: 'gateway', name: 'API Gateway', type: 'gateway', position: { x: 300, y: 50 }, connections: ['user-service', 'order-service', 'payment-service'] },
              { id: 'user-service', name: 'User Service', type: 'service', position: { x: 100, y: 150 }, connections: ['user-db'] },
              { id: 'order-service', name: 'Order Service', type: 'service', position: { x: 300, y: 150 }, connections: ['order-db'] },
              { id: 'payment-service', name: 'Payment Service', type: 'service', position: { x: 500, y: 150 }, connections: ['payment-db'] },
              { id: 'user-db', name: 'User DB', type: 'database', position: { x: 100, y: 250 }, connections: [] },
              { id: 'order-db', name: 'Order DB', type: 'database', position: { x: 300, y: 250 }, connections: [] },
              { id: 'payment-db', name: 'Payment DB', type: 'database', position: { x: 500, y: 250 }, connections: [] },
              { id: 'event-bus', name: 'Event Bus', type: 'messaging', position: { x: 300, y: 350 }, connections: ['user-service', 'order-service', 'payment-service'] },
              { id: 'client', name: 'Client Applications', type: 'client', position: { x: 300, y: -50 }, connections: ['gateway'] }
            ],
            improvements: [
              'Independent scaling',
              'Fault isolation between services',
              'Technology diversity per service',
              'Independent deployment cycles',
              'Clear service boundaries'
            ]
          }
        ],
        implementationSteps: [
          {
            id: 'step-1',
            title: 'Domain Analysis and Bounded Contexts',
            description: 'Identify business domains and service boundaries using Domain-Driven Design',
            codeChanges: `// Identify bounded contexts
1. User Management (authentication, profiles, preferences)
2. Order Processing (cart, checkout, fulfillment)
3. Payment Processing (billing, transactions, refunds)
4. Inventory Management (products, stock, catalog)`,
            estimatedTime: '2-3 weeks',
            prerequisites: []
          },
          {
            id: 'step-2',
            title: 'Data Migration Strategy',
            description: 'Plan database separation and data migration between services',
            codeChanges: `// Database separation plan
CREATE DATABASE user_service;
CREATE DATABASE order_service;
CREATE DATABASE payment_service;

-- Migration scripts for data distribution`,
            estimatedTime: '3-4 weeks',
            prerequisites: ['step-1']
          },
          {
            id: 'step-3',
            title: 'Service Interface Design',
            description: 'Design REST APIs and event schemas for service communication',
            codeChanges: `// User Service API
GET /api/users/:id
POST /api/users
PUT /api/users/:id

// Events
user.created
user.updated
user.deleted`,
            estimatedTime: '2-3 weeks',
            prerequisites: ['step-1']
          }
        ],
        performanceMetrics: {
          before: {
            'Deployment Frequency': '1 per month',
            'Lead Time': '2 weeks',
            'MTTR': '4 hours',
            'Team Productivity': '60%'
          },
          after: {
            'Deployment Frequency': '10 per day',
            'Lead Time': '2 days',
            'MTTR': '30 minutes',
            'Team Productivity': '85%'
          },
          improvement: '10x deployment frequency, 87% faster recovery'
        },
        testCases: [
          {
            id: 'test-service-isolation',
            name: 'Service Isolation Test',
            input: { userServiceDown: true, orderRequest: {} },
            expectedOutput: { status: 'partial_failure', orderCreated: false },
            testCode: `test('should handle service failures gracefully', async () => {
  // Simulate user service down
  userServiceMock.mockRejectedValue(new Error('Service unavailable'));

  const result = await orderService.createOrder({userId: 123});
  expect(result.status).toBe('partial_failure');
});`
          }
        ]
      }
    ];
  }

  async getAllPrototypes(): Promise<TransformationPrototype[]> {
    return this.prototypes;
  }

  async getPrototypeById(id: string): Promise<TransformationPrototype | null> {
    return this.prototypes.find(p => p.id === id) || null;
  }

  async getPrototypesByCategory(category: string): Promise<TransformationPrototype[]> {
    return this.prototypes.filter(p => p.category === category);
  }

  async getPrototypesByFactor(factor: string): Promise<TransformationPrototype[]> {
    return this.prototypes.filter(p => p.factor === factor);
  }

  async generateCustomPrototype(requirements: {
    factor: string;
    complexity: 'low' | 'medium' | 'high';
    technology: string;
    useCase: string;
  }): Promise<TransformationPrototype> {
    // Generate a custom prototype based on requirements
    const customPrototype: TransformationPrototype = {
      id: `custom-${Date.now()}`,
      title: `Custom ${requirements.factor} Transformation`,
      description: `Generated transformation for ${requirements.useCase} using ${requirements.technology}`,
      category: 'configuration',
      factor: requirements.factor,
      codeExamples: [],
      architectureDiagrams: [],
      implementationSteps: [],
      performanceMetrics: {
        before: {},
        after: {},
        improvement: 'Custom transformation benefits'
      },
      testCases: []
    };

    return customPrototype;
  }
}