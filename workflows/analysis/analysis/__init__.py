"""MultiBench analysis workflow — cross-tradition report / figures / bootstrap CIs.

A port of JaleesBench's report/figure/stats tooling, reframed so the comparison
axis is the **tradition** (subjects nested). Consumes ``workflows/judging`` output
(one ``--results-dir`` per tradition) read-only; emits a self-contained HTML report,
scenario-cluster bootstrap 95% CIs, and optional matplotlib figures.
"""
