'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  Home, 
  Brain, 
  Activity, 
  PlayCircle, 
  BarChart3, 
  Settings,
  Zap,
  Network,
  Bot
} from 'lucide-react';

const navigationItems = [
  {
    name: 'Executive Dashboard',
    href: '/',
    icon: Home,
    description: 'Main disruption management overview'
  },
  {
    name: 'AI Monitoring',
    href: '/ai-monitoring',
    icon: Brain,
    description: 'AI agent decision tracking'
  },
  {
    name: 'Autonomous Agents',
    href: '/autonomous-agents',
    icon: Bot,
    description: 'Live autonomous agent intelligence'
  },
  {
    name: 'Live Scenarios',
    href: '/live-scenarios',
    icon: PlayCircle,
    description: 'Real-time scenario execution'
  }
];

export default function Navigation() {
  const pathname = usePathname();

  return (
    <nav className="bg-white shadow-sm border-b border-slate-200">
      <div className="px-4 sm:px-6">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-500 rounded-lg">
              <Zap className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-slate-800">Flight Disruption AI</h1>
              <p className="text-xs text-slate-600">Autonomous Intelligence Platform</p>
            </div>
          </div>

          {/* Navigation Links */}
          <div className="hidden md:flex items-center space-x-1">
            {navigationItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-blue-100 text-blue-700 border border-blue-200'
                      : 'text-slate-600 hover:text-slate-800 hover:bg-slate-100'
                  }`}
                  title={item.description}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </div>

          {/* Mobile Navigation */}
          <div className="md:hidden">
            <select
              value={pathname}
              onChange={(e) => window.location.href = e.target.value}
              className="px-3 py-2 border border-slate-200 rounded-lg text-sm"
            >
              {navigationItems.map((item) => (
                <option key={item.href} value={item.href}>
                  {item.name}
                </option>
              ))}
            </select>
          </div>

          {/* Status Indicator */}
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-sm font-medium text-slate-700">Live System</span>
          </div>
        </div>
      </div>
    </nav>
  );
}