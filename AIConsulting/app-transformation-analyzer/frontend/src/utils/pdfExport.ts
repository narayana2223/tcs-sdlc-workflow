/**
 * PDF Export Utilities
 * Generate comprehensive PDF reports from 12-factor assessment results
 */

import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import { TwelveFactorAssessment, FactorEvaluation, Recommendation, Gap } from '../types';

interface AssessmentSummary {
  overview: {
    grade: string;
    overall_score: number;
    weighted_score: number;
    confidence: number;
    coverage: number;
  };
  factor_breakdown: {
    excellent: { count: number; factors: string[] };
    good: { count: number; factors: string[] };
    fair: { count: number; factors: string[] };
    poor: { count: number; factors: string[] };
  };
  gaps: {
    summary: string;
    health_score: number;
    status: string;
    breakdown: { [key: string]: number };
  };
  recommendations: {
    total: number;
    critical: number;
    high: number;
    roadmap: any;
  };
  insights: string[];
  next_steps: string[];
}

interface ExportOptions {
  includeCharts?: boolean;
  includeRecommendations?: boolean;
  includeExecutiveSummary?: boolean;
  includeDetailedAnalysis?: boolean;
  includeAppendices?: boolean;
  format?: 'portrait' | 'landscape';
  theme?: 'default' | 'professional' | 'minimal';
}

export class PDFExporter {
  private pdf: jsPDF;
  private pageHeight: number;
  private pageWidth: number;
  private margin: number;
  private yPosition: number;
  private options: Required<ExportOptions>;

  constructor(options: ExportOptions = {}) {
    this.options = {
      includeCharts: true,
      includeRecommendations: true,
      includeExecutiveSummary: true,
      includeDetailedAnalysis: true,
      includeAppendices: true,
      format: 'portrait',
      theme: 'professional',
      ...options
    };

    this.pdf = new jsPDF({
      orientation: this.options.format,
      unit: 'mm',
      format: 'a4'
    });

    this.pageWidth = this.pdf.internal.pageSize.getWidth();
    this.pageHeight = this.pdf.internal.pageSize.getHeight();
    this.margin = 20;
    this.yPosition = this.margin;
  }

  /**
   * Export complete assessment report
   */
  async exportAssessmentReport(
    assessment: TwelveFactorAssessment,
    summary?: AssessmentSummary
  ): Promise<void> {
    try {
      // Add title page
      this.addTitlePage(assessment);

      // Add table of contents
      if (this.options.includeExecutiveSummary || this.options.includeDetailedAnalysis) {
        this.addTableOfContents();
      }

      // Add executive summary
      if (this.options.includeExecutiveSummary && summary) {
        this.addExecutiveSummary(assessment, summary);
      }

      // Add detailed analysis
      if (this.options.includeDetailedAnalysis) {
        await this.addDetailedAnalysis(assessment);
      }

      // Add recommendations
      if (this.options.includeRecommendations) {
        this.addRecommendationsSection(assessment.recommendations);
      }

      // Add charts
      if (this.options.includeCharts) {
        await this.addChartsSection();
      }

      // Add appendices
      if (this.options.includeAppendices) {
        this.addAppendices(assessment);
      }

      // Add footer to all pages
      this.addFooters();

      // Save the PDF
      const fileName = `12-factor-assessment-${assessment.assessment_id}-${new Date().toISOString().split('T')[0]}.pdf`;
      this.pdf.save(fileName);

    } catch (error) {
      console.error('Error exporting PDF:', error);
      throw new Error('Failed to export PDF report');
    }
  }

