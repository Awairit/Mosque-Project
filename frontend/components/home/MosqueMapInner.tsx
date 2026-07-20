"use client";

// leaflet.css is imported here — NOT in globals.css — so it is only delivered
// to browsers when this component (the interactive map) is actually rendered.
// This file is loaded via `dynamic(..., { ssr: false })` in MosqueMap.tsx,
// which means Next.js code-splits it into its own chunk. The CSS import here
// travels with that chunk — eliminating the 72 KB Leaflet stylesheet cost on
// all non-map routes (login, mosque detail, about, city page, etc.).
import "leaflet/dist/leaflet.css";

import { useEffect, useMemo, useRef, useState, memo } from "react";
import { MapContainer, TileLayer, Marker, Popup, useMap, useMapEvents } from "react-leaflet";
import L from "leaflet";
import Link from "next/link";
import { apiRequest } from "@/lib/api/client";
import { formatDistance, formatTimeTo12Hour, formatRelativeTime } from "@/lib/utils/formatters";
import { getPreviewFacilities } from "@/lib/constants/facilities";

// Define Types
type PrayerTiming = {
  fajr_time: string;
  dhuhr_time: string;
  asr_time: string;
  maghrib_time: string;
  isha_time: string;
  /** ISO 8601 UTC timestamp: when congregation timings were last saved. */
  updated_at?: string | null;
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

// MapInstanceSelector to fetch Map instance reference
function MapInstanceSelector({ setMapInstance }: { setMapInstance: (map: L.Map) => void }) {
  const map = useMap();
  useEffect(() => {
    if (map) {
      setMapInstance(map);
    }
  }, [map, setMapInstance]);
  return null;
}

const MosqueMapInner = memo(function MosqueMapInner({
  mosques,
  userCoords,
  center,
  onBoundsChange,
}: MosqueMapInnerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [mapInstance, setMapInstance] = useState<L.Map | null>(null);
  const [showDesktopWarning, setShowDesktopWarning] = useState(false);
  const [showMobileWarning, setShowMobileWarning] = useState(false);
  const [isMac, setIsMac] = useState(false);

  const desktopTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const mobileTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isDesktopWarningActive = useRef(false);
  const isMobileWarningActive = useRef(false);

  useEffect(() => {
    const checkMac = () => {
      if (typeof window === "undefined" || !window.navigator) return false;
      const nav = window.navigator as any;
      if (nav.userAgentData?.platform) {
        return /mac/i.test(nav.userAgentData.platform);
      }
      if (nav.platform) {
        return /mac/i.test(nav.platform);
      }
      return /mac/i.test(nav.userAgent);
    };
    setIsMac(checkMac());

    return () => {
      if (desktopTimeoutRef.current) clearTimeout(desktopTimeoutRef.current);
      if (mobileTimeoutRef.current) clearTimeout(mobileTimeoutRef.current);
    };
  }, []);

  // Configure Gesture Handling (Ctrl + Scroll, Two Finger Pan) on the container
  useEffect(() => {
    const container = containerRef.current;
    if (!container || !mapInstance) return;

    // 1. Initialize default scroll/drag states
    mapInstance.scrollWheelZoom.disable();
    // Default to enabled for mouse drag, touch handlers will adjust on touchstart
    mapInstance.dragging.enable();
    mapInstance.touchZoom.enable();

    let isMouseOver = false;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isMouseOver) return;
      if (e.ctrlKey || e.metaKey) {
        mapInstance.scrollWheelZoom.enable();
      }
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      if (!e.ctrlKey && !e.metaKey) {
        mapInstance.scrollWheelZoom.disable();
      }
    };

    const handleMouseEnter = (e: MouseEvent) => {
      isMouseOver = true;
      if (e.ctrlKey || e.metaKey) {
        mapInstance.scrollWheelZoom.enable();
      }
      window.addEventListener("keydown", handleKeyDown);
      window.addEventListener("keyup", handleKeyUp);
    };

    const handleMouseLeave = () => {
      isMouseOver = false;
      mapInstance.scrollWheelZoom.disable();
      setShowDesktopWarning(false);
      isDesktopWarningActive.current = false;
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("keyup", handleKeyUp);
    };

    // 2. Wheel Event Handler (Desktop Ctrl/⌘ + Scroll Zoom)
    const handleWheel = (e: WheelEvent) => {
      const hasModifier = e.ctrlKey || e.metaKey;

      if (hasModifier) {
        // Enable built-in zoom natively so Leaflet does cursor-centered zoom
        mapInstance.scrollWheelZoom.enable();
        setShowDesktopWarning(false);
        isDesktopWarningActive.current = false;
      } else {
        // Disable built-in zoom to let the browser scroll the page
        mapInstance.scrollWheelZoom.disable();
        
        // Show warning only when the user scrolls the wheel over the map without modifier
        if (!isDesktopWarningActive.current) {
          isDesktopWarningActive.current = true;
          setShowDesktopWarning(true);
        }
        if (desktopTimeoutRef.current) clearTimeout(desktopTimeoutRef.current);
        desktopTimeoutRef.current = setTimeout(() => {
          setShowDesktopWarning(false);
          isDesktopWarningActive.current = false;
        }, 1500);
      }
    };

    // 3. Touch Event Handlers (Mobile Two-Finger Panning)
    const handleTouchStart = (e: TouchEvent) => {
      if (e.touches.length >= 2) {
        mapInstance.dragging.enable();
        mapInstance.touchZoom.enable();
        setShowMobileWarning(false);
        isMobileWarningActive.current = false;
        if (e.cancelable) e.preventDefault();
      } else {
        mapInstance.dragging.disable();
        mapInstance.touchZoom.disable();
      }
    };

    const handleTouchMove = (e: TouchEvent) => {
      if (e.touches.length === 1) {
        // Show warning only when user attempts to drag using one finger
        if (!isMobileWarningActive.current) {
          isMobileWarningActive.current = true;
          setShowMobileWarning(true);
        }
        if (mobileTimeoutRef.current) clearTimeout(mobileTimeoutRef.current);
        mobileTimeoutRef.current = setTimeout(() => {
          setShowMobileWarning(false);
          isMobileWarningActive.current = false;
        }, 1500);
      } else if (e.touches.length >= 2) {
        if (e.cancelable) e.preventDefault();
      }
    };

    const handleTouchEnd = (e: TouchEvent) => {
      if (e.touches.length < 2) {
        mapInstance.dragging.disable();
        mapInstance.touchZoom.disable();
      }
    };

    // Register listeners
    container.addEventListener("mouseenter", handleMouseEnter);
    container.addEventListener("mouseleave", handleMouseLeave);
    container.addEventListener("wheel", handleWheel, { passive: true });
    container.addEventListener("touchstart", handleTouchStart, { passive: false });
    container.addEventListener("touchmove", handleTouchMove, { passive: false });
    container.addEventListener("touchend", handleTouchEnd, { passive: false });

    return () => {
      container.removeEventListener("mouseenter", handleMouseEnter);
      container.removeEventListener("mouseleave", handleMouseLeave);
      container.removeEventListener("wheel", handleWheel);
      container.removeEventListener("touchstart", handleTouchStart);
      container.removeEventListener("touchmove", handleTouchMove);
      container.removeEventListener("touchend", handleTouchEnd);
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("keyup", handleKeyUp);
    };
  }, [mapInstance]);

  const handleNavigateNow = (m: MosquePreview) => {
    if (m.latitude === null || m.longitude === null) return;
    const isiOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
    if (isiOS) {
      window.open(`maps://?daddr=${m.latitude},${m.longitude}&dirflg=d`, "_blank");
    } else {
      window.open(`https://www.google.com/maps/dir/?api=1&destination=${m.latitude},${m.longitude}&travelmode=driving`, "_blank");
    }
  };

  const handleFocus = () => {
    if (mapInstance) {
      // Focus Leaflet's container to enable native keyboard navigation instantly
      mapInstance.getContainer().focus();
    }
  };

  return (
    <div
      ref={containerRef}
      onFocus={handleFocus}
      aria-label="Interactive Mosque Locations Map. Use arrow keys to pan the map, and plus and minus keys to zoom. On desktop, hold Control (or Command on Mac) and scroll to zoom. On mobile, use two fingers to pan."
      className="relative h-[320px] sm:h-[400px] md:h-[480px] w-full overflow-hidden rounded-2xl border border-slate-900/10 shadow-lg focus-within:ring-2 focus-within:ring-emerald-800 focus-within:ring-offset-2 outline-none transition-all duration-200 [&_.leaflet-bar_a]:focus-visible:ring-2 [&_.leaflet-bar_a]:focus-visible:ring-emerald-800 [&_.leaflet-bar_a]:focus-visible:outline-none"
    >
      {/* Desktop interaction warning overlay */}
      <div
        className={`absolute inset-0 flex items-center justify-center bg-black/35 z-[999] pointer-events-none transition-opacity duration-300 ${
          showDesktopWarning ? "opacity-100" : "opacity-0"
        }`}
      >
        <div className="mx-4 bg-slate-950/90 text-slate-100 font-semibold px-5 py-3.5 rounded-xl shadow-2xl flex items-center gap-3 border border-white/10 backdrop-blur-sm max-w-xs text-center text-sm">
          <span className="text-lg">⌨️</span>
          <span>Use <kbd className="bg-slate-800 px-1.5 py-0.5 rounded border border-slate-700 font-mono text-xs">{isMac ? "⌘" : "Ctrl"}</kbd> + scroll to zoom</span>
        </div>
      </div>

      {/* Mobile interaction warning overlay */}
      <div
        className={`absolute inset-0 flex items-center justify-center bg-black/35 z-[999] pointer-events-none transition-opacity duration-300 ${
          showMobileWarning ? "opacity-100" : "opacity-0"
        }`}
      >
        <div className="mx-4 bg-slate-950/90 text-slate-100 font-semibold px-5 py-3.5 rounded-xl shadow-2xl flex items-center gap-3 border border-white/10 backdrop-blur-sm max-w-xs text-center text-sm">
          <span className="text-lg">✌️</span>
          <span>Use two fingers to move the map</span>
        </div>
      </div>

      <MapContainer
        center={[center.lat, center.lon]}
        zoom={13}
        className="h-full w-full"
        style={{ zIndex: 1 }}
        scrollWheelZoom={false}
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
                      <span className="font-medium text-slate-500">{formatDistance(m.distance, true)} away</span>
                    )}
                  </div>

                  {m.operating_status?.next_prayer_name && m.operating_status.next_prayer_time && (
                    <div className="text-[10px] text-slate-600">
                      Next: <span className="font-bold">{m.operating_status.next_prayer_name}</span> at{" "}
                      <span className="font-mono">{formatTimeTo12Hour(m.operating_status.next_prayer_time)}</span>
                    </div>
                  )}
                  {(() => {
                    const { preview, remainingCount } = getPreviewFacilities(m, 5);
                    if (preview.length === 0) return null;
                    return (
                      <div className="mt-1.5 flex flex-wrap items-center gap-1.5 text-xs">
                        {preview.map((f) => (
                          <span key={f.key} title={f.label} className="cursor-help">
                            {f.icon}
                          </span>
                        ))}
                        {remainingCount > 0 && (
                          <span className="text-[8px] font-bold bg-slate-100 text-slate-500 rounded px-1 leading-none py-0.5" title={`${remainingCount} more facilities`}>
                            +{remainingCount}
                          </span>
                        )}
                      </div>
                    );
                  })()}

                  <div className="mt-1.5 flex items-center justify-between border-t border-slate-100 pt-1.5">
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
        <MapInstanceSelector setMapInstance={setMapInstance} />
      </MapContainer>
    </div>
  );
});

export default MosqueMapInner;
