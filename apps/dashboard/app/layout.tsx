import type { Metadata } from "next";
import "./globals.css";
import { Nav } from "@/components/Nav";

export const metadata: Metadata = {
  title: "Kick Fleet",
  description: "Control plane for authorized Kick browser workers",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" />
      </head>
      <body className="min-h-screen font-sans">
        <Nav />
        <main className="mx-auto max-w-6xl px-8 py-8">{children}</main>
      </body>
    </html>
  );
}
