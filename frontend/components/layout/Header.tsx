'use client';

import React from 'react';
import {
  Clock,
  Wifi,
  WifiOff,
  Sun,
  Moon,
  Database,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';
import { DataProviderStatus } from '@/types';
import { DataProvider } from '@/services/data-provider';
import { cn } from '@/lib/utils';

interface HeaderProps {
  status?: DataProviderStatus;
  onRefresh?: () => void;
}

export function Header({ status: initialStatus }: HeaderProps) {
  const [theme, setTheme] = React.useState<'light' | 'dark'>('light');
  const [mounted, setMounted] = React.useState(false);
  const [currentStatus, setCurrentStatus] = React.useState<DataProviderStatus | undefined>(initialStatus);

  React.useEffect(() => {
    setMounted(true);
    if (document.documentElement.classList.contains('dark')) {
      setTheme('dark');
    }

    // Subscribe to DataProvider runtime status updates
    const unsubscribe = DataProvider.subscribeStatus((newStatus) => {
      setCurrentStatus(newStatus);
    });

    return () => {
      unsubscribe();
    };
  }, []);

  React.useEffect(() => {
    if (initialStatus) {
      setCurrentStatus(initialStatus);
    }
  }, [initialStatus]);

  const toggleTheme = () => {
    const nextTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(nextTheme);
    if (nextTheme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  const isDemo = currentStatus ? currentStatus.isDemo : true;
  const lastChecked = currentStatus?.lastChecked || new Date().toLocaleTimeString();
  const isLiveApiConnected = Boolean(!isDemo && currentStatus?.liveSource?.is_connected);
  const liveSourceStatus = currentStatus?.liveSource?.status;
  const isDegraded = Boolean(!isDemo && (liveSourceStatus === 'DEGRADED' || liveSourceStatus === 'ERROR'));

  return (
    <header className="h-16 px-6 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between z-20 shrink-0 shadow-sm">
      {/* Title & Scope */}
      <div className="flex items-center space-x-3">
        <div>
          <h1 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            Real-Time Airfare Price Index for India
            <span className="text-[11px] font-mono font-medium px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
              NATIONAL BASKET
            </span>
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 font-medium hidden sm:block">
            Official Jevons / Short-Index Aggregate • Policy Analytical Dashboard
          </p>
        </div>
      </div>

      {/* Meta Indicators & Controls */}
      <div className="flex items-center space-x-4 text-xs font-medium">
        {/* Data Timestamp */}
        <div className="hidden md:flex items-center space-x-1.5 text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-800/60 px-3 py-1.5 rounded-md border border-slate-200 dark:border-slate-700">
          <Clock className="w-3.5 h-3.5 text-slate-400" />
          <span>Updated: <span className="font-mono font-semibold">{lastChecked}</span></span>
        </div>

        {/* Backend / Live Source Status Badge */}
        <div
          className={cn(
            'flex items-center space-x-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border transition-all',
            isLiveApiConnected
              ? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/30'
              : isDegraded
              ? 'bg-rose-500/10 text-rose-700 dark:text-rose-400 border-rose-500/30'
              : 'bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/30'
          )}
        >
          {isLiveApiConnected ? (
            <>
              <Wifi className="w-3.5 h-3.5 text-emerald-500" />
              <span>LIVE API</span>
            </>
          ) : isDegraded ? (
            <>
              <AlertTriangle className="w-3.5 h-3.5 text-rose-500" />
              <span>DEGRADED</span>
            </>
          ) : (
            <>
              <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
              <span>DEMO DATA</span>
            </>
          )}
        </div>

        {/* Theme Toggle */}
        {mounted && (
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
            title={`Switch to ${theme === 'light' ? 'Dark' : 'Light'} Mode`}
          >
            {theme === 'light' ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4 text-amber-400" />}
          </button>
        )}
      </div>
    </header>
  );
}
