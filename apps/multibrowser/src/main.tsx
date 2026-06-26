import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { PersistQueryClientProvider } from "@tanstack/react-query-persist-client";
import { createSyncStoragePersister } from "@tanstack/query-sync-storage-persister";
import { RouterProvider } from "@tanstack/react-router";
import { router } from "./router";
import { queryClient } from "./lib/queryClient";
import { ErrorBoundary } from "./components/ErrorBoundary";
import "./styles.css";

// Persist the (SHA-pinned, immutable) query cache to localStorage so a returning visitor reuses
// it instead of re-fetching — cross-session politeness to GitHub's unauthenticated rate limit.
const persister = createSyncStoragePersister({
  storage: window.localStorage,
  key: "multibrowser-query-cache",
});

const root = document.getElementById("root");
if (root) {
  createRoot(root).render(
    <StrictMode>
      <ErrorBoundary>
        <PersistQueryClientProvider
          client={queryClient}
          persistOptions={{ persister, maxAge: 1000 * 60 * 60 * 24 }}
        >
          <RouterProvider router={router} />
        </PersistQueryClientProvider>
      </ErrorBoundary>
    </StrictMode>,
  );
}
