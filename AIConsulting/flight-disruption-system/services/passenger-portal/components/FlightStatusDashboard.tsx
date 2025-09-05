'use client';

import React, { useState, useEffect } from 'react';
import { Flight, Passenger } from '@/types';
import { 
  Plane, 
  Clock, 
  MapPin, 
  AlertCircle, 
  CheckCircle, 
  Users, 
  Wifi, 
  Calendar,
  Navigation,
  Bell,
  RefreshCw
} from 'lucide-react';

interface FlightStatusDashboardProps {
  flight: Flight;
  passenger: Passenger;
  onRefresh?: () => void;
  isConnected?: boolean;
}

export default function FlightStatusDashboard({ 
  flight, 
  passenger, 
  onRefresh,
  isConnected = true 
}: FlightStatusDashboardProps) {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const getStatusIcon = (status: Flight['status']) => {
    switch (status) {
      case 'scheduled':
        return <CheckCircle className="w-5 h-5 text-blue-500" />;
      case 'delayed':
        return <Clock className="w-5 h-5 text-warning-500" />;
      case 'cancelled':
        return <AlertCircle className="w-5 h-5 text-danger-500" />;
      case 'boarding':
        return <Users className="w-5 h-5 text-success-500 animate-pulse" />;
      case 'departed':
        return <Plane className="w-5 h-5 text-slate-500" />;
      case 'arrived':
        return <CheckCircle className="w-5 h-5 text-success-500" />;
      default:
        return <Clock className="w-5 h-5 text-slate-500" />;
    }
  };

  const getStatusColor = (status: Flight['status']) => {
    switch (status) {
      case 'scheduled':
        return 'flight-status-scheduled';
      case 'delayed':
        return 'flight-status-delayed';
      case 'cancelled':
        return 'flight-status-cancelled';
      case 'boarding':
        return 'flight-status-boarding';
      case 'departed':
        return 'flight-status-departed';
      case 'arrived':
        return 'flight-status-scheduled';
      default:
        return 'flight-status-scheduled';
    }
  };

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
      day: 'numeric',
      month: 'short',
    }).format(date);
  };

  const getDelayText = () => {
    if (!flight.delay || flight.delay <= 0) return null;
    
    const hours = Math.floor(flight.delay / 60);
    const minutes = flight.delay % 60;
    
    if (hours > 0) {
      return `${hours}h ${minutes}m delayed`;
    }
    return `${minutes}m delayed`;
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    if (onRefresh) {
      onRefresh();
    }
    setTimeout(() => {
      setRefreshing(false);
    }, 1000);
  };

  const getTimeUntilDeparture = () => {
    const departureTime = flight.estimatedDeparture || flight.scheduledDeparture;
    const diff = departureTime.getTime() - currentTime.getTime();
    
    if (diff <= 0) return null;
    
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    return `${hours}h ${minutes}m until departure`;
  };

  return (
    <div className="mobile-container">
      {/* Header with connection status */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-responsive-2xl font-bold text-gradient">
            Hello, {passenger.firstName}!
          </h1>
          <p className="text-slate-600">Your flight status</p>
        </div>
        
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <Wifi className={`w-4 h-4 ${isConnected ? 'text-success-500' : 'text-danger-500'}`} />
            <span className={`text-sm ${isConnected ? 'text-success-600' : 'text-danger-600'}`}>
              {isConnected ? 'Live' : 'Offline'}
            </span>
          </div>
          
          <button
            onClick={handleRefresh}
            className={`p-2 rounded-full bg-slate-100 hover:bg-slate-200 transition-colors touch-target ${refreshing ? 'animate-spin' : ''}`}
            disabled={refreshing}
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Flight Card */}
      <div className="card card-hover animate-fade-in">
        {/* Flight Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-primary-100 rounded-2xl">
              <Plane className="w-8 h-8 text-primary-600" />
            </div>
            <div>
              <h2 className="text-responsive-xl font-bold">
                {flight.flightNumber}
              </h2>
              <p className="text-slate-600 text-responsive-sm">
                {flight.airline}
              </p>
            </div>
          </div>
          
          <div className="text-right">
            <div className={`flight-status ${getStatusColor(flight.status)} mb-2`}>
              {getStatusIcon(flight.status)}
              <span className="ml-2 capitalize">{flight.status}</span>
            </div>
            {getDelayText() && (
              <p className="text-warning-600 text-sm font-medium">
                {getDelayText()}
              </p>
            )}
          </div>
        </div>

        {/* Route Information */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          {/* Departure */}
          <div className="text-center">
            <div className="text-responsive-2xl font-bold text-slate-800">
              {flight.departureAirport}
            </div>
            <div className="text-slate-600 text-sm mb-2">
              {formatDate(flight.scheduledDeparture)}
            </div>
            <div className="space-y-1">
              <div className="text-responsive-lg font-semibold">
                {formatTime(flight.scheduledDeparture)}
              </div>
              {flight.estimatedDeparture.getTime() !== flight.scheduledDeparture.getTime() && (
                <div className="text-warning-600 font-medium">
                  → {formatTime(flight.estimatedDeparture)}
                </div>
              )}
            </div>
            {flight.gate && (
              <div className="mt-2 text-xs bg-slate-100 rounded-full px-2 py-1">
                Gate {flight.gate}
              </div>
            )}
          </div>

          {/* Flight Path */}
          <div className="flex flex-col items-center justify-center">
            <div className="flex items-center w-full mb-2">
              <div className="flex-1 h-0.5 bg-slate-300"></div>
              <Plane className="w-4 h-4 text-slate-500 mx-2" />
              <div className="flex-1 h-0.5 bg-slate-300"></div>
            </div>
            <div className="text-xs text-slate-500">
              {getTimeUntilDeparture()}
            </div>
          </div>

          {/* Arrival */}
          <div className="text-center">
            <div className="text-responsive-2xl font-bold text-slate-800">
              {flight.arrivalAirport}
            </div>
            <div className="text-slate-600 text-sm mb-2">
              {formatDate(flight.scheduledArrival)}
            </div>
            <div className="space-y-1">
              <div className="text-responsive-lg font-semibold">
                {formatTime(flight.scheduledArrival)}
              </div>
              {flight.estimatedArrival.getTime() !== flight.scheduledArrival.getTime() && (
                <div className="text-warning-600 font-medium">
                  → {formatTime(flight.estimatedArrival)}
                </div>
              )}
            </div>
            {flight.arrivalTerminal && (
              <div className="mt-2 text-xs bg-slate-100 rounded-full px-2 py-1">
                Terminal {flight.arrivalTerminal}
              </div>
            )}
          </div>
        </div>

        {/* Flight Details */}
        <div className="grid grid-cols-2 gap-4 pt-6 border-t border-slate-200">
          <div className="flex items-center space-x-3">
            <MapPin className="w-5 h-5 text-slate-500" />
            <div>
              <div className="font-medium text-slate-800">Seat</div>
              <div className="text-slate-600">{flight.seat || 'Not assigned'}</div>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <Navigation className="w-5 h-5 text-slate-500" />
            <div>
              <div className="font-medium text-slate-800">Aircraft</div>
              <div className="text-slate-600">{flight.aircraft || 'Unknown'}</div>
            </div>
          </div>
        </div>

        {/* Disruption Alert */}
        {(flight.status === 'delayed' || flight.status === 'cancelled') && flight.reason && (
          <div className="mt-4 p-4 bg-warning-50 border border-warning-200 rounded-xl">
            <div className="flex items-start space-x-3">
              <AlertCircle className="w-5 h-5 text-warning-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-medium text-warning-800 mb-1">
                  Flight {flight.status === 'cancelled' ? 'Cancelled' : 'Delayed'}
                </h3>
                <p className="text-warning-700 text-sm">
                  {flight.reason}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-2 gap-4 mt-6">
        <button className="btn btn-secondary">
          <Bell className="w-4 h-4 mr-2" />
          Notifications
        </button>
        <button className="btn btn-primary">
          <Calendar className="w-4 h-4 mr-2" />
          Manage Booking
        </button>
      </div>

      {/* Real-time Updates Indicator */}
      {isConnected && (
        <div className="mt-6 p-3 bg-success-50 border border-success-200 rounded-xl">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-success-500 rounded-full animate-pulse"></div>
            <span className="text-success-700 text-sm font-medium">
              Real-time updates active
            </span>
          </div>
        </div>
      )}

      {/* Last Updated */}
      <div className="mt-4 text-center">
        <p className="text-xs text-slate-500">
          Last updated: {formatTime(currentTime)}
        </p>
      </div>
    </div>
  );
}