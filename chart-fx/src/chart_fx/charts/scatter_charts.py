# Filepath: core/post/charts_fx/charts/scatter_charts.py
# Condensed Description: Animated scatter and bubble chart effects â€” dots appear with
#   fade/grow animation, bubble sizes animate, optional trendlines.
# Architecture Layer: Post-Production
# Environment: Both

from __future__ import annotations
import numpy as np

from chart_fx.base import ChartEffect, ChartParams, ChartData, get_palette, format_number

__all__ = ["ScatterChartEffect", "BubbleChartEffect"]


class ScatterChartEffect(ChartEffect):
    """Animated scatter plot â€” points fade/grow in during enter.

    chart_params:
        marker: str (default "o")
        marker_size: int (default 40)
        show_trend: bool (default False)
        jitter: float (default 0)
    """
    name = "scatter"
    description = "Animated scatter plot"
    category = "chart"

    def render_frame(self, frame_idx: int, phase: str, progress: float) -> np.ndarray:
        import matplotlib.pyplot as plt

        fig, ax = self._create_figure()
        self._style_ax(ax)

        if not self.data.series:
            return self._fig_to_rgba(fig)

        s = self.data.series[0]
        x_vals = np.array(s.x or list(range(len(s.values))), dtype=float)
        y_vals = np.array(s.y or s.values, dtype=float)
        n = len(x_vals)
        ms = self.params.chart_params.get("marker_size", 40)
        marker = self.params.chart_params.get("marker", "o")
        show_trend = self.params.chart_params.get("show_trend", False)
        color = s.color or self._colors[0]
        opacity = progress if phase != "hold" else 1.0

        if phase == "enter":
            n_vis = max(1, int(n * progress))
            sizes = np.full(n_vis, ms * progress)
            ax.scatter(x_vals[:n_vis], y_vals[:n_vis], s=sizes, c=color,
                       marker=marker, alpha=0.7, edgecolors="white", linewidths=0.5, zorder=3)
        else:
            ax.scatter(x_vals, y_vals, s=ms, c=color, marker=marker,
                       alpha=0.7 * opacity, edgecolors="white", linewidths=0.5, zorder=3)
            if show_trend and n >= 2:
                z = np.polyfit(x_vals, y_vals, 1)
                p = np.poly1d(z)
                trend_x = np.linspace(x_vals.min(), x_vals.max(), 100)
                ax.plot(trend_x, p(trend_x), "--", color=color, alpha=0.5 * opacity,
                        linewidth=1.5, zorder=2)

        if s.labels and self.params.show_values and phase != "enter":
            for i, lbl in enumerate(s.labels[:n]):
                ax.annotate(lbl, (x_vals[i], y_vals[i]), fontsize=self.params.font_size - 4,
                           color=self.params.text_color, alpha=opacity * 0.8,
                           xytext=(5, 5), textcoords="offset points")

        return self._apply_opacity(self._fig_to_rgba(fig), opacity)


class BubbleChartEffect(ChartEffect):
    """Animated bubble chart â€” size dimension added to scatter.

    chart_params:
        min_size: float (default 20)
        max_size: float (default 500)
        show_labels: bool (default True)
    """
    name = "bubble"
    description = "Animated bubble chart with size dimension"
    category = "chart"

    def render_frame(self, frame_idx: int, phase: str, progress: float) -> np.ndarray:
        import matplotlib.pyplot as plt

        fig, ax = self._create_figure()
        self._style_ax(ax)

        if not self.data.series:
            return self._fig_to_rgba(fig)

        s = self.data.series[0]
        x_vals = np.array(s.x or list(range(len(s.values))), dtype=float)
        y_vals = np.array(s.y or s.values, dtype=float)
        n = len(x_vals)
        raw_sizes = np.array(s.sizes or [100]*n, dtype=float)
        min_s = self.params.chart_params.get("min_size", 20)
        max_s = self.params.chart_params.get("max_size", 500)
        if raw_sizes.max() > raw_sizes.min():
            sizes = min_s + (raw_sizes - raw_sizes.min()) / (raw_sizes.max() - raw_sizes.min()) * (max_s - min_s)
        else:
            sizes = np.full(n, (min_s + max_s) / 2)

        opacity = progress if phase != "hold" else 1.0
        if phase == "enter":
            sizes = sizes * progress
            n_vis = max(1, int(n * min(1, progress * 1.3)))
        else:
            n_vis = n

        if s.color_values:
            color_vals = np.array(s.color_values[:n_vis], dtype=float)
            scatter = ax.scatter(x_vals[:n_vis], y_vals[:n_vis], s=sizes[:n_vis],
                                c=color_vals, cmap="viridis",
                                alpha=0.7 * opacity, edgecolors="white", linewidths=0.5, zorder=3)
            if phase != "enter":
                cbar = fig.colorbar(scatter, ax=ax, shrink=0.6, pad=0.02)
                cbar.ax.tick_params(colors=self.params.text_color, labelsize=self.params.font_size - 4)
                if self.data.value_label:
                    cbar.set_label(self.data.value_label, color=self.params.text_color,
                                  fontsize=self.params.font_size - 2)
        else:
            colors = get_palette(self.params.palette, n)
            ax.scatter(x_vals[:n_vis], y_vals[:n_vis], s=sizes[:n_vis],
                       c=colors[:n_vis], alpha=0.7 * opacity,
                       edgecolors="white", linewidths=0.5, zorder=3)

        show_labels = self.params.chart_params.get("show_labels", True)
        if show_labels and s.labels and phase != "enter":
            for i, lbl in enumerate(s.labels[:n_vis]):
                ax.annotate(lbl, (x_vals[i], y_vals[i]), fontsize=self.params.font_size - 4,
                           color=self.params.text_color, alpha=opacity * 0.8,
                           ha="center", va="bottom", xytext=(0, 8), textcoords="offset points")

        return self._apply_opacity(self._fig_to_rgba(fig), opacity)
