import { apiRequest } from "@/lib/api/client";

const VISITOR_ID_KEY = "mq_vid";

export function getOrCreateVisitorId(): string | null {
  if (typeof window === "undefined") return null;
  let vid = localStorage.getItem(VISITOR_ID_KEY);
  if (!vid) {
    // Generate UUID v4
    vid = "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
      const r = (Math.random() * 16) | 0;
      const v = c === "x" ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
    localStorage.setItem(VISITOR_ID_KEY, vid);
  }
  return vid;
}

export async function trackVisit(options: {
  path?: string;
  city_id?: number;
  mosque_id?: number;
  event_type?: string;
}) {
  if (typeof window === "undefined") return;

  try {
    const vid = getOrCreateVisitorId();
    const currentPath = options.path || window.location.pathname;

    const data = await apiRequest<{ visitor_id: string; is_new_visitor: boolean }>({
      path: "/analytics/track/",
      method: "POST",
      body: JSON.stringify({
        visitor_id: vid,
        path: currentPath,
        city_id: options.city_id,
        mosque_id: options.mosque_id,
        event_type: options.event_type || "page_view",
      }),
    });

    if (data?.visitor_id) {
      localStorage.setItem(VISITOR_ID_KEY, data.visitor_id);
    }
  } catch (err) {
    // Non-blocking silent fallback for analytics
  }
}
