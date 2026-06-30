# Filepath: core/post/charts_fx/matrices/correlation_matrix.py
# Condensed Description: Animated correlation matrix â€” specialized heatmap for correlation
#   coefficients (-1 to +1), diverging colormap centered at zero, auto-annotation.
# Architecture Layer: Post-Production
# Environment: Both

from __future__ import annotations
import numpy as np

from chart_fx.base import ChartEffect, ChartParams, ChartData

__all__ = ["CorrelationMatrixEffect"]


class CorrelationMatrixEffect(ChartEffect):
    """Animated correlation matrix â€” diverging heatmap for -1 to +1 values.

    Data: self.data.matrix (n Ã— n ndarray of correlation coefficients)

    chart_params:
        colormap: str (default "RdBu_r")
        annotate: bool (default True)
        mask_upper: bool (default False) â€” hide upper triangle
        circle_mode: bool (default False) â€” show circles instead of squares
    """
    name = "correlation_matrix"
    description = "Animated correlation matrix heatmap"
    category = "matrix"

    def render_frame(self, frame_idx: int, phase: str, progress: float) -> np.ndarray:
        import matplotlib.pyplot as plt
        from matplotlib.colors import Normalize
        import matplotlib.patches as mpatches

        fig, ax = self._create_figure()

        matrix = self.data.matrix
        if matrix is None or matrix.size == 0:
            return self._fig_to_rgba(fig)

        n = matrix.shape[0]
        cmap = self.params.chart_params.get("colormap", "RdBu_r")
        annotate = self.params.chart_params.get("annotate", True)
        mask_upper = self.params.chart_params.get("mask_upper", False)
        circle_mode = self.params.chart_params.get("circle_mode", False)

        opacity = progress if phase != "hold" else 1.0
        labels = self.data.row_labels or [f"Var {i+1}" for i in range(n)]
        colormap = plt.cm.get_cmap(cmap)
        norm = Normalize(vmin=-1, vmax=1)

        if circle_mode:
            # Circle-based correlation matrix
            ax.set_xlim(-0.5, n - 0.5)
            ax.set_ylim(-0.5, n - 0.5)
            ax.set_aspect("equal")
            ax.invert_yaxis()

            for r in range(n):
                for c in range(n):
                    if mask_upper and c > r: continue
                    val = matrix[r, c]
                    if np.isnan(val): continue

                    # Animation
                    if phase == "enter":
                        if (r + c) / (2 * n) > progress: continue
                        scale = min(1, progress * 2)
                    else:
                        scale = 1.0

                    radius = abs(val) * 0.45 * scale
                    color = colormap(norm(val))
                    circle = mpatches.Circle((c, r), radius, facecolor=color,
                                             edgecolor="white", linewidth=0.5,
                                             alpha=0.85 * opacity)
                    ax.add_patch(circle)

                    if annotate and scale > 0.5:
                        ax.text(c, r, f"{val:.2f}", ha="center", va="center",
                               fontsize=max(6, self.params.font_size - 6),
                               color="white" if abs(val) > 0.5 else "black",
                               alpha=opacity * 0.9, fontweight="bold")
        else:
            # Standard heatmap
            display = matrix.copy()
            if mask_upper:
                mask = np.triu(np.ones_like(matrix, dtype=bool), k=1)
                display = np.where(mask, np.nan, display)

            if phase == "enter":
                vis = max(1, int(n * progress))
                show = np.full_like(display, np.nan)
                show[:vis, :vis] = display[:vis, :vis]
                display = show

            im = ax.imshow(display, cmap=cmap, vmin=-1, vmax=1,
                           interpolation="nearest", alpha=opacity)

            if annotate and n <= 15:
                for r in range(n):
                    for c in range(n):
                        val = matrix[r, c]
                        if np.isnan(display[r, c]) if phase == "enter" else (mask_upper and c > r):
                            continue
                        ax.text(c, r, f"{val:.2f}", ha="center", va="center",
                               fontsize=max(6, self.params.font_size - 5),
                               color="white" if abs(val) > 0.5 else "black",
                               alpha=opacity * 0.9)

            cbar = fig.colorbar(im, ax=ax, shrink=0.7, pad=0.02)
            cbar.ax.tick_params(colors=self.params.text_color, labelsize=self.params.font_size - 4)
            cbar.set_label("Correlation", color=self.params.text_color,
                          fontsize=self.params.font_size - 2)

        ax.set_xticks(range(n))
        ax.set_xticklabels(labels[:n], rotation=45, ha="right")
        ax.set_yticks(range(n))
        ax.set_yticklabels(labels[:n])
        self._style_ax(ax)
        ax.tick_params(colors=self.params.text_color, labelsize=self.params.font_size - 3)

        return self._apply_opacity(self._fig_to_rgba(fig), opacity)
