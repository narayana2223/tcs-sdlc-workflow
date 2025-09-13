# Application Transformation Analyzer

A comprehensive full-stack application that analyzes codebases and provides intelligent recommendations for application transformation, modernization, and optimization.

## Overview

The Application Transformation Analyzer is designed to help organizations understand their existing applications and plan their transformation journey. It provides detailed analysis of code quality, architecture patterns, security vulnerabilities, and performance bottlenecks.

## Features

- **Comprehensive Code Analysis**: Analyze code complexity, maintainability, and quality metrics
- **Dependency Management**: Identify outdated dependencies and security vulnerabilities  
- **Architecture Assessment**: Evaluate architectural patterns and identify anti-patterns
- **Transformation Recommendations**: Get prioritized recommendations for modernization
- **Risk Assessment**: Understand transformation risks and mitigation strategies
- **Interactive Dashboard**: Visualize analysis results with charts and graphs

## Project Structure

```
app-transformation-analyzer/
├── frontend/           # React TypeScript frontend
├── backend/           # Express TypeScript API server
├── analysis-engine/   # Python analysis engine
└── shared/           # Shared types and constants
```

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.8+
- Git

### Installation

1. Clone the repository
2. Install frontend dependencies: `cd frontend && npm install`
3. Install backend dependencies: `cd backend && npm install`
4. Install Python dependencies: `cd analysis-engine && pip install -r requirements.txt`

### Running the Application

1. Start the analysis engine: `cd analysis-engine && python -m src.main`
2. Start the backend server: `cd backend && npm run dev`
3. Start the frontend: `cd frontend && npm start`

The application will be available at `http://localhost:3000`

## Documentation

- [Frontend Documentation](./frontend/README.md)
- [Backend Documentation](./backend/README.md)
- [Analysis Engine Documentation](./analysis-engine/README.md)

## Contributing

Please read our contributing guidelines and code of conduct before submitting pull requests.

## License

MIT License - see LICENSE file for details