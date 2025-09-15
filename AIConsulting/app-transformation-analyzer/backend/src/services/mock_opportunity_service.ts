/**
 * Mock Transformation Opportunity Service
 * Generates comprehensive transformation opportunities based on assessment results
 * Provides concrete, executive-ready transformation recommendations
 */

export interface TransformationOpportunity {
  id: string;
  title: string;
  description: string;
  category: OpportunityCategory;
  type: OpportunityType;
  businessValue: string;
  impactScore: number; // 1-10 scale
  effortScore: number; // 1-10 scale (10 = highest effort)
  roiScore: number; // Calculated ROI percentage
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH';
  implementationTimeline: string;
  prerequisites: string[];
  implementationApproach: ImplementationStep[];
  codeExamples: CodeExample[];
  relatedFactors: string[]; // 12-factor principles this addresses
  businessMetrics: BusinessMetric[];
  stakeholders: string[];
  successCriteria: string[];
  potentialChallenges: string[];
  estimatedCost: string;
  estimatedSavings: string;
  priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
}

export interface ImplementationStep {
  phase: string;
  description: string;
  duration: string;
  resources: string[];
  deliverables: string[];
  risks: string[];
}

export interface CodeExample {
  language: string;
  title: string;
  before: string;
  after: string;
  explanation: string;
  benefits: string[];
}

export interface BusinessMetric {
  name: string;
  current: string;
  target: string;
  improvement: string;
  timeframe: string;
}

export enum OpportunityCategory {
  NLP = 'NLP',
  AUTOMATION = 'AUTOMATION',
  DECISION = 'DECISION',
  DATA = 'DATA',
  INFRASTRUCTURE = 'INFRASTRUCTURE',
  SECURITY = 'SECURITY',
  PERFORMANCE = 'PERFORMANCE',
  COST_OPTIMIZATION = 'COST_OPTIMIZATION'
}

export enum OpportunityType {
  QUICK_WIN = 'QUICK_WIN',
  STRATEGIC = 'STRATEGIC',
  FOUNDATIONAL = 'FOUNDATIONAL',
  INNOVATION = 'INNOVATION',
  COMPLIANCE = 'COMPLIANCE'
}

