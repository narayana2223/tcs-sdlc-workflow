/**
 * Cascade Disruption Scenarios for Agentic Intelligence Demonstration
 * 
 * Complex, interconnected disruption scenarios affecting 150+ passengers
 * that showcase advanced multi-agent coordination, conflict resolution,
 * and resource optimization at scale.
 */

export interface CascadePassenger {
  id: string
  name: string
  pnr: string
  flightNumber: string
  priority: number
  tier: 'diamond' | 'gold' | 'silver' | 'bronze' | 'economy'
  specialNeeds: string[]
  connectionFlights: string[]
  groupAssociation?: string
  medicalRequirements?: string[]
  businessValue: number
  satisfactionTarget: number
  constraints: string[]
}

export interface CascadeScenario {
  id: string
  name: string
  description: string
  triggerEvent: string
  affected_airports: string[]
  affected_flights: string[]
  total_passengers: number
  cascade_timeline: CascadeEvent[]
  passenger_breakdown: {
    by_tier: Record<string, number>
    by_special_needs: Record<string, number>
    by_destination: Record<string, number>
    groups: GroupBooking[]
  }
  agent_challenges: AgentChallenge[]
  expected_resolution_time: number
  cost_impact: number
  success_metrics: SuccessMetric[]
}

export interface CascadeEvent {
  timestamp: number // minutes from scenario start
  event_type: 'disruption' | 'cascade' | 'agent_decision' | 'resolution' | 'complication'
  description: string
  affected_passengers: string[]
  agent_response: string
  decision_reasoning: string[]
  alternatives_considered: string[]
  cost_impact: number
  passenger_satisfaction_impact: number
}

export interface GroupBooking {
  group_id: string
  group_name: string
  leader: string
  members: string[]
  group_type: 'business' | 'family' | 'tour' | 'conference' | 'wedding'
  keep_together: boolean
  budget_constraints: number
}

export interface AgentChallenge {
  agent_type: string
  challenge: string
  complexity_factors: string[]
  decision_tree_depth: number
  collaboration_required: string[]
  success_criteria: string
}

export interface SuccessMetric {
  metric: string
  target: number
  current: number
  unit: string
  importance: 'critical' | 'high' | 'medium' | 'low'
}