  /**
   * Add title page
   */
  private addTitlePage(assessment: TwelveFactorAssessment): void {
    // Set title page colors based on theme
    const colors = this.getThemeColors();

    // Header background
    this.pdf.setFillColor(colors.primary.r, colors.primary.g, colors.primary.b);
    this.pdf.rect(0, 0, this.pageWidth, 60, 'F');

    // Title
    this.pdf.setTextColor(255, 255, 255);
    this.pdf.setFontSize(24);
    this.pdf.setFont('helvetica', 'bold');
    this.pdf.text('12-Factor Application Assessment Report', this.pageWidth / 2, 30, { align: 'center' });

    // Subtitle
    this.pdf.setFontSize(14);
    this.pdf.setFont('helvetica', 'normal');
    this.pdf.text('Comprehensive Analysis & Recommendations', this.pageWidth / 2, 45, { align: 'center' });

    // Repository info
    this.pdf.setTextColor(colors.text.r, colors.text.g, colors.text.b);
    this.yPosition = 80;

    this.addText('Repository:', assessment.repository_url, 'bold');
    this.addText('Assessment Date:', new Date(assessment.timestamp).toLocaleDateString());
    this.addText('Assessment ID:', assessment.assessment_id);

    // Grade box
    this.yPosition += 20;
    const gradeColor = this.getGradeColor(assessment.grade);
    this.pdf.setFillColor(gradeColor[0], gradeColor[1], gradeColor[2]);
    this.pdf.roundedRect(this.margin, this.yPosition, 60, 30, 3, 3, 'F');

    this.pdf.setTextColor(255, 255, 255);
    this.pdf.setFontSize(20);
    this.pdf.setFont('helvetica', 'bold');
    this.pdf.text('Grade', this.margin + 30, this.yPosition + 12, { align: 'center' });
    this.pdf.setFontSize(28);
    this.pdf.text(assessment.grade, this.margin + 30, this.yPosition + 25, { align: 'center' });

    // Score summary
    this.pdf.setTextColor(colors.text.r, colors.text.g, colors.text.b);
    this.pdf.setFontSize(12);
    this.pdf.setFont('helvetica', 'normal');

    const scoreX = this.margin + 80;
    this.pdf.text(`Overall Score: ${Math.round(assessment.overall_score * 20)}%`, scoreX, this.yPosition + 12);
    this.pdf.text(`Weighted Score: ${assessment.weighted_score.toFixed(1)}/5.0`, scoreX, this.yPosition + 22);
    this.pdf.text(`Confidence: ${Math.round(assessment.confidence * 100)}%`, scoreX, this.yPosition + 32);

    // Key metrics
    this.yPosition += 60;
    this.addSectionHeader('Key Metrics');

    const metrics = [
      [`Total Factors Evaluated`, assessment.summary.total_factors.toString()],
      [`Gaps Identified`, assessment.summary.total_gaps.toString()],
      [`Recommendations`, assessment.summary.total_recommendations.toString()],
      [`Critical Issues`, assessment.summary.critical_issues.toString()],
      [`Excellent Factors`, assessment.summary.excellent_factors.toString()]
    ];

    this.addTable(metrics, ['Metric', 'Value']);

    this.addNewPage();
  }

  /**
   * Add table of contents
   */
  private addTableOfContents(): void {
    this.addSectionHeader('Table of Contents');

    const contents = [
      'Executive Summary ......................................................... 3',
      'Detailed Factor Analysis ................................................ 4',
      'Recommendations & Implementation Plan .......................... 8',
      'Visual Analysis & Charts ............................................... 12',
      'Appendices ................................................................. 15',
      '  A. 12-Factor Methodology Overview ............................ 16',
      '  B. Evidence Details .................................................... 17',
      '  C. Technical Implementation Examples ......................... 18'
    ];

    this.pdf.setFontSize(11);
    this.pdf.setFont('helvetica', 'normal');

    contents.forEach(item => {
      this.pdf.text(item, this.margin, this.yPosition);
      this.yPosition += 8;
    });

    this.addNewPage();
  }

