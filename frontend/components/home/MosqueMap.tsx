"use client";

import { memo } from "react";
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
  separate_women_entrance?: boolean;
  parking_available: boolean;
  wudu_facility_available: boolean;
  wheelchair_accessible: boolean;
  drinking_water_available?: boolean;
  washrooms_available?: boolean;
  library_available?: boolean;
  quran_classes_available?: boolean;
  hifz_program_available?: boolean;
  nikah_service_available?: boolean;
  muslim_burial_ground_available?: boolean;
  community_hall_available?: boolean;
  ramadan_iftar_available?: boolean;
  eid_prayer_ground_available?: boolean;
  zakat_collection_available?: boolean;
  funeral_prayer_facility_available?: boolean;
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
    <div className="flex h-[320px] sm:h-[400px] md:h-[480px] w-full animate-pulse items-center justify-center rounded-2xl border border-slate-200 bg-slate-50 text-sm font-semibold text-slate-400">
      Loading interactive map details...
    </div>
  ),
});

export const MosqueMap = memo(function MosqueMap(props: MosqueMapProps) {
  return <MosqueMapInner {...props} />;
});
