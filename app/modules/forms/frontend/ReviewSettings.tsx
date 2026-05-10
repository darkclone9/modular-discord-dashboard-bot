import { type ReactNode, useEffect, useMemo, useState } from "react";

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
            Viewer roles are invited for discussion only.
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
        <RoleIdsInput
          label="Reviewer role IDs"
          value={settings.reviewerRoleIds}
          emptyText="Add at least one reviewer role ID."
          help={
            <>
              Paste role IDs or role mentions here. These roles can approve, deny, request more
              info, and will be pinged on new submissions.
            </>
          }
          onChange={(reviewerRoleIds) => onChange({ ...settings, reviewerRoleIds })}
        />
      </label>
      <label className="grid gap-1 text-sm font-medium text-foreground">
        <RoleIdsInput
          label="Viewer role IDs"
          value={settings.viewerRoleIds}
          emptyText="Optional. Add roles that can watch and talk in review threads."
          help={
            <>
              Viewer roles are included in the private thread announcement and can discuss the
              application, but they cannot approve, deny, or request more info. Give these roles
              access to the review channel and thread messaging in Discord.
            </>
          }
          onChange={(viewerRoleIds) => onChange({ ...settings, viewerRoleIds })}
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


type RoleIdsInputProps = {
  label: string;
  value: string[];
  emptyText: string;
  help: ReactNode;
  onChange: (roleIds: string[]) => void;
};

function RoleIdsInput({ label, value, emptyText, help, onChange }: RoleIdsInputProps) {
  const roleSignature = useMemo(() => value.join(","), [value]);
  const [inputValue, setInputValue] = useState(value.join(", "));

  useEffect(() => {
    setInputValue(value.join(", "));
  }, [roleSignature]);

  function updateRoles(nextValue: string) {
    setInputValue(nextValue);
    onChange(parseRoleIds(nextValue));
  }

  return (
    <>
      <span className="flex items-center gap-2">
        {label}
        <InfoBubble label={`${label} help`}>{help}</InfoBubble>
      </span>
      <textarea
        className="min-h-20 rounded-md border border-border px-3 py-2 text-sm font-normal"
        value={inputValue}
        onChange={(event) => updateRoles(event.target.value)}
        placeholder="123456789012345678, 234567890123456789"
      />
      <div className="flex flex-wrap gap-2 pt-1">
        {value.length > 0 ? (
          value.map((roleId) => (
            <span
              key={roleId}
              className="rounded-md border border-border bg-muted px-2 py-1 text-xs font-normal text-muted-foreground"
            >
              {roleId}
            </span>
          ))
        ) : (
          <span className="text-xs font-normal text-muted-foreground">{emptyText}</span>
        )}
      </div>
    </>
  );
}

function parseRoleIds(value: string): string[] {
  return Array.from(new Set(value.match(/\d{15,25}/g) ?? []));
}
