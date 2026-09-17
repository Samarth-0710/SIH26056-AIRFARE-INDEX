import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import ValidationPage from '@/app/validation/page';
import { DataProvider } from '@/services/data-provider';

jest.mock('@/services/data-provider');

describe('Validation Benchmark Page', () => {
  beforeEach(() => {
    (DataProvider.getStatus as jest.Mock).mockResolvedValue({
      isDemo: true,
      isLive: false,
      lastChecked: '12:00:00',
    });
  });

  it('renders connected MoSPI status badge and metadata when reference is connected', async () => {
    (DataProvider.getValidationResult as jest.Mock).mockResolvedValue({
      data: {
        period: '2026-08-15 to 2026-09-14',
        calculated_index: 104.96,
        reference_index: 135.49,
        absolute_difference: 30.53,
        percentage_difference: -22.53,
        correlation: null,
        is_reference_connected: true,
        reference_name: 'MoSPI e-Sankhyiki CPI Airfare (Base 2024 = 100, 20 Monthly Records)',
        status: 'VALIDATED',
        metrics: [
          {
            metric: 'Official MoSPI Reference Link',
            value: 'Connected (20 records)',
            status: 'PASS',
            description: 'Direct programmatic ingestion of MoSPI CPI item 07.3.3.1.2.01',
          },
        ],
        history: [],
        reference_dataset_details: {
          name: 'MoSPI e-Sankhyiki CPI Airfare',
          source: 'MoSPI e-Sankhyiki',
          item: 'Airfare',
          item_code: '07.3.3.1.2.01',
          base_year: 2024,
          frequency: 'MONTHLY',
          state: 'All India',
          sector: 'Combined',
          connected: true,
          records: 20,
          first_date: '2025-01-01',
          latest_date: '2026-08-01',
          latest_cpi: 135.49,
        },
        alignment: {
          overlapping_months: 1,
          status: 'CONNECTED',
          aligned_months: ['2026-08'],
        },
        comparison: {
          reference_month: '2026-08',
          our_monthly_index: 106.0,
          mospi_monthly_index: 135.49,
          absolute_difference: 29.49,
          percentage_difference: -21.76,
          rebasing_method: 'Rebased to common base 100.0 at reference month (2026-08)',
          our_rebased_index: 100.0,
          mospi_rebased_index: 100.0,
        },
        movement: {
          our_mom_change: null,
          mospi_mom_change: null,
          absolute_difference: null,
        },
        correlation_details: {
          value: null,
          status: 'INSUFFICIENT_OVERLAP',
          minimum_required_months: 3,
          description: 'Pearson correlation requires >= 3 overlapping monthly points (currently 1).',
        },
        monthly_series: [
          {
            month: '2025-01',
            our_monthly_index: null,
            mospi_cpi: 115.05,
            our_rebased: null,
            mospi_rebased: 84.91,
            status: 'REFERENCE_ONLY',
          },
          {
            month: '2026-08',
            our_monthly_index: 106.0,
            mospi_cpi: 135.49,
            our_rebased: 100.0,
            mospi_rebased: 100.0,
            status: 'ALIGNED',
          },
        ],
      },
      status: { isDemo: true, isLive: false },
    });

    render(<ValidationPage />);

    // Wait for the connected badge
    await waitFor(() => {
      expect(screen.getByText('🟢 Connected')).toBeInTheDocument();
    });

    // Verify dataset code
    expect(screen.getByText('07.3.3.1.2.01')).toBeInTheDocument();

    // Verify observations count
    expect(screen.getByText('20')).toBeInTheDocument();
  });
});
