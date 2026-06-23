"use client";

import Link from "next/link";
import { useMemo, useState, useEffect } from "react";
import { apiRequest } from "@/lib/api/client";
import { MapFilters, FilterState } from "./MapFilters";
import { MosqueMap } from "./MosqueMap";

type LocationState = "idle" | "requesting" | "granted" | "denied" | "unsupported";

type PrayerTiming = {
  fajr_time: string;
  dhuhr_time: string;
  asr_time: string;
  maghrib_time: string;
  isha_time: string;
  jumuah_time: string;
  effective_from: string;
};

type OperatingStatus = {
  is_open: boolean;
  status_label: string; // Open Now, Closed, Open 24 Hours, Closing Soon, Schedule Not Verified
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
  separate_women_entrance: boolean;
  mosque_status: string;
  prayer_timing?: PrayerTiming | null;
  operating_status?: OperatingStatus | null;
  distance?: number | null; // in meters
};

type MosqueListResponse = {
  count: number;
  results: MosquePreview[];
};

type CityDetails = {
  id: number;
  name: string;
  latitude: string;
  longitude: string;
};

type CityTimings = {
  id: number;
  city: number;
  city_name: string;
  calendar_date: string | null;
  fajr_time: string;
  dhuhr_time: string;
  asr_time: string;
  maghrib_time: string;
  isha_time: string;
  city_details: CityDetails;
};

type CityListResponse = {
  count: number;
  results: CityDetails[];
};

type Prayer = {
  name: string;
  time: string;
  isNext?: boolean;
};

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

const getNextPrayerIndex = (prayersList: Prayer[]) => {
  if (typeof window === "undefined" || prayersList.length === 0) return 2; // Default to index 2 (Asr)
  const now = new Date();
  const currentMinutes = now.getHours() * 60 + now.getMinutes();

  for (let i = 0; i < prayersList.length; i++) {
    const p = prayersList[i];
    const parts = p.time.split(" ");
    if (parts.length < 2) continue;
    const timeParts = parts[0].split(":");
    let hours = parseInt(timeParts[0], 10);
    const minutes = parseInt(timeParts[1], 10);
    const ampm = parts[1];
    if (ampm === "PM" && hours !== 12) hours += 12;
    if (ampm === "AM" && hours === 12) hours = 0;
    const prayerMinutes = hours * 60 + minutes;

    if (prayerMinutes > currentMinutes) {
      return i;
    }
  }
  return 0; // Default to Fajr if all have passed today
};

interface LocationButtonProps {
  state: LocationState;
  onClick: () => void;
}

function LocationButton({ state, onClick }: LocationButtonProps) {
  const label = useMemo(() => {
    switch (state) {
      case "requesting":
        return "Finding nearby mosques";
      case "granted":
        return "Location enabled";
      case "denied":
        return "Search by area instead";
      case "unsupported":
        return "Location unavailable";
      default:
        return "Use my location";
    }
  }, [state]);

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={state === "requesting"}
      className="inline-flex min-h-12 items-center justify-center rounded-full bg-emerald-800 px-6 text-sm font-semibold text-white shadow-lg shadow-emerald-950/10 transition hover:bg-emerald-900 focus:outline-none focus:ring-4 focus:ring-emerald-800/20 disabled:cursor-wait disabled:opacity-75"
    >
      {label}
    </button>
  );
}

interface CurrentPrayerCardProps {
  cityTimings: CityTimings | null;
  isLoading: boolean;
  hasError: boolean;
  cities: CityDetails[];
  selectedCity: string;
  onCityChange: (cityId: string) => void;
}

