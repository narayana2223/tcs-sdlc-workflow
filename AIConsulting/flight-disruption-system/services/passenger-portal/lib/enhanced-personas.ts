import { PassengerPersona, Flight, Passenger, Notification, RebookingOption, TravelAssistance, Compensation } from '@/types';

/**
 * Enhanced Passenger Personas for Agentic Intelligence Demonstration
 * 
 * Complex, interconnected scenarios that showcase advanced agent reasoning,
 * group dynamics, special needs handling, and cascade effect management.
 */

export const enhancedPersonas: PassengerPersona[] = [
  // Original 3 personas (enhanced)
  {
    id: 'business-exec',
    name: 'Sarah Chen - Business Executive',
    description: 'Frequent business traveler with critical board meeting',
    avatar: '👩‍💼',
    scenario: 'Cancelled international flight with £2M merger presentation',
    passenger: {
      id: 'passenger-1',
      pnr: 'ABC123',
      firstName: 'Sarah',
      lastName: 'Chen',
      email: 'sarah.chen@globalcorp.com',
      phone: '+44 7700 123456',
      tier: 'gold',
      frequentFlyer: 'BA123456789',
      preferences: {
        seatType: 'aisle',
        mealType: 'kosher',
        notifications: ['email', 'sms', 'push', 'whatsapp'],
        timePreference: 'morning',
      },
      specialRequests: ['priority_rebooking', 'business_lounge_access', 'executive_car_service'],
      travelPurpose: 'business_critical',
      companyBudget: 15000,
    },
    mockFlight: {
      id: 'flight-1',
      flightNumber: 'BA123',
      airline: 'British Airways',
      departureAirport: 'LHR',
      arrivalAirport: 'JFK',
      departureTerminal: '5',
      arrivalTerminal: '7',
      scheduledDeparture: new Date('2024-01-15T08:00:00Z'),
      scheduledArrival: new Date('2024-01-15T16:30:00Z'),
      estimatedDeparture: new Date('2024-01-15T08:00:00Z'),
      estimatedArrival: new Date('2024-01-15T16:30:00Z'),
      status: 'cancelled',
      seat: '3A',
      aircraft: 'Boeing 787-9',
      reason: 'Aircraft technical issue - engine maintenance required',
      originalCost: 4500,
    },
    agentReasoningContext: {
      priority: 10,
      businessImpact: 'critical',
      timeConstraints: ['board_meeting_14:00_NYC', 'merger_announcement_16:00'],
      alternatives: ['private_jet', 'premium_competing_airline', 'video_conference_backup'],
      cost_flexibility: 'high',
      satisfaction_target: 4.8,
    }
  },

  {
    id: 'family-vacation',
    name: 'The Johnson Family',
    description: 'Family of four with connecting flights and resort bookings',
    avatar: '👨‍👩‍👧‍👦',
    scenario: 'Delayed vacation flight risking £8K resort package',
    passenger: {
      id: 'passenger-2',
      pnr: 'FAM456',
      firstName: 'David',
      lastName: 'Johnson',
      email: 'david.johnson@gmail.com',
      phone: '+44 7700 987654',
      tier: 'economy',
      familyGroup: ['david_johnson', 'emma_johnson', 'sophie_johnson_8', 'charlie_johnson_5'],
      preferences: {
        seatType: 'together',
        mealType: 'child_meals',
        notifications: ['email', 'sms'],
        timePreference: 'flexible',
      },
      specialRequests: ['family_seating', 'child_entertainment', 'early_boarding'],
      travelPurpose: 'family_vacation',
      budgetConstraints: 'medium',
    },
    mockFlight: {
      id: 'flight-2',
      flightNumber: 'EZY892',
      airline: 'easyJet',
      departureAirport: 'LGW',
      arrivalAirport: 'BCN',
      scheduledDeparture: new Date('2024-01-15T07:30:00Z'),
      scheduledArrival: new Date('2024-01-15T10:45:00Z'),
      estimatedDeparture: new Date('2024-01-15T12:30:00Z'),
      estimatedArrival: new Date('2024-01-15T15:45:00Z'),
      status: 'delayed',
      delay: 300,
      seat: '15A-15D',
      aircraft: 'Airbus A320',
      reason: 'Air traffic control restrictions - thunderstorms',
      originalCost: 1200,
    },
    agentReasoningContext: {
      priority: 7,
      businessImpact: 'medium',
      groupDynamics: 'family_unit_priority',
      timeConstraints: ['resort_checkin_16:00', 'connecting_flight_BCN_PMI_17:30'],
      alternatives: ['later_direct_flight', 'alternative_airport', 'overnight_accommodation'],
      cost_flexibility: 'low',
      satisfaction_target: 4.2,
      special_considerations: ['child_welfare', 'family_stress_minimization'],
    }
  },

  {
    id: 'budget-student',
    name: 'Alex Rivera - Student',
    description: 'Budget-conscious student with tight financial constraints',
    avatar: '🎓',
    scenario: 'Budget flight cancelled, needs affordable alternatives',
    passenger: {
      id: 'passenger-3',
      pnr: 'STU789',
      firstName: 'Alex',
      lastName: 'Rivera',
      email: 'alex.rivera@university.ac.uk',
      phone: '+44 7700 555123',
      tier: 'economy',
      studentStatus: 'verified',
      preferences: {
        seatType: 'any',
        mealType: 'vegetarian',
        notifications: ['email', 'push'],
        timePreference: 'flexible',
      },
      specialRequests: ['student_discount', 'budget_accommodation'],
      travelPurpose: 'personal',
      budgetLimit: 300,
    },
    mockFlight: {
      id: 'flight-3',
      flightNumber: 'FR456',
      airline: 'Ryanair',
      departureAirport: 'STN',
      arrivalAirport: 'MAD',
      scheduledDeparture: new Date('2024-01-15T06:00:00Z'),
      scheduledArrival: new Date('2024-01-15T09:30:00Z'),
      estimatedDeparture: new Date('2024-01-15T06:00:00Z'),
      estimatedArrival: new Date('2024-01-15T09:30:00Z'),
      status: 'cancelled',
      aircraft: 'Boeing 737-800',
      reason: 'Crew scheduling conflict - industrial action',
      originalCost: 89,
    },
    agentReasoningContext: {
      priority: 4,
      businessImpact: 'low',
      budgetConstraints: 'critical',
      timeConstraints: ['university_term_start_tomorrow'],
      alternatives: ['budget_competitor', 'bus_alternative', 'train_option'],
      cost_flexibility: 'very_low',
      satisfaction_target: 3.8,
      special_considerations: ['financial_hardship', 'student_support'],
    }
  },

  // NEW COMPLEX PERSONAS

  {
    id: 'elderly-mobility',
    name: 'Margaret & Harold Thompson - Elderly Couple',
    description: 'Elderly passengers with mobility issues and medical needs',
    avatar: '👴👵',
    scenario: 'Medical appointment trip with wheelchair assistance and medication timing',
    passenger: {
      id: 'passenger-4',
      pnr: 'ELD123',
      firstName: 'Margaret',
      lastName: 'Thompson',
      email: 'margaret.thompson@gmail.com',
      phone: '+44 7700 334455',
      tier: 'economy',
      age: 78,
      companionPassenger: 'harold_thompson_82',
      medicalNeeds: ['wheelchair_assistance', 'oxygen_concentrator', 'medication_schedule'],
      preferences: {
        seatType: 'aisle_with_wheelchair_access',
        mealType: 'low_sodium',
        notifications: ['phone_call', 'large_text_sms'],
        timePreference: 'morning_preferred',
      },
      specialRequests: ['priority_boarding', 'medical_equipment', 'assistance_throughout'],
      travelPurpose: 'medical_appointment',
      insuranceCoverage: 'comprehensive',
    },
    mockFlight: {
      id: 'flight-4',
      flightNumber: 'BA567',
      airline: 'British Airways',
      departureAirport: 'MAN',
      arrivalAirport: 'LHR',
      scheduledDeparture: new Date('2024-01-15T09:00:00Z'),
      scheduledArrival: new Date('2024-01-15T10:15:00Z'),
      estimatedDeparture: new Date('2024-01-15T11:30:00Z'),
      estimatedArrival: new Date('2024-01-15T12:45:00Z'),
      status: 'delayed',
      delay: 150,
      seat: '1A-1B',
      aircraft: 'Airbus A320',
      reason: 'Dense fog at destination - visibility below minimums',
      originalCost: 240,
    },
    agentReasoningContext: {
      priority: 9,
      businessImpact: 'high',
      medicalUrgency: 'critical',
      timeConstraints: ['cardiologist_appointment_15:00', 'medication_schedule_12:00'],
      alternatives: ['medical_transport', 'postpone_appointment', 'ground_transport'],
      cost_flexibility: 'medium',
      satisfaction_target: 4.5,
      special_considerations: ['health_safety_priority', 'comfort_paramount', 'stress_minimization'],
      accessibilityRequirements: ['wheelchair_boarding', 'medical_equipment_space', 'assistance_personnel'],
    }
  },

  {
    id: 'business-group',
    name: 'TechCorp Executive Team',
    description: 'Business group of 12 executives traveling to acquisition meeting',
    avatar: '🏢',
    scenario: 'Corporate group flight cancelled - £50M acquisition at stake',
    passenger: {
      id: 'passenger-5',
      pnr: 'GRP890',
      firstName: 'James',
      lastName: 'Mitchell',
      email: 'james.mitchell@techcorp.com',
      phone: '+44 7700 112233',
      tier: 'platinum',
      groupLeader: true,
      groupSize: 12,
      groupMembers: [
        'james_mitchell_ceo', 'sarah_williams_cfo', 'david_brown_cto', 'lisa_davis_cmo',
        'michael_jones_vp_sales', 'jennifer_wilson_vp_ops', 'robert_taylor_legal',
        'mary_anderson_hr', 'william_thomas_strategy', 'elizabeth_jackson_finance',
        'christopher_white_rd', 'jessica_martin_compliance'
      ],
      preferences: {
        seatType: 'business_class_together',
        mealType: 'business_select',
        notifications: ['email', 'executive_assistant'],
        timePreference: 'morning',
      },
      specialRequests: ['group_seating', 'priority_check_in', 'business_lounge', 'conference_facilities'],
      travelPurpose: 'business_critical',
      companyBudget: 85000,
    },
    mockFlight: {
      id: 'flight-5',
      flightNumber: 'VS024',
      airline: 'Virgin Atlantic',
      departureAirport: 'LHR',
      arrivalAirport: 'SFO',
      scheduledDeparture: new Date('2024-01-15T10:30:00Z'),
      scheduledArrival: new Date('2024-01-15T21:45:00Z'),
      estimatedDeparture: new Date('2024-01-15T10:30:00Z'),
      estimatedArrival: new Date('2024-01-15T21:45:00Z'),
      status: 'cancelled',
      seat: '6A-9D',
      aircraft: 'Boeing 787-9',
      reason: 'Aircraft maintenance - mandatory safety inspection',
      originalCost: 42000,
    },
    agentReasoningContext: {
      priority: 10,
      businessImpact: 'critical',
      groupDynamics: 'leadership_hierarchy',
      timeConstraints: ['acquisition_meeting_09:00_pst', 'board_call_15:00_gmt', 'market_announcement_deadline'],
      alternatives: ['charter_aircraft', 'first_class_competitors', 'split_group_multiple_flights'],
      cost_flexibility: 'very_high',
      satisfaction_target: 4.9,
      special_considerations: ['confidentiality', 'group_cohesion', 'executive_expectations'],
      groupRequirements: ['secure_communication', 'meeting_space', 'catering_arrangements'],
    }
  },

  {
    id: 'unaccompanied-minor',
    name: 'Emma Rodriguez - Unaccompanied Minor',
    description: '12-year-old traveling alone to divorced parent',
    avatar: '👧',
    scenario: 'Child traveling alone with strict custody schedule and guardian coordination',
    passenger: {
      id: 'passenger-6',
      pnr: 'UMR345',
      firstName: 'Emma',
      lastName: 'Rodriguez',
      email: 'maria.rodriguez@gmail.com', // Guardian contact
      phone: '+44 7700 998877',
      tier: 'economy',
      age: 12,
      unaccompaniedMinor: true,
      guardianInfo: {
        departure: 'maria_rodriguez_mother',
        arrival: 'carlos_rodriguez_father',
        emergency: 'ana_rodriguez_grandmother',
      },
      preferences: {
        seatType: 'window_supervised',
        mealType: 'child_meal',
        notifications: ['guardian_sms', 'guardian_email'],
        timePreference: 'not_late_evening',
      },
      specialRequests: ['um_supervision', 'child_entertainment', 'regular_check_ins'],
      travelPurpose: 'family_visit',
      legalRequirements: ['custody_documentation', 'guardian_authorization'],
    },
    mockFlight: {
      id: 'flight-6',
      flightNumber: 'IB3847',
      airline: 'Iberia',
      departureAirport: 'LHR',
      arrivalAirport: 'MAD',
      scheduledDeparture: new Date('2024-01-15T16:20:00Z'),
      scheduledArrival: new Date('2024-01-15T19:35:00Z'),
      estimatedDeparture: new Date('2024-01-15T16:20:00Z'),
      estimatedArrival: new Date('2024-01-15T19:35:00Z'),
      status: 'cancelled',
      seat: '12A',
      aircraft: 'Airbus A320',
      reason: 'Strike action by ground handling staff',
      originalCost: 180,
    },
    agentReasoningContext: {
      priority: 9,
      businessImpact: 'high',
      childWelfare: 'paramount',
      timeConstraints: ['custody_schedule_friday_18:00', 'school_monday_08:00'],
      alternatives: ['next_day_flight', 'accompanied_rebooking', 'guardian_travel'],
      cost_flexibility: 'low',
      satisfaction_target: 4.7,
      special_considerations: ['child_safety', 'legal_compliance', 'emotional_support'],
      regulatoryRequirements: ['um_protocols', 'guardian_notification', 'documentation_verification'],
    }
  },

  {
    id: 'international-transfer',
    name: 'Dr. Raj Patel - Transit Passenger',
    description: 'International passenger with visa constraints and tight connection',
    avatar: '👨‍⚕️',
    scenario: 'Medical conference speaker with visa restrictions and equipment',
    passenger: {
      id: 'passenger-7',
      pnr: 'INT567',
      firstName: 'Raj',
      lastName: 'Patel',
      email: 'dr.patel@medical-institute.in',
      phone: '+91 98765 43210',
      tier: 'gold',
      nationality: 'indian',
      visaStatus: {
        transit_uk: 'not_required',
        destination_germany: 'conference_visa',
        restrictions: ['no_overnight_stay', 'airside_only'],
      },
      preferences: {
        seatType: 'aisle',
        mealType: 'vegetarian_hindu',
        notifications: ['email', 'whatsapp'],
        timePreference: 'flexible',
      },
      specialRequests: ['medical_equipment_carry_on', 'priority_connection'],
      travelPurpose: 'professional_conference',
      timeZoneConstraints: 'presentation_schedule_cet',
    },
    mockFlight: {
      id: 'flight-7',
      flightNumber: 'AI131',
      airline: 'Air India',
      departureAirport: 'DEL',
      arrivalAirport: 'LHR',
      connectionFlight: 'LH924_LHR_FRA',
      scheduledDeparture: new Date('2024-01-15T02:00:00Z'),
      scheduledArrival: new Date('2024-01-15T06:30:00Z'),
      estimatedDeparture: new Date('2024-01-15T04:30:00Z'),
      estimatedArrival: new Date('2024-01-15T09:00:00Z'),
      status: 'delayed',
      delay: 150,
      seat: '9C',
      aircraft: 'Boeing 787-8',
      reason: 'Runway congestion at departure - peak hour traffic',
      originalCost: 890,
      connectionTight: true,
    },
    agentReasoningContext: {
      priority: 8,
      businessImpact: 'medium',
      visaComplications: 'critical',
      timeConstraints: ['conference_keynote_14:00_cet', 'connection_lh924_11:30'],
      alternatives: ['later_connection', 'overnight_option_restricted', 'alternative_routing'],
      cost_flexibility: 'medium',
      satisfaction_target: 4.3,
      special_considerations: ['visa_restrictions', 'medical_equipment', 'international_protocols'],
      complianceRequirements: ['immigration_clearance', 'customs_medical_equipment', 'transit_documentation'],
    }
  },

  {
    id: 'pregnant-traveler',
    name: 'Dr. Sophie Laurent - Pregnant Traveler',
    description: '7-months pregnant doctor traveling for emergency family medical situation',
    avatar: '🤰',
    scenario: 'Pregnant passenger with medical restrictions and family emergency',
    passenger: {
      id: 'passenger-8',
      pnr: 'PRG789',
      firstName: 'Sophie',
      lastName: 'Laurent',
      email: 'sophie.laurent@hopital-paris.fr',
      phone: '+33 6 12 34 56 78',
      tier: 'silver',
      pregnancyWeeks: 28,
      medicalClearance: 'fit_to_fly_until_32_weeks',
      preferences: {
        seatType: 'aisle_extra_legroom',
        mealType: 'pregnancy_nutrition',
        notifications: ['email', 'sms'],
        timePreference: 'avoid_late_evening',
      },
      specialRequests: ['priority_boarding', 'medical_assistance_standby', 'frequent_comfort_stops'],
      travelPurpose: 'family_emergency',
      emergencyContact: 'husband_pediatrician',
      medicalNeeds: ['regular_movement', 'hydration', 'stress_minimization'],
    },
    mockFlight: {
      id: 'flight-8',
      flightNumber: 'AF1580',
      airline: 'Air France',
      departureAirport: 'CDG',
      arrivalAirport: 'LHR',
      scheduledDeparture: new Date('2024-01-15T14:30:00Z'),
      scheduledArrival: new Date('2024-01-15T14:50:00Z'),
      estimatedDeparture: new Date('2024-01-15T14:30:00Z'),
      estimatedArrival: new Date('2024-01-15T14:50:00Z'),
      status: 'cancelled',
      seat: '8A',
      aircraft: 'Airbus A319',
      reason: 'Air traffic control strikes - French airspace restrictions',
      originalCost: 320,
    },
    agentReasoningContext: {
      priority: 9,
      businessImpact: 'high',
      medicalPriority: 'pregnancy_safety',
      timeConstraints: ['father_surgery_tomorrow_09:00', 'medical_curfew_20:00'],
      alternatives: ['eurostar_option', 'next_available_flight', 'medical_transport'],
      cost_flexibility: 'medium',
      satisfaction_target: 4.6,
      special_considerations: ['pregnancy_comfort', 'medical_safety', 'family_emergency_stress'],
      medicalRequirements: ['doctor_clearance', 'medical_assistance', 'comfort_priority'],
    }
  },

  {
    id: 'frequent-flyer-elite',
    name: 'Marcus Sterling - Diamond Status',
    description: 'Ultra-high-value frequent flyer with diamond status and complex routing',
    avatar: '💎',
    scenario: 'Diamond elite member with multi-city business trip and upgrade expectations',
    passenger: {
      id: 'passenger-9',
      pnr: 'DIA001',
      firstName: 'Marcus',
      lastName: 'Sterling',
      email: 'marcus.sterling@sterling-ventures.com',
      phone: '+1 555 123 4567',
      tier: 'diamond',
      frequentFlyerNumber: 'BA000123456',
      lifetimeStatus: 'million_miler',
      annualSpend: 125000,
      preferences: {
        seatType: 'first_class_preferred',
        mealType: 'chef_selection',
        notifications: ['dedicated_agent', 'priority_sms'],
        timePreference: 'morning_flights',
      },
      specialRequests: ['automatic_upgrades', 'concierge_service', 'priority_everything'],
      travelPurpose: 'multi_city_business',
      loyaltyExpectations: 'white_glove_service',
      complexItinerary: ['LHR-LAX-NRT-LHR'],
    },
    mockFlight: {
      id: 'flight-9',
      flightNumber: 'BA269',
      airline: 'British Airways',
      departureAirport: 'LHR',
      arrivalAirport: 'LAX',
      scheduledDeparture: new Date('2024-01-15T11:30:00Z'),
      scheduledArrival: new Date('2024-01-15T23:05:00Z'),
      estimatedDeparture: new Date('2024-01-15T11:30:00Z'),
      estimatedArrival: new Date('2024-01-15T23:05:00Z'),
      status: 'cancelled',
      seat: '1A',
      aircraft: 'Boeing 777-300ER',
      reason: 'Aircraft rotation issue - maintenance delay on incoming flight',
      originalCost: 8500,
      upgradedCost: 0, // Complimentary due to status
    },
    agentReasoningContext: {
      priority: 10,
      businessImpact: 'critical',
      loyaltyValue: 'ultra_high',
      timeConstraints: ['board_meeting_la_tomorrow', 'tokyo_presentation_thursday'],
      alternatives: ['first_class_any_airline', 'private_jet_reimbursement', 'premium_competitor'],
      cost_flexibility: 'unlimited',
      satisfaction_target: 4.95,
      special_considerations: ['reputation_protection', 'loyalty_retention', 'service_excellence'],
      vipRequirements: ['personal_attention', 'proactive_solutions', 'compensation_generous'],
    }
  },

  {
    id: 'last-minute-emergency',
    name: 'Jennifer Walsh - Medical Emergency',
    description: 'Last-minute booking for family medical emergency',
    avatar: '🚑',
    scenario: 'Emergency travel for critical family medical situation',
    passenger: {
      id: 'passenger-10',
      pnr: 'EMG456',
      firstName: 'Jennifer',
      lastName: 'Walsh',
      email: 'jennifer.walsh@gmail.com',
      phone: '+44 7700 445566',
      tier: 'economy',
      emergencyBooking: true,
      bookingTime: new Date(Date.now() - 3600000), // 1 hour ago
      preferences: {
        seatType: 'any_available',
        mealType: 'any',
        notifications: ['urgent_sms', 'phone_call'],
        timePreference: 'asap',
      },
      specialRequests: ['emergency_priority', 'flexible_ticket'],
      travelPurpose: 'family_medical_emergency',
      emotionalState: 'distressed',
      paymentMethod: 'emergency_credit_card',
    },
    mockFlight: {
      id: 'flight-10',
      flightNumber: 'EI154',
      airline: 'Aer Lingus',
      departureAirport: 'LHR',
      arrivalAirport: 'DUB',
      scheduledDeparture: new Date('2024-01-15T18:30:00Z'),
      scheduledArrival: new Date('2024-01-15T19:45:00Z'),
      estimatedDeparture: new Date('2024-01-15T21:00:00Z'),
      estimatedArrival: new Date('2024-01-15T22:15:00Z'),
      status: 'delayed',
      delay: 150,
      seat: '23F',
      aircraft: 'Airbus A320',
      reason: 'Crew duty time limits - replacement crew en route',
      originalCost: 340,
      emergencyBookingFee: 150,
    },
    agentReasoningContext: {
      priority: 9,
      businessImpact: 'high',
      emotionalUrgency: 'critical',
      timeConstraints: ['hospital_visiting_hours_end_21:00', 'surgery_tomorrow_early'],
      alternatives: ['any_available_flight', 'ground_transport', 'competing_airline'],
      cost_flexibility: 'secondary_concern',
      satisfaction_target: 4.4,
      special_considerations: ['emotional_support', 'urgency_paramount', 'compassionate_handling'],
      emergencyProtocols: ['immediate_rebooking', 'fee_waiver_consideration', 'support_services'],
    }
  },
];

