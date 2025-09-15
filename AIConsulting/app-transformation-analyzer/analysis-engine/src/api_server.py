"""
HTTP API server for the Application Transformation Analyzer engine.
Provides REST endpoints for repository analysis and health checks.
"""

import os
import sys
import json
import traceback
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Add src to path for imports
src_path = os.path.dirname(__file__)
project_root = os.path.dirname(src_path)
sys.path.insert(0, src_path)
sys.path.insert(0, project_root)

from utils.logging_config import setup_analysis_logging, configure_logger_for_module
from analyzers.repository_analyzer import RepositoryAnalyzer


logger = configure_logger_for_module(__name__)


def serialize_networkx_graph(graph):
    """Convert a NetworkX graph to serializable dict."""
    if hasattr(graph, 'nodes') and hasattr(graph, 'edges'):
        return {
            "nodes": list(graph.nodes(data=True)),
            "edges": list(graph.edges(data=True)),
            "number_of_nodes": graph.number_of_nodes(),
            "number_of_edges": graph.number_of_edges()
        }
    return {
        "nodes": [],
        "edges": [],
        "number_of_nodes": 0,
        "number_of_edges": 0
    }


def deep_serialize_data(data):
    """Recursively serialize data, converting NetworkX graphs and other non-serializable objects."""
    if hasattr(data, 'nodes') and hasattr(data, 'edges'):
        # This is a NetworkX graph
        return serialize_networkx_graph(data)
    elif isinstance(data, dict):
        # Recursively process dictionary
        return {key: deep_serialize_data(value) for key, value in data.items()}
    elif isinstance(data, list):
        # Recursively process list
        return [deep_serialize_data(item) for item in data]
    elif hasattr(data, '__dict__'):
        # Convert objects to dictionaries
        return deep_serialize_data(data.__dict__)
    else:
        # Return as-is for basic types
        return data


def convert_component_map_to_dict(component_map):
    """Convert ComponentMap dataclass with NetworkX graphs to serializable dict."""
    try:
        # ComponentMap is a dataclass with specific attributes
        serializable_map = {
            "components": component_map.components,
            "clusters": component_map.clusters,
            "complexity_metrics": component_map.complexity_metrics
        }

        # Convert relationships (List[ComponentRelationship])
        serializable_relationships = []
        for rel in component_map.relationships:
            if hasattr(rel, '__dict__'):
                serializable_relationships.append(rel.__dict__)
            else:
                serializable_relationships.append(rel)
        serializable_map["relationships"] = serializable_relationships

        # Convert NetworkX DiGraph to serializable format
        if hasattr(component_map.dependency_graph, 'nodes') and hasattr(component_map.dependency_graph, 'edges'):
            serializable_map["dependency_graph"] = {
                "nodes": list(component_map.dependency_graph.nodes(data=True)),
                "edges": list(component_map.dependency_graph.edges(data=True)),
                "number_of_nodes": component_map.dependency_graph.number_of_nodes(),
                "number_of_edges": component_map.dependency_graph.number_of_edges()
            }
        else:
            serializable_map["dependency_graph"] = {
                "nodes": [],
                "edges": [],
                "number_of_nodes": 0,
                "number_of_edges": 0
            }

        return serializable_map
    except Exception as e:
        logger.error(f"Error converting component map: {e}")
        logger.error(f"Component map type: {type(component_map)}")
        logger.error(f"Component map attributes: {dir(component_map) if hasattr(component_map, '__dict__') else 'No attributes'}")
        # Return a simple fallback structure
        return {
            "components": {},
            "relationships": [],
            "clusters": [],
            "dependency_graph": {
                "nodes": [],
                "edges": [],
                "number_of_nodes": 0,
                "number_of_edges": 0
            },
            "complexity_metrics": {
                "total_components": 0,
                "total_relationships": 0,
                "error": str(e)
            }
        }


# Pydantic models for request/response
class AnalysisRequest(BaseModel):
    repository_url: str = Field(..., description="Repository URL to analyze")
    branch: Optional[str] = Field(None, description="Specific branch to analyze")
    analysis_type: Optional[str] = Field("full", description="Type of analysis to perform")
    options: Dict[str, Any] = Field(default_factory=dict, description="Analysis options")


class ValidationRequest(BaseModel):
    repository_url: str = Field(..., description="Repository URL to validate")


class AnalysisResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    analysis_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class HealthResponse(BaseModel):
    status: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    version: str = "1.0.0"
    engine: str = "Python Analysis Engine"


# Global analyzer instance
analyzer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    global analyzer
    logger.info("Starting Analysis Engine API Server...")

    try:
        analyzer = RepositoryAnalyzer()
        logger.info("Repository Analyzer initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize analyzer: {e}")
        analyzer = None

    yield

    # Shutdown
    logger.info("Shutting down Analysis Engine API Server...")


# Create FastAPI app
app = FastAPI(
    title="Application Transformation Analyzer Engine",
    description="HTTP API for repository analysis and transformation insights",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:5001"],  # Frontend and backend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy")


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - returns basic info."""
    return HealthResponse(status="running")


@app.post("/validate", response_model=AnalysisResponse)
async def validate_repository(request: ValidationRequest):
    """Validate repository accessibility."""
    try:
        logger.info(f"Validating repository: {request.repository_url}")

        if not analyzer:
            raise HTTPException(status_code=503, detail="Analyzer not initialized")

        # For now, do basic URL validation
        # In a real implementation, you might check if the repo is accessible
        accessible = True
        error_msg = None

        # Basic URL validation
        if not request.repository_url.startswith(("http://", "https://", "git@")):
            accessible = False
            error_msg = "Invalid repository URL format"

        return AnalysisResponse(
            success=True,
            data={
                "accessible": accessible,
                "error": error_msg
            }
        )

    except Exception as e:
        logger.error(f"Repository validation failed: {e}")
        return AnalysisResponse(
            success=False,
            error=str(e)
        )


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_repository(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """Analyze repository and return results."""
    try:
        logger.info(f"Starting analysis of repository: {request.repository_url}")

        if not analyzer:
            raise HTTPException(status_code=503, detail="Analyzer not initialized")

        # Generate analysis ID
        analysis_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"

        # Setup logging for this analysis
        log_file = setup_analysis_logging(
            analysis_id=analysis_id,
            repo_url=request.repository_url,
            log_dir="logs"
        )

        logger.info(f"Analysis ID: {analysis_id}")
        logger.info(f"Log file: {log_file}")

        # Perform analysis
        results = analyzer.analyze_repository(
            repo_url=request.repository_url,
            branch=request.branch,
            depth=request.options.get('depth')
        )

        # Convert results to dict format expected by backend using deep serialization
        # This will handle ALL NetworkX graphs and non-serializable objects throughout the response
        analysis_data = deep_serialize_data({
            "repository_info": results.repository_info,
            "technology_stack": {
                "primary_language": results.technology_stack.primary_language,
                "languages": results.technology_stack.languages,
                "frameworks": results.technology_stack.frameworks,
                "databases": results.technology_stack.databases,
                "web_servers": results.technology_stack.web_servers,
                "build_tools": results.technology_stack.build_tools,
                "testing_frameworks": results.technology_stack.testing_frameworks,
                "deployment_tools": results.technology_stack.deployment_tools,
                "package_managers": results.technology_stack.package_managers,
                "confidence_score": results.technology_stack.confidence_score
            },
            "component_map": results.component_map,
            "code_analysis": results.code_analysis,
            "dependency_analysis": results.dependency_analysis,
            "quality_metrics": results.quality_metrics,
            "recommendations": results.recommendations,
            "analysis_timestamp": results.analysis_timestamp
        })

        logger.info(f"Analysis completed successfully for {request.repository_url}")

        return AnalysisResponse(
            success=True,
            data=analysis_data,
            analysis_id=analysis_id
        )

    except Exception as e:
        error_msg = f"Analysis failed: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")

        return AnalysisResponse(
            success=False,
            error=error_msg,
            analysis_id=analysis_id if 'analysis_id' in locals() else None
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    logger.error(f"Traceback: {traceback.format_exc()}")

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "timestamp": datetime.now().isoformat()
        }
    )


def main():
    """Main entry point for the API server."""
    import argparse

    parser = argparse.ArgumentParser(description="Analysis Engine API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--log-level", default="info", help="Log level")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()

    logger.info(f"Starting Analysis Engine API Server on {args.host}:{args.port}")

    uvicorn.run(
        "api_server:app",
        host=args.host,
        port=args.port,
        log_level=args.log_level,
        reload=args.reload
    )


if __name__ == "__main__":
    main()