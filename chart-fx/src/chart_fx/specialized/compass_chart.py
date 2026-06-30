# Filepath: core/post/charts_fx/specialized/compass_chart.py
# Condensed Description: Animated compass display â€” navigational compass with needle
#   that sweeps to target heading. Cardinal/intercardinal markers, degree ring.
# Architecture Layer: Post-Production
# Environment: Both

from __future__ import annotations
import math
import numpy as np

from chart_fx.base import ChartEffect, ChartParams, ChartData

__all__ = ["CompassChartEffect"]


class CompassChartEffect(ChartEffect):
    """Animated compass â€” needle sweeps to target heading.

    Data: series[0].values[0] = heading in degrees (0-360, 0=N, 90=E)

    chart_params:
        needle_color: str (default "#ff3366")
        ring_color: str (default "#00aaff")
        show_degrees: bool (default True)
        style: str â€” "modern" | "classic" (default "modern")
    """
    name = "compass"
    description = "Animated compass with sweeping needle"
    category = "specialized"

    def render_frame(self, frame_idx: int, phase: str, progress: float) -> np.ndarray:
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches

        fig, ax = self._create_figure()
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(-1.2, 1.2)

        if not self.data.series or not self.data.series[0].values:
            return self._fig_to_rgba(fig)

        heading = self.data.series[0].values[0] % 360
        needle_color = self.params.chart_params.get("needle_color", "#ff3366")
        ring_color = self.params.chart_params.get("ring_color", "#00aaff")
        show_degrees = self.params.chart_params.get("show_degrees", True)
        opacity = progress if phase != "hold" else 1.0

        # Outer ring
        ring = mpatches.Circle((0, 0), 1.0, facecolor="none",
                                edgecolor=ring_color, linewidth=2.5,
                                alpha=0.8 * opacity)
        ax.add_patch(ring)

        # Inner ring
        inner_ring = mpatches.Circle((0, 0), 0.85, facecolor="none",
                                      edgecolor=self.params.grid_color, linewidth=0.5,
                                      alpha=0.4 * opacity)
        ax.add_patch(inner_ring)

        # Cardinal directions
        cardinals = {"N": 90, "E": 0, "S": 270, "W": 180}
        intercardinals = {"NE": 45, "SE": 315, "SW": 225, "NW": 135}

        for label, angle_deg in cardinals.items():
            angle = math.radians(angle_deg)
            r_text = 0.93
            ax.text(r_text * math.cos(angle), r_text * math.sin(angle), label,
                   ha="center", va="center", fontsize=self.params.title_size,
                   fontweight="bold", color=self.params.text_color, alpha=opacity)

        for label, angle_deg in intercardinals.items():
            angle = math.radians(angle_deg)
            r_text = 0.93
            ax.text(r_text * math.cos(angle), r_text * math.sin(angle), label,
                   ha="center", va="center", fontsize=self.params.font_size - 2,
                   color=self.params.text_color, alpha=opacity * 0.6)

        # Degree tick marks
        if show_degrees:
            for deg in range(0, 360, 10):
                angle = math.radians(90 - deg)  # Convert compass to math
                is_major = deg % 30 == 0
                r_inner = 0.78 if is_major else 0.82
                r_outer = 0.85
                ax.plot([r_inner * math.cos(angle), r_outer * math.cos(angle)],
                       [r_inner * math.sin(angle), r_outer * math.sin(angle)],
                       color=self.params.text_color, linewidth=1.5 if is_major else 0.5,
                       alpha=0.6 * opacity)

                if is_major and deg % 90 != 0:
                    r_label = 0.72
                    ax.text(r_label * math.cos(angle), r_label * math.sin(angle),
                           f"{deg}Â°", ha="center", va="center",
                           fontsize=self.params.font_size - 5,
                           color=self.params.text_color, alpha=opacity * 0.5)

        # Needle â€” sweeps from 0 to target heading
        if phase == "enter":
            current_heading = heading * progress
        else:
            current_heading = heading

        needle_angle = math.radians(90 - current_heading)  # Compass to math
        needle_len = 0.65

        # Needle triangle (forward)
        nx = needle_len * math.cos(needle_angle)
        ny = needle_len * math.sin(needle_angle)
        # Tail
        tail_len = 0.2
        tx = tail_len * math.cos(needle_angle + math.pi)
        ty = tail_len * math.sin(needle_angle + math.pi)
        # Width
        perp = needle_angle + math.pi/2
        hw = 0.04
        # Forward triangle (red)
        tri_x = [nx, hw*math.cos(perp), -hw*math.cos(perp)]
        tri_y = [ny, hw*math.sin(perp), -hw*math.sin(perp)]
        ax.fill(tri_x, tri_y, color=needle_color, alpha=0.9 * opacity, zorder=5)
        # Tail triangle (white/gray)
        tri_bx = [tx, hw*math.cos(perp), -hw*math.cos(perp)]
        tri_by = [ty, hw*math.sin(perp), -hw*math.sin(perp)]
        ax.fill(tri_bx, tri_by, color=self.params.text_color, alpha=0.5 * opacity, zorder=5)

        # Center dot
        center = mpatches.Circle((0, 0), 0.035, facecolor=needle_color,
                                  edgecolor="white", linewidth=1.5,
                                  alpha=opacity, zorder=6)
        ax.add_patch(center)

        # Heading display
        ax.text(0, -1.1, f"{current_heading:.0f}Â°", ha="center", va="center",
               fontsize=self.params.title_size + 4, fontweight="bold",
               color=self.params.text_color, alpha=opacity)

        if self.data.title:
            ax.text(0, 1.15, self.data.title, ha="center", va="center",
                   fontsize=self.params.title_size, fontweight="bold",
                   color=self.params.text_color, alpha=opacity)

        return self._apply_opacity(self._fig_to_rgba(fig), opacity)
