"""Numeric diverging color scale — the port of JaleesBench ``band_color`` (spec §4.4).

Keeps the source's seven-stop diverging colormap (deep red → grey-beige → deep
green) and the ``TwoSlopeNorm(vmin=-1, vcenter=0, vmax=1)`` mapping — but on the
**numeric −1…+1 scale with the ×0.5 rescale dropped** (D1) and **no band names
anywhere** (D2). Pure Python (no matplotlib) so the HTML path never imports it.

Because vmin/vmax are symmetric about the center, ``TwoSlopeNorm`` reduces to a
linear map (−1→0, 0→0.5, +1→1); ``score_color`` interpolates the stops at that
position. ``heatmap_color`` applies the source's auto-contrast norm
``TwoSlopeNorm(-vmax, 0, vmax)`` for the steadfastness heatmap.
"""

from __future__ import annotations

# The seven diverging stops (identical to make_figures.py's BAND_CMAP), evenly spaced.
_STOPS: tuple[str, ...] = (
    "#9E1B32", "#D6604D", "#F4A582", "#D9D2C5", "#A6D49A", "#5AAE61", "#1B7837",
)

# Reference lines on the numeric axis (the port of band_axis, spec §4.4): dashed grey
# at the ±0.5 marks, solid grey at neutral 0. No band-name labels.
MINOR_REFS: tuple[float, ...] = (-0.5, 0.5)
ZERO_REF: float = 0.0


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    return int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02X}{g:02X}{b:02X}"


def _interp(t: float) -> str:
    """Interpolate the diverging stops at ``t`` ∈ [0, 1] (clamped)."""
    t = min(1.0, max(0.0, t))
    n = len(_STOPS) - 1
    x = t * n
    i = min(int(x), n - 1)
    f = x - i
    a = _hex_to_rgb(_STOPS[i])
    b = _hex_to_rgb(_STOPS[i + 1])
    return _rgb_to_hex(*(round(a[k] + (b[k] - a[k]) * f) for k in range(3)))


def score_color(value: float) -> str:
    """Diverging color for a score on −1…+1 (TwoSlopeNorm(−1, 0, 1); linear here)."""
    return _interp((value + 1.0) / 2.0)


def heatmap_color(value: float, vmax: float) -> str:
    """Auto-contrast diverging color: TwoSlopeNorm(−vmax, 0, vmax) (source Fig 3/6/7)."""
    if vmax <= 0:
        return _interp(0.5)  # all-zero matrix → neutral centre
    return _interp((value / vmax + 1.0) / 2.0)


def on_color(value: float, vmax: float) -> str:
    """Readable label color over a heatmap cell (source: dark text on faint cells)."""
    return "#111111" if abs(value) < 0.33 * vmax else "#FFFFFF"
