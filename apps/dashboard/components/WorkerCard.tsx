"use client";

import Link from "next/link";
import { api } from "@/lib/api";
import type { Worker } from "@/lib/types";
import { Badge, statusTone } from "./Badge";

export function WorkerCard({ worker, onChanged }: { worker: Worker; onChanged: () => void }) {
  const preview = worker.has_snapshot ? api.snapshotUrl(worker.id) : null;
  async function act(action: "start" | "stop" | "restart") {
    await api.control(worker.id, action);
    onChanged();
  }
  return (
    <article className="rounded-2xl border border-line bg-panel p-4">
      <div className="mb-3 flex items-start justify-between">
        <div>
          <h3 className="text-lg">{worker.name}</h3>
          <p className="font-mono text-xs text-dim">{worker.id} · Chromium</p>
        </div>
        <Badge tone={statusTone(worker.status)}>{worker.status}</Badge>
      </div>
      <Link href={`/workers/${worker.id}`} className="block overflow-hidden rounded-xl border border-line bg-black">
        {preview ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={preview} alt={worker.name} className="h-40 w-full object-cover opacity-90" />
        ) : (
          <div className="flex h-40 items-center justify-center text-sm text-dim">Sin snapshot</div>
        )}
      </Link>
      <dl className="mt-3 grid grid-cols-2 gap-2 text-xs text-dim">
        <div>CPU {worker.cpu_percent.toFixed(1)}%</div>
        <div>RAM {Math.round(worker.ram_mb)} MB</div>
      </dl>
      <div className="mt-3 flex gap-2">
        <button onClick={() => act("start")} className="rounded-lg border border-line px-2 py-1 text-xs hover:border-go">
          Start
        </button>
        <button onClick={() => act("stop")} className="rounded-lg border border-line px-2 py-1 text-xs hover:border-red-400">
          Stop
        </button>
        <button onClick={() => act("restart")} className="rounded-lg border border-line px-2 py-1 text-xs hover:border-white">
          Restart
        </button>
      </div>
    </article>
  );
}
