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
  const url = new URL(path.replace(/^\//, ""), `${env.apiBaseUrl.replace(/\/$/, "")}/`);
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
    const token = localStorage.getItem("auth_token");
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
    throw new ApiError(`API request failed with status ${response.status}`, response.status, payload);
  }

  return payload as TResponse;
}
