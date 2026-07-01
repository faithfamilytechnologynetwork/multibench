"""End-to-end pipeline: ``collect → judge → report`` for one tradition (spec §5.10 / S1).

Runs the three stages in order against a single results directory, threading the collector's
``sittings.jsonl`` into the judge and the judge's ``judgments.jsonl`` into the report. The
provider seams (``subject_fn`` / ``judge_fn``) are injectable, so the whole pipeline is
testable end-to-end with mocked models (no live API). ``report`` always runs last (it never
hard-fails, M12), so partial results + coverage are written even when some cells failed;
``failed`` in the returned summary drives the CLI's non-zero exit.
"""

from __future__ import annotations

from pathlib import Path

from judging.collect import SubjectFn, collect
from judging.config import Config, default_config
from judging.judge import JudgeFn, judge_all
from judging.report import write_report


def run_pipeline(
    tradition_dir: str | Path,
    results_dir: str | Path,
    config: Config | None = None,
    subject_fn: SubjectFn | None = None,
    judge_fn: JudgeFn | None = None,
    limit: int | None = None,
) -> dict:
    """Collect, judge, then report for ``tradition_dir`` into ``results_dir``.

    Returns ``{"collect", "judge", "report", "failed"}``. ``failed`` is the sum of collect and
    judge failed cells; ``> 0`` means the caller should exit non-zero (failed cells are left
    pending and are resumable, M12). All three stages share one ``config`` so the grid, panel,
    and scopes are consistent across collection, judging, and reporting.
    """
    config = config or default_config()
    rd = Path(results_dir)

    collected = collect(tradition_dir, rd, config=config, subject_fn=subject_fn, limit=limit)
    judged = judge_all(
        rd / "sittings.jsonl", tradition_dir, rd, config=config, judge_fn=judge_fn
    )
    reported = write_report(rd, tradition_dir, config)

    return {
        "collect": collected,
        "judge": judged,
        "report": reported,
        "failed": collected["failed"] + judged["failed"],
    }
