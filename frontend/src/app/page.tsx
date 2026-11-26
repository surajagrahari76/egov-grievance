"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { FilePlus2, Search, ClipboardList, ShieldAlert } from "lucide-react";

export default function HomePage() {
  const router = useRouter();
  const [ticketId, setTicketId] = useState("");

  const handleQuickTrack = (e: FormEvent) => {
    e.preventDefault();
    if (!ticketId.trim()) return;
    router.push(`/track?ticket=${encodeURIComponent(ticketId.trim())}`);
  };

  return (
    <div className="space-y-8">
      <section className="gov-card p-6 sm:p-10 bg-gradient-to-br from-blue-950 to-slate-900 text-white border-0">
        <div className="max-w-3xl space-y-4">
          <span className="inline-block px-3 py-1 rounded-full text-xs font-semibold bg-amber-500 text-slate-950">
            Citizen-First Public Grievance Portal
          </span>
          <h1 id="main-content" tabIndex={-1} className="text-3xl sm:text-4xl font-bold tracking-tight">
            JanSamadhan AI — E-Governance Grievance Redressal
          </h1>
          <p className="text-slate-200 text-base sm:text-lg">
            Report civic issues across Water, Electricity, Roads, Sanitation, Public Health, or Safety.
            Track progress transparently with guaranteed SLA timelines.
          </p>

          <div className="flex flex-wrap gap-3 pt-2">
            <Link
              href="/submit"
              className="inline-flex items-center gap-2 px-5 py-3 rounded-lg bg-amber-500 text-slate-950 font-semibold hover:bg-amber-400"
            >
              <FilePlus2 className="w-5 h-5" aria-hidden="true" />
              File a Complaint
            </Link>
            <Link
              href="/login"
              className="inline-flex items-center gap-2 px-5 py-3 rounded-lg bg-white/10 text-white border border-white/25 font-semibold hover:bg-white/20"
            >
              Citizen / Officer Login
            </Link>
          </div>
        </div>
      </section>

      <section className="gov-card p-6">
        <h2 className="text-lg font-bold mb-3">Quick Track by Ticket ID</h2>
        <search>
          <form onSubmit={handleQuickTrack} className="flex flex-col sm:flex-row gap-3">
            <div className="flex-1">
              <label htmlFor="quick-ticket" className="visually-hidden">
                Ticket ID
              </label>
              <input
                id="quick-ticket"
                name="ticket"
                type="text"
                className="gov-input"
                placeholder="Enter Ticket ID (e.g., GRV-2026-100001)"
                value={ticketId}
                onChange={(e) => setTicketId(e.target.value)}
                autoCorrect="off"
                autoCapitalize="characters"
                spellCheck={false}
                required
              />
            </div>
            <button
              type="submit"
              className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-lg bg-blue-900 text-white hover:bg-blue-800 dark:bg-blue-500 dark:text-slate-950 font-semibold min-h-[48px]"
            >
              <Search className="w-4 h-4" aria-hidden="true" />
              Track Status
            </button>
          </form>
        </search>
      </section>

      <section className="grid sm:grid-cols-3 gap-4">
        <Link href="/submit" className="gov-card p-5 hover:border-blue-500 transition-colors space-y-2">
          <FilePlus2 className="w-7 h-7 text-blue-700 dark:text-blue-400" aria-hidden="true" />
          <h2 className="font-bold text-lg">Submit Grievance</h2>
          <p className="text-sm text-slate-600 dark:text-slate-300">
            Attach photos, auto-detect GPS location, or file anonymously with a private tracking code.
          </p>
        </Link>

        <Link href="/my-complaints" className="gov-card p-5 hover:border-blue-500 transition-colors space-y-2">
          <ClipboardList className="w-7 h-7 text-emerald-700 dark:text-emerald-400" aria-hidden="true" />
          <h2 className="font-bold text-lg">My Complaints</h2>
          <p className="text-sm text-slate-600 dark:text-slate-300">
            View all submitted complaints, stage-by-stage timeline, and estimated resolution deadline.
          </p>
        </Link>

        <Link href="/track?ticket=GRV-2026-100001" className="gov-card p-5 hover:border-blue-500 transition-colors space-y-2">
          <ShieldAlert className="w-7 h-7 text-amber-600" aria-hidden="true" />
          <h2 className="font-bold text-lg">Try Seeded Ticket</h2>
          <p className="text-sm text-slate-600 dark:text-slate-300">
            Inspect sample ticket <code>GRV-2026-100001</code> or anonymous ticket{" "}
            <code>GRV-2026-100003</code>.
          </p>
        </Link>
      </section>
    </div>
  );
}
