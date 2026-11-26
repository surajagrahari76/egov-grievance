"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { ArrowLeft, CheckCircle2, Paperclip, UserCheck, Building2 } from "lucide-react";
import {
  assignStaffGrievance,
  BACKEND_ORIGIN,
  Department,
  fetchDepartments,
  fetchOfficerTeam,
  fetchStaffGrievanceDetail,
  getStoredUser,
  getToken,
  Grievance,
  isStaffRole,
  OfficerSummary,
  reassignStaffDepartment,
  updateStaffGrievanceStatus,
} from "@/lib/api";
import { StatusTimeline } from "@/components/StatusTimeline";

const NEXT_STATUS_OPTIONS: Record<string, { value: string; label: string }[]> = {
  submitted: [
    { value: "assigned", label: "Assigned" },
    { value: "in_progress", label: "In Progress" },
  ],
  assigned: [
    { value: "in_progress", label: "In Progress" },
    { value: "resolved", label: "Resolved" },
  ],
  in_progress: [
    { value: "resolved", label: "Resolved" },
    { value: "assigned", label: "Assigned" },
  ],
  resolved: [
    { value: "closed", label: "Closed" },
    { value: "in_progress", label: "In Progress (Reopen)" },
  ],
  reopened: [
    { value: "assigned", label: "Assigned" },
    { value: "in_progress", label: "In Progress" },
  ],
  closed: [],
};

