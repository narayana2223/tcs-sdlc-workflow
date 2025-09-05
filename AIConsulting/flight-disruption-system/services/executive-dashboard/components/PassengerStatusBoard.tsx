'use client';

import React from 'react';
import { PassengerMetrics } from '@/types';
import { Users, Clock, CheckCircle, Smile, Star, Timer, TrendingUp, UserCheck } from 'lucide-react';

interface PassengerStatusBoardProps {
  metrics: PassengerMetrics;
}

export default function PassengerStatusBoard({ metrics }: PassengerStatusBoardProps) {
  const completionRate = metrics.totalAffected > 0 
    ? (metrics.rebooked / metrics.totalAffected) * 100 
    : 0;

  const satisfactionColor = (score: number) => {
    if (score >= 4.5) return 'text-success-600';
    if (score >= 3.5) return 'text-warning-600';
    return 'text-danger-600';
  };

  const getSatisfactionStars = (rating: number) => {
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 >= 0.5;
    
    return (
      <div className="flex items-center space-x-1">
        {[...Array(5)].map((_, i) => (
          <Star
            key={i}
            className={`w-4 h-4 ${
              i < fullStars
                ? 'text-yellow-400 fill-current'
                : i === fullStars && hasHalfStar
                ? 'text-yellow-400 fill-current'
                : 'text-slate-300'
            }`}
          />
        ))}
        <span className="ml-2 text-sm font-medium">
          {rating.toFixed(1)}/5.0
        </span>
      </div>
    );
  };

  const formatTime = (minutes: number) => {
    if (minutes < 60) {
      return `${Math.round(minutes)}min`;
    }
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    return `${hours}h ${mins}min`;
  };

  return (
    <div className="space-y-6">
      {/* Overall Status Summary */}
      <div className="card bg-gradient-to-r from-primary-50 to-primary-100 border-primary-200">
        <div className="text-center">
          <div className="flex items-center justify-center mb-4">
            <div className="p-3 bg-primary-500 rounded-full text-white">
              <Users className="w-8 h-8" />
            </div>
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <div className="text-3xl font-bold text-primary-700">
                {metrics.totalAffected.toLocaleString()}
              </div>
              <div className="text-sm text-primary-600">Total Affected</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-success-700">
                {metrics.rebooked.toLocaleString()}
              </div>
              <div className="text-sm text-success-600">Rebooked</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-warning-700">
                {metrics.inProgress.toLocaleString()}
              </div>
              <div className="text-sm text-warning-600">In Progress</div>
            </div>
          </div>
          
          {/* Progress Bar */}
          <div className="mt-4">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-primary-700">Completion Rate</span>
              <span className="text-sm font-bold text-primary-700">
                {completionRate.toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-white rounded-full h-3 shadow-inner">
              <div 
                className="bg-primary-500 h-3 rounded-full transition-all duration-1000 flex items-center justify-end pr-1"
                style={{ width: `${Math.min(100, completionRate)}%` }}
              >
                {completionRate > 20 && (
                  <div className="text-xs text-white font-bold">
                    {completionRate.toFixed(0)}%
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Satisfaction Metrics */}
      <div className="grid grid-cols-2 gap-4">
        <div className="metric-card">
          <div className="flex items-center justify-between mb-3">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <Smile className="w-5 h-5 text-yellow-600" />
            </div>
            <div className={`text-2xl font-bold ${satisfactionColor(metrics.averageSatisfaction)}`}>
              {metrics.averageSatisfaction.toFixed(1)}
            </div>
          </div>
          <div className="mb-2">
            {getSatisfactionStars(metrics.averageSatisfaction)}
          </div>
          <div className="text-sm text-slate-600">Average Satisfaction</div>
        </div>

        <div className="metric-card">
          <div className="flex items-center justify-between mb-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <UserCheck className="w-5 h-5 text-green-600" />
            </div>
            <TrendingUp className="w-4 h-4 text-success-500" />
          </div>
          <div className="text-2xl font-bold text-slate-800 mb-1">
            {metrics.satisfied.toLocaleString()}
          </div>
          <div className="text-sm text-slate-600">
            Satisfied Passengers ({((metrics.satisfied / Math.max(metrics.totalAffected, 1)) * 100).toFixed(1)}%)
          </div>
        </div>
      </div>

      {/* Rebooking Performance */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold text-slate-800 flex items-center space-x-2">
            <Timer className="w-5 h-5" />
            <span>Rebooking Performance</span>
          </h3>
        </div>

        <div className="grid grid-cols-2 gap-6">
          {/* Average Rebooking Time */}
          <div className="text-center">
            <div className="text-3xl font-bold text-primary-600 mb-2">
              {formatTime(metrics.averageRebookingTime)}
            </div>
            <div className="text-sm text-slate-600 mb-4">Average Rebooking Time</div>
            
            {/* Time breakdown visualization */}
            <div className="space-y-2">
              <div className="flex justify-between items-center text-sm">
                <span className="text-slate-600">Target: 15min</span>
                <span className={`font-medium ${metrics.averageRebookingTime <= 15 ? 'text-success-600' : 'text-warning-600'}`}>
                  {metrics.averageRebookingTime <= 15 ? '✓ Met' : '⚠ Above'}
                </span>
              </div>
              <div className="w-full bg-slate-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full transition-all duration-1000 ${
                    metrics.averageRebookingTime <= 15 ? 'bg-success-500' : 
                    metrics.averageRebookingTime <= 30 ? 'bg-warning-500' : 'bg-danger-500'
                  }`}
                  style={{ width: `${Math.min(100, (metrics.averageRebookingTime / 30) * 100)}%` }}
                />
              </div>
            </div>
          </div>

          {/* Processing Status */}
          <div>
            <div className="text-lg font-semibold text-slate-800 mb-4 text-center">
              Processing Status
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-success-50 rounded-lg border border-success-200">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="w-4 h-4 text-success-600" />
                  <span className="text-sm font-medium text-success-700">Completed</span>
                </div>
                <span className="text-sm font-bold text-success-700">
                  {metrics.rebooked.toLocaleString()}
                </span>
              </div>

              <div className="flex items-center justify-between p-3 bg-warning-50 rounded-lg border border-warning-200">
                <div className="flex items-center space-x-2">
                  <Clock className="w-4 h-4 text-warning-600" />
                  <span className="text-sm font-medium text-warning-700">In Progress</span>
                </div>
                <span className="text-sm font-bold text-warning-700">
                  {metrics.inProgress.toLocaleString()}
                </span>
              </div>

              <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg border border-slate-200">
                <div className="flex items-center space-x-2">
                  <Users className="w-4 h-4 text-slate-600" />
                  <span className="text-sm font-medium text-slate-700">Pending</span>
                </div>
                <span className="text-sm font-bold text-slate-700">
                  {(metrics.totalAffected - metrics.rebooked - metrics.inProgress).toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Key Performance Indicators */}
        <div className="mt-6 p-4 bg-slate-50 rounded-lg">
          <h4 className="text-sm font-semibold text-slate-800 mb-3">Key Performance Indicators</h4>
          <div className="grid grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-xl font-bold text-primary-600">
                {completionRate.toFixed(1)}%
              </div>
              <div className="text-xs text-slate-600">Completion</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-success-600">
                {((metrics.satisfied / Math.max(metrics.rebooked, 1)) * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-slate-600">Satisfaction</div>
            </div>
            <div className="text-center">
              <div className={`text-xl font-bold ${metrics.averageRebookingTime <= 15 ? 'text-success-600' : 'text-warning-600'}`}>
                {formatTime(metrics.averageRebookingTime)}
              </div>
              <div className="text-xs text-slate-600">Avg Time</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-purple-600">
                {Math.round((metrics.rebooked / Math.max(metrics.averageRebookingTime / 60, 1)) * 60)}
              </div>
              <div className="text-xs text-slate-600">Per Hour</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}