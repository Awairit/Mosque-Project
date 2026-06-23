"use client";

import dynamic from "next/dynamic";

// Define Types for wrapper safety
type PrayerTiming = {
  fajr_time: string;
  dhuhr_time: string;
  asr_time: string;
  maghrib_time: string;
  isha_time: string;
};

type OperatingStatus = {
  is_open: boolean;
  status_label: string;
  current_window?: string | null;
  closes_at?: string | null;
  opens_at?: string | null;
  next_prayer_name?: string | null;
  next_prayer_time?: string | null;
};

type MosquePreview = {
  id: number;
  mosque_name: string;
  city: string;
  address: string;
  latitude: number | string | null;
  longitude: number | string | null;
  women_prayer_available: boolean;
  parking_available: boolean;
  wudu_facility_available: boolean;
  wheelchair_accessible: boolean;
  prayer_timing?: PrayerTiming | null;
  operating_status?: OperatingStatus | null;
  distance?: number | null;
};

interface MosqueMapProps {
  mosques: MosquePreview[];
  userCoords: { lat: number; lon: number } | null;
  center: { lat: number; lon: number };
  onBoundsChange: (bbox: string) => void;
}

// Dynamically import Leaflet inner map with SSR disabled to prevent Server-Side DOM check issues
const MosqueMapInner = dynamic(() => import("./MosqueMapInner"), {
  ssr: false,
  loading: () => (
    <div className="flex h-[480px] w-full animate-pulse items-center justify-center rounded-2xl border border-slate-200 bg-slate-50 text-sm font-semibold text-slate-400">
      Loading interactive map details...
    </div>
  ),
});

export function MosqueMap(props: MosqueMapProps) {
  return <MosqueMapInner {...props} />;
}
