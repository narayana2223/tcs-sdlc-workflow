'use client';

import React, { useState } from 'react';
import { Alert } from '@/types';
import { AlertTriangle, CheckCircle, Info, X, Bell, Clock, Zap } from 'lucide-react';

interface AlertsNotificationsProps {
  alerts: Alert[];
  onAcknowledgeAlert: (alertId: string) => void;
}

const alertIcons = {
  critical: AlertTriangle,
  warning: AlertTriangle,
  info: Info,
};

const alertColors = {
  critical: {
    bg: 'bg-danger-50',
    border: 'border-danger-200',
    text: 'text-danger-700',
    icon: 'text-danger-600',
    badge: 'bg-danger-500'
  },
  warning: {
    bg: 'bg-warning-50',
    border: 'border-warning-200',
    text: 'text-warning-700',
    icon: 'text-warning-600',
    badge: 'bg-warning-500'
  },
  info: {
    bg: 'bg-primary-50',
    border: 'border-primary-200',
    text: 'text-primary-700',
    icon: 'text-primary-600',
    badge: 'bg-primary-500'
  },
};

export default function AlertsNotifications({ alerts, onAcknowledgeAlert }: AlertsNotificationsProps) {
  const [filter, setFilter] = useState<'all' | Alert['type']>('all');
  const [showAcknowledged, setShowAcknowledged] = useState(false);

  const filteredAlerts = alerts.filter(alert => {
    const typeMatch = filter === 'all' || alert.type === filter;
    const acknowledgedMatch = showAcknowledged || !alert.acknowledged;
    return typeMatch && acknowledgedMatch;
  });

  const unacknowledgedCount = alerts.filter(alert => !alert.acknowledged).length;
  const criticalCount = alerts.filter(alert => alert.type === 'critical' && !alert.acknowledged).length;

  const getTimeSince = (timestamp: Date) => {
    const now = new Date();
    const diff = now.getTime() - timestamp.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return 'Just now';
  };

  const AlertCard = ({ alert }: { alert: Alert }) => {
    const AlertIcon = alertIcons[alert.type];
    const colors = alertColors[alert.type];

    return (
      <div className={`${colors.bg} ${colors.border} border rounded-lg p-4 ${alert.acknowledged ? 'opacity-60' : ''}`}>
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-3 flex-1">
            <div className={`p-1 rounded-full ${alert.acknowledged ? 'bg-slate-200' : colors.badge} ${alert.acknowledged ? 'text-slate-600' : 'text-white'}`}>
              {alert.acknowledged ? (
                <CheckCircle className="w-4 h-4" />
              ) : (
                <AlertIcon className="w-4 h-4" />
              )}
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <span className={`text-xs font-medium uppercase tracking-wider ${colors.text}`}>
                    {alert.type}
                  </span>
                  {alert.type === 'critical' && !alert.acknowledged && (
                    <div className="pulse-indicator">
                      <div className="bg-danger-500"></div>
                      <div className="bg-danger-500"></div>
                    </div>
                  )}
                </div>
                <div className="flex items-center space-x-2 text-xs text-slate-500">
                  <Clock className="w-3 h-3" />
                  <span>{getTimeSince(alert.timestamp)}</span>
                </div>
              </div>

              <p className={`text-sm mb-2 ${colors.text}`}>
                {alert.message}
              </p>

              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-600">
                  Source: {alert.source}
                </span>
                {!alert.acknowledged && (
                  <button
                    onClick={() => onAcknowledgeAlert(alert.id)}
                    className="text-xs px-2 py-1 bg-white border border-slate-300 rounded hover:bg-slate-50 transition-colors"
                  >
                    Acknowledge
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="card h-full flex flex-col">
      <div className="card-header">
        <div className="flex items-center space-x-2">
          <Bell className="w-6 h-6 text-slate-700" />
          <div>
            <h2 className="text-xl font-semibold text-slate-800">Alerts & Notifications</h2>
            <p className="text-sm text-slate-600">Critical system alerts requiring attention</p>
          </div>
        </div>
        
        {/* Alert Summary */}
        <div className="flex items-center space-x-4">
          {unacknowledgedCount > 0 && (
            <div className="flex items-center space-x-1 px-2 py-1 bg-danger-100 rounded-full">
              <Zap className="w-3 h-3 text-danger-600" />
              <span className="text-xs font-medium text-danger-700">
                {unacknowledgedCount} unread
              </span>
            </div>
          )}
          {criticalCount > 0 && (
            <div className="flex items-center space-x-1 px-2 py-1 bg-danger-500 text-white rounded-full animate-pulse">
              <AlertTriangle className="w-3 h-3" />
              <span className="text-xs font-bold">
                {criticalCount} critical
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value as any)}
            className="px-3 py-1 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="all">All Types</option>
            <option value="critical">Critical</option>
            <option value="warning">Warning</option>
            <option value="info">Info</option>
          </select>
          
          <label className="flex items-center space-x-2 text-sm">
            <input
              type="checkbox"
              checked={showAcknowledged}
              onChange={(e) => setShowAcknowledged(e.target.checked)}
              className="rounded border-slate-300 text-primary-600 focus:ring-primary-500"
            />
            <span className="text-slate-600">Show acknowledged</span>
          </label>
        </div>

        {/* Quick Stats */}
        <div className="flex items-center space-x-4 text-xs">
          <div className="flex items-center space-x-1">
            <div className="w-2 h-2 bg-danger-500 rounded-full"></div>
            <span className="text-slate-600">
              {alerts.filter(a => a.type === 'critical').length} Critical
            </span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-2 h-2 bg-warning-500 rounded-full"></div>
            <span className="text-slate-600">
              {alerts.filter(a => a.type === 'warning').length} Warning
            </span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-2 h-2 bg-primary-500 rounded-full"></div>
            <span className="text-slate-600">
              {alerts.filter(a => a.type === 'info').length} Info
            </span>
          </div>
        </div>
      </div>

      {/* Alerts List */}
      <div className="flex-1 overflow-y-auto">
        <div className="space-y-3">
          {filteredAlerts.length > 0 ? (
            filteredAlerts.map(alert => (
              <AlertCard key={alert.id} alert={alert} />
            ))
          ) : (
            <div className="text-center py-8">
              <CheckCircle className="w-12 h-12 text-success-400 mx-auto mb-3" />
              <p className="text-slate-600">
                {showAcknowledged ? 'No alerts to display' : 'All clear! No unacknowledged alerts'}
              </p>
              <p className="text-sm text-slate-500">
                {showAcknowledged ? 'Try adjusting your filters' : 'System is operating normally'}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Alert Statistics */}
      <div className="mt-4 pt-4 border-t border-slate-200">
        <div className="grid grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-lg font-bold text-danger-600">
              {alerts.filter(a => a.type === 'critical').length}
            </div>
            <div className="text-xs text-slate-600">Critical</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold text-warning-600">
              {alerts.filter(a => a.type === 'warning').length}
            </div>
            <div className="text-xs text-slate-600">Warning</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold text-primary-600">
              {alerts.filter(a => a.type === 'info').length}
            </div>
            <div className="text-xs text-slate-600">Info</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold text-success-600">
              {alerts.filter(a => a.acknowledged).length}
            </div>
            <div className="text-xs text-slate-600">Resolved</div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      {unacknowledgedCount > 0 && (
        <div className="mt-4 pt-4 border-t border-slate-200">
          <button
            onClick={() => {
              alerts.filter(a => !a.acknowledged).forEach(a => onAcknowledgeAlert(a.id));
            }}
            className="w-full px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg transition-colors text-sm font-medium"
          >
            Acknowledge All ({unacknowledgedCount})
          </button>
        </div>
      )}
    </div>
  );
}