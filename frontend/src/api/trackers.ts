import { apiFetch } from "./client";

export type TrackerProvider = "youtube" | "tiktok" | "instagram" | "facebook";

export type SocialTracker = {
  id: string;
  guildId: string;
  provider: TrackerProvider;
  label: string;
  sourceId: string;
  sourceUrl: string | null;
  notificationChannelId: string;
  customMessage: string;
  isEnabled: boolean;
  lastSeenExternalId: string | null;
  lastSeenUrl: string | null;
  lastCheckedAt: string | null;
  createdAt: string;
  updatedAt: string;
};

export type SocialTrackerPayload = {
  provider: TrackerProvider;
  label: string;
  sourceId: string;
  sourceUrl: string | null;
  notificationChannelId: string;
  customMessage: string;
  isEnabled: boolean;
};

export type GameSuggestionSettings = {
  guildId: string;
  enabled: boolean;
  announcementChannelId: string | null;
  rewardRoleId: string | null;
  mentionEveryone: boolean;
  announcementWeekday: number;
  announcementHourUtc: number;
  customMessage: string;
  lastAnnouncedWeek: string | null;
  createdAt: string | null;
  updatedAt: string | null;
};

export type GameSuggestionPick = {
  id: string;
  guildId: string;
  userId: string;
  username: string;
  gameName: string;
  channelId: string | null;
  messageId: string | null;
  announcedWeek: string;
  announcedAt: string;
};

export function listSocialTrackers(guildId: string) {
  return apiFetch<SocialTracker[]>(`/guilds/${guildId}/trackers`);
}

export function createSocialTracker(guildId: string, payload: SocialTrackerPayload) {
  return apiFetch<SocialTracker>(`/guilds/${guildId}/trackers`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateSocialTracker(
  guildId: string,
  trackerId: string,
  payload: Partial<SocialTrackerPayload>,
) {
  return apiFetch<SocialTracker>(`/guilds/${guildId}/trackers/${trackerId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteSocialTracker(guildId: string, trackerId: string) {
  return apiFetch<void>(`/guilds/${guildId}/trackers/${trackerId}`, { method: "DELETE" });
}

export function getGameSuggestionSettings(guildId: string) {
  return apiFetch<GameSuggestionSettings>(`/guilds/${guildId}/trackers/games/settings`);
}

export function updateGameSuggestionSettings(
  guildId: string,
  payload: Omit<GameSuggestionSettings, "guildId" | "lastAnnouncedWeek" | "createdAt" | "updatedAt">,
) {
  return apiFetch<GameSuggestionSettings>(`/guilds/${guildId}/trackers/games/settings`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function listGameSuggestionPicks(guildId: string) {
  return apiFetch<GameSuggestionPick[]>(`/guilds/${guildId}/trackers/games/picks`);
}
