import type { Metadata } from 'next';
import { Inter, JetBrains_Mono } from 'next/font/google';
import './globals.css';
import { Header } from '../components/Header';
import { AuthProvider } from '../lib/auth-context';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'BHARATBUY — AI Procurement Intelligence (SIH26108)',
  description: 'Evidence-backed procurement intelligence and statutory compliance engine for Indian Standards.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable} light`}>
      <body className="bg-surface text-on-surface font-sans antialiased selection:bg-primary-fixed selection:text-on-primary-fixed">
        <AuthProvider>
          <Header />
          <main className="pt-20 pb-24 bg-surface min-h-[calc(100vh-5rem)]">
            {children}
          </main>
          <footer className="border-t border-surface-container-high bg-surface-container-low py-6 text-center text-xs text-secondary">
            <p className="font-medium text-on-surface">© 2026 Smart India Hackathon Project SIH26108 — BharatBuy AI Procurement Intelligence Engine</p>
            <p className="text-[11px] text-secondary mt-1 max-w-2xl mx-auto px-4">
              Procurement intelligence is evidence-backed decision support. Certification validity and supplier eligibility should be independently verified before buyer approval.
            </p>
          </footer>
        </AuthProvider>
      </body>
    </html>
  );
}
