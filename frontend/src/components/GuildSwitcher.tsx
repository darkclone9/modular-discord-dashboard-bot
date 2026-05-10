import type { Guild } from "../api/guilds";

type Props = {
  guilds: Guild[];
  selectedGuildId?: string;
  onSelect: (guildId: string) => void;
};

export function GuildSwitcher({ guilds, selectedGuildId, onSelect }: Props) {
  return (
    <select
      className="h-9 w-full rounded-md border border-border bg-white px-3 text-sm"
      value={selectedGuildId ?? ""}
      onChange={(event) => onSelect(event.target.value)}
      aria-label="Select guild"
    >
      <option value="" disabled>
        Select a server
      </option>
      {guilds.map((guild) => (
        <option key={guild.id} value={guild.id}>
          {guild.name}
        </option>
      ))}
    </select>
  );
}
