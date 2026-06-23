"use client";

import { FormEvent, useMemo, useState } from "react";

import { ApiError, apiRequest } from "@/lib/api/client";

type FieldErrors = Partial<Record<keyof FormState | "non_field_errors", string>>;

type FormState = {
  mosque_name: string;
  admin_name: string;
  mobile_number: string;
  city: string;
  address: string;
  google_maps_link: string;
  women_prayer_available: boolean;
  notes: string;
};

type SuccessResponse = {
  message: string;
  request_id: number;
  status: string;
};

const initialFormState: FormState = {
  mosque_name: "",
  admin_name: "",
  mobile_number: "",
  city: "",
  address: "",
  google_maps_link: "",
  women_prayer_available: false,
  notes: "",
};

function extractErrors(error: unknown): FieldErrors {
  if (!(error instanceof ApiError) || !error.details || typeof error.details !== "object") {
    return {
      non_field_errors: "Something went wrong. Please try again.",
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

export function MosqueRegistrationForm() {
  const [form, setForm] = useState<FormState>(initialFormState);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [successMessage, setSuccessMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const canSubmit = useMemo(
    () => form.mosque_name.trim().length > 0 && form.mobile_number.trim().length > 0,
    [form.mobile_number, form.mosque_name],
  );

  const updateField = <TField extends keyof FormState>(field: TField, value: FormState[TField]) => {
    setForm((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: undefined, non_field_errors: undefined }));
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSuccessMessage("");

    const nextErrors: FieldErrors = {};
    if (!form.mosque_name.trim()) {
      nextErrors.mosque_name = "Mosque name is required.";
    }
    if (!form.mobile_number.trim()) {
      nextErrors.mobile_number = "Mobile number is required.";
    }

    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors);
      return;
    }

    setIsSubmitting(true);
    setErrors({});

    try {
      const response = await apiRequest<SuccessResponse>({
        path: "/mosque-registration/",
        method: "POST",
        body: JSON.stringify(form),
      });

      setSuccessMessage(response.message);
      setForm(initialFormState);
    } catch (error) {
      setErrors(extractErrors(error));
    } finally {
      setIsSubmitting(false);
    }
  };

  if (successMessage) {
    return (
      <div className="rounded-2xl border border-emerald-900/10 bg-white p-6 shadow-soft">
        <div className="rounded-full bg-emerald-50 px-4 py-2 text-sm font-semibold text-emerald-900">
          Request submitted
        </div>
        <h2 className="mt-5 text-2xl font-semibold text-slate-950">Thank you</h2>
        <p className="mt-3 leading-7 text-slate-600">{successMessage}</p>
        <button
          type="button"
          onClick={() => setSuccessMessage("")}
          className="mt-6 min-h-12 rounded-full bg-emerald-900 px-6 text-sm font-semibold text-white transition hover:bg-emerald-950 focus:outline-none focus:ring-4 focus:ring-emerald-900/20"
        >
          Submit another request
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-2xl border border-slate-900/10 bg-white p-5 shadow-soft sm:p-6">
      <div className="grid gap-5">
        <div>
          <label htmlFor="mosque_name" className="block text-sm font-semibold text-slate-900">
            Mosque name <span className="text-red-700">*</span>
          </label>
          <input
            id="mosque_name"
            name="mosque_name"
            value={form.mosque_name}
            onChange={(event) => updateField("mosque_name", event.target.value)}
            className="mt-2 min-h-12 w-full rounded-xl border border-slate-200 px-4 text-slate-950 outline-none transition focus:border-emerald-900 focus:ring-4 focus:ring-emerald-900/10"
            autoComplete="organization"
          />
          <FieldError message={errors.mosque_name} />
        </div>

        <div>
          <label htmlFor="admin_name" className="block text-sm font-semibold text-slate-900">
            Your name
          </label>
          <input
            id="admin_name"
            name="admin_name"
            value={form.admin_name}
            onChange={(event) => updateField("admin_name", event.target.value)}
            className="mt-2 min-h-12 w-full rounded-xl border border-slate-200 px-4 text-slate-950 outline-none transition focus:border-emerald-900 focus:ring-4 focus:ring-emerald-900/10"
            autoComplete="name"
          />
          <FieldError message={errors.admin_name} />
        </div>

        <div>
          <label htmlFor="mobile_number" className="block text-sm font-semibold text-slate-900">
            Mobile number <span className="text-red-700">*</span>
          </label>
          <input
            id="mobile_number"
            name="mobile_number"
            value={form.mobile_number}
            onChange={(event) => updateField("mobile_number", event.target.value)}
            className="mt-2 min-h-12 w-full rounded-xl border border-slate-200 px-4 text-slate-950 outline-none transition focus:border-emerald-900 focus:ring-4 focus:ring-emerald-900/10"
            autoComplete="tel"
            inputMode="tel"
          />
          <FieldError message={errors.mobile_number} />
        </div>

        <div>
          <label htmlFor="city" className="block text-sm font-semibold text-slate-900">
            City
          </label>
          <input
            id="city"
            name="city"
            value={form.city}
            onChange={(event) => updateField("city", event.target.value)}
            className="mt-2 min-h-12 w-full rounded-xl border border-slate-200 px-4 text-slate-950 outline-none transition focus:border-emerald-900 focus:ring-4 focus:ring-emerald-900/10"
            autoComplete="address-level2"
          />
          <FieldError message={errors.city} />
        </div>

        <div>
          <label htmlFor="address" className="block text-sm font-semibold text-slate-900">
            Address
          </label>
          <textarea
            id="address"
            name="address"
            value={form.address}
            onChange={(event) => updateField("address", event.target.value)}
            rows={3}
            className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 text-slate-950 outline-none transition focus:border-emerald-900 focus:ring-4 focus:ring-emerald-900/10"
          />
          <FieldError message={errors.address} />
        </div>

        <div>
          <label htmlFor="google_maps_link" className="block text-sm font-semibold text-slate-900">
            Google Maps link
          </label>
          <input
            id="google_maps_link"
            name="google_maps_link"
            value={form.google_maps_link}
            onChange={(event) => updateField("google_maps_link", event.target.value)}
            className="mt-2 min-h-12 w-full rounded-xl border border-slate-200 px-4 text-slate-950 outline-none transition focus:border-emerald-900 focus:ring-4 focus:ring-emerald-900/10"
            inputMode="url"
          />
          <FieldError message={errors.google_maps_link} />
        </div>

        <label className="flex items-start gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4">
          <input
            type="checkbox"
            checked={form.women_prayer_available}
            onChange={(event) => updateField("women_prayer_available", event.target.checked)}
            className="mt-1 h-5 w-5 rounded border-slate-300 text-emerald-900 focus:ring-emerald-900"
          />
          <span>
            <span className="block text-sm font-semibold text-slate-900">
              Women&apos;s prayer space is available
            </span>
            <span className="mt-1 block text-sm text-slate-600">
              This helps visitors understand available facilities before they arrive.
            </span>
          </span>
        </label>

        <div>
          <label htmlFor="notes" className="block text-sm font-semibold text-slate-900">
            Notes
          </label>
          <textarea
            id="notes"
            name="notes"
            value={form.notes}
            onChange={(event) => updateField("notes", event.target.value)}
            rows={4}
            className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 text-slate-950 outline-none transition focus:border-emerald-900 focus:ring-4 focus:ring-emerald-900/10"
            placeholder="Share anything useful for verification."
          />
          <FieldError message={errors.notes} />
        </div>

        <FieldError message={errors.non_field_errors} />

        <button
          type="submit"
          disabled={isSubmitting || !canSubmit}
          className="min-h-12 rounded-full bg-emerald-900 px-6 text-sm font-semibold text-white transition hover:bg-emerald-950 focus:outline-none focus:ring-4 focus:ring-emerald-900/20 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSubmitting ? "Submitting request..." : "Submit registration request"}
        </button>
      </div>
    </form>
  );
}
