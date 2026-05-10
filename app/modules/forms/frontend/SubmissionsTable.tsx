import { ExternalLink } from "lucide-react";
import { useEffect, useState } from "react";

import { listSubmissions, type Submission } from "../../../../frontend/src/api/forms";

type Props = {
  guildId: string;
  formId: string;
};

const STATUSES = ["", "pending", "approved", "denied"];

export function SubmissionsTable({ guildId, formId }: Props) {
  const [status, setStatus] = useState("");
  const [submissions, setSubmissions] = useState<Submission[]>([]);

  useEffect(() => {
    void listSubmissions(guildId, formId, status || undefined).then(setSubmissions);
  }, [guildId, formId, status]);

  return (
    <div className="rounded-lg border border-border bg-card">
      <div className="flex items-center justify-between border-b border-border p-3">
        <h3 className="font-semibold">Submissions</h3>
        <select
          className="h-9 rounded-md border border-border bg-card px-3 text-sm"
          value={status}
          onChange={(event) => setStatus(event.target.value)}
        >
          {STATUSES.map((item) => (
            <option key={item || "all"} value={item}>
              {item || "all"}
            </option>
          ))}
        </select>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-muted text-muted-foreground">
            <tr>
              <th className="p-3">User</th>
              <th className="p-3">Status</th>
              <th className="p-3">Decision by</th>
              <th className="p-3">Created</th>
              <th className="p-3">Thread</th>
            </tr>
          </thead>
          <tbody>
            {submissions.map((submission) => (
              <tr key={submission.id} className="border-t border-border">
                <td className="p-3">{submission.username}</td>
                <td className="p-3">{submission.status}</td>
                <td className="p-3">{decisionBy(submission)}</td>
                <td className="p-3">{new Date(submission.createdAt).toLocaleString()}</td>
                <td className="p-3">
                  {submission.threadId && (
                    <a
                      className="inline-flex items-center gap-1 text-primary"
                      href={`https://discord.com/channels/${guildId}/${submission.threadId}`}
                    >
                      <ExternalLink aria-hidden="true" size={14} />
                      Open
                    </a>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function decisionBy(submission: Submission) {
  if (submission.status === "pending") {
    return "-";
  }
  const action = [...submission.actions]
    .reverse()
    .find((item) => item.action === "approved" || item.action === "denied");
  if (!action) {
    return "Unknown";
  }
  if (action.action === "approved" && action.note) {
    return action.note;
  }
  return `Discord ID ${action.actorId}`;
}
