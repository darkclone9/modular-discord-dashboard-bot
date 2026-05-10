type Props = {
  guildId: string;
};

export function FormsPage({ guildId }: Props) {
  return (
    <div className="rounded-lg border border-dashed border-border bg-white p-6 text-sm text-muted-foreground">
      Forms module coming in PR #2 for server {guildId}.
    </div>
  );
}
