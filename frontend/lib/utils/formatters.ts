/**
 * Shared utility functions for formatting display values.
 */

export const formatDistance = (meters?: number | null, short = false): string => {
  if (meters === undefined || meters === null) return "";
  if (meters < 1000) {
    return short ? `${Math.round(meters)}m` : `${Math.round(meters)} meters away`;
  }
  return short ? `${(meters / 1000).toFixed(1)} km` : `${(meters / 1000).toFixed(1)} km away`;
};

export const formatTimeTo12Hour = (timeStr?: string | null): string => {
  if (!timeStr) return "Not set";
  const parts = timeStr.split(":");
  if (parts.length < 2) return timeStr;
  let hour = parseInt(parts[0], 10);
  const minute = parts[1];
  const ampm = hour >= 12 ? "PM" : "AM";
  hour = hour % 12;
  hour = hour ? hour : 12;
  return `${hour}:${minute} ${ampm}`;
};

/**
 * Converts an ISO 8601 timestamp into a human-friendly relative label.
 *
 * Examples:
 *   "Just Now"      — within 60 seconds
 *   "2 Hours Ago"   — within 24 hours
 *   "Yesterday"     — 1 full day ago
 *   "3 Days Ago"    — 2–6 days ago
 *   "1 Week Ago"    — 7–13 days ago
 *   "2 Weeks Ago"   — 14–29 days ago
 *   "1 Month Ago"   — 30–59 days ago
 *   "3 Months Ago"  — 60+ days ago
 *
 * Returns an empty string for missing / unparseable timestamps so callers
 * can gate rendering with a simple truthiness check.
 */
export const formatRelativeTime = (isoTimestamp?: string | null): string => {
  if (!isoTimestamp) return "";
  let past: Date;
  try {
    past = new Date(isoTimestamp);
    if (isNaN(past.getTime())) return "";
  } catch {
    return "";
  }

  const now = new Date();
  const diffMs = now.getTime() - past.getTime();

  // Clamp future timestamps (clock skew / timezone oddities) to "Just Now"
  if (diffMs < 0) return "Just Now";

  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);
  const diffWeeks = Math.floor(diffDays / 7);
  const diffMonths = Math.floor(diffDays / 30);

  if (diffSeconds < 60) return "Just Now";
  if (diffHours < 1) return `${diffMinutes} ${diffMinutes === 1 ? "Minute" : "Minutes"} Ago`;
  if (diffDays < 1) return `${diffHours} ${diffHours === 1 ? "Hour" : "Hours"} Ago`;
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return `${diffDays} Days Ago`;
  if (diffWeeks === 1) return "1 Week Ago";
  if (diffDays < 30) return `${diffWeeks} Weeks Ago`;
  if (diffMonths === 1) return "1 Month Ago";
  return `${diffMonths} Months Ago`;
};

