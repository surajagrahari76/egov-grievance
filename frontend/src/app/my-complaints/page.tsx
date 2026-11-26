"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { fetchMyGrievances, getStoredUser, Grievance } from "@/lib/api";
import { StatusTimeline } from "@/components/StatusTimeline";

export default function MyComplaintsPage() {
  const [items, setItems] = useState<Grievance[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [loggedIn, setLoggedIn] = useState(false);

  const load = async (targetPage: number, filter: string) => {
    setLoading(true);
    setError("");
    try {
      const data = await fetchMyGrievances(targetPage, filter);
      setItems(data.items);
      setTotalPages(data.total_pages);
      setPage(data.page);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load complaints");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const user = getStoredUser();
    setLoggedIn(Boolean(user));
    if (user) {
      load(1, "");
    } else {
      setLoading(false);
    }
  }, []);

  if (!loggedIn && !loading) {
    return (
      <div className="max-w-xl mx-auto gov-card p-8 text-center space-y-4">
        <h1 id="main-content" tabIndex={-1} className="text-2xl font-bold">
          My Complaints
        </h1>
        <p className="text-sm text-slate-600 dark:text-slate-300">
          Please sign in with your mobile OTP to view your filed complaints, or track an individual ticket without logging in.
        </p>
        <div className="flex justify-center gap-3">
          <Link href="/login" className="px-5 py-2.5 rounded-lg bg-blue-900 text-white font-semibold">
            Sign In
          </Link>
          <Link href="/track" className="px-5 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 font-semibold">
            Track Ticket
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 id="main-content" tabIndex={-1} className="text-2xl font-bold">
            My Complaints
          </h1>
          <p className="text-sm text-slate-600 dark:text-slate-300">
            Track status progression and estimated resolution times.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <label htmlFor="status-filter" className="text-sm font-semibold">
            Status:
          </label>
          <select
            id="status-filter"
            className="gov-input !w-auto !min-h-[42px]"
            value={statusFilter}
            onChange={(e) => {
              const next = e.target.value;
              setStatusFilter(next);
              load(1, next);
            }}
          >
            <option value="">All</option>
            <option value="submitted">Submitted</option>
            <option value="assigned">Assigned</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
          </select>
        </div>
      </div>

      {error && (
        <div role="alert" className="p-3 rounded-lg bg-red-50 dark:bg-red-950/50 border border-red-300 text-sm text-red-800 dark:text-red-200">
          {error}
        </div>
      )}

      {loading ? (
        <div className="gov-card p-8 text-center text-sm text-slate-500">Loading complaints...</div>
      ) : items.length === 0 ? (
        <div className="gov-card p-8 text-center space-y-3">
          <p className="text-slate-600 dark:text-slate-300">No complaints found.</p>
          <Link href="/submit" className="inline-block px-5 py-2.5 rounded-lg bg-blue-900 text-white font-semibold">
            File a New Complaint
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {items.map((g) => (
            <article key={g.id} className="gov-card p-5 sm:p-6 space-y-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <span className="font-mono font-semibold">{g.ticket_id}</span>
                    <span>•</span>
                    <span>{g.department?.name || g.category}</span>
                    {g.ward && (
                      <>
                        <span>•</span>
                        <span>{g.ward.name}</span>
                      </>
                    )}
                  </div>
                  <h2 className="text-lg font-bold mt-1">{g.title}</h2>
                  <p className="text-sm text-slate-600 dark:text-slate-300 mt-1">{g.text}</p>
                </div>

                <div className="flex gap-2">
                  <span className="px-2.5 py-1 rounded-full text-xs font-semibold uppercase bg-blue-100 text-blue-900 dark:bg-blue-950 dark:text-blue-200">
                    {g.status.replace("_", " ")}
                  </span>
                  <span className="px-2.5 py-1 rounded-full text-xs font-semibold uppercase bg-amber-100 text-amber-900 dark:bg-amber-950 dark:text-amber-200">
                    {g.priority}
                  </span>
                </div>
              </div>

              {g.estimated_resolution_at && (
                <p className="text-xs text-slate-500">
                  Estimated Resolution: {new Date(g.estimated_resolution_at).toLocaleString()}
                </p>
              )}

              <StatusTimeline currentStatus={g.status} history={g.status_history} />
            </article>
          ))}

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-3 pt-2">
              <button
                type="button"
                disabled={page <= 1}
                onClick={() => load(page - 1, statusFilter)}
                className="px-4 py-2 rounded border border-slate-300 dark:border-slate-700 disabled:opacity-50"
              >
                Previous
              </button>
              <span className="text-sm">
                Page {page} of {totalPages}
              </span>
              <button
                type="button"
                disabled={page >= totalPages}
                onClick={() => load(page + 1, statusFilter)}
                className="px-4 py-2 rounded border border-slate-300 dark:border-slate-700 disabled:opacity-50"
              >
                Next
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
