"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { Filter, ArrowRight, ShieldAlert } from "lucide-react";
import {
  Department,
  fetchDepartments,
  fetchStaffGrievances,
  fetchWards,
  getStoredUser,
  getToken,
  Grievance,
  isStaffRole,
  User,
  Ward,
} from "@/lib/api";

export default function OfficerDashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [authorized, setAuthorized] = useState(false);

  const [items, setItems] = useState<Grievance[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const [departments, setDepartments] = useState<Department[]>([]);
  const [wards, setWards] = useState<Ward[]>([]);

  const [statusFilter, setStatusFilter] = useState("");
  const [deptFilter, setDeptFilter] = useState("");
  const [wardFilter, setWardFilter] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadQueue = useCallback(
    async (
      targetPage: number,
      filters: { status: string; dept: string; ward: string; priority: string }
    ) => {
      setLoading(true);
      setError("");
      try {
        const res = await fetchStaffGrievances({
          page: targetPage,
          page_size: 15,
          status: filters.status,
          dept_id: filters.dept,
          ward_id: filters.ward,
          priority: filters.priority,
        });
        setItems(res.items);
        setTotal(res.total);
        setPage(res.page);
        setTotalPages(res.total_pages);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load officer queue");
      } finally {
        setLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    const token = getToken();
    const stored = getStoredUser();
    if (!token || !stored || !isStaffRole(stored.role)) {
      router.replace("/login?tab=staff&next=/officer");
      return;
    }
    setUser(stored);
    setAuthorized(true);
    fetchDepartments().then(setDepartments).catch(() => {});
    fetchWards().then(setWards).catch(() => {});
    loadQueue(1, { status: "", dept: "", ward: "", priority: "" });
  }, [router, loadQueue]);

  if (!authorized) {
    return (
      <div className="gov-card p-8 text-center text-sm text-slate-500">
        Verifying staff access...
      </div>
    );
  }

  const handleApplyFilters = (e: FormEvent) => {
    e.preventDefault();
    loadQueue(1, {
      status: statusFilter,
      dept: deptFilter,
      ward: wardFilter,
      priority: priorityFilter,
    });
  };

  const resetFilters = () => {
    setStatusFilter("");
    setDeptFilter("");
    setWardFilter("");
    setPriorityFilter("");
    loadQueue(1, { status: "", dept: "", ward: "", priority: "" });
  };

  const canFilterAllDepts = user?.role === "admin" || user?.role === "district_head";

  const activeCount = items.filter((g) =>
    ["submitted", "assigned", "in_progress"].includes(g.status)
  ).length;
  const resolvedCount = items.filter((g) =>
    ["resolved", "closed"].includes(g.status)
  ).length;
  const highPriorityCount = items.filter((g) =>
    ["high", "critical"].includes(g.priority)
  ).length;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 id="main-content" tabIndex={-1} className="text-2xl font-bold">
            Officer & Admin Grievance Queue
          </h1>
          <p className="text-sm text-slate-600 dark:text-slate-300 mt-1">
            Signed in as <strong>{user?.name}</strong> ({user?.role.replace("_", " ").toUpperCase()})
            {!canFilterAllDepts && " — scoped to your assigned department"}
          </p>
        </div>
      </div>

      <section className="grid grid-cols-2 sm:grid-cols-4 gap-3" aria-label="Queue summary">
        <div className="gov-card p-4">
          <p className="text-xs text-slate-500">Matching Tickets</p>
          <p className="text-2xl font-bold mt-1">{total}</p>
        </div>
        <div className="gov-card p-4">
          <p className="text-xs text-slate-500">Active (This Page)</p>
          <p className="text-2xl font-bold mt-1 text-amber-600">{activeCount}</p>
        </div>
        <div className="gov-card p-4">
          <p className="text-xs text-slate-500">Resolved / Closed</p>
          <p className="text-2xl font-bold mt-1 text-emerald-600">{resolvedCount}</p>
        </div>
        <div className="gov-card p-4">
          <p className="text-xs text-slate-500">High / Critical</p>
          <p className="text-2xl font-bold mt-1 text-red-600">{highPriorityCount}</p>
        </div>
      </section>

      <section className="gov-card p-5">
        <search>
          <form onSubmit={handleApplyFilters} className="grid sm:grid-cols-5 gap-3 items-end">
            <div>
              <label htmlFor="flt-status" className="block text-xs font-semibold mb-1">
                Status
              </label>
              <select
                id="flt-status"
                className="gov-input !min-h-[42px]"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="">All Statuses</option>
                <option value="submitted">Submitted</option>
                <option value="assigned">Assigned</option>
                <option value="in_progress">In Progress</option>
                <option value="resolved">Resolved</option>
                <option value="closed">Closed</option>
              </select>
            </div>

            <div>
              <label htmlFor="flt-dept" className="block text-xs font-semibold mb-1">
                Department
              </label>
              <select
                id="flt-dept"
                className="gov-input !min-h-[42px] disabled:opacity-60"
                value={deptFilter}
                onChange={(e) => setDeptFilter(e.target.value)}
                disabled={!canFilterAllDepts}
              >
                <option value="">
                  {canFilterAllDepts ? "All Departments" : "My Department"}
                </option>
                {departments.map((d) => (
                  <option key={d.id} value={String(d.id)}>
                    {d.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="flt-ward" className="block text-xs font-semibold mb-1">
                Ward
              </label>
              <select
                id="flt-ward"
                className="gov-input !min-h-[42px]"
                value={wardFilter}
                onChange={(e) => setWardFilter(e.target.value)}
              >
                <option value="">All Wards</option>
                {wards.map((w) => (
                  <option key={w.id} value={String(w.id)}>
                    {w.code} — {w.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="flt-priority" className="block text-xs font-semibold mb-1">
                Priority
              </label>
              <select
                id="flt-priority"
                className="gov-input !min-h-[42px]"
                value={priorityFilter}
                onChange={(e) => setPriorityFilter(e.target.value)}
              >
                <option value="">All Priorities</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>

            <div className="flex gap-2">
              <button
                type="submit"
                className="flex-1 inline-flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-lg bg-blue-900 text-white hover:bg-blue-800 dark:bg-blue-500 dark:text-slate-950 font-semibold min-h-[42px]"
              >
                <Filter className="w-4 h-4" aria-hidden="true" />
                Filter
              </button>
              <button
                type="button"
                onClick={resetFilters}
                className="px-3 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 text-sm font-semibold min-h-[42px]"
              >
                Reset
              </button>
            </div>
          </form>
        </search>
      </section>

      {error && (
        <div
          role="alert"
          className="p-3 rounded-lg bg-red-50 dark:bg-red-950/50 border border-red-300 text-sm text-red-800 dark:text-red-200"
        >
          {error}
        </div>
      )}

      <section className="gov-card p-4 sm:p-6">
        {loading ? (
          <div className="py-10 text-center text-sm text-slate-500">Loading complaints queue...</div>
        ) : items.length === 0 ? (
          <div className="py-10 text-center text-sm text-slate-500">
            No grievances match the selected filters.
          </div>
        ) : (
          <div
            tabIndex={0}
            role="region"
            aria-labelledby="officer-queue-caption"
            className="table-wrapper"
          >
            <table className="gov-table text-sm text-left">
              <caption id="officer-queue-caption" className="visually-hidden">
                Priority-sorted grievances assigned to staff queue
              </caption>
              <thead className="bg-slate-100 dark:bg-slate-800 text-xs uppercase text-slate-600 dark:text-slate-300">
                <tr>
                  <th scope="col" className="px-3 py-3">Ticket</th>
                  <th scope="col" className="px-3 py-3">Complaint</th>
                  <th scope="col" className="px-3 py-3">Department</th>
                  <th scope="col" className="px-3 py-3">Ward</th>
                  <th scope="col" className="px-3 py-3">Priority</th>
                  <th scope="col" className="px-3 py-3">Status</th>
                  <th scope="col" className="px-3 py-3">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                {items.map((g) => (
                  <tr key={g.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                    <th scope="row" className="px-3 py-3 font-mono text-xs font-bold whitespace-nowrap">
                      <Link
                        href={`/officer/${encodeURIComponent(g.ticket_id)}`}
                        className="text-blue-800 dark:text-blue-300 hover:underline"
                      >
                        {g.ticket_id}
                      </Link>
                    </th>
                    <td data-label="Complaint" className="px-3 py-3 max-w-xs">
                      <div className="font-semibold line-clamp-1">{g.title}</div>
                      <div className="text-xs text-slate-500">
                        {new Date(g.created_at).toLocaleDateString()}
                        {g.is_emergency && (
                          <span className="ml-2 inline-flex items-center gap-1 text-red-600 font-semibold">
                            <ShieldAlert className="w-3 h-3" aria-hidden="true" />
                            Emergency
                          </span>
                        )}
                      </div>
                    </td>
                    <td data-label="Department" className="px-3 py-3 whitespace-nowrap">
                      {g.department?.name || g.category}
                    </td>
                    <td data-label="Ward" className="px-3 py-3 whitespace-nowrap">
                      {g.ward ? `${g.ward.code} (${g.ward.name})` : "—"}
                    </td>
                    <td data-label="Priority" className="px-3 py-3 whitespace-nowrap">
                      <span className="px-2 py-0.5 rounded-full text-xs font-semibold uppercase bg-amber-100 text-amber-900 dark:bg-amber-950 dark:text-amber-200">
                        {g.priority}
                      </span>
                    </td>
                    <td data-label="Status" className="px-3 py-3 whitespace-nowrap">
                      <span className="px-2 py-0.5 rounded-full text-xs font-semibold uppercase bg-blue-100 text-blue-900 dark:bg-blue-950 dark:text-blue-200">
                        {g.status.replace("_", " ")}
                      </span>
                    </td>
                    <td data-label="Action" className="px-3 py-3 whitespace-nowrap">
                      <Link
                        href={`/officer/${encodeURIComponent(g.ticket_id)}`}
                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md bg-blue-900 text-white dark:bg-blue-500 dark:text-slate-950 text-xs font-semibold hover:opacity-90"
                      >
                        Manage
                        <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-3 pt-4 mt-4 border-t border-slate-200 dark:border-slate-800">
            <button
              type="button"
              disabled={page <= 1}
              onClick={() =>
                loadQueue(page - 1, {
                  status: statusFilter,
                  dept: deptFilter,
                  ward: wardFilter,
                  priority: priorityFilter,
                })
              }
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
              onClick={() =>
                loadQueue(page + 1, {
                  status: statusFilter,
                  dept: deptFilter,
                  ward: wardFilter,
                  priority: priorityFilter,
                })
              }
              className="px-4 py-2 rounded border border-slate-300 dark:border-slate-700 disabled:opacity-50"
            >
              Next
            </button>
          </div>
        )}
      </section>
    </div>
  );
}
