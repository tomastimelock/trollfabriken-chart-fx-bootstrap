# Filepath: core/post/charts_fx/specialized/waterfall_chart.py
# Condensed Description: Animated waterfall chart â€” floating bars showing incremental
#   changes (positive green, negative red, total blue). Bars cascade in during enter.
# Architecture Layer: Post-Production
# Environment: Both

from __future__ import annotations
import numpy as np

from chart_fx.base import ChartEffect, ChartParams, ChartData, format_number

__all__ = ["WaterfallEffect"]


class WaterfallEffect(ChartEffect):
    """Animated waterfall chart â€” bars cascade from left to right.

    Data: series[0].values = deltas (first value is start, last is final total)
          series[0].labels or x_categories = step labels

    chart_params:
        positive_color: str (default "#4caf50")
        negative_color: str (default "#f44336")
        total_color: str (default "#2196f3")
        connector_lines: bool (default True)
        total_indices: list[int] â€” which bars are totals (default [0, -1])
    """
    name = "waterfall"
    description = "Animated waterfall chart"
    category = "specialized"

    def render_frame(self, frame_idx: int, phase: str, progress: float) -> np.ndarray:
        import matplotlib.pyplot as plt

        fig, ax = self._create_figure()
        self._style_ax(ax)

        if not self.data.series or not self.data.series[0].values:
            return self._fig_to_rgba(fig)

        s = self.data.series[0]
        values = list(s.values)
        n = len(values)
        labels = self.data.x_categories or s.labels or [f"Step {i+1}" for i in range(n)]

        pos_color = self.params.chart_params.get("positive_color", "#4caf50")
        neg_color = self.params.chart_params.get("negative_color", "#f44336")
        total_color = self.params.chart_params.get("total_color", "#2196f3")
        connectors = self.params.chart_params.get("connector_lines", True)
        total_indices = self.params.chart_params.get("total_indices", [0, n-1])
        # Normalize negative indices
        total_indices = [i if i >= 0 else n + i for i in total_indices]

        opacity = progress if phase != "hold" else 1.0

        # Compute cumulative positions
        cumulative = [0.0]
        for i, v in enumerate(values):
            if i in total_indices:
                cumulative.append(v)
            else:
                cumulative.append(cumulative[-1] + v)

        bottoms = []
        heights = []
        colors = []
        for i, v in enumerate(values):
            if i in total_indices:
                bottoms.append(0)
                heights.append(v)
                colors.append(total_color)
            else:
                if v >= 0:
                    bottoms.append(cumulative[i])
                    heights.append(v)
                    colors.append(pos_color)
                else:
                    bottoms.append(cumulative[i] + v)
                    heights.append(abs(v))
                    colors.append(neg_color)

        x = np.arange(n)

        # Animation: bars appear left to right
        if phase == "enter":
            n_vis = max(1, int(n * progress))
        else:
            n_vis = n

        for i in range(n_vis):
            h = heights[i]
            b = bottoms[i]
            if phase == "enter":
                # Each bar grows from its bottom
                bar_progress = min(1, (progress * n - i) / 1) if progress * n > i else 0
                h = h * bar_progress

            ax.bar(x[i], h, bottom=b, width=0.6, color=colors[i],
                   alpha=0.85 * opacity, edgecolor="white", linewidth=0.5, zorder=3)

            # Value label
            if self.params.show_values and (phase != "enter" or bar_progress > 0.8):
                val = values[i]
                sign = "+" if val > 0 and i not in total_indices else ""
                label_y = b + heights[i] + abs(max(values)) * 0.02
                ax.text(x[i], label_y, f"{sign}{format_number(val)}",
                       ha="center", va="bottom", fontsize=self.params.font_size - 3,
                       color=self.params.text_color, alpha=opacity * 0.9, fontweight="bold")

            # Connector line to next bar
            if connectors and i < n_vis - 1 and i not in total_indices:
                top = b + heights[i]
                ax.plot([x[i] + 0.3, x[i+1] - 0.3], [cumulative[i+1], cumulative[i+1]],
                       color=self.params.grid_color, linewidth=1, linestyle="--",
                       alpha=0.4 * opacity, zorder=2)

        ax.set_xticks(x[:n_vis])
        ax.set_xticklabels(labels[:n_vis], rotation=30 if n > 5 else 0,
                           ha="right" if n > 5 else "center")
        ax.axhline(y=0, color=self.params.grid_color, linewidth=0.5, alpha=0.5)

        return self._apply_opacity(self._fig_to_rgba(fig), opacity)
