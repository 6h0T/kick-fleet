import type { Account, Script, Task, Worker } from "./types";

export function apiBase(): string {
  return process.env.NEXT_PUBLIC_CONTROLLER_URL || "";
}

export function wsUrl(): string {
  if (process.env.NEXT_PUBLIC_WS_URL) return process.env.NEXT_PUBLIC_WS_URL;
  if (typeof window === "undefined") return "ws://localhost:3030/ws";
  const proto = window.location.protocol === "https:" ? "wss" : "ws";
  return `${proto}://${window.location.host}/ws`;
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${apiBase()}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json();
}

export const api = {
  workers: () => req<Worker[]>("/api/v1/workers"),
  accounts: () => req<Account[]>("/api/v1/accounts"),
  tasks: () => req<Task[]>("/api/v1/tasks"),
  logs: () => req<Array<{ id: number; worker_id: string | null; level: string; message: string; created_at: string }>>("/api/v1/logs"),
  chat: () => req<Array<{ id: string; worker_id: string | null; channel: string; direction: string; body: string; created_at: string }>>("/api/v1/chat/messages"),
  scripts: () => req<Script[]>("/api/v1/scripts"),
  control: (id: string, action: "start" | "stop" | "restart") => req(`/api/v1/workers/${id}/${action}`, { method: "POST" }),
  provision: (body: object) => req("/api/v1/accounts/provision", { method: "POST", body: JSON.stringify(body) }),
  createAccount: (body: object) => req("/api/v1/accounts", { method: "POST", body: JSON.stringify(body) }),
  dispatch: (body: object) => req("/api/v1/chat/dispatch", { method: "POST", body: JSON.stringify(body) }),
  createTask: (body: object) => req("/api/v1/tasks", { method: "POST", body: JSON.stringify(body) }),
  saveScript: (body: object) => req("/api/v1/scripts", { method: "POST", body: JSON.stringify(body) }),
  snapshotUrl: (id: string) => `${apiBase()}/api/v1/workers/${id}/snapshot?t=${Date.now()}`,
};
