"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Flota" },
  { href: "/accounts", label: "Cuentas" },
  { href: "/chat", label: "Chat" },
  { href: "/scripts", label: "Scripts" },
  { href: "/logs", label: "Logs" },
];

export function Nav() {
  const path = usePathname();
  return (
    <header className="flex items-center justify-between border-b border-line px-8 py-5">
      <div>
        <p className="text-xs uppercase tracking-[0.2em] text-dim">Control plane</p>
        <h1 className="text-xl font-medium">Kick Bot Farm — infrastructure</h1>
      </div>
      <nav className="flex gap-2">
        {links.map((l) => (
          <Link
            key={l.href}
            href={l.href}
            className={`rounded-full px-3 py-1.5 text-sm ${
              path === l.href ? "bg-white text-black" : "text-dim hover:text-white"
            }`}
          >
            {l.label}
          </Link>
        ))}
      </nav>
    </header>
  );
}
