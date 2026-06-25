import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

// Placeholder shell. The real providers (HeroUI + TanStack Query + Router) and routes
// are wired in Phase 3. Phase 1 ships the offline parsing core (see src/lib/) + tests.
function App() {
  return (
    <main className="mx-auto max-w-3xl p-8">
      <h1 className="text-2xl font-semibold">MultiBrowser</h1>
      <p className="text-default-500">Browse &amp; explore MultiBench traditions.</p>
    </main>
  );
}

const root = document.getElementById("root");
if (root) {
  createRoot(root).render(
    <StrictMode>
      <App />
    </StrictMode>,
  );
}
