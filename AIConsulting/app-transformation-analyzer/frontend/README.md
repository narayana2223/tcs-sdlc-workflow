# Frontend - Application Transformation Analyzer

React TypeScript frontend application for the Application Transformation Analyzer.

## Features

- Modern React 18 with TypeScript
- Material-UI components for consistent design
- D3.js for data visualizations
- Responsive design
- Real-time analysis progress tracking

## Tech Stack

- **React 18**: Modern React with hooks and concurrent features
- **TypeScript**: Type-safe development
- **Material-UI**: Component library and theming
- **D3.js**: Data visualization library
- **React Router**: Client-side routing

## Getting Started

### Installation

```bash
npm install
```

### Development

```bash
npm start
```

Runs the app in development mode on [http://localhost:3000](http://localhost:3000).

### Building

```bash
npm run build
```

Builds the app for production to the `build` folder.

### Testing

```bash
npm test
```

Launches the test runner in interactive watch mode.

## Project Structure

```
src/
├── components/     # Reusable UI components
├── pages/         # Page components and routing
├── services/      # API services and data fetching
├── utils/         # Utility functions and helpers
└── types/         # TypeScript type definitions
```

## Key Components

- **Dashboard**: Main analysis dashboard with charts and metrics
- **AnalysisForm**: Form for configuring analysis parameters
- **ResultsViewer**: Display analysis results and recommendations
- **ProgressTracker**: Real-time analysis progress display

## API Integration

The frontend communicates with the backend API for:
- Submitting analysis requests
- Retrieving analysis results
- Real-time progress updates
- Authentication and user management