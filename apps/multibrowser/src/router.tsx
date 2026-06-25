import {
  createRootRoute,
  createRoute,
  createRouter,
  type RouterHistory,
} from "@tanstack/react-router";
import { RootLayout } from "./routes/RootLayout";
import { IndexPage } from "./routes/IndexPage";
import { TraditionPage } from "./routes/TraditionPage";
import { ScenarioPage } from "./routes/ScenarioPage";
import { NotFound } from "./routes/NotFound";
import { parseSearch, stringifySearch } from "./lib/searchParams";
import type { SearchRecord } from "./lib/filtering";

// Code-based routing (deliberate, documented deviation from the plan's "file-based" choice):
// avoids the router-plugin codegen step, keeps the route tree explicit, and is fully unit-
// testable with a memory history. Same library, same deep-linkable URLs.

const rootRoute = createRootRoute({
  component: RootLayout,
  notFoundComponent: () => <NotFound />,
});

const indexRoute = createRoute({ getParentRoute: () => rootRoute, path: "/", component: IndexPage });

export const traditionRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/t/$traditionId",
  component: TraditionPage,
  // Filters live in the URL. Axis values are data-dependent, so we accept the flat record and
  // interpret it against the manifest's axes in the page (fail-soft).
  validateSearch: (search: Record<string, unknown>): SearchRecord => search as SearchRecord,
});

export const scenarioRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/t/$traditionId/$scenarioId",
  component: ScenarioPage,
});

const routeTree = rootRoute.addChildren([indexRoute, traditionRoute, scenarioRoute]);

export function createAppRouter(history?: RouterHistory) {
  return createRouter({
    routeTree,
    defaultNotFoundComponent: () => <NotFound />,
    parseSearch,
    stringifySearch,
    ...(history ? { history } : {}),
  });
}

export const router = createAppRouter();

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}
