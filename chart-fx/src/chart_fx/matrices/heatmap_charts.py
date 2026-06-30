# Filepath: core/post/charts_fx/matrices/heatmap_charts.py
# Condensed Description: Animated heatmaps â€” standard 2D heatmap (rows Ã— cols) and
#   hour-year heatmap (365 days Ã— 24 hours) for displaying annual hourly data like
#   energy consumption, temperature, or traffic. Reveal animation wipes across.
# Architecture Layer: Post-Production
# Environment: Both

from __future__ import annotations
import math
import numpy as np

from chart_fx.base import ChartEffect, ChartParams, ChartData, get_palette, format_number

__all__ = ["HeatmapEffect", "HourYearHeatmapEffect"]


class HeatmapEffect(ChartEffect):
    """Animated heatmap â€” cells appear with wipe or fade animation.

    Data source: self.data.matrix (np.ndarray), self.data.row_labels, self.data.col_labels

    chart_params:
        colormap: str (default "viridis")
        vmin/vmax: float (auto by default)
        annotate: bool (default False) â€” show values in cells
        cell_border: bool (default True)
    """
    name = "heatmap"
    description = "Animated 2D heatmap"
    category = "matrix"

    def render_frame(self, frame_idx: int, phase: str, progress: float) -> np.ndarray:
        import matplotlib.pyplot as plt
        from matplotlib.colors import Normalize

        fig, ax = self._create_figure()

        matrix = self.data.matrix
        if matrix is None or matrix.size == 0:
            return self._fig_to_rgba(fig)

        cmap = self.params.chart_params.get("colormap", "viridis")
        vmin = self.params.chart_params.get("vmin", float(np.nanmin(matrix)))
        vmax = self.params.chart_params.get("vmax", float(np.nanmax(matrix)))
        annotate = self.params.chart_params.get("annotate", False)
        cell_border = self.params.chart_params.get("cell_border", True)

        opacity = progress if phase != "hold" else 1.0
        rows, cols = matrix.shape

        if phase == "enter":
            # Wipe reveal â€” mask columns beyond progress
            vis_cols = max(1, int(cols * progress))
            display = np.full_like(matrix, np.nan)
            display[:, :vis_cols] = matrix[:, :vis_cols]
        else:
            display = matrix

        im = ax.imshow(display, aspect="auto", cmap=cmap, vmin=vmin, vmax=vmax,
                        interpolation="nearest", alpha=opacity)

        # Colorbar
        cbar = fig.colorbar(im, ax=ax, shrink=0.75, pad=0.02)
        cbar.ax.tick_params(colors=self.params.text_color, labelsize=self.params.font_size - 4)
        if self.data.value_label:
            cbar.set_label(self.data.value_label, color=self.params.text_color,
                          fontsize=self.params.font_size - 2)

        # Labels
        if self.data.row_labels:
            ax.set_yticks(range(rows))
            ax.set_yticklabels(self.data.row_labels[:rows])
        if self.data.col_labels:
            step = max(1, cols // 12)
            ticks = list(range(0, cols, step))
            ax.set_xticks(ticks)
            ax.set_xticklabels([self.data.col_labels[t] for t in ticks if t < len(self.data.col_labels)],
                               rotation=45, ha="right")

        # Cell annotations
        if annotate and phase != "enter" and rows * cols <= 100:
            for r in range(rows):
                for c in range(cols):
                    val = matrix[r, c]
                    text_c = "white" if val > (vmin + vmax) / 2 else "black"
                    ax.text(c, r, format_number(val), ha="center", va="center",
                           fontsize=max(6, self.params.font_size - 6), color=text_c,
                           alpha=opacity * 0.9)

        # Grid lines
        if cell_border:
            ax.set_xticks(np.arange(-0.5, cols, 1), minor=True)
            ax.set_yticks(np.arange(-0.5, rows, 1), minor=True)
            ax.grid(which="minor", color=self.params.grid_color, linewidth=0.3, alpha=0.3)
            ax.tick_params(which="minor", length=0)

        self._style_ax(ax)
        ax.tick_params(colors=self.params.text_color, labelsize=self.params.font_size - 3)

        return self._apply_opacity(self._fig_to_rgba(fig), opacity)


class HourYearHeatmapEffect(ChartEffect):
    """Annual hour-of-year heatmap â€” 365 columns (days) Ã— 24 rows (hours).

    Perfect for: energy consumption, temperature, server load, traffic, solar radiation.
    Color encodes the metric value; x-axis shows months, y-axis shows hours 0-23.

    Data: self.data.matrix should be (24, 365) ndarray.

    chart_params:
        colormap: str (default "RdYlBu_r" for temperature, "YlOrRd" for energy)
        vmin/vmax: float (auto)
        month_lines: bool (default True) â€” vertical lines at month boundaries
        show_colorbar: bool (default True)
    """
    name = "hour_year_heatmap"
    description = "Annual hourly heatmap (365Ã—24)"
    category = "matrix"

    MONTH_STARTS = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

    def render_frame(self, frame_idx: int, phase: str, progress: float) -> np.ndarray:
        import matplotlib.pyplot as plt
        from matplotlib.colors import Normalize

        fig, ax = self._create_figure()

        matrix = self.data.matrix
        if matrix is None or matrix.size == 0:
            return self._fig_to_rgba(fig)

        # Ensure (24, 365) shape
        if matrix.shape[0] != 24 and matrix.shape[1] == 24:
            matrix = matrix.T

        hours, days = matrix.shape
        cmap = self.params.chart_params.get("colormap", "RdYlBu_r")
        vmin = self.params.chart_params.get("vmin", float(np.nanmin(matrix)))
        vmax = self.params.chart_params.get("vmax", float(np.nanmax(matrix)))
        month_lines = self.params.chart_params.get("month_lines", True)

        opacity = progress if phase != "hold" else 1.0

        # Animation: wipe from left (day 0) to right (day 365)
        if phase == "enter":
            vis_days = max(1, int(days * progress))
            display = np.full_like(matrix, np.nan)
            display[:, :vis_days] = matrix[:, :vis_days]
        else:
            display = matrix

        im = ax.imshow(display, aspect="auto", cmap=cmap, vmin=vmin, vmax=vmax,
                        interpolation="nearest", origin="lower", alpha=opacity)

        # Y-axis: hours
        hour_ticks = list(range(0, 24, 3))
        ax.set_yticks(hour_ticks)
        ax.set_yticklabels([f"{h:02d}:00" for h in hour_ticks])

        # X-axis: months
        month_mids = [(self.MONTH_STARTS[i] + (self.MONTH_STARTS[i+1] if i+1 < 12 else days)) // 2
                      for i in range(12)]
        ax.set_xticks(month_mids)
        ax.set_xticklabels(self.MONTH_NAMES)

        # Month boundary lines
        if month_lines:
            for ms in self.MONTH_STARTS[1:]:
                ax.axvline(x=ms - 0.5, color=self.params.text_color, linewidth=0.5,
                          alpha=0.3 * opacity, linestyle=":")

        # Colorbar
        if self.params.chart_params.get("show_colorbar", True):
            cbar = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.02, orientation="vertical")
            cbar.ax.tick_params(colors=self.params.text_color, labelsize=self.params.font_size - 4)
            label = self.data.value_label or self.data.unit or ""
            if label:
                cbar.set_label(label, color=self.params.text_color,
                              fontsize=self.params.font_size - 2)

        self._style_ax(ax)
        ax.tick_params(colors=self.params.text_color, labelsize=self.params.font_size - 3)
        ax.set_ylabel("Hour of Day", color=self.params.text_color, fontsize=self.params.font_size)
        ax.set_xlabel("Month", color=self.params.text_color, fontsize=self.params.font_size)

        return self._apply_opacity(self._fig_to_rgba(fig), opacity)
