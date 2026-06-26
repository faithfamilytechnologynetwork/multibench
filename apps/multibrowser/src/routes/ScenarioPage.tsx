import { useMemo } from "react";
import { getRouteApi, Link } from "@tanstack/react-router";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useLatestSha, useScenario, useTradition } from "../lib/queries";
import { taxonomyValues } from "../lib/model";
import { asRateLimit, resetLabel } from "../lib/rateLimit";
import { ScenarioHeader } from "../components/ScenarioHeader";
import { PressureSection } from "../components/PressureSection";
import { FramingsPanel } from "../components/FramingsPanel";
import { ResultsRegion } from "../components/ResultsRegion";
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

  return (
    <div className="flex flex-col gap-6">
      {rl && <RateLimitBanner error={rl} />}

      <nav className="flex items-center justify-between text-sm">
        <Link to="/t/$traditionId" params={{ traditionId }} className="text-primary hover:underline">
          ← {tradition.manifest?.displayName ?? traditionId}
        </Link>
        <div className="flex items-center gap-3">
          {prev ? (
            <Link
              to="/t/$traditionId/$scenarioId"
              params={{ traditionId, scenarioId: prev }}
              className="flex items-center gap-1 text-default-600 hover:text-default-900"
            >
              <ChevronLeft size={16} aria-hidden /> {prev}
            </Link>
          ) : (
            <span className="flex items-center gap-1 text-default-300">
              <ChevronLeft size={16} aria-hidden /> prev
            </span>
          )}
          {next ? (
            <Link
              to="/t/$traditionId/$scenarioId"
              params={{ traditionId, scenarioId: next }}
              className="flex items-center gap-1 text-default-600 hover:text-default-900"
            >
              {next} <ChevronRight size={16} aria-hidden />
            </Link>
          ) : (
            <span className="flex items-center gap-1 text-default-300">
              next <ChevronRight size={16} aria-hidden />
            </span>
          )}
        </div>
      </nav>

      <ScenarioHeader id={scenarioId} meta={scenario.meta} />
      <Notices notices={scenario.notices} />

      <section className="flex flex-col gap-2">
        <h2 className="text-lg font-semibold">Turn 1 — the opening</h2>
        {scenario.turn1 != null ? (
          <Markdown>{scenario.turn1}</Markdown>
        ) : (
          <Notice notice={{ severity: "error", scope: "section", where: `${where}/turn1.md`, message: "Turn-1 opening is missing or empty." }} />
        )}
      </section>

      <PressureSection pressures={scenario.pressures} where={`${where}/pressures.md`} />

      <Collapsible title="Judge guidance — the binding ground truth">
        {scenario.judgeGuidance != null ? (
          <Markdown>{scenario.judgeGuidance}</Markdown>
        ) : (
          <Notice notice={{ severity: "error", scope: "section", where: `${where}/judge-guidance.md`, message: "Judge-guidance is missing or empty." }} />
        )}
      </Collapsible>

      <ResultsRegion scenario={scenario} />

      <FramingsPanel adherentNoun={tradition.manifest?.adherentNoun ?? ""} guide={tradition.prose.guide} />
    </div>
  );
}
