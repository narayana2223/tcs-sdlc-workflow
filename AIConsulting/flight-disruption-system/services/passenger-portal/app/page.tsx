'use client';

import React, { useState, useEffect } from 'react';
import { 
  Bell, 
  Clock, 
  CheckCircle2, 
  AlertTriangle,
  Plane, 
  MapPin, 
  Phone, 
  MessageSquare,
  Shield,
  CreditCard,
  Calendar,
  Users,
  Star,
  ArrowRight,
  Zap,
  Heart,
  Coffee,
  Hotel,
  Car,
  Utensils,
  Wifi,
  Gift
} from 'lucide-react';

interface ProactiveAlert {
  id: string;
  type: 'early_warning' | 'solution_ready' | 'action_needed' | 'completed';
  priority: 'high' | 'medium' | 'low';
  timestamp: Date;
  title: string;
  message: string;
  passengerName: string;
  flightNumber: string;
  route: string;
  solutions?: Solution[];
  autoActionTaken?: string;
  estimatedDelay?: string;
  confidence: number;
}

interface Solution {
  id: string;
  title: string;
  description: string;
  benefits: string[];
  cost: string;
  timeToExecute: string;
  recommended: boolean;
  icon: React.ElementType;
  color: string;
  details: SolutionDetails;
}

interface SolutionDetails {
  flight?: {
    number: string;
    route: string;
    departure: string;
    arrival: string;
    aircraft: string;
    seatClass: string;
  };
  hotel?: {
    name: string;
    rating: number;
    location: string;
    amenities: string[];
    rate: string;
  };
  transport?: {
    type: string;
    provider: string;
    pickup: string;
    cost: string;
  };
  compensation?: {
    amount: string;
    type: string;
    reason: string;
  };
  extras?: {
    loungeAccess: boolean;
    mealVouchers: boolean;
    wifiCredits: boolean;
    priorityBoarding: boolean;
  };
}

interface PassengerProfile {
  id: string;
  name: string;
  email: string;
  phone: string;
  preferences: {
    seatType: string;
    mealType: string;
    communicationChannel: string;
    hotelCategory: string;
    transportType: string;
  };
  loyaltyStatus: string;
  pastDisruptions: number;
  satisfaction: number;
  businessProfile: {
    isBusinessTravel: boolean;
    company: string;
    meetingTime?: string;
    colleagues?: string[];
  };
}

