import { apiFetch } from "./client";

export type MessageMode = "bot_post" | "existing_message";
export type PickerStyle = "reactions" | "buttons" | "select";
export type MenuBehavior = "toggle" | "add_only" | "single";

export type ReactionRoleOption = {
  id?: string;
  position?: number;
  label: string;
  roleId: string;
  emoji: string | null;
  description: string;
};

export type ReactionRoleMenu = {
  id: string;
  guildId: string;
  name: string;
  channelId: string;
  messageId: string | null;
  messageMode: MessageMode;
  pickerStyle: PickerStyle;
  behavior: MenuBehavior;
  title: string;
  description: string;
  isEnabled: boolean;
  options: ReactionRoleOption[];
  createdAt: string;
  updatedAt: string;
};

export type ReactionRoleMenuPayload = Omit<
  ReactionRoleMenu,
  "id" | "guildId" | "createdAt" | "updatedAt"
>;

export function listReactionRoleMenus(guildId: string) {
  return apiFetch<ReactionRoleMenu[]>(`/guilds/${guildId}/reaction-roles`);
}

export function createReactionRoleMenu(guildId: string, payload: ReactionRoleMenuPayload) {
  return apiFetch<ReactionRoleMenu>(`/guilds/${guildId}/reaction-roles`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateReactionRoleMenu(
  guildId: string,
  menuId: string,
  payload: Partial<ReactionRoleMenuPayload>,
) {
  return apiFetch<ReactionRoleMenu>(`/guilds/${guildId}/reaction-roles/${menuId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function publishReactionRoleMenu(guildId: string, menuId: string) {
  return apiFetch<ReactionRoleMenu>(`/guilds/${guildId}/reaction-roles/${menuId}/publish`, {
    method: "POST",
  });
}

export function deleteReactionRoleMenu(guildId: string, menuId: string) {
  return apiFetch<void>(`/guilds/${guildId}/reaction-roles/${menuId}`, { method: "DELETE" });
}
