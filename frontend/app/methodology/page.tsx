'use client';

import React from 'react';
import { BookOpen, Layers, Activity } from 'lucide-react';

const STEPS = [
  {
    step: '01',
    title: 'Data Collection',
    owner: "Kumuda's Module (`data-collection`)",
    desc: 'Automated multi-source collection of permitted domestic flight fare events from OTAs, meta-search engines, and direct APIs with crawl timestamps and provenance tracking.',
  },
  {
    step: '02',
    title: 'Fare Normalization',
    owner: "Hindu's Module (`data-quality`)",
    desc: 'Standardizes fare components (base fare, mandatory taxes, fees) into a uniform comparable fare in INR. Normalizes cabin class, baggage allowance, and flight numbers.',
  },
  {
    step: '03',
    title: 'Data Quality & Filtering',
    owner: "Hindu's Module (`data-quality`)",
    desc: 'Filters out invalid records, negative/zero fares, duplicate scrapes, and statistical outliers before passing data to the statistical index engine.',
  },
  {
    step: '04',
    title: 'Comparable Fare Fingerprinting',
    owner: "Samarth's Module (`statistical-engine`)",
    desc: 'Generates a SHA-256 constant-quality fingerprint matching identical flights across period t-1 and period t based on route, airline, flight number, departure slot, and cabin class.',
  },
  {
    step: '05',
    title: 'Price Relatives Calculation',
    owner: "Samarth's Module (`statistical-engine`)",
    desc: 'Computes period-to-period price relatives R_i = P_{i,t} / P_{i,t-1} for matched flight pairs.',
  },
  {
    step: '06',
    title: 'Jevons Elementary Index',
    owner: "Samarth's Module (`statistical-engine`)",
    desc: 'Calculates the unweighted geometric mean of price relatives for each route and booking window slice.',
  },
  {
    step: '07',
    title: 'Route-Level Indices',
    owner: "Samarth's Module (`statistical-engine`)",
    desc: 'Aggregates elementary indices into corridor-specific time series for each of the 20 major domestic corridors.',
  },
  {
    step: '08',
    title: 'Booking Window Segregation',
    owner: "Samarth's Module (`statistical-engine`)",
    desc: 'Strictly segregates observations into T+1, T+7, T+15, T+30, and T+45 advance purchase horizons without cross-window mixing.',
  },
  {
    step: '09',
    title: 'Prescribed Weighted Aggregation',
    owner: "Samarth's Module (`statistical-engine`)",
    desc: 'Applies official DGCA passenger traffic volume weights (w_r) to aggregate route indices into composite national indices.',
  },
  {
    step: '10',
    title: 'National Airfare Price Index',
    owner: "Samarth's Module (`statistical-engine`)",
    desc: 'Produces the official aggregate National Index: I_national = sum(w_r * I_r).',
  },
  {
    step: '11',
    title: 'AI/ML Intelligence Layer',
    owner: "Harshitha's Module (`intelligence`)",
    desc: 'Runs isolation forest anomaly detection, shock identification algorithms, and pressure rankings on top of the calculated statistical output.',
  },
  {
    step: '12',
    title: '30-Day Backtest & Validation',
    owner: "Samarth's Module (`statistical-engine`)",
    desc: 'Validates index stability against external DGCA/MoSPI benchmarks using Pearson correlation, MAE, RMSE, directional accuracy, and stability metrics.',
  },
];

