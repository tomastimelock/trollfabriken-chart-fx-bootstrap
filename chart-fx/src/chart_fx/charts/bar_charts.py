# Filepath: core/post/charts_fx/charts/bar_charts.py
# Condensed Description: Animated bar chart effects â€” standard, stacked, grouped, horizontal.
#   Enter animation grows bars from baseline; hold displays full chart; exit fades out.
# Architecture Layer: Post-Production
# Environment: Both

from __future__ import annotations
from typing import List
import numpy as np
import math

from chart_fx.base import ChartEffect, ChartParams, ChartData, get_easing, get_palette, format_number

__all__ = ["BarChartEffect", "StackedBarEffect", "GroupedBarEffect", "HorizontalBarEffect"]


class BarChartEffect(ChartEffect):
    """Animated vertical bar chart â€” bars grow upward during enter phase.

    chart_params:
        bar_width: float (default 0.6)
        bar_gap: float (default 0.1)
        rounded: bool (default False)
        value_format: str (default "auto")
    """
    name = "bar"
    description = "Animated vertical bar chart"
    category = "chart"

    def render_frame(self, frame_idx: int, phase: str, progress: float) -> np.ndarray:
        import matplotlib.pyplot as plt

        fig, ax = self._create_figure()
        self._style_ax(ax)

        series = self.data.series
        if not series or not series[0].values:
            return self._fig_to_rgba(fig)

        s = series[0]
        n = len(s.values)
        cats = self.data.x_categories or s.labels or [str(i+1) for i in range(n)]
        x = np.arange(n)
        bw = self.params.chart_params.get("bar_width", 0.6)
        colors = get_palette(self.params.palette, n)

        # Animated values
        if phase == "enter":
            anim_vals = [v * progress for v in s.values]
            opacity = min(1.0, progress * 1.5)
        elif phase == "hold":
            anim_vals = list(s.values)
            opacity = 1.0
        else:
            anim_vals = list(s.values)
            opacity = progress

        bars = ax.bar(x, anim_vals, width=bw, color=colors[:n], alpha=opacity * 0.85,
                      edgecolor=[c for c in colors[:n]], linewidth=0.5)

        # Value labels
        if self.params.show_values and phase != "enter":
            for i, (bar, val) in enumerate(zip(bars, s.values)):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(s.values)*0.02,
                        format_number(val), ha="center", va="bottom",
                        color=self.params.text_color, fontsize=self.params.font_size - 2,
                        alpha=opacity)

        ax.set_xticks(x)
        ax.set_xticklabels(cats, rotation=30 if n > 6 else 0, ha="right" if n > 6 else "center")
        ax.set_ylim(0, max(s.values) * 1.15)

        if self.params.show_legend and s.name:
            ax.legend([s.name], loc="upper right", facecolor="none", edgecolor="none",
                      labelcolor=self.params.text_color, fontsize=self.params.font_size - 2)

        frame = self._fig_to_rgba(fig)
        return self._apply_opacity(frame, opacity) if phase == "exit" else frame


class StackedBarEffect(ChartEffect):
    """Animated stacked bar chart â€” layers stack up sequentially."""
    name = "stacked_bar"
    description = "Animated stacked bar chart"
    category = "chart"

    def render_frame(self, frame_idx: int, phase: str, progress: float) -> np.ndarray:
        import matplotlib.pyplot as plt

        fig, ax = self._create_figure()
        self._style_ax(ax)

        if len(self.data.series) < 2:
            return self._fig_to_rgba(fig)

        n = len(self.data.series[0].values)
        cats = self.data.x_categories or [str(i+1) for i in range(n)]
        x = np.arange(n)
        bw = self.params.chart_params.get("bar_width", 0.6)

        opacity = progress if phase != "hold" else 1.0
        bottom = np.zeros(n)

        for si, s in enumerate(self.data.series):
            vals = np.array(s.values[:n], dtype=float)
            # Stagger: each series enters slightly later
            if phase == "enter":
                series_delay = si / max(1, len(self.data.series))
                local_prog = max(0, (progress - series_delay * 0.3) / (1 - series_delay * 0.3))
                vals = vals * local_prog

            color = s.color or self._colors[si]
            ax.bar(x, vals, width=bw, bottom=bottom, color=color, alpha=0.85,
                   label=s.name, edgecolor=color, linewidth=0.3)
            bottom += vals

        ax.set_xticks(x)
        ax.set_xticklabels(cats, rotation=30 if n > 6 else 0, ha="right" if n > 6 else "center")

        if self.params.show_legend:
            ax.legend(loc="upper right", facecolor="none", edgecolor="none",
                      labelcolor=self.params.text_color, fontsize=self.params.font_size - 2)

        return self._apply_opacity(self._fig_to_rgba(fig), opacity)