export const cascadeScenarios: CascadeScenario[] = [
  {
    id: 'london_weather_cascade',
    name: 'London Weather System Cascade',
    description: 'Severe thunderstorm system closes all London airports, triggering Europe-wide cascade disruptions affecting 180+ passengers with complex interconnections',
    triggerEvent: 'Severe thunderstorm with 60+ mph winds and lightning closes LHR, LGW, STN, and LTN simultaneously',
    affected_airports: ['LHR', 'LGW', 'STN', 'LTN', 'CDG', 'AMS', 'FRA', 'MAD', 'FCO'],
    affected_flights: [
      'BA123_LHR_JFK', 'VS024_LHR_SFO', 'LH924_LHR_FRA', 'AF1580_CDG_LHR',
      'EZY892_LGW_BCN', 'U23478_LGW_MAD', 'FR456_STN_MAD', 'IB3847_LHR_MAD',
      'AI131_DEL_LHR', 'EI154_LHR_DUB', 'BA567_MAN_LHR', 'KL1234_AMS_LHR'
    ],
    total_passengers: 187,
    cascade_timeline: [
      {
        timestamp: 0,
        event_type: 'disruption',
        description: 'Weather system detected 2 hours out - predictive agents activate',
        affected_passengers: ['all'],
        agent_response: 'Prediction agents initiate early warning protocols, begin alternative planning',
        decision_reasoning: [
          'Met Office data shows 95% probability of closure within 2 hours',
          'Historical data indicates 6-8 hour closure typical for this weather pattern',
          'Proactive passenger notification required to minimize stress'
        ],
        alternatives_considered: [
          'Immediate ground stop', 'Selective diversions', 'Passenger pre-notification'
        ],
        cost_impact: 0,
        passenger_satisfaction_impact: 0.2 // Positive for proactive communication
      },
      {
        timestamp: 30,
        event_type: 'cascade',
        description: 'All London airports declare closure - 12 inbound flights must divert',
        affected_passengers: ['flight_12_passengers'],
        agent_response: 'Resource agents coordinate with European airports for diversion capacity',
        decision_reasoning: [
          'Birmingham and Manchester have available slots for wide-body aircraft',
          'Passenger distribution favors northern UK airports for ground transport',
          'Hotel availability concentrated around Birmingham for overnight stays'
        ],
        alternatives_considered: [
          'European diversions (CDG/AMS)', 'UK regional airports', 'Return to origin'
        ],
        cost_impact: 125000,
        passenger_satisfaction_impact: -0.3
      },
      {
        timestamp: 45,
        event_type: 'agent_decision',
        description: 'Multi-agent collaboration resolves resource conflicts for premium passengers',
        affected_passengers: ['business_group_techcorp', 'diamond_marcus_sterling'],
        agent_response: 'Coordinator agent mediates between competing high-value passenger claims',
        decision_reasoning: [
          'Marcus Sterling (Diamond) vs TechCorp group (12 executives) - complex priority calculation',
          'Individual lifetime value vs group booking value analysis',
          'Compromise: Sterling gets first class seat, TechCorp gets business class block'
        ],
        alternatives_considered: [
          'Strict tier-based priority', 'Business value priority', 'Hybrid solution'
        ],
        cost_impact: 45000,
        passenger_satisfaction_impact: 0.4
      },
      {
        timestamp: 90,
        event_type: 'complication',
        description: 'Medical emergency passenger requires immediate accommodation',
        affected_passengers: ['jennifer_walsh_emergency'],
        agent_response: 'Medical protocols override standard prioritization - emergency medical transport arranged',
        decision_reasoning: [
          'Family medical emergency takes precedence over commercial considerations',
          'Ground ambulance to Edinburgh with medical escort',
          'Insurance covers emergency transport costs'
        ],
        alternatives_considered: [
          'Air ambulance', 'Ground transport with medical escort', 'Hospital transfer'
        ],
        cost_impact: 12000,
        passenger_satisfaction_impact: 0.8
      },
      {
        timestamp: 120,
        event_type: 'resolution',
        description: 'All passengers accommodated - autonomous rebooking complete',
        affected_passengers: ['all'],
        agent_response: 'Final optimization complete - 187 passengers accommodated within 2 hours',
        decision_reasoning: [
          '98% of passengers accepted alternative arrangements',
          'Average satisfaction score 4.2/5 vs traditional 2.1/5',
          'Cost optimization achieved £340K savings vs manual handling'
        ],
        alternatives_considered: [],
        cost_impact: -340000, // Savings
        passenger_satisfaction_impact: 1.2
      }
    ],
    passenger_breakdown: {
      by_tier: {
        'diamond': 2,
        'gold': 15,
        'silver': 28,
        'bronze': 42,
        'economy': 100
      },
      by_special_needs: {
        'wheelchair_assistance': 8,
        'unaccompanied_minor': 3,
        'pregnant_traveler': 2,
        'medical_equipment': 4,
        'group_booking': 67,
        'connecting_flights': 89
      },
      by_destination: {
        'north_america': 45,
        'europe': 78,
        'asia': 23,
        'domestic_uk': 41
      },
      groups: [
        {
          group_id: 'techcorp_executives',
          group_name: 'TechCorp Executive Team',
          leader: 'james_mitchell',
          members: ['james_mitchell', 'sarah_williams', 'david_brown', 'lisa_davis', 'michael_jones', 'jennifer_wilson', 'robert_taylor', 'mary_anderson', 'william_thomas', 'elizabeth_jackson', 'christopher_white', 'jessica_martin'],
          group_type: 'business',
          keep_together: true,
          budget_constraints: 85000
        },
        {
          group_id: 'johnson_family',
          group_name: 'Johnson Family Vacation',
          leader: 'david_johnson',
          members: ['david_johnson', 'emma_johnson', 'sophie_johnson', 'charlie_johnson'],
          group_type: 'family',
          keep_together: true,
          budget_constraints: 3000
        },
        {
          group_id: 'medical_conference',
          group_name: 'European Medical Conference Delegates',
          leader: 'dr_raj_patel',
          members: ['dr_raj_patel', 'dr_sophie_laurent', 'dr_marcus_webb', 'prof_anna_schneider', 'dr_alessandro_rossi'],
          group_type: 'conference',
          keep_together: false,
          budget_constraints: 25000
        },
        {
          group_id: 'school_trip',
          group_name: 'St. Marys School Educational Trip',
          leader: 'teacher_helen_clark',
          members: ['teacher_helen_clark', 'assistant_mike_brown', 'emma_rodriguez', 'tom_wilson', 'lucy_garcia', 'alex_murphy', 'olivia_taylor', 'james_anderson', 'sophia_martinez', 'noah_thompson', 'isabella_white', 'william_lopez'],
          group_type: 'tour',
          keep_together: true,
          budget_constraints: 8000
        }
      ]
    },
    agent_challenges: [
      {
        agent_type: 'prediction',
        challenge: 'Weather pattern analysis with 2-4 hour forecast accuracy for multiple airports',
        complexity_factors: ['micro-climate variations', 'storm tracking', 'airport-specific thresholds'],
        decision_tree_depth: 4,
        collaboration_required: ['resource_agent', 'coordinator_agent'],
        success_criteria: 'Accurate closure prediction with 95% confidence'
      },
      {
        agent_type: 'resource',
        challenge: 'Multi-airport hotel allocation with complex passenger prioritization',
        complexity_factors: ['inventory constraints', 'location preferences', 'accessibility requirements'],
        decision_tree_depth: 5,
        collaboration_required: ['passenger_agent', 'cost_optimizer'],
        success_criteria: 'All passengers accommodated within budget and preference constraints'
      },
      {
        agent_type: 'passenger',
        challenge: 'Group booking management with individual vs collective optimization',
        complexity_factors: ['group dynamics', 'individual priorities', 'budget allocation'],
        decision_tree_depth: 6,
        collaboration_required: ['coordinator_agent', 'finance_agent'],
        success_criteria: 'Balanced individual and group satisfaction > 4.0'
      },
      {
        agent_type: 'coordinator',
        challenge: 'Multi-agent conflict resolution with competing high-value passengers',
        complexity_factors: ['loyalty tiers', 'business value', 'fairness principles'],
        decision_tree_depth: 7,
        collaboration_required: ['all_agents'],
        success_criteria: 'Conflicts resolved with transparent reasoning and stakeholder buy-in'
      }
    ],
    expected_resolution_time: 120, // 2 hours
    cost_impact: 680000, // Total operational cost
    success_metrics: [
      { metric: 'passenger_satisfaction', target: 4.2, current: 4.3, unit: '/5', importance: 'critical' },
      { metric: 'resolution_time', target: 180, current: 120, unit: 'minutes', importance: 'high' },
      { metric: 'cost_vs_manual', target: 300000, current: 340000, unit: 'GBP_saved', importance: 'high' },
      { metric: 'rebooking_success', target: 95, current: 98, unit: 'percent', importance: 'critical' },
      { metric: 'agent_decisions', target: 50, current: 67, unit: 'count', importance: 'medium' },
      { metric: 'conflicts_resolved', target: 8, current: 12, unit: 'count', importance: 'high' }
    ]
  },

  {
    id: 'crew_shortage_cascade',
    name: 'European Crew Strike Cascade',
    description: 'Coordinated cabin crew strikes across 5 European airlines create cascading effects with 200+ affected passengers and complex crew scheduling challenges',
    triggerEvent: 'Multi-airline cabin crew industrial action affects 15 flights across Europe',
    affected_airports: ['LHR', 'CDG', 'FRA', 'MAD', 'FCO', 'AMS', 'ZUR'],
    affected_flights: [
      'BA456_LHR_CDG', 'AF789_CDG_LHR', 'LH567_FRA_LHR', 'IB890_MAD_LHR',
      'FR123_STN_MAD', 'U2456_LGW_BCN', 'EZY789_LTN_AMS', 'KL234_AMS_LHR',
      'LX567_ZUR_LHR', 'AZ890_FCO_LHR', 'VY123_BCN_LHR', 'TP456_LIS_LHR',
      'OS789_VIE_LHR', 'SN123_BRU_LHR', 'SK456_CPH_LHR'
    ],
    total_passengers: 203,
    cascade_timeline: [
      {
        timestamp: 0,
        event_type: 'disruption',
        description: 'Strike announced - 6 hour notice given by cabin crew unions',
        affected_passengers: ['all'],
        agent_response: 'Crew scheduling agents activate emergency protocols, assess available crew resources',
        decision_reasoning: [
          'Strike affects 40% of planned crew schedules',
          'Reserve crew activation can cover 60% of affected flights',
          'Cross-training protocols allow limited inter-airline crew sharing'
        ],
        alternatives_considered: [
          'Flight cancellations', 'Crew reallocation', 'Partner airline agreements'
        ],
        cost_impact: 0,
        passenger_satisfaction_impact: -0.1
      },
      {
        timestamp: 60,
        event_type: 'cascade',
        description: 'Crew shortages force cancellation of 8 flights, delaying 12 others',
        affected_passengers: ['cancelled_flight_passengers'],
        agent_response: 'Mass rebooking operation initiated with partner airline coordination',
        decision_reasoning: [
          'Partner airlines have available capacity on competing routes',
          'Code-share agreements enable seamless transfers',
          'Premium passengers prioritized for same-day rebooking'
        ],
        alternatives_considered: [
          'Next day rebooking', 'Competitor airline transfers', 'Ground transport alternatives'
        ],
        cost_impact: 450000,
        passenger_satisfaction_impact: -0.4
      },
      {
        timestamp: 90,
        event_type: 'complication',
        description: 'Unaccompanied minor requires special handling due to custody constraints',
        affected_passengers: ['emma_rodriguez_um'],
        agent_response: 'Legal compliance agent ensures custody schedule adherence with emergency protocols',
        decision_reasoning: [
          'Custody agreement requires child delivery by Friday 18:00',
          'Strike delays risk violating legal custody arrangements',
          'Emergency guardian travel approval secured for accompaniment'
        ],
        alternatives_considered: [
          'Guardian accompaniment', 'Legal delay notification', 'Alternative custody arrangement'
        ],
        cost_impact: 8000,
        passenger_satisfaction_impact: 0.3
      }
    ],
    passenger_breakdown: {
      by_tier: {
        'diamond': 3,
        'gold': 18,
        'silver': 35,
        'bronze': 47,
        'economy': 100
      },
      by_special_needs: {
        'unaccompanied_minors': 4,
        'business_groups': 89,
        'medical_requirements': 6,
        'connecting_flights': 112
      },
      by_destination: {
        'uk_domestic': 45,
        'europe_mainland': 89,
        'long_haul_connections': 69
      },
      groups: []
    },
    agent_challenges: [
      {
        agent_type: 'crew_scheduling',
        challenge: 'Emergency crew reallocation across multiple airlines with union constraints',
        complexity_factors: ['union agreements', 'certification requirements', 'duty time limits'],
        decision_tree_depth: 5,
        collaboration_required: ['regulatory_agent', 'coordinator_agent'],
        success_criteria: 'Compliant crew scheduling for maximum flight operations'
      }
    ],
    expected_resolution_time: 180,
    cost_impact: 890000,
    success_metrics: [
      { metric: 'flights_operated', target: 70, current: 75, unit: 'percent', importance: 'critical' },
      { metric: 'regulatory_compliance', target: 100, current: 100, unit: 'percent', importance: 'critical' }
    ]
  },

  {
    id: 'system_failure_cascade',
    name: 'Air Traffic Control System Failure',
    description: 'NATS system failure creates nationwide UK airspace restrictions affecting 250+ passengers with complex routing challenges',
    triggerEvent: 'Primary and backup ATC systems fail simultaneously, closing UK airspace',
    affected_airports: ['LHR', 'LGW', 'STN', 'LTN', 'MAN', 'BHX', 'EDI', 'GLA'],
    affected_flights: [
      // 18 affected flights
      'BA001_LHR_SYD', 'QF002_LHR_SYD', 'UA901_LHR_EWR', 'VS003_LHR_JFK',
      'EY019_LHR_AUH', 'SV121_LHR_RUH', 'TK1980_LHR_IST', 'LH921_LHR_FRA',
      'AF1581_CDG_LHR', 'KL1023_AMS_LHR', 'IB3163_MAD_LHR', 'AZ201_FCO_LHR'
    ],
    total_passengers: 267,
    cascade_timeline: [
      {
        timestamp: 0,
        event_type: 'disruption',
        description: 'NATS system failure - UK airspace closed indefinitely',
        affected_passengers: ['all'],
        agent_response: 'Network optimization agents calculate European diversion scenarios',
        decision_reasoning: [
          'System failure could last 6-24 hours based on historical incidents',
          'European airports have limited capacity for UK flight diversions',
          'Passenger distribution across Europe required for accommodation'
        ],
        alternatives_considered: [
          'European diversions', 'Return to origin', 'Ground transport from Europe'
        ],
        cost_impact: 0,
        passenger_satisfaction_impact: -0.2
      }
    ],
    passenger_breakdown: {
      by_tier: {
        'diamond': 5,
        'gold': 25,
        'silver': 45,
        'bronze': 67,
        'economy': 125
      },
      by_special_needs: {
        'long_haul_passengers': 156,
        'connecting_international': 98,
        'business_critical': 78
      },
      by_destination: {
        'asia_pacific': 89,
        'north_america': 67,
        'middle_east': 45,
        'europe': 66
      },
      groups: []
    },
    agent_challenges: [
      {
        agent_type: 'network_optimization',
        challenge: 'European airspace capacity optimization with geopolitical constraints',
        complexity_factors: ['airspace sovereignty', 'airport capacity', 'ground handling'],
        decision_tree_depth: 6,
        collaboration_required: ['regulatory_agent', 'diplomatic_protocols'],
        success_criteria: 'Optimal passenger distribution minimizing total system cost'
      }
    ],
    expected_resolution_time: 360, // 6 hours
    cost_impact: 1200000,
    success_metrics: [
      { metric: 'diversion_success', target: 90, current: 95, unit: 'percent', importance: 'critical' },
      { metric: 'passenger_accommodation', target: 95, current: 98, unit: 'percent', importance: 'critical' }
    ]
  }
];

