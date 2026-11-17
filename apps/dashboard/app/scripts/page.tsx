"use client";

import { FormEvent, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Script } from "@/lib/types";

const sample = `[
  {"action": "goto_channel", "channel": "{{channel}}"},
  {"action": "wait_chat", "timeout_ms": 20000},
  {"action": "send_chat", "text": "{{text}}"},
  {"action": "listen", "duration_ms": 10000}
]`;

export default function ScriptsPage() {
  const [scripts, setScripts] = useState<Script[]>([]);

  async function load() {
    setScripts(await api.scripts());
  }

  useEffect(() => {
    load();
  }, []);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const triggerContains = String(fd.get("trigger") || "").trim();
    let steps: unknown[];
    try {
      steps = JSON.parse(String(fd.get("steps")));
    } catch {
      window.alert("steps JSON inválido");
      return;
    }
    await api.saveScript({
      name: fd.get("name"),
      enabled: true,
      steps,
      trigger: triggerContains ? { contains: triggerContains, reply: fd.get("reply") } : null,
    });
    load();
  }

  return (
    <div className="grid gap-8 md:grid-cols-2">
      <div>
        <h2 className="mb-4 text-2xl">Scripts de interacción</h2>
        <ul className="space-y-3">
          {scripts.map((s) => (
            <li key={s.id} className="rounded-xl border border-line bg-panel p-4">
              <div className="mb-2 flex justify-between">
                <strong>{s.name}</strong>
                <span className="text-xs text-dim">{s.enabled ? "on" : "off"}</span>
              </div>
              <pre className="overflow-auto text-xs text-dim">{JSON.stringify(s.steps, null, 2)}</pre>
            </li>
          ))}
        </ul>
      </div>
      <form onSubmit={onSubmit} className="space-y-3 rounded-2xl border border-line bg-panel p-5">
        <h3 className="text-lg">Nuevo script</h3>
        <input name="name" required placeholder="nombre" className="w-full rounded-lg border border-line bg-ink px-3 py-2 text-sm" />
        <textarea name="steps" defaultValue={sample} className="h-56 w-full rounded-lg border border-line bg-ink px-3 py-2 font-mono text-xs" />
        <input name="trigger" placeholder="si el chat contiene…" className="w-full rounded-lg border border-line bg-ink px-3 py-2 text-sm" />
        <input name="reply" placeholder="respuesta evento" className="w-full rounded-lg border border-line bg-ink px-3 py-2 text-sm" />
        <button className="w-full rounded-lg bg-go py-2 text-sm font-medium text-black">Guardar</button>
      </form>
    </div>
  );
}
