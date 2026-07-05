"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useMemo, useState } from "react";

import { Eye, EyeOff } from "lucide-react";

import { ApiError, apiRequest } from "@/lib/api/client";

type FieldErrors = Partial<Record<keyof FormState | "non_field_errors", string>>;

type FormState = {
  username: string;
  password: string;
};

type LoginResponse = {
  token: string;
  username: string;
  email: string;
};

const initialFormState: FormState = {
  username: "",
  password: "",
};

function extractErrors(error: unknown): FieldErrors {
  if (
    !(error instanceof ApiError) ||
    !error.details ||
    typeof error.details !== "object"
  ) {
    return {
      non_field_errors: "Invalid admin credentials. Please check your username and password.",
    };
  }

  const errors: FieldErrors = {};
  const details = error.details as Record<string, unknown>;

  Object.entries(details).forEach(([key, value]) => {
    const message = Array.isArray(value) ? value.join(" ") : String(value);
    errors[key as keyof FieldErrors] = message;
  });

  return errors;
}

function FieldError({ message }: { message?: string }) {
  if (!message) {
    return null;
  }

  return <p className="mt-1.5 text-xs font-medium text-red-600">{message}</p>;
}

export function SuperAdminLoginForm() {
  const router = useRouter();
  const [form, setForm] = useState<FormState>(initialFormState);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const canSubmit = useMemo(
    () => form.username.trim().length > 0 && form.password.trim().length > 0,
    [form.username, form.password],
  );

  const updateField = <TField extends keyof FormState>(
    field: TField,
    value: FormState[TField],
  ) => {
    setForm((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({
      ...current,
      [field]: undefined,
      non_field_errors: undefined,
    }));
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const nextErrors: FieldErrors = {};
    if (!form.username.trim()) {
      nextErrors.username = "Username is required.";
    }
    if (!form.password.trim()) {
      nextErrors.password = "Password is required.";
    }

    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors);
      return;
    }

    setIsSubmitting(true);
    setErrors({});

    try {
      const response = await apiRequest<LoginResponse>({
        path: "/platform/auth/login/",
        method: "POST",
        body: JSON.stringify(form),
      });

      // Save token and metadata separately under super admin keys
      localStorage.setItem("super_auth_token", response.token);
      localStorage.setItem("super_username", response.username);

      router.push("/super-admin/dashboard");
    } catch (error) {
      setErrors(extractErrors(error));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900"
    >
      <div className="grid gap-5">
        {errors.non_field_errors && (
          <div className="rounded-lg bg-red-50 p-3.5 text-sm font-medium text-red-800 dark:bg-red-950/30 dark:text-red-400">
            {errors.non_field_errors}
          </div>
        )}

        <div>
          <label
            htmlFor="username"
            className="block text-sm font-semibold text-slate-900 dark:text-slate-200"
          >
            System Username <span className="text-red-500">*</span>
          </label>
          <input
            id="username"
            name="username"
            type="text"
            value={form.username}
            onChange={(event) => updateField("username", event.target.value)}
            className="mt-2 min-h-11 w-full rounded-xl border border-slate-200 bg-transparent px-4 py-2 text-sm text-slate-900 placeholder-slate-400 outline-none transition focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/10 dark:border-slate-800 dark:text-slate-100 dark:focus:border-emerald-500"
            placeholder="e.g. admin"
            disabled={isSubmitting}
            required
          />
          <FieldError message={errors.username} />
        </div>

        <div>
          <label
            htmlFor="password"
            className="block text-sm font-semibold text-slate-900 dark:text-slate-200"
          >
            Password <span className="text-red-500">*</span>
          </label>
          <div className="relative mt-2">
            <input
              id="password"
              name="password"
              type={showPassword ? "text" : "password"}
              value={form.password}
              onChange={(event) => updateField("password", event.target.value)}
              className="min-h-11 w-full rounded-xl border border-slate-200 bg-transparent pl-4 pr-12 py-2 text-sm text-slate-900 placeholder-slate-400 outline-none transition focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/10 dark:border-slate-800 dark:text-slate-100 dark:focus:border-emerald-500"
              placeholder="••••••••"
              disabled={isSubmitting}
              required
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute inset-y-0 right-0 flex items-center px-4 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 focus:outline-none"
              tabIndex={-1}
            >
              {showPassword ? (
                <EyeOff className="h-5 w-5" />
              ) : (
                <Eye className="h-5 w-5" />
              )}
            </button>
          </div>
          <FieldError message={errors.password} />
        </div>

        <button
          type="submit"
          disabled={isSubmitting || !canSubmit}
          className="mt-2 inline-flex min-h-11 items-center justify-center rounded-xl bg-emerald-700 px-4 py-2 text-sm font-semibold text-white shadow transition hover:bg-emerald-800 focus:outline-none focus:ring-2 focus:ring-emerald-600 focus:ring-offset-2 disabled:bg-slate-100 disabled:text-slate-400 dark:bg-emerald-600 dark:hover:bg-emerald-700 dark:disabled:bg-slate-800 dark:disabled:text-slate-600"
        >
          {isSubmitting ? (
            <svg className="h-5 w-5 animate-spin text-current" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          ) : (
            "Access Admin Console"
          )}
        </button>
      </div>
    </form>
  );
}
