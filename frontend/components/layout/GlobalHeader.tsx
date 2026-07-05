"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";

export function GlobalHeader() {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);

  // Close mobile menu when route changes
  useEffect(() => {
    setIsOpen(false);
  }, [pathname]);

  // Don't render header on dashboard routes
  if (pathname?.startsWith("/dashboard")) {
    return null;
  }

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-200/80 bg-white/90 backdrop-blur-md dark:bg-slate-900/90 dark:border-slate-800/80">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo Brand */}
          <div className="flex items-center">
            <Link href="/" className="flex items-center gap-2 text-emerald-800 hover:opacity-90 transition">
              <svg
                className="h-6 w-6 text-emerald-700"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M3 21h18" />
                <path d="M12 2v19" />
                <path d="M5 21V10l7-5 7 5v11" />
                <path d="M9 21v-4a2 2 0 0 1 4 0v4" />
              </svg>
              <span className="font-sans text-lg font-bold tracking-tight text-slate-900 dark:text-white">
                Mosque Finder
              </span>
            </Link>
          </div>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center gap-x-6 text-sm font-semibold text-slate-700 dark:text-slate-350">
            <Link href="/" className="hover:text-emerald-800 transition">
              Home
            </Link>
            <Link href="/#nearest-mosque-title" className="hover:text-emerald-800 transition">
              Mosques
            </Link>
            <Link href="/#current-prayer-title" className="hover:text-emerald-800 transition">
              Prayer Timings
            </Link>
            <Link href="/for-mosques" className="hover:text-emerald-800 transition">
              For Mosques
            </Link>
          </nav>

          {/* CTAs */}
          <div className="hidden md:flex items-center gap-4">
            <Link
              href="/mosque-registration"
              className="inline-flex min-h-10 items-center justify-center rounded-full bg-emerald-50 px-4 text-xs font-bold text-emerald-800 border border-emerald-950/10 hover:bg-emerald-100 transition"
            >
              Register Mosque
            </Link>
            <Link
              href="/login"
              className="inline-flex min-h-10 items-center justify-center rounded-full bg-emerald-800 px-5 text-xs font-bold text-white shadow-md hover:bg-emerald-900 transition"
            >
              Admin Login
            </Link>
          </div>

          {/* Mobile Hamburger Toggle */}
          <div className="flex md:hidden">
            <button
              onClick={() => setIsOpen(!isOpen)}
              type="button"
              className="inline-flex items-center justify-center rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-800 focus:ring-offset-2 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200"
              aria-controls="mobile-menu"
              aria-expanded={isOpen}
            >
              <span className="sr-only">Open main menu</span>
              {isOpen ? (
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              ) : (
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer Menu */}
      {isOpen && (
        <div className="md:hidden animate-fadeIn" id="mobile-menu">
          <div className="space-y-1.5 px-4 pb-5 pt-3 border-t border-slate-100 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-lg">
            <Link
              href="/"
              className="block rounded-xl px-4 py-2.5 text-base font-semibold text-slate-800 hover:bg-slate-50 dark:text-slate-200 dark:hover:bg-slate-800"
            >
              Home
            </Link>
            <Link
              href="/#nearest-mosque-title"
              className="block rounded-xl px-4 py-2.5 text-base font-semibold text-slate-800 hover:bg-slate-50 dark:text-slate-200 dark:hover:bg-slate-800"
            >
              Mosques
            </Link>
            <Link
              href="/#current-prayer-title"
              className="block rounded-xl px-4 py-2.5 text-base font-semibold text-slate-800 hover:bg-slate-50 dark:text-slate-200 dark:hover:bg-slate-800"
            >
              Prayer Timings
            </Link>
            <Link
              href="/for-mosques"
              className="block rounded-xl px-4 py-2.5 text-base font-semibold text-slate-800 hover:bg-slate-50 dark:text-slate-200 dark:hover:bg-slate-800"
            >
              For Mosques
            </Link>
            
            <div className="grid grid-cols-2 gap-3 pt-4 border-t border-slate-100 dark:border-slate-800 mt-3">
              <Link
                href="/mosque-registration"
                className="inline-flex min-h-12 items-center justify-center rounded-full bg-emerald-50 px-4 text-sm font-bold text-emerald-800 border border-emerald-950/10 hover:bg-emerald-100 transition text-center"
              >
                Register Mosque
              </Link>
              <Link
                href="/login"
                className="inline-flex min-h-12 items-center justify-center rounded-full bg-emerald-800 px-4 text-sm font-bold text-white hover:bg-emerald-900 transition text-center"
              >
                Admin Login
              </Link>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
