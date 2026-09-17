import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { Header } from '@/components/layout/Header';
import DashboardPage from '@/app/dashboard/page';
import { DataProvider } from '@/services/data-provider';
import { DataProviderStatus } from '@/types';

jest.mock('@/services/data-provider');

describe('Header & Dashboard Live Status Consistency', () => {
  beforeEach(() => {
    (DataProvider.getCurrentIndex as jest.Mock).mockResolvedValue({
      data: {
        index: 105.0,
        previous_index: 104.0,
        change_percent: 0.96,
        observation_date: '2026-09-15',
        booking_window: 'T+15',
        status: 'SUCCESS',
      },
      status: { isDemo: false, isLive: true },
    });

    (DataProvider.getIndexHistory as jest.Mock).mockResolvedValue({
      data: { items: [] },
      status: { isDemo: false, isLive: true },
    });

    (DataProvider.getRouteContributions as jest.Mock).mockResolvedValue({
      data: [],
      status: { isDemo: false, isLive: true },
    });

    (DataProvider.getBookingWindowSnapshots as jest.Mock).mockResolvedValue({
      data: null,
      status: { isDemo: false, isLive: true },
    });

    (DataProvider.getIntelligenceEvents as jest.Mock).mockResolvedValue({
      data: [],
      status: { isDemo: false, isLive: true },
    });

    (DataProvider.getQualityMetrics as jest.Mock).mockResolvedValue({
      data: {
        total_observations: 100,
        valid_observations: 95,
        anomalous_observations: 5,
        source_breakdown: {},
        observation_volume: 'High',
        freshness: 'Excellent',
      },
      status: { isDemo: false, isLive: true },
    });

    (DataProvider.getConfidenceMetrics as jest.Mock).mockResolvedValue({
      data: {
        overall_confidence: 90,
        variance_stability: 92,
        sample_adequacy: 88,
        source_diversity: 90,
      },
      status: { isDemo: false, isLive: true },
    });

    (DataProvider.getValidationResult as any) = jest.fn().mockResolvedValue({
      data: { is_reference_connected: true },
      status: { isDemo: false, isLive: true },
    });
  });

  it('both Header badge and Dashboard card show CONNECTED / LIVE API when live Ignav source is verified', async () => {
    const liveStatus: DataProviderStatus = {
      isDemo: false,
      isLive: true,
      lastChecked: '12:00:00',
      liveSource: {
        source: 'IGNAV',
        is_configured: true,
        is_connected: true,
        status: 'CONNECTED',
        message: 'Live Ignav airfare data is available.',
      },
    };

    (DataProvider.getStatus as jest.Mock).mockResolvedValue(liveStatus);
    (DataProvider.subscribeStatus as jest.Mock) = jest.fn((callback) => {
      callback(liveStatus);
      return () => {};
    });

    render(
      <div>
        <Header status={liveStatus} />
        <DashboardPage />
      </div>
    );

    await waitFor(() => {
      // Header badge
      expect(screen.getByText('LIVE API')).toBeInTheDocument();
      // Dashboard card
      expect(screen.getByText('Real live airfare data')).toBeInTheDocument();
      expect(screen.getAllByText('🟢 Connected').length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText('Live Ignav airfare data is available.')).toBeInTheDocument();
    });
  });

  it('both Header badge and Dashboard card show unconfigured/demo fallback when credentials are missing', async () => {
    const unconfiguredStatus: DataProviderStatus = {
      isDemo: false,
      isLive: true,
      lastChecked: '12:00:00',
      liveSource: {
        source: 'IGNAV',
        is_configured: false,
        is_connected: false,
        status: 'NOT_CONFIGURED',
        message: 'Live API credentials unconfigured; fallback active',
      },
    };

    (DataProvider.getStatus as jest.Mock).mockResolvedValue(unconfiguredStatus);
    (DataProvider.subscribeStatus as jest.Mock) = jest.fn((callback) => {
      callback(unconfiguredStatus);
      return () => {};
    });

    render(
      <div>
        <Header status={unconfiguredStatus} />
        <DashboardPage />
      </div>
    );

    await waitFor(() => {
      // Header badge must NOT say LIVE API
      expect(screen.queryByText('LIVE API')).not.toBeInTheDocument();
      expect(screen.getByText('DEMO DATA')).toBeInTheDocument();

      // Dashboard card shows Not demonstrated
      expect(screen.getByText('Real live airfare data')).toBeInTheDocument();
      expect(screen.getByText('🟡 Not demonstrated')).toBeInTheDocument();
      expect(screen.getByText('Live API credentials unconfigured; fallback active')).toBeInTheDocument();
    });
  });

  it('both Header badge and Dashboard card show DEGRADED when Ignav API is unreachable', async () => {
    const degradedStatus: DataProviderStatus = {
      isDemo: false,
      isLive: true,
      lastChecked: '12:00:00',
      liveSource: {
        source: 'IGNAV',
        is_configured: true,
        is_connected: false,
        status: 'DEGRADED',
        message: 'Live Ignav API unreachable; synthetic fallback active',
      },
    };

    (DataProvider.getStatus as jest.Mock).mockResolvedValue(degradedStatus);
    (DataProvider.subscribeStatus as jest.Mock) = jest.fn((callback) => {
      callback(degradedStatus);
      return () => {};
    });

    render(
      <div>
        <Header status={degradedStatus} />
        <DashboardPage />
      </div>
    );

    await waitFor(() => {
      // Header badge must NOT say LIVE API
      expect(screen.queryByText('LIVE API')).not.toBeInTheDocument();
      expect(screen.getByText('DEGRADED')).toBeInTheDocument();

      // Dashboard card shows Degraded
      expect(screen.getByText('Real live airfare data')).toBeInTheDocument();
      expect(screen.getByText('🔴 Degraded')).toBeInTheDocument();
      expect(screen.getByText('Live Ignav API unreachable; synthetic fallback active')).toBeInTheDocument();
    });
  });
});
