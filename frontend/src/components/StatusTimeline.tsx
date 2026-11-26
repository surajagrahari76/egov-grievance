import { CheckCircle2, Clock } from "lucide-react";
import type { StatusHistoryItem } from "@/lib/api";

const WORKFLOW_STEPS = [
  { key: "submitted", label: "Submitted" },
  { key: "assigned", label: "Assigned" },
  { key: "in_progress", label: "In Progress" },
  { key: "resolved", label: "Resolved" },
  { key: "closed", label: "Closed" },
];

export function StatusTimeline({
  currentStatus,
  history,
}: {
  currentStatus: string;
  history: StatusHistoryItem[];
}) {
  const currentIdx = WORKFLOW_STEPS.findIndex((s) => s.key === currentStatus);

  return (
    <div className="space-y-4">
      <ol className="grid grid-cols-2 sm:grid-cols-5 gap-2" aria-label="Complaint progress stages">
        {WORKFLOW_STEPS.map((step, idx) => {
          const completed = currentIdx >= idx;
          const isCurrent = step.key === currentStatus;
          return (
            <li
              key={step.key}
              aria-current={isCurrent ? "step" : undefined}
              className={`p-2.5 rounded-lg border text-xs font-semibold flex items-center gap-2 ${
                completed
                  ? "border-emerald-500 bg-emerald-50 text-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-200"
                  : "border-slate-200 dark:border-slate-700 text-slate-500"
              }`}
            >
              {completed ? (
                <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" aria-hidden="true" />
              ) : (
                <Clock className="w-4 h-4 shrink-0 opacity-60" aria-hidden="true" />
              )}
              <span>{step.label}</span>
            </li>
          );
        })}
      </ol>

      {history.length > 0 && (
        <div className="space-y-2 border-l-2 border-blue-200 dark:border-blue-800 pl-4">
          {history.map((item) => (
            <div key={item.id} className="text-sm">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-semibold uppercase text-xs px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800">
                  {item.to_status.replace("_", " ")}
                </span>
                <time className="text-xs text-slate-500 dark:text-slate-400">
                  {new Date(item.created_at).toLocaleString()}
                </time>
              </div>
              {item.remarks && (
                <p className="text-slate-600 dark:text-slate-300 mt-0.5">{item.remarks}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
