# Filepath: core/post/charts_fx/charts/line_charts.py
# Condensed Description: Animated line/area chart effects â€” line draws progressively,
#   area fills up, multi-line staggers entry, sparkline is minimal.
# Architecture Layer: Post-Production
# Environment: Both

from __future__ import annotations
import numpy as np

from chart_fx.base import ChartEffect, ChartParams, ChartData, get_palette

__all__ = ["LineChartEffect", "AreaChartEffect", "MultiLineEffect", "SparklineEffect"]


class LineChartEffect(ChartEffect):
    """Animated line chart â€” line draws from left to right.

    chart_params:
        line_width: float (default 2.5)
        marker: str (default "o")
        marker_size: int (default 5)
        smooth: bool (default False) â€” cubic interpolation
    """
    name = "line"
    description = "Animated line chart drawn left to right"
    category = "chart"

    def render_frame(self, frame_idx: int, phase: str, progress: float) -> np.ndarray:
        import matplotlib.pyplot as plt

        fig, ax = self._create_figure()
        self._style_ax(ax)

        if not self.data.series: return self._fig_to_rgba(fig)
        s = self.data.series[0]
        n = len(s.values)
        cats = self.data.x_categories or s.labels or [str(i+1) for i in range(n)]
        x = np.arange(n)
        lw = self.params.chart_params.get("line_width", 2.5)
        marker = self.params.chart_params.get("marker", "o")
        ms = self.params.chart_params.get("marker_size", 5)
        color = s.color or self._colors[0]
        opacity = progress if phase != "hold" else 1.0

        if phase == "enter":
            # Draw progressively â€” show first n_visible points
            n_vis = max(2, int(n * progress))
            ax.plot(x[:n_vis], s.values[:n_vis], color=color, linewidth=lw,
                    marker=marker, markersize=ms, alpha=0.9, zorder=3)
        else:
            ax.plot(x, s.values, color=color, linewidth=lw,
                    marker=marker, markersize=ms, alpha=0.9 * opacity, zorder=3)

        ax.set_xticks(x)
        ax.set_xticklabels(cats, rotation=30 if n > 8 else 0,
                           ha="right" if n > 8 else "center")
        ax.set_ylim(min(s.values) * 0.9, max(s.values) * 1.1)

        return self._apply_opacity(self._fig_to_rgba(fig), opacity)


class AreaChartEffect(ChartEffect):
    """Animated area chart â€” fill rises from baseline."""
    name = "area"
    description = "Animated area chart with rising fill"
    category = "chart"

    def render_frame(self, frame_idx: int, phase: str, progress: float) -> np.ndarray:
        import matplotlib.pyplot as plt

        fig, ax = self._create_figure()
        self._style_ax(ax)

        if not self.data.series: return self._fig_to_rgba(fig)
        opacity = progress if phase != "hold" else 1.0

        for si, s in enumerate(self.data.series):
            n = len(s.values)
            x = np.arange(n)
            vals = np.array(s.values, dtype=float)
            if phase == "enter":
                vals = vals * progress
            color = s.color or self._colors[si]
            ax.fill_between(x, vals, alpha=0.35 * opacity, color=color, zorder=2)
            ax.plot(x, vals, color=color, linewidth=2, alpha=0.9 * opacity, zorder=3,
                    label=s.name)

        cats = self.data.x_categories or [str(i+1) for i in range(n)]
        ax.set_xticks(np.arange(n))
        ax.set_xticklabels(cats, rotation=30 if n > 8 else 0,
                           ha="right" if n > 8 else "center")

        if self.params.show_legend and len(self.data.series) > 1:
            ax.legend(loc="upper left", facecolor="none", edgecolor="none",
                      labelcolor=self.params.text_color, fontsize=self.params.font_size - 2)

        return self._apply_opacity(self._fig_to_rgba(fig), opacity)


class MultiLineEffect(ChartEffect):
    """Animated multi-line chart â€” each line draws in with stagger."""
    name = "multi_line"
    description = "Multiple animated lines with staggered entry"
    category = "chart"

    def render_frame(self, frame_idx: int, phase: str, progress: float) -> np.ndarray:
        import matplotlib.pyplot as plt

        fig, ax = self._create_figure()
        self._style_ax(ax)

        ns = len(self.data.series)
        if ns == 0: return self._fig_to_rgba(fig)

        n = len(self.data.series[0].values)
        x = np.arange(n)
        cats = self.data.x_categories or [str(i+1) for i in range(n)]
        opacity = progress if phase != "hold" else 1.0

        for si, s in enumerate(self.data.series):
            color = s.color or self._colors[si]
            if phase == "enter":
                delay = si / max(1, ns) * 0.3
                local = max(0, min(1, (progress - delay) / (1 - delay * 0.5)))
                n_vis = max(2, int(n * local))
                ax.plot(x[:n_vis], s.values[:n_vis], color=color, linewidth=2.5,
                        marker="o", markersize=4, alpha=0.9, label=s.name, zorder=3)
            else:
                ax.plot(x, s.values, color=color, linewidth=2.5,
                        marker="o", markersize=4, alpha=0.9 * opacity,
                        label=s.name, zorder=3)

        ax.set_xticks(x)
        ax.set_xticklabels(cats, rotation=30 if n > 8 else 0,
                           ha="right" if n > 8 else "center")

        if self.params.show_legend:
            ax.legend(loc="upper left", facecolor="none", edgecolor="none",
                      labelcolor=self.params.text_color, fontsize=self.params.font_size - 2)

        return self._apply_opacity(self._fig_to_rgba(fig), opacity)


class SparklineEffect(ChartEffect):
    """Minimal sparkline â€” no axes, just the line with optional fill."""
    name = "sparkline"
    description = "Minimal sparkline without axes"
    category = "chart"

    def render_frame(self, frame_idx: int, phase: str, progress: float) -> np.ndarray:
        import matplotlib.pyplot as plt

        fig, ax = self._create_figure()
        ax.axis("off")
        fig.subplots_adjust(left=0.02, right=0.98, top=0.9, bottom=0.15)

        if not self.data.series: return self._fig_to_rgba(fig)
        s = self.data.series[0]
        n = len(s.values)
        x = np.arange(n)
        color = s.color or self._colors[0]
        opacity = progress if phase != "hold" else 1.0

        n_vis = max(2, int(n * progress)) if phase == "enter" else n
        ax.plot(x[:n_vis], s.values[:n_vis], color=color, linewidth=3, alpha=0.9 * opacity)
        ax.fill_between(x[:n_vis], s.values[:n_vis], alpha=0.15 * opacity, color=color)

        # Highlight last point
        if n_vis > 0:
            ax.plot(x[n_vis-1], s.values[n_vis-1], "o", color=color,
                    markersize=8, alpha=opacity, zorder=5)

        if self.data.title:
            ax.set_title(self.data.title, color=self.params.text_color,
                        fontsize=self.params.title_size, fontweight="bold", loc="left")

        return self._apply_opacity(self._fig_to_rgba(fig), opacity)
