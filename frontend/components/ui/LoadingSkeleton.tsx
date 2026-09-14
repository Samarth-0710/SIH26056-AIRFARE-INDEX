'use client';

import React from 'react';

export function LoadingSkeleton() {
  return (
    <div className="space-y-6 animate-pulse p-6">
      {/* Top Grid Skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-32 bg-slate-200 dark:bg-slate-800 rounded-xl"></div>
        ))}
      </div>

      {/* Main Chart Skeleton */}
      <div className="h-80 bg-slate-200 dark:bg-slate-800 rounded-xl"></div>

      {/* Grid Skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="h-64 bg-slate-200 dark:bg-slate-800 rounded-xl"></div>
        <div className="h-64 bg-slate-200 dark:bg-slate-800 rounded-xl"></div>
      </div>
    </div>
  );
}