class GroupedBarEffect(ChartEffect):
    """Animated grouped bar chart â€” groups slide in together."""
    name = "grouped_bar"
    description = "Animated grouped bar chart"
    category = "chart"

    def render_frame(self, frame_idx: int, phase: str, progress: float) -> np.ndarray:
        import matplotlib.pyplot as plt

        fig, ax = self._create_figure()
        self._style_ax(ax)

        ns = len(self.data.series)
        if ns == 0: return self._fig_to_rgba(fig)

        n = len(self.data.series[0].values)
        cats = self.data.x_categories or [str(i+1) for i in range(n)]
        x = np.arange(n)
        total_width = 0.7
        bw = total_width / ns

        opacity = progress if phase != "hold" else 1.0
        max_val = max(max(s.values) for s in self.data.series if s.values)

        for si, s in enumerate(self.data.series):
            offset = -total_width/2 + bw * (si + 0.5)
            vals = np.array(s.values[:n], dtype=float)
            if phase == "enter":
                vals = vals * progress
            color = s.color or self._colors[si]
            ax.bar(x + offset, vals, width=bw * 0.85, color=color, alpha=0.85,
                   label=s.name, edgecolor=color, linewidth=0.3)

        ax.set_xticks(x)
        ax.set_xticklabels(cats)
        ax.set_ylim(0, max_val * 1.15)

        if self.params.show_legend:
            ax.legend(loc="upper right", facecolor="none", edgecolor="none",
                      labelcolor=self.params.text_color, fontsize=self.params.font_size - 2)

        return self._apply_opacity(self._fig_to_rgba(fig), opacity)


class HorizontalBarEffect(ChartEffect):
    """Animated horizontal bar chart â€” bars extend from left."""
    name = "horizontal_bar"
    description = "Animated horizontal bar chart"
    category = "chart"

    def render_frame(self, frame_idx: int, phase: str, progress: float) -> np.ndarray:
        import matplotlib.pyplot as plt

        fig, ax = self._create_figure()
        self._style_ax(ax)

        series = self.data.series
        if not series: return self._fig_to_rgba(fig)
        s = series[0]
        n = len(s.values)
        cats = self.data.x_categories or s.labels or [str(i+1) for i in range(n)]
        y = np.arange(n)
        colors = get_palette(self.params.palette, n)

        opacity = progress if phase != "hold" else 1.0
        vals = [v * progress for v in s.values] if phase == "enter" else list(s.values)

        ax.barh(y, vals, height=0.6, color=colors[:n], alpha=0.85 * opacity)
        ax.set_yticks(y)
        ax.set_yticklabels(cats)
        ax.set_xlim(0, max(s.values) * 1.15)
        ax.invert_yaxis()

        if self.params.show_values:
            for i, val in enumerate(s.values):
                display_val = val * progress if phase == "enter" else val
                ax.text(display_val + max(s.values)*0.02, i,
                        format_number(val), va="center",
                        color=self.params.text_color, fontsize=self.params.font_size - 2,
                        alpha=opacity)

        return self._apply_opacity(self._fig_to_rgba(fig), opacity)
