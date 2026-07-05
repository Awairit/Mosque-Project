import React, { useState, useEffect } from "react";

export const COUNTRIES = [
  { code: "+91", label: "India", flag: "🇮🇳", placeholder: "98765 43210" },
  { code: "+966", label: "Saudi Arabia", flag: "🇸🇦", placeholder: "51 234 5678" },
  { code: "+971", label: "UAE", flag: "🇦🇪", placeholder: "50 123 4567" },
  { code: "+974", label: "Qatar", flag: "🇶🇦", placeholder: "5512 3456" },
  { code: "+965", label: "Kuwait", flag: "🇰🇼", placeholder: "5123 4567" },
  { code: "+968", label: "Oman", flag: "🇴🇲", placeholder: "9123 4567" },
  { code: "+44", label: "United Kingdom", flag: "🇬🇧", placeholder: "7123 456789" },
  { code: "+1", label: "USA / Canada", flag: "🇺🇸", placeholder: "201 555 0123" },
];

interface PhoneInputProps {
  value: string; // Combined E.164 number, e.g. "+919876543210"
  onChange: (value: string) => void;
  disabled?: boolean;
  error?: string;
  id?: string;
  label?: string;
  hint?: string;
  required?: boolean;
}

export function PhoneInput({
  value,
  onChange,
  disabled = false,
  error,
  id = "mobile_number",
  label,
  hint,
  required = false,
}: PhoneInputProps) {
  // Parse initial value
  const getInitialState = () => {
    if (value && value.startsWith("+")) {
      for (const country of COUNTRIES) {
        if (value.startsWith(country.code)) {
          return {
            country,
            local: value.slice(country.code.length),
          };
        }
      }
    }
    // Default to India
    return {
      country: COUNTRIES[0],
      local: value ? value.replace(/^\+/, "") : "",
    };
  };

  const initialState = getInitialState();
  const [selectedCountry, setSelectedCountry] = useState(initialState.country);
  const [localNumber, setLocalNumber] = useState(initialState.local);

  // Sync internal state with prop value changes from outside
  useEffect(() => {
    const updated = getInitialState();
    setSelectedCountry(updated.country);
    setLocalNumber(updated.local);
  }, [value]);

  const handleCountryChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const code = e.target.value;
    const country = COUNTRIES.find((c) => c.code === code) || COUNTRIES[0];
    setSelectedCountry(country);
    const cleanedLocal = localNumber.replace(/\D/g, "");
    onChange(country.code + cleanedLocal);
  };

  const handleNumberChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    const cleanedLocal = val.replace(/\D/g, "");
    setLocalNumber(cleanedLocal);
    onChange(selectedCountry.code + cleanedLocal);
  };

  return (
    <div className="grid gap-1.5 w-full">
      {label && (
        <label htmlFor={id} className="block text-sm font-semibold text-slate-800 dark:text-slate-200">
          {label} {required && <span className="text-red-600">*</span>}
        </label>
      )}
      {hint && <p className="text-xs text-slate-500">{hint}</p>}

      <div className="flex gap-2 w-full">
        {/* Country Selector Dropdown Overlay */}
        <div className="relative flex items-center rounded-xl border border-slate-200 bg-white px-2 focus-within:border-emerald-900 focus-within:ring-4 focus-within:ring-emerald-900/10 transition dark:border-slate-800 dark:bg-slate-950">
          <span className="text-lg mr-1 select-none">{selectedCountry.flag}</span>
          <select
            value={selectedCountry.code}
            onChange={handleCountryChange}
            disabled={disabled}
            className="bg-transparent text-sm font-semibold text-slate-900 outline-none pr-3 py-3 cursor-pointer disabled:cursor-not-allowed disabled:text-slate-400 dark:text-slate-100"
          >
            {COUNTRIES.map((c) => (
              <option key={c.code} value={c.code} className="dark:bg-slate-950 dark:text-slate-100">
                {c.code} ({c.label})
              </option>
            ))}
          </select>
        </div>

        {/* Local Mobile Number Input Field */}
        <input
          id={id}
          type="tel"
          value={localNumber}
          onChange={handleNumberChange}
          disabled={disabled}
          placeholder={selectedCountry.placeholder}
          inputMode="tel"
          autoComplete="tel"
          className="min-h-12 flex-1 rounded-xl border border-slate-200 px-4 text-slate-950 outline-none transition focus:border-emerald-900 focus:ring-4 focus:ring-emerald-900/10 disabled:bg-slate-50 disabled:text-slate-400 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-100 dark:focus:border-emerald-800"
        />
      </div>

      {error && <p className="text-sm text-red-650 font-medium">{error}</p>}
    </div>
  );
}
