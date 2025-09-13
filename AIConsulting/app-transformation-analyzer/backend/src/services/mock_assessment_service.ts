/**
 * Mock Assessment Service for 12-Factor App Analysis
 * Generates realistic assessment data for demonstration and development purposes
 */

import {
  TwelveFactorAssessment,
  FactorEvaluation,
  Gap,
  Recommendation,
  AssessmentSummary,
  ImplementationRoadmap,
  RoadmapPhase,
  RecommendationPriority,
  ImplementationComplexity,
  getGradeFromScore,
  getFactorScoreName,
  calculateHealthScore
} from '../models/assessment_model';

export class MockAssessmentService {

  /**
   * Generate a complete mock 12-factor assessment
   */
  static generateMockAssessment(repositoryUrl: string = 'demo-repository'): TwelveFactorAssessment {
    const assessmentId = `assess_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const timestamp = new Date().toISOString();

    // Generate factor evaluations with realistic scores
    const factorEvaluations = this.generateFactorEvaluations();

    // Calculate overall scores
    const scores = Object.values(factorEvaluations).map(f => f.score);
    const weights = Object.values(factorEvaluations).map(f => f.weight);
    const overall_score = scores.reduce((sum, score) => sum + score, 0) / scores.length;
    const weighted_score = scores.reduce((sum, score, i) => sum + (score * weights[i]), 0) / weights.reduce((sum, w) => sum + w, 0);

    const grade = getGradeFromScore(weighted_score);

    // Generate gaps and recommendations
    const gaps = this.generateGaps(factorEvaluations);
    const recommendations = this.generateRecommendations(factorEvaluations, gaps);

    // Calculate distributions
    const scoreDistribution = this.calculateScoreDistribution(factorEvaluations);
    const priorityDistribution = this.calculatePriorityDistribution(recommendations);

    // Generate summary statistics
    const summary = {
      total_factors: Object.keys(factorEvaluations).length,
      total_gaps: gaps.length,
      total_recommendations: recommendations.length,
      critical_issues: recommendations.filter(r => r.priority === 'critical').length,
      excellent_factors: Object.values(factorEvaluations).filter(f => f.score === 5).length,
      poor_factors: Object.values(factorEvaluations).filter(f => f.score <= 2).length,
    };

    return {
      repository_url: repositoryUrl,
      assessment_id: assessmentId,
      timestamp,
      factor_evaluations: factorEvaluations,
      overall_score: Math.round(overall_score * 100) / 100,
      weighted_score: Math.round(weighted_score * 100) / 100,
      grade,
      gaps,
      recommendations,
      confidence: 0.85,
      coverage: 100,
      score_distribution: scoreDistribution,
      priority_distribution: priorityDistribution,
      summary
    };
  }

  /**
   * Generate realistic factor evaluations for 12 factors
   */
  private static generateFactorEvaluations(): { [factorName: string]: FactorEvaluation } {
    const factors = [
      'codebase', 'dependencies', 'config', 'backing_services', 'build_release_run',
      'processes', 'port_binding', 'concurrency', 'disposability', 'dev_prod_parity',
      'logs', 'admin_processes'
    ];

    const evaluations: { [factorName: string]: FactorEvaluation } = {};

    factors.forEach((factor, index) => {
      // Generate realistic but varied scores
      const baseScore = 2.5 + Math.random() * 2.5; // Score between 2.5-5
      const score = Math.round(baseScore);

      // Generate confidence based on score (higher scores = higher confidence)
      const confidence = Math.min(0.95, 0.6 + (score / 5) * 0.35 + (Math.random() * 0.1));

      evaluations[factor] = {
        factor_name: factor,
        factor_description: this.getFactorDescription(factor),
        score,
        score_name: getFactorScoreName(score),
        score_reasoning: this.generateScoreReasoning(factor, score),
        evidence: this.generateEvidence(factor, score),
        confidence: Math.round(confidence * 100) / 100,
        weight: 1.0 + (Math.random() * 0.4 - 0.2) // Weight between 0.8-1.2
      };
    });

    return evaluations;
  }

  /**
   * Generate gaps based on factor evaluations
   */
  private static generateGaps(factorEvaluations: { [factorName: string]: FactorEvaluation }): Gap[] {
    const gaps: Gap[] = [];

    Object.entries(factorEvaluations).forEach(([factorName, evaluation]) => {
      if (evaluation.score <= 3) {
        gaps.push({
          factor_name: factorName,
          gap_type: evaluation.score <= 2 ? 'missing' : 'partial',
          description: this.generateGapDescription(factorName, evaluation.score),
          impact: this.getGapImpact(evaluation.score),
          current_state: this.getCurrentState(factorName, evaluation.score),
          desired_state: this.getDesiredState(factorName),
          severity: this.getSeverity(evaluation.score),
          affected_components: this.getAffectedComponents(factorName)
        });
      }
    });

    return gaps;
  }

  /**
   * Generate recommendations based on evaluations and gaps
   */
  private static generateRecommendations(
    factorEvaluations: { [factorName: string]: FactorEvaluation },
    gaps: Gap[]
  ): Recommendation[] {
    const recommendations: Recommendation[] = [];
    let recommendationId = 1;

    gaps.forEach(gap => {
      const evaluation = factorEvaluations[gap.factor_name];
      const priority = this.getRecommendationPriority(evaluation.score);
      const complexity = this.getImplementationComplexity(gap.factor_name);

      recommendations.push({
        id: `rec_${recommendationId.toString().padStart(3, '0')}`,
        factor_name: gap.factor_name,
        title: this.getRecommendationTitle(gap.factor_name),
        description: this.getRecommendationDescription(gap.factor_name),
        rationale: this.getRecommendationRationale(gap.factor_name),
        implementation_steps: this.getImplementationSteps(gap.factor_name),
        priority,
        complexity,
        estimated_effort: this.getEstimatedEffort(complexity),
        benefits: this.getBenefits(gap.factor_name),
        risks: this.getRisks(gap.factor_name),
        prerequisites: this.getPrerequisites(gap.factor_name),
        resources: this.getResources(gap.factor_name),
        code_examples: this.getCodeExamples(gap.factor_name)
      });

      recommendationId++;
    });

    return recommendations;
  }

  /**
   * Generate assessment summary with detailed insights
   */
  static generateAssessmentSummary(assessment: TwelveFactorAssessment): AssessmentSummary {
    const factorBreakdown = {
      excellent: { count: 0, factors: [] as string[] },
      good: { count: 0, factors: [] as string[] },
      fair: { count: 0, factors: [] as string[] },
      poor: { count: 0, factors: [] as string[] }
    };

    Object.entries(assessment.factor_evaluations).forEach(([name, evaluation]) => {
      if (evaluation.score === 5) {
        factorBreakdown.excellent.count++;
        factorBreakdown.excellent.factors.push(name);
      } else if (evaluation.score === 4) {
        factorBreakdown.good.count++;
        factorBreakdown.good.factors.push(name);
      } else if (evaluation.score === 3) {
        factorBreakdown.fair.count++;
        factorBreakdown.fair.factors.push(name);
      } else {
        factorBreakdown.poor.count++;
        factorBreakdown.poor.factors.push(name);
      }
    });

    const gapBreakdown = {
      critical: assessment.recommendations.filter(r => r.priority === 'critical').length,
      high: assessment.recommendations.filter(r => r.priority === 'high').length,
      medium: assessment.recommendations.filter(r => r.priority === 'medium').length,
      low: assessment.recommendations.filter(r => r.priority === 'low').length,
    };

    const healthScore = calculateHealthScore(assessment.gaps);
    const roadmap = this.generateImplementationRoadmap(assessment.recommendations);

    return {
      overview: {
        grade: assessment.grade,
        overall_score: assessment.overall_score,
        weighted_score: assessment.weighted_score,
        confidence: assessment.confidence,
        coverage: assessment.coverage
      },
      factor_breakdown: factorBreakdown,
      gaps: {
        summary: `${assessment.gaps.length} gaps identified across ${factorBreakdown.poor.count + factorBreakdown.fair.count} factors`,
        health_score: healthScore,
        status: healthScore >= 80 ? 'healthy' : healthScore >= 60 ? 'needs_attention' : 'critical',
        breakdown: gapBreakdown
      },
      recommendations: {
        total: assessment.recommendations.length,
        critical: gapBreakdown.critical,
        high: gapBreakdown.high,
        roadmap
      },
      insights: this.generateInsights(assessment),
      next_steps: this.generateNextSteps(assessment)
    };
  }

  /**
   * Generate implementation roadmap
   */
  private static generateImplementationRoadmap(recommendations: Recommendation[]): ImplementationRoadmap {
    const criticalRecs = recommendations.filter(r => r.priority === 'critical');
    const highRecs = recommendations.filter(r => r.priority === 'high');
    const mediumRecs = recommendations.filter(r => r.priority === 'medium');
    const lowRecs = recommendations.filter(r => r.priority === 'low');

    const phases: ImplementationRoadmap['phases'] = {
      phase_1_immediate: {
        description: 'Critical issues that block production readiness',
        timeline: '1-2 weeks',
        recommendations: criticalRecs.map(r => r.id),
        count: criticalRecs.length
      },
      phase_2_short_term: {
        description: 'High priority improvements for stability',
        timeline: '1-2 months',
        recommendations: highRecs.map(r => r.id),
        count: highRecs.length
      },
      phase_3_medium_term: {
        description: 'Medium priority enhancements for optimization',
        timeline: '3-6 months',
        recommendations: mediumRecs.map(r => r.id),
        count: mediumRecs.length
      },
      phase_4_long_term: {
        description: 'Low priority improvements for excellence',
        timeline: '6+ months',
        recommendations: lowRecs.map(r => r.id),
        count: lowRecs.length
      }
    };

    const quickWins = recommendations.filter(r =>
      r.complexity === 'low' && (r.priority === 'high' || r.priority === 'medium')
    ).length;

    return {
      total_recommendations: recommendations.length,
      phases,
      estimated_total_effort: this.calculateTotalEffort(recommendations),
      quick_wins: quickWins
    };
  }

  // Helper methods for generating realistic data

  private static getFactorDescription(factor: string): string {
    const descriptions: { [key: string]: string } = {
      'codebase': 'One codebase tracked in revision control, many deploys',
      'dependencies': 'Explicitly declare and isolate dependencies',
      'config': 'Store config in the environment',
      'backing_services': 'Treat backing services as attached resources',
      'build_release_run': 'Strictly separate build and run stages',
      'processes': 'Execute the app as one or more stateless processes',
      'port_binding': 'Export services via port binding',
      'concurrency': 'Scale out via the process model',
      'disposability': 'Maximize robustness with fast startup and graceful shutdown',
      'dev_prod_parity': 'Keep development, staging, and production as similar as possible',
      'logs': 'Treat logs as event streams',
      'admin_processes': 'Run admin/management tasks as one-off processes'
    };
    return descriptions[factor] || `Assessment of ${factor} factor`;
  }

  private static generateScoreReasoning(factor: string, score: number): string {
    const reasonings = {
      5: `Excellent implementation of ${factor} with best practices followed throughout`,
      4: `Good implementation of ${factor} with minor areas for improvement`,
      3: `Fair implementation of ${factor} but missing some key aspects`,
      2: `Poor implementation of ${factor} with significant gaps`,
      1: `Missing implementation of ${factor} - critical issues identified`
    };
    return reasonings[score as keyof typeof reasonings] || `Score ${score} for ${factor}`;
  }

  private static generateEvidence(factor: string, score: number): any[] {
    const evidenceCount = Math.floor(Math.random() * 3) + 2; // 2-4 pieces of evidence
    const evidence: any[] = [];

    for (let i = 0; i < evidenceCount; i++) {
      evidence.push({
        type: score >= 4 ? 'positive' : score >= 3 ? 'neutral' : 'negative',
        description: `Evidence for ${factor} implementation`,
        file_path: `src/config/${factor}.js`,
        line_number: Math.floor(Math.random() * 100) + 1,
        code_snippet: `// ${factor} implementation`,
        confidence: 0.7 + Math.random() * 0.3
      });
    }

    return evidence;
  }

  private static generateGapDescription(factor: string, score: number): string {
    if (score <= 2) {
      return `${factor} implementation is missing or severely inadequate`;
    } else {
      return `${factor} implementation is partial but lacks key components`;
    }
  }

  private static getGapImpact(score: number): string {
    if (score <= 2) return 'High impact on system reliability and maintainability';
    return 'Medium impact on system optimization and best practices';
  }

  private static getCurrentState(factor: string, score: number): string {
    const states = {
      1: `No ${factor} implementation detected`,
      2: `Basic ${factor} setup with significant gaps`,
      3: `Partial ${factor} implementation with some best practices`
    };
    return states[score as keyof typeof states] || `Current ${factor} state`;
  }

  private static getDesiredState(factor: string): string {
    return `Fully compliant ${factor} implementation following 12-factor methodology`;
  }

  private static getSeverity(score: number): string {
    if (score <= 1) return 'critical';
    if (score <= 2) return 'high';
    return 'medium';
  }

  private static getAffectedComponents(factor: string): string[] {
    const components = ['application', 'deployment', 'configuration', 'monitoring'];
    return components.slice(0, Math.floor(Math.random() * 3) + 1);
  }

  private static getRecommendationPriority(score: number): string {
    if (score <= 1) return 'critical';
    if (score <= 2) return 'high';
    if (score <= 3) return 'medium';
    return 'low';
  }

  private static getImplementationComplexity(factor: string): string {
    const complexities = ['low', 'medium', 'high'];
    return complexities[Math.floor(Math.random() * complexities.length)];
  }

  private static getRecommendationTitle(factor: string): string {
    return `Implement proper ${factor.replace('_', ' ')} handling`;
  }

  private static getRecommendationDescription(factor: string): string {
    return `Improve ${factor} implementation to achieve 12-factor compliance`;
  }

  private static getRecommendationRationale(factor: string): string {
    return `Proper ${factor} implementation is essential for scalable, maintainable applications`;
  }

  private static getImplementationSteps(factor: string): string[] {
    return [
      `Audit current ${factor} implementation`,
      `Design improved ${factor} architecture`,
      `Implement ${factor} best practices`,
      `Test and validate ${factor} improvements`,
      `Deploy and monitor ${factor} changes`
    ];
  }

  private static getEstimatedEffort(complexity: string): string {
    const efforts = {
      'low': '1-2 days',
      'medium': '1-2 weeks',
      'high': '2-4 weeks',
      'very_high': '1-3 months'
    };
    return efforts[complexity as keyof typeof efforts] || '1-2 weeks';
  }

  private static getBenefits(factor: string): string[] {
    return [
      'Improved system reliability',
      'Better scalability',
      'Enhanced maintainability',
      'Reduced operational overhead'
    ];
  }

  private static getRisks(factor: string): string[] {
    return [
      'Temporary service disruption during implementation',
      'Learning curve for team members',
      'Potential integration challenges'
    ];
  }

  private static getPrerequisites(factor: string): string[] {
    return [
      'Team training on 12-factor principles',
      'Development environment setup',
      'Testing framework preparation'
    ];
  }

  private static getResources(factor: string): string[] {
    return [
      'https://12factor.net/',
      'Internal documentation',
      'Training materials'
    ];
  }

  private static getCodeExamples(factor: string): any[] {
    return [
      {
        language: 'javascript',
        title: `${factor} implementation example`,
        code: `// Example ${factor} implementation\nconst config = process.env.${factor.toUpperCase()};\n// Implementation details...`
      }
    ];
  }

  private static calculateScoreDistribution(factorEvaluations: { [factorName: string]: FactorEvaluation }): { [scoreName: string]: number } {
    const distribution: { [scoreName: string]: number } = {
      'EXCELLENT': 0,
      'GOOD': 0,
      'FAIR': 0,
      'POOR': 0,
      'MISSING': 0
    };

    Object.values(factorEvaluations).forEach(evaluation => {
      distribution[evaluation.score_name]++;
    });

    return distribution;
  }

  private static calculatePriorityDistribution(recommendations: Recommendation[]): { [priority: string]: number } {
    const distribution: { [priority: string]: number } = {
      'critical': 0,
      'high': 0,
      'medium': 0,
      'low': 0
    };

    recommendations.forEach(recommendation => {
      distribution[recommendation.priority]++;
    });

    return distribution;
  }

  private static generateInsights(assessment: TwelveFactorAssessment): string[] {
    const insights: string[] = [];

    if (assessment.grade === 'A' || assessment.grade === 'B') {
      insights.push('Your application demonstrates strong 12-factor methodology compliance');
    } else {
      insights.push('Significant opportunities exist to improve 12-factor compliance');
    }

    const excellentFactors = Object.values(assessment.factor_evaluations).filter(f => f.score === 5).length;
    if (excellentFactors > 6) {
      insights.push('More than half of your factors show excellent implementation');
    }

    const criticalRecs = assessment.recommendations.filter(r => r.priority === 'critical').length;
    if (criticalRecs > 0) {
      insights.push(`${criticalRecs} critical issues require immediate attention`);
    }

    return insights;
  }

  private static generateNextSteps(assessment: TwelveFactorAssessment): string[] {
    const steps: string[] = [];

    const criticalRecs = assessment.recommendations.filter(r => r.priority === 'critical');
    if (criticalRecs.length > 0) {
      steps.push(`Address ${criticalRecs.length} critical recommendations first`);
    }

    const quickWins = assessment.recommendations.filter(r => r.complexity === 'low').length;
    if (quickWins > 0) {
      steps.push(`Implement ${quickWins} quick wins for immediate improvement`);
    }

    steps.push('Schedule regular reassessments to track progress');

    return steps;
  }

  private static calculateTotalEffort(recommendations: Recommendation[]): string {
    const effortHours = recommendations.reduce((total, rec) => {
      const hours = {
        'low': 16,      // 2 days
        'medium': 80,   // 2 weeks
        'high': 160,    // 4 weeks
        'very_high': 480 // 3 months
      };
      return total + (hours[rec.complexity as keyof typeof hours] || 40);
    }, 0);

    const weeks = Math.ceil(effortHours / 40);
    if (weeks <= 4) return `${weeks} weeks`;
    if (weeks <= 16) return `${Math.ceil(weeks / 4)} months`;
    return `${Math.ceil(weeks / 12)} quarters`;
  }
}