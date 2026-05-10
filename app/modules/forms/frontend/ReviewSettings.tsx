import type { ReviewSettings as ReviewSettingsType } from "../../../../frontend/src/api/forms";

type Props = {
  settings: ReviewSettingsType;
  onChange: (settings: ReviewSettingsType) => void;
};

export function ReviewSettings({ settings, onChange }: Props) {
  return (
    <div className="grid gap-3 rounded-md border border-border bg-white p-3">
      <div className="grid gap-3 sm:grid-cols-2">
        <input
          className="h-9 rounded-md border border-border px-3 text-sm"
          value={settings.reviewChannelId}
          onChange={(event) => onChange({ ...settings, reviewChannelId: event.target.value })}
          placeholder="Review thread parent channel ID"
        />
        <input
          className="h-9 rounded-md border border-border px-3 text-sm"
          value={settings.autoRoleId ?? ""}
          onChange={(event) => onChange({ ...settings, autoRoleId: event.target.value || null })}
          placeholder="Approval auto-role ID"
        />
      </div>
      <input
        className="h-9 rounded-md border border-border px-3 text-sm"
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
        placeholder="Reviewer role IDs separated by commas"
      />
      <textarea
        className="min-h-16 rounded-md border border-border px-3 py-2 text-sm"
        value={settings.approvalMessage}
        onChange={(event) => onChange({ ...settings, approvalMessage: event.target.value })}
        placeholder="Approval DM"
      />
      <textarea
        className="min-h-16 rounded-md border border-border px-3 py-2 text-sm"
        value={settings.denialMessage}
        onChange={(event) => onChange({ ...settings, denialMessage: event.target.value })}
        placeholder="Denial DM"
      />
    </div>
  );
}
