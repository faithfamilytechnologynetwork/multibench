import { Link, Outlet } from "@tanstack/react-router";
import { Github } from "lucide-react";
import { REF, REPO } from "../lib/constants";
import { useLatestSha } from "../lib/queries";

export function RootLayout() {
  // Point the GitHub link at the CONFIGURED repo and the exact loaded snapshot (the polled SHA),
  // falling back to the configured ref — so the link always matches the source the UI is showing.
  const { data: sha } = useLatestSha();
  const ref = sha ?? REF;
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-default-200">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <Link to="/" className="text-lg font-semibold">
            Multi<span className="text-primary">Browser</span>
          </Link>
          <a
            href={`https://github.com/${REPO}/tree/${ref}/traditions`}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 text-sm text-default-500 hover:text-default-700"
          >
            <Github size={16} aria-hidden /> traditions on GitHub
          </a>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
