'use client';

import React, { useState, useEffect } from 'react';
import { RebookingOption, Passenger, Flight } from '@/types';
import { 
  Sparkles, 
  Clock, 
  Plane, 
  Star,
  CheckCircle, 
  Users, 
  Wifi,
  Coffee,
  Utensils,
  MapPin,
  ArrowRight,
  Filter,
  SortAsc
} from 'lucide-react';

interface RebookingPortalProps {
  originalFlight: Flight;
  passenger: Passenger;
  rebookingOptions: RebookingOption[];
  onSelectOption: (option: RebookingOption) => void;
  onConfirmBooking: (optionId: string, seatClass: string) => void;
  loading?: boolean;
}

export default function RebookingPortal({ 
  originalFlight,
  passenger,
  rebookingOptions,
  onSelectOption,
  onConfirmBooking,
  loading = false
}: RebookingPortalProps) {
  const [selectedOption, setSelectedOption] = useState<RebookingOption | null>(null);
  const [selectedClass, setSelectedClass] = useState<string>('economy');
  const [sortBy, setSortBy] = useState<'recommended' | 'time' | 'price'>('recommended');
  const [showFilters, setShowFilters] = useState(false);
  const [confirming, setConfirming] = useState(false);

  useEffect(() => {
    // Auto-select recommended option
    const recommended = rebookingOptions.find(option => option.recommended);
    if (recommended && !selectedOption) {
      setSelectedOption(recommended);
    }
  }, [rebookingOptions, selectedOption]);

  const formatTime = (date: Date) => {
    return new Intl.DateTimeFormat('en-GB', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    }).format(date);
  };

  const formatDate = (date: Date) => {
    return new Intl.DateTimeFormat('en-GB', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
    }).format(date);
  };

  const getDurationText = (duration: string) => {
    // Assuming duration is in format "2h 30m"
    return duration;
  };

  const getStopsText = (stops: number) => {
    if (stops === 0) return 'Direct';
    return `${stops} stop${stops > 1 ? 's' : ''}`;
  };

  const getSeatAvailability = (option: RebookingOption, seatClass: string) => {
    const classKey = seatClass as keyof typeof option.availableSeats;
    return option.availableSeats[classKey];
  };

  const getSeatPrice = (option: RebookingOption, seatClass: string) => {
    const classKey = seatClass as keyof typeof option.price;
    return option.price[classKey];
  };

  const handleConfirmBooking = async () => {
    if (!selectedOption) return;
    
    setConfirming(true);
    
    // Simulate API call
    setTimeout(() => {
      onConfirmBooking(selectedOption.id, selectedClass);
      setConfirming(false);
    }, 2000);
  };

  const sortedOptions = [...rebookingOptions].sort((a, b) => {
    switch (sortBy) {
      case 'recommended':
        return b.recommended ? 1 : -1;
      case 'time':
        return a.departureTime.getTime() - b.departureTime.getTime();
      case 'price':
        return a.price.economy - b.price.economy;
      default:
        return 0;
    }
  });

  const OptionCard = ({ option }: { option: RebookingOption }) => {
    const isSelected = selectedOption?.id === option.id;
    const seatAvailable = getSeatAvailability(option, selectedClass) > 0;
    const price = getSeatPrice(option, selectedClass);
    
    return (
      <div
        className={`card cursor-pointer transition-all duration-200 ${
          isSelected 
            ? 'ring-2 ring-primary-500 bg-primary-50' 
            : 'hover:shadow-md hover:scale-[1.01]'
        } ${!seatAvailable ? 'opacity-60' : ''}`}
        onClick={() => seatAvailable && setSelectedOption(option)}
      >
        {/* Recommended Badge */}
        {option.recommended && (
          <div className="absolute -top-2 -right-2 bg-success-500 text-white px-2 py-1 rounded-full text-xs font-medium flex items-center">
            <Sparkles className="w-3 h-3 mr-1" />
            AI Recommended
          </div>
        )}

        <div className="relative">
          {/* Flight Header */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-primary-100 rounded-lg">
                <Plane className="w-5 h-5 text-primary-600" />
              </div>
              <div>
                <div className="font-semibold text-slate-800">
                  {option.flightNumber}
                </div>
                <div className="text-sm text-slate-600">
                  {option.airline}
                </div>
              </div>
            </div>
            
            <div className="text-right">
              <div className="text-lg font-bold text-success-600">
                £{price}
              </div>
              <div className="text-xs text-slate-500">
                {selectedClass}
              </div>
            </div>
          </div>

          {/* Route and Time */}
          <div className="grid grid-cols-3 gap-2 mb-4">
            <div className="text-center">
              <div className="text-xl font-bold text-slate-800">
                {formatTime(option.departureTime)}
              </div>
              <div className="text-xs text-slate-600">
                {formatDate(option.departureTime)}
              </div>
            </div>
            
            <div className="flex flex-col items-center justify-center">
              <div className="flex items-center w-full mb-1">
                <div className="flex-1 h-0.5 bg-slate-300"></div>
                <ArrowRight className="w-4 h-4 text-slate-500 mx-1" />
                <div className="flex-1 h-0.5 bg-slate-300"></div>
              </div>
              <div className="text-xs text-slate-500">
                {getDurationText(option.duration)}
              </div>
              <div className="text-xs text-slate-500">
                {getStopsText(option.stops)}
              </div>
            </div>
            
            <div className="text-center">
              <div className="text-xl font-bold text-slate-800">
                {formatTime(option.arrivalTime)}
              </div>
              <div className="text-xs text-slate-600">
                {formatDate(option.arrivalTime)}
              </div>
            </div>
          </div>

          {/* Aircraft and Amenities */}
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center space-x-4">
              <span className="text-slate-600">{option.aircraft}</span>
              <div className="flex items-center space-x-2">
                {option.amenities.includes('wifi') && <Wifi className="w-4 h-4 text-primary-500" />}
                {option.amenities.includes('meal') && <Utensils className="w-4 h-4 text-primary-500" />}
                {option.amenities.includes('entertainment') && <Coffee className="w-4 h-4 text-primary-500" />}
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <Users className="w-4 h-4 text-slate-500" />
              <span className="text-slate-600">
                {getSeatAvailability(option, selectedClass)} seats
              </span>
            </div>
          </div>

          {/* AI Recommendation Reason */}
          {option.recommended && option.reason && (
            <div className="mt-3 p-3 bg-success-50 rounded-lg border border-success-200">
              <div className="flex items-start space-x-2">
                <Sparkles className="w-4 h-4 text-success-600 flex-shrink-0 mt-0.5" />
                <div>
                  <div className="text-sm font-medium text-success-800 mb-1">
                    Why we recommend this flight:
                  </div>
                  <div className="text-sm text-success-700">
                    {option.reason}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Unavailable overlay */}
          {!seatAvailable && (
            <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center rounded-lg">
              <div className="text-center">
                <div className="text-sm font-medium text-slate-800">
                  Not available in {selectedClass}
                </div>
                <div className="text-xs text-slate-600">
                  Try a different class
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="mobile-container">
        <div className="text-center py-12">
          <div className="loading-dots text-primary-500 mb-4">
            <div className="loading-dot"></div>
            <div className="loading-dot" style={{ animationDelay: '0.1s' }}></div>
            <div className="loading-dot" style={{ animationDelay: '0.2s' }}></div>
          </div>
          <p className="text-slate-600">Finding the best options for you...</p>
          <p className="text-sm text-slate-500 mt-2">
            AI is analyzing {rebookingOptions.length} available flights
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="mobile-container">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-responsive-2xl font-bold text-slate-800 mb-2">
          Alternative Flights
        </h1>
        <p className="text-slate-600">
          AI-powered recommendations based on your preferences
        </p>
      </div>

      {/* Original Flight Info */}
      <div className="card bg-slate-50 border-slate-300 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm text-slate-600 mb-1">Original Flight</div>
            <div className="font-semibold text-slate-800">
              {originalFlight.flightNumber} • {originalFlight.departureAirport} → {originalFlight.arrivalAirport}
            </div>
            <div className="text-sm text-slate-600">
              {formatDate(originalFlight.scheduledDeparture)} • {formatTime(originalFlight.scheduledDeparture)}
            </div>
          </div>
          <div className="flight-status flight-status-cancelled">
            {originalFlight.status}
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between mb-6">
        {/* Class Selection */}
        <div className="flex items-center space-x-2">
          <span className="text-sm font-medium text-slate-700">Class:</span>
          <select
            value={selectedClass}
            onChange={(e) => setSelectedClass(e.target.value)}
            className="px-3 py-1 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="economy">Economy</option>
            <option value="premium">Premium Economy</option>
            <option value="business">Business</option>
            <option value="first">First Class</option>
          </select>
        </div>

        {/* Sort Options */}
        <div className="flex items-center space-x-2">
          <SortAsc className="w-4 h-4 text-slate-500" />
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="px-3 py-1 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="recommended">AI Recommended</option>
            <option value="time">Departure Time</option>
            <option value="price">Price</option>
          </select>
        </div>
      </div>

      {/* Rebooking Options */}
      <div className="space-y-4 mb-8">
        {sortedOptions.map((option) => (
          <OptionCard key={option.id} option={option} />
        ))}
      </div>

      {/* Confirmation Section */}
      {selectedOption && (
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 p-4 safe-bottom">
          <div className="mobile-container">
            <div className="flex items-center justify-between mb-4">
              <div>
                <div className="font-semibold text-slate-800">
                  {selectedOption.flightNumber}
                </div>
                <div className="text-sm text-slate-600">
                  {formatTime(selectedOption.departureTime)} → {formatTime(selectedOption.arrivalTime)}
                </div>
              </div>
              <div className="text-right">
                <div className="text-lg font-bold text-primary-600">
                  £{getSeatPrice(selectedOption, selectedClass)}
                </div>
                <div className="text-sm text-slate-600 capitalize">
                  {selectedClass} class
                </div>
              </div>
            </div>
            
            <button
              onClick={handleConfirmBooking}
              disabled={confirming}
              className={`btn btn-primary w-full ${confirming ? 'opacity-50' : ''}`}
            >
              {confirming ? (
                <>
                  <div className="loading-dots text-white mr-2">
                    <div className="loading-dot"></div>
                    <div className="loading-dot" style={{ animationDelay: '0.1s' }}></div>
                    <div className="loading-dot" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                  Confirming Booking...
                </>
              ) : (
                <>
                  <CheckCircle className="w-5 h-5 mr-2" />
                  Confirm New Booking
                </>
              )}
            </button>
            
            <p className="text-xs text-slate-500 text-center mt-2">
              No additional charges • Instant confirmation
            </p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {rebookingOptions.length === 0 && (
        <div className="text-center py-12">
          <MapPin className="w-12 h-12 text-slate-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-slate-800 mb-2">
            No Options Available
          </h3>
          <p className="text-slate-600">
            We're working on finding alternative flights for you.
          </p>
        </div>
      )}
    </div>
  );
}