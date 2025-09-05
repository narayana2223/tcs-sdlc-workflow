'use client';

import React, { useState, useEffect } from 'react';
import { Compensation, Flight, Passenger } from '@/types';
import { 
  Calculator, 
  Euro,
  FileText,
  Clock,
  CheckCircle,
  AlertCircle,
  Download,
  Send,
  Info,
  Scale,
  Plane
} from 'lucide-react';

interface CompensationPortalProps {
  flight: Flight;
  passenger: Passenger;
  existingCompensation?: Compensation[];
  onSubmitClaim: (claimData: ClaimData) => void;
  onDownloadReceipt: (compensationId: string) => void;
}

interface ClaimData {
  flightId: string;
  compensationType: 'eu261' | 'goodwill' | 'refund';
  amount: number;
  reason: string;
  supportingDocuments?: FileList;
}

export default function CompensationPortal({ 
  flight,
  passenger,
  existingCompensation = [],
  onSubmitClaim,
  onDownloadReceipt
}: CompensationPortalProps) {
  const [activeTab, setActiveTab] = useState<'calculate' | 'claims' | 'info'>('calculate');
  const [calculatedAmount, setCalculatedAmount] = useState<number | null>(null);
  const [eligibilityReason, setEligibilityReason] = useState<string>('');
  const [claimSubmitting, setClaimSubmitting] = useState(false);

  // EU261 compensation calculation
  useEffect(() => {
    calculateCompensation();
  }, [flight]);

  const calculateCompensation = () => {
    // EU261 compensation rules
    const getFlightDistance = (depAirport: string, arrAirport: string): number => {
      // Simplified distance calculation - in production this would use actual coordinates
      const distances: { [key: string]: number } = {
        'LHR-CDG': 350,
        'LGW-JFK': 5600,
        'LHR-FRA': 650,
        'MAN-BCN': 1200,
        'EDI-AMS': 600,
      };
      return distances[`${depAirport}-${arrAirport}`] || distances[`${arrAirport}-${depAirport}`] || 800;
    };

    const distance = getFlightDistance(flight.departureAirport, flight.arrivalAirport);
    const delayMinutes = flight.delay || 0;

    let amount = 0;
    let reason = '';

    if (flight.status === 'cancelled') {
      // Cancelled flights
      if (distance <= 1500) {
        amount = 250;
      } else if (distance <= 3500) {
        amount = 400;
      } else {
        amount = 600;
      }
      reason = 'Flight cancellation compensation under EU261 regulation';
    } else if (delayMinutes >= 180) {
      // Delayed flights (3+ hours)
      if (distance <= 1500) {
        amount = 250;
      } else if (distance <= 3500) {
        amount = 400;
      } else {
        amount = 600;
      }
      reason = `Flight delay compensation for ${Math.floor(delayMinutes / 60)}h ${delayMinutes % 60}m delay`;
    } else if (delayMinutes >= 120) {
      // Moderate delays (2-3 hours)
      reason = 'Delay under 3 hours - not eligible for EU261 compensation, but may qualify for goodwill compensation';
      amount = 0;
    } else {
      reason = 'Flight disruption does not meet EU261 compensation criteria';
      amount = 0;
    }

    setCalculatedAmount(amount);
    setEligibilityReason(reason);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-GB', {
      style: 'currency',
      currency: 'EUR',
    }).format(amount);
  };

  const getStatusIcon = (status: Compensation['status']) => {
    switch (status) {
      case 'pending':
        return <Clock className="w-4 h-4 text-warning-500" />;
      case 'approved':
        return <CheckCircle className="w-4 h-4 text-success-500" />;
      case 'paid':
        return <CheckCircle className="w-4 h-4 text-success-500" />;
      case 'rejected':
        return <AlertCircle className="w-4 h-4 text-danger-500" />;
      default:
        return <Clock className="w-4 h-4 text-slate-500" />;
    }
  };

  const getStatusColor = (status: Compensation['status']) => {
    switch (status) {
      case 'pending':
        return 'text-warning-600 bg-warning-100';
      case 'approved':
        return 'text-success-600 bg-success-100';
      case 'paid':
        return 'text-success-600 bg-success-100';
      case 'rejected':
        return 'text-danger-600 bg-danger-100';
      default:
        return 'text-slate-600 bg-slate-100';
    }
  };

  const handleSubmitClaim = async () => {
    if (calculatedAmount === null || calculatedAmount <= 0) return;

    setClaimSubmitting(true);

    const claimData: ClaimData = {
      flightId: flight.id,
      compensationType: calculatedAmount > 0 ? 'eu261' : 'goodwill',
      amount: calculatedAmount,
      reason: eligibilityReason,
    };

    setTimeout(() => {
      onSubmitClaim(claimData);
      setClaimSubmitting(false);
    }, 2000);
  };

  const CompensationCalculator = () => (
    <div className="space-y-6">
      {/* Flight Details */}
      <div className="card bg-slate-50">
        <h3 className="font-semibold text-slate-800 mb-4">Flight Details</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-slate-600">Flight:</span>
            <div className="font-medium">{flight.flightNumber}</div>
          </div>
          <div>
            <span className="text-slate-600">Route:</span>
            <div className="font-medium">{flight.departureAirport} → {flight.arrivalAirport}</div>
          </div>
          <div>
            <span className="text-slate-600">Status:</span>
            <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
              flight.status === 'cancelled' ? 'bg-danger-100 text-danger-800' : 'bg-warning-100 text-warning-800'
            }`}>
              {flight.status}
            </div>
          </div>
          <div>
            <span className="text-slate-600">Delay:</span>
            <div className="font-medium">
              {flight.delay ? `${Math.floor(flight.delay / 60)}h ${flight.delay % 60}m` : 'On time'}
            </div>
          </div>
        </div>
      </div>

      {/* Compensation Result */}
      <div className="card">
        <div className="flex items-center space-x-3 mb-4">
          <div className="p-2 bg-primary-100 rounded-lg">
            <Calculator className="w-6 h-6 text-primary-600" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-800">Compensation Assessment</h3>
            <p className="text-sm text-slate-600">Based on EU261 regulation</p>
          </div>
        </div>

        {calculatedAmount !== null && (
          <div className="text-center py-6">
            <div className="text-4xl font-bold text-primary-600 mb-2">
              {calculatedAmount > 0 ? formatCurrency(calculatedAmount) : '€0'}
            </div>
            <div className={`text-sm font-medium mb-4 ${
              calculatedAmount > 0 ? 'text-success-600' : 'text-slate-600'
            }`}>
              {calculatedAmount > 0 ? 'You are eligible for compensation' : 'Not eligible for EU261 compensation'}
            </div>
            <p className="text-sm text-slate-600 mb-6">
              {eligibilityReason}
            </p>

            {calculatedAmount > 0 && (
              <button
                onClick={handleSubmitClaim}
                disabled={claimSubmitting}
                className={`btn btn-primary w-full ${claimSubmitting ? 'opacity-50' : ''}`}
              >
                {claimSubmitting ? (
                  <>
                    <div className="loading-dots text-white mr-2">
                      <div className="loading-dot"></div>
                      <div className="loading-dot" style={{ animationDelay: '0.1s' }}></div>
                      <div className="loading-dot" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                    Submitting Claim...
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4 mr-2" />
                    Submit Compensation Claim
                  </>
                )}
              </button>
            )}
          </div>
        )}
      </div>

      {/* EU261 Quick Guide */}
      <div className="card bg-blue-50 border-blue-200">
        <div className="flex items-start space-x-3">
          <Scale className="w-5 h-5 text-blue-600 flex-shrink-0 mt-1" />
          <div>
            <h4 className="font-medium text-blue-800 mb-2">EU261 Compensation Guide</h4>
            <div className="text-sm text-blue-700 space-y-1">
              <p>• €250 for flights up to 1,500km</p>
              <p>• €400 for flights 1,500-3,500km</p>
              <p>• €600 for flights over 3,500km</p>
              <p className="pt-2 text-xs">
                Applies to cancellations and delays over 3 hours on EU flights
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const ClaimsHistory = () => (
    <div className="space-y-4">
      {existingCompensation.length > 0 ? (
        existingCompensation.map((compensation) => (
          <div key={compensation.id} className="card">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-2">
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(compensation.status)}`}>
                    {getStatusIcon(compensation.status)}
                    <span className="ml-1 capitalize">{compensation.status}</span>
                  </span>
                  <span className="text-xs text-slate-500">
                    {compensation.reference}
                  </span>
                </div>
                
                <h3 className="font-medium text-slate-800 mb-1">
                  {formatCurrency(compensation.amount)} Compensation
                </h3>
                <p className="text-sm text-slate-600 mb-2">
                  {compensation.reason}
                </p>
                
                <div className="text-xs text-slate-500">
                  Claimed: {new Intl.DateTimeFormat('en-GB').format(compensation.claimDate)}
                  {compensation.processedDate && (
                    <span className="ml-2">
                      • Processed: {new Intl.DateTimeFormat('en-GB').format(compensation.processedDate)}
                    </span>
                  )}
                </div>
              </div>
              
              <div className="text-right ml-4">
                <div className="text-lg font-bold text-slate-800">
                  {formatCurrency(compensation.amount)}
                </div>
                {compensation.status === 'paid' && (
                  <button
                    onClick={() => onDownloadReceipt(compensation.id)}
                    className="mt-2 text-sm text-primary-600 hover:text-primary-700 flex items-center"
                  >
                    <Download className="w-3 h-3 mr-1" />
                    Receipt
                  </button>
                )}
              </div>
            </div>
          </div>
        ))
      ) : (
        <div className="text-center py-12">
          <FileText className="w-12 h-12 text-slate-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-slate-800 mb-2">
            No Claims Yet
          </h3>
          <p className="text-slate-600">
            Your compensation claims will appear here
          </p>
        </div>
      )}
    </div>
  );

  const InfoPanel = () => (
    <div className="space-y-6">
      <div className="card">
        <h3 className="font-semibold text-slate-800 mb-4 flex items-center">
          <Info className="w-5 h-5 mr-2 text-primary-600" />
          Your Rights Under EU261
        </h3>
        <div className="space-y-4 text-sm">
          <div>
            <h4 className="font-medium text-slate-800 mb-2">When You're Entitled:</h4>
            <ul className="list-disc list-inside text-slate-600 space-y-1">
              <li>Flight cancelled with less than 14 days notice</li>
              <li>Flight delayed by more than 3 hours</li>
              <li>Denied boarding due to overbooking</li>
              <li>Flight departs from EU or arrives in EU on EU airline</li>
            </ul>
          </div>
          
          <div>
            <h4 className="font-medium text-slate-800 mb-2">Compensation Amounts:</h4>
            <ul className="list-disc list-inside text-slate-600 space-y-1">
              <li>€250 for flights up to 1,500km</li>
              <li>€400 for flights between 1,500-3,500km</li>
              <li>€600 for flights over 3,500km</li>
            </ul>
          </div>
          
          <div>
            <h4 className="font-medium text-slate-800 mb-2">Additional Rights:</h4>
            <ul className="list-disc list-inside text-slate-600 space-y-1">
              <li>Free meals and refreshments</li>
              <li>Hotel accommodation if needed</li>
              <li>Transport to and from hotel</li>
              <li>Free phone calls/emails</li>
            </ul>
          </div>
        </div>
      </div>

      <div className="card bg-warning-50 border-warning-200">
        <div className="flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-warning-600 flex-shrink-0 mt-1" />
          <div>
            <h4 className="font-medium text-warning-800 mb-2">Important Notes</h4>
            <div className="text-sm text-warning-700 space-y-1">
              <p>• No compensation if disruption due to extraordinary circumstances</p>
              <p>• You have up to 3 years to claim (varies by country)</p>
              <p>• Alternative flight arrangements don't affect compensation</p>
              <p>• Claims are processed automatically in most cases</p>
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <h4 className="font-medium text-slate-800 mb-3">Need Help?</h4>
        <p className="text-sm text-slate-600 mb-4">
          Our automated system handles most claims instantly. For complex cases or questions, 
          contact our dedicated compensation team.
        </p>
        <button className="btn btn-secondary">
          <FileText className="w-4 h-4 mr-2" />
          Contact Compensation Team
        </button>
      </div>
    </div>
  );

  return (
    <div className="mobile-container">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-responsive-2xl font-bold text-slate-800 mb-2">
          Compensation & Claims
        </h1>
        <p className="text-slate-600">
          Get the compensation you're entitled to under EU261
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="flex items-center space-x-1 mb-6 bg-slate-100 rounded-lg p-1">
        <button
          onClick={() => setActiveTab('calculate')}
          className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'calculate'
              ? 'bg-white text-slate-800 shadow-sm'
              : 'text-slate-600 hover:text-slate-800'
          }`}
        >
          <Calculator className="w-4 h-4 mr-2 inline" />
          Calculate
        </button>
        <button
          onClick={() => setActiveTab('claims')}
          className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'claims'
              ? 'bg-white text-slate-800 shadow-sm'
              : 'text-slate-600 hover:text-slate-800'
          }`}
        >
          <FileText className="w-4 h-4 mr-2 inline" />
          My Claims ({existingCompensation.length})
        </button>
        <button
          onClick={() => setActiveTab('info')}
          className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'info'
              ? 'bg-white text-slate-800 shadow-sm'
              : 'text-slate-600 hover:text-slate-800'
          }`}
        >
          <Info className="w-4 h-4 mr-2 inline" />
          Your Rights
        </button>
      </div>

      {/* Content */}
      {activeTab === 'calculate' && <CompensationCalculator />}
      {activeTab === 'claims' && <ClaimsHistory />}
      {activeTab === 'info' && <InfoPanel />}
    </div>
  );
}