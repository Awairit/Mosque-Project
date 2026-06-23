"use client";

import { useEffect, useMemo } from "react";
import { MapContainer, TileLayer, Marker, Popup, useMap, useMapEvents } from "react-leaflet";
import L from "leaflet";
import Link from "next/link";
import { apiRequest } from "@/lib/api/client";

// Define Types
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

interface MosqueMapInnerProps {
  mosques: MosquePreview[];
  userCoords: { lat: number; lon: number } | null;
  center: { lat: number; lon: number };
  onBoundsChange: (bbox: string) => void;
}

// Vector Markers
const openIcon = L.divIcon({
  className: "custom-leaflet-marker-open",
  html: `<div class="w-8 h-8 flex items-center justify-center bg-emerald-800 rounded-full border-2 border-white shadow-lg text-white font-bold text-lg hover:scale-110 transition-transform">🕌</div>`,
  iconSize: [32, 32],
  iconAnchor: [16, 16],
});

const closedIcon = L.divIcon({
  className: "custom-leaflet-marker-closed",
  html: `<div class="w-8 h-8 flex items-center justify-center bg-rose-600 rounded-full border-2 border-white shadow-lg text-white font-bold text-lg hover:scale-110 transition-transform">🕌</div>`,
  iconSize: [32, 32],
  iconAnchor: [16, 16],
});

const userIcon = L.divIcon({
  className: "custom-leaflet-marker-user",
  html: `<div class="relative flex h-5 w-5"><span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span><span class="relative inline-flex rounded-full h-5 w-5 bg-blue-600 border-2 border-white shadow-md"></span></div>`,
  iconSize: [20, 20],
  iconAnchor: [10, 10],
});

// Map Controller for Center syncing
function MapCenterController({ center }: { center: { lat: number; lon: number } }) {
  const map = useMap();
  useEffect(() => {
    if (center.lat && center.lon) {
      map.setView([center.lat, center.lon], map.getZoom());
    }
  }, [center, map]);
  return null;
}

// Map Event Listener for Bounding Box bounds updates
function MapBoundsUpdater({ onBoundsChange }: { onBoundsChange: (bbox: string) => void }) {
  const map = useMapEvents({
    moveend: () => {
      const bounds = map.getBounds();
      const sw = bounds.getSouthWest();
      const ne = bounds.getNorthEast();
      onBoundsChange(`${sw.lat},${sw.lng},${ne.lat},${ne.lng}`);
    },
    zoomend: () => {
      const bounds = map.getBounds();
      const sw = bounds.getSouthWest();
      const ne = bounds.getNorthEast();
      onBoundsChange(`${sw.lat},${sw.lng},${ne.lat},${ne.lng}`);
    },
  });

  // Fetch initial bounds on mount
  useEffect(() => {
    const bounds = map.getBounds();
    const sw = bounds.getSouthWest();
    const ne = bounds.getNorthEast();
    onBoundsChange(`${sw.lat},${sw.lng},${ne.lat},${ne.lng}`);
  }, [map, onBoundsChange]);

  return null;
}

export default function MosqueMapInner({
  mosques,
  userCoords,
  center,
  onBoundsChange,
}: MosqueMapInnerProps) {
  
  const formatTimeTo12Hour = (timeStr?: string | null) => {
    if (!timeStr) return "";
    const parts = timeStr.split(":");
    if (parts.length < 2) return timeStr;
    let hour = parseInt(parts[0], 10);
    const minute = parts[1];
    const ampm = hour >= 12 ? "PM" : "AM";
    hour = hour % 12;
    hour = hour ? hour : 12;
    return `${hour}:${minute} ${ampm}`;
  };

  const handleNavigateNow = (m: MosquePreview) => {
    if (m.latitude === null || m.longitude === null) return;
    const isiOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
    if (isiOS) {
      window.open(`maps://?daddr=${m.latitude},${m.longitude}&dirflg=d`, "_blank");
    } else {
      window.open(`https://www.google.com/maps/dir/?api=1&destination=${m.latitude},${m.longitude}&travelmode=driving`, "_blank");
    }
  };

  const formatDistance = (meters?: number | null) => {
    if (meters === undefined || meters === null) return "";
    if (meters < 1000) {
      return `${Math.round(meters)}m`;
    }
    return `${(meters / 1000).toFixed(1)} km`;
  };

  return (
    <div className="relative h-[480px] w-full overflow-hidden rounded-2xl border border-slate-900/10 shadow-lg">
      <MapContainer
        center={[center.lat, center.lon]}
        zoom={13}
        className="h-full w-full"
        style={{ zIndex: 1 }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
        />

        {/* User Current Location Marker */}
        {userCoords && (
          <Marker position={[userCoords.lat, userCoords.lon]} icon={userIcon}>
            <Popup>
              <div className="text-xs font-semibold text-slate-800">You are here</div>
            </Popup>
          </Marker>
        )}

        {/* Mosque Markers */}
        {mosques.map((m) => {
          if (m.latitude === null || m.longitude === null) return null;
          const latNum = typeof m.latitude === "string" ? parseFloat(m.latitude) : m.latitude;
          const lonNum = typeof m.longitude === "string" ? parseFloat(m.longitude) : m.longitude;
          if (isNaN(latNum) || isNaN(lonNum)) return null;

          const isOpen = m.operating_status?.is_open ?? false;
          const icon = isOpen ? openIcon : closedIcon;

          return (
            <Marker key={m.id} position={[latNum, lonNum]} icon={icon}>
              <Popup>
                <div className="flex flex-col gap-1.5 p-0.5 text-xs leading-normal" style={{ minWidth: "180px" }}>
                  <div className="font-bold text-slate-950">{m.mosque_name}</div>
                  
                  <div className="flex items-center gap-2">
                    <span
                      className={`inline-block rounded px-1.5 py-0.5 text-[10px] font-bold ${
                        isOpen ? "bg-emerald-50 text-emerald-800" : "bg-red-50 text-red-800"
                      }`}
                    >
                      {m.operating_status?.status_label || "Closed"}
                    </span>
                    {m.distance !== undefined && m.distance !== null && (
                      <span className="font-medium text-slate-500">{formatDistance(m.distance)} away</span>
                    )}
                  </div>

                  {m.operating_status?.next_prayer_name && m.operating_status.next_prayer_time && (
                    <div className="text-[10px] text-slate-600">
                      Next: <span className="font-bold">{m.operating_status.next_prayer_name}</span> at{" "}
                      <span className="font-mono">{formatTimeTo12Hour(m.operating_status.next_prayer_time)}</span>
                    </div>
                  )}

                  <div className="mt-1 flex items-center justify-between border-t border-slate-100 pt-1.5">
                    <Link
                      href={`/mosque/${m.id}`}
                      className="font-semibold text-emerald-850 hover:underline"
                    >
                      View Profile
                    </Link>
                    <button
                      type="button"
                      onClick={() => handleNavigateNow(m)}
                      className="rounded bg-emerald-800 px-2 py-0.5 font-bold text-white hover:bg-emerald-900 transition-colors"
                    >
                      Navigate Now
                    </button>
                  </div>
                </div>
              </Popup>
            </Marker>
          );
        })}

        <MapCenterController center={center} />
        <MapBoundsUpdater onBoundsChange={onBoundsChange} />
      </MapContainer>
    </div>
  );
}
