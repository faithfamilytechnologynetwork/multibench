import { useMemo } from "react";
import { getRouteApi, Link } from "@tanstack/react-router";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useLatestSha, useScenario, useTradition } from "../lib/queries";
import { taxonomyValues } from "../lib/model";
import { asRateLimit, resetLabel } from "../lib/rateLimit";
import { ScenarioHeader } from "../components/ScenarioHeader";
import { PressureSection } from "../components/PressureSection";
import { ScenarioResponses } from "../components/ScenarioResponses";
import { Collapsible } from "../components/Collapsible";
import { Markdown } from "../components/Markdown";
import { Notices, Notice } from "../components/Notice";
import { RateLimitBanner } from "../components/RateLimitBanner";
import { CenteredSpinner } from "../components/Loading";
import { NotFound } from "./NotFound";

const route = getRouteApi("/t/$traditionId/$scenarioId");

export function ScenarioPage() {
  const { traditionId, scenarioId } = route.useParams();
  const shaQ = useLatestSha();
  const sha = shaQ.data;
  const tradQ = useTradition(sha, traditionId);
  const tradition = tradQ.data;
  const declaredTax = useMemo(
    () => taxonomyValues(tradition?.manifest?.taxonomies ?? {}),
    [tradition],
  );
  const scenarioIds = tradition?.scenarioIds ?? [];
  const scenQ = useScenario(sha, traditionId, scenarioId, declaredTax);
  const scenario = scenQ.data;
  const rl = asRateLimit(shaQ.error) ?? asRateLimit(tradQ.error) ?? asRateLimit(scenQ.error);
  const otherError = !rl && (shaQ.error || tradQ.error || scenQ.error);

  const errorFallback = (what: string) => (
    <div className="flex flex-col gap-4">
      {rl && <RateLimitBanner error={rl} />}
      <Notice
        notice={{
          severity: "error",
          scope: "github",
          where: "GitHub",
          message: rl
            ? `Couldn't load this ${what} — GitHub's rate limit was reached and nothing is cached yet. Live data resumes around ${resetLabel(rl)}.`
            : `Couldn't load this ${what}: ${(otherError as Error).message}`,
        }}
      />
    </div>
  );

  if (!tradition && (rl || otherError)) return errorFallback("scenario");
  if (tradQ.isLoading && !tradition) return <CenteredSpinner label="Loading…" />;
  if (tradition === null) return <NotFound what={`Tradition “${traditionId}”`} />;
  if (tradition && !scenarioIds.includes(scenarioId)) {
    return <NotFound what={`Scenario “${scenarioId}”`} />;
  }
  if (scenQ.isLoading && !scenario) return <CenteredSpinner label="Loading scenario…" />;
  if (!scenario && (rl || otherError)) return errorFallback("scenario");
  if (!scenario || !tradition) return null;

  const idx = scenarioIds.indexOf(scenarioId);
  const prev = idx > 0 ? scenarioIds[idx - 1] : null;
  const next = idx >= 0 && idx < scenarioIds.length - 1 ? scenarioIds[idx + 1] : null;
  const where = `${traditionId}/scenarios/${scenarioId}`;

  const adherent = tradition.manifest?.adherentNoun?.trim() || "person of faith";

  return (
    <>
      {rl && <RateLimitBanner error={rl} />}
      {/* First-visit framing: a newcomer with zero context should grasp, in one sentence, what this
          project measures and what this page shows. Wording derives from the tradition's own vocab
          (adherent noun) + the project's purpose — no new claims. */}
      <header className="mb-5 max-w-3xl" data-testid="page-framing">
        <p className="text-base text-default-700">
          <span className="font-semibold text-default-900">MultiBench</span> measures the spiritual impact of AI
          assistants: when a {adherent} brings a real dilemma and is then <em>pushed</em> to compromise, does
          the assistant hold to the tradition&rsquo;s own guidance?
        </p>
        <p className="mt-1 text-sm text-default-500">
          This page is <strong>one such scenario</strong> — the question &amp; the pushes on the left, and{" "}
          <strong>how each model answered</strong> (with the judges&rsquo; scores) on the right.
        </p>
      </header>
      {/* App-shell (JaleesBrowser layout): a sticky, own-scrolling context sidebar + a main pane for
          the responses. On a desktop viewport the reader sees BOTH at once — context stays at hand
          while a response scrolls. Below 860px it degrades to a single stacked column. */}
      <div className="flex flex-col gap-6 min-[860px]:flex-row min-[860px]:items-start" data-testid="scenario-shell">
        <aside
          data-testid="scenario-sidebar"
          aria-label="Scenario context"
          tabIndex={0}
          className="flex flex-col gap-4 rounded focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary min-[860px]:sticky min-[860px]:top-6 min-[860px]:max-h-[calc(100vh-3rem)] min-[860px]:w-[400px] min-[860px]:shrink-0 min-[860px]:overflow-auto min-[860px]:pr-1"
        >
          <nav className="flex items-center justify-between text-sm">
            <Link to="/t/$traditionId" params={{ traditionId }} className="text-primary hover:underline">
              ← {tradition.manifest?.displayName ?? traditionId}
            </Link>
            <div className="flex items-center gap-3">
              {prev ? (
                <Link to="/t/$traditionId/$scenarioId" params={{ traditionId, scenarioId: prev }}
                  className="flex items-center gap-1 text-default-600 hover:text-default-900">
                  <ChevronLeft size={16} aria-hidden /> {prev}
                </Link>
              ) : (
                <span className="flex items-center gap-1 text-default-300"><ChevronLeft size={16} aria-hidden /> prev</span>
              )}
              {next ? (
                <Link to="/t/$traditionId/$scenarioId" params={{ traditionId, scenarioId: next }}
                  className="flex items-center gap-1 text-default-600 hover:text-default-900">
                  {next} <ChevronRight size={16} aria-hidden />
                </Link>
              ) : (
                <span className="flex items-center gap-1 text-default-300">next <ChevronRight size={16} aria-hidden /></span>
              )}
            </div>
          </nav>

          <ScenarioHeader id={scenarioId} meta={scenario.meta} />
          <Notices notices={scenario.notices} />

          <section className="flex flex-col gap-1">
            <h2 className="text-sm font-semibold text-default-700">The question</h2>
            <p className="text-xs text-default-400">what the {adherent} first asked the assistant</p>
            {scenario.turn1 != null ? (
              <Markdown>{scenario.turn1}</Markdown>
            ) : (
              <Notice notice={{ severity: "error", scope: "section", where: `${where}/turn1.md`, message: "Turn-1 opening is missing or empty." }} />
            )}
          </section>

          <PressureSection pressures={scenario.pressures} where={`${where}/pressures.md`} compact />

          <Collapsible title="What good counsel looks like (the tradition's guidance the judges use)">
            {scenario.judgeGuidance != null ? (
              <Markdown>{scenario.judgeGuidance}</Markdown>
            ) : (
              <Notice notice={{ severity: "error", scope: "section", where: `${where}/judge-guidance.md`, message: "Judge-guidance is missing or empty." }} />
            )}
          </Collapsible>
        </aside>

        <section className="min-w-0 flex-1" data-testid="scenario-main">
          <ScenarioResponses traditionId={traditionId} scenarioId={scenarioId} />
        </section>
      </div>
    </>
  );
}
