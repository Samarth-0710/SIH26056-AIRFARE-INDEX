import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import DashboardPage from '@/app/dashboard/page';
import { DataProvider } from '@/services/data-provider';

// Mock DataProvider
jest.mock('@/services/data-provider');

describe('Overview Dashboard Page', () => {
  beforeEach(() => {
    (DataProvider.getStatus as jest.Mock).mockResolvedValue({
      isDemo: true,
      isLive: false,
      lastChecked: '19:54:00',
    });

    (DataProvider.getCurrentIndex as jest.Mock).mockResolvedValue({
      data: {
        index: 112.6,
        previous_index: 110.0,
        change_percent: 2.36,
        timestamp: '2026-09-08T19:50:00Z',
        observation_date: '2026-09-08',
        booking_window: 'T+15',
        status: 'SUCCESS',
        methodology_version: 'JEVONS_SHORT_INDEX_v1.0',
        basket_version: 'BASKET_IND_TOP20_v1.0',
        weight_version: 'DGCA_PAX_WEIGHTS_2024_v1.0',
        calculation_version: '1.0.0',
        observation_set_version: 'OBS_20260908_01',
      },
      status: { isDemo: true, isLive: false },
    });

    (DataProvider.getIndexHistory as jest.Mock).mockResolvedValue({
      data: { items: [] },
      status: { isDemo: true, isLive: false },
    });

    (DataProvider.getRouteContributions as jest.Mock).mockResolvedValue({
      data: [
        {
          route: 'DEL-BOM',
          weight: 0.28,
          route_index: 118.4,
          level_contribution: 33.15,
          point_contribution: 1.34,
          percentage_share_of_change: 56.78,
        },
      ],
      status: { isDemo: true, isLive: false },
    });

    (DataProvider.getBookingWindowSnapshots as jest.Mock).mockResolvedValue({
      data: {
        'T+1': { index: 124.8, change_percent: 6.21 },
        'T+7': { index: 116.3, change_percent: 3.84 },
        'T+15': { index: 112.6, change_percent: 2.36 },
        'T+30': { index: 107.1, change_percent: 0.94 },
        'T+45': { index: 103.4, change_percent: -0.38 },
      },
      status: { isDemo: true, isLive: false },
    });

    (DataProvider.getIntelligenceEvents as jest.Mock).mockResolvedValue({
      data: [],
      status: { isDemo: true, isLive: false },
    });

    (DataProvider.getQualityMetrics as jest.Mock).mockResolvedValue({
      data: [],
      status: { isDemo: true, isLive: false },
    });

    (DataProvider.getConfidenceMetrics as jest.Mock).mockResolvedValue({
      data: {
        overall_confidence: 94,
        source_coverage: 96,
        route_coverage: 98,
        observation_volume: 'High',
        freshness: 'Excellent',
      },
      status: { isDemo: true, isLive: false },
    });
  });

  it('renders National Airfare Price Index value cleanly', async () => {
    render(<DashboardPage />);
    await waitFor(() => {
      expect(screen.getByText('National Airfare Price Index')).toBeInTheDocument();
      expect(screen.getAllByText('112.6').length).toBeGreaterThan(0);
    });
  });

  it('renders confidence meter metrics correctly', async () => {
    render(<DashboardPage />);
    await waitFor(() => {
      expect(screen.getByText('Measurement Reliability & Confidence')).toBeInTheDocument();
      expect(screen.getAllByText('94%').length).toBeGreaterThan(0);
    });
  });
});