  /**
   * Add executive summary
   */
  private addExecutiveSummary(assessment: TwelveFactorAssessment, summary: AssessmentSummary): void {
    this.addSectionHeader('Executive Summary');

    // Overall assessment
    this.addSubsectionHeader('Overall Assessment');

    let summaryText = `This 12-factor assessment evaluated ${assessment.summary.total_factors} core factors for cloud-native application compliance. `;
    summaryText += `The application received an overall grade of ${assessment.grade} with a weighted score of ${assessment.weighted_score.toFixed(1)} out of 5.0.`;

    if (assessment.summary.critical_issues > 0) {
      summaryText += ` ${assessment.summary.critical_issues} critical issues require immediate attention to ensure production readiness.`;
    }

    if (assessment.summary.excellent_factors > assessment.summary.total_factors / 2) {
      summaryText += ` The application demonstrates strong compliance in ${assessment.summary.excellent_factors} factors, indicating a solid foundation for cloud-native deployment.`;
    }

    this.addParagraph(summaryText);

    // Key findings
    this.addSubsectionHeader('Key Findings');

    const findings = summary.insights || [
      'Analysis completed with high confidence rating',
      'Multiple improvement opportunities identified',
      'Immediate action required for critical issues'
    ];

    findings.forEach(finding => {
      this.pdf.text(`• ${finding}`, this.margin + 5, this.yPosition);
      this.yPosition += 6;
    });

    this.yPosition += 5;

    // Recommendations overview
    this.addSubsectionHeader('Priority Recommendations');

    const priorityRecs = assessment.recommendations
      .filter(r => r.priority === 'critical' || r.priority === 'high')
      .slice(0, 3);

    priorityRecs.forEach((rec, index) => {
      this.pdf.setFont('helvetica', 'bold');
      this.pdf.text(`${index + 1}. ${rec.title}`, this.margin, this.yPosition);
      this.yPosition += 6;

      this.pdf.setFont('helvetica', 'normal');
      this.addParagraph(rec.description, this.margin + 5);
    });

    // Next steps
    this.addSubsectionHeader('Immediate Next Steps');

    const nextSteps = summary.next_steps || [
      'Address critical priority recommendations',
      'Implement quick wins for immediate improvement',
      'Develop comprehensive implementation roadmap'
    ];

    nextSteps.forEach(step => {
      this.pdf.text(`• ${step}`, this.margin + 5, this.yPosition);
      this.yPosition += 6;
    });

    this.addNewPage();
  }

  /**
   * Add detailed factor analysis
   */
  private async addDetailedAnalysis(assessment: TwelveFactorAssessment): Promise<void> {
    this.addSectionHeader('Detailed Factor Analysis');

    // Factor breakdown chart (placeholder for actual chart)
    this.addSubsectionHeader('Factor Score Distribution');

    // Create a simple text-based chart
    const scoreDistribution = assessment.score_distribution || {};
    Object.entries(scoreDistribution).forEach(([scoreName, count]) => {
      const percentage = (count / assessment.summary.total_factors * 100).toFixed(1);
      this.pdf.text(`${scoreName}: ${count} factors (${percentage}%)`, this.margin, this.yPosition);
      this.yPosition += 6;
    });

    this.yPosition += 10;

    // Individual factor details
    this.addSubsectionHeader('Factor Evaluations');

    Object.entries(assessment.factor_evaluations).forEach(([factorName, factor]) => {
      this.addFactorDetail(factorName, factor);

      // Add page break if needed
      if (this.yPosition > this.pageHeight - 60) {
        this.addNewPage();
      }
    });
  }

  /**
   * Add factor detail section
   */
  private addFactorDetail(factorName: string, factor: FactorEvaluation): void {
    // Factor header
    this.pdf.setFillColor(240, 240, 240);
    this.pdf.rect(this.margin, this.yPosition - 2, this.pageWidth - 2 * this.margin, 15, 'F');

    this.pdf.setFont('helvetica', 'bold');
    this.pdf.setFontSize(12);
    this.pdf.text(this.formatFactorName(factorName), this.margin + 3, this.yPosition + 8);

    // Score badge
    this.pdf.setFillColor(...this.getScoreColor(factor.score));
    this.pdf.roundedRect(this.pageWidth - 40, this.yPosition, 20, 10, 2, 2, 'F');
    this.pdf.setTextColor(255, 255, 255);
    this.pdf.setFontSize(10);
    this.pdf.text(`${factor.score}/5`, this.pageWidth - 30, this.yPosition + 7, { align: 'center' });

    this.yPosition += 20;
    this.pdf.setTextColor(0, 0, 0);
    this.pdf.setFont('helvetica', 'normal');
    this.pdf.setFontSize(10);

    // Factor description
    this.addParagraph(factor.factor_description);

    // Score reasoning
    this.pdf.setFont('helvetica', 'bold');
    this.pdf.text('Assessment Reasoning:', this.margin, this.yPosition);
    this.yPosition += 5;
    this.pdf.setFont('helvetica', 'normal');
    this.addParagraph(factor.score_reasoning, this.margin + 5);

    // Evidence summary
    this.pdf.setFont('helvetica', 'bold');
    this.pdf.text(`Evidence (${factor.evidence.length} items):`, this.margin, this.yPosition);
    this.yPosition += 5;

    const positiveCount = factor.evidence.filter(e => e.type === 'positive').length;
    const negativeCount = factor.evidence.filter(e => e.type === 'negative').length;
    const neutralCount = factor.evidence.filter(e => e.type === 'neutral').length;

    this.pdf.setFont('helvetica', 'normal');
    this.pdf.text(`Positive: ${positiveCount} | Negative: ${negativeCount} | Neutral: ${neutralCount}`, this.margin + 5, this.yPosition);
    this.yPosition += 8;

    // Confidence and weight
    this.pdf.text(`Confidence: ${Math.round(factor.confidence * 100)}% | Weight: ${factor.weight.toFixed(1)}x`, this.margin + 5, this.yPosition);
    this.yPosition += 15;
  }

