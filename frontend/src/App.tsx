import { useCallback, useEffect, useState } from "react";

import { getCurrentUser, type DashboardUser } from "./api/auth";
import { type Guild, listGuilds } from "./api/guilds";
import { AppShell } from "./components/AppShell";
import { GuildDashboardPage } from "./pages/GuildDashboardPage";
import { GuildsPage } from "./pages/GuildsPage";
import { LoginPage } from "./pages/LoginPage";

function getInitialTheme(): "light" | "dark" {
  const saved = window.localStorage.getItem("theme");
  if (saved === "light" || saved === "dark") {
    return saved;
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function App() {
  const [user, setUser] = useState<DashboardUser | null>(null);
  const [guilds, setGuilds] = useState<Guild[]>([]);
  const [selectedGuildId, setSelectedGuildId] = useState<string | null>(null);
  const [dashboardError, setDashboardError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [theme, setTheme] = useState<"light" | "dark">(getInitialTheme);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    window.localStorage.setItem("theme", theme);
  }, [theme]);

  const loadDashboard = useCallback(async (nextUser?: DashboardUser) => {
    setDashboardError(null);
    const me = nextUser ?? (await getCurrentUser());
    setUser(me);
    try {
      const manageableGuilds = await listGuilds();
      setGuilds(manageableGuilds);
      setSelectedGuildId((current) => {
        if (current && manageableGuilds.some((guild) => guild.id === current)) {
          return current;
        }
        return manageableGuilds[0]?.id ?? null;
      });
    } catch {
      setGuilds([]);
      setSelectedGuildId(null);
      setDashboardError("Signed in, but I could not load servers for this account.");
    }
  }, []);

  useEffect(() => {
    async function load() {
      try {
        await loadDashboard();
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
    return (
      <LoginPage
        theme={theme}
        onToggleTheme={() => setTheme((current) => (current === "dark" ? "light" : "dark"))}
        onAuthenticated={loadDashboard}
      />
    );
  }

  return (
    <AppShell
      username={user.username}
      theme={theme}
      onToggleTheme={() => setTheme((current) => (current === "dark" ? "light" : "dark"))}
      onLogout={() => setUser(null)}
    >
      {dashboardError && (
        <div className="mb-4 rounded-md border border-border bg-card p-3 text-sm text-muted-foreground">
          {dashboardError}
        </div>
      )}
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
