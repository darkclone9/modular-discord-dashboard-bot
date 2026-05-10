import { Bell, Gamepad2, Plus, Save, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";

import {
  createSocialTracker,
  deleteSocialTracker,
  getGameSuggestionSettings,
  type GameSuggestionPick,
  type GameSuggestionSettings,
  listGameSuggestionPicks,
  listSocialTrackers,
  type SocialTracker,
  type SocialTrackerPayload,
  type TrackerProvider,
  updateGameSuggestionSettings,
  updateSocialTracker,
} from "../../../../frontend/src/api/trackers";
import { Button } from "../../../../frontend/src/components/ui/button";
import { Card } from "../../../../frontend/src/components/ui/card";
import { InfoBubble } from "../../forms/frontend/InfoBubble";

type Props = {
  guildId: string;
};

const providers: TrackerProvider[] = ["youtube", "tiktok", "instagram", "facebook"];
const weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

export function TrackersPage({ guildId }: Props) {
  const [trackers, setTrackers] = useState<SocialTracker[]>([]);
  const [editing, setEditing] = useState<SocialTrackerPayload>(newTrackerDraft());
  const [editingId, setEditingId] = useState<string | null>(null);
  const [gameSettings, setGameSettings] = useState<GameSuggestionSettings | null>(null);
  const [gamePicks, setGamePicks] = useState<GameSuggestionPick[]>([]);
  const [status, setStatus] = useState<string | null>(null);

  async function reload() {
    const [loadedTrackers, loadedGameSettings, loadedPicks] = await Promise.all([
      listSocialTrackers(guildId),
      getGameSuggestionSettings(guildId),
      listGameSuggestionPicks(guildId),
    ]);
    setTrackers(loadedTrackers);
    setGameSettings(loadedGameSettings);
    setGamePicks(loadedPicks);
  }

  useEffect(() => {
    setStatus(null);
    setEditing(newTrackerDraft());
    setEditingId(null);
    void reload();
  }, [guildId]);

  async function saveTracker() {
    setStatus("Saving tracker...");
    if (editingId) {
      await updateSocialTracker(guildId, editingId, editing);
    } else {
      await createSocialTracker(guildId, editing);
    }
    setEditing(newTrackerDraft());
    setEditingId(null);
    await reload();
    setStatus("Tracker saved.");
  }

  async function removeTracker(trackerId: string) {
    setStatus("Deleting tracker...");
    await deleteSocialTracker(guildId, trackerId);
    await reload();
    setStatus("Tracker deleted.");
  }

  async function saveGameSettings() {
    if (!gameSettings) {
      return;
    }
    setStatus("Saving game settings...");
    const updated = await updateGameSuggestionSettings(guildId, {
      enabled: gameSettings.enabled,
      announcementChannelId: gameSettings.announcementChannelId,
      rewardRoleId: gameSettings.rewardRoleId,
      mentionEveryone: gameSettings.mentionEveryone,
      announcementWeekday: gameSettings.announcementWeekday,
      announcementHourUtc: gameSettings.announcementHourUtc,
      customMessage: gameSettings.customMessage,
    });
    setGameSettings(updated);
    setStatus("Game settings saved.");
  }

  return (
    <div className="grid gap-6">
      <section className="grid gap-3">
        <div className="flex items-center gap-2">
          <Bell aria-hidden="true" size={20} />
          <h2 className="text-lg font-semibold">Social trackers</h2>
          <InfoBubble label="Tracker help">
            YouTube uses public channel RSS feeds now. TikTok, Instagram, and Facebook are saved as
            provider configs for the next API connector pass.
          </InfoBubble>
        </div>

        <div className="grid gap-3 lg:grid-cols-[1fr_360px]">
          <div className="grid gap-2">
            {trackers.length === 0 && (
              <Card className="p-3 text-sm text-muted-foreground">
                No trackers yet. Add one with the form on the right.
              </Card>
            )}
            {trackers.map((tracker) => (
              <Card key={tracker.id} className="p-3">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="font-semibold">{tracker.label}</h3>
                      <span className="rounded-md bg-muted px-2 py-1 text-xs text-muted-foreground">
                        {tracker.provider}
                      </span>
                      <span className="rounded-md bg-muted px-2 py-1 text-xs text-muted-foreground">
                        {tracker.isEnabled ? "Enabled" : "Paused"}
                      </span>
                    </div>
                    <div className="mt-1 text-sm text-muted-foreground">
                      Channel ID: {tracker.notificationChannelId}
                    </div>
                    <div className="mt-1 text-sm text-muted-foreground">
                      Source: {tracker.sourceId}
                    </div>
                    {tracker.lastSeenUrl && (
                      <a
                        className="mt-1 block text-sm text-primary"
                        href={tracker.lastSeenUrl}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Last seen item
                      </a>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="secondary"
                      onClick={() => {
                        setEditingId(tracker.id);
                        setEditing({
                          provider: tracker.provider,
                          label: tracker.label,
                          sourceId: tracker.sourceId,
                          sourceUrl: tracker.sourceUrl,
                          notificationChannelId: tracker.notificationChannelId,
                          customMessage: tracker.customMessage,
                          isEnabled: tracker.isEnabled,
                        });
                      }}
                    >
                      Edit
                    </Button>
                    <Button variant="ghost" onClick={() => removeTracker(tracker.id)}>
                      <Trash2 aria-hidden="true" size={16} />
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>

          <Card className="p-4">
            <div className="mb-3 flex items-center gap-2">
              <Plus aria-hidden="true" size={18} />
              <h3 className="font-semibold">{editingId ? "Edit tracker" : "Add tracker"}</h3>
            </div>
            <div className="grid gap-3">
              <label className="grid gap-1 text-sm font-medium">
                Provider
                <select
                  className="h-9 rounded-md border border-border px-3 text-sm font-normal"
                  value={editing.provider}
                  onChange={(event) =>
                    setEditing({ ...editing, provider: event.target.value as TrackerProvider })
                  }
                >
                  {providers.map((provider) => (
                    <option key={provider} value={provider}>
                      {provider}
                    </option>
                  ))}
                </select>
              </label>
              <label className="grid gap-1 text-sm font-medium">
                Name
                <input
                  className="h-9 rounded-md border border-border px-3 text-sm font-normal"
                  value={editing.label}
                  onChange={(event) => setEditing({ ...editing, label: event.target.value })}
                  placeholder="BU Gaming YouTube"
                />
              </label>
              <label className="grid gap-1 text-sm font-medium">
                Source ID
                <input
                  className="h-9 rounded-md border border-border px-3 text-sm font-normal"
                  value={editing.sourceId}
                  onChange={(event) => setEditing({ ...editing, sourceId: event.target.value })}
                  placeholder="YouTube channel ID"
                />
              </label>
              <label className="grid gap-1 text-sm font-medium">
                Source URL
                <input
                  className="h-9 rounded-md border border-border px-3 text-sm font-normal"
                  value={editing.sourceUrl ?? ""}
                  onChange={(event) =>
                    setEditing({ ...editing, sourceUrl: event.target.value || null })
                  }
                  placeholder="Optional public profile URL"
                />
              </label>
              <label className="grid gap-1 text-sm font-medium">
                Notification channel ID
                <input
                  className="h-9 rounded-md border border-border px-3 text-sm font-normal"
                  value={editing.notificationChannelId}
                  onChange={(event) =>
                    setEditing({ ...editing, notificationChannelId: event.target.value })
                  }
                  placeholder="123456789012345678"
                />
              </label>
              <label className="grid gap-1 text-sm font-medium">
                Message
                <textarea
                  className="min-h-24 rounded-md border border-border px-3 py-2 text-sm font-normal"
                  value={editing.customMessage}
                  onChange={(event) =>
                    setEditing({ ...editing, customMessage: event.target.value })
                  }
                />
              </label>
              <label className="flex items-center gap-2 text-sm font-medium">
                <input
                  type="checkbox"
                  checked={editing.isEnabled}
                  onChange={(event) =>
                    setEditing({ ...editing, isEnabled: event.target.checked })
                  }
                />
                Enabled
              </label>
              <div className="flex gap-2">
                <Button onClick={saveTracker}>
                  <Save aria-hidden="true" size={16} />
                  Save tracker
                </Button>
                {editingId && (
                  <Button
                    variant="ghost"
                    onClick={() => {
                      setEditingId(null);
                      setEditing(newTrackerDraft());
                    }}
                  >
                    Cancel
                  </Button>
                )}
              </div>
            </div>
          </Card>
        </div>
      </section>

      <section className="grid gap-3">
        <div className="flex items-center gap-2">
          <Gamepad2 aria-hidden="true" size={20} />
          <h2 className="text-lg font-semibold">Weekly game suggestion</h2>
          <InfoBubble label="Game suggestion help">
            The bot watches Discord playing activity, picks one user's game each week, optionally
            grants a reward role, and posts the configured announcement.
          </InfoBubble>
        </div>

        {gameSettings && (
          <Card className="p-4">
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="flex items-center gap-2 text-sm font-medium sm:col-span-2">
                <input
                  type="checkbox"
                  checked={gameSettings.enabled}
                  onChange={(event) =>
                    setGameSettings({ ...gameSettings, enabled: event.target.checked })
                  }
                />
                Enable weekly pick
              </label>
              <label className="grid gap-1 text-sm font-medium">
                Announcement channel ID
                <input
                  className="h-9 rounded-md border border-border px-3 text-sm font-normal"
                  value={gameSettings.announcementChannelId ?? ""}
                  onChange={(event) =>
                    setGameSettings({
                      ...gameSettings,
                      announcementChannelId: event.target.value || null,
                    })
                  }
                />
              </label>
              <label className="grid gap-1 text-sm font-medium">
                Reward role ID
                <input
                  className="h-9 rounded-md border border-border px-3 text-sm font-normal"
                  value={gameSettings.rewardRoleId ?? ""}
                  onChange={(event) =>
                    setGameSettings({ ...gameSettings, rewardRoleId: event.target.value || null })
                  }
                />
              </label>
              <label className="grid gap-1 text-sm font-medium">
                Pick day
                <select
                  className="h-9 rounded-md border border-border px-3 text-sm font-normal"
                  value={gameSettings.announcementWeekday}
                  onChange={(event) =>
                    setGameSettings({
                      ...gameSettings,
                      announcementWeekday: Number(event.target.value),
                    })
                  }
                >
                  {weekdays.map((day, index) => (
                    <option key={day} value={index}>
                      {day}
                    </option>
                  ))}
                </select>
              </label>
              <label className="grid gap-1 text-sm font-medium">
                Pick hour UTC
                <input
                  className="h-9 rounded-md border border-border px-3 text-sm font-normal"
                  type="number"
                  min={0}
                  max={23}
                  value={gameSettings.announcementHourUtc}
                  onChange={(event) =>
                    setGameSettings({
                      ...gameSettings,
                      announcementHourUtc: Number(event.target.value),
                    })
                  }
                />
              </label>
              <label className="flex items-center gap-2 text-sm font-medium sm:col-span-2">
                <input
                  type="checkbox"
                  checked={gameSettings.mentionEveryone}
                  onChange={(event) =>
                    setGameSettings({ ...gameSettings, mentionEveryone: event.target.checked })
                  }
                />
                Mention @everyone
              </label>
              <label className="grid gap-1 text-sm font-medium sm:col-span-2">
                Announcement message
                <textarea
                  className="min-h-24 rounded-md border border-border px-3 py-2 text-sm font-normal"
                  value={gameSettings.customMessage}
                  onChange={(event) =>
                    setGameSettings({ ...gameSettings, customMessage: event.target.value })
                  }
                />
              </label>
            </div>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <Button onClick={saveGameSettings}>
                <Save aria-hidden="true" size={16} />
                Save game settings
              </Button>
              {gameSettings.lastAnnouncedWeek && (
                <span className="text-sm text-muted-foreground">
                  Last announced: {gameSettings.lastAnnouncedWeek}
                </span>
              )}
            </div>
          </Card>
        )}

        <div className="grid gap-2">
          {gamePicks.map((pick) => (
            <Card key={pick.id} className="p-3 text-sm">
              <span className="font-medium">{pick.gameName}</span>
              <span className="text-muted-foreground"> from {pick.username}</span>
              <span className="text-muted-foreground"> during {pick.announcedWeek}</span>
            </Card>
          ))}
        </div>
      </section>

      {status && <div className="text-sm text-muted-foreground">{status}</div>}
    </div>
  );
}

function newTrackerDraft(): SocialTrackerPayload {
  return {
    provider: "youtube",
    label: "",
    sourceId: "",
    sourceUrl: null,
    notificationChannelId: "",
    customMessage: "New {provider} post from {source}: {title}\n{url}",
    isEnabled: true,
  };
}