// Enhanced scenario interconnections and group dynamics
export const scenarioInterconnections = {
  business_group_conflicts: {
    'business-exec': {
      conflicts_with: ['business-group'],
      reason: 'Competing for last business class seats on alternative flights',
      resolution: 'Priority based on individual vs group booking value',
    },
    'frequent-flyer-elite': {
      conflicts_with: ['business-exec', 'business-group'],
      reason: 'Status-based upgrade priorities in limited premium inventory',
      resolution: 'Lifetime status trumps individual booking value',
    },
  },
  resource_competition: {
    hotel_availability: {
      competing_passengers: ['business-exec', 'business-group', 'frequent-flyer-elite'],
      limited_inventory: 'Only 5 five-star hotel rooms available',
      agent_reasoning: 'Multi-criteria optimization balancing status, cost, and group size',
    },
    ground_transport: {
      competing_passengers: ['elderly-mobility', 'pregnant-traveler', 'unaccompanied-minor'],
      special_needs: 'Limited wheelchair-accessible vehicles and child safety seats',
      agent_reasoning: 'Medical and safety needs prioritization matrix',
    },
  },
  cascade_effects: {
    weather_closure: {
      affected_flights: ['flight-1', 'flight-2', 'flight-4', 'flight-7', 'flight-8'],
      impact_radius: 'All European destinations affected by storm system',
      agent_coordination: 'Multi-agent collaboration for network optimization',
    },
    crew_shortage: {
      affected_flights: ['flight-3', 'flight-6', 'flight-10'],
      impact_type: 'Strike action spreading across multiple carriers',
      agent_coordination: 'Real-time negotiation with alternative carriers',
    },
  },
};