function CurrentPrayerCard({
  cityTimings,
  isLoading,
  hasError,
  cities,
  selectedCity,
  onCityChange,
}: CurrentPrayerCardProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const prayersList = useMemo(() => {
    if (!cityTimings) return [];
    return [
      { name: "Fajr", time: formatTimeTo12Hour(cityTimings.fajr_time) },
      { name: "Dhuhr", time: formatTimeTo12Hour(cityTimings.dhuhr_time) },
      { name: "Asr", time: formatTimeTo12Hour(cityTimings.asr_time) },
      { name: "Maghrib", time: formatTimeTo12Hour(cityTimings.maghrib_time) },
      { name: "Isha", time: formatTimeTo12Hour(cityTimings.isha_time) },
    ];
  }, [cityTimings]);

  const activePrayers = useMemo(() => {
    if (prayersList.length === 0) return [];
    const nextIdx = mounted ? getNextPrayerIndex(prayersList) : -1;
    return prayersList.map((p, idx) => ({
      ...p,
      isNext: idx === nextIdx,
    }));
  }, [prayersList, mounted]);

  const nextPrayer = activePrayers.find((prayer) => prayer.isNext);

  return (
    <section
      aria-labelledby="current-prayer-title"
      className="rounded-2xl border border-emerald-900/10 bg-white/90 p-5 shadow-xl shadow-slate-950/5 backdrop-blur"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-700">
              City Prayer Timings
            </span>
          </div>
          <div className="mt-2 flex items-center gap-2">
            <label htmlFor="city-select" className="sr-only">
              Select City
            </label>
            <select
              id="city-select"
              value={selectedCity}
              onChange={(e) => onCityChange(e.target.value)}
              className="rounded-xl border border-slate-200 bg-white px-2 py-1 text-sm font-bold text-slate-800 shadow-sm outline-none transition focus:border-emerald-800"
            >
              {Array.isArray(cities) && cities.map((c) => (
                <option key={c.id} value={String(c.id)}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>
        </div>
        {nextPrayer && (
          <div className="w-fit rounded-full bg-emerald-50 px-3.5 py-1 text-xs font-bold text-emerald-800">
            Next: {nextPrayer.name} at {nextPrayer.time}
          </div>
        )}
      </div>

      {isLoading ? (
        <div className="mt-5 rounded-xl bg-slate-50 py-6 text-center text-sm text-slate-400">
          Loading timings...
        </div>
      ) : hasError || !cityTimings ? (
        <div className="mt-5 rounded-xl bg-red-50 py-6 text-center text-sm text-red-800">
          Failed to load city timings.
        </div>
      ) : (
        <div className="mt-5 grid grid-cols-5 gap-1.5">
          {activePrayers.map((prayer) => (
            <div
              key={prayer.name}
              className={
                prayer.isNext
                  ? "rounded-xl bg-emerald-800 px-1 py-2.5 text-center text-white"
                  : "rounded-xl bg-slate-50 px-1 py-2.5 text-center text-slate-700"
              }
            >
              <p className="text-[10px] font-medium">{prayer.name}</p>
              <p className="mt-1 font-mono text-[11px] font-semibold tabular-nums leading-none sm:text-xs">
                {prayer.time.split(" ")[0]}
                <span className="block text-[8px] font-sans font-normal opacity-85 mt-0.5">
                  {prayer.time.split(" ")[1]}
                </span>
              </p>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

interface ApprovedMosquesCardProps {
  mosques: MosquePreview[];
  isLoading: boolean;
  hasError: boolean;
}

function ApprovedMosquesCard({ mosques, isLoading, hasError }: ApprovedMosquesCardProps) {
  const formatDistance = (meters?: number | null) => {
    if (meters === undefined || meters === null) return "";
    if (meters < 1000) {
      return `${Math.round(meters)} meters away`;
    }
    return `${(meters / 1000).toFixed(1)} km away`;
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

  const getStatusBadge = (status?: OperatingStatus | null) => {
    if (!status) {
      return (
        <span className="inline-flex items-center rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-600">
          Status unknown
        </span>
      );
    }

    switch (status.status_label) {
      case "Open 24 Hours":
        return (
          <span className="inline-flex items-center rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-800 border border-emerald-950/10">
            Open 24 Hours
          </span>
        );
      case "Open Now":
        return (
          <span className="inline-flex items-center rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-800 border border-emerald-950/10">
            🟢 Open Now {status.closes_at ? `· Closes: ${status.closes_at}` : ""}
          </span>
        );
      case "Closing Soon":
        return (
          <span className="inline-flex items-center rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-semibold text-amber-800 border border-amber-950/10">
            ⚠️ Closing Soon {status.closes_at ? `· Closes: ${status.closes_at}` : ""}
          </span>
        );
      case "Schedule Not Verified":
        return (
          <span className="inline-flex items-center rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-600 border border-slate-200">
            ⚪ Schedule Not Verified
          </span>
        );
      case "Closed":
      default:
        return (
          <span className="inline-flex items-center rounded-full bg-red-50 px-2 py-0.5 text-[10px] font-semibold text-red-800 border border-red-950/10">
            🔴 Closed {status.opens_at ? `· Opens: ${status.opens_at}` : ""}
          </span>
        );
    }
  };

  return (
    <section
      aria-labelledby="nearest-mosque-title"
      className="rounded-2xl border border-slate-900/10 bg-white p-4 shadow-xl shadow-slate-950/5"
    >
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">
          Nearest Mosques
        </p>
        <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-800">
          Live discovery
        </span>
      </div>

      <h2 id="nearest-mosque-title" className="mt-3 text-lg font-semibold text-slate-950">
        Top 5 Approved Mosques
      </h2>

      <div className="mt-4 space-y-3">
        {isLoading ? (
          <div className="rounded-xl bg-slate-50 p-3 text-sm text-slate-600">
            Loading approved mosques...
          </div>
        ) : null}

        {!isLoading && hasError ? (
          <div className="rounded-xl bg-red-50 p-3 text-sm text-red-800">
            Approved mosques could not be loaded right now.
          </div>
        ) : null}

        {!isLoading && !hasError && mosques.length === 0 ? (
          <div className="rounded-xl bg-slate-50 p-3 text-sm text-slate-600">
            No approved mosques match your filters.
          </div>
        ) : null}

        {!isLoading && !hasError
          ? mosques.map((mosque) => (
              <article
                key={mosque.id}
                className="rounded-xl bg-slate-50 p-4 shadow-sm border border-slate-100 hover:border-emerald-800/20 transition-all duration-200"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="text-sm font-bold text-slate-950">
                      {mosque.mosque_name}
                    </h3>
                    <p className="mt-1 text-xs text-slate-500">
                      {[mosque.city, mosque.address].filter(Boolean).join(" · ") ||
                        "Location details pending"}
                    </p>
                    {mosque.distance !== undefined && mosque.distance !== null && (
                      <p className="mt-1 text-xs font-semibold text-emerald-800">
                        {formatDistance(mosque.distance)}
                      </p>
                    )}
                  </div>
                  <div className="flex flex-col items-end gap-1.5">
                    {getStatusBadge(mosque.operating_status)}
                    {mosque.operating_status?.current_window && (
                      <span className="text-[9px] font-medium text-emerald-800 uppercase tracking-wider">
                        Window: {mosque.operating_status.current_window}
                      </span>
                    )}
                  </div>
                </div>

                {/* Next Jamaat Highlight */}
                {mosque.operating_status?.next_prayer_name && mosque.operating_status.next_prayer_time && (
                  <div className="mt-2.5 rounded-lg bg-emerald-50 px-2.5 py-1.5 text-[10px] font-semibold text-slate-700">
                    📢 Next Congregation: <span className="text-emerald-800 font-bold">{mosque.operating_status.next_prayer_name}</span> at <span className="font-mono">{formatTimeTo12Hour(mosque.operating_status.next_prayer_time)}</span>
                  </div>
                )}

                {/* Jamaat Timings Quick Glance */}
                {mosque.prayer_timing ? (
                  <div className="mt-3 bg-white border border-slate-100 rounded-lg p-2 grid grid-cols-5 gap-1 text-center font-sans text-[10px]">
                    <div>
                      <span className="block text-[9px] text-slate-400 font-semibold">Fajr</span>
                      <span className="block mt-0.5 font-bold text-slate-900">
                        {formatTimeTo12Hour(mosque.prayer_timing.fajr_time).split(" ")[0]}
                      </span>
                    </div>
                    <div>
                      <span className="block text-[9px] text-slate-400 font-semibold">Dhuhr</span>
                      <span className="block mt-0.5 font-bold text-slate-900">
                        {formatTimeTo12Hour(mosque.prayer_timing.dhuhr_time).split(" ")[0]}
                      </span>
                    </div>
                    <div>
                      <span className="block text-[9px] text-slate-400 font-semibold">Asr</span>
                      <span className="block mt-0.5 font-bold text-slate-900">
                        {formatTimeTo12Hour(mosque.prayer_timing.asr_time).split(" ")[0]}
                      </span>
                    </div>
                    <div>
                      <span className="block text-[9px] text-slate-400 font-semibold">Maghr.</span>
                      <span className="block mt-0.5 font-bold text-slate-900">
                        {formatTimeTo12Hour(mosque.prayer_timing.maghrib_time).split(" ")[0]}
                      </span>
                    </div>
                    <div>
                      <span className="block text-[9px] text-slate-400 font-semibold">Isha</span>
                      <span className="block mt-0.5 font-bold text-slate-900">
                        {formatTimeTo12Hour(mosque.prayer_timing.isha_time).split(" ")[0]}
                      </span>
                    </div>
                  </div>
                ) : (
                  <div className="mt-3 bg-white/70 border border-slate-100 rounded-lg py-2 text-center text-[10px] text-slate-400 font-normal">
                    Timings unconfigured
                  </div>
                )}

                {/* Facilities List & Action */}
                <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-slate-100 pt-2.5">
                  <div className="flex flex-wrap gap-1">
                    {mosque.women_prayer_available && (
                      <span className="rounded-full bg-white border border-slate-200/60 px-2 py-0.5 text-[9px] text-slate-600">
                        🚺 Women Space
                      </span>
                    )}
                    {mosque.parking_available && (
                      <span className="rounded-full bg-white border border-slate-200/60 px-2 py-0.5 text-[9px] text-slate-600">
                        🚗 Parking
                      </span>
                    )}
                    {mosque.wudu_facility_available && (
                      <span className="rounded-full bg-white border border-slate-200/60 px-2 py-0.5 text-[9px] text-slate-600">
                        💧 Wudu
                      </span>
                    )}
                    {mosque.wheelchair_accessible && (
                      <span className="rounded-full bg-white border border-slate-200/60 px-2 py-0.5 text-[9px] text-slate-600">
                        ♿ Wheelchair
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    <Link
                      href={`/mosque/${mosque.id}`}
                      className="inline-flex items-center text-[10px] font-bold text-emerald-800 hover:text-emerald-950 transition-colors"
                    >
                      View Profile →
                    </Link>
                    {mosque.latitude !== null && mosque.longitude !== null && (
                      <button
                        type="button"
                        onClick={() => handleNavigateNow(mosque)}
                        className="inline-flex items-center rounded-full bg-emerald-800 px-3 py-1 text-[10px] font-bold text-white hover:bg-emerald-900 transition-colors shadow-sm"
                      >
                        🚀 Navigate Now
                      </button>
                    )}
                  </div>
                </div>
              </article>
            ))
          : null}
      </div>
    </section>
  );
}

export function HomeHero() {
  const [locationState, setLocationState] = useState<LocationState>("idle");
  const [coords, setCoords] = useState<{ lat: number; lon: number } | null>(null);
  
  const [cities, setCities] = useState<CityDetails[]>([]);
  const [selectedCity, setSelectedCity] = useState<string>("");
  
  const [cityTimings, setCityTimings] = useState<CityTimings | null>(null);
  const [loadingTimings, setLoadingTimings] = useState(true);
  const [timingsError, setTimingsError] = useState(false);

  const [mosques, setMosques] = useState<MosquePreview[]>([]);
  const [loadingMosques, setLoadingMosques] = useState(true);
  const [mosquesError, setMosquesError] = useState(false);

  // Map viewport and mosques state
  const [mapBbox, setMapBbox] = useState<string>("");
  const [mapMosques, setMapMosques] = useState<MosquePreview[]>([]);

  // Shared filters state
  const [filters, setFilters] = useState<FilterState>({
    openNow: false,
    womenPrayerAvailable: false,
    wuduFacilityAvailable: false,
    parkingAvailable: false,
    wheelchairAccessible: false,
    jumuahAvailable: false,
  });

  const handleToggleFilter = (key: keyof FilterState) => {
    setFilters((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  // 1. Fetch Cities List on Mount
  useEffect(() => {
    let isMounted = true;
    async function loadCities() {
      try {
        const response = await apiRequest<any>({
          path: "/locations/cities/",
        });
        if (isMounted && response) {
          const list = Array.isArray(response)
            ? response
            : response.results || [];
          setCities(list);
          if (list.length > 0) {
            // Set initial selected city to Nanded if available, else first city
            const nandedCity = list.find((c: any) => c.name.toLowerCase() === "nanded");
            setSelectedCity(nandedCity ? String(nandedCity.id) : String(list[0].id));
          }
        }
      } catch (err) {
        console.error("Failed to load cities", err);
      }
    }
    loadCities();
    return () => {
      isMounted = false;
    };
  }, []);

  // 2. Load timings and Top 5 nearby mosques based on GPS/city selection & Filters
  useEffect(() => {
    let isMounted = true;

    async function loadData() {
      setLoadingTimings(true);
      setLoadingMosques(true);
      
      try {
        let timingsPath = "/locations/city-timings/";
        let mosquesPath = "/mosques/";

        if (locationState === "granted" && coords) {
          timingsPath += `?lat=${coords.lat}&lon=${coords.lon}`;
          mosquesPath += `?lat=${coords.lat}&lon=${coords.lon}`;
        } else if (selectedCity) {
          timingsPath += `?city=${selectedCity}`;
          const activeCity = cities.find((c) => String(c.id) === selectedCity);
          if (activeCity) {
            mosquesPath += `?lat=${activeCity.latitude}&lon=${activeCity.longitude}`;
          }
        }

        // Apply shared filters to the Top 5 API query path
        let filterParams = "";
        if (filters.openNow) filterParams += "&open_now=true";
        if (filters.womenPrayerAvailable) filterParams += "&women_prayer_available=true";
        if (filters.wuduFacilityAvailable) filterParams += "&wudu_facility_available=true";
        if (filters.parkingAvailable) filterParams += "&parking_available=true";
        if (filters.wheelchairAccessible) filterParams += "&wheelchair_accessible=true";
        if (filters.jumuahAvailable) filterParams += "&jumuah_available=true";

        if (filterParams) {
          mosquesPath += (mosquesPath.includes("?") ? "" : "?") + filterParams.substring(1);
        }

        // Fetch Timings
        try {
          const timingResponse = await apiRequest<CityTimings>({ path: timingsPath, cache: "no-store" });
          if (isMounted) {
            setCityTimings(timingResponse);
            setTimingsError(false);
            if (timingResponse.city_details && String(timingResponse.city_details.id) !== selectedCity && locationState === "granted") {
              setSelectedCity(String(timingResponse.city_details.id));
            }
          }
        } catch {
          if (isMounted) setTimingsError(true);
        } finally {
          if (isMounted) setLoadingTimings(false);
        }

        // Fetch Top 5 Mosques
        try {
          const mosquesResponse = await apiRequest<MosqueListResponse>({ path: mosquesPath, cache: "no-store" });
          if (isMounted) {
            setMosques(mosquesResponse.results);
            setMosquesError(false);
          }
        } catch {
          if (isMounted) setMosquesError(true);
        } finally {
          if (isMounted) setLoadingMosques(false);
        }

      } catch (err) {
        console.error("General error loading data", err);
      }
    }

    loadData();

    return () => {
      isMounted = false;
    };
  }, [locationState, coords, selectedCity, cities, filters]);

  // 3. Load Map Viewport Mosques dynamically on Bounds / Filters change
  useEffect(() => {
    if (!mapBbox) return;
    let isMounted = true;
    async function loadMapMosques() {
      try {
        let path = `/mosques/?in_bbox=${mapBbox}`;
        if (coords) {
          path += `&lat=${coords.lat}&lon=${coords.lon}`;
        } else if (selectedCity && cities.length > 0) {
          const activeCity = cities.find((c) => String(c.id) === selectedCity);
          if (activeCity) {
            path += `&lat=${activeCity.latitude}&lon=${activeCity.longitude}`;
          }
        }

        // Apply filters
        if (filters.openNow) path += "&open_now=true";
        if (filters.womenPrayerAvailable) path += "&women_prayer_available=true";
        if (filters.wuduFacilityAvailable) path += "&wudu_facility_available=true";
        if (filters.parkingAvailable) path += "&parking_available=true";
        if (filters.wheelchairAccessible) path += "&wheelchair_accessible=true";
        if (filters.jumuahAvailable) path += "&jumuah_available=true";

        const response = await apiRequest<MosqueListResponse>({ path, cache: "no-store" });
        if (isMounted && response.results) {
          setMapMosques(response.results);
        }
      } catch (err) {
        console.error("Failed to load map mosques", err);
      }
    }
    loadMapMosques();
    return () => {
      isMounted = false;
    };
  }, [mapBbox, filters, coords, selectedCity, cities]);

  const mapCenter = useMemo(() => {
    if (locationState === "granted" && coords) {
      return { lat: coords.lat, lon: coords.lon };
    }
    if (selectedCity && cities.length > 0) {
      const activeCity = cities.find((c) => String(c.id) === selectedCity);
      if (activeCity) {
        return {
          lat: parseFloat(activeCity.latitude),
          lon: parseFloat(activeCity.longitude),
        };
      }
    }
    return { lat: 19.15, lon: 77.30 }; // Default to Nanded
  }, [locationState, coords, selectedCity, cities]);

  const handleLocationRequest = () => {
    if (!("geolocation" in navigator)) {
      setLocationState("unsupported");
      return;
    }

    setLocationState("requesting");

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocationState("granted");
        setCoords({
          lat: position.coords.latitude,
          lon: position.coords.longitude,
        });
      },
      () => setLocationState("denied"),
      {
        enableHighAccuracy: false,
        maximumAge: 300000,
        timeout: 9000,
      },
    );
  };

  const handleCityChange = (cityId: string) => {
    setSelectedCity(cityId);
    setLocationState("idle");
    setCoords(null);
  };

  return (
    <section className="relative isolate overflow-hidden bg-[#F4F7F5] px-4 py-8 sm:px-6 lg:px-8">
      <div className="absolute inset-x-0 top-0 -z-10 h-64 bg-[radial-gradient(circle_at_top,_rgba(15,95,74,0.16),_transparent_58%)]" />

      <div className="mx-auto max-w-6xl">
        <div className="grid gap-8 lg:min-h-[580px] lg:grid-cols-[1fr_440px] lg:items-center">
          <div className="pt-6 sm:pt-10">
            <p className="inline-flex rounded-full border border-emerald-900/10 bg-white/70 px-4 py-2 text-sm font-medium text-emerald-800 shadow-sm">
              Prayer-aware mosque discovery
            </p>

            <h1 className="mt-6 max-w-3xl text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl lg:text-6xl">
              Find a peaceful place to pray, wherever you are.
            </h1>

            <p className="mt-5 max-w-2xl text-base leading-7 text-slate-600 sm:text-lg">
              See nearby mosques, today&apos;s prayer times, jamaat details, women&apos;s prayer support,
              and directions in one calm mobile-first experience.
            </p>

            <div className="mt-7 flex flex-col gap-3 sm:flex-row sm:items-center">
              <LocationButton state={locationState} onClick={handleLocationRequest} />
              <span className="text-xs text-slate-500 font-medium sm:ml-2">Or select below:</span>
            </div>
          </div>

          <div className="grid gap-4 pb-6 lg:pb-0">
            <CurrentPrayerCard
              cityTimings={cityTimings}
              isLoading={loadingTimings}
              hasError={timingsError}
              cities={cities}
              selectedCity={selectedCity}
              onCityChange={handleCityChange}
            />
            <ApprovedMosquesCard
              mosques={mosques}
              isLoading={loadingMosques}
              hasError={mosquesError}
            />
          </div>
        </div>

        {/* Dynamic Filters Bar */}
        <div className="mt-8 border-t border-slate-200/60 pt-6">
          <div className="mb-4">
            <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider">Search Filters</h3>
            <p className="text-xs text-slate-500">Filter mosques on the card view and map simultaneously</p>
          </div>
          <MapFilters filters={filters} onToggleFilter={handleToggleFilter} />
        </div>

        {/* Interactive Map enhancement */}
        <div className="mt-6">
          <div className="mb-4">
            <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider">Interactive Map</h3>
            <p className="text-xs text-slate-500">Pan and zoom the map to discover mosques inside the viewport</p>
          </div>
          <MosqueMap
            mosques={mapMosques}
            userCoords={coords}
            center={mapCenter}
            onBoundsChange={setMapBbox}
          />
        </div>
      </div>
    </section>
  );
}