export default function ProactivePassengerPortal() {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [activeAlert, setActiveAlert] = useState<ProactiveAlert | null>(null);
  const [selectedSolution, setSelectedSolution] = useState<Solution | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionStep, setExecutionStep] = useState('');

  // Sample proactive alerts
  const [alerts, setAlerts] = useState<ProactiveAlert[]>([
    {
      id: '1',
      type: 'early_warning',
      priority: 'high',
      timestamp: new Date(Date.now() - 3600000), // 1 hour ago
      title: 'Potential Disruption Detected',
      message: 'Weather patterns suggest 80% chance of 2-3 hour delays for your LHR-JFK flight. We\'ve prepared solutions.',
      passengerName: 'Sarah Chen',
      flightNumber: 'BA123',
      route: 'LHR → JFK',
      estimatedDelay: '2-3 hours',
      confidence: 85,
      solutions: [
        {
          id: 'sol1',
          title: 'Same Day via Dublin',
          description: 'Reroute through Dublin, arrives 2 hours later than original',
          benefits: ['Earlier arrival than delayed direct', 'Business lounge access', 'Priority boarding'],
          cost: 'No additional cost',
          timeToExecute: 'Ready in 2 minutes',
          recommended: true,
          icon: Plane,
          color: 'text-blue-600',
          details: {
            flight: {
              number: 'EI154 + EI105',
              route: 'LHR → DUB → JFK',
              departure: '14:30',
              arrival: '21:45',
              aircraft: 'A321 + A330',
              seatClass: 'Business'
            },
            extras: {
              loungeAccess: true,
              mealVouchers: false,
              wifiCredits: true,
              priorityBoarding: true
            }
          }
        },
        {
          id: 'sol2',
          title: 'Tomorrow Direct + Premium Hotel',
          description: 'Next day direct flight with luxury hotel tonight',
          benefits: ['Direct flight', '5-star hotel near airport', '£200 dining credit', 'Late checkout'],
          cost: '£200 credit applied',
          timeToExecute: 'Hotel booked in 1 minute',
          recommended: false,
          icon: Hotel,
          color: 'text-purple-600',
          details: {
            flight: {
              number: 'BA117',
              route: 'LHR → JFK',
              departure: '10:30',
              arrival: '14:15',
              aircraft: 'B777',
              seatClass: 'Business'
            },
            hotel: {
              name: 'Sofitel London Heathrow',
              rating: 5,
              location: '5 minutes from Terminal 5',
              amenities: ['Spa', 'Fine dining', 'Business center', 'Concierge'],
              rate: 'Complimentary'
            },
            transport: {
              type: 'Hotel shuttle',
              provider: 'Complimentary',
              pickup: 'Terminal 5',
              cost: 'Free'
            },
            compensation: {
              amount: '£200',
              type: 'Dining credit',
              reason: 'Schedule disruption'
            }
          }
        },
        {
          id: 'sol3',
          title: 'Virgin Atlantic Upgrade',
          description: 'Business class on partner airline, same day',
          benefits: ['Business class upgrade', 'Earlier departure', 'Premium service', 'Lounge access'],
          cost: 'Upgrade covered',
          timeToExecute: 'Confirmed in 30 seconds',
          recommended: false,
          icon: Star,
          color: 'text-gold-600',
          details: {
            flight: {
              number: 'VS003',
              route: 'LHR → JFK',
              departure: '11:45',
              arrival: '15:30',
              aircraft: 'A350',
              seatClass: 'Upper Class'
            },
            extras: {
              loungeAccess: true,
              mealVouchers: true,
              wifiCredits: true,
              priorityBoarding: true
            }
          }
        }
      ]
    }
  ]);

  const [passengerProfile] = useState<PassengerProfile>({
    id: 'sarah_chen',
    name: 'Sarah Chen',
    email: 'sarah.chen@techcorp.com',
    phone: '+1-555-0123',
    preferences: {
      seatType: 'Aisle, Extra legroom',
      mealType: 'Vegetarian',
      communicationChannel: 'Push + SMS',
      hotelCategory: 'Business 4-5 star',
      transportType: 'Taxi/Uber preferred'
    },
    loyaltyStatus: 'Gold Executive',
    pastDisruptions: 3,
    satisfaction: 4.8,
    businessProfile: {
      isBusinessTravel: true,
      company: 'TechCorp International',
      meetingTime: 'Tomorrow 9:00 AM',
      colleagues: ['Mike Johnson', 'Lisa Wong']
    }
  });

  // Update current time every second
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Set the first alert as active for demo
  useEffect(() => {
    if (alerts.length > 0) {
      setActiveAlert(alerts[0]);
    }
  }, [alerts]);

  const handleSolutionSelect = (solution: Solution) => {
    setSelectedSolution(solution);
  };

  const handleExecuteSolution = async () => {
    if (!selectedSolution) return;

    setIsExecuting(true);
    
    // Comprehensive service orchestration steps
    const orchestrationSteps = [
      {
        category: 'Flight Rebooking',
        steps: [
          'Connecting to airline reservation system...',
          'Securing seat 12A (aisle, extra legroom) on EI154...',
          'Applying Gold Executive benefits and upgrades...',
          'Transferring meal preference (vegetarian) to new flights...',
          'Rerouting baggage to final destination JFK...',
          'Completing check-in for tomorrow 14:30 departure...',
          'Generating mobile boarding passes for both flights...'
        ]
      },
      {
        category: 'Accommodation Management',
        steps: [
          'Searching hotels near Dublin Airport for tonight...',
          'Booking king bed, high floor at Clayton Hotel Burlington Road...',
          'Activating Hilton Honors benefits (late checkout, wifi)...',
          'Arranging late check-in for 23:45 arrival...',
          'Setting wake-up call for 12:00 PM tomorrow...',
          'Coordinating checkout with morning transport...'
        ]
      },
      {
        category: 'Ground Transportation',
        steps: [
          'Booking airport shuttle from Terminal 5 to hotel...',
          'Arranging return transport: hotel pickup at 13:15...',
          'Optimizing route for traffic and connection time...',
          'Pre-authorizing payment with corporate card ending 4321...',
          'Sending transport details to passenger mobile...',
          'Setting backup transport option in case of delays...'
        ]
      },
      {
        category: 'Meal & Service Management',
        steps: [
          'Activating €40 meal voucher for Dublin layover...',
          'Reserving lounge access: Virgin Clubhouse LHR Terminal 5...',
          'Booking restaurant table at The Conrad Dublin for tonight...',
          'Arranging priority boarding for both connecting flights...',
          'Providing entertainment credit for in-flight wifi...'
        ]
      },
      {
        category: 'Communication Orchestration',
        steps: [
          'Updating Outlook calendar with new flight times...',
          'Notifying colleagues Mike Johnson and Lisa Wong of delay...',
          'Sending revised meeting invitation for 11:00 AM (2 hours later)...',
          'Updating corporate expense report with €340 disruption costs...',
          'Notifying emergency contact of travel change...',
          'Sending comprehensive itinerary to passenger phone...'
        ]
      },
      {
        category: 'Final Confirmation',
        steps: [
          'Verifying all bookings and confirmations...',
          'Testing all mobile boarding passes and voucher codes...',
          'Confirming real-time monitoring for all services...',
          'Activating failure detection and backup systems...',
          'Complete! All services coordinated and confirmed.'
        ]
      }
    ];

    for (const category of orchestrationSteps) {
      for (const step of category.steps) {
        setExecutionStep(`${category.category}: ${step}`);
        await new Promise(resolve => setTimeout(resolve, 1200));
      }
    }

    // Mark as completed
    if (activeAlert) {
      const updatedAlert = {
        ...activeAlert,
        type: 'completed' as const,
        autoActionTaken: selectedSolution.title
      };
      setActiveAlert(updatedAlert);
      setIsExecuting(false);
      setExecutionStep('');
    }
  };

  const getTimeAgo = (date: Date) => {
    const minutes = Math.floor((Date.now() - date.getTime()) / 60000);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    return `${hours}h ago`;
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'border-red-500 bg-red-50';
      case 'medium': return 'border-yellow-500 bg-yellow-50';
      case 'low': return 'border-green-500 bg-green-50';
      default: return 'border-gray-500 bg-gray-50';
    }
  };

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'early_warning': return AlertTriangle;
      case 'solution_ready': return Zap;
      case 'action_needed': return Bell;
      case 'completed': return CheckCircle2;
      default: return Bell;
    }
  };

  if (isExecuting) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-800 to-purple-800 p-6">
        <div className="max-w-2xl mx-auto">
          <div className="bg-white rounded-2xl p-8 shadow-2xl">
            <div className="text-center mb-8">
              <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <Zap className="w-10 h-10 text-blue-600 animate-pulse" />
              </div>
              <h2 className="text-3xl font-bold text-gray-800 mb-2">Service Orchestration in Progress</h2>
              <p className="text-gray-600">Coordinating all aspects of your journey automatically</p>
            </div>

            {/* Progress Indicator */}
            <div className="mb-8">
              <div className="bg-gray-200 rounded-full h-3 mb-4">
                <div className="bg-gradient-to-r from-blue-600 to-purple-600 h-3 rounded-full animate-pulse transition-all duration-1000" style={{ width: '75%' }}></div>
              </div>
              
              {/* Current Step */}
              <div className="bg-blue-50 rounded-xl p-4 border-l-4 border-blue-500">
                <div className="flex items-center space-x-3">
                  <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse"></div>
                  <p className="text-blue-900 font-medium">{executionStep}</p>
                </div>
              </div>
            </div>

            {/* Service Categories */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-8">
              <div className="text-center p-4 bg-green-50 rounded-xl border border-green-200">
                <Plane className="w-6 h-6 text-green-600 mx-auto mb-2" />
                <div className="text-sm font-medium text-green-800">Flight Rebooking</div>
                <div className="text-xs text-green-600">Seat 12A Secured</div>
              </div>
              
              <div className="text-center p-4 bg-purple-50 rounded-xl border border-purple-200">
                <Hotel className="w-6 h-6 text-purple-600 mx-auto mb-2" />
                <div className="text-sm font-medium text-purple-800">Hotel Booking</div>
                <div className="text-xs text-purple-600">King Bed Reserved</div>
              </div>
              
              <div className="text-center p-4 bg-orange-50 rounded-xl border border-orange-200">
                <Car className="w-6 h-6 text-orange-600 mx-auto mb-2" />
                <div className="text-sm font-medium text-orange-800">Transport</div>
                <div className="text-xs text-orange-600">Shuttle Confirmed</div>
              </div>
              
              <div className="text-center p-4 bg-red-50 rounded-xl border border-red-200">
                <Utensils className="w-6 h-6 text-red-600 mx-auto mb-2" />
                <div className="text-sm font-medium text-red-800">Meals & Services</div>
                <div className="text-xs text-red-600">€40 Voucher Active</div>
              </div>
              
              <div className="text-center p-4 bg-blue-50 rounded-xl border border-blue-200">
                <MessageSquare className="w-6 h-6 text-blue-600 mx-auto mb-2" />
                <div className="text-sm font-medium text-blue-800">Communications</div>
                <div className="text-xs text-blue-600">Colleagues Notified</div>
              </div>
              
              <div className="text-center p-4 bg-gray-50 rounded-xl border border-gray-200">
                <Shield className="w-6 h-6 text-gray-600 mx-auto mb-2" />
                <div className="text-sm font-medium text-gray-800">Monitoring</div>
                <div className="text-xs text-gray-600">Real-time Tracking</div>
              </div>
            </div>

            {/* Live Updates */}
            <div className="bg-slate-50 rounded-xl p-4">
              <h4 className="font-semibold text-slate-800 mb-3">🔄 Live Service Updates</h4>
              <div className="space-y-2 text-sm max-h-32 overflow-y-auto">
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600" />
                  <span className="text-slate-700">EI154 seat 12A confirmed with extra legroom</span>
                  <span className="text-xs text-slate-500">Now</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600" />
                  <span className="text-slate-700">Clayton Hotel room upgraded to Executive King</span>
                  <span className="text-xs text-slate-500">5s ago</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600" />
                  <span className="text-slate-700">Virgin Clubhouse access activated until 15:30</span>
                  <span className="text-xs text-slate-500">12s ago</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600" />
                  <span className="text-slate-700">Meeting moved to 11:00 AM, attendees confirmed</span>
                  <span className="text-xs text-slate-500">18s ago</span>
                </div>
              </div>
            </div>

            <div className="text-center mt-6">
              <p className="text-sm text-gray-500">
                🤖 AI orchestrating 6 service categories across 15+ vendors
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!activeAlert) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 flex items-center justify-center p-6">
        <div className="text-center">
          <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle2 className="w-10 h-10 text-green-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-800 mb-4">All Systems Running Smoothly</h2>
          <p className="text-gray-600">No disruptions detected. We're monitoring your journey 24/7.</p>
        </div>
      </div>
    );
  }

  if (activeAlert.type === 'completed') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-900 via-green-800 to-blue-800 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-2xl p-8 shadow-2xl">
            <div className="text-center mb-8">
              <div className="w-24 h-24 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <CheckCircle2 className="w-12 h-12 text-green-600" />
              </div>
              <h2 className="text-4xl font-bold text-gray-800 mb-4">All Set, {passengerProfile.name}! ✈️</h2>
              <p className="text-lg text-gray-600 mb-2">
                We've executed "<span className="font-semibold text-blue-600">{activeAlert.autoActionTaken}</span>" 
                for your {activeAlert.flightNumber} {activeAlert.route} journey.
              </p>
              <p className="text-sm text-gray-500">
                All 6 service categories coordinated across 15+ vendors automatically
              </p>
            </div>

            {/* Service Orchestration Results */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
              {/* Flight Rebooking */}
              <div className="bg-blue-50 rounded-xl p-6 border border-blue-200">
                <div className="flex items-center space-x-3 mb-4">
                  <Plane className="w-8 h-8 text-blue-600" />
                  <h3 className="font-bold text-blue-800">Flight Rebooking</h3>
                </div>
                <div className="space-y-2 text-sm text-blue-700">
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>EI154 + EI105 via Dublin confirmed</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Seat 12A (aisle, extra legroom) secured</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Vegetarian meals transferred to both flights</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Mobile boarding passes generated</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Baggage rerouted to JFK automatically</span>
                  </div>
                </div>
              </div>

              {/* Accommodation */}
              <div className="bg-purple-50 rounded-xl p-6 border border-purple-200">
                <div className="flex items-center space-x-3 mb-4">
                  <Hotel className="w-8 h-8 text-purple-600" />
                  <h3 className="font-bold text-purple-800">Hotel & Accommodation</h3>
                </div>
                <div className="space-y-2 text-sm text-purple-700">
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Clayton Hotel Burlington Road booked</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Executive King room (high floor)</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Late check-in arranged (23:45)</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Wake-up call set for 12:00 PM</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Hilton Honors benefits activated</span>
                  </div>
                </div>
              </div>

              {/* Ground Transport */}
              <div className="bg-orange-50 rounded-xl p-6 border border-orange-200">
                <div className="flex items-center space-x-3 mb-4">
                  <Car className="w-8 h-8 text-orange-600" />
                  <h3 className="font-bold text-orange-800">Ground Transportation</h3>
                </div>
                <div className="space-y-2 text-sm text-orange-700">
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Airport shuttle to hotel booked</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Return pickup: 13:15 hotel lobby</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Route optimized for traffic patterns</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Corporate card pre-authorized</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Backup transport option secured</span>
                  </div>
                </div>
              </div>

              {/* Meals & Services */}
              <div className="bg-red-50 rounded-xl p-6 border border-red-200">
                <div className="flex items-center space-x-3 mb-4">
                  <Utensils className="w-8 h-8 text-red-600" />
                  <h3 className="font-bold text-red-800">Meals & Services</h3>
                </div>
                <div className="space-y-2 text-sm text-red-700">
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>€40 meal voucher activated for Dublin</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Virgin Clubhouse LHR access (3 hours)</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>The Conrad Dublin table reserved</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Priority boarding both flights</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>In-flight wifi credits provided</span>
                  </div>
                </div>
              </div>

              {/* Communication */}
              <div className="bg-green-50 rounded-xl p-6 border border-green-200">
                <div className="flex items-center space-x-3 mb-4">
                  <MessageSquare className="w-8 h-8 text-green-600" />
                  <h3 className="font-bold text-green-800">Communication</h3>
                </div>
                <div className="space-y-2 text-sm text-green-700">
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Outlook calendar updated automatically</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Mike Johnson & Lisa Wong notified</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Meeting rescheduled to 11:00 AM</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Emergency contact informed</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Complete itinerary sent to phone</span>
                  </div>
                </div>
              </div>

              {/* Monitoring & Support */}
              <div className="bg-slate-50 rounded-xl p-6 border border-slate-200">
                <div className="flex items-center space-x-3 mb-4">
                  <Shield className="w-8 h-8 text-slate-600" />
                  <h3 className="font-bold text-slate-800">Monitoring & Support</h3>
                </div>
                <div className="space-y-2 text-sm text-slate-700">
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Real-time service monitoring active</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Failure detection systems enabled</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Backup services pre-arranged</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>24/7 support escalation ready</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Expense report updated (€340)</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Key Metrics */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              <div className="text-center p-4 bg-blue-50 rounded-xl border border-blue-200">
                <Clock className="w-6 h-6 text-blue-600 mx-auto mb-2" />
                <div className="font-bold text-2xl text-blue-800">2m 14s</div>
                <div className="text-sm text-blue-600">Total Resolution Time</div>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-xl border border-green-200">
                <CheckCircle2 className="w-6 h-6 text-green-600 mx-auto mb-2" />
                <div className="font-bold text-2xl text-green-800">31</div>
                <div className="text-sm text-green-600">Services Coordinated</div>
              </div>
              <div className="text-center p-4 bg-purple-50 rounded-xl border border-purple-200">
                <Users className="w-6 h-6 text-purple-600 mx-auto mb-2" />
                <div className="font-bold text-2xl text-purple-800">0</div>
                <div className="text-sm text-purple-600">Human Interventions</div>
              </div>
              <div className="text-center p-4 bg-red-50 rounded-xl border border-red-200">
                <Heart className="w-6 h-6 text-red-600 mx-auto mb-2" />
                <div className="font-bold text-2xl text-red-800">0</div>
                <div className="text-sm text-red-600">Passenger Stress</div>
              </div>
            </div>

            {/* Final Message */}
            <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-xl p-6 text-center">
              <h3 className="font-bold text-gray-800 mb-2">🎯 Service Orchestration Complete</h3>
              <p className="text-gray-600 mb-4">
                No queues, no phone calls, no management required. Your disruption has been transformed into a premium service experience.
              </p>
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <button 
                  className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-xl transition-colors"
                  onClick={() => window.location.reload()}
                >
                  View Complete Journey Details
                </button>
                <button 
                  className="bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-6 rounded-xl transition-colors"
                  onClick={() => window.location.reload()}
                >
                  Start New Demo
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const AlertIcon = getAlertIcon(activeAlert.type);

  return (
    <div className="min-h-screen bg-gradient-to-br from-rose-950 via-purple-950 to-indigo-950">
      {/* Header */}
      <div className="bg-gradient-to-r from-rose-600/90 via-pink-600/90 to-purple-600/90 backdrop-blur-xl border-b border-pink-400/30 shadow-2xl">
        <div className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="relative">
                <div className="w-4 h-4 bg-pink-400 rounded-full animate-pulse shadow-lg shadow-pink-400/50"></div>
                <div className="w-4 h-4 bg-pink-400 rounded-full animate-ping absolute top-0 left-0 opacity-30"></div>
              </div>
              <div>
                <h1 className="text-white font-bold text-2xl tracking-wide">✨ Proactive Travel Assistant</h1>
                <p className="text-pink-100 text-sm font-medium">AI-Powered Journey Intelligence</p>
              </div>
            </div>
            <div className="bg-black/20 backdrop-blur-sm rounded-2xl px-4 py-3 border border-pink-300/20">
              <div className="text-pink-200 text-sm font-medium">Live Time</div>
              <div className="text-white text-lg font-mono font-bold">
                {currentTime.toLocaleTimeString()}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="p-8 max-w-5xl mx-auto">
        {/* Alert Card */}
        <div className="bg-white/10 backdrop-blur-2xl rounded-3xl border border-white/20 shadow-2xl hover:shadow-pink-500/10 transition-all duration-500 mb-8">
          <div className="p-8">
            {/* Alert Header */}
            <div className="flex items-start justify-between mb-8">
              <div className="flex items-center space-x-4">
                <div className="p-4 bg-gradient-to-r from-pink-500/20 to-rose-500/20 rounded-2xl border border-pink-400/30">
                  <AlertIcon className="w-8 h-8 text-pink-400" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-white tracking-wide">{activeAlert.title}</h2>
                  <p className="text-sm text-pink-300 font-medium">{getTimeAgo(activeAlert.timestamp)}</p>
                </div>
              </div>
              <div className="text-right bg-white/10 backdrop-blur-sm rounded-2xl px-6 py-4 border border-white/20">
                <div className="text-3xl font-bold text-white bg-gradient-to-r from-pink-400 to-rose-400 bg-clip-text text-transparent">{activeAlert.confidence}%</div>
                <div className="text-sm text-pink-300 font-medium">Confidence</div>
              </div>
            </div>

            {/* Personal Message */}
            <div className="bg-gradient-to-r from-cyan-500/10 to-blue-500/10 backdrop-blur-sm rounded-2xl p-6 mb-8 border border-cyan-400/20">
              <p className="text-white text-lg leading-relaxed">
                <span className="font-bold text-cyan-400">Hi {activeAlert.passengerName},</span> we've detected potential delays 
                for your <span className="font-bold text-purple-400">{activeAlert.flightNumber}</span> {activeAlert.route} flight due to weather. 
                <br/><br/>
                <span className="font-bold text-pink-400 text-xl">We've already secured 3 options for you - choose what works best:</span>
              </p>
            </div>

            {/* Solutions */}
            <div className="space-y-6 mb-8">
              {activeAlert.solutions?.map((solution) => (
                <div 
                  key={solution.id}
                  className={`bg-white/5 backdrop-blur-xl rounded-3xl p-6 cursor-pointer transition-all duration-300 hover:shadow-2xl border ${
                    selectedSolution?.id === solution.id 
                      ? 'border-cyan-400/50 bg-cyan-500/10 shadow-2xl shadow-cyan-500/20' 
                      : solution.recommended 
                        ? 'border-emerald-400/50 bg-emerald-500/10 hover:border-emerald-400/70 hover:shadow-emerald-500/10' 
                        : 'border-white/20 hover:border-white/40 hover:bg-white/10'
                  }`}
                  onClick={() => handleSolutionSelect(solution)}
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center space-x-4">
                      <div className={`p-3 rounded-2xl border ${
                        solution.color.includes('blue') ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border-cyan-400/30' :
                        solution.color.includes('purple') ? 'bg-gradient-to-r from-violet-500/20 to-purple-500/20 border-violet-400/30' :
                        'bg-gradient-to-r from-amber-500/20 to-yellow-500/20 border-amber-400/30'
                      }`}>
                        <solution.icon className={`w-7 h-7 ${
                          solution.color.includes('blue') ? 'text-cyan-400' :
                          solution.color.includes('purple') ? 'text-violet-400' :
                          'text-amber-400'
                        }`} />
                      </div>
                      <div>
                        <h3 className="font-bold text-white text-xl mb-1">{solution.title}</h3>
                        {solution.recommended && (
                          <span className="inline-flex items-center px-3 py-1 text-xs font-bold bg-gradient-to-r from-emerald-500/20 to-green-500/20 text-emerald-400 rounded-full border border-emerald-400/30">
                            ⭐ Recommended
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="text-right bg-white/10 backdrop-blur-sm rounded-2xl px-4 py-3 border border-white/20">
                      <div className="font-bold text-white text-lg">{solution.cost}</div>
                      <div className="text-sm text-slate-300 font-medium">{solution.timeToExecute}</div>
                    </div>
                  </div>
                  
                  <p className="text-slate-200 mb-4 text-lg leading-relaxed">{solution.description}</p>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {solution.benefits.slice(0, 4).map((benefit, idx) => (
                      <div key={idx} className="flex items-center space-x-2 bg-white/5 backdrop-blur-sm rounded-xl p-2 border border-white/10">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                        <span className="text-sm text-white font-medium">{benefit}</span>
                      </div>
                    ))}
                  </div>

                  {/* Detailed breakdown for selected solution */}
                  {selectedSolution?.id === solution.id && (
                    <div className="mt-4 pt-4 border-t border-blue-200">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                        {solution.details.flight && (
                          <div className="bg-white rounded-lg p-3">
                            <h4 className="font-semibold text-blue-800 mb-2">✈️ Flight Details</h4>
                            <div className="space-y-1 text-gray-700">
                              <div>Flight: {solution.details.flight.number}</div>
                              <div>Route: {solution.details.flight.route}</div>
                              <div>Departure: {solution.details.flight.departure}</div>
                              <div>Class: {solution.details.flight.seatClass}</div>
                            </div>
                          </div>
                        )}
                        
                        {solution.details.hotel && (
                          <div className="bg-white rounded-lg p-3">
                            <h4 className="font-semibold text-purple-800 mb-2">🏨 Hotel Details</h4>
                            <div className="space-y-1 text-gray-700">
                              <div>Hotel: {solution.details.hotel.name}</div>
                              <div>Rating: {'⭐'.repeat(solution.details.hotel.rating)}</div>
                              <div>Location: {solution.details.hotel.location}</div>
                              <div>Rate: {solution.details.hotel.rate}</div>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-4">
              <button
                onClick={handleExecuteSolution}
                disabled={!selectedSolution}
                className={`flex-1 py-5 px-8 rounded-2xl font-bold transition-all duration-300 ${
                  selectedSolution
                    ? 'bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white shadow-2xl hover:shadow-cyan-500/30 border border-cyan-400/30'
                    : 'bg-white/10 text-slate-500 cursor-not-allowed border border-white/20'
                }`}
              >
                {selectedSolution ? (
                  <div className="flex items-center justify-center space-x-3">
                    <Zap className="w-6 h-6" />
                    <span className="text-lg">Execute Solution</span>
                    <ArrowRight className="w-6 h-6" />
                  </div>
                ) : (
                  <span className="text-lg">Select an option above</span>
                )}
              </button>
              
              <button className="px-8 py-5 bg-white/10 backdrop-blur-sm border-2 border-white/20 rounded-2xl text-white font-bold hover:bg-white/20 hover:border-white/40 transition-all duration-300">
                <div className="flex items-center justify-center space-x-3">
                  <Phone className="w-6 h-6" />
                  <span className="text-lg">Call Me</span>
                </div>
              </button>
            </div>
          </div>
        </div>

        {/* Passenger Info */}
        <div className="bg-white/5 backdrop-blur-2xl rounded-3xl border border-white/10 shadow-2xl p-6">
          <h3 className="font-bold text-white text-xl mb-6 flex items-center space-x-3">
            <div className="p-2 bg-gradient-to-r from-violet-500/20 to-purple-500/20 rounded-xl border border-violet-400/30">
              <Users className="w-6 h-6 text-violet-400" />
            </div>
            <span>Your Profile & Preferences</span>
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-4 border border-cyan-400/20 hover:border-cyan-400/40 transition-all duration-300">
                <div className="font-bold text-cyan-400 text-lg mb-1">{passengerProfile.loyaltyStatus}</div>
                <div className="text-slate-300 text-sm font-medium">Status</div>
              </div>
            </div>
            <div className="text-center">
              <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-4 border border-emerald-400/20 hover:border-emerald-400/40 transition-all duration-300">
                <div className="font-bold text-emerald-400 text-lg mb-1">{passengerProfile.satisfaction}/5</div>
                <div className="text-slate-300 text-sm font-medium">Satisfaction</div>
              </div>
            </div>
            <div className="text-center">
              <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-4 border border-amber-400/20 hover:border-amber-400/40 transition-all duration-300">
                <div className="font-bold text-amber-400 text-lg mb-1">{passengerProfile.businessProfile.meetingTime}</div>
                <div className="text-slate-300 text-sm font-medium">Meeting</div>
              </div>
            </div>
            <div className="text-center">
              <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-4 border border-violet-400/20 hover:border-violet-400/40 transition-all duration-300">
                <div className="font-bold text-violet-400 text-lg mb-1">{passengerProfile.preferences.communicationChannel}</div>
                <div className="text-slate-300 text-sm font-medium">Communication</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}