// Agent reasoning complexity showcase
export const agentReasoningShowcase = {
  multi_criteria_decisions: [
    {
      scenario: 'Hotel allocation with limited premium rooms',
      agents_involved: ['resource_agent', 'passenger_agent', 'cost_optimizer'],
      decision_factors: ['passenger_tier', 'booking_value', 'medical_needs', 'group_size'],
      conflict_resolution: 'Weighted scoring with transparency',
      outcome: 'Optimal allocation with detailed reasoning explanation',
    },
    {
      scenario: 'Medical equipment passenger vs. business group seating',
      agents_involved: ['passenger_agent', 'coordinator_agent', 'compliance_agent'],
      decision_factors: ['safety_requirements', 'business_value', 'regulatory_compliance'],
      conflict_resolution: 'Safety and compliance override commercial considerations',
      outcome: 'Medical needs prioritized with alternative business arrangements',
    },
  ],
  learning_adaptations: [
    {
      scenario: 'Pregnant passenger satisfaction tracking',
      learning_input: 'Previous pregnant passenger feedback and medical recommendations',
      agent_adaptation: 'Enhanced comfort protocols and proactive medical checks',
      outcome: 'Improved satisfaction scores and safety compliance',
    },
    {
      scenario: 'Business group rebooking optimization',
      learning_input: 'Historical group dynamics and productivity impact data',
      agent_adaptation: 'Preference for keeping groups together vs. faster individual solutions',
      outcome: 'Balanced approach based on group size and urgency',
    },
  ],
};

export const getPersonaById = (id: string): PassengerPersona | null => {
  return enhancedPersonas.find(persona => persona.id === id) || null;
};

export const getPersonasByPriority = (): PassengerPersona[] => {
  return enhancedPersonas.sort((a, b) => 
    (b.agentReasoningContext?.priority || 0) - (a.agentReasoningContext?.priority || 0)
  );
};

export const getConflictingScenarios = (): PassengerPersona[] => {
  return enhancedPersonas.filter(persona => 
    ['business-exec', 'business-group', 'frequent-flyer-elite'].includes(persona.id)
  );
};

export const getMedicalPriorityPassengers = (): PassengerPersona[] => {
  return enhancedPersonas.filter(persona => 
    persona.passenger.medicalNeeds || 
    persona.agentReasoningContext?.medicalPriority ||
    persona.passenger.pregnancyWeeks ||
    persona.passenger.age > 70
  );
};