import './globals.css';
import type { Metadata } from 'next';
import { Sidebar } from '@/components/layout/Sidebar';
import { Header } from '@/components/layout/Header';
import { DataProvider } from '@/services/data-provider';

export const metadata: Metadata = {
  title: 'SIH26056 — Real-Time Airfare Price Index for India',
  description: 'Official Jevons airfare price index, route contributions, advance booking windows, and policy intelligence dashboard.',
};

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Probe backend status for initial render
  const status = await DataProvider.getStatus().catch(() => ({
    isDemo: true,
    isLive: false,
    lastChecked: new Date().toLocaleTimeString(),
  }));

  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-row overflow-hidden font-sans">
        <Sidebar />
        <div className="flex-1 flex flex-col min-w-0 h-screen overflow-hidden">
          <Header status={status} />
          <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 bg-slate-50 dark:bg-slate-950">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
