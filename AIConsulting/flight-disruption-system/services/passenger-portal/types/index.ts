export interface Passenger {
  id: string;
  pnr: string;
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  tier: 'economy' | 'premium' | 'business' | 'first';
  frequentFlyer?: string;
  preferences: {
    seatType: 'aisle' | 'window' | 'any';
    mealType: 'standard' | 'vegetarian' | 'vegan' | 'halal' | 'kosher';
    notifications: ('email' | 'sms' | 'push')[];
    timePreference: 'morning' | 'afternoon' | 'evening' | 'any';
  };
}

export interface Flight {
  id: string;
  flightNumber: string;
  airline: string;
  departureAirport: string;
  arrivalAirport: string;
  departureTerminal?: string;
  arrivalTerminal?: string;
  scheduledDeparture: Date;
  scheduledArrival: Date;
  estimatedDeparture: Date;
  estimatedArrival: Date;
  actualDeparture?: Date;
  actualArrival?: Date;
  status: 'scheduled' | 'delayed' | 'cancelled' | 'boarding' | 'departed' | 'arrived';
  gate?: string;
  seat?: string;
  aircraft?: string;
  delay?: number; // in minutes
  reason?: string;
}

export interface RebookingOption {
  id: string;
  flightNumber: string;
  airline: string;
  route: string;
  departureTime: Date;
  arrivalTime: Date;
  duration: string;
  stops: number;
  aircraft: string;
  availableSeats: {
    economy: number;
    premium: number;
    business: number;
    first: number;
  };
  price: {
    economy: number;
    premium: number;
    business: number;
    first: number;
  };
  recommended: boolean;
  reason?: string;
  amenities: string[];
}

export interface Notification {
  id: string;
  type: 'info' | 'warning' | 'success' | 'error' | 'update';
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
  actionRequired: boolean;
  actions?: NotificationAction[];
  relatedFlightId?: string;
}

export interface NotificationAction {
  id: string;
  label: string;
  type: 'primary' | 'secondary';
  action: string;
}

export interface TravelAssistance {
  id: string;
  type: 'hotel' | 'transport' | 'meal' | 'lounge';
  title: string;
  description: string;
  provider: string;
  location: string;
  price: number;
  rating: number;
  amenities: string[];
  available: boolean;
  bookingUrl?: string;
  voucherCode?: string;
}

export interface Compensation {
  id: string;
  flightId: string;
  type: 'eu261' | 'goodwill' | 'refund';
  amount: number;
  currency: string;
  reason: string;
  status: 'pending' | 'approved' | 'paid' | 'rejected';
  claimDate: Date;
  processedDate?: Date;
  reference: string;
}

export interface FeedbackSubmission {
  id: string;
  rating: number;
  category: 'rebooking' | 'communication' | 'assistance' | 'overall';
  comments?: string;
  timestamp: Date;
  flightId?: string;
  anonymous: boolean;
}

export interface PassengerSession {
  passenger: Passenger;
  currentFlight?: Flight;
  upcomingFlights: Flight[];
  notifications: Notification[];
  rebookingOptions: RebookingOption[];
  assistance: TravelAssistance[];
  compensation: Compensation[];
  isConnected: boolean;
  lastUpdated: Date;
}

// Demo passenger personas for CXO presentations
export interface PassengerPersona {
  id: string;
  name: string;
  description: string;
  avatar: string;
  scenario: string;
  passenger: Passenger;
  mockFlight: Flight;
  mockData: {
    notifications: Notification[];
    rebookingOptions: RebookingOption[];
    assistance: TravelAssistance[];
    compensation: Compensation[];
  };
}