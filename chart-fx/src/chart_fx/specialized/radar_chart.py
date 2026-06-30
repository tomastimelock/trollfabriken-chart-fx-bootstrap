# Filepath: core/post/charts_fx/specialized/radar_chart.py
# Condensed Description: Animated radar/spider chart â€” polar plot with multiple overlaid
#   series, animated web expansion during enter phase.
# Architecture Layer: Post-Production
# Environment: Both

from __future__ import annotations
import math
import numpy as np

from chart_fx.base import ChartEffect, ChartParams, ChartData, get_palette

__all__ = ["RadarChartEffect"]


class RadarChartEffect(ChartEffect):
    """Animated radar/spider chart.

    Each series forms a polygon on polar axes. Categories are axis spokes.
    Enter animation expands the web from center outward.

    chart_params:
        fill_alpha: float (default 0.15)
        line_width: float (default 2.5)
        marker_size: float (default 6)
        show_rings: bool (default True)
        max_value: float (auto) â€” outer ring value
    """
    name = "radar"
    description = "Animated radar/spider chart"
    category = "specialized"

    def render_frame(self, frame_idx: int, phase: str, progress: float) -> np.ndarray:
        import matplotlib.pyplot as plt

        # Polar figure
        import matplotlib
        matplotlib.use("Agg")
        dpi = 100
        fig = plt.figure(figsize=(self.width/dpi, self.height/dpi), dpi=dpi)
        ax = fig.add_subplot(111, polar=True)
        fig.patch.set_alpha(0)
        ax.set_facecolor("none")

        ns = len(self.data.series)
        if ns == 0: return self._fig_to_rgba(fig)

        cats = self.data.x_categories or self.data.series[0].labels or \
               [f"Axis {i+1}" for i in range(len(self.data.series[0].values))]
        n_cats = len(cats)
        angles = np.linspace(0, 2 * np.pi, n_cats, endpoint=False).tolist()
        angles += angles[:1]  # Close the polygon

        fill_alpha = self.params.chart_params.get("fill_alpha", 0.15)
        lw = self.params.chart_params.get("line_width", 2.5)
        ms = self.params.chart_params.get("marker_size", 6)
        show_rings = self.params.chart_params.get("show_rings", True)
        max_val = self.params.chart_params.get("max_value", None)

        if max_val is None:
            max_val = max(max(s.values) for s in self.data.series if s.values)
        max_val = max(max_val, 1)

        opacity = progress if phase != "hold" else 1.0

        # Ring grid
        if show_rings:
            for ring_frac in [0.25, 0.5, 0.75, 1.0]:
                ring_vals = [max_val * ring_frac] * (n_cats + 1)
                ax.plot(angles, ring_vals, color=self.params.grid_color,
                       linewidth=0.5, alpha=0.3 * opacity, linestyle="--")

        # Series
        for si, s in enumerate(self.data.series):
            vals = list(s.values[:n_cats])
            vals += vals[:1]  # Close polygon
            color = s.color or self._colors[si]

            if phase == "enter":
                # Expand from center
                anim_vals = [v * progress for v in vals]
            else:
                anim_vals = vals

            ax.plot(angles, anim_vals, color=color, linewidth=lw, alpha=0.9 * opacity,
                    label=s.name, zorder=3)
            ax.fill(angles, anim_vals, color=color, alpha=fill_alpha * opacity, zorder=2)
            ax.scatter(angles[:-1], anim_vals[:-1], color=color, s=ms**2,
                      alpha=0.9 * opacity, edgecolors="white", linewidths=0.5, zorder=4)

        # Axes
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(cats, color=self.params.text_color,
                           fontsize=self.params.font_size - 2)
        ax.set_ylim(0, max_val * 1.1)
        ax.set_yticklabels([])
        ax.spines["polar"].set_color(self.params.grid_color)
        ax.spines["polar"].set_alpha(0.3)
        ax.tick_params(colors=self.params.text_color)

        if self.data.title:
            ax.set_title(self.data.title, color=self.params.text_color,
                        fontsize=self.params.title_size, fontweight="bold", pad=20)

        if self.params.show_legend and ns > 1:
            ax.legend(loc="lower right", bbox_to_anchor=(1.2, -0.05),
                      facecolor="none", edgecolor="none",
                      labelcolor=self.params.text_color, fontsize=self.params.font_size - 2)

        return self._apply_opacity(self._fig_to_rgba(fig), opacity)
