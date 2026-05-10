import { useState } from "react";

import type { Guild } from "../api/guilds";
import { GuildSwitcher } from "../components/GuildSwitcher";
import { FormsPage } from "../../../app/modules/forms/frontend/FormsPage";
import { TrackersPage } from "../../../app/modules/trackers/frontend/TrackersPage";

type Props = {
  guilds: Guild[];
  selectedGuildId: string;
  onSelectGuild: (guildId: string) => void;
};

export function GuildDashboardPage({ guilds, selectedGuildId, onSelectGuild }: Props) {
  const guild = guilds.find((item) => item.id === selectedGuildId);
  const [activeModule, setActiveModule] = useState<"forms" | "trackers">("forms");

  return (
    <section>
      <div className="flex flex-col gap-3 border-b border-border pb-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{guild?.name ?? "Server"}</h1>
          <p className="mt-1 text-sm text-muted-foreground">Server modules</p>
        </div>
        <div className="w-full sm:w-72">
          <GuildSwitcher guilds={guilds} selectedGuildId={selectedGuildId} onSelect={onSelectGuild} />
        </div>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <button
          className={`rounded-md px-3 py-2 text-sm font-medium ${
            activeModule === "forms" ? "bg-primary text-primary-foreground" : "bg-muted"
          }`}
          onClick={() => setActiveModule("forms")}
        >
          Forms
        </button>
        <button
          className={`rounded-md px-3 py-2 text-sm font-medium ${
            activeModule === "trackers" ? "bg-primary text-primary-foreground" : "bg-muted"
          }`}
          onClick={() => setActiveModule("trackers")}
        >
          Trackers
        </button>
      </div>
      <div className="mt-6">
        {activeModule === "forms" ? (
          <FormsPage guildId={selectedGuildId} />
        ) : (
          <TrackersPage guildId={selectedGuildId} />
        )}
      </div>
    </section>
  );
}
