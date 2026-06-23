import type { Metadata } from "next";

import { MosqueRegistrationForm } from "@/components/mosque-registration/MosqueRegistrationForm";

export const metadata: Metadata = {
  title: "Register a Mosque",
  description: "Request to register a mosque for verification by the platform team.",
};

export default function MosqueRegistrationPage() {
  return (
    <main className="min-h-screen bg-page px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto grid max-w-5xl gap-8 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
        <section className="pt-4 lg:sticky lg:top-8">
          <p className="inline-flex rounded-full border border-emerald-900/10 bg-white px-4 py-2 text-sm font-medium text-emerald-900 shadow-sm">
            Mosque registration
          </p>
          <h1 className="mt-6 text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">
            Request to add your mosque.
          </h1>
          <p className="mt-5 max-w-xl leading-7 text-slate-600">
            Submit the basic mosque details and our platform team will review the request before
            publishing anything publicly.
          </p>
          <div className="mt-6 rounded-2xl border border-emerald-900/10 bg-white/80 p-4 text-sm leading-6 text-slate-600">
            <p className="font-semibold text-slate-950">What happens next?</p>
            <p className="mt-2">
              Your request will appear in the Django admin panel as pending. A platform admin can
              manually approve or reject it after verification.
            </p>
          </div>
        </section>

        <MosqueRegistrationForm />
      </div>
    </main>
  );
}
