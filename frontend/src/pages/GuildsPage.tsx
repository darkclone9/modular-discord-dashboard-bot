import type { Guild } from "../api/guilds";
import { Card } from "../components/ui/card";

type Props = {
  guilds: Guild[];
  onSelect: (guildId: string) => void;
};

export function GuildsPage({ guilds, onSelect }: Props) {
  return (
    <section>
      <h1 className="text-2xl font-semibold">Servers</h1>
      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {guilds.map((guild) => (
          <button key={guild.id} className="text-left" onClick={() => onSelect(guild.id)}>
            <Card className="p-4 transition-colors hover:border-primary">
              <div className="font-medium">{guild.name}</div>
              <div className="mt-1 text-sm text-muted-foreground">Manage Server</div>
            </Card>
          </button>
        ))}
      </div>
    </section>
  );
}
