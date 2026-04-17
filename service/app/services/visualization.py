from __future__ import annotations

from io import StringIO

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

from .kde_stats import compute_sample_statistics


def _build_legend_label(label: str, values: np.ndarray, clip_zero: bool) -> str:
    sample_stats = compute_sample_statistics(values, clip_zero=clip_zero)
    return (
        f"{label} | "
        f"μ={sample_stats.mean:.2f}, "
        f"σ={sample_stats.std:.2f}, "
        f"CV={sample_stats.cv:.2f}, "
        f"Skew={sample_stats.skew:.2f}, "
        f"Kurt={sample_stats.kurtosis:.2f}, "
        f"Median={sample_stats.median:.2f}, "
        f"Peak={sample_stats.kde_peak:.2f}"
    )


def render_kde_plot_svg(
    samples: dict[str, np.ndarray],
    attribute: str,
    clip_zero: bool = False,
    title: str | None = None,
) -> str:
    if not samples:
        raise ValueError("samples must not be empty")

    figure, axis = plt.subplots(figsize=(10, 6))
    colors = plt.cm.tab10(np.linspace(0, 1, len(samples)))

    for color, (label, values) in zip(colors, samples.items()):
        array = np.asarray(values, dtype=float)
        lower = max(0.0, float(array.min())) if clip_zero else float(array.min())
        upper = float(array.max())
        if lower == upper:
            axis.axvline(lower, color=color, linewidth=2, label=_build_legend_label(label, array, clip_zero))
            continue

        grid = np.linspace(lower, upper, 1024)
        kde = stats.gaussian_kde(array, bw_method="scott")
        axis.plot(
            grid,
            kde(grid),
            color=color,
            linewidth=2,
            label=_build_legend_label(label, array, clip_zero),
        )

    axis.set_title(title or f"KDE Plot of {attribute}")
    axis.set_xlabel(attribute)
    axis.set_ylabel("Density")
    axis.grid(True, which="both", axis="both", linestyle="--", linewidth=0.5)
    if clip_zero:
        axis.set_xlim(left=0)
    axis.legend(fontsize="small", loc="upper right")
    figure.tight_layout()

    buffer = StringIO()
    figure.savefig(buffer, format="svg")
    plt.close(figure)
    return buffer.getvalue()


def build_kde_plot_html(
    svg_content: str,
    attribute: str,
    comment_text: str = "",
    extra_html: str = "",
) -> str:
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>KDE Plot</title></head>
<body>
<h2>KDE Plot: {attribute}</h2>
{svg_content}
<p style="font-family: sans-serif; font-size: 14px; color: #333;">{comment_text}</p>
{extra_html}
</body>
</html>"""
