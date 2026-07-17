"use client";

import { useMemo, memo } from "react";

export type FilterState = {
  openNow: boolean;
  womenPrayerAvailable: boolean;
  wuduFacilityAvailable: boolean;
  parkingAvailable: boolean;
  wheelchairAccessible: boolean;
  jumuahAvailable: boolean;
};

interface MapFiltersProps {
  filters: FilterState;
  onToggleFilter: (key: keyof FilterState) => void;
}

export const MapFilters = memo(function MapFilters({ filters, onToggleFilter }: MapFiltersProps) {
  const filterButtons = useMemo(() => {
    return [
      { key: "openNow" as const, label: "🟢 Open Now" },
      { key: "womenPrayerAvailable" as const, label: "🚺 Women Space" },
      { key: "wuduFacilityAvailable" as const, label: "💧 Wudu Available" },
      { key: "parkingAvailable" as const, label: "🚗 Parking Available" },
      { key: "wheelchairAccessible" as const, label: "♿ Wheelchair Access" },
      { key: "jumuahAvailable" as const, label: "🕌 Jumuah Hosted" },
    ];
  }, []);

  return (
    <div className="flex w-full items-center gap-2 overflow-x-auto pb-2.5 pt-1 scrollbar-thin scrollbar-thumb-slate-200">
      {filterButtons.map((btn) => {
        const isActive = filters[btn.key];
        return (
          <button
            key={btn.key}
            type="button"
            onClick={() => onToggleFilter(btn.key)}
            className={`inline-flex h-9 shrink-0 items-center justify-center rounded-full px-4 text-xs font-semibold shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-emerald-800/30 ${
              isActive
                ? "bg-emerald-800 text-white hover:bg-emerald-900"
                 : "bg-white border border-slate-200 text-slate-600 hover:bg-slate-50"
            }`}
          >
            {btn.label}
          </button>
        );
      })}
    </div>
  );
});
