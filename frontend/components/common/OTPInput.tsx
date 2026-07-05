import React, { useRef, useEffect } from "react";

interface OTPInputProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

export function OTPInput({ value, onChange, disabled = false }: OTPInputProps) {
  const length = 6;
  const inputsRef = useRef<(HTMLInputElement | null)[]>([]);

  // Split value into array
  const otpArray = value.split("").slice(0, length);
  while (otpArray.length < length) {
    otpArray.push("");
  }

  // Focus the first input on load
  useEffect(() => {
    inputsRef.current[0]?.focus();
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>, idx: number) => {
    const val = e.target.value;
    if (!/^\d*$/.test(val)) return; // Digits only

    const newOtpArray = [...otpArray];
    newOtpArray[idx] = val.slice(-1); // Take last digit if multiple entered
    const newOtp = newOtpArray.join("");
    onChange(newOtp);

    // Focus next if this slot is filled
    if (val && idx < length - 1) {
      inputsRef.current[idx + 1]?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>, idx: number) => {
    if (e.key === "Backspace") {
      if (!otpArray[idx] && idx > 0) {
        // Current slot is empty, backspace to previous and clear it
        const newOtpArray = [...otpArray];
        newOtpArray[idx - 1] = "";
        onChange(newOtpArray.join(""));
        inputsRef.current[idx - 1]?.focus();
      } else {
        // Clear current slot
        const newOtpArray = [...otpArray];
        newOtpArray[idx] = "";
        onChange(newOtpArray.join(""));
      }
    } else if (e.key === "ArrowLeft" && idx > 0) {
      inputsRef.current[idx - 1]?.focus();
    } else if (e.key === "ArrowRight" && idx < length - 1) {
      inputsRef.current[idx + 1]?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault();
    const pasteData = e.clipboardData.getData("text").trim();
    if (!/^\d+$/.test(pasteData)) return; // Only allow digits

    const digits = pasteData.slice(0, length);
    onChange(digits);

    // Focus corresponding input
    const focusIndex = Math.min(digits.length, length - 1);
    inputsRef.current[focusIndex]?.focus();
  };

  return (
    <div className="flex gap-2.5 sm:gap-3.5 justify-center" onPaste={handlePaste}>
      {otpArray.map((digit, idx) => (
        <input
          key={idx}
          ref={(el) => {
            inputsRef.current[idx] = el;
          }}
          type="text"
          inputMode="numeric"
          pattern="[0-9]*"
          maxLength={1}
          value={digit}
          onChange={(e) => handleChange(e, idx)}
          onKeyDown={(e) => handleKeyDown(e, idx)}
          disabled={disabled}
          className="h-12 w-10 sm:h-14 sm:w-12 rounded-xl border border-slate-200 text-center text-xl sm:text-2xl font-bold text-slate-900 outline-none transition focus:border-emerald-600 focus:ring-4 focus:ring-emerald-900/10 disabled:bg-slate-50 disabled:text-slate-400 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-100"
          placeholder="-"
        />
      ))}
    </div>
  );
}
