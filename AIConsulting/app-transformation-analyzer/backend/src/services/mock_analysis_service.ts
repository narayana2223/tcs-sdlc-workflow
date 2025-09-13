/**
 * Mock Analysis Service - Generates realistic analysis data
 * Provides comprehensive mock results for repository analysis
 */

export interface MockAnalysisResult {
  jobId: string;
  repositoryUrl: string;
  status: 'completed';
  progress: 100;
  results: {
    repository: {
      name: string;
      fullName: string;
      description: string;
      language: string;
      size: number;
      createdAt: string;
      updatedAt: string;
      stars: number;
      forks: number;
      openIssues: number;
    };
    analysis: {
      totalFiles: number;
      totalLinesOfCode: number;
      languages: { [key: string]: { files: number; lines: number; percentage: number } };
      components: {
        name: string;
        type: string;
        files: number;
        complexity: number;
        dependencies: string[];
      }[];
      architecture: {
        patterns: string[];
        layers: string[];
        frameworks: string[];
        buildTools: string[];
        testingFrameworks: string[];
      };
      dependencies: {
        total: number;
        direct: number;
        dev: number;
        outdated: number;
        vulnerable: number;
        list: {
          name: string;
          version: string;
          type: 'production' | 'development';
          outdated: boolean;
          vulnerable: boolean;
          severity?: 'low' | 'medium' | 'high' | 'critical';
        }[];
      };
      codeQuality: {
        maintainabilityIndex: number;
        complexity: number;
        duplication: number;
        testCoverage: number;
        technicalDebt: number;
      };
    };
    insights: {
      strengths: string[];
      improvements: string[];
      recommendations: string[];
    };
  };
  metadata: {
    analysisTime: number;
    timestamp: string;
  };
}

export class MockAnalysisService {
  private static repositoryData: { [key: string]: Partial<MockAnalysisResult['results']['repository']> } = {
    'https://github.com/facebook/react': {
      name: 'react',
      fullName: 'facebook/react',
      description: 'The library for web and native user interfaces',
      language: 'JavaScript',
      stars: 218000,
      forks: 45000,
      openIssues: 1200,
    },
    'https://github.com/expressjs/express': {
      name: 'express',
      fullName: 'expressjs/express',
      description: 'Fast, unopinionated, minimalist web framework for node.',
      language: 'JavaScript',
      stars: 63000,
      forks: 13000,
      openIssues: 150,
    },
    'https://github.com/microsoft/vscode': {
      name: 'vscode',
      fullName: 'microsoft/vscode',
      description: 'Visual Studio Code',
      language: 'TypeScript',
      stars: 155000,
      forks: 28000,
      openIssues: 5000,
    },
    'https://github.com/vercel/next.js': {
      name: 'next.js',
      fullName: 'vercel/next.js',
      description: 'The React Framework for the Web',
      language: 'TypeScript',
      stars: 118000,
      forks: 25000,
      openIssues: 2000,
    },
  };

