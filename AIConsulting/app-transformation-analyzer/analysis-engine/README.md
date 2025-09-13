# Analysis Engine - Application Transformation Analyzer

Python-based analysis engine that performs deep code analysis and generates transformation recommendations.

## Features

- Repository analysis from Git URLs
- Code complexity and quality metrics
- Dependency vulnerability scanning
- Architecture pattern detection
- Performance analysis
- Security assessment
- Transformation recommendations

## Tech Stack

- **Python 3.8+**: Core runtime
- **GitPython**: Git repository handling
- **NetworkX**: Dependency graph analysis
- **Pandas**: Data processing and analysis
- **NumPy**: Numerical computations
- **Matplotlib/Seaborn**: Data visualization
- **Scikit-learn**: Machine learning algorithms

## Getting Started

### Installation

```bash
pip install -r requirements.txt
```

Or install in development mode:

```bash
pip install -e .[dev]
```

### Running

```bash
python -m src.main
```

### Testing

```bash
pytest
```

### Code Formatting

```bash
black src/
flake8 src/
```

## Project Structure

```
src/
├── analyzers/      # Core analysis modules
├── evaluators/     # Code quality evaluators
├── transformers/   # Data transformation utilities
└── utils/          # Helper functions and utilities
```

## Analysis Modules

### Code Analyzers

- **ComplexityAnalyzer**: Measures cyclomatic and cognitive complexity
- **DependencyAnalyzer**: Analyzes project dependencies
- **ArchitectureAnalyzer**: Detects architectural patterns
- **SecurityAnalyzer**: Identifies security vulnerabilities

### Evaluators

- **QualityEvaluator**: Assesses overall code quality
- **MaintainabilityEvaluator**: Evaluates code maintainability
- **PerformanceEvaluator**: Analyzes performance characteristics

### Transformers

- **RecommendationEngine**: Generates transformation recommendations
- **RiskAssessment**: Calculates transformation risks
- **ReportGenerator**: Creates analysis reports

## Configuration

Create a `.env` file in the analysis-engine directory:

```env
LOG_LEVEL=INFO
CACHE_DIR=./cache
TEMP_DIR=./temp
MAX_REPO_SIZE_MB=500
ANALYSIS_TIMEOUT_MINUTES=30
```

## API Integration

The analysis engine can be used as:
1. **Standalone CLI tool**: Direct command-line usage
2. **HTTP service**: REST API for backend integration  
3. **Python library**: Import and use in other Python applications

## Supported Languages

- JavaScript/TypeScript
- Python
- Java
- C#
- Go
- Rust
- PHP
- Ruby

## Output Format

Analysis results are returned as structured JSON with:
- Project overview and metrics
- Code quality assessment
- Dependency analysis
- Architecture evaluation
- Prioritized recommendations
- Risk assessment