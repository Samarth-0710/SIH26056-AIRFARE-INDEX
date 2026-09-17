import { formatIndex, formatPercent, formatNumber, toNumber, formatDate, formatDateTime } from '@/lib/utils';

describe('lib/utils formatting and conversion helpers', () => {
  describe('toNumber', () => {
    it('returns numbers as-is', () => {
      expect(toNumber(102.5)).toBe(102.5);
      expect(toNumber(0)).toBe(0);
      expect(toNumber(-15.2)).toBe(-15.2);
    });

    it('parses valid numeric strings', () => {
      expect(toNumber('102.5000')).toBe(102.5);
      expect(toNumber('0')).toBe(0);
      expect(toNumber('-3.14')).toBe(-3.14);
      expect(toNumber('  42.5  ')).toBe(42.5);
    });

    it('returns null for empty, null, or undefined values', () => {
      expect(toNumber(null)).toBeNull();
      expect(toNumber(undefined)).toBeNull();
      expect(toNumber('')).toBeNull();
      expect(toNumber('   ')).toBeNull();
    });

    it('returns null for non-numeric strings or special values', () => {
      expect(toNumber('N/A')).toBeNull();
      expect(toNumber('invalid')).toBeNull();
      expect(toNumber(NaN)).toBeNull();
      expect(toNumber(Infinity)).toBeNull();
      expect(toNumber(-Infinity)).toBeNull();
      expect(toNumber({})).toBeNull();
    });
  });

  describe('formatIndex', () => {
    it('formats numbers to 1 decimal place', () => {
      expect(formatIndex(102.5)).toBe('102.5');
      expect(formatIndex(100)).toBe('100.0');
      expect(formatIndex(0)).toBe('0.0');
    });

    it('formats numeric strings to 1 decimal place without throwing TypeError', () => {
      expect(formatIndex('102.5000')).toBe('102.5');
      expect(formatIndex('98.44')).toBe('98.4');
      expect(formatIndex('0')).toBe('0.0');
    });

    it('returns "N/A" for null, undefined, empty, or invalid input', () => {
      expect(formatIndex(null)).toBe('N/A');
      expect(formatIndex(undefined)).toBe('N/A');
      expect(formatIndex('')).toBe('N/A');
      expect(formatIndex('abc')).toBe('N/A');
      expect(formatIndex(NaN)).toBe('N/A');
    });
  });

  describe('formatPercent', () => {
    it('formats positive and negative numbers with signs', () => {
      expect(formatPercent(2.36)).toBe('+2.4%');
      expect(formatPercent(-1.52)).toBe('-1.5%');
      expect(formatPercent(0)).toBe('0.0%');
    });

    it('formats numeric strings safely', () => {
      expect(formatPercent('3.5000')).toBe('+3.5%');
      expect(formatPercent('-4.2')).toBe('-4.2%');
    });

    it('respects includeSign = false', () => {
      expect(formatPercent(2.36, false)).toBe('2.4%');
      expect(formatPercent(-1.52, false)).toBe('1.5%');
    });

    it('returns "N/A" for null, undefined, empty, or invalid input', () => {
      expect(formatPercent(null)).toBe('N/A');
      expect(formatPercent(undefined)).toBe('N/A');
      expect(formatPercent('')).toBe('N/A');
      expect(formatPercent('invalid')).toBe('N/A');
    });
  });

  describe('formatNumber', () => {
    it('formats numbers with custom decimals', () => {
      expect(formatNumber(3.8438, 2)).toBe('3.84');
      expect(formatNumber(3.8438, 4)).toBe('3.8438');
      expect(formatNumber('3.8438', 2)).toBe('3.84');
      expect(formatNumber(null)).toBe('N/A');
      expect(formatNumber(undefined)).toBe('N/A');
      expect(formatNumber('invalid')).toBe('N/A');
    });
  });

  describe('formatDate and formatDateTime', () => {
    it('formats dates cleanly', () => {
      const formatted = formatDate('2026-09-14');
      expect(typeof formatted).toBe('string');
      expect(formatted).not.toBe('');
    });

    it('handles invalid dates gracefully', () => {
      expect(formatDate('not-a-date')).toBe('not-a-date');
      expect(formatDateTime('not-a-date')).toBe('not-a-date');
    });
  });
});
