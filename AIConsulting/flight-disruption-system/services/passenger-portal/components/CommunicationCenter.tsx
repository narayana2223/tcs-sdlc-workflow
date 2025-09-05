'use client';

import React, { useState, useEffect } from 'react';
import { Notification, NotificationAction } from '@/types';
import { 
  Bell, 
  MessageCircle, 
  Mail, 
  Smartphone, 
  Check, 
  Clock,
  AlertTriangle,
  Info,
  CheckCircle,
  X,
  Settings,
  Volume2,
  VolumeX
} from 'lucide-react';

interface CommunicationCenterProps {
  notifications: Notification[];
  onMarkAsRead: (notificationId: string) => void;
  onExecuteAction: (notificationId: string, actionId: string) => void;
  onUpdatePreferences: (preferences: NotificationPreferences) => void;
  preferences: NotificationPreferences;
}

interface NotificationPreferences {
  email: boolean;
  sms: boolean;
  push: boolean;
  soundEnabled: boolean;
  quietHours: {
    enabled: boolean;
    start: string;
    end: string;
  };
}

export default function CommunicationCenter({ 
  notifications,
  onMarkAsRead,
  onExecuteAction,
  onUpdatePreferences,
  preferences
}: CommunicationCenterProps) {
  const [activeTab, setActiveTab] = useState<'all' | 'unread' | 'settings'>('all');
  const [expandedNotification, setExpandedNotification] = useState<string | null>(null);
  const [localPreferences, setLocalPreferences] = useState(preferences);

  useEffect(() => {
    setLocalPreferences(preferences);
  }, [preferences]);

  const getNotificationIcon = (type: Notification['type']) => {
    switch (type) {
      case 'info':
        return <Info className="w-5 h-5 text-blue-500" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-warning-500" />;
      case 'success':
        return <CheckCircle className="w-5 h-5 text-success-500" />;
      case 'error':
        return <AlertTriangle className="w-5 h-5 text-danger-500" />;
      case 'update':
        return <Bell className="w-5 h-5 text-primary-500" />;
      default:
        return <Bell className="w-5 h-5 text-slate-500" />;
    }
  };

  const getNotificationStyle = (type: Notification['type']) => {
    switch (type) {
      case 'info':
        return 'notification-info';
      case 'warning':
        return 'notification-warning';
      case 'success':
        return 'notification-success';
      case 'error':
        return 'notification-error';
      case 'update':
        return 'notification-info';
      default:
        return 'notification-info';
    }
  };

  const formatTime = (date: Date) => {
    return new Intl.DateTimeFormat('en-GB', {
      hour: '2-digit',
      minute: '2-digit',
      day: 'numeric',
      month: 'short',
    }).format(date);
  };

  const filteredNotifications = notifications.filter(notification => {
    switch (activeTab) {
      case 'unread':
        return !notification.read;
      case 'all':
      default:
        return true;
    }
  });

  const unreadCount = notifications.filter(n => !n.read).length;

  const handlePreferenceUpdate = (key: keyof NotificationPreferences, value: any) => {
    const updated = { ...localPreferences, [key]: value };
    setLocalPreferences(updated);
    onUpdatePreferences(updated);
  };

  const NotificationCard = ({ notification }: { notification: Notification }) => {
    const isExpanded = expandedNotification === notification.id;
    
    return (
      <div 
        className={`notification ${getNotificationStyle(notification.type)} ${
          !notification.read ? 'ring-2 ring-primary-200' : ''
        } ${notification.actionRequired ? 'shadow-md' : ''}`}
      >
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-3 flex-1">
            {getNotificationIcon(notification.type)}
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold text-slate-800 text-responsive-sm">
                  {notification.title}
                  {!notification.read && (
                    <span className="inline-block w-2 h-2 bg-primary-500 rounded-full ml-2"></span>
                  )}
                </h3>
                <span className="text-xs text-slate-500 whitespace-nowrap ml-2">
                  {formatTime(notification.timestamp)}
                </span>
              </div>
              
              <p className={`text-sm mb-3 ${
                isExpanded ? '' : 'line-clamp-2'
              }`}>
                {notification.message}
              </p>

              {/* Action Required Badge */}
              {notification.actionRequired && (
                <div className="inline-flex items-center px-2 py-1 bg-warning-100 text-warning-800 rounded-full text-xs font-medium mb-3">
                  <Clock className="w-3 h-3 mr-1" />
                  Action Required
                </div>
              )}

              {/* Actions */}
              {notification.actions && notification.actions.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-3">
                  {notification.actions.map((action) => (
                    <button
                      key={action.id}
                      onClick={() => onExecuteAction(notification.id, action.id)}
                      className={`text-xs px-3 py-1 rounded-full font-medium transition-colors ${
                        action.type === 'primary'
                          ? 'bg-primary-500 hover:bg-primary-600 text-white'
                          : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                      }`}
                    >
                      {action.label}
                    </button>
                  ))}
                </div>
              )}

              {/* Expand/Collapse and Mark as Read */}
              <div className="flex items-center justify-between">
                <button
                  onClick={() => setExpandedNotification(
                    isExpanded ? null : notification.id
                  )}
                  className="text-xs text-slate-500 hover:text-slate-700"
                >
                  {isExpanded ? 'Show less' : 'Show more'}
                </button>
                
                {!notification.read && (
                  <button
                    onClick={() => onMarkAsRead(notification.id)}
                    className="flex items-center text-xs text-primary-600 hover:text-primary-700"
                  >
                    <Check className="w-3 h-3 mr-1" />
                    Mark as read
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const SettingsPanel = () => (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-slate-800 mb-4">
        Notification Preferences
      </h3>

      {/* Channel Preferences */}
      <div className="card">
        <h4 className="font-medium text-slate-800 mb-4">Delivery Channels</h4>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Mail className="w-5 h-5 text-slate-500" />
              <div>
                <div className="font-medium text-slate-800">Email</div>
                <div className="text-sm text-slate-600">
                  Important updates and confirmations
                </div>
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={localPreferences.email}
                onChange={(e) => handlePreferenceUpdate('email', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-slate-200 peer-focus:ring-2 peer-focus:ring-primary-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
            </label>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Smartphone className="w-5 h-5 text-slate-500" />
              <div>
                <div className="font-medium text-slate-800">SMS</div>
                <div className="text-sm text-slate-600">
                  Urgent alerts and gate changes
                </div>
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={localPreferences.sms}
                onChange={(e) => handlePreferenceUpdate('sms', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-slate-200 peer-focus:ring-2 peer-focus:ring-primary-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
            </label>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Bell className="w-5 h-5 text-slate-500" />
              <div>
                <div className="font-medium text-slate-800">Push Notifications</div>
                <div className="text-sm text-slate-600">
                  Real-time updates in the app
                </div>
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={localPreferences.push}
                onChange={(e) => handlePreferenceUpdate('push', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-slate-200 peer-focus:ring-2 peer-focus:ring-primary-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
            </label>
          </div>
        </div>
      </div>

      {/* Sound Settings */}
      <div className="card">
        <h4 className="font-medium text-slate-800 mb-4">Sound & Alerts</h4>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {localPreferences.soundEnabled ? (
              <Volume2 className="w-5 h-5 text-slate-500" />
            ) : (
              <VolumeX className="w-5 h-5 text-slate-500" />
            )}
            <div>
              <div className="font-medium text-slate-800">Sound Notifications</div>
              <div className="text-sm text-slate-600">
                Play sound for important alerts
              </div>
            </div>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={localPreferences.soundEnabled}
              onChange={(e) => handlePreferenceUpdate('soundEnabled', e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-slate-200 peer-focus:ring-2 peer-focus:ring-primary-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
          </label>
        </div>
      </div>

      {/* Quiet Hours */}
      <div className="card">
        <h4 className="font-medium text-slate-800 mb-4">Quiet Hours</h4>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium text-slate-800">Enable Quiet Hours</div>
              <div className="text-sm text-slate-600">
                Reduce non-urgent notifications during specified hours
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={localPreferences.quietHours.enabled}
                onChange={(e) => handlePreferenceUpdate('quietHours', {
                  ...localPreferences.quietHours,
                  enabled: e.target.checked
                })}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-slate-200 peer-focus:ring-2 peer-focus:ring-primary-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
            </label>
          </div>

          {localPreferences.quietHours.enabled && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Start Time
                </label>
                <input
                  type="time"
                  value={localPreferences.quietHours.start}
                  onChange={(e) => handlePreferenceUpdate('quietHours', {
                    ...localPreferences.quietHours,
                    start: e.target.value
                  })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  End Time
                </label>
                <input
                  type="time"
                  value={localPreferences.quietHours.end}
                  onChange={(e) => handlePreferenceUpdate('quietHours', {
                    ...localPreferences.quietHours,
                    end: e.target.value
                  })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <div className="mobile-container">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-responsive-2xl font-bold text-slate-800 mb-2">
          Messages & Updates
        </h1>
        <p className="text-slate-600">
          Stay informed about your journey
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="flex items-center space-x-1 mb-6 bg-slate-100 rounded-lg p-1">
        <button
          onClick={() => setActiveTab('all')}
          className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'all'
              ? 'bg-white text-slate-800 shadow-sm'
              : 'text-slate-600 hover:text-slate-800'
          }`}
        >
          <MessageCircle className="w-4 h-4 mr-2 inline" />
          All ({notifications.length})
        </button>
        <button
          onClick={() => setActiveTab('unread')}
          className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'unread'
              ? 'bg-white text-slate-800 shadow-sm'
              : 'text-slate-600 hover:text-slate-800'
          }`}
        >
          <Bell className="w-4 h-4 mr-2 inline" />
          Unread ({unreadCount})
        </button>
        <button
          onClick={() => setActiveTab('settings')}
          className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'settings'
              ? 'bg-white text-slate-800 shadow-sm'
              : 'text-slate-600 hover:text-slate-800'
          }`}
        >
          <Settings className="w-4 h-4 mr-2 inline" />
          Settings
        </button>
      </div>

      {/* Content */}
      {activeTab === 'settings' ? (
        <SettingsPanel />
      ) : (
        <div className="space-y-4">
          {filteredNotifications.length > 0 ? (
            filteredNotifications.map((notification) => (
              <NotificationCard key={notification.id} notification={notification} />
            ))
          ) : (
            <div className="text-center py-12">
              <Bell className="w-12 h-12 text-slate-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-800 mb-2">
                {activeTab === 'unread' ? 'All caught up!' : 'No messages yet'}
              </h3>
              <p className="text-slate-600">
                {activeTab === 'unread' 
                  ? 'You have no unread notifications'
                  : 'New updates will appear here'
                }
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}