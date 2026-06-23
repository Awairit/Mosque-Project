const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000/api/v1";

export const env = {
  apiBaseUrl: process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_API_BASE_URL,
  appEnv: process.env.NEXT_PUBLIC_APP_ENV ?? "local",
  googleMapsApiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY ?? "",
} as const;
