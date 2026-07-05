import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "For Mosques",
  description: "Learn how to register and manage your mosque's profile, prayer timings, and announcements on Mosque Finder.",
};

export default function ForMosquesPage() {
  const faqs = [
    {
      q: "Is there any cost to register or use this platform?",
      a: "No. Mosque Finder is completely free of charge for mosques and public users alike. Our goal is to provide a clean, accessible service to connect the community."
    },
    {
      q: "How long does the mosque registration approval take?",
      a: "Our team reviews registration requests manually to verify credentials and contact details. This process typically takes less than 24 hours. Once approved, you will receive login details."
    },
    {
      q: "Can we upload our existing yearly prayer timetable?",
      a: "Yes. Our dashboard supports uploading yearly calendars in standard CSV format, and we are working on direct Excel (.xlsx) import support. Naive times are stored in local timezones."
    },
    {
      q: "Can we display our timings on external TVs or screens?",
      a: "Yes. Every approved mosque receives a public detail page with a clean layout, and all timing data is served via our REST API. You can read the JSON endpoints directly for custom displays."
    }
  ];

  return (
    <main className="min-h-screen bg-[#F4F7F5] px-4 py-12 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-4xl space-y-12">
        {/* Hero Section */}
        <section className="text-center space-y-4">
          <p className="inline-flex rounded-full border border-emerald-900/10 bg-white/70 px-4 py-2 text-sm font-semibold text-emerald-800 shadow-sm">
            Onboarding Portal
          </p>
          <h1 className="text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">
            Empower your mosque, connect your community.
          </h1>
          <p className="mx-auto max-w-2xl text-base leading-7 text-slate-600 sm:text-lg">
            Register your mosque to manage congregational (jamaat) timings, publish local events,
            share Janazah notices, and provide directions to visitors in one clean experience.
          </p>
          
          <div className="pt-6 flex flex-col gap-3 justify-center sm:flex-row sm:items-center">
            <Link
              href="/mosque-registration"
              className="inline-flex min-h-12 items-center justify-center rounded-full bg-emerald-800 px-6 text-sm font-bold text-white shadow-lg hover:bg-emerald-900 transition focus:outline-none focus:ring-4 focus:ring-emerald-800/20"
            >
              Register Your Mosque
            </Link>
            <Link
              href="/login"
              className="inline-flex min-h-12 items-center justify-center rounded-full border border-slate-200 bg-white px-6 text-sm font-bold text-slate-800 shadow-sm hover:bg-slate-50 transition focus:outline-none focus:ring-4 focus:ring-slate-950/10"
            >
              Access Admin Login
            </Link>
          </div>
        </section>

        {/* Benefits Grid */}
        <section className="grid gap-6 sm:grid-cols-2">
          <div className="rounded-2xl border border-slate-900/10 bg-white p-6 shadow-sm">
            <h3 className="text-lg font-bold text-slate-900 font-sans">📋 Timetable Management</h3>
            <p className="mt-2 text-sm text-slate-600 leading-relaxed font-normal">
              Manage both daily prayer times and Friday Jumuah shifts. Update timings instantly when congregation
              schedules change for Daylight Savings or seasonal shifts.
            </p>
          </div>
          <div className="rounded-2xl border border-slate-900/10 bg-white p-6 shadow-sm">
            <h3 className="text-lg font-bold text-slate-900 font-sans">📢 Announcements & Events</h3>
            <p className="mt-2 text-sm text-slate-600 leading-relaxed font-normal">
              Publish news, Ramadan program details, weekly dars lectures, and youth events. Control public visibility
              with simple draft, published, and archived workflows.
            </p>
          </div>
          <div className="rounded-2xl border border-slate-900/10 bg-white p-6 shadow-sm">
            <h3 className="text-lg font-bold text-slate-900 font-sans">🖤 Janazah Notice Broadcasts</h3>
            <p className="mt-2 text-sm text-slate-600 leading-relaxed font-normal">
              Create funeral announcements with custom Salah times, burial details, GPS cemetery coordinates, and
              pre-formatted WhatsApp share links.
            </p>
          </div>
          <div className="rounded-2xl border border-slate-900/10 bg-white p-6 shadow-sm">
            <h3 className="text-lg font-bold text-slate-900 font-sans">🔒 Multi-Tenancy Protection</h3>
            <p className="mt-2 text-sm text-slate-600 leading-relaxed font-normal">
              Secure authentication boundaries guarantee that only verified, assigned administrators can modify your
              mosque's database profile and schedule listings.
            </p>
          </div>
        </section>

        {/* Approval Workflow */}
        <section className="rounded-2xl border border-slate-900/10 bg-white p-6 sm:p-8 shadow-sm">
          <h2 className="text-2xl font-bold text-slate-900 font-sans">Verification & Approval Process</h2>
          <p className="mt-2 text-sm text-slate-600 font-normal">
            To ensure data integrity and prevent unauthorized changes, we follow a strict onboarding lifecycle:
          </p>
          
          <div className="mt-6 grid gap-6 md:grid-cols-3 text-center">
            <div className="space-y-2">
              <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-emerald-50 text-sm font-bold text-emerald-800 border border-emerald-100">1</span>
              <h4 className="text-sm font-bold text-slate-900">Request Submitted</h4>
              <p className="text-xs text-slate-500 font-normal">Fill the registration form with your mosque details and admin phone.</p>
            </div>
            <div className="space-y-2">
              <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-emerald-50 text-sm font-bold text-emerald-800 border border-emerald-100">2</span>
              <h4 className="text-sm font-bold text-slate-900">Platform Review</h4>
              <p className="text-xs text-slate-500 font-normal">Our system administrators verify details and contact coordinates manually.</p>
            </div>
            <div className="space-y-2">
              <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-emerald-50 text-sm font-bold text-emerald-800 border border-emerald-100">3</span>
              <h4 className="text-sm font-bold text-slate-900">Credentials Sent</h4>
              <p className="text-xs text-slate-500 font-normal">Upon approval, login credentials are generated and provided to begin setup.</p>
            </div>
          </div>
        </section>

        {/* FAQ Section */}
        <section className="space-y-6">
          <h2 className="text-2xl font-bold text-slate-900 font-sans text-center">Frequently Asked Questions</h2>
          <div className="space-y-4">
            {faqs.map((faq, i) => (
              <div key={i} className="rounded-2xl border border-slate-900/10 bg-white p-5 shadow-sm">
                <h4 className="text-sm font-bold text-slate-900 font-sans">❓ {faq.q}</h4>
                <p className="mt-2 text-xs text-slate-600 leading-relaxed font-normal">{faq.a}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Final CTA */}
        <section className="text-center pt-4">
          <h3 className="text-lg font-bold text-slate-900 font-sans">Ready to list your mosque?</h3>
          <p className="mt-2 text-sm text-slate-500 font-normal">Listing takes less than 5 minutes. Get started today.</p>
          <div className="mt-4">
            <Link
              href="/mosque-registration"
              className="inline-flex min-h-12 items-center justify-center rounded-full bg-emerald-800 px-8 text-sm font-bold text-white hover:bg-emerald-900 shadow-lg transition"
            >
              Add Your Mosque Now
            </Link>
          </div>
        </section>
      </div>
    </main>
  );
}
