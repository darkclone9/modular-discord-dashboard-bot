import type { ReviewSettings as ReviewSettingsType } from "../../../../frontend/src/api/forms";
import { InfoBubble } from "./InfoBubble";

type Props = {
  settings: ReviewSettingsType;
  onChange: (settings: ReviewSettingsType) => void;
};

export function ReviewSettings({ settings, onChange }: Props) {
  return (
    <div className="grid gap-3 rounded-md border border-border bg-card p-3">
      <div>
        <div className="flex items-center gap-2 text-sm font-semibold">
          Review workflow
          <InfoBubble label="Review workflow help">
            Submissions create a private thread in the review channel. Reviewer roles are pinged
            once and are the only roles allowed to approve, deny, or request more information.
          </InfoBubble>
        </div>
        <p className="mt-1 text-sm text-muted-foreground">
          Use Discord developer mode to copy channel and role IDs.
        </p>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="grid gap-1 text-sm font-medium text-foreground">
          <span className="flex items-center gap-2">
            Review channel ID
            <InfoBubble label="Review channel help">
              This is the channel where the bot creates each private review thread.
            </InfoBubble>
          </span>
          <input
            className="h-9 rounded-md border border-border px-3 text-sm font-normal"
            value={settings.reviewChannelId}
            onChange={(event) => onChange({ ...settings, reviewChannelId: event.target.value })}
            placeholder="123456789012345678"
          />
        </label>
        <label className="grid gap-1 text-sm font-medium text-foreground">
          <span className="flex items-center gap-2">
            Approval auto-role ID
            <InfoBubble label="Auto-role help">
              Optional. When a reviewer approves the submission, the bot gives this role to the
              applicant.
            </InfoBubble>
          </span>
          <input
            className="h-9 rounded-md border border-border px-3 text-sm font-normal"
            value={settings.autoRoleId ?? ""}
            onChange={(event) => onChange({ ...settings, autoRoleId: event.target.value || null })}
            placeholder="Optional role ID"
          />
        </label>
      </div>
      <label className="grid gap-1 text-sm font-medium text-foreground">
        <span className="flex items-center gap-2">
          Reviewer role IDs
          <InfoBubble label="Reviewer roles help">
            Put role IDs here, separated by commas. These roles are pinged when a submission arrives.
          </InfoBubble>
        </span>
        <input
          className="h-9 rounded-md border border-border px-3 text-sm font-normal"
          value={settings.reviewerRoleIds.join(", ")}
          onChange={(event) =>
            onChange({
              ...settings,
              reviewerRoleIds: event.target.value
                .split(",")
                .map((item) => item.trim())
                .filter(Boolean),
            })
          }
          placeholder="123456789012345678, 234567890123456789"
        />
      </label>
      <label className="grid gap-1 text-sm font-medium text-foreground">
        Approval DM message
        <textarea
          className="min-h-16 rounded-md border border-border px-3 py-2 text-sm font-normal"
          value={settings.approvalMessage}
          onChange={(event) => onChange({ ...settings, approvalMessage: event.target.value })}
          placeholder="Your application has been approved."
        />
      </label>
      <label className="grid gap-1 text-sm font-medium text-foreground">
        Denial DM message
        <textarea
          className="min-h-16 rounded-md border border-border px-3 py-2 text-sm font-normal"
          value={settings.denialMessage}
          onChange={(event) => onChange({ ...settings, denialMessage: event.target.value })}
          placeholder="Your application was denied."
        />
      </label>
    </div>
  );
}
