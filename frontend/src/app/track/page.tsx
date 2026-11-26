"use client";

import { FormEvent, Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Search } from "lucide-react";
import { PublicTrackResponse, trackGrievance } from "@/lib/api";
import { StatusTimeline } from "@/components/StatusTimeline";

function TrackContent() {
  const searchParams = useSearchParams();
  const initialTicket = searchParams.get("ticket") || "";

  const [ticketId, setTicketId] = useState(initialTicket);
  const [anonCode, setAnonCode] = useState("");
  const [result, setResult] = useState<PublicTrackResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const runLookup = async (ticket: string, code?: string) => {
    if (!ticket.trim()) return;
    setLoading(true);
    setError("");
    try {
      const data = await trackGrievance(ticket, code);
      setResult(data);
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : "Ticket not found");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (initialTicket) {
      runLookup(initialTicket);
    }
  }, [initialTicket]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    runLookup(ticketId, anonCode);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="gov-card p-6 space-y-4">
        <div>
          <h1 id="main-content" tabIndex={-1} className="text-2xl font-bold">
            Track Grievance Status
          </h1>
          <p className="text-sm text-slate-600 dark:text-slate-300 mt-1">
            No login required. Enter your Ticket ID (and Private Code if verifying an anonymous ticket).
          </p>
        </div>

        <search>
          <form onSubmit={handleSubmit} className="grid sm:grid-cols-3 gap-3">
            <div className="sm:col-span-2">
              <label htmlFor="track-ticket" className="block text-xs font-semibold mb-1">
                Ticket ID <span aria-hidden="true">*</span>
              </label>
              <input
                id="track-ticket"
                name="ticket_id"
                type="text"
                className="gov-input"
                placeholder="GRV-2026-100001"
                value={ticketId}
                onChange={(e) => setTicketId(e.target.value)}
                autoCorrect="off"
                autoCapitalize="characters"
                spellCheck={false}
                required
              />
            </div>

            <div>
              <label htmlFor="track-anon" className="block text-xs font-semibold mb-1">
                Anonymous Code (Optional)
              </label>
              <input
                id="track-anon"
                name="anonymous_code"
                type="text"
                className="gov-input"
                placeholder="ANON-XXXX"
                value={anonCode}
                onChange={(e) => setAnonCode(e.target.value)}
                autoCorrect="off"
                autoCapitalize="characters"
                spellCheck={false}
              />
            </div>

            <div className="sm:col-span-3">
              <button
                type="submit"
                disabled={loading}
                className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-lg bg-blue-900 text-white hover:bg-blue-800 dark:bg-blue-500 dark:text-slate-950 font-semibold min-h-[48px]"
              >
                <Search className="w-4 h-4" aria-hidden="true" />
                {loading ? "Searching..." : "Track Grievance"}
              </button>
            </div>
          </form>
        </search>

        {error && (
          <div role="alert" className="p-3 rounded-lg bg-red-50 dark:bg-red-950/50 border border-red-300 dark:border-red-800 text-sm text-red-800 dark:text-red-200">
            {error}
          </div>
        )}
      </div>

      {result && (
        <article className="gov-card p-6 space-y-5">
          <div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-200 dark:border-slate-700 pb-4">
            <div>
              <p className="text-xs font-mono text-slate-500">{result.ticket_id}</p>
              <h2 className="text-xl font-bold mt-0.5">{result.title}</h2>
            </div>
            <div className="flex gap-2">
              <span className="px-2.5 py-1 rounded-full text-xs font-semibold uppercase bg-blue-100 text-blue-900 dark:bg-blue-950 dark:text-blue-200">
                {result.status.replace("_", " ")}
              </span>
              <span className="px-2.5 py-1 rounded-full text-xs font-semibold uppercase bg-amber-100 text-amber-900 dark:bg-amber-950 dark:text-amber-200">
                {result.priority}
              </span>
            </div>
          </div>

          <dl className="grid sm:grid-cols-3 gap-4 text-sm">
            <div>
              <dt className="text-xs text-slate-500">Department</dt>
              <dd className="font-semibold">{result.department_name || result.category}</dd>
            </div>
            <div>
              <dt className="text-xs text-slate-500">Ward / Area</dt>
              <dd className="font-semibold">{result.ward_name || "Not specified"}</dd>
            </div>
            <div>
              <dt className="text-xs text-slate-500">Estimated Resolution (SLA)</dt>
              <dd className="font-semibold">
                {result.estimated_resolution_at
                  ? new Date(result.estimated_resolution_at).toLocaleString()
                  : "Pending"}
              </dd>
            </div>
          </dl>

          <StatusTimeline currentStatus={result.status} history={result.status_history} />
        </article>
      )}
    </div>
  );
}

export default function TrackPage() {
  return (
    <Suspense fallback={<div className="text-sm text-slate-500">Loading tracker...</div>}>
      <TrackContent />
    </Suspense>
  );
}
