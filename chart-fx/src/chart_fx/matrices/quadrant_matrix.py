# Filepath: core/post/charts_fx/matrices/quadrant_matrix.py
# Condensed Description: Animated quadrant matrix â€” 2Ã—2 strategic quadrant with dots
#   positioned by X/Y values, sized by a third dimension, colored by category or value.
#   Quadrant labels, crosshair lines, legend. Dots animate into position.
# Architecture Layer: Post-Production
# Environment: Both

from __future__ import annotations
import math
import numpy as np

from chart_fx.base import ChartEffect, ChartParams, ChartData, get_palette, format_number

__all__ = ["QuadrantMatrixEffect"]


class QuadrantMatrixEffect(ChartEffect):
    """Animated quadrant/matrix chart (BCG-style, Gartner MQ, etc).

    Dots positioned on X/Y axes, sized by 3rd variable, colored by category.
    Quadrant dividers drawn at midpoints (or custom thresholds).

    chart_params:
        x_threshold: float (default mid) â€” vertical divider
        y_threshold: float (default mid) â€” horizontal divider
        quadrant_labels: list[str] â€” 4 labels [top-left, top-right, bottom-left, bottom-right]
        quadrant_colors: list[str] â€” 4 background tints
        min_dot_size: float (default 30)
        max_dot_size: float (default 400)
        show_labels: bool (default True)
        animate_mode: str â€” "fly_in" | "grow" | "fade" (default "fly_in")
    """
    name = "quadrant_matrix"
    description = "Animated strategic quadrant matrix"
    category = "matrix"

    def render_frame(self, frame_idx: int, phase: str, progress: float) -> np.ndarray:
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches

        fig, ax = self._create_figure()
        self._style_ax(ax)

        if not self.data.series:
            return self._fig_to_rgba(fig)

        s = self.data.series[0]
        x_vals = np.array(s.x or list(range(len(s.values))), dtype=float)
        y_vals = np.array(s.y or s.values, dtype=float)
        n = len(x_vals)

        # Size mapping
        raw_sizes = np.array(s.sizes or [100]*n, dtype=float)
        min_s = self.params.chart_params.get("min_dot_size", 30)
        max_s = self.params.chart_params.get("max_dot_size", 400)
        if raw_sizes.max() > raw_sizes.min():
            sizes = min_s + (raw_sizes - raw_sizes.min()) / (raw_sizes.max() - raw_sizes.min()) * (max_s - min_s)
        else:
            sizes = np.full(n, (min_s + max_s) / 2)

        labels = s.labels or [f"Item {i+1}" for i in range(n)]
        colors = get_palette(self.params.palette, n)

        # Thresholds
        x_thresh = self.params.chart_params.get("x_threshold", (x_vals.min() + x_vals.max()) / 2)
        y_thresh = self.params.chart_params.get("y_threshold", (y_vals.min() + y_vals.max()) / 2)

        # Quadrant labels & background tints
        q_labels = self.params.chart_params.get("quadrant_labels",
                   ["Stars", "Question Marks", "Cash Cows", "Dogs"])
        q_colors = self.params.chart_params.get("quadrant_colors",
                   ["#4caf5020", "#ff980020", "#2196f320", "#f4433620"])

        opacity = progress if phase != "hold" else 1.0
        x_margin = (x_vals.max() - x_vals.min()) * 0.15 or 1
        y_margin = (y_vals.max() - y_vals.min()) * 0.15 or 1
        x_min, x_max = x_vals.min() - x_margin, x_vals.max() + x_margin
        y_min, y_max = y_vals.min() - y_margin, y_vals.max() + y_margin

        # Quadrant background shading
        for qi, (x0, x1, y0, y1) in enumerate([
            (x_min, x_thresh, y_thresh, y_max),   # Top-left
            (x_thresh, x_max, y_thresh, y_max),   # Top-right
            (x_min, x_thresh, y_min, y_thresh),    # Bottom-left
            (x_thresh, x_max, y_min, y_thresh),    # Bottom-right
        ]):
            rect = mpatches.Rectangle((x0, y0), x1-x0, y1-y0,
                                       facecolor=q_colors[qi] if len(q_colors) > qi else "#ffffff10",
                                       edgecolor="none", alpha=0.3 * opacity, zorder=0)
            ax.add_patch(rect)
            # Quadrant label
            if qi < len(q_labels):
                lx = (x0 + x1) / 2
                ly = (y0 + y1) / 2
                ax.text(lx, ly, q_labels[qi], ha="center", va="center",
                       fontsize=self.params.font_size + 2, fontweight="bold",
                       color=self.params.text_color, alpha=0.15 * opacity, zorder=1)

        # Crosshair lines
        ax.axvline(x=x_thresh, color=self.params.grid_color, linewidth=1.5,
                   linestyle="--", alpha=0.5 * opacity, zorder=2)
        ax.axhline(y=y_thresh, color=self.params.grid_color, linewidth=1.5,
                   linestyle="--", alpha=0.5 * opacity, zorder=2)

        # Dots â€” animation
        anim_mode = self.params.chart_params.get("animate_mode", "fly_in")

        for i in range(n):
            if phase == "enter":
                if anim_mode == "fly_in":
                    # Dots fly from center outward
                    cx = x_thresh + (x_vals[i] - x_thresh) * progress
                    cy = y_thresh + (y_vals[i] - y_thresh) * progress
                    ds = sizes[i] * progress
                elif anim_mode == "grow":
                    cx, cy = x_vals[i], y_vals[i]
                    ds = sizes[i] * progress
                else:  # fade
                    cx, cy = x_vals[i], y_vals[i]
                    ds = sizes[i]
            else:
                cx, cy = x_vals[i], y_vals[i]
                ds = sizes[i]

            ax.scatter([cx], [cy], s=[ds], c=[colors[i % len(colors)]],
                       alpha=0.75 * opacity, edgecolors="white", linewidths=1, zorder=4)

            # Labels
            show_labels = self.params.chart_params.get("show_labels", True)
            if show_labels and phase != "enter":
                ax.annotate(labels[i], (cx, cy), fontsize=self.params.font_size - 4,
                           color=self.params.text_color, alpha=opacity * 0.85,
                           ha="center", va="bottom", xytext=(0, 8),
                           textcoords="offset points", zorder=5)

        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)

        return self._apply_opacity(self._fig_to_rgba(fig), opacity)