  static generateMockAnalysis(repositoryUrl: string): MockAnalysisResult {
    const jobId = this.generateJobId();
    const repoInfo = this.repositoryData[repositoryUrl] || this.generateGenericRepoInfo(repositoryUrl);

    return {
      jobId,
      repositoryUrl,
      status: 'completed',
      progress: 100,
      results: {
        repository: {
          name: repoInfo.name || this.extractRepoName(repositoryUrl),
          fullName: repoInfo.fullName || this.extractFullName(repositoryUrl),
          description: repoInfo.description || 'A software project',
          language: repoInfo.language || 'JavaScript',
          size: Math.floor(Math.random() * 50000) + 5000,
          createdAt: new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000).toISOString(),
          updatedAt: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
          stars: repoInfo.stars || Math.floor(Math.random() * 10000),
          forks: repoInfo.forks || Math.floor(Math.random() * 2000),
          openIssues: repoInfo.openIssues || Math.floor(Math.random() * 500),
        },
        analysis: this.generateAnalysisData(repoInfo.language || 'JavaScript'),
        insights: this.generateInsights(),
      },
      metadata: {
        analysisTime: Math.floor(Math.random() * 180) + 60, // 1-3 minutes
        timestamp: new Date().toISOString(),
      },
    };
  }

  private static generateJobId(): string {
    // Generate a UUID-like string
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }

  private static extractRepoName(url: string): string {
    const match = url.match(/\/([^\/]+)(?:\.git)?$/);
    return match ? match[1] : 'unknown-repo';
  }

  private static extractFullName(url: string): string {
    const match = url.match(/github\.com\/([^\/]+\/[^\/]+)/);
    return match ? match[1].replace('.git', '') : 'unknown/repo';
  }

  private static generateGenericRepoInfo(url: string) {
    const languages = ['JavaScript', 'TypeScript', 'Python', 'Java', 'Go', 'Rust', 'C#'];
    return {
      name: this.extractRepoName(url),
      fullName: this.extractFullName(url),
      description: 'A software development project',
      language: languages[Math.floor(Math.random() * languages.length)],
      stars: Math.floor(Math.random() * 1000),
      forks: Math.floor(Math.random() * 200),
      openIssues: Math.floor(Math.random() * 50),
    };
  }

  private static generateAnalysisData(primaryLanguage: string) {
    const languages = this.generateLanguageBreakdown(primaryLanguage);
    const totalFiles = Math.floor(Math.random() * 500) + 50;
    const totalLinesOfCode = Math.floor(Math.random() * 50000) + 5000;

    return {
      totalFiles,
      totalLinesOfCode,
      languages,
      components: this.generateComponents(),
      architecture: this.generateArchitecture(primaryLanguage),
      dependencies: this.generateDependencies(),
      codeQuality: this.generateCodeQuality(),
    };
  }

  private static generateLanguageBreakdown(primaryLanguage: string) {
    const allLanguages = ['JavaScript', 'TypeScript', 'CSS', 'HTML', 'JSON', 'Markdown', 'YAML'];
    const languages: { [key: string]: { files: number; lines: number; percentage: number } } = {};

    // Primary language gets largest share
    languages[primaryLanguage] = {
      files: Math.floor(Math.random() * 100) + 50,
      lines: Math.floor(Math.random() * 20000) + 10000,
      percentage: Math.floor(Math.random() * 30) + 50,
    };

    // Add 2-4 other languages
    const otherLanguages = allLanguages
      .filter(lang => lang !== primaryLanguage)
      .sort(() => 0.5 - Math.random())
      .slice(0, Math.floor(Math.random() * 3) + 2);

    let remainingPercentage = 100 - languages[primaryLanguage].percentage;

    otherLanguages.forEach((lang, index) => {
      const percentage = index === otherLanguages.length - 1
        ? remainingPercentage
        : Math.floor(Math.random() * (remainingPercentage / 2));

      languages[lang] = {
        files: Math.floor(Math.random() * 30) + 5,
        lines: Math.floor(Math.random() * 5000) + 500,
        percentage,
      };

      remainingPercentage -= percentage;
    });

    return languages;
  }

  private static generateComponents() {
    const componentTypes = ['Service', 'Controller', 'Model', 'Component', 'Utility', 'Helper', 'Module'];
    const components = [];

    for (let i = 0; i < Math.floor(Math.random() * 8) + 3; i++) {
      const type = componentTypes[Math.floor(Math.random() * componentTypes.length)];
      components.push({
        name: `${type}${i + 1}`,
        type,
        files: Math.floor(Math.random() * 10) + 1,
        complexity: Math.floor(Math.random() * 100) + 10,
        dependencies: this.generateRandomDependencies(),
      });
    }

    return components;
  }

  private static generateRandomDependencies(): string[] {
    const allDeps = ['Database', 'Cache', 'Logger', 'Validator', 'Router', 'Middleware', 'Utils'];
    return allDeps
      .sort(() => 0.5 - Math.random())
      .slice(0, Math.floor(Math.random() * 4) + 1);
  }

  private static generateArchitecture(primaryLanguage: string) {
    const patterns = {
      JavaScript: ['MVC', 'Component-based', 'Functional', 'Event-driven'],
      TypeScript: ['MVC', 'MVVM', 'Clean Architecture', 'Hexagonal'],
      Python: ['MVC', 'Django Pattern', 'Flask Pattern', 'Microservices'],
      Java: ['MVC', 'Spring Pattern', 'Microservices', 'Layered'],
    };

    const frameworks = {
      JavaScript: ['React', 'Express', 'Node.js', 'Jest'],
      TypeScript: ['React', 'Angular', 'NestJS', 'TypeORM'],
      Python: ['Django', 'Flask', 'FastAPI', 'SQLAlchemy'],
      Java: ['Spring Boot', 'Hibernate', 'Maven', 'JUnit'],
    };

    return {
      patterns: (patterns[primaryLanguage as keyof typeof patterns] || patterns.JavaScript)
        .sort(() => 0.5 - Math.random())
        .slice(0, 2),
      layers: ['Presentation', 'Business Logic', 'Data Access', 'Infrastructure'],
      frameworks: (frameworks[primaryLanguage as keyof typeof frameworks] || frameworks.JavaScript)
        .sort(() => 0.5 - Math.random())
        .slice(0, 3),
      buildTools: ['npm', 'webpack', 'babel', 'eslint'],
      testingFrameworks: ['Jest', 'Mocha', 'Cypress', 'Testing Library'],
    };
  }

  private static generateDependencies() {
    const total = Math.floor(Math.random() * 100) + 20;
    const direct = Math.floor(total * 0.3);
    const dev = Math.floor(total * 0.2);
    const outdated = Math.floor(total * 0.15);
    const vulnerable = Math.floor(total * 0.1);

    const dependencyNames = [
      'lodash', 'axios', 'express', 'react', 'vue', 'angular',
      'typescript', 'webpack', 'babel', 'eslint', 'prettier',
      'jest', 'mocha', 'chai', 'sinon', 'moment', 'dayjs'
    ];

    const list = [];
    for (let i = 0; i < Math.min(total, 50); i++) {
      const name = dependencyNames[Math.floor(Math.random() * dependencyNames.length)];
      const isOutdated = Math.random() < 0.15;
      const isVulnerable = Math.random() < 0.1;

      list.push({
        name: `${name}-${i}`,
        version: `${Math.floor(Math.random() * 5) + 1}.${Math.floor(Math.random() * 10)}.${Math.floor(Math.random() * 10)}`,
        type: Math.random() < 0.7 ? 'production' as const : 'development' as const,
        outdated: isOutdated,
        vulnerable: isVulnerable,
        severity: isVulnerable
          ? (['low', 'medium', 'high', 'critical'] as const)[Math.floor(Math.random() * 4)]
          : undefined,
      });
    }

    return {
      total,
      direct,
      dev,
      outdated,
      vulnerable,
      list,
    };
  }

  private static generateCodeQuality() {
    return {
      maintainabilityIndex: Math.floor(Math.random() * 40) + 60, // 60-100
      complexity: Math.floor(Math.random() * 30) + 10, // 10-40
      duplication: Math.floor(Math.random() * 15) + 5, // 5-20%
      testCoverage: Math.floor(Math.random() * 40) + 60, // 60-100%
      technicalDebt: Math.floor(Math.random() * 10) + 5, // 5-15 days
    };
  }

  private static generateInsights() {
    const strengthsPool = [
      'Well-structured codebase with clear separation of concerns',
      'Comprehensive test coverage across major components',
      'Modern development practices and tooling',
      'Good documentation and code comments',
      'Consistent coding standards throughout the project',
      'Efficient dependency management',
      'Strong error handling and logging practices',
    ];

    const improvementsPool = [
      'Consider updating outdated dependencies for security',
      'Some components could benefit from reduced complexity',
      'Test coverage could be improved in utility modules',
      'Documentation could be expanded for new contributors',
      'Code duplication detected in several modules',
      'Performance optimizations possible in data processing',
      'Consider implementing automated code quality checks',
    ];

    const recommendationsPool = [
      'Implement 12-factor app principles for better scalability',
      'Add continuous integration and deployment pipelines',
      'Consider microservices architecture for better modularity',
      'Implement comprehensive monitoring and observability',
      'Add automated security scanning to the development workflow',
      'Establish code review guidelines and practices',
      'Consider adopting container-based deployment strategies',
    ];

    return {
      strengths: strengthsPool.sort(() => 0.5 - Math.random()).slice(0, 3),
      improvements: improvementsPool.sort(() => 0.5 - Math.random()).slice(0, 3),
      recommendations: recommendationsPool.sort(() => 0.5 - Math.random()).slice(0, 3),
    };
  }

  static async simulateAnalysisProgress(onProgress: (progress: number, message: string) => void): Promise<void> {
    const steps = [
      { progress: 10, message: 'Cloning repository...' },
      { progress: 25, message: 'Analyzing file structure...' },
      { progress: 40, message: 'Processing source code...' },
      { progress: 55, message: 'Analyzing dependencies...' },
      { progress: 70, message: 'Evaluating code quality...' },
      { progress: 85, message: 'Detecting architecture patterns...' },
      { progress: 100, message: 'Analysis complete!' },
    ];

    for (const step of steps) {
      await new Promise(resolve => setTimeout(resolve, Math.random() * 2000 + 1000));
      onProgress(step.progress, step.message);
    }
  }
}