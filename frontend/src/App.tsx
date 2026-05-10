import { useEffect, useState } from "react";

import { apiFetch } from "./api/client";
import { type Guild, listGuilds } from "./api/guilds";
import { AppShell } from "./components/AppShell";
import { GuildDashboardPage } from "./pages/GuildDashboardPage";
import { GuildsPage } from "./pages/GuildsPage";
import { LoginPage } from "./pages/LoginPage";

type User = {
  id: string;
  username: string;
  avatar: string | null;
  csrfToken: string;
};

export function App() {
  const [user, setUser] = useState<User | null>(null);
  const [guilds, setGuilds] = useState<Guild[]>([]);
  const [selectedGuildId, setSelectedGuildId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const me = await apiFetch<User>("/auth/me");
        setUser(me);
        const manageableGuilds = await listGuilds();
        setGuilds(manageableGuilds);
        setSelectedGuildId(manageableGuilds[0]?.id ?? null);
      } catch {
        setUser(null);
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, []);

  if (loading) {
    return <div className="grid min-h-screen place-items-center text-sm">Loading dashboard...</div>;
  }

  if (!user) {
    return <LoginPage />;
  }

  return (
    <AppShell username={user.username} onLogout={() => setUser(null)}>
      {selectedGuildId ? (
        <GuildDashboardPage
          guilds={guilds}
          selectedGuildId={selectedGuildId}
          onSelectGuild={setSelectedGuildId}
        />
      ) : (
        <GuildsPage guilds={guilds} onSelect={setSelectedGuildId} />
      )}
    </AppShell>
  );
}
