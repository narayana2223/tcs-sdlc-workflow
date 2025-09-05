import { PassengerPersona, Flight, Passenger, Notification, RebookingOption, TravelAssistance, Compensation } from '@/types';

export const demoPersonas: PassengerPersona[] = [
  {
    id: 'business-exec',
    name: 'Sarah Chen - Business Executive',
    description: 'Frequent business traveler who values time and efficiency',
    avatar: '👩‍💼',
    scenario: 'Cancelled international flight with important meeting',
    passenger: {
      id: 'passenger-1',
      pnr: 'ABC123',
      firstName: 'Sarah',
      lastName: 'Chen',
      email: 'sarah.chen@company.com',
      phone: '+44 7700 123456',
      tier: 'business',
      frequentFlyer: 'BA123456789',
      preferences: {
        seatType: 'aisle',
        mealType: 'standard',
        notifications: ['email', 'sms', 'push'],
        timePreference: 'morning',
      },
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
      reason: 'Aircraft technical issue',
    },
    mockData: {
      notifications: [
        {
          id: 'notif-1',
          type: 'error',
          title: 'Flight BA123 Cancelled',
          message: 'We sincerely apologize for the cancellation of your flight BA123 due to a technical issue. Our AI system has automatically found alternative options for you.',
          timestamp: new Date(Date.now() - 300000),
          read: false,
          actionRequired: true,
          actions: [
            { id: 'view-options', label: 'View Alternatives', type: 'primary', action: 'rebooking' },
            { id: 'contact-us', label: 'Contact Us', type: 'secondary', action: 'support' }
          ],
        },
        {
          id: 'notif-2',
          type: 'success',
          title: 'Compensation Automatically Approved',
          message: 'Your EU261 compensation of €600 has been automatically approved and will be processed within 7 days.',
          timestamp: new Date(Date.now() - 600000),
          read: false,
          actionRequired: false,
        },
        {
          id: 'notif-3',
          type: 'info',
          title: 'Hotel Voucher Available',
          message: 'Due to the overnight delay, we\'ve arranged complimentary accommodation at the Hilton Heathrow.',
          timestamp: new Date(Date.now() - 900000),
          read: true,
          actionRequired: false,
          actions: [
            { id: 'use-voucher', label: 'Use Voucher', type: 'primary', action: 'assistance' }
          ],
        }
      ],
      rebookingOptions: [
        {
          id: 'option-1',
          flightNumber: 'BA177',
          airline: 'British Airways',
          route: 'LHR → JFK',
          departureTime: new Date('2024-01-15T14:00:00Z'),
          arrivalTime: new Date('2024-01-15T22:30:00Z'),
          duration: '8h 30m',
          stops: 0,
          aircraft: 'Boeing 787-9',
          availableSeats: { economy: 45, premium: 12, business: 8, first: 4 },
          price: { economy: 0, premium: 150, business: 0, first: 500 },
          recommended: true,
          reason: 'Same aircraft type, maintains your business class seat, minimal delay impact',
          amenities: ['wifi', 'meal', 'entertainment', 'lounge'],
        },
        {
          id: 'option-2',
          flightNumber: 'VS003',
          airline: 'Virgin Atlantic',
          route: 'LHR → JFK',
          departureTime: new Date('2024-01-15T11:30:00Z'),
          arrivalTime: new Date('2024-01-15T19:45:00Z'),
          duration: '8h 15m',
          stops: 0,
          aircraft: 'Airbus A350-1000',
          availableSeats: { economy: 23, premium: 8, business: 3, first: 0 },
          price: { economy: 0, premium: 100, business: 0, first: 0 },
          recommended: false,
          amenities: ['wifi', 'meal', 'entertainment'],
        }
      ],
      assistance: [
        {
          id: 'hotel-1',
          type: 'hotel',
          title: 'Hilton London Heathrow',
          description: 'Connected to Terminal 4, luxury business hotel with full amenities',
          provider: 'Hilton Hotels',
          location: 'Heathrow Airport',
          price: 0,
          rating: 4.5,
          amenities: ['Free WiFi', 'Business Center', 'Fitness Center', 'Restaurant', 'Bar'],
          available: true,
          voucherCode: 'HLH-COMP-789',
        },
        {
          id: 'transport-1',
          type: 'transport',
          title: 'Executive Car Service',
          description: 'Door-to-door luxury car service to your destination or accommodation',
          provider: 'ExecCars',
          location: 'London',
          price: 0,
          rating: 4.8,
          amenities: ['WiFi', 'Phone Chargers', 'Refreshments', 'Professional Driver'],
          available: true,
          voucherCode: 'EXEC-COMP-456',
        }
      ],
      compensation: [
        {
          id: 'comp-1',
          flightId: 'flight-1',
          type: 'eu261',
          amount: 600,
          currency: 'EUR',
          reason: 'Flight cancellation compensation under EU261 regulation',
          status: 'approved',
          claimDate: new Date(Date.now() - 600000),
          processedDate: new Date(Date.now() - 300000),
          reference: 'EU261-BA123-20240115',
        }
      ],
    },
  },
  {
    id: 'family-vacation',
    name: 'The Johnson Family',
    description: 'Family of four traveling for vacation with children',
    avatar: '👨‍👩‍👧‍👦',
    scenario: 'Delayed vacation flight with connecting flights at risk',
    passenger: {
      id: 'passenger-2',
      pnr: 'FAM456',
      firstName: 'David',
      lastName: 'Johnson',
      email: 'david.johnson@gmail.com',
      phone: '+44 7700 987654',
      tier: 'economy',
      preferences: {
        seatType: 'any',
        mealType: 'standard',
        notifications: ['email', 'push'],
        timePreference: 'any',
      },
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
      delay: 300, // 5 hours
      seat: '15A-15D',
      aircraft: 'Airbus A320',
      reason: 'Air traffic control restrictions due to fog',
    },
    mockData: {
      notifications: [
        {
          id: 'notif-f1',
          type: 'warning',
          title: 'Flight EZY892 Delayed',
          message: 'Your family flight has been delayed by 5 hours due to weather conditions. We\'ve automatically rearranged your connecting flights.',
          timestamp: new Date(Date.now() - 180000),
          read: false,
          actionRequired: true,
          actions: [
            { id: 'view-new-itinerary', label: 'View New Itinerary', type: 'primary', action: 'rebooking' },
            { id: 'meal-vouchers', label: 'Get Meal Vouchers', type: 'secondary', action: 'assistance' }
          ],
        }
      ],
      rebookingOptions: [
        {
          id: 'option-f1',
          flightNumber: 'EZY894',
          airline: 'easyJet',
          route: 'LGW → BCN',
          departureTime: new Date('2024-01-15T16:00:00Z'),
          arrivalTime: new Date('2024-01-15T19:15:00Z'),
          duration: '2h 15m',
          stops: 0,
          aircraft: 'Airbus A320',
          availableSeats: { economy: 56, premium: 0, business: 0, first: 0 },
          price: { economy: 0, premium: 0, business: 0, first: 0 },
          recommended: true,
          reason: 'Later flight with guaranteed seats for your family of 4',
          amenities: ['meal'],
        }
      ],
      assistance: [
        {
          id: 'meal-1',
          type: 'meal',
          title: 'Family Meal Vouchers',
          description: '£60 meal vouchers for family of 4 at airport restaurants',
          provider: 'Gatwick Airport',
          location: 'Gatwick South Terminal',
          price: 0,
          rating: 4.0,
          amenities: ['Valid at all terminal restaurants', 'Kids meals included'],
          available: true,
          voucherCode: 'MEAL-FAM-123',
        }
      ],
      compensation: [],
    },
  },
  {
    id: 'budget-student',
    name: 'Alex Rivera - Student',
    description: 'Budget-conscious student traveling home for holidays',
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
      preferences: {
        seatType: 'any',
        mealType: 'vegetarian',
        notifications: ['email'],
        timePreference: 'any',
      },
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
      reason: 'Crew scheduling issues',
    },
    mockData: {
      notifications: [
        {
          id: 'notif-s1',
          type: 'error',
          title: 'Flight FR456 Cancelled',
          message: 'Your flight has been cancelled due to operational reasons. We\'ve found budget-friendly alternatives for you.',
          timestamp: new Date(Date.now() - 240000),
          read: false,
          actionRequired: true,
          actions: [
            { id: 'view-budget-options', label: 'View Alternatives', type: 'primary', action: 'rebooking' }
          ],
        }
      ],
      rebookingOptions: [
        {
          id: 'option-s1',
          flightNumber: 'U23478',
          airline: 'easyJet',
          route: 'LGW → MAD',
          departureTime: new Date('2024-01-15T14:30:00Z'),
          arrivalTime: new Date('2024-01-15T18:00:00Z'),
          duration: '2h 30m',
          stops: 0,
          aircraft: 'Airbus A319',
          availableSeats: { economy: 78, premium: 0, business: 0, first: 0 },
          price: { economy: 0, premium: 0, business: 0, first: 0 },
          recommended: true,
          reason: 'No extra cost, departs from London area',
          amenities: ['meal purchase available'],
        }
      ],
      assistance: [],
      compensation: [
        {
          id: 'comp-s1',
          flightId: 'flight-3',
          type: 'eu261',
          amount: 250,
          currency: 'EUR',
          reason: 'Short-haul flight cancellation compensation',
          status: 'pending',
          claimDate: new Date(Date.now() - 120000),
          reference: 'EU261-FR456-20240115',
        }
      ],
    },
  },
];

export const getPersonaById = (id: string): PassengerPersona | null => {
  return demoPersonas.find(persona => persona.id === id) || null;
};

export const getDefaultPersona = (): PassengerPersona => {
  return demoPersonas[0]; // Business executive by default
};