'use client';

import React, { useState } from 'react';
import { TravelAssistance } from '@/types';
import { 
  Hotel, 
  Car, 
  Utensils, 
  Coffee,
  Star,
  MapPin,
  Clock,
  Check,
  ExternalLink,
  Ticket,
  CreditCard,
  Shield
} from 'lucide-react';

interface TravelAssistancePortalProps {
  assistance: TravelAssistance[];
  onBook: (assistanceId: string) => void;
  onUseVoucher: (assistanceId: string, voucherCode: string) => void;
  loading?: boolean;
}

export default function TravelAssistancePortal({ 
  assistance,
  onBook,
  onUseVoucher,
  loading = false
}: TravelAssistancePortalProps) {
  const [activeCategory, setActiveCategory] = useState<'all' | 'hotel' | 'transport' | 'meal' | 'lounge'>('all');
  const [sortBy, setSortBy] = useState<'recommended' | 'price' | 'rating'>('recommended');

  const getAssistanceIcon = (type: TravelAssistance['type']) => {
    switch (type) {
      case 'hotel':
        return <Hotel className="w-5 h-5" />;
      case 'transport':
        return <Car className="w-5 h-5" />;
      case 'meal':
        return <Utensils className="w-5 h-5" />;
      case 'lounge':
        return <Coffee className="w-5 h-5" />;
      default:
        return <Shield className="w-5 h-5" />;
    }
  };

  const getAssistanceColor = (type: TravelAssistance['type']) => {
    switch (type) {
      case 'hotel':
        return 'text-blue-600 bg-blue-100';
      case 'transport':
        return 'text-green-600 bg-green-100';
      case 'meal':
        return 'text-orange-600 bg-orange-100';
      case 'lounge':
        return 'text-purple-600 bg-purple-100';
      default:
        return 'text-slate-600 bg-slate-100';
    }
  };

  const StarRating = ({ rating }: { rating: number }) => (
    <div className="flex items-center space-x-1">
      {[...Array(5)].map((_, i) => (
        <Star
          key={i}
          className={`w-4 h-4 ${
            i < Math.floor(rating)
              ? 'text-yellow-400 fill-current'
              : 'text-slate-300'
          }`}
        />
      ))}
      <span className="text-sm text-slate-600 ml-1">
        {rating.toFixed(1)}
      </span>
    </div>
  );

  const filteredAssistance = assistance.filter(item => 
    activeCategory === 'all' || item.type === activeCategory
  );

  const sortedAssistance = [...filteredAssistance].sort((a, b) => {
    switch (sortBy) {
      case 'price':
        return a.price - b.price;
      case 'rating':
        return b.rating - a.rating;
      case 'recommended':
      default:
        return b.rating - a.rating; // Default to rating for recommended
    }
  });

  const AssistanceCard = ({ item }: { item: TravelAssistance }) => {
    const isAvailable = item.available;
    const hasVoucher = !!item.voucherCode;
    
    return (
      <div className={`card transition-all duration-200 ${
        isAvailable ? 'hover:shadow-lg hover:scale-[1.02]' : 'opacity-60'
      }`}>
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-start space-x-3">
            <div className={`p-2 rounded-lg ${getAssistanceColor(item.type)}`}>
              {getAssistanceIcon(item.type)}
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-slate-800 text-responsive-base">
                {item.title}
              </h3>
              <p className="text-slate-600 text-sm">
                {item.provider}
              </p>
              <div className="flex items-center space-x-2 mt-1">
                <MapPin className="w-4 h-4 text-slate-400" />
                <span className="text-sm text-slate-600">{item.location}</span>
              </div>
            </div>
          </div>
          
          <div className="text-right">
            <div className="text-lg font-bold text-slate-800">
              {hasVoucher ? (
                <span className="text-success-600">FREE</span>
              ) : (
                `£${item.price}`
              )}
            </div>
            {hasVoucher && (
              <div className="text-xs text-success-600 font-medium">
                Covered by airline
              </div>
            )}
          </div>
        </div>

        {/* Rating and Description */}
        <div className="mb-4">
          <StarRating rating={item.rating} />
          <p className="text-sm text-slate-600 mt-2 line-clamp-2">
            {item.description}
          </p>
        </div>

        {/* Amenities */}
        {item.amenities.length > 0 && (
          <div className="mb-4">
            <div className="flex flex-wrap gap-2">
              {item.amenities.slice(0, 4).map((amenity, index) => (
                <span
                  key={index}
                  className="inline-flex items-center px-2 py-1 bg-slate-100 text-slate-700 rounded-full text-xs"
                >
                  {amenity}
                </span>
              ))}
              {item.amenities.length > 4 && (
                <span className="inline-flex items-center px-2 py-1 bg-slate-100 text-slate-700 rounded-full text-xs">
                  +{item.amenities.length - 4} more
                </span>
              )}
            </div>
          </div>
        )}

        {/* Voucher Code Display */}
        {hasVoucher && (
          <div className="mb-4 p-3 bg-success-50 border border-success-200 rounded-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Ticket className="w-4 h-4 text-success-600" />
                <span className="text-sm font-medium text-success-800">
                  Voucher Code
                </span>
              </div>
              <div className="font-mono text-sm font-bold text-success-800 bg-white px-2 py-1 rounded border">
                {item.voucherCode}
              </div>
            </div>
            <p className="text-xs text-success-700 mt-2">
              Present this code when booking or show to staff
            </p>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3">
          {hasVoucher ? (
            <>
              <button
                onClick={() => onUseVoucher(item.id, item.voucherCode!)}
                disabled={!isAvailable}
                className={`flex-1 btn ${
                  isAvailable ? 'btn-success' : 'bg-slate-300 text-slate-500'
                }`}
              >
                <Check className="w-4 h-4 mr-2" />
                Use Voucher
              </button>
              {item.bookingUrl && (
                <button
                  onClick={() => window.open(item.bookingUrl, '_blank')}
                  className="btn btn-secondary"
                >
                  <ExternalLink className="w-4 h-4" />
                </button>
              )}
            </>
          ) : (
            <>
              <button
                onClick={() => onBook(item.id)}
                disabled={!isAvailable}
                className={`flex-1 btn ${
                  isAvailable ? 'btn-primary' : 'bg-slate-300 text-slate-500'
                }`}
              >
                <CreditCard className="w-4 h-4 mr-2" />
                Book Now
              </button>
              {item.bookingUrl && (
                <button
                  onClick={() => window.open(item.bookingUrl, '_blank')}
                  className="btn btn-secondary"
                >
                  <ExternalLink className="w-4 h-4" />
                </button>
              )}
            </>
          )}
        </div>

        {/* Unavailable Overlay */}
        {!isAvailable && (
          <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center rounded-2xl">
            <div className="text-center">
              <Clock className="w-8 h-8 text-slate-400 mx-auto mb-2" />
              <div className="text-sm font-medium text-slate-600">
                Currently Unavailable
              </div>
            </div>
          </div>
        )}
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
          <p className="text-slate-600">Finding assistance options...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="mobile-container">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-responsive-2xl font-bold text-slate-800 mb-2">
          Travel Assistance
        </h1>
        <p className="text-slate-600">
          We've arranged options to help with your disrupted journey
        </p>
      </div>

      {/* Category Tabs */}
      <div className="flex items-center space-x-2 mb-6 overflow-x-auto pb-2">
        {[
          { key: 'all', label: 'All', icon: Shield },
          { key: 'hotel', label: 'Hotels', icon: Hotel },
          { key: 'transport', label: 'Transport', icon: Car },
          { key: 'meal', label: 'Meals', icon: Utensils },
          { key: 'lounge', label: 'Lounge', icon: Coffee },
        ].map(({ key, label, icon: Icon }) => {
          const count = key === 'all' 
            ? assistance.length 
            : assistance.filter(item => item.type === key).length;
            
          return (
            <button
              key={key}
              onClick={() => setActiveCategory(key as any)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
                activeCategory === key
                  ? 'bg-primary-500 text-white'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{label}</span>
              {count > 0 && (
                <span className={`px-2 py-0.5 rounded-full text-xs ${
                  activeCategory === key
                    ? 'bg-primary-400 text-white'
                    : 'bg-slate-200 text-slate-600'
                }`}>
                  {count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Sort Options */}
      <div className="flex items-center justify-between mb-6">
        <div className="text-sm text-slate-600">
          {sortedAssistance.length} option{sortedAssistance.length !== 1 ? 's' : ''} available
        </div>
        
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as any)}
          className="px-3 py-1 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          <option value="recommended">Recommended</option>
          <option value="rating">Highest Rated</option>
          <option value="price">Lowest Price</option>
        </select>
      </div>

      {/* Assistance Cards */}
      <div className="space-y-4">
        {sortedAssistance.map((item) => (
          <AssistanceCard key={item.id} item={item} />
        ))}
      </div>

      {/* Empty State */}
      {sortedAssistance.length === 0 && (
        <div className="text-center py-12">
          <Shield className="w-12 h-12 text-slate-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-slate-800 mb-2">
            No assistance available
          </h3>
          <p className="text-slate-600">
            {activeCategory === 'all' 
              ? 'We\'re working on finding options for you'
              : `No ${activeCategory} options available at the moment`
            }
          </p>
        </div>
      )}

      {/* Support Note */}
      <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-xl">
        <div className="flex items-start space-x-3">
          <Shield className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-medium text-blue-800 mb-1">
              Need additional help?
            </h3>
            <p className="text-blue-700 text-sm">
              Our customer service team is available 24/7 to assist with special requirements 
              or if you need help with bookings.
            </p>
            <button className="mt-2 text-blue-600 hover:text-blue-700 text-sm font-medium">
              Contact Support →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}