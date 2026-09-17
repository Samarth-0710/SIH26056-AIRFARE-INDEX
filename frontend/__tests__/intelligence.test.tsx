import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import IntelligencePage from '@/app/intelligence/page';
import { DataProvider } from '@/services/data-provider';

jest.mock('@/services/data-provider');

describe('Intelligence Page', () => {
  beforeEach(() => {
    (DataProvider.getStatus as jest.Mock).mockResolvedValue({
      isDemo: true,
      isLive: false,
      lastChecked: '12:00:00',
    });
  });

  it('renders intelligence page cleanly without hook errors across loading and resolved states', async () => {
    (DataProvider.getIntelligenceEvents as jest.Mock).mockResolvedValue({
      data: [
        {
          id: 1,
          event_type: 'AIRFARE_SHOCK',
          route: 'DEL-BOM',
          shock_status: 'ALERT',
          explanation: 'Sudden spike in economy fares across multiple carriers',
          affected_sources: ['OTA_ALPHA', 'OTA_BETA'],
          affected_routes: ['DEL-BOM', 'BOM-DEL'],
          model_version: 'SHOCK_DETECTOR_V2',
          event_timestamp: '2026-09-14T12:00:00Z',
          pressure_score: 85,
        },
        {
          id: 2,
          event_type: 'ANOMALY',
          route: 'DEL-BLR',
          shock_status: 'SUSPECT',
          explanation: 'Statistical anomaly in fare dispersion',
          affected_sources: ['OTA_ALPHA'],
          affected_routes: ['DEL-BLR'],
          model_version: 'ISOLATION_FOREST_V1',
          event_timestamp: '2026-09-14T11:00:00Z',
          anomaly_score: 4.5,
        },
      ],
      status: { isDemo: true, isLive: false },
    });

    render(<IntelligencePage />);

    // Wait for the page to resolve from loading to loaded state
    await waitFor(() => {
      expect(screen.getByText(/Intelligence Layer Governance/i)).toBeInTheDocument();
    });

    // Check shock card
    expect(screen.getByText('ACTIVE SHOCK ALERT')).toBeInTheDocument();
    expect(screen.getAllByText('DEL-BOM').length).toBeGreaterThan(0);

    // Check pressure rankings
    expect(screen.getByText(/Airfare Pressure Index/i)).toBeInTheDocument();
    expect(screen.getByText('85')).toBeInTheDocument();
  });
});
