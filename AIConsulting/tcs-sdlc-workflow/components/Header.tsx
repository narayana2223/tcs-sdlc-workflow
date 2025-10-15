'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Shield, DollarSign, Activity, Home, Download, PlayCircle } from 'lucide-react';

export function Header() {
  const pathname = usePathname();

  const navItems = [
    { href: '/', label: 'Workflow', icon: Home },
    { href: '/ai-operations', label: 'AI Ops', icon: Activity },
    { href: '/governance', label: 'Governance', icon: Shield },
    { href: '/cost-management', label: 'Cost Mgmt', icon: DollarSign },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/60">
      <div className="container flex h-20 items-center justify-between px-8">
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-[#E94B3C] to-[#C23729]">
              <span className="text-xl font-bold text-white">TCS</span>
            </div>
            <div>
              <h1 className="text-lg font-bold text-gray-900">
                AI-Driven SDLC Transformation
              </h1>
              <p className="text-xs text-gray-600">
                Enterprise AI Development Platform
              </p>
            </div>
          </Link>

          <nav className="flex gap-1 ml-8">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-[#E94B3C] text-white shadow-sm'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <Icon size={14} />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="flex items-center gap-4">
          <button className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50">
            <Download size={16} />
            Download PDF
          </button>
          <button className="flex items-center gap-2 rounded-lg bg-gradient-to-r from-[#E94B3C] to-[#C23729] px-4 py-2 text-sm font-medium text-white transition-opacity hover:opacity-90">
            <PlayCircle size={16} />
            Request Demo
          </button>
        </div>
      </div>
    </header>
  );
}
