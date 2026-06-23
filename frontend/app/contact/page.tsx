import Link from "next/link";

export const metadata = {
  title: "Contact Us",
  description: "Get in touch with support, submit corrections, or resolve mosque onboarding issues.",
};

export default function ContactPage() {
  return (
    <main className="min-h-screen bg-[#F4F7F5] px-4 py-12 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-3xl rounded-2xl border border-slate-900/10 bg-white p-6 shadow-sm sm:p-8 space-y-6">
        <Link href="/" className="inline-flex items-center text-sm font-bold text-emerald-800 hover:text-emerald-950 transition-colors">
          ← Back to discovery
        </Link>
        <h1 className="text-3xl font-bold tracking-tight text-slate-950">Contact Us</h1>
        <p className="text-sm text-slate-600 leading-relaxed font-normal">
          If you have questions, need assistance registering a mosque, or need to suggest adjustments to prayer schedules, please reach out to our team using the channels below.
        </p>

        <section className="space-y-4">
          <div className="rounded-xl border border-slate-100 bg-slate-50/50 p-4 space-y-2">
            <h2 className="text-md font-bold text-slate-900">📧 General Support & Registration Issues</h2>
            <p className="text-xs text-slate-600 leading-relaxed font-normal">
              Need help validating credentials or managing your admin dashboard? Send us an email detailing your request:
            </p>
            <a href="mailto:support@example.com" className="text-sm font-semibold text-emerald-800 hover:underline block">
              support@example.com
            </a>
          </div>

          <div className="rounded-xl border border-slate-100 bg-slate-50/50 p-4 space-y-2">
            <h2 className="text-md font-bold text-slate-900">✏️ Timing Correction Requests</h2>
            <p className="text-xs text-slate-600 leading-relaxed font-normal">
              Notice an outdated or incorrect congregation time? 
              Please send the correct schedule, along with the name and location of the mosque, to our support email or submit a validation request to:
            </p>
            <a href="mailto:corrections@example.com" className="text-sm font-semibold text-emerald-800 hover:underline block">
              corrections@example.com
            </a>
          </div>

          <div className="rounded-xl border border-slate-100 bg-slate-50/50 p-4 space-y-2">
            <h2 className="text-md font-bold text-slate-900">📝 Suggest a New Mosque</h2>
            <p className="text-xs text-slate-600 leading-relaxed font-normal">
              Want to add a mosque to our directory? You can apply directly through our public onboarding form:
            </p>
            <Link href="/mosque-registration" className="text-sm font-bold text-emerald-800 hover:underline block">
              Submit Mosque Registration Form →
            </Link>
          </div>
        </section>
      </div>
    </main>
  );
}