  /**
   * Add recommendations section
   */
  private addRecommendationsSection(recommendations: Recommendation[]): void {
    this.addSectionHeader('Recommendations & Implementation Plan');

    // Group by priority
    const groupedRecs = {
      critical: recommendations.filter(r => r.priority === 'critical'),
      high: recommendations.filter(r => r.priority === 'high'),
      medium: recommendations.filter(r => r.priority === 'medium'),
      low: recommendations.filter(r => r.priority === 'low')
    };

    Object.entries(groupedRecs).forEach(([priority, recs]) => {
      if (recs.length === 0) return;

      this.addSubsectionHeader(`${priority.charAt(0).toUpperCase() + priority.slice(1)} Priority (${recs.length} recommendations)`);

      recs.forEach((rec, index) => {
        this.addRecommendationDetail(rec, index + 1);
      });
    });
  }

  /**
   * Add recommendation detail
   */
  private addRecommendationDetail(rec: Recommendation, index: number): void {
    // Recommendation header
    this.pdf.setFont('helvetica', 'bold');
    this.pdf.setFontSize(11);
    this.pdf.text(`${index}. ${rec.title}`, this.margin, this.yPosition);
    this.yPosition += 6;

    // Priority and complexity chips
    this.pdf.setFontSize(9);
    this.pdf.text(`Priority: ${rec.priority.toUpperCase()} | Complexity: ${rec.complexity} | Effort: ${rec.estimated_effort}`, this.margin + 5, this.yPosition);
    this.yPosition += 8;

    // Description
    this.pdf.setFont('helvetica', 'normal');
    this.pdf.setFontSize(10);
    this.addParagraph(rec.description, this.margin + 5);

    // Implementation steps
    this.pdf.setFont('helvetica', 'bold');
    this.pdf.text('Implementation Steps:', this.margin + 5, this.yPosition);
    this.yPosition += 5;

    this.pdf.setFont('helvetica', 'normal');
    rec.implementation_steps.forEach((step, stepIndex) => {
      this.pdf.text(`${stepIndex + 1}. ${step}`, this.margin + 10, this.yPosition);
      this.yPosition += 5;
    });

    this.yPosition += 5;

    // Benefits
    if (rec.benefits.length > 0) {
      this.pdf.setFont('helvetica', 'bold');
      this.pdf.text('Benefits:', this.margin + 5, this.yPosition);
      this.yPosition += 5;

      this.pdf.setFont('helvetica', 'normal');
      rec.benefits.forEach(benefit => {
        this.pdf.text(`• ${benefit}`, this.margin + 10, this.yPosition);
        this.yPosition += 5;
      });
      this.yPosition += 3;
    }

    this.yPosition += 10;

    // Check for page break
    if (this.yPosition > this.pageHeight - 60) {
      this.addNewPage();
    }
  }

