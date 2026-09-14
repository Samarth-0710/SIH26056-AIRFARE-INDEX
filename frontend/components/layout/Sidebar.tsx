'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Plane,
  CalendarClock,
  BrainCircuit,
  ShieldCheck,
  CheckCircle2,
  Sliders,
  BookOpen,
  Activity,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
  badge?: string;
}

const NAV_ITEMS: NavItem[] = [
  { name: 'Overview', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Route Analysis', href: '/routes', icon: Plane },
  { name: 'Booking Windows', href: '/booking-windows', icon: CalendarClock },
  { name: 'Intelligence', href: '/intelligence', icon: BrainCircuit, badge: 'AI' },
  { name: 'Data Quality', href: '/data-quality', icon: ShieldCheck },
  { name: 'Validation', href: '/validation', icon: CheckCircle2 },
  { name: 'What-If Simulator', href: '/simulator', icon: Sliders },
  { name: 'Methodology', href: '/methodology', icon: BookOpen },
];

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = React.useState(false);

  return (
    <aside
      className={cn(
        'bg-slate-900 text-slate-100 flex flex-col border-r border-slate-800 transition-all duration-300 z-30 shrink-0 select-none',
        collapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Brand Header */}
      <div className="h-16 px-4 flex items-center justify-between border-b border-slate-800 bg-slate-950/60">
        {!collapsed && (
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold shadow-md shadow-blue-500/20">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <div className="font-extrabold text-sm tracking-wider text-slate-100 flex items-center gap-1.5">
                SIH26056
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 font-mono font-medium border border-blue-500/30">IND</span>
              </div>
              <div className="text-[11px] text-slate-400 font-medium truncate max-w-[150px]">
                Airfare Price Index
              </div>
            </div>
          </div>
        )}
        {collapsed && (
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold mx-auto">
            <Activity className="w-5 h-5" />
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="text-slate-400 hover:text-slate-200 p-1.5 rounded-md hover:bg-slate-800 transition-colors hidden md:block"
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Nav List */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href || (item.href === '/dashboard' && pathname === '/');
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center px-3 py-2.5 rounded-lg text-sm font-medium transition-all group relative',
                isActive
                  ? 'bg-blue-600/90 text-white shadow-sm shadow-blue-600/30 font-semibold'
                  : 'text-slate-300 hover:bg-slate-800/80 hover:text-white'
              )}
            >
              <Icon className={cn('w-5 h-5 shrink-0', isActive ? 'text-white' : 'text-slate-400 group-hover:text-slate-200')} />
              {!collapsed && (
                <span className="ml-3 flex-1 truncate">{item.name}</span>
              )}
              {!collapsed && item.badge && (
                <span className="ml-auto text-[10px] px-1.5 py-0.5 rounded font-mono font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Official Policy Footer */}
      {!collapsed && (
        <div className="p-3 border-t border-slate-800 bg-slate-950/40 text-[11px] text-slate-400">
          <div className="font-semibold text-slate-300">Statistical Index System</div>
          <div className="text-[10px] mt-0.5 text-slate-500">Ministry of Civil Aviation / SIH26056</div>
        </div>
      )}
    </aside>
  );
}
