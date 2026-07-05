"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { apiRequest } from "@/lib/api/client";

type Activity = {
  id: number;
  action: string;
  details: string;
  time: string;
};

type DashboardStats = {
  pending_mosque_requests: number;
  approved_mosques: number;
  cities: number;
  prayer_timetable_imports: number;
  recent_activity: Activity[];
  system_status: string;
};

export default function SuperAdminDashboardHome() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchStats() {
      try {
        const data = await apiRequest<DashboardStats>({
          path: "/platform/dashboard/stats/",
          method: "GET",
        });
        setStats(data);
      } catch (err) {
        console.error("Failed to load platform stats:", err);
        setError("Could not retrieve platform statistics. Please try again.");
      } finally {
        setLoading(false);
      }
    }
    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-10 w-48 rounded bg-slate-200 dark:bg-slate-800" />
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-28 rounded-2xl bg-slate-200 dark:bg-slate-800" />
          ))}
        </div>
        <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
          <div className="h-64 rounded-2xl bg-slate-200 dark:bg-slate-800" />
          <div className="h-64 rounded-2xl bg-slate-200 dark:bg-slate-800" />
        </div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 p-6 dark:border-red-950/30 dark:bg-red-950/20">
        <h2 className="text-md font-bold text-red-800 dark:text-red-400">Connection Failure</h2>
        <p className="mt-2 text-sm text-red-700 dark:text-red-300">{error || "Failed to connect to the administration API."}</p>
      </div>
    );
  }

  const statCards = [
    {
      label: "Pending Approvals",
      value: stats.pending_mosque_requests,
      color: "text-amber-600 bg-amber-50 dark:text-amber-400 dark:bg-amber-950/30",
      description: "Mosques awaiting approval",
      icon: (
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      ),
    },
    {
      label: "Approved Mosques",
      value: stats.approved_mosques,
      color: "text-emerald-700 bg-emerald-50 dark:text-emerald-400 dark:bg-emerald-950/30",
      description: "Verified active mosques",
      icon: (
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
      ),
    },
    {
      label: "Active Cities",
      value: stats.cities,
      color: "text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-950/30",
      description: "Cities mapped for prayers",
      icon: (
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
        </svg>
      ),
    },
    {
      label: "Timetable Imports",
      value: stats.prayer_timetable_imports,
      color: "text-purple-600 bg-purple-50 dark:text-purple-400 dark:bg-purple-950/30",
      description: "Import logs & active feeds",
      icon: (
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
      ),
    },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">Platform Control Panel</h1>
        <p className="text-sm text-slate-500 mt-1">Operational status and system metrics overview.</p>
      </div>

      {/* Grid of Metric stats cards */}
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {statCards.map((card, idx) => (
          <div
            key={idx}
            className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm hover:shadow transition-shadow dark:border-slate-800 dark:bg-slate-900"
          >
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-slate-500">{card.label}</span>
              <div className={`rounded-lg p-2 ${card.color}`}>{card.icon}</div>
            </div>
            <div className="mt-4">
              <span className="text-3xl font-bold text-slate-900 dark:text-white">{card.value}</span>
              <p className="text-[11px] font-medium text-slate-400 mt-1">{card.description}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Primary Panels section (Layout Split) */}
      <div className="grid gap-6 lg:grid-cols-[2fr_1fr] items-start">
        {/* Recent Platform Activity */}
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">Recent Admin Activity</h3>
            <span className="inline-flex rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-400">
              Live Feed
            </span>
          </div>

          <div className="mt-4 divide-y divide-slate-100 dark:divide-slate-800">
            {stats.recent_activity.length > 0 ? (
              stats.recent_activity.map((activity) => (
                <div key={activity.id} className="py-3.5 first:pt-0 last:pb-0 flex items-start gap-4">
                  <div className="mt-1 flex h-2 w-2 rounded-full bg-emerald-500" />
                  <div className="flex-grow min-w-0">
                    <div className="flex items-center justify-between gap-4">
                      <p className="text-xs font-bold text-slate-900 dark:text-white truncate">{activity.action}</p>
                      <span className="text-[10px] font-medium text-slate-400 shrink-0">{activity.time}</span>
                    </div>
                    <p className="text-xs text-slate-500 mt-1 line-clamp-1">{activity.details}</p>
                  </div>
                </div>
              ))
            ) : (
              <div className="py-10 text-center text-xs text-slate-500 dark:text-slate-450">
                No recent activity
              </div>
            )}
          </div>
        </section>

        {/* Quick Actions Panel */}
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <h3 className="text-sm font-bold text-slate-900 dark:text-white pb-4 border-b border-slate-100 dark:border-slate-800">
            Quick Actions
          </h3>

          <div className="mt-4 space-y-2.5">
            <Link
              href="/super-admin/dashboard/mosques"
              className="flex items-center justify-between rounded-xl border border-slate-100 p-3.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors dark:border-slate-800 dark:text-slate-300 dark:hover:bg-slate-800/50"
            >
              <span>Approve Mosque Requests</span>
              <svg className="h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </Link>

            <Link
              href="/super-admin/dashboard/cities"
              className="flex items-center justify-between rounded-xl border border-slate-100 p-3.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors dark:border-slate-800 dark:text-slate-300 dark:hover:bg-slate-800/50"
            >
              <span>Add New City</span>
              <svg className="h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </Link>

            <Link
              href="/super-admin/dashboard/timetables"
              className="flex items-center justify-between rounded-xl border border-slate-100 p-3.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors dark:border-slate-800 dark:text-slate-300 dark:hover:bg-slate-800/50"
            >
              <span>Upload Prayer Timetable</span>
              <svg className="h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </Link>

            <Link
              href="/super-admin/dashboard/cities"
              className="flex items-center justify-between rounded-xl border border-slate-100 p-3.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors dark:border-slate-800 dark:text-slate-300 dark:hover:bg-slate-800/50"
            >
              <span>Manage Cities</span>
              <svg className="h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </Link>

            <Link
              href="/super-admin/dashboard/settings"
              className="flex items-center justify-between rounded-xl border border-slate-100 p-3.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors dark:border-slate-800 dark:text-slate-300 dark:hover:bg-slate-800/50"
            >
              <span>Platform Settings</span>
              <svg className="h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          </div>
        </section>
      </div>
    </div>
  );
}
