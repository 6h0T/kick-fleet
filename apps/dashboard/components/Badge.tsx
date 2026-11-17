export function Badge({ children, tone = "dim" }: { children: React.ReactNode; tone?: "go" | "dim" | "warn" | "bad" }) {
  const map = {
    go: "bg-go/15 text-go",
    dim: "bg-white/5 text-dim",
    warn: "bg-amber-400/15 text-amber-300",
    bad: "bg-red-500/15 text-red-300",
  };
  return <span className={`rounded-full px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide ${map[tone]}`}>{children}</span>;
}

export function statusTone(status: string): "go" | "dim" | "warn" | "bad" {
  if (["idle", "active", "session_live", "done", "busy"].includes(status)) return "go";
  if (["starting", "provisioning", "queued", "running"].includes(status)) return "warn";
  if (["error", "stale", "unhealthy", "stopped"].includes(status)) return "bad";
  return "dim";
}