// Agent coordination patterns for complex scenarios
export const agentCoordinationPatterns = {
  resource_allocation: {
    pattern: 'hierarchical_with_consensus',
    description: 'Resource agent leads with passenger and cost agents providing input',
    decision_flow: ['resource_agent', 'passenger_agent', 'cost_optimizer', 'coordinator_approval'],
    conflict_resolution: 'weighted_voting_with_expertise_bonus'
  },
  
  medical_emergency: {
    pattern: 'medical_priority_override',
    description: 'Medical and safety considerations override all commercial priorities',
    decision_flow: ['medical_assessment', 'safety_clearance', 'resource_allocation', 'cost_secondary'],
    conflict_resolution: 'medical_safety_absolute_priority'
  },
  
  group_optimization: {
    pattern: 'multi_objective_with_constraints',
    description: 'Balance individual optimization with group cohesion requirements',
    decision_flow: ['group_constraint_analysis', 'individual_optimization', 'group_preference_weighting', 'compromise_solution'],
    conflict_resolution: 'pareto_optimal_with_fairness_adjustment'
  },

  vip_handling: {
    pattern: 'relationship_value_optimization',
    description: 'Long-term relationship value balanced with immediate operational efficiency',
    decision_flow: ['relationship_value_assessment', 'expectation_analysis', 'service_level_optimization', 'satisfaction_prediction'],
    conflict_resolution: 'lifetime_value_weighted_priority'
  }
};

