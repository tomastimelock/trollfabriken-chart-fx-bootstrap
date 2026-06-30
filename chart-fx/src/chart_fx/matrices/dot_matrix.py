# Filepath: core/post/charts_fx/matrices/dot_matrix.py
# Condensed Description: Animated dot matrix â€” regular grid of dots whose size and color
#   represent data values. Supports row-sweep, random, and grow-all animations.
# Architecture Layer: Post-Production
# Environment: Both

from __future__ import annotations
import numpy as np

from chart_fx.base import ChartEffect, ChartParams, ChartData, get_palette

__all__ = ["DotMatrixEffect"]


class DotMatrixEffect(ChartEffect):
    """Animated dot matrix â€” grid of circles with size/color encoding.

    Data: self.data.matrix (rows Ã— cols ndarray)

    chart_params:
        min_dot: float (default 10) | max_dot: float (default 200)
        colormap: str (default "viridis")
        animate_mode: "row_sweep" | "random" | "grow_all"
        dot_shape: "o" | "s" | "D" | "^"
    """
    name = "dot_matrix"
    description = "Animated grid of variable-size/color dots"
    category = "matrix"

    def render_frame(self, frame_idx: int, phase: str, progress: float) -> np.ndarray:
        import matplotlib.pyplot as plt
        from matplotlib.colors import Normalize

        fig, ax = self._create_figure()
        self._style_ax(ax)

        matrix = self.data.matrix
        if matrix is None or matrix.size == 0:
            return self._fig_to_rgba(fig)

        rows, cols = matrix.shape
        cmap = self.params.chart_params.get("colormap", "viridis")
        min_d = self.params.chart_params.get("min_dot", 10)
        max_d = self.params.chart_params.get("max_dot", 200)
        anim_mode = self.params.chart_params.get("animate_mode", "row_sweep")
        dot_shape = self.params.chart_params.get("dot_shape", "o")

        opacity = progress if phase != "hold" else 1.0
        vmin, vmax = float(np.nanmin(matrix)), float(np.nanmax(matrix))
        norm = Normalize(vmin=vmin, vmax=vmax)
        size_norm = (matrix - vmin) / max(vmax - vmin, 1e-9)
        sizes = min_d + size_norm * (max_d - min_d)
        colormap = plt.cm.get_cmap(cmap)

        for r in range(rows):
            for c in range(cols):
                val = matrix[r, c]
                if np.isnan(val): continue

                if phase == "enter":
                    if anim_mode == "row_sweep":
                        if r >= max(1, int(rows * progress)): continue
                        scale = progress
                    elif anim_mode == "random":
                        threshold = (r * cols + c) / (rows * cols)
                        if threshold > progress: continue
                        scale = min(1, (progress - threshold) * 3)
                    else:
                        scale = progress
                else:
                    scale = 1.0

                x_pos, y_pos = c, rows - 1 - r
                ax.scatter([x_pos], [y_pos], s=[sizes[r, c] * scale],
                          c=[colormap(norm(val))], marker=dot_shape,
                          alpha=0.8 * opacity, edgecolors="white", linewidths=0.3, zorder=3)

        if self.data.col_labels:
            step = max(1, cols // 10)
            ticks = list(range(0, cols, step))
            ax.set_xticks(ticks)
            ax.set_xticklabels([self.data.col_labels[t] for t in ticks
                                if t < len(self.data.col_labels)], rotation=45, ha="right")
        if self.data.row_labels:
            ax.set_yticks(list(range(rows)))
            ax.set_yticklabels(self.data.row_labels[:rows])

        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=ax, shrink=0.7, pad=0.02)
        cbar.ax.tick_params(colors=self.params.text_color, labelsize=self.params.font_size - 4)
        if self.data.value_label:
            cbar.set_label(self.data.value_label, color=self.params.text_color,
                          fontsize=self.params.font_size - 2)

        ax.set_xlim(-0.5, cols - 0.5)
        ax.set_ylim(-0.5, rows - 0.5)
        ax.set_aspect("equal")
        return self._apply_opacity(self._fig_to_rgba(fig), opacity)
