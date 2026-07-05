"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useMemo, useState } from "react";

import { Eye, EyeOff } from "lucide-react";
import Link from "next/link";

import { ApiError, apiRequest } from "@/lib/api/client";
import { PhoneInput } from "@/components/common/PhoneInput";

type FieldErrors = Partial<Record<keyof FormState | "non_field_errors", string>>;

type FormState = {
  mobile_number: string;
  password: string;
};

type LoginResponse = {
  token: string;
  mobile_number: string;
  mosque_id: number;
  mosque_name: string;
  must_change_password?: boolean;
};

const initialFormState: FormState = {
  mobile_number: "",
  password: "",
};

function extractErrors(error: unknown): FieldErrors {
  if (
    !(error instanceof ApiError) ||
    !error.details ||
    typeof error.details !== "object"
  ) {
    return {
      non_field_errors: "Invalid login credentials. Please try again.",
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

  return <p className="mt-2 text-sm text-red-700">{message}</p>;
}

export function LoginForm() {
  const router = useRouter();
  const [form, setForm] = useState<FormState>(initialFormState);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const canSubmit = useMemo(
    () =>
      form.mobile_number.trim().length > 0 && form.password.trim().length > 0,
    [form.mobile_number, form.password],
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
    if (!form.mobile_number.trim()) {
      nextErrors.mobile_number = "Primary WhatsApp Contact is required.";
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
        path: "/auth/login/",
        method: "POST",
        body: JSON.stringify(form),
      });

      // Save token and metadata in localStorage
      localStorage.setItem("auth_token", response.token);
      localStorage.setItem("admin_mobile", response.mobile_number);
      localStorage.setItem("admin_mosque_id", String(response.mosque_id));
      localStorage.setItem("admin_mosque_name", response.mosque_name);

      // Route to dashboard
      if (response.must_change_password) {
        localStorage.setItem("must_change_password", "true");
        router.push("/change-password");
      } else {
        localStorage.removeItem("must_change_password");
        router.push("/dashboard");
      }
    } catch (error) {
      setErrors(extractErrors(error));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-2xl border border-slate-900/10 bg-white p-5 shadow-soft sm:p-6"
    >
      <div className="grid gap-5">
        <PhoneInput
          id="mobile_number"
          label="Primary WhatsApp Contact"
          value={form.mobile_number}
          onChange={(val) => updateField("mobile_number", val)}
          disabled={isSubmitting}
          error={errors.mobile_number}
          required
        />

        <div>
          <div className="flex items-center justify-between">
            <label
              htmlFor="password"
              className="block text-sm font-semibold text-slate-900"
            >
              Password <span className="text-red-700">*</span>
            </label>
            <Link
              href="/forgot-password"
              className="text-sm font-semibold text-emerald-900 hover:underline"
              tabIndex={-1}
            >
              Forgot password?
            </Link>
          </div>
          <div className="relative mt-2">
            <input
              id="password"
              name="password"
              type={showPassword ? "text" : "password"}
              value={form.password}
              onChange={(event) => updateField("password", event.target.value)}
              className="min-h-12 w-full rounded-xl border border-slate-200 pl-4 pr-12 text-slate-950 outline-none transition focus:border-emerald-900 focus:ring-4 focus:ring-emerald-900/10"
              autoComplete="current-password"
              disabled={isSubmitting}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute inset-y-0 right-0 flex items-center px-4 text-slate-400 hover:text-slate-600 focus:outline-none"
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

        {errors.non_field_errors ? (
          <div className="rounded-xl bg-red-50 p-3 text-sm text-red-800">
            {errors.non_field_errors}
          </div>
        ) : null}

        <button
          type="submit"
          disabled={isSubmitting || !canSubmit}
          className="min-h-12 rounded-full bg-emerald-900 px-6 text-sm font-semibold text-white transition hover:bg-emerald-950 focus:outline-none focus:ring-4 focus:ring-emerald-900/20 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSubmitting ? "Logging in..." : "Login"}
        </button>
      </div>
    </form>
  );
}