export default function MethodologyPage() {
  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Title & Metadata Banner */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm space-y-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-blue-600/10 text-blue-600 dark:text-blue-400 flex items-center justify-center">
            <BookOpen className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-slate-900 dark:text-slate-100">
              Official Methodology &amp; Calculation Architecture
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">
              Comprehensive statistical index methodology breakdown for SIH26056
            </p>
          </div>
        </div>

        {/* Version Metadata Pills */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-3 border-t border-slate-100 dark:border-slate-800 text-xs font-mono">
          <div className="p-2.5 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200/80 dark:border-slate-800">
            <span className="text-slate-400 text-[10px]">Methodology Version</span>
            <div className="font-bold text-blue-600 dark:text-blue-400">JEVONS_SHORT_INDEX_v1.0</div>
          </div>
          <div className="p-2.5 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200/80 dark:border-slate-800">
            <span className="text-slate-400 text-[10px]">Route Basket Version</span>
            <div className="font-bold text-slate-900 dark:text-slate-100">BASKET_IND_TOP20_v1.0</div>
          </div>
          <div className="p-2.5 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200/80 dark:border-slate-800">
            <span className="text-slate-400 text-[10px]">Weight Dataset</span>
            <div className="font-bold text-slate-900 dark:text-slate-100">DGCA_PAX_WEIGHTS_2024</div>
          </div>
          <div className="p-2.5 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200/80 dark:border-slate-800">
            <span className="text-slate-400 text-[10px]">Engine Version</span>
            <div className="font-bold text-emerald-600 dark:text-emerald-400">v1.0.0 (Authoritative)</div>
          </div>
        </div>
      </div>

      {/* Core Formulas Callout Box */}
      <div className="bg-slate-900 text-slate-100 border border-slate-800 rounded-xl p-6 shadow-sm space-y-4 font-mono">
        <h3 className="text-sm font-bold text-blue-400 uppercase tracking-wider flex items-center gap-2">
          <Activity className="w-4 h-4" />
          Authoritative Mathematical Formulas
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="p-4 bg-slate-950 rounded-lg border border-slate-800 space-y-2">
            <div className="text-slate-400 font-bold">1. Jevons Elementary Index Formula:</div>
            <div className="text-blue-300 text-sm font-extrabold p-2 bg-slate-900/80 rounded text-center border border-slate-800">
              {'I_{r,w} = ( \\prod_{i=1}^{n} \\frac{P_{i,t}}{P_{i,t-1}} )^{1/n} \\times 100.0'}
            </div>
            <p className="text-[11px] text-slate-400 font-sans">
              Unweighted geometric mean of price relatives across matched comparable flight pairs. Satisfies time reversal test.
            </p>
          </div>

          <div className="p-4 bg-slate-950 rounded-lg border border-slate-800 space-y-2">
            <div className="text-slate-400 font-bold">2. National Composite Aggregate Formula:</div>
            <div className="text-emerald-300 text-sm font-extrabold p-2 bg-slate-900/80 rounded text-center border border-slate-800">
              {'I_{t}^{\\text{national}} = \\sum_{r \\in \\text{Routes}} w_r \\cdot I_{r,t}'}
            </div>
            <p className="text-[11px] text-slate-400 font-sans">
              Prescribed weighted Young-type aggregation using fixed DGCA passenger volume weights where sum(w_r) = 1.0.
            </p>
          </div>
        </div>
      </div>

      {/* 12-Step Pipeline Walkthrough */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm space-y-6">
        <div className="border-b border-slate-100 dark:border-slate-800 pb-3">
          <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Layers className="w-5 h-5 text-blue-600" />
            12-Step End-to-End Pipeline Breakdown
          </h3>
          <p className="text-xs text-slate-500 font-medium">
            Detailed workflow from raw fare scraping to statistical aggregation and AI intelligence
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {STEPS.map((s) => (
            <div
              key={s.step}
              className="p-4 bg-slate-50 dark:bg-slate-800/40 rounded-xl border border-slate-200/80 dark:border-slate-800 space-y-1.5"
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-extrabold text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/60 px-2 py-0.5 rounded border border-blue-200 dark:border-blue-800">
                  STEP {s.step}
                </span>
                <span className="text-[10px] text-slate-500 font-mono">{s.owner}</span>
              </div>
              <h4 className="font-bold text-sm text-slate-900 dark:text-slate-100">{s.title}</h4>
              <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">{s.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
