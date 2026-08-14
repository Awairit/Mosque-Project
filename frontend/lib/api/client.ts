import { env } from "@/lib/config/env";

type ApiRequestOptions = RequestInit & {
  path: string;
};

export class ApiError extends Error {
  status: number;
  details: unknown;

  constructor(message: string, status: number, details: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

export async function apiRequest<TResponse>({ path, ...init }: ApiRequestOptions) {
  // Strip leading slashes and any redundant 'api/v1/' prefix if path includes it (RC-BUG-001)
  let normalizedPath = path.replace(/^\//, "");
  if (normalizedPath.startsWith("api/v1/")) {
    normalizedPath = normalizedPath.substring(7);
  }

  const url = new URL(normalizedPath, `${env.apiBaseUrl.replace(/\/$/, "")}/`);
  const headers = new Headers(init.headers);

  if (!headers.has("Accept")) {
    headers.set("Accept", "application/json");
  }

  if (init.body instanceof FormData) {
    headers.delete("Content-Type");
  } else if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (typeof window !== "undefined") {
    const isPlatform =
      normalizedPath.startsWith("platform/") ||
      normalizedPath.startsWith("analytics/overview");
    const superToken = localStorage.getItem("super_auth_token");
    const normalToken = localStorage.getItem("auth_token");

    const token = isPlatform
      ? superToken || normalToken
      : normalToken || (normalizedPath.startsWith("city-admin/") ? null : superToken);

    if (token && !headers.has("Authorization")) {
      headers.set("Authorization", `Token ${token}`);
    }
  }

  const response = await fetch(url, {
    ...init,
    headers,
  });

  const isJson = response.headers.get("content-type")?.includes("application/json");
  const payload = isJson ? await response.json() : null;

  if (!response.ok) {
    // Centralized 401 Unauthorized token cleanup and safe redirect (BUG-011 & RC-BUG-002)
    if (response.status === 401 && typeof window !== "undefined") {
      const isPublicAuthRoute =
        normalizedPath.startsWith("auth/login") ||
        normalizedPath.startsWith("platform/login") ||
        normalizedPath.startsWith("auth/forgot-password") ||
        normalizedPath.startsWith("auth/verify-otp");

      const currentPath = window.location.pathname;
      const isExcludedPage =
        currentPath === "/login" ||
        currentPath === "/super-admin/login" ||
        currentPath === "/city-admin/login" ||
        currentPath === "/change-password";

      if (!isPublicAuthRoute && !isExcludedPage) {
        localStorage.removeItem("auth_token");
        localStorage.removeItem("super_auth_token");
        localStorage.removeItem("user_role");
        localStorage.removeItem("admin_mobile");
        localStorage.removeItem("admin_mosque_id");
        localStorage.removeItem("admin_mosque_name");

        const targetLogin = normalizedPath.startsWith("platform/")
          ? "/super-admin/login"
          : normalizedPath.startsWith("city-admin/")
          ? "/city-admin/login"
          : "/login";

        window.location.href = targetLogin;
      }
    }

    throw new ApiError(`API request failed with status ${response.status}`, response.status, payload);
  }

  return payload as TResponse;
}
