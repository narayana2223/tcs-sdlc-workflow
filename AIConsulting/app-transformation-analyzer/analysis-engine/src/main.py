"""
Main entry point for the Application Transformation Analyzer engine.
Provides CLI interface and orchestrates the analysis process.
"""

import argparse
import json
import os
import sys
from typing import Optional
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from utils.logging_config import setup_analysis_logging, log_performance, configure_logger_for_module
from analyzers.repository_analyzer import RepositoryAnalyzer, RepositoryAnalysisResult


logger = configure_logger_for_module(__name__)


@log_performance
def analyze_repository_cli(
    repo_url: str,
    branch: Optional[str] = None,
    depth: Optional[int] = None,
    output_file: Optional[str] = None,
    output_format: str = 'json'
) -> RepositoryAnalysisResult:
    """
    Perform repository analysis via CLI.
    
    Args:
        repo_url: Repository URL to analyze
        branch: Specific branch to analyze
        depth: Clone depth for faster analysis
        output_file: Output file path
        output_format: Output format ('json', 'yaml', 'text')
        
    Returns:
        Analysis results
    """
    
    logger.info(f"Starting analysis of repository: {repo_url}")
    
    try:
        # Initialize analyzer
        analyzer = RepositoryAnalyzer()
        
        # Perform analysis
        results = analyzer.analyze_repository(repo_url, branch, depth)
        
        # Output results
        if output_file:
            save_results(results, output_file, output_format)
            logger.info(f"Results saved to: {output_file}")
        else:
            print_results_summary(results)
        
        logger.info("Analysis completed successfully")
        return results
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise


def save_results(
    results: RepositoryAnalysisResult, 
    output_file: str, 
    output_format: str
) -> None:
    """Save analysis results to file."""
    
    # Create output directory if needed
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    if output_format.lower() == 'json':
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results.__dict__, f, indent=2, default=str)
    
    elif output_format.lower() == 'yaml':
        import yaml
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(results.__dict__, f, default_flow_style=False, default=str)
    
    elif output_format.lower() == 'text':
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(format_text_report(results))
    
    else:
        raise ValueError(f"Unsupported output format: {output_format}")


def print_results_summary(results: RepositoryAnalysisResult) -> None:
    """Print a summary of analysis results to console."""
    
    print("\n" + "="*80)
    print("REPOSITORY ANALYSIS SUMMARY")
    print("="*80)
    
    # Repository info
    repo_info = results.repository_info
    print(f"Repository: {repo_info.get('remote_url', 'Unknown')}")
    print(f"Branch: {repo_info.get('active_branch', 'Unknown')}")
    print(f"Total Files: {repo_info.get('total_files', 0):,}")
    print(f"Total Commits: {repo_info.get('total_commits', 0):,}")
    
    # Technology stack
    tech_stack = results.technology_stack
    print(f"\nPrimary Language: {tech_stack.primary_language}")
    print(f"Frameworks: {', '.join(tech_stack.frameworks) if tech_stack.frameworks else 'None detected'}")
    print(f"Databases: {', '.join(tech_stack.databases) if tech_stack.databases else 'None detected'}")
    print(f"Build Tools: {', '.join(tech_stack.build_tools) if tech_stack.build_tools else 'None detected'}")
    
    # Code analysis
    code_analysis = results.code_analysis.get('analysis_summary', {})
    print(f"\nCode Files Analyzed: {code_analysis.get('total_files', 0)}")
    print(f"Code Elements Found: {code_analysis.get('total_elements', 0)}")
    print(f"Average Complexity: {code_analysis.get('avg_complexity', 0):.1f}")
    
    # Dependencies
    dep_analysis = results.dependency_analysis
    total_deps = dep_analysis.get('total_dependencies', 0)
    vulnerabilities = len(dep_analysis.get('vulnerabilities', {}))
    print(f"\nTotal Dependencies: {total_deps}")
    print(f"Security Vulnerabilities: {vulnerabilities}")
    
    # Quality metrics
    quality = results.quality_metrics
    print(f"\nOverall Quality Score: {quality.get('overall_score', 0):.1f}/100")
    print(f"Maintainability Score: {quality.get('maintainability_score', 0):.1f}/100")
    print(f"Security Score: {quality.get('security_score', 0):.1f}/100")
    
    # Recommendations
    recommendations = results.recommendations
    print(f"\nRecommendations: {len(recommendations)}")
    for i, rec in enumerate(recommendations[:5], 1):  # Show top 5
        print(f"  {i}. [{rec.get('priority', 'low').upper()}] {rec.get('title', 'No title')}")
    
    if len(recommendations) > 5:
        print(f"  ... and {len(recommendations) - 5} more")
    
    print("="*80)


