import { Plus, Save, Trash2 } from "lucide-react";
import type { Dispatch, SetStateAction } from "react";
import { useEffect, useState } from "react";

import {
  createReactionRoleMenu,
  deleteReactionRoleMenu,
  listReactionRoleMenus,
  type MenuBehavior,
  type MessageMode,
  type PickerStyle,
  publishReactionRoleMenu,
  type ReactionRoleMenu,
  type ReactionRoleMenuPayload,
  type ReactionRoleOption,
  updateReactionRoleMenu,
} from "../../../../frontend/src/api/reactionRoles";
import { Button } from "../../../../frontend/src/components/ui/button";
import { Card } from "../../../../frontend/src/components/ui/card";
import { InfoBubble } from "../../forms/frontend/InfoBubble";

type Props = {
  guildId: string;
};

const pickerStyles: PickerStyle[] = ["reactions", "buttons", "select"];
const behaviors: MenuBehavior[] = ["toggle", "add_only", "single"];
const messageModes: MessageMode[] = ["bot_post", "existing_message"];

export function ReactionRolesPage({ guildId }: Props) {
  const [menus, setMenus] = useState<ReactionRoleMenu[]>([]);
  const [draft, setDraft] = useState<ReactionRoleMenuPayload>(newMenuDraft());
  const [editingId, setEditingId] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);

  async function reload() {
    setMenus(await listReactionRoleMenus(guildId));
  }

  useEffect(() => {
    setDraft(newMenuDraft());
    setEditingId(null);
    setStatus(null);
    void reload();
  }, [guildId]);

  async function saveMenu() {
    setStatus("Saving role menu...");
    if (editingId) {
      await updateReactionRoleMenu(guildId, editingId, draft);
    } else {
      await createReactionRoleMenu(guildId, draft);
    }
    setDraft(newMenuDraft());
    setEditingId(null);
    await reload();
    setStatus("Role menu saved. The bot will publish or refresh enabled menus.");
  }

  async function publish(menuId: string) {
    setStatus("Queueing publish...");
    await publishReactionRoleMenu(guildId, menuId);
    await reload();
    setStatus("Publish queued. The bot will post or refresh it shortly.");
  }

  async function remove(menuId: string) {
    setStatus("Deleting role menu...");
    await deleteReactionRoleMenu(guildId, menuId);
    await reload();
    setStatus("Role menu deleted.");
  }

  return (
    <div className="grid gap-5 lg:grid-cols-[1fr_420px]">
      <section className="grid gap-3">
        <div className="flex items-center gap-2">
          <h2 className="text-lg font-semibold">Reaction roles</h2>
          <InfoBubble label="Reaction roles help">
            Create classic emoji reaction roles or modern button/dropdown role menus. The bot role
            must be above every role it grants.
          </InfoBubble>
        </div>
        {menus.length === 0 && (
          <Card className="p-3 text-sm text-muted-foreground">
            No reaction role menus yet. Create one with the editor.
          </Card>
        )}
        {menus.map((menu) => (
          <Card key={menu.id} className="p-3">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="font-semibold">{menu.name}</h3>
                  <span className="rounded-md bg-muted px-2 py-1 text-xs text-muted-foreground">
                    {menu.pickerStyle}
                  </span>
                  <span className="rounded-md bg-muted px-2 py-1 text-xs text-muted-foreground">
                    {menu.behavior}
                  </span>
                  <span className="rounded-md bg-muted px-2 py-1 text-xs text-muted-foreground">
                    {menu.isEnabled ? "Enabled" : "Disabled"}
                  </span>
                </div>
                <div className="mt-1 text-sm text-muted-foreground">
                  Channel ID: {menu.channelId}
                </div>
                <div className="mt-1 text-sm text-muted-foreground">
                  Message ID: {menu.messageId ?? "not posted yet"}
                </div>
                <div className="mt-2 flex flex-wrap gap-2">
                  {menu.options.map((option) => (
                    <span
                      key={option.id ?? option.roleId}
                      className="rounded-md border border-border bg-muted px-2 py-1 text-xs"
                    >
                      {option.emoji ? `${option.emoji} ` : ""}
                      {option.label} - {option.roleId}
                    </span>
                  ))}
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button
                  variant="secondary"
                  onClick={() => {
                    setEditingId(menu.id);
                    setDraft(menuToPayload(menu));
                  }}
                >
                  Edit
                </Button>
                <Button variant="secondary" onClick={() => publish(menu.id)}>
                  Publish
                </Button>
                <Button variant="ghost" onClick={() => remove(menu.id)} title="Delete menu">
                  <Trash2 aria-hidden="true" size={16} />
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </section>

      <Card className="p-4">
        <div className="mb-3 flex items-center gap-2">
          <Plus aria-hidden="true" size={18} />
          <h3 className="font-semibold">{editingId ? "Edit role menu" : "Create role menu"}</h3>
        </div>
        <div className="grid gap-3">
          <label className="grid gap-1 text-sm font-medium">
            Internal name
            <input
              className="h-9 rounded-md border border-border px-3 text-sm font-normal"
              value={draft.name}
              onChange={(event) => setDraft({ ...draft, name: event.target.value })}
              placeholder="Pronoun roles"
            />
          </label>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="grid gap-1 text-sm font-medium">
              Message mode
              <select
                className="h-9 rounded-md border border-border px-3 text-sm font-normal"
                value={draft.messageMode}
                onChange={(event) =>
                  setDraft({ ...draft, messageMode: event.target.value as MessageMode })
                }
              >
                {messageModes.map((mode) => (
                  <option key={mode} value={mode}>
                    {mode}
                  </option>
                ))}
              </select>
            </label>
            <label className="grid gap-1 text-sm font-medium">
              Picker style
              <select
                className="h-9 rounded-md border border-border px-3 text-sm font-normal"
                value={draft.pickerStyle}
                onChange={(event) =>
                  setDraft({ ...draft, pickerStyle: event.target.value as PickerStyle })
                }
              >
                {pickerStyles.map((style) => (
                  <option key={style} value={style}>
                    {style}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <label className="grid gap-1 text-sm font-medium">
            Behavior
            <select
              className="h-9 rounded-md border border-border px-3 text-sm font-normal"
              value={draft.behavior}
              onChange={(event) =>
                setDraft({ ...draft, behavior: event.target.value as MenuBehavior })
              }
            >
              {behaviors.map((behavior) => (
                <option key={behavior} value={behavior}>
                  {behavior}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-sm font-medium">
            Channel ID
            <input
              className="h-9 rounded-md border border-border px-3 text-sm font-normal"
              value={draft.channelId}
              onChange={(event) => setDraft({ ...draft, channelId: event.target.value })}
              placeholder="123456789012345678"
            />
          </label>
          <label className="grid gap-1 text-sm font-medium">
            Existing message ID
            <input
              className="h-9 rounded-md border border-border px-3 text-sm font-normal"
              value={draft.messageId ?? ""}
              onChange={(event) => setDraft({ ...draft, messageId: event.target.value || null })}
              placeholder="Only required for existing_message mode"
            />
          </label>
          <label className="grid gap-1 text-sm font-medium">
            Public title
            <input
              className="h-9 rounded-md border border-border px-3 text-sm font-normal"
              value={draft.title}
              onChange={(event) => setDraft({ ...draft, title: event.target.value })}
              placeholder="Choose your roles"
            />
          </label>
          <label className="grid gap-1 text-sm font-medium">
            Public description
            <textarea
              className="min-h-20 rounded-md border border-border px-3 py-2 text-sm font-normal"
              value={draft.description}
              onChange={(event) => setDraft({ ...draft, description: event.target.value })}
              placeholder="React or use the menu below to pick your roles."
            />
          </label>
          <div className="grid gap-2">
            <div className="text-sm font-semibold">Options</div>
            {draft.options.map((option, index) => (
              <OptionEditor
                key={index}
                option={option}
                onChange={(next) => updateOption(index, next, setDraft)}
                onRemove={() =>
                  setDraft((current) => ({
                    ...current,
                    options: current.options.filter((_, optionIndex) => optionIndex !== index),
                  }))
                }
              />
            ))}
            <Button
              variant="secondary"
              onClick={() =>
                setDraft((current) => ({
                  ...current,
                  options: [
                    ...current.options,
                    { label: "", roleId: "", emoji: null, description: "" },
                  ],
                }))
              }
            >
              Add option
            </Button>
          </div>
          <label className="flex items-center gap-2 text-sm font-medium">
            <input
              type="checkbox"
              checked={draft.isEnabled}
              onChange={(event) => setDraft({ ...draft, isEnabled: event.target.checked })}
            />
            Enabled
          </label>
          <div className="flex flex-wrap items-center gap-2">
            <Button onClick={saveMenu}>
              <Save aria-hidden="true" size={16} />
              Save menu
            </Button>
            {editingId && (
              <Button
                variant="ghost"
                onClick={() => {
                  setEditingId(null);
                  setDraft(newMenuDraft());
                }}
              >
                Cancel
              </Button>
            )}
          </div>
          {status && <div className="text-sm text-muted-foreground">{status}</div>}
        </div>
      </Card>
    </div>
  );
}

function OptionEditor({
  option,
  onChange,
  onRemove,
}: {
  option: ReactionRoleOption;
  onChange: (option: ReactionRoleOption) => void;
  onRemove: () => void;
}) {
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
      <div className="grid gap-2 sm:grid-cols-[1fr_1fr_80px_40px]">
        <input
          className="h-9 rounded-md border border-border px-3 text-sm"
          value={option.label}
          onChange={(event) => onChange({ ...option, label: event.target.value })}
          placeholder="Role label"
        />
        <input
          className="h-9 rounded-md border border-border px-3 text-sm"
          value={option.roleId}
          onChange={(event) => onChange({ ...option, roleId: event.target.value })}
          placeholder="Role ID"
        />
        <input
          className="h-9 rounded-md border border-border px-3 text-sm"
          value={option.emoji ?? ""}
          onChange={(event) => onChange({ ...option, emoji: event.target.value || null })}
          placeholder="Emoji"
        />
        <Button variant="ghost" onClick={onRemove} title="Remove option">
          <Trash2 aria-hidden="true" size={16} />
        </Button>
      </div>
      <input
        className="h-9 rounded-md border border-border px-3 text-sm"
        value={option.description}
        onChange={(event) => onChange({ ...option, description: event.target.value })}
        placeholder="Optional dropdown description"
      />
    </div>
  );
}

function updateOption(
  index: number,
  option: ReactionRoleOption,
  setDraft: Dispatch<SetStateAction<ReactionRoleMenuPayload>>,
) {
  setDraft((current) => ({
    ...current,
    options: current.options.map((item, optionIndex) => (optionIndex === index ? option : item)),
  }));
}

function menuToPayload(menu: ReactionRoleMenu): ReactionRoleMenuPayload {
  return {
    name: menu.name,
    channelId: menu.channelId,
    messageId: menu.messageId,
    messageMode: menu.messageMode,
    pickerStyle: menu.pickerStyle,
    behavior: menu.behavior,
    title: menu.title,
    description: menu.description,
    isEnabled: menu.isEnabled,
    options: menu.options.map((option) => ({
      label: option.label,
      roleId: option.roleId,
      emoji: option.emoji,
      description: option.description,
    })),
  };
}

function newMenuDraft(): ReactionRoleMenuPayload {
  return {
    name: "",
    channelId: "",
    messageId: null,
    messageMode: "bot_post",
    pickerStyle: "reactions",
    behavior: "toggle",
    title: "Choose your roles",
    description: "React or use the menu below to pick your roles.",
    isEnabled: true,
    options: [{ label: "", roleId: "", emoji: null, description: "" }],
  };
}
