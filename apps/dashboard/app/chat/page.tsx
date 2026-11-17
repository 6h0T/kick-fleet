"use client";

import { FormEvent, useEffect, useState } from "react";
import { api, wsUrl } from "@/lib/api";
import type { Account, Script } from "@/lib/types";

type Msg = { id: string; worker_id: string | null; channel: string; direction: string; body: string; created_at: string };

export default function ChatPage() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [scripts, setScripts] = useState<Script[]>([]);

  async function load() {
    setMessages(await api.chat());
    setAccounts(await api.accounts());
    setScripts(await api.scripts());
  }

  useEffect(() => {
    load();
    const ws = new WebSocket(wsUrl());
    ws.onmessage = () => load();
    return () => ws.close();
  }, []);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const accountId = String(fd.get("account_id") || "");
    await api.dispatch({
      channel: fd.get("channel"),
      text: fd.get("text"),
      account_ids: accountId ? [accountId] : undefined,
      script_name: fd.get("script_name") || null,
    });
    load();
  }

  return (
    <div className="grid gap-6 md:grid-cols-[1fr_340px]">
      <div>
        <h2 className="mb-4 text-2xl">Actividad de chat</h2>
        <ul className="space-y-2 font-mono text-sm">
          {messages.map((m) => (
            <li key={m.id} className="rounded-xl border border-line bg-panel px-4 py-3">
              <span className="text-dim">
                {m.created_at} · {m.direction} · {m.channel} · {m.worker_id}
              </span>
              <div>{m.body}</div>
            </li>
          ))}
        </ul>
      </div>
      <form onSubmit={onSubmit} className="space-y-3 rounded-2xl border border-line bg-panel p-5">
        <h3 className="text-lg">Dispatcher</h3>
        <input name="channel" required placeholder="canal" className="w-full rounded-lg border border-line bg-ink px-3 py-2 text-sm" />
        <textarea name="text" required placeholder="mensaje de prueba" className="h-24 w-full rounded-lg border border-line bg-ink px-3 py-2 text-sm" />
        <select name="account_id" className="w-full rounded-lg border border-line bg-ink px-3 py-2 text-sm">
          <option value="">todas las cuentas asignadas</option>
          {accounts.map((a) => (
            <option key={a.id} value={a.id}>
              {a.username}
            </option>
          ))}
        </select>
        <select name="script_name" className="w-full rounded-lg border border-line bg-ink px-3 py-2 text-sm">
          <option value="">enviar texto directo</option>
          {scripts.map((s) => (
            <option key={s.id} value={s.name}>
              {s.name}
            </option>
          ))}
        </select>
        <button className="w-full rounded-lg bg-white py-2 text-sm font-medium text-black">Encolar</button>
      </form>
    </div>
  );
}
