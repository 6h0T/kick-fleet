"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import type { Worker } from "@/lib/types";
import { Badge, statusTone } from "@/components/Badge";

function vncSrc(url: string | null, id: string) {
  if (!url) return "";
  if (url.startsWith("/")) return `${url.replace(/\/?$/, "/")}/vnc.html?autoconnect=1&resize=scale&path=websockify`;
  return `${url.replace(/\/?$/, "/")}/vnc.html?autoconnect=1&resize=scale`;
}

export default function WorkerPage() {
  const params = useParams<{ id: string }>();
  const [worker, setWorker] = useState<Worker | null>(null);

  async function load() {
    const all = await api.workers();
    setWorker(all.find((w) => w.id === params.id) || null);
  }

  useEffect(() => {
    load();
    const t = setInterval(load, 4000);
    return () => clearInterval(t);
  }, [params.id]);

  if (!worker) return <p className="text-dim">Cargando worker…</p>;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl">{worker.name}</h2>
          <p className="font-mono text-xs text-dim">{worker.id}</p>
        </div>
        <Badge tone={statusTone(worker.status)}>{worker.status}</Badge>
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        <div className="rounded-xl border border-line bg-panel p-4 text-sm">CPU {worker.cpu_percent.toFixed(1)}%</div>
        <div className="rounded-xl border border-line bg-panel p-4 text-sm">RAM {Math.round(worker.ram_mb)} MB</div>
        <div className="rounded-xl border border-line bg-panel p-4 text-sm">Límite {worker.ram_limit_mb ? `${Math.round(worker.ram_limit_mb)} MB` : "host"}</div>
        <div className="flex gap-2">
          {(["start", "stop", "restart"] as const).map((a) => (
            <button
              key={a}
              onClick={async () => {
                await api.control(worker.id, a);
                load();
              }}
              className="flex-1 rounded-xl border border-line bg-panel text-sm capitalize"
            >
              {a}
            </button>
          ))}
        </div>
      </div>
      <div className="overflow-hidden rounded-2xl border border-line bg-black">
        <iframe title="noVNC" className="h-[70vh] w-full border-0" src={vncSrc(worker.novnc_url, worker.id)} />
      </div>
      <div className="flex gap-2">
        <button
          className="rounded-lg border border-line px-3 py-2 text-sm"
          onClick={() => api.createTask({ type: "inspect", worker_id: worker.id })}
        >
          Inspección DOM / a11y
        </button>
        <button
          className="rounded-lg border border-line px-3 py-2 text-sm"
          onClick={() => api.createTask({ type: "screenshot", worker_id: worker.id })}
        >
          Screenshot
        </button>
      </div>
    </div>
  );
}
