import { render } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider, createMemoryHistory } from "@tanstack/react-router";
import { createAppRouter } from "../router";
import { makeQueryClient } from "../lib/queryClient";

/** Render the real app (router + providers) at `path`, with an isolated QueryClient. */
export function renderApp(path = "/") {
  const history = createMemoryHistory({ initialEntries: [path] });
  const router = createAppRouter(history);
  const qc = makeQueryClient();
  const result = render(
    <QueryClientProvider client={qc}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
  return { ...result, router, qc };
}
