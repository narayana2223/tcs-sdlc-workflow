# Backend - Application Transformation Analyzer

Express TypeScript backend API server for the Application Transformation Analyzer.

## Features

- RESTful API with Express.js
- TypeScript for type safety
- CORS support for frontend integration
- Environment configuration with dotenv
- Security middleware with helmet
- Request logging with morgan

## Tech Stack

- **Express.js**: Web application framework
- **TypeScript**: Type-safe development
- **CORS**: Cross-origin resource sharing
- **Helmet**: Security middleware
- **Morgan**: HTTP request logging
- **dotenv**: Environment variable management

## Getting Started

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

Starts the development server with hot reload on port 5000.

### Production

```bash
npm run build
npm start
```

### Testing

```bash
npm test
```

## Project Structure

```
src/
├── controllers/    # Route handlers and business logic
├── services/      # Business services and external integrations
├── models/        # Data models and schemas
├── routes/        # API route definitions
└── utils/         # Utility functions and helpers
```

## API Endpoints

### Analysis Endpoints

- `POST /api/analysis` - Submit new analysis request
- `GET /api/analysis/:id` - Get analysis status
- `GET /api/analysis/:id/results` - Get analysis results
- `DELETE /api/analysis/:id` - Cancel analysis

### Health Check

- `GET /api/health` - Service health status

## Environment Variables

Create a `.env` file in the backend directory:

```env
PORT=5000
NODE_ENV=development
ANALYSIS_ENGINE_URL=http://localhost:8000
CORS_ORIGIN=http://localhost:3000
```

## Integration

The backend serves as the API layer between the frontend and the Python analysis engine:
- Receives analysis requests from frontend
- Forwards requests to analysis engine
- Manages analysis state and results
- Provides real-time progress updates