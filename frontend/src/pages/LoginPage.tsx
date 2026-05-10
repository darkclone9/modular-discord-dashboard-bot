import type { FormEvent } from "react";
import { useState } from "react";

import { loginWithPassword, type DashboardUser } from "../api/auth";
import { LoginButton } from "../components/LoginButton";
import { ThemeToggle } from "../components/ThemeToggle";
import { Button } from "../components/ui/button";
import { Card } from "../components/ui/card";

type Props = {
  theme: "light" | "dark";
  onToggleTheme: () => void;
  onAuthenticated: (user: DashboardUser) => Promise<void>;
};

export function LoginPage({ theme, onToggleTheme, onAuthenticated }: Props) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function submitLocalLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const user = await loginWithPassword(username, password);
      await onAuthenticated(user);
    } catch {
      setError("Username or password was not accepted.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="grid min-h-screen place-items-center px-4">
      <Card className="w-full max-w-sm p-6">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h1 className="text-xl font-semibold">Modular Bot Dashboard</h1>
            <p className="mt-2 text-sm text-muted-foreground">
              Sign in with the local admin account or Discord OAuth.
            </p>
          </div>
          <ThemeToggle theme={theme} onToggle={onToggleTheme} />
        </div>

        <form className="mt-5 grid gap-3" onSubmit={submitLocalLogin}>
          <label className="grid gap-1 text-sm font-medium">
            Username
            <input
              className="h-9 rounded-md border border-border px-3 text-sm font-normal"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              autoComplete="username"
            />
          </label>
          <label className="grid gap-1 text-sm font-medium">
            Password
            <input
              className="h-9 rounded-md border border-border px-3 text-sm font-normal"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              type="password"
              autoComplete="current-password"
            />
          </label>
          {error && <div className="text-sm text-red-600 dark:text-red-300">{error}</div>}
          <Button type="submit" disabled={submitting || !username || !password}>
            {submitting ? "Signing in..." : "Sign in"}
          </Button>
        </form>

        <div className="my-5 h-px bg-border" />
        <p className="mt-2 text-sm text-muted-foreground">
          Discord login is still available when OAuth is configured correctly.
        </p>
        <div className="mt-3">
          <LoginButton />
        </div>
      </Card>
    </main>
  );
}
