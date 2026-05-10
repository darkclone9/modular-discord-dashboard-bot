import type { Guild } from "../api/guilds";
import { GuildSwitcher } from "../components/GuildSwitcher";
import { FormsPage } from "../../../app/modules/forms/frontend/FormsPage";

type Props = {
  guilds: Guild[];
  selectedGuildId: string;
  onSelectGuild: (guildId: string) => void;
};

export function GuildDashboardPage({ guilds, selectedGuildId, onSelectGuild }: Props) {
  const guild = guilds.find((item) => item.id === selectedGuildId);

  return (
    <section>
      <div className="flex flex-col gap-3 border-b border-border pb-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{guild?.name ?? "Server"}</h1>
          <p className="mt-1 text-sm text-muted-foreground">Forms and applications</p>
        </div>
        <div className="w-full sm:w-72">
          <GuildSwitcher guilds={guilds} selectedGuildId={selectedGuildId} onSelect={onSelectGuild} />
        </div>
      </div>
      <div className="mt-6">
        <FormsPage guildId={selectedGuildId} />
      </div>
    </section>
  );
}