export default function OfficerTicketDetailPage() {
  const params = useParams<{ ticketId: string }>();
  const ticketId = decodeURIComponent(params.ticketId || "");
  const router = useRouter();

  const [authorized, setAuthorized] = useState(false);
  const [grievance, setGrievance] = useState<Grievance | null>(null);
  const [team, setTeam] = useState<OfficerSummary[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);

  const [nextStatus, setNextStatus] = useState("");
  const [remarks, setRemarks] = useState("");
  const [selectedOfficerId, setSelectedOfficerId] = useState("");
  const [targetDeptCode, setTargetDeptCode] = useState("");

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [feedbackMsg, setFeedbackMsg] = useState("");

  const loadDetail = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await fetchStaffGrievanceDetail(ticketId);
      setGrievance(data);
      const opts = NEXT_STATUS_OPTIONS[data.status] || [];
      setNextStatus(opts[0]?.value || "");
      setTargetDeptCode(data.department?.code || data.category || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load ticket");
    } finally {
      setLoading(false);
    }
  }, [ticketId]);

  useEffect(() => {
    const token = getToken();
    const stored = getStoredUser();
    if (!token || !stored || !isStaffRole(stored.role)) {
      router.replace(`/login?tab=staff&next=/officer/${encodeURIComponent(ticketId)}`);
      return;
    }
    setAuthorized(true);
    loadDetail();
    fetchOfficerTeam().then(setTeam).catch(() => {});
    fetchDepartments().then(setDepartments).catch(() => {});
  }, [router, ticketId, loadDetail]);

  if (!authorized) {
    return (
      <div className="gov-card p-8 text-center text-sm text-slate-500">
        Verifying staff access...
      </div>
    );
  }

  const handleStatusUpdate = async (e: FormEvent) => {
    e.preventDefault();
    if (!nextStatus) return;
    setSaving(true);
    setError("");
    setFeedbackMsg("");
    try {
      const updated = await updateStaffGrievanceStatus(
        ticketId,
        nextStatus,
        remarks,
        selectedOfficerId ? Number(selectedOfficerId) : undefined
      );
      setGrievance(updated);
      const opts = NEXT_STATUS_OPTIONS[updated.status] || [];
      setNextStatus(opts[0]?.value || "");
      setRemarks("");
      setFeedbackMsg(`Status updated to "${updated.status.replace("_", " ")}".`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update status");
    } finally {
      setSaving(false);
    }
  };

  const handleAssignOfficer = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    setFeedbackMsg("");
    try {
      const updated = await assignStaffGrievance(
        ticketId,
        selectedOfficerId ? Number(selectedOfficerId) : undefined,
        remarks || undefined
      );
      setGrievance(updated);
      const opts = NEXT_STATUS_OPTIONS[updated.status] || [];
      setNextStatus(opts[0]?.value || "");
      setFeedbackMsg("Officer assignment updated.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to assign officer");
    } finally {
      setSaving(false);
    }
  };

  const handleReassignDept = async (e: FormEvent) => {
    e.preventDefault();
    if (!targetDeptCode) return;
    setSaving(true);
    setError("");
    setFeedbackMsg("");
    try {
      const updated = await reassignStaffDepartment(ticketId, targetDeptCode, remarks || undefined);
      setGrievance(updated);
      setFeedbackMsg(`Reassigned to ${updated.department?.name || updated.category}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to reassign department");
    } finally {
      setSaving(false);
    }
  };

  const availableStatuses = grievance ? NEXT_STATUS_OPTIONS[grievance.status] || [] : [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <Link
          href="/officer"
          className="inline-flex items-center gap-1.5 text-sm font-semibold text-blue-800 dark:text-blue-300 hover:underline"
        >
          <ArrowLeft className="w-4 h-4" aria-hidden="true" />
          Back to Officer Queue
        </Link>
      </div>

      {error && (
        <div
          role="alert"
          className="p-3 rounded-lg bg-red-50 dark:bg-red-950/50 border border-red-300 text-sm text-red-800 dark:text-red-200"
        >
          {error}
        </div>
      )}

      {feedbackMsg && (
        <div
          role="status"
          className="p-3 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-300 text-sm text-emerald-900 dark:text-emerald-200 flex items-center gap-2"
        >
          <CheckCircle2 className="w-4 h-4 shrink-0" aria-hidden="true" />
          {feedbackMsg}
        </div>
      )}

      {loading ? (
        <div className="gov-card p-8 text-center text-sm text-slate-500">
          Loading grievance details...
        </div>
      ) : grievance ? (
        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <article className="gov-card p-6 space-y-4">
              <div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-200 dark:border-slate-800 pb-4">
                <div>
                  <p className="text-xs font-mono text-slate-500">{grievance.ticket_id}</p>
                  <h1 id="main-content" tabIndex={-1} className="text-2xl font-bold mt-0.5">
                    {grievance.title}
                  </h1>
                </div>
                <div className="flex gap-2">
                  <span className="px-2.5 py-1 rounded-full text-xs font-semibold uppercase bg-blue-100 text-blue-900 dark:bg-blue-950 dark:text-blue-200">
                    {grievance.status.replace("_", " ")}
                  </span>
                  <span className="px-2.5 py-1 rounded-full text-xs font-semibold uppercase bg-amber-100 text-amber-900 dark:bg-amber-950 dark:text-amber-200">
                    {grievance.priority}
                  </span>
                </div>
              </div>

              <p className="text-sm whitespace-pre-wrap text-slate-700 dark:text-slate-200">
                {grievance.text}
              </p>

              <dl className="grid sm:grid-cols-2 gap-4 text-sm pt-2 border-t border-slate-200 dark:border-slate-800">
                <div>
                  <dt className="text-xs text-slate-500">Department</dt>
                  <dd className="font-semibold">
                    {grievance.department?.name || grievance.category}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-slate-500">Ward / Address</dt>
                  <dd className="font-semibold">
                    {grievance.ward ? `${grievance.ward.code} — ${grievance.ward.name}` : "Not set"}
                    {grievance.address ? ` • ${grievance.address}` : ""}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-slate-500">Language / Filing</dt>
                  <dd className="font-semibold">
                    {grievance.language.toUpperCase()} •{" "}
                    {grievance.is_anonymous ? "Anonymous" : `Citizen #${grievance.user_id}`}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-slate-500">SLA Deadline</dt>
                  <dd className="font-semibold">
                    {grievance.sla_deadline
                      ? new Date(grievance.sla_deadline).toLocaleString()
                      : "N/A"}
                  </dd>
                </div>
              </dl>

              {grievance.attachments.length > 0 && (
                <div className="pt-3 border-t border-slate-200 dark:border-slate-800">
                  <h2 className="text-xs font-semibold uppercase text-slate-500 mb-2">
                    Attachments
                  </h2>
                  <ul className="space-y-1 text-sm">
                    {grievance.attachments.map((att) => (
                      <li key={att.id}>
                        <a
                          href={`${BACKEND_ORIGIN}/uploads/${att.file_path}`}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1.5 text-blue-800 dark:text-blue-300 hover:underline"
                        >
                          <Paperclip className="w-3.5 h-3.5" aria-hidden="true" />
                          {att.original_name} ({Math.ceil(att.size_bytes / 1024)} KB)
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </article>

            <section className="gov-card p-6">
              <h2 className="text-lg font-bold mb-4">Audit & Status Timeline</h2>
              <StatusTimeline
                currentStatus={grievance.status}
                history={grievance.status_history}
              />
            </section>
          </div>

          <aside className="space-y-4">
            <section className="gov-card p-5 space-y-4">
              <h2 className="text-lg font-bold">Update Status</h2>
              {availableStatuses.length === 0 ? (
                <p className="text-sm text-slate-500">
                  This ticket is closed and has no further workflow transitions.
                </p>
              ) : (
                <form onSubmit={handleStatusUpdate} className="space-y-3">
                  <div>
                    <label htmlFor="next-status" className="block text-xs font-semibold mb-1">
                      Next Status <span aria-hidden="true">*</span>
                    </label>
                    <select
                      id="next-status"
                      className="gov-input !min-h-[42px]"
                      value={nextStatus}
                      onChange={(e) => setNextStatus(e.target.value)}
                      required
                    >
                      {availableStatuses.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label htmlFor="status-remarks" className="block text-xs font-semibold mb-1">
                      Action Remarks
                    </label>
                    <textarea
                      id="status-remarks"
                      rows={3}
                      className="gov-input"
                      value={remarks}
                      onChange={(e) => setRemarks(e.target.value)}
                      placeholder="Inspection notes or resolution details..."
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={saving}
                    className="w-full py-2.5 rounded-lg bg-blue-900 text-white hover:bg-blue-800 dark:bg-blue-500 dark:text-slate-950 font-semibold min-h-[44px] disabled:opacity-60"
                  >
                    {saving ? "Updating..." : "Save Status Update"}
                  </button>
                </form>
              )}
            </section>

            <section className="gov-card p-5 space-y-3">
              <h2 className="text-sm font-bold flex items-center gap-2">
                <UserCheck className="w-4 h-4 text-blue-700 dark:text-blue-300" aria-hidden="true" />
                Assign Officer
              </h2>
              <form onSubmit={handleAssignOfficer} className="space-y-3">
                <div>
                  <label htmlFor="assign-officer" className="visually-hidden">
                    Select Officer
                  </label>
                  <select
                    id="assign-officer"
                    className="gov-input !min-h-[42px]"
                    value={selectedOfficerId}
                    onChange={(e) => setSelectedOfficerId(e.target.value)}
                  >
                    <option value="">Assign to myself</option>
                    {team.map((o) => (
                      <option key={o.id} value={String(o.id)}>
                        {o.name} — {o.designation}
                      </option>
                    ))}
                  </select>
                </div>
                <button
                  type="submit"
                  disabled={saving}
                  className="w-full py-2 rounded-lg border border-slate-300 dark:border-slate-700 font-semibold text-sm hover:bg-slate-100 dark:hover:bg-slate-800"
                >
                  Assign Officer
                </button>
              </form>
            </section>

            <section className="gov-card p-5 space-y-3">
              <h2 className="text-sm font-bold flex items-center gap-2">
                <Building2 className="w-4 h-4 text-amber-600" aria-hidden="true" />
                Reassign Department
              </h2>
              <form onSubmit={handleReassignDept} className="space-y-3">
                <div>
                  <label htmlFor="reassign-dept" className="visually-hidden">
                    Target Department
                  </label>
                  <select
                    id="reassign-dept"
                    className="gov-input !min-h-[42px]"
                    value={targetDeptCode}
                    onChange={(e) => setTargetDeptCode(e.target.value)}
                    required
                  >
                    {departments.map((d) => (
                      <option key={d.id} value={d.code}>
                        {d.name}
                      </option>
                    ))}
                  </select>
                </div>
                <button
                  type="submit"
                  disabled={saving}
                  className="w-full py-2 rounded-lg border border-slate-300 dark:border-slate-700 font-semibold text-sm hover:bg-slate-100 dark:hover:bg-slate-800"
                >
                  Reassign Department
                </button>
              </form>
            </section>
          </aside>
        </div>
      ) : null}
    </div>
  );
}
