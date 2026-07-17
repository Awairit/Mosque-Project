/**
 * Centralised UI label strings for region-specific terminology.
 *
 * These strings are used across mosque-facing UI components.
 * Centralising them here means a wording change requires updating
 * only this file — not hunting through individual components.
 *
 * Do NOT use this for i18n.  This is purely a maintainability
 * convenience for a single-language, single-region product.
 *
 * Rule: text labels only — no emojis, icons, or SVGs.
 * Presentation elements belong inside React components.
 */

export const LABELS = {
  /**
   * Label for the next congregation prayer shown on mosque cards.
   * "Jamaat" is the preferred term for the Indian-Muslim audience
   * of Mosque Finder V1.1.
   */
  NEXT_JAMAAT: "Next Jamaat",

  /**
   * Label for the prayer timing freshness indicator shown on mosque
   * cards and the mosque detail page.
   */
  LAST_UPDATED: "Last Updated",
} as const;
