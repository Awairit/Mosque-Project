import type { Metadata } from "next";
import { MosqueRegistrationForm } from "@/components/mosque-registration/MosqueRegistrationForm";
import { ShieldCheck, MessageCircle, UserCheck, KeyRound } from "lucide-react";

export const metadata: Metadata = {
  title: "Register a Mosque — Trust-First Onboarding",
  description:
    "Register your mosque on the platform. We verify every administrator's identity before approval.",
};

const STEPS = [
  {
    icon: MessageCircle,
    title: "Verify WhatsApp",
    description: "We verify you own the contact number before accepting your request.",
  },
  {
    icon: UserCheck,
    title: "Manual Identity Check",
    description: "Our Super Admin will contact you on WhatsApp to confirm your authority to represent the mosque.",
  },
  {
    icon: ShieldCheck,
    title: "Approved & Onboarded",
    description: "After approval, your temporary login credentials are sent securely.",
  },
  {
    icon: KeyRound,
    title: "Secure First Login",
    description: "You log in and immediately set your own permanent password.",
  },
];

export default function MosqueRegistrationPage() {
  return (
    <main className="min-h-screen bg-page px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto grid max-w-5xl gap-8 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
        {/* Left Panel */}
        <section className="pt-4 lg:sticky lg:top-8">
          <p className="inline-flex items-center gap-1.5 rounded-full border border-emerald-900/10 bg-white px-4 py-2 text-sm font-medium text-emerald-900 shadow-sm">
            <ShieldCheck className="h-4 w-4" />
            Trust-First Onboarding
          </p>
          <h1 className="mt-6 text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">
            Register your mosque.
          </h1>
          <p className="mt-5 max-w-xl leading-7 text-slate-600">
            This platform is built on verified, trustworthy information. Every mosque administrator
            is manually verified before gaining access.
          </p>

          <div className="mt-8 space-y-4">
            {STEPS.map((s, i) => {
              const Icon = s.icon;
              return (
                <div key={s.title} className="flex items-start gap-4 rounded-2xl border border-slate-100 bg-white/80 p-4">
                  <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-emerald-50 text-emerald-800">
                    <Icon className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-900">
                      <span className="mr-1.5 text-xs font-bold text-emerald-700">{i + 1}.</span>
                      {s.title}
                    </p>
                    <p className="mt-0.5 text-xs leading-5 text-slate-500">{s.description}</p>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-xs text-amber-800">
            <strong className="font-semibold">Important:</strong> A person does not become a Mosque
            Admin simply by submitting this form. Automation verifies contact ownership.{" "}
            <strong>Super Admin verifies authority.</strong>
          </div>
        </section>

        {/* Right Panel: Form */}
        <MosqueRegistrationForm />
      </div>
    </main>
  );
}
