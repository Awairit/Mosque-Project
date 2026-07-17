import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import Link from "next/link";
import { GlobalHeader } from "@/components/layout/GlobalHeader";
import { env } from "@/lib/config/env";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Mosque Finder",
    template: "%s | Mosque Finder",
  },
  description:
    "Discover nearby mosques, prayer times, jamaat timings, facilities, and directions.",
  metadataBase: new URL(env.siteUrl),
};


export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#0F5F4A",
};

type RootLayoutProps = {
  children: ReactNode;
};

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en">
      <body className="flex flex-col min-h-screen">
        <GlobalHeader />
        <div className="flex-grow">{children}</div>
        <footer className="w-full border-t border-slate-200 bg-white py-6 dark:bg-slate-900 dark:border-slate-800">
          <div className="mx-auto max-w-4xl px-4 flex flex-col items-center justify-between gap-4 sm:flex-row text-xs text-slate-600 dark:text-slate-400">
            <div className="text-center sm:text-left">
              <p>© 2026 Awair_it. All rights reserved.</p>
              <p className="mt-0.5 text-[10px] text-slate-500">Designed & Developed by Awair_it</p>
            </div>
            <nav className="flex flex-wrap gap-x-6 gap-y-2 justify-center">
              <Link href="/about" className="hover:text-emerald-800 hover:underline transition-colors font-medium">About Us</Link>
              <Link href="/contact" className="hover:text-emerald-800 hover:underline transition-colors font-medium">Contact Us</Link>
              <Link href="/privacy" className="hover:text-emerald-800 hover:underline transition-colors font-medium">Privacy Policy</Link>
              <Link href="/terms" className="hover:text-emerald-800 hover:underline transition-colors font-medium">Terms of Service</Link>
            </nav>
          </div>
        </footer>
      </body>
    </html>
  );
}