  /**
   * Add charts section (placeholder)
   */
  private async addChartsSection(): Promise<void> {
    this.addSectionHeader('Visual Analysis & Charts');

    // Placeholder for charts - in a real implementation, you would:
    // 1. Capture chart elements from DOM
    // 2. Convert to images using html2canvas
    // 3. Add images to PDF

    this.addSubsectionHeader('Factor Compliance Radar Chart');
    this.pdf.text('Chart visualization would appear here in full implementation', this.margin, this.yPosition);
    this.yPosition += 20;

    this.addSubsectionHeader('Gap Analysis Heatmap');
    this.pdf.text('Heatmap visualization would appear here in full implementation', this.margin, this.yPosition);
    this.yPosition += 20;

    this.addSubsectionHeader('Priority Distribution');
    this.pdf.text('Priority chart would appear here in full implementation', this.margin, this.yPosition);
    this.yPosition += 20;

    this.addNewPage();
  }

  /**
   * Add appendices
   */
  private addAppendices(assessment: TwelveFactorAssessment): void {
    this.addSectionHeader('Appendices');

    // Appendix A: 12-Factor Methodology Overview
    this.addSubsectionHeader('Appendix A: 12-Factor Methodology Overview');

    const methodologyText = `The 12-Factor App methodology is a set of best practices designed to enable applications to be built with portability and resilience when deployed to the web. These factors apply to apps written in any programming language, and which use any combination of backing services.`;

    this.addParagraph(methodologyText);

    // Appendix B: Detailed Evidence
    this.addSubsectionHeader('Appendix B: Evidence Details');

    Object.entries(assessment.factor_evaluations).forEach(([factorName, factor]) => {
      this.pdf.setFont('helvetica', 'bold');
      this.pdf.text(this.formatFactorName(factorName), this.margin, this.yPosition);
      this.yPosition += 6;

      this.pdf.setFont('helvetica', 'normal');
      factor.evidence.forEach((evidence, index) => {
        this.pdf.text(`${index + 1}. [${evidence.type.toUpperCase()}] ${evidence.description}`, this.margin + 5, this.yPosition);
        this.yPosition += 5;

        if (evidence.file_path) {
          this.pdf.setFontSize(9);
          this.pdf.text(`   File: ${evidence.file_path}${evidence.line_number ? ` (Line ${evidence.line_number})` : ''}`, this.margin + 10, this.yPosition);
          this.pdf.setFontSize(10);
          this.yPosition += 5;
        }
      });

      this.yPosition += 5;

      // Check for page break
      if (this.yPosition > this.pageHeight - 60) {
        this.addNewPage();
      }
    });
  }

  /**
   * Helper methods
   */
  private addSectionHeader(title: string): void {
    const colors = this.getThemeColors();

    this.pdf.setFillColor(colors.secondary.r, colors.secondary.g, colors.secondary.b);
    this.pdf.rect(this.margin, this.yPosition, this.pageWidth - 2 * this.margin, 12, 'F');

    this.pdf.setTextColor(255, 255, 255);
    this.pdf.setFontSize(14);
    this.pdf.setFont('helvetica', 'bold');
    this.pdf.text(title, this.margin + 5, this.yPosition + 8);

    this.yPosition += 20;
    this.pdf.setTextColor(0, 0, 0);
  }

  private addSubsectionHeader(title: string): void {
    this.pdf.setFont('helvetica', 'bold');
    this.pdf.setFontSize(12);
    this.pdf.text(title, this.margin, this.yPosition);
    this.yPosition += 8;
    this.pdf.setFont('helvetica', 'normal');
  }

  private addText(label: string, value: string, fontWeight: 'normal' | 'bold' = 'normal'): void {
    this.pdf.setFont('helvetica', 'bold');
    this.pdf.text(label, this.margin, this.yPosition);

    this.pdf.setFont('helvetica', fontWeight);
    this.pdf.text(value, this.margin + 40, this.yPosition);
    this.yPosition += 8;
  }

  private addParagraph(text: string, x: number = this.margin): void {
    const lines = this.pdf.splitTextToSize(text, this.pageWidth - 2 * this.margin - (x - this.margin));
    lines.forEach((line: string) => {
      this.pdf.text(line, x, this.yPosition);
      this.yPosition += 5;
    });
    this.yPosition += 3;
  }