export class MockOpportunityService {
  private static opportunityTemplates: Partial<TransformationOpportunity>[] = [
    {
      id: 'nlp-doc-automation',
      title: 'Automated Document Processing with NLP',
      description: 'Implement intelligent document processing to extract, classify, and route documents automatically using natural language processing.',
      category: OpportunityCategory.NLP,
      type: OpportunityType.STRATEGIC,
      businessValue: 'Reduce manual document processing by 80%, improve accuracy by 95%, and enable 24/7 processing capability.',
      impactScore: 9,
      effortScore: 6,
      riskLevel: 'MEDIUM',
      implementationTimeline: '6-8 months',
      prerequisites: ['Document digitization infrastructure', 'Training data collection', 'API gateway setup'],
      relatedFactors: ['Factor VI: Processes', 'Factor XII: Admin processes', 'Factor IV: Backing services'],
      estimatedCost: '$120,000 - $180,000',
      estimatedSavings: '$450,000 annually',
      priority: 'HIGH'
    },
    {
      id: 'intelligent-chatbot',
      title: 'Intelligent Customer Support Chatbot',
      description: 'Deploy an AI-powered chatbot to handle 70% of customer inquiries automatically with natural language understanding.',
      category: OpportunityCategory.NLP,
      type: OpportunityType.QUICK_WIN,
      businessValue: 'Reduce support costs by 60%, improve response times to <30 seconds, and increase customer satisfaction scores.',
      impactScore: 8,
      effortScore: 4,
      riskLevel: 'LOW',
      implementationTimeline: '3-4 months',
      prerequisites: ['Knowledge base setup', 'Integration with existing support systems', 'Training data preparation'],
      relatedFactors: ['Factor III: Config', 'Factor IV: Backing services', 'Factor XI: Logs'],
      estimatedCost: '$80,000 - $120,000',
      estimatedSavings: '$280,000 annually',
      priority: 'HIGH'
    },
    {
      id: 'predictive-analytics',
      title: 'Predictive Analytics for Business Decisions',
      description: 'Implement machine learning models to predict customer behavior, sales trends, and operational issues before they occur.',
      category: OpportunityCategory.DECISION,
      type: OpportunityType.STRATEGIC,
      businessValue: 'Improve forecast accuracy by 40%, reduce operational issues by 50%, and increase revenue by 15% through better targeting.',
      impactScore: 9,
      effortScore: 7,
      riskLevel: 'MEDIUM',
      implementationTimeline: '8-12 months',
      prerequisites: ['Data warehouse setup', 'Data quality improvement', 'Analytics team training'],
      relatedFactors: ['Factor I: Codebase', 'Factor IV: Backing services', 'Factor XI: Logs'],
      estimatedCost: '$200,000 - $300,000',
      estimatedSavings: '$800,000 annually',
      priority: 'CRITICAL'
    },
    {
      id: 'workflow-automation',
      title: 'Intelligent Process Automation',
      description: 'Automate repetitive business processes using RPA and AI to reduce manual work and improve consistency.',
      category: OpportunityCategory.AUTOMATION,
      type: OpportunityType.QUICK_WIN,
      businessValue: 'Eliminate 90% of manual data entry, reduce processing time by 75%, and improve accuracy to 99.5%.',
      impactScore: 8,
      effortScore: 5,
      riskLevel: 'LOW',
      implementationTimeline: '4-6 months',
      prerequisites: ['Process mapping', 'System integration setup', 'Exception handling design'],
      relatedFactors: ['Factor VI: Processes', 'Factor XII: Admin processes', 'Factor VIII: Concurrency'],
      estimatedCost: '$100,000 - $150,000',
      estimatedSavings: '$350,000 annually',
      priority: 'HIGH'
    },
    {
      id: 'data-lake-analytics',
      title: 'Modern Data Lake with Real-time Analytics',
      description: 'Build a comprehensive data lake with streaming analytics to provide real-time business insights and support data-driven decisions.',
      category: OpportunityCategory.DATA,
      type: OpportunityType.FOUNDATIONAL,
      businessValue: 'Enable real-time decision making, reduce report generation time by 90%, and support advanced analytics use cases.',
      impactScore: 9,
      effortScore: 8,
      riskLevel: 'HIGH',
      implementationTimeline: '10-14 months',
      prerequisites: ['Cloud infrastructure setup', 'Data governance framework', 'Security compliance review'],
      relatedFactors: ['Factor IV: Backing services', 'Factor IX: Disposability', 'Factor XI: Logs'],
      estimatedCost: '$300,000 - $500,000',
      estimatedSavings: '$600,000 annually',
      priority: 'MEDIUM'
    },
    {
      id: 'microservices-migration',
      title: 'Microservices Architecture Migration',
      description: 'Transform monolithic applications into microservices architecture for improved scalability and maintainability.',
      category: OpportunityCategory.INFRASTRUCTURE,
      type: OpportunityType.FOUNDATIONAL,
      businessValue: 'Improve deployment frequency by 10x, reduce downtime by 80%, and enable independent team scaling.',
      impactScore: 8,
      effortScore: 9,
      riskLevel: 'HIGH',
      implementationTimeline: '12-18 months',
      prerequisites: ['Container orchestration setup', 'DevOps pipeline maturity', 'Monitoring infrastructure'],
      relatedFactors: ['Factor I: Codebase', 'Factor VI: Processes', 'Factor VIII: Concurrency', 'Factor IX: Disposability'],
      estimatedCost: '$400,000 - $600,000',
      estimatedSavings: '$500,000 annually',
      priority: 'MEDIUM'
    },
    {
      id: 'ai-fraud-detection',
      title: 'AI-Powered Fraud Detection System',
      description: 'Implement machine learning algorithms to detect fraudulent activities in real-time with minimal false positives.',
      category: OpportunityCategory.DECISION,
      type: OpportunityType.STRATEGIC,
      businessValue: 'Reduce fraud losses by 85%, decrease false positive rates by 70%, and improve customer experience.',
      impactScore: 9,
      effortScore: 7,
      riskLevel: 'MEDIUM',
      implementationTimeline: '6-9 months',
      prerequisites: ['Historical fraud data preparation', 'Real-time processing infrastructure', 'Model validation framework'],
      relatedFactors: ['Factor IV: Backing services', 'Factor VIII: Concurrency', 'Factor XI: Logs'],
      estimatedCost: '$180,000 - $250,000',
      estimatedSavings: '$900,000 annually',
      priority: 'CRITICAL'
    },
    {
      id: 'cloud-cost-optimization',
      title: 'Intelligent Cloud Cost Optimization',
      description: 'Implement automated cloud resource optimization to reduce infrastructure costs while maintaining performance.',
      category: OpportunityCategory.COST_OPTIMIZATION,
      type: OpportunityType.QUICK_WIN,
      businessValue: 'Reduce cloud costs by 40%, improve resource utilization by 60%, and eliminate waste through automation.',
      impactScore: 7,
      effortScore: 3,
      riskLevel: 'LOW',
      implementationTimeline: '2-3 months',
      prerequisites: ['Cloud monitoring setup', 'Resource tagging strategy', 'Automated scaling policies'],
      relatedFactors: ['Factor VII: Port binding', 'Factor VIII: Concurrency', 'Factor IX: Disposability'],
      estimatedCost: '$50,000 - $80,000',
      estimatedSavings: '$300,000 annually',
      priority: 'HIGH'
    }
  ];