def format_text_report(results: RepositoryAnalysisResult) -> str:
    """Format results as a detailed text report."""
    
    report_lines = []
    
    # Header
    report_lines.extend([
        "APPLICATION TRANSFORMATION ANALYZER REPORT",
        "=" * 50,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Analysis ID: {results.analysis_timestamp}",
        ""
    ])
    
    # Repository Information
    repo_info = results.repository_info
    report_lines.extend([
        "REPOSITORY INFORMATION",
        "-" * 30,
        f"URL: {repo_info.get('remote_url', 'Unknown')}",
        f"Branch: {repo_info.get('active_branch', 'Unknown')}",
        f"Total Files: {repo_info.get('total_files', 0):,}",
        f"Total Commits: {repo_info.get('total_commits', 0):,}",
        f"Total Size: {repo_info.get('total_size_bytes', 0):,} bytes",
        ""
    ])
    
    # Technology Stack
    tech_stack = results.technology_stack
    report_lines.extend([
        "TECHNOLOGY STACK",
        "-" * 30,
        f"Primary Language: {tech_stack.primary_language}",
        f"Languages: {', '.join(f'{lang} ({pct:.1f}%)' for lang, pct in tech_stack.languages.items())}",
        f"Frameworks: {', '.join(tech_stack.frameworks) if tech_stack.frameworks else 'None detected'}",
        f"Databases: {', '.join(tech_stack.databases) if tech_stack.databases else 'None detected'}",
        f"Build Tools: {', '.join(tech_stack.build_tools) if tech_stack.build_tools else 'None detected'}",
        f"Package Managers: {', '.join(tech_stack.package_managers) if tech_stack.package_managers else 'None detected'}",
        f"Confidence Score: {tech_stack.confidence_score:.2f}",
        ""
    ])
    
    # Quality Metrics
    quality = results.quality_metrics
    report_lines.extend([
        "QUALITY METRICS",
        "-" * 30,
        f"Overall Score: {quality.get('overall_score', 0):.1f}/100",
        f"Maintainability Score: {quality.get('maintainability_score', 0):.1f}/100",
        f"Security Score: {quality.get('security_score', 0):.1f}/100",
        f"Complexity Score: {quality.get('complexity_score', 0):.1f}/100",
        ""
    ])
    
    # Recommendations
    recommendations = results.recommendations
    if recommendations:
        report_lines.extend([
            "RECOMMENDATIONS",
            "-" * 30
        ])
        
        for i, rec in enumerate(recommendations, 1):
            report_lines.extend([
                f"{i}. {rec.get('title', 'No title')} [{rec.get('priority', 'low').upper()}]",
                f"   Category: {rec.get('category', 'general')}",
                f"   Description: {rec.get('description', 'No description')}",
                f"   Action: {rec.get('action', 'No action specified')}",
                ""
            ])
    
    return "\n".join(report_lines)


def main():
    """Main CLI entry point."""
    
    parser = argparse.ArgumentParser(
        description="Application Transformation Analyzer - Analyze code repositories for transformation insights",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py https://github.com/user/repo
  python main.py https://github.com/user/repo --branch main --depth 1
  python main.py https://github.com/user/repo --output results.json --format json
  python main.py https://github.com/user/repo --output report.txt --format text
        """
    )
    
    # Required arguments
    parser.add_argument(
        'repo_url',
        help='Repository URL to analyze (GitHub, GitLab, etc.)'
    )
    
    # Optional arguments
    parser.add_argument(
        '--branch', '-b',
        help='Specific branch to analyze (default: repository default branch)'
    )
    
    parser.add_argument(
        '--depth', '-d',
        type=int,
        help='Shallow clone depth for faster analysis'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output file path for results'
    )
    
    parser.add_argument(
        '--format', '-f',
        choices=['json', 'yaml', 'text'],
        default='json',
        help='Output format (default: json)'
    )
    
    parser.add_argument(
        '--log-level', '-l',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--log-dir',
        default='logs',
        help='Directory for log files (default: logs)'
    )
    
    parser.add_argument(
        '--no-colors',
        action='store_true',
        help='Disable colored console output'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Generate analysis ID
    analysis_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # Set up logging
        log_file = setup_analysis_logging(
            analysis_id=analysis_id,
            repo_url=args.repo_url,
            log_dir=args.log_dir
        )
        
        logger.info(f"Starting analysis - ID: {analysis_id}")
        logger.info(f"Repository: {args.repo_url}")
        logger.info(f"Log file: {log_file}")
        
        # Perform analysis
        results = analyze_repository_cli(
            repo_url=args.repo_url,
            branch=args.branch,
            depth=args.depth,
            output_file=args.output,
            output_format=args.format
        )
        
        logger.info("Analysis completed successfully")
        print(f"\nAnalysis completed! Log file: {log_file}")
        
        return 0
        
    except KeyboardInterrupt:
        logger.warning("Analysis interrupted by user")
        print("\nAnalysis interrupted by user")
        return 1
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        print(f"\nAnalysis failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)