// Success measurement frameworks
export const cascadeSuccessMetrics = {
  operational_efficiency: [
    'resolution_time_vs_baseline',
    'cost_optimization_vs_manual',
    'resource_utilization_rate',
    'agent_decision_accuracy'
  ],
  
  passenger_satisfaction: [
    'satisfaction_score_vs_traditional',
    'complaint_rate',
    'rebooking_acceptance_rate',
    'compensation_claim_rate'
  ],
  
  business_continuity: [
    'revenue_protection_rate',
    'relationship_damage_mitigation',
    'competitive_advantage_maintained',
    'brand_reputation_impact'
  ],
  
  regulatory_compliance: [
    'eu261_compliance_rate',
    'disability_accommodation_success',
    'unaccompanied_minor_protocol_adherence',
    'medical_emergency_response_time'
  ]
};

export const getCascadeScenarioById = (id: string): CascadeScenario | null => {
  return cascadeScenarios.find(scenario => scenario.id === id) || null;
};

export const getScenariosByComplexity = (): CascadeScenario[] => {
  return cascadeScenarios.sort((a, b) => b.total_passengers - a.total_passengers);
};

export const getScenariosByResolutionTime = (): CascadeScenario[] => {
  return cascadeScenarios.sort((a, b) => a.expected_resolution_time - b.expected_resolution_time);
};