  public static generateOpportunities(assessmentId: string, assessmentData?: any): TransformationOpportunity[] {
    const opportunities: TransformationOpportunity[] = [];

    // Generate opportunities based on templates
    this.opportunityTemplates.forEach((template, index) => {
      const opportunity = this.createFullOpportunity(template, assessmentId, index);
      opportunities.push(opportunity);
    });

    // Sort by priority and ROI
    return opportunities.sort((a, b) => {
      const priorityOrder = { 'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1 };
      const priorityDiff = priorityOrder[b.priority] - priorityOrder[a.priority];
      if (priorityDiff !== 0) return priorityDiff;
      return b.roiScore - a.roiScore;
    });
  }

  private static createFullOpportunity(template: Partial<TransformationOpportunity>, assessmentId: string, index: number): TransformationOpportunity {
    const roiScore = this.calculateROI(template.impactScore || 5, template.effortScore || 5);

    return {
      id: template.id || `opportunity-${index}`,
      title: template.title || 'Transformation Opportunity',
      description: template.description || 'Description not available',
      category: template.category || OpportunityCategory.AUTOMATION,
      type: template.type || OpportunityType.STRATEGIC,
      businessValue: template.businessValue || 'Significant business value expected',
      impactScore: template.impactScore || 5,
      effortScore: template.effortScore || 5,
      roiScore,
      riskLevel: template.riskLevel || 'MEDIUM',
      implementationTimeline: template.implementationTimeline || '6-12 months',
      prerequisites: template.prerequisites || ['Assessment completed', 'Budget approved'],
      implementationApproach: this.generateImplementationApproach(template.category || OpportunityCategory.AUTOMATION),
      codeExamples: this.generateCodeExamples(template.category || OpportunityCategory.AUTOMATION),
      relatedFactors: template.relatedFactors || ['Factor I: Codebase'],
      businessMetrics: this.generateBusinessMetrics(template.impactScore || 5),
      stakeholders: this.generateStakeholders(template.category || OpportunityCategory.AUTOMATION),
      successCriteria: this.generateSuccessCriteria(template.category || OpportunityCategory.AUTOMATION),
      potentialChallenges: this.generateChallenges(template.riskLevel || 'MEDIUM'),
      estimatedCost: template.estimatedCost || '$100,000 - $200,000',
      estimatedSavings: template.estimatedSavings || '$300,000 annually',
      priority: template.priority || 'MEDIUM'
    };
  }

  private static calculateROI(impact: number, effort: number): number {
    // ROI calculation: (Impact^2 / Effort) * 10
    // Higher impact and lower effort = higher ROI
    const baseROI = (Math.pow(impact, 2) / effort) * 10;
    return Math.round(Math.min(baseROI, 200)); // Cap at 200% ROI
  }

  private static generateImplementationApproach(category: OpportunityCategory): ImplementationStep[] {
    const approaches: { [key in OpportunityCategory]: ImplementationStep[] } = {
      [OpportunityCategory.NLP]: [
        {
          phase: 'Phase 1: Foundation',
          description: 'Set up NLP infrastructure and data pipeline',
          duration: '4-6 weeks',
          resources: ['Data Scientists', 'ML Engineers', 'DevOps'],
          deliverables: ['Data pipeline', 'Model training environment', 'Initial dataset'],
          risks: ['Data quality issues', 'Infrastructure complexity']
        },
        {
          phase: 'Phase 2: Model Development',
          description: 'Develop and train NLP models',
          duration: '6-8 weeks',
          resources: ['Data Scientists', 'Domain Experts'],
          deliverables: ['Trained models', 'Validation results', 'Performance benchmarks'],
          risks: ['Model accuracy', 'Training time']
        },
        {
          phase: 'Phase 3: Integration',
          description: 'Integrate models into production systems',
          duration: '4-6 weeks',
          resources: ['Backend Developers', 'DevOps', 'QA'],
          deliverables: ['Production deployment', 'API endpoints', 'Monitoring setup'],
          risks: ['Integration complexity', 'Performance issues']
        }
      ],
      [OpportunityCategory.AUTOMATION]: [
        {
          phase: 'Phase 1: Process Analysis',
          description: 'Map and analyze current processes',
          duration: '2-3 weeks',
          resources: ['Business Analysts', 'Process Owners'],
          deliverables: ['Process maps', 'Automation opportunities', 'Requirements document'],
          risks: ['Process complexity', 'Stakeholder alignment']
        },
        {
          phase: 'Phase 2: Automation Development',
          description: 'Build automation workflows',
          duration: '6-8 weeks',
          resources: ['RPA Developers', 'Integration Specialists'],
          deliverables: ['Automation workflows', 'Testing scripts', 'Documentation'],
          risks: ['Technical complexity', 'System integration']
        },
        {
          phase: 'Phase 3: Deployment',
          description: 'Deploy and monitor automation',
          duration: '3-4 weeks',
          resources: ['DevOps', 'Support Team', 'End Users'],
          deliverables: ['Production deployment', 'User training', 'Monitoring dashboard'],
          risks: ['User adoption', 'Process changes']
        }
      ],
      [OpportunityCategory.DECISION]: [
        {
          phase: 'Phase 1: Data Preparation',
          description: 'Prepare and validate data for decision models',
          duration: '4-6 weeks',
          resources: ['Data Engineers', 'Business Analysts'],
          deliverables: ['Clean datasets', 'Data quality report', 'Feature engineering'],
          risks: ['Data availability', 'Data quality']
        },
        {
          phase: 'Phase 2: Model Building',
          description: 'Build predictive and decision models',
          duration: '6-10 weeks',
          resources: ['Data Scientists', 'Business Experts'],
          deliverables: ['Decision models', 'Validation results', 'Business rules'],
          risks: ['Model complexity', 'Business alignment']
        },
        {
          phase: 'Phase 3: Implementation',
          description: 'Implement decision systems in business processes',
          duration: '4-6 weeks',
          resources: ['Developers', 'Business Users', 'Change Management'],
          deliverables: ['Decision system', 'User interfaces', 'Training materials'],
          risks: ['User adoption', 'Change resistance']
        }
      ],
      [OpportunityCategory.DATA]: [
        {
          phase: 'Phase 1: Architecture Design',
          description: 'Design data architecture and governance',
          duration: '4-6 weeks',
          resources: ['Data Architects', 'Infrastructure Engineers'],
          deliverables: ['Architecture design', 'Data governance framework', 'Security model'],
          risks: ['Architecture complexity', 'Compliance requirements']
        },
        {
          phase: 'Phase 2: Infrastructure Setup',
          description: 'Build data infrastructure and pipelines',
          duration: '8-12 weeks',
          resources: ['Data Engineers', 'DevOps', 'Security Team'],
          deliverables: ['Data lake infrastructure', 'ETL pipelines', 'Security implementation'],
          risks: ['Technical complexity', 'Performance issues']
        },
        {
          phase: 'Phase 3: Analytics Layer',
          description: 'Build analytics and visualization layer',
          duration: '6-8 weeks',
          resources: ['Analytics Engineers', 'Business Analysts', 'UX Designers'],
          deliverables: ['Analytics platform', 'Dashboards', 'Self-service tools'],
          risks: ['User adoption', 'Performance optimization']
        }
      ],
      [OpportunityCategory.INFRASTRUCTURE]: [
        {
          phase: 'Phase 1: Assessment & Planning',
          description: 'Assess current infrastructure and plan migration',
          duration: '3-4 weeks',
          resources: ['Solution Architects', 'Infrastructure Engineers'],
          deliverables: ['Infrastructure assessment', 'Migration plan', 'Risk analysis'],
          risks: ['Complexity assessment', 'Resource planning']
        },
        {
          phase: 'Phase 2: Foundation Setup',
          description: 'Set up new infrastructure foundation',
          duration: '8-12 weeks',
          resources: ['DevOps Engineers', 'Security Team', 'Network Engineers'],
          deliverables: ['Infrastructure foundation', 'CI/CD pipelines', 'Monitoring setup'],
          risks: ['Technical challenges', 'Security compliance']
        },
        {
          phase: 'Phase 3: Migration & Optimization',
          description: 'Migrate applications and optimize performance',
          duration: '12-16 weeks',
          resources: ['Development Teams', 'DevOps', 'QA'],
          deliverables: ['Migrated applications', 'Performance optimization', 'Documentation'],
          risks: ['Migration complexity', 'Business continuity']
        }
      ],
      [OpportunityCategory.SECURITY]: [
        {
          phase: 'Phase 1: Security Assessment',
          description: 'Comprehensive security assessment and planning',
          duration: '3-4 weeks',
          resources: ['Security Architects', 'Compliance Officers'],
          deliverables: ['Security assessment', 'Compliance gap analysis', 'Implementation roadmap'],
          risks: ['Compliance requirements', 'Resource constraints']
        },
        {
          phase: 'Phase 2: Security Implementation',
          description: 'Implement security controls and monitoring',
          duration: '8-10 weeks',
          resources: ['Security Engineers', 'DevOps', 'Developers'],
          deliverables: ['Security controls', 'Monitoring systems', 'Incident response'],
          risks: ['Technical complexity', 'Performance impact']
        },
        {
          phase: 'Phase 3: Validation & Training',
          description: 'Validate security measures and train staff',
          duration: '4-6 weeks',
          resources: ['Security Team', 'Training Specialists', 'All Staff'],
          deliverables: ['Security validation', 'Training programs', 'Documentation'],
          risks: ['User compliance', 'Ongoing maintenance']
        }
      ],
      [OpportunityCategory.PERFORMANCE]: [
        {
          phase: 'Phase 1: Performance Analysis',
          description: 'Analyze current performance and identify bottlenecks',
          duration: '2-3 weeks',
          resources: ['Performance Engineers', 'System Administrators'],
          deliverables: ['Performance baseline', 'Bottleneck analysis', 'Optimization plan'],
          risks: ['Analysis complexity', 'System impact']
        },
        {
          phase: 'Phase 2: Optimization Implementation',
          description: 'Implement performance optimizations',
          duration: '6-8 weeks',
          resources: ['Developers', 'Database Administrators', 'DevOps'],
          deliverables: ['Optimized code', 'Database tuning', 'Infrastructure improvements'],
          risks: ['Code complexity', 'System stability']
        },
        {
          phase: 'Phase 3: Monitoring & Validation',
          description: 'Set up monitoring and validate improvements',
          duration: '2-4 weeks',
          resources: ['Monitoring Specialists', 'QA Team'],
          deliverables: ['Monitoring dashboard', 'Performance validation', 'Optimization documentation'],
          risks: ['Monitoring overhead', 'Performance regression']
        }
      ],
      [OpportunityCategory.COST_OPTIMIZATION]: [
        {
          phase: 'Phase 1: Cost Analysis',
          description: 'Analyze current costs and identify optimization opportunities',
          duration: '2-3 weeks',
          resources: ['Cost Analysts', 'Cloud Engineers', 'Finance Team'],
          deliverables: ['Cost breakdown', 'Optimization opportunities', 'Savings projections'],
          risks: ['Data accuracy', 'Business impact']
        },
        {
          phase: 'Phase 2: Optimization Implementation',
          description: 'Implement cost optimization measures',
          duration: '4-6 weeks',
          resources: ['Cloud Engineers', 'DevOps', 'Automation Specialists'],
          deliverables: ['Optimized resources', 'Automation scripts', 'Cost controls'],
          risks: ['Service disruption', 'Performance impact']
        },
        {
          phase: 'Phase 3: Monitoring & Governance',
          description: 'Set up ongoing cost monitoring and governance',
          duration: '2-3 weeks',
          resources: ['FinOps Team', 'Management', 'IT Operations'],
          deliverables: ['Cost monitoring', 'Governance policies', 'Regular reporting'],
          risks: ['Process adoption', 'Ongoing discipline']
        }
      ]
    };

    return approaches[category] || approaches[OpportunityCategory.AUTOMATION];
  }

  private static generateCodeExamples(category: OpportunityCategory): CodeExample[] {
    const examples: { [key in OpportunityCategory]: CodeExample[] } = {
      [OpportunityCategory.NLP]: [
        {
          language: 'python',
          title: 'Document Classification with NLP',
          before: `# Manual document processing
def process_document(document):
    # Manual categorization
    if 'invoice' in document.lower():
        category = 'billing'
    elif 'contract' in document.lower():
        category = 'legal'
    else:
        category = 'unknown'
    return category`,
          after: `# Automated NLP document processing
import transformers
from transformers import pipeline

classifier = pipeline("text-classification",
                     model="document-classifier-v1")

def process_document_ai(document):
    result = classifier(document)
    return {
        'category': result[0]['label'],
        'confidence': result[0]['score'],
        'processing_time': 'instant'
    }`,
          explanation: 'Transform manual document categorization into automated AI-powered classification.',
          benefits: ['95% accuracy improvement', '99% time reduction', 'Consistent classification', '24/7 processing']
        }
      ],
      [OpportunityCategory.AUTOMATION]: [
        {
          language: 'python',
          title: 'Automated Data Processing Pipeline',
          before: `# Manual data processing
def process_data_manual():
    # Step 1: Download files
    files = manually_download_files()

    # Step 2: Process each file
    for file in files:
        data = manually_clean_data(file)
        manually_validate_data(data)
        manually_upload_results(data)

    return "Process completed"`,
          after: `# Automated data processing pipeline
from airflow import DAG
from airflow.operators.python_operator import PythonOperator

def automated_pipeline():
    with DAG('data_processing',
             schedule_interval='@hourly') as dag:

        download = PythonOperator(
            task_id='download_files',
            python_callable=auto_download_files
        )

        process = PythonOperator(
            task_id='process_data',
            python_callable=auto_process_data
        )

        validate = PythonOperator(
            task_id='validate_results',
            python_callable=auto_validate_data
        )

        download >> process >> validate

    return dag`,
          explanation: 'Replace manual data processing with automated, scheduled pipelines.',
          benefits: ['Eliminate human error', 'Run 24/7 automatically', 'Scalable processing', 'Complete audit trail']
        }
      ],
      [OpportunityCategory.DECISION]: [
        {
          language: 'python',
          title: 'Predictive Decision Making',
          before: `# Manual decision making
def make_business_decision(metrics):
    # Manual analysis
    if metrics['revenue'] > 100000:
        decision = 'expand'
    elif metrics['costs'] > metrics['revenue']:
        decision = 'reduce'
    else:
        decision = 'maintain'

    return decision`,
          after: `# AI-powered predictive decisions
import joblib
from sklearn.ensemble import RandomForestClassifier

model = joblib.load('business_decision_model.pkl')

def make_ai_decision(metrics, forecast_data):
    # Prepare features
    features = prepare_features(metrics, forecast_data)

    # Get prediction with confidence
    prediction = model.predict([features])[0]
    confidence = model.predict_proba([features]).max()

    return {
        'decision': prediction,
        'confidence': confidence,
        'reasoning': get_feature_importance(features),
        'risk_assessment': calculate_risk(features)
    }`,
          explanation: 'Transform intuitive decisions into data-driven, predictive recommendations.',
          benefits: ['40% better accuracy', 'Consistent decision making', 'Risk quantification', 'Explainable AI']
        }
      ],
      [OpportunityCategory.DATA]: [
        {
          language: 'sql',
          title: 'Real-time Analytics Pipeline',
          before: `-- Manual batch reporting
SELECT
    DATE(created_at) as report_date,
    COUNT(*) as daily_count,
    AVG(amount) as avg_amount
FROM transactions
WHERE DATE(created_at) = CURRENT_DATE - 1
GROUP BY DATE(created_at);`,
          after: `-- Real-time streaming analytics
CREATE STREAM transaction_stream (
    transaction_id STRING,
    amount DOUBLE,
    timestamp BIGINT
) WITH (
    kafka_topic='transactions',
    value_format='JSON'
);

CREATE TABLE real_time_metrics AS
SELECT
    WINDOWSTART as window_start,
    WINDOWEND as window_end,
    COUNT(*) as transaction_count,
    AVG(amount) as avg_amount,
    SUM(amount) as total_amount
FROM transaction_stream
WINDOW TUMBLING (SIZE 1 HOUR)
GROUP BY 1, 2;`,
          explanation: 'Move from batch reporting to real-time streaming analytics.',
          benefits: ['Real-time insights', 'Immediate alerts', 'Better decision speed', 'Continuous monitoring']
        }
      ],
      [OpportunityCategory.INFRASTRUCTURE]: [
        {
          language: 'yaml',
          title: 'Microservices Architecture',
          before: `# Monolithic deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: monolith-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: monolith
  template:
    metadata:
      labels:
        app: monolith
    spec:
      containers:
      - name: app
        image: monolith:latest
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"`,
          after: `# Microservices deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: user-service
  template:
    spec:
      containers:
      - name: user-service
        image: user-service:v1.2.0
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
        livenessProbe:
          httpGet:
            path: /health
            port: 8080`,
          explanation: 'Break monolithic applications into scalable microservices.',
          benefits: ['Independent scaling', 'Faster deployments', 'Technology diversity', 'Better fault isolation']
        }
      ],
      [OpportunityCategory.SECURITY]: [
        {
          language: 'python',
          title: 'Zero-Trust Security Implementation',
          before: `# Traditional security
def authenticate_user(username, password):
    if check_credentials(username, password):
        return create_session(username)
    return None

def access_resource(user_session, resource):
    if user_session.is_valid():
        return get_resource(resource)
    return "Unauthorized"`,
          after: `# Zero-trust security
import jwt
from functools import wraps

def zero_trust_auth(required_permissions):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = request.headers.get('Authorization')

            # Verify token
            payload = jwt.decode(token, secret_key)

            # Check device trust
            device_trust = verify_device_fingerprint(request)

            # Check behavioral patterns
            behavior_score = analyze_user_behavior(payload['user_id'])

            # Risk-based access control
            risk_score = calculate_risk_score(device_trust, behavior_score)

            if risk_score > threshold:
                require_additional_auth()

            if has_permissions(payload, required_permissions):
                return f(*args, **kwargs)

            return jsonify({'error': 'Access denied'}), 403

        return decorated_function
    return decorator`,
          explanation: 'Implement zero-trust security with continuous verification.',
          benefits: ['Advanced threat detection', 'Behavioral analysis', 'Reduced breach risk', 'Compliance ready']
        }
      ],
      [OpportunityCategory.PERFORMANCE]: [
        {
          language: 'javascript',
          title: 'Performance Optimization with Caching',
          before: `// No caching - slow database queries
async function getUserData(userId) {
    const query = 'SELECT * FROM users WHERE id = ?';
    const result = await database.query(query, [userId]);

    // Complex calculations
    const metrics = await calculateUserMetrics(userId);
    const recommendations = await generateRecommendations(userId);

    return {
        user: result[0],
        metrics,
        recommendations
    };
}`,
          after: `// Optimized with multi-layer caching
const redis = require('redis');
const client = redis.createClient();

async function getUserDataOptimized(userId) {
    const cacheKey = \`user:$\{userId\}:data\`;

    // Try L1 cache (memory)
    let cached = memoryCache.get(cacheKey);
    if (cached) return cached;

    // Try L2 cache (Redis)
    cached = await client.get(cacheKey);
    if (cached) {
        memoryCache.set(cacheKey, JSON.parse(cached));
        return JSON.parse(cached);
    }

    // Fetch from database (parallel execution)
    const [user, metrics, recommendations] = await Promise.all([
        getUserFromDB(userId),
        calculateUserMetrics(userId),
        generateRecommendations(userId)
    ]);

    const result = { user, metrics, recommendations };

    // Cache at both levels
    await client.setex(cacheKey, 3600, JSON.stringify(result));
    memoryCache.set(cacheKey, result);

    return result;
}`,
          explanation: 'Implement multi-layer caching for dramatic performance improvements.',
          benefits: ['95% faster response times', 'Reduced database load', 'Better user experience', 'Lower infrastructure costs']
        }
      ],
      [OpportunityCategory.COST_OPTIMIZATION]: [
        {
          language: 'terraform',
          title: 'Automated Resource Optimization',
          before: `# Static resource allocation
resource "aws_instance" "web_server" {
  ami           = "ami-12345678"
  instance_type = "m5.2xlarge"  # Always large instance

  tags = {
    Name = "WebServer"
  }
}

resource "aws_rds_instance" "database" {
  instance_class = "db.r5.xlarge"  # Always large DB
  storage_type   = "gp2"
  allocated_storage = 1000  # Fixed storage
}`,
          after: `# Dynamic resource optimization
resource "aws_autoscaling_group" "web_servers" {
  name                = "web-servers-asg"
  vpc_zone_identifier = [aws_subnet.private[*].id]
  target_group_arns   = [aws_lb_target_group.web.arn]
  health_check_type   = "ELB"

  min_size         = 2
  max_size         = 10
  desired_capacity = 3

  # Scale based on CPU and custom metrics
  enabled_metrics = [
    "GroupMinSize",
    "GroupMaxSize",
    "GroupDesiredCapacity",
    "GroupInServiceInstances"
  ]

  mixed_instances_policy {
    instances_distribution {
      on_demand_base_capacity                  = 1
      on_demand_percentage_above_base_capacity = 20
      spot_allocation_strategy                 = "capacity-optimized"
    }

    launch_template {
      launch_template_specification {
        launch_template_id = aws_launch_template.web.id
        version           = "$Latest"
      }

      # Use multiple instance types for cost optimization
      override {
        instance_type     = "m5.large"
        weighted_capacity = "1"
      }
      override {
        instance_type     = "m5a.large"
        weighted_capacity = "1"
      }
      override {
        instance_type     = "c5.large"
        weighted_capacity = "1"
      }
    }
  }
}`,
          explanation: 'Transform fixed infrastructure into dynamic, cost-optimized resources.',
          benefits: ['40-60% cost reduction', 'Automatic scaling', 'Spot instance savings', 'Performance maintained']
        }
      ]
    };

    return examples[category] || examples[OpportunityCategory.AUTOMATION];
  }

  private static generateBusinessMetrics(impactScore: number): BusinessMetric[] {
    const baseMetrics = [
      {
        name: 'Processing Time',
        current: '4-6 hours',
        target: '15-30 minutes',
        improvement: '85% faster',
        timeframe: '3 months'
      },
      {
        name: 'Cost per Transaction',
        current: '$12.50',
        target: '$2.30',
        improvement: '82% reduction',
        timeframe: '6 months'
      },
      {
        name: 'Accuracy Rate',
        current: '87%',
        target: '99.5%',
        improvement: '+12.5%',
        timeframe: '4 months'
      },
      {
        name: 'Customer Satisfaction',
        current: '6.2/10',
        target: '8.8/10',
        improvement: '+42%',
        timeframe: '6 months'
      }
    ];

    // Adjust metrics based on impact score
    return baseMetrics.slice(0, Math.max(2, Math.ceil(impactScore / 3)));
  }

  private static generateStakeholders(category: OpportunityCategory): string[] {
    const stakeholderMap: { [key in OpportunityCategory]: string[] } = {
      [OpportunityCategory.NLP]: ['Chief Technology Officer', 'Data Science Team', 'Business Process Owners', 'Customer Support Team'],
      [OpportunityCategory.AUTOMATION]: ['Chief Operations Officer', 'Business Process Owners', 'IT Operations', 'Finance Team'],
      [OpportunityCategory.DECISION]: ['Chief Executive Officer', 'Business Intelligence Team', 'Department Heads', 'Data Analysts'],
      [OpportunityCategory.DATA]: ['Chief Data Officer', 'Analytics Team', 'IT Infrastructure', 'Business Units'],
      [OpportunityCategory.INFRASTRUCTURE]: ['Chief Technology Officer', 'DevOps Team', 'Security Team', 'Finance Team'],
      [OpportunityCategory.SECURITY]: ['Chief Information Security Officer', 'IT Security Team', 'Compliance Team', 'All Departments'],
      [OpportunityCategory.PERFORMANCE]: ['Chief Technology Officer', 'Engineering Team', 'Operations Team', 'Customer Success'],
      [OpportunityCategory.COST_OPTIMIZATION]: ['Chief Financial Officer', 'IT Operations', 'Business Unit Leaders', 'Executive Team']
    };

    return stakeholderMap[category];
  }

  private static generateSuccessCriteria(category: OpportunityCategory): string[] {
    const criteriaMap: { [key in OpportunityCategory]: string[] } = {
      [OpportunityCategory.NLP]: [
        'Achieve 95%+ accuracy in document classification',
        'Reduce processing time by 80%',
        'Handle 10,000+ documents per hour',
        'Maintain 99.9% system uptime'
      ],
      [OpportunityCategory.AUTOMATION]: [
        'Eliminate 90%+ manual tasks',
        'Achieve 99.5% process accuracy',
        'Reduce processing time by 75%',
        'Zero critical errors in production'
      ],
      [OpportunityCategory.DECISION]: [
        'Improve forecast accuracy by 40%',
        'Reduce decision-making time by 60%',
        'Increase revenue by 15%',
        'Achieve 85%+ user adoption'
      ],
      [OpportunityCategory.DATA]: [
        'Enable real-time data access (<1 second)',
        'Achieve 99.9% data quality score',
        'Support 100+ concurrent users',
        'Reduce report generation time by 90%'
      ],
      [OpportunityCategory.INFRASTRUCTURE]: [
        'Achieve 10x deployment frequency',
        'Reduce downtime by 80%',
        'Support independent team scaling',
        'Maintain <100ms response times'
      ],
      [OpportunityCategory.SECURITY]: [
        'Pass all security audits',
        'Reduce security incidents by 95%',
        'Achieve compliance certification',
        'Zero data breaches'
      ],
      [OpportunityCategory.PERFORMANCE]: [
        'Improve response times by 90%',
        'Reduce infrastructure costs by 40%',
        'Support 10x more concurrent users',
        'Achieve 99.99% availability'
      ],
      [OpportunityCategory.COST_OPTIMIZATION]: [
        'Reduce infrastructure costs by 40%',
        'Improve resource utilization by 60%',
        'Eliminate waste completely',
        'Maintain performance standards'
      ]
    };

    return criteriaMap[category];
  }

  private static generateChallenges(riskLevel: string): string[] {
    const challengesByRisk = {
      'LOW': [
        'User training and adoption',
        'Process documentation updates',
        'Minor integration complexities',
        'Change management coordination'
      ],
      'MEDIUM': [
        'Technical integration complexity',
        'Data quality and availability',
        'Stakeholder alignment and buy-in',
        'Resource allocation and timing',
        'Performance optimization requirements'
      ],
      'HIGH': [
        'Complex system architecture changes',
        'Significant organizational change management',
        'Regulatory compliance requirements',
        'Large-scale data migration challenges',
        'Extended timeline and budget risks',
        'Multiple stakeholder coordination',
        'Legacy system integration difficulties'
      ]
    };

    return challengesByRisk[riskLevel as keyof typeof challengesByRisk] || challengesByRisk['MEDIUM'];
  }

  public static getOpportunityById(opportunityId: string): TransformationOpportunity | null {
    const opportunities = this.generateOpportunities('mock-assessment');
    return opportunities.find(opp => opp.id === opportunityId) || null;
  }

  public static getOpportunitiesByCategory(category: OpportunityCategory): TransformationOpportunity[] {
    const opportunities = this.generateOpportunities('mock-assessment');
    return opportunities.filter(opp => opp.category === category);
  }

  public static getPrioritizedOpportunities(maxCount?: number): TransformationOpportunity[] {
    const opportunities = this.generateOpportunities('mock-assessment');
    return maxCount ? opportunities.slice(0, maxCount) : opportunities;
  }

  public static generateOpportunityMatrix(): {
    opportunities: TransformationOpportunity[],
    matrix: { impact: number, effort: number, opportunities: TransformationOpportunity[] }[]
  } {
    const opportunities = this.generateOpportunities('mock-assessment');

    // Create impact vs effort matrix
    const matrix: { impact: number, effort: number, opportunities: TransformationOpportunity[] }[] = [];

    for (let impact = 1; impact <= 10; impact++) {
      for (let effort = 1; effort <= 10; effort++) {
        const oppsInCell = opportunities.filter(opp =>
          opp.impactScore === impact && opp.effortScore === effort
        );
        if (oppsInCell.length > 0) {
          matrix.push({ impact, effort, opportunities: oppsInCell });
        }
      }
    }

    return { opportunities, matrix };
  }
}