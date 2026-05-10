import { LoginButton } from "../components/LoginButton";
import { Card } from "../components/ui/card";

export function LoginPage() {
  return (
    <main className="grid min-h-screen place-items-center px-4">
      <Card className="w-full max-w-sm p-6">
        <h1 className="text-xl font-semibold">Modular Bot Dashboard</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Sign in with Discord to manage servers where you have Manage Server.
        </p>
        <div className="mt-5">
          <LoginButton />
        </div>
      </Card>
    </main>
  );
}
