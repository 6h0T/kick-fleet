"use client";

import { FormEvent, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Account, Worker } from "@/lib/types";
import { Badge, statusTone } from "@/components/Badge";

export default function AccountsPage() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [workers, setWorkers] = useState<Worker[]>([]);

  async function load() {
    setAccounts(await api.accounts());
    setWorkers(await api.workers());
  }

  useEffect(() => {
    load();
  }, []);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget; // React nulls currentTarget after the await
    const fd = new FormData(form);
    await api.provision({
      username: fd.get("username"),
      password: fd.get("password"),
      channel: fd.get("channel"),
      worker_id: fd.get("worker_id") || null,
      notes: "authorized test account",
    });
    form.reset();
    load();
  }

  return (
    <div className="grid gap-8 md:grid-cols-[1fr_320px]">
      <div>
        <h2 className="mb-4 text-2xl">Inventario de cuentas</h2>
        <table className="w-full text-left text-sm">
          <thead className="text-dim">
            <tr>
              <th className="pb-2">Usuario</th>
              <th>Estado</th>
              <th>Salud</th>
              <th>Worker</th>
            </tr>
          </thead>
          <tbody>
            {accounts.map((a) => (
              <tr key={a.id} className="border-t border-line">
                <td className="py-3 font-mono">{a.username}</td>
                <td>
                  <Badge tone={statusTone(a.status)}>{a.status}</Badge>
                </td>
                <td>{a.health_score}</td>
                <td className="text-dim">{a.assigned_worker_id || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <form onSubmit={onSubmit} className="space-y-3 rounded-2xl border border-line bg-panel p-5">
        <h3 className="text-lg">Provisionar cuenta de prueba</h3>
        <input name="username" required placeholder="usuario" className="w-full rounded-lg border border-line bg-ink px-3 py-2 text-sm" />
        <input name="password" required type="password" placeholder="credencial" className="w-full rounded-lg border border-line bg-ink px-3 py-2 text-sm" />
        <input name="channel" required placeholder="canal kick" className="w-full rounded-lg border border-line bg-ink px-3 py-2 text-sm" />
        <select name="worker_id" className="w-full rounded-lg border border-line bg-ink px-3 py-2 text-sm">
          <option value="">asignar worker</option>
          {workers.map((w) => (
            <option key={w.id} value={w.id}>
              {w.name}
            </option>
          ))}
        </select>
        <button className="w-full rounded-lg bg-go py-2 text-sm font-medium text-black">Guardar y login</button>
        <p className="text-xs text-dim">Vault cifrado con FERNET_KEY. Solo cuentas de prueba autorizadas.</p>
      </form>
    </div>
  );
}
