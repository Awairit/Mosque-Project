export type FacilityKey =
  | "women_prayer_available"
  | "separate_women_entrance"
  | "parking_available"
  | "wudu_facility_available"
  | "wheelchair_accessible"
  | "drinking_water_available"
  | "washrooms_available"
  | "library_available"
  | "quran_classes_available"
  | "hifz_program_available"
  | "nikah_service_available"
  | "muslim_burial_ground_available"
  | "community_hall_available"
  | "ramadan_iftar_available"
  | "eid_prayer_ground_available"
  | "zakat_collection_available"
  | "funeral_prayer_facility_available";

export type FacilityConfig = {
  key: FacilityKey;
  label: string;
  desc: string;
  icon: string;
  priority: number; // Lower numbers represent higher priority (1 = highest)
};

export const FACILITIES_LIST: FacilityConfig[] = [
  {
    key: "women_prayer_available",
    label: "Women's Prayer Area",
    desc: "Separate area for ladies to pray.",
    icon: "🚺",
    priority: 1,
  },
  {
    key: "wudu_facility_available",
    label: "Wudu Facility",
    desc: "Ablution spaces on site.",
    icon: "💧",
    priority: 2,
  },
  {
    key: "parking_available",
    label: "Parking",
    desc: "Dedicated parking for cars/bikes.",
    icon: "🚗",
    priority: 3,
  },
  {
    key: "wheelchair_accessible",
    label: "Wheelchair Accessibility",
    desc: "Ramps or elevators for wheelchair entry.",
    icon: "♿",
    priority: 4,
  },
  {
    key: "washrooms_available",
    label: "Washrooms",
    desc: "Toilet facilities on site.",
    icon: "🚻",
    priority: 5,
  },
  {
    key: "drinking_water_available",
    label: "Drinking Water",
    desc: "Clean drinking water available.",
    icon: "🚰",
    priority: 6,
  },
  {
    key: "separate_women_entrance",
    label: "Separate Women's Entrance",
    desc: "Private entrance for ladies.",
    icon: "🚪",
    priority: 7,
  },
  {
    key: "funeral_prayer_facility_available",
    label: "Funeral Prayer Facility",
    desc: "Janazah prayer space available.",
    icon: "🕊️",
    priority: 8,
  },
  {
    key: "ramadan_iftar_available",
    label: "Ramadan Iftar",
    desc: "Iftar meals provided during Ramadan.",
    icon: "🌙",
    priority: 9,
  },
  {
    key: "eid_prayer_ground_available",
    label: "Eid Prayer Ground",
    desc: "Open ground for Eid prayers.",
    icon: "🌟",
    priority: 10,
  },
  {
    key: "zakat_collection_available",
    label: "Zakat Collection",
    desc: "Accepts Zakat on behalf of those in need.",
    icon: "🤲",
    priority: 11,
  },
  {
    key: "quran_classes_available",
    label: "Quran Classes",
    desc: "Regular Quran teaching sessions.",
    icon: "📖",
    priority: 12,
  },
  {
    key: "hifz_program_available",
    label: "Hifz Program",
    desc: "Quran memorisation programme.",
    icon: "🕌",
    priority: 13,
  },
  {
    key: "nikah_service_available",
    label: "Nikah Service",
    desc: "Marriage ceremony services offered.",
    icon: "💍",
    priority: 14,
  },
  {
    key: "library_available",
    label: "Library",
    desc: "Islamic books and resources available.",
    icon: "📚",
    priority: 15,
  },
  {
    key: "community_hall_available",
    label: "Community Hall",
    desc: "Hall available for community events.",
    icon: "🏛️",
    priority: 16,
  },
  {
    key: "muslim_burial_ground_available",
    label: "Muslim Burial Ground",
    desc: "Islamic burial ground affiliated or nearby.",
    icon: "🌿",
    priority: 17,
  },
];

// Helper to filter and sort active facilities for a mosque object
export function getActiveFacilities(mosque: Record<string, any>): FacilityConfig[] {
  if (!mosque) return [];
  return FACILITIES_LIST.filter((f) => !!mosque[f.key]).sort((a, b) => a.priority - b.priority);
}

// Get the top N highest priority facilities for preview cards or popups
export function getPreviewFacilities(
  mosque: Record<string, any>,
  maxCount = 6
): { preview: FacilityConfig[]; remainingCount: number } {
  const active = getActiveFacilities(mosque);
  const preview = active.slice(0, maxCount);
  const remainingCount = Math.max(0, active.length - maxCount);
  return { preview, remainingCount };
}
