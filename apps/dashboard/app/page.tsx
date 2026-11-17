"use client";

import { useCallback, useEffect, useState } from "react";
import { WorkerCard } from "@/components/WorkerCard";
import { api, wsUrl } from "@/lib/api";
import type { Worker } from "@/lib/types";

export default function HomePage() {
  const [workers, setWorkers] = useState<Worker[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setWorkers(await api.workers());
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "error");
    }
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, 4000);
    const ws = new WebSocket(wsUrl());
    ws.onmessage = () => load();
    return () => {
      clearInterval(t);
      ws.close();
    };
  }, [load]);

  return (
    <div>
      <div className="mb-6 flex items-end justify-between">
        <div>
          <p className="mb-2 inline-flex rounded-full bg-go/15 px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide text-go">
            Control plane
          </p>
          <h2 className="text-2xl">Web Dashboard + API</h2>
          <p className="text-sm text-dim">Fleet management · Monitoring · Logs · Commands</p>
        </div>
        <p className="text-xs text-dim">Docker network · Resource limits · Health checks</p>
      </div>
      {error && <p className="mb-4 text-sm text-red-300">{error}</p>}
      <div className="grid gap-4 md:grid-cols-3">
        {workers.map((w) => (
          <WorkerCard key={w.id} worker={w} onChanged={load} />
        ))}
      </div>
      {workers.length === 0 && !error && <p className="text-dim">Esperando registro de workers…</p>}
    </div>
  );
}
