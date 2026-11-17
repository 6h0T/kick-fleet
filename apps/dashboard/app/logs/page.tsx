"use client";

import { useEffect, useState } from "react";
import { api, wsUrl } from "@/lib/api";

type Log = { id: number; worker_id: string | null; level: string; message: string; created_at: string };

export default function LogsPage() {
  const [logs, setLogs] = useState<Log[]>([]);

  async function load() {
    setLogs(await api.logs());
  }

  useEffect(() => {
    load();
    const ws = new WebSocket(wsUrl());
    ws.onmessage = () => load();
    const t = setInterval(load, 5000);
    return () => {
      ws.close();
      clearInterval(t);
    };
  }, []);

  return (
    <div>
      <h2 className="mb-4 text-2xl">Logs</h2>
      <ul className="space-y-2 font-mono text-xs">
        {logs.map((l) => (
          <li key={l.id} className="rounded-lg border border-line bg-panel px-3 py-2">
            <span className="text-dim">
              {l.created_at} [{l.level}] {l.worker_id}
            </span>
            <div>{l.message}</div>
          </li>
        ))}
      </ul>
    </div>
  );
}
