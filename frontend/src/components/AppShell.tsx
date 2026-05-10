import { LogOut, Settings } from "lucide-react";
import type { ReactNode } from "react";

import { apiFetch } from "../api/client";
import { Button } from "./ui/button";

type Props = {
  children: ReactNode;
  username?: string;
  onLogout: () => void;
};

export function AppShell({ children, username, onLogout }: Props) {
  async function logout() {
    await apiFetch("/auth/logout", { method: "POST" });
    onLogout();
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-border bg-white">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
          <div className="flex items-center gap-2 text-sm font-semibold">
            <Settings aria-hidden="true" size={17} />
            Modular Bot
          </div>
          <div className="flex items-center gap-3 text-sm text-muted-foreground">
            {username && <span>{username}</span>}
            <Button variant="ghost" onClick={logout} title="Log out">
              <LogOut aria-hidden="true" size={16} />
            </Button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>
    </div>
  );
}