  private addTable(data: string[][], headers: string[]): void {
    const colWidth = (this.pageWidth - 2 * this.margin) / headers.length;

    // Headers
    this.pdf.setFillColor(230, 230, 230);
    this.pdf.rect(this.margin, this.yPosition, this.pageWidth - 2 * this.margin, 8, 'F');

    this.pdf.setFont('helvetica', 'bold');
    headers.forEach((header, index) => {
      this.pdf.text(header, this.margin + index * colWidth + 2, this.yPosition + 6);
    });

    this.yPosition += 12;

    // Data rows
    this.pdf.setFont('helvetica', 'normal');
    data.forEach(row => {
      row.forEach((cell, index) => {
        this.pdf.text(cell, this.margin + index * colWidth + 2, this.yPosition);
      });
      this.yPosition += 8;
    });

    this.yPosition += 5;
  }

  private addNewPage(): void {
    this.pdf.addPage();
    this.yPosition = this.margin;
  }

  private addFooters(): void {
    const pageCount = this.pdf.getNumberOfPages();

    for (let i = 1; i <= pageCount; i++) {
      this.pdf.setPage(i);

      // Footer line
      this.pdf.setDrawColor(200, 200, 200);
      this.pdf.line(this.margin, this.pageHeight - 15, this.pageWidth - this.margin, this.pageHeight - 15);

      // Page number
      this.pdf.setFontSize(9);
      this.pdf.setFont('helvetica', 'normal');
      this.pdf.text(`Page ${i} of ${pageCount}`, this.pageWidth - this.margin, this.pageHeight - 8, { align: 'right' });

      // Footer text
      this.pdf.text('12-Factor Assessment Report', this.margin, this.pageHeight - 8);

      // Generation date
      this.pdf.text(`Generated: ${new Date().toLocaleDateString()}`, this.pageWidth / 2, this.pageHeight - 8, { align: 'center' });
    }
  }

  private formatFactorName(name: string): string {
    return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }

  private getThemeColors() {
    const themes = {
      default: {
        primary: { r: 33, g: 150, b: 243 },
        secondary: { r: 63, g: 81, b: 181 },
        text: { r: 33, g: 33, b: 33 }
      },
      professional: {
        primary: { r: 0, g: 123, b: 255 },
        secondary: { r: 52, g: 58, b: 64 },
        text: { r: 73, g: 80, b: 87 }
      },
      minimal: {
        primary: { r: 96, g: 125, b: 139 },
        secondary: { r: 144, g: 164, b: 174 },
        text: { r: 97, g: 97, b: 97 }
      }
    };

    return themes[this.options.theme] || themes.default;
  }

  private getGradeColor(grade: string): [number, number, number] {
    switch (grade) {
      case 'A': return [76, 175, 80];   // Green
      case 'B': return [139, 195, 74];  // Light Green
      case 'C': return [255, 193, 7];   // Amber
      case 'D': return [255, 152, 0];   // Orange
      case 'F': return [244, 67, 54];   // Red
      default: return [158, 158, 158];  // Grey
    }
  }

  private getScoreColor(score: number): [number, number, number] {
    if (score >= 4) return [76, 175, 80];   // Green
    if (score >= 3) return [255, 193, 7];   // Amber
    if (score >= 2) return [255, 152, 0];   // Orange
    return [244, 67, 54];                   // Red
  }
}

/**
 * Convenience function to export assessment as PDF
 */
export const exportAssessmentToPDF = async (
  assessment: TwelveFactorAssessment,
  summary?: AssessmentSummary,
  options?: ExportOptions
): Promise<void> => {
  const exporter = new PDFExporter(options);
  await exporter.exportAssessmentReport(assessment, summary);
};

/**
 * Export individual chart as PDF
 */
export const exportChartToPDF = async (
  chartElement: HTMLElement,
  title: string,
  options?: ExportOptions
): Promise<void> => {
  try {
    const canvas = await html2canvas(chartElement, {
      backgroundColor: '#ffffff',
      scale: 2
    });

    const pdf = new jsPDF({
      orientation: 'landscape',
      unit: 'mm',
      format: 'a4'
    });

    const imgWidth = 297; // A4 landscape width
    const imgHeight = (canvas.height * imgWidth) / canvas.width;

    pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 0, 0, imgWidth, imgHeight);
    pdf.save(`${title.toLowerCase().replace(/\s+/g, '-')}-chart.pdf`);
  } catch (error) {
    console.error('Error exporting chart to PDF:', error);
    throw new Error('Failed to export chart to PDF');
  }
};

export default PDFExporter;