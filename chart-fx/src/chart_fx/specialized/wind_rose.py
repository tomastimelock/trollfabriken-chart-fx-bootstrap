# Filepath: core/post/charts_fx/specialized/wind_rose.py
# Condensed Description: Animated wind rose â€” polar stacked bar chart showing frequency
#   distribution of wind speeds across compass directions. Bars grow outward.
# Architecture Layer: Post-Production
# Environment: Both

from __future__ import annotations
import math
import numpy as np

from chart_fx.base import ChartEffect, ChartParams, ChartData, get_palette

__all__ = ["WindRoseEffect"]


class WindRoseEffect(ChartEffect):
    """Animated wind rose â€” polar stacked bar chart.

    Data: series[i] represents a speed bin, series[i].values[j] is frequency for direction j.
    x_categories: compass directions (e.g. ["N","NNE","NE",...])

    chart_params:
        num_sectors: int (default from data or 16)
        bar_alpha: float (default 0.75)
        bar_edge: bool (default True)
        speed_unit: str (default "m/s")
    """
    name = "wind_rose"
    description = "Animated wind rose diagram"
    category = "specialized"

    def render_frame(self, frame_idx: int, phase: str, progress: float) -> np.ndarray:
        import matplotlib.pyplot as plt

        import matplotlib
        matplotlib.use("Agg")
        dpi = 100
        fig = plt.figure(figsize=(self.width/dpi, self.height/dpi), dpi=dpi)
        ax = fig.add_subplot(111, polar=True)
        fig.patch.set_alpha(0)
        ax.set_facecolor("none")

        ns = len(self.data.series)
        if ns == 0: return self._fig_to_rgba(fig)

        # Number of direction sectors
        n_dirs = len(self.data.series[0].values)
        dirs = self.data.x_categories or \
               ["N","NNE","NE","ENE","E","ESE","SE","SSE",
                "S","SSW","SW","WSW","W","WNW","NW","NNW"][:n_dirs]

        # Convert directions to radians (N=0, clockwise)
        theta = np.linspace(0, 2*np.pi, n_dirs, endpoint=False)
        width = 2 * np.pi / n_dirs * 0.85

        opacity = progress if phase != "hold" else 1.0
        bar_alpha = self.params.chart_params.get("bar_alpha", 0.75)
        speed_unit = self.params.chart_params.get("speed_unit", "m/s")

        bottom = np.zeros(n_dirs)

        for si, s in enumerate(self.data.series):
            vals = np.array(s.values[:n_dirs], dtype=float)
            if phase == "enter":
                vals = vals * progress
            color = s.color or self._colors[si]
            ax.bar(theta, vals, width=width, bottom=bottom, color=color,
                   alpha=bar_alpha * opacity, label=s.name,
                   edgecolor="white" if self.params.chart_params.get("bar_edge", True) else "none",
                   linewidth=0.5, zorder=3)
            bottom += vals

        # Configure polar axes
        ax.set_theta_zero_location("N")
        ax.set_theta_direction(-1)  # Clockwise
        ax.set_xticks(theta)
        ax.set_xticklabels(dirs[:n_dirs], color=self.params.text_color,
                           fontsize=self.params.font_size - 2)
        ax.tick_params(colors=self.params.text_color)
        ax.spines["polar"].set_color(self.params.grid_color)
        ax.spines["polar"].set_alpha(0.3)
        ax.yaxis.grid(True, color=self.params.grid_color, alpha=0.2, linestyle="--")

        if self.data.title:
            ax.set_title(self.data.title, color=self.params.text_color,
                        fontsize=self.params.title_size, fontweight="bold", pad=20)

        if self.params.show_legend:
            ax.legend(loc="lower right", bbox_to_anchor=(1.25, -0.05),
                      facecolor="none", edgecolor="none",
                      labelcolor=self.params.text_color, fontsize=self.params.font_size - 3,
                      title=f"Speed ({speed_unit})", title_fontsize=self.params.font_size - 2)

        return self._apply_opacity(self._fig_to_rgba(fig), opacity)
