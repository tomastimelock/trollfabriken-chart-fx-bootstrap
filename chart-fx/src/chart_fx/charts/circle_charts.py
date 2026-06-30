# Filepath: core/post/charts_fx/charts/circle_charts.py
# Condensed Description: Animated circular chart effects â€” pie (wedges grow), donut (ring fills),
#   gauge (needle sweeps). All use polar/patch-based matplotlib rendering.
# Architecture Layer: Post-Production
# Environment: Both

from __future__ import annotations
import math
import numpy as np

from chart_fx.base import ChartEffect, ChartParams, ChartData, get_palette, hex_to_rgba, format_number

__all__ = ["PieChartEffect", "DonutChartEffect", "GaugeChartEffect"]


class PieChartEffect(ChartEffect):
    """Animated pie chart â€” wedges sweep open during enter phase.

    chart_params:
        explode: list[float] â€” explode distance per wedge (default none)
        start_angle: float (default 90)
        shadow: bool (default False)
    """
    name = "pie"
    description = "Animated pie chart with sweeping wedges"
    category = "chart"

    def render_frame(self, frame_idx: int, phase: str, progress: float) -> np.ndarray:
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches

        fig, ax = self._create_figure()
        ax.set_aspect("equal")
        ax.axis("off")

        if not self.data.series or not self.data.series[0].values:
            return self._fig_to_rgba(fig)

        s = self.data.series[0]
        values = np.array(s.values, dtype=float)
        total = values.sum()
        if total == 0:
            return self._fig_to_rgba(fig)

        labels = s.labels or [f"Item {i+1}" for i in range(len(values))]
        n = len(values)
        colors = get_palette(self.params.palette, n)
        start_angle = self.params.chart_params.get("start_angle", 90)
        explode = self.params.chart_params.get("explode", None)

        opacity = progress if phase != "hold" else 1.0

        if phase == "enter":
            sweep_angle = 360 * progress
            fracs = values / total
            cum_angle = start_angle
            for i, frac in enumerate(fracs):
                wedge_deg = frac * 360
                visible_deg = min(wedge_deg, max(0, sweep_angle - (cum_angle - start_angle)))
                if visible_deg <= 0:
                    cum_angle += wedge_deg
                    continue
                dx, dy = 0, 0
                if explode and i < len(explode):
                    mid_angle = math.radians(cum_angle + visible_deg / 2)
                    dx = explode[i] * math.cos(mid_angle) * 0.05
                    dy = explode[i] * math.sin(mid_angle) * 0.05

                wedge = mpatches.Wedge(
                    center=(0.5 + dx, 0.5 + dy), r=0.38,
                    theta1=cum_angle, theta2=cum_angle + visible_deg,
                    facecolor=colors[i], edgecolor="white", linewidth=1.5,
                    alpha=0.85, transform=ax.transAxes
                )
                ax.add_patch(wedge)
                cum_angle += wedge_deg
        else:
            wedges, _ = ax.pie(
                values, labels=None, colors=colors[:n],
                startangle=start_angle, explode=explode,
                wedgeprops=dict(edgecolor="white", linewidth=1.5, alpha=0.85 * opacity),
            )
            if self.params.show_legend:
                legend_handles = [mpatches.Patch(color=colors[i],
                    label=f"{labels[i]}: {format_number(values[i])}")
                    for i in range(n)]
                ax.legend(handles=legend_handles, loc="center left", bbox_to_anchor=(1, 0.5),
                          facecolor="none", edgecolor="none",
                          labelcolor=self.params.text_color, fontsize=self.params.font_size - 2)

        if self.data.title:
            ax.set_title(self.data.title, color=self.params.text_color,
                        fontsize=self.params.title_size, fontweight="bold", pad=20)

        return self._apply_opacity(self._fig_to_rgba(fig), opacity)


class DonutChartEffect(ChartEffect):
    """Animated donut chart â€” ring fills clockwise with center label.

    chart_params:
        inner_radius: float (default 0.55)
        center_label: str (default "Total")
    """
    name = "donut"
    description = "Animated donut chart with center label"
    category = "chart"

    def render_frame(self, frame_idx: int, phase: str, progress: float) -> np.ndarray:
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches

        fig, ax = self._create_figure()
        ax.set_aspect("equal")
        ax.axis("off")

        if not self.data.series or not self.data.series[0].values:
            return self._fig_to_rgba(fig)

        s = self.data.series[0]
        values = np.array(s.values, dtype=float)
        total = values.sum()
        labels = s.labels or [f"Item {i+1}" for i in range(len(values))]
        n = len(values)
        colors = get_palette(self.params.palette, n)
        inner_r = self.params.chart_params.get("inner_radius", 0.55)
        center_label = self.params.chart_params.get("center_label", "Total")

        opacity = progress if phase != "hold" else 1.0

        if phase == "enter":
            sweep = 360 * progress
            fracs = values / total
            cum = 90
            for i, frac in enumerate(fracs):
                wedge_deg = frac * 360
                visible = min(wedge_deg, max(0, sweep - (cum - 90)))
                if visible <= 0:
                    cum += wedge_deg
                    continue
                outer_w = mpatches.Wedge((0.5, 0.5), 0.38, cum, cum + visible,
                                         width=0.38 * (1 - inner_r),
                                         facecolor=colors[i], edgecolor="white",
                                         linewidth=1.5, alpha=0.85, transform=ax.transAxes)
                ax.add_patch(outer_w)
                cum += wedge_deg
        else:
            wedges, _ = ax.pie(values, colors=colors[:n], startangle=90,
                               wedgeprops=dict(width=1-inner_r, edgecolor="white",
                                               linewidth=1.5, alpha=0.85 * opacity))

        # Center text
        center_val = format_number(total) if center_label == "Total" else center_label
        ax.text(0.5, 0.52, center_val, transform=ax.transAxes,
                ha="center", va="center", fontsize=self.params.title_size + 4,
                fontweight="bold", color=self.params.text_color, alpha=opacity)
        ax.text(0.5, 0.44, center_label, transform=ax.transAxes,
                ha="center", va="center", fontsize=self.params.font_size,
                color=self.params.text_color, alpha=opacity * 0.7)

        if self.data.title:
            ax.set_title(self.data.title, color=self.params.text_color,
                        fontsize=self.params.title_size, fontweight="bold", pad=20)

        if self.params.show_legend and phase != "enter":
            handles = [mpatches.Patch(color=colors[i],
                       label=f"{labels[i]}: {format_number(values[i])}")
                       for i in range(n)]
            ax.legend(handles=handles, loc="center left", bbox_to_anchor=(1, 0.5),
                      facecolor="none", edgecolor="none",
                      labelcolor=self.params.text_color, fontsize=self.params.font_size - 2)

        return self._apply_opacity(self._fig_to_rgba(fig), opacity)


class GaugeChartEffect(ChartEffect):
    """Animated gauge/speedometer â€” needle sweeps to value.

    chart_params:
        min_val: float (default 0)
        max_val: float (default 100)
        zones: list of dicts [{start, end, color}]
        needle_color: str (default "#ff3366")
    """
    name = "gauge"
    description = "Animated gauge/speedometer"
    category = "chart"

    def render_frame(self, frame_idx: int, phase: str, progress: float) -> np.ndarray:
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches

        fig, ax = self._create_figure()
        ax.set_aspect("equal")
        ax.axis("off")

        if not self.data.series or not self.data.series[0].values:
            return self._fig_to_rgba(fig)

        value = self.data.series[0].values[0]
        min_v = self.params.chart_params.get("min_val", 0)
        max_v = self.params.chart_params.get("max_val", 100)
        needle_color = self.params.chart_params.get("needle_color", "#ff3366")
        zones = self.params.chart_params.get("zones", [
            {"start": 0, "end": 33, "color": "#4caf50"},
            {"start": 33, "end": 66, "color": "#ffeb3b"},
            {"start": 66, "end": 100, "color": "#f44336"},
        ])

        opacity = progress if phase != "hold" else 1.0
        angle_range = 180
        cx, cy = 0.5, 0.4

        # Draw zones
        for zone in zones:
            z_start = (zone["start"] - min_v) / (max_v - min_v)
            z_end = (zone["end"] - min_v) / (max_v - min_v)
            theta1 = 180 - z_end * angle_range
            theta2 = 180 - z_start * angle_range
            arc = mpatches.Wedge((cx, cy), 0.35, theta1, theta2, width=0.08,
                                 facecolor=zone["color"], alpha=0.6 * opacity,
                                 transform=ax.transAxes)
            ax.add_patch(arc)

        # Tick marks
        for i in range(11):
            frac = i / 10
            angle = math.radians(180 - frac * angle_range)
            r_outer, r_inner = 0.36, 0.33
            x1 = cx + r_inner * math.cos(angle)
            y1 = cy + r_inner * math.sin(angle)
            x2 = cx + r_outer * math.cos(angle)
            y2 = cy + r_outer * math.sin(angle)
            ax.plot([x1, x2], [y1, y2], color=self.params.text_color, linewidth=1,
                    alpha=opacity * 0.7, transform=ax.transAxes, clip_on=False)
            tick_val = min_v + frac * (max_v - min_v)
            lbl_r = 0.30
            lx = cx + lbl_r * math.cos(angle)
            ly = cy + lbl_r * math.sin(angle)
            ax.text(lx, ly, format_number(tick_val), transform=ax.transAxes,
                    ha="center", va="center", fontsize=self.params.font_size - 4,
                    color=self.params.text_color, alpha=opacity * 0.8)

        # Needle
        norm_val = np.clip((value - min_v) / (max_v - min_v), 0, 1)
        if phase == "enter":
            norm_val *= progress
        needle_angle = math.radians(180 - norm_val * angle_range)
        needle_len = 0.28
        nx = cx + needle_len * math.cos(needle_angle)
        ny = cy + needle_len * math.sin(needle_angle)
        ax.plot([cx, nx], [cy, ny], color=needle_color, linewidth=3,
                solid_capstyle="round", alpha=opacity, transform=ax.transAxes, zorder=5)
        circle = mpatches.Circle((cx, cy), 0.02, facecolor=needle_color,
                                  edgecolor="white", linewidth=1, alpha=opacity,
                                  transform=ax.transAxes, zorder=6)
        ax.add_patch(circle)

        # Value
        display_val = value * progress if phase == "enter" else value
        ax.text(cx, cy - 0.1, format_number(display_val),
                transform=ax.transAxes, ha="center", va="center",
                fontsize=self.params.title_size + 6, fontweight="bold",
                color=self.params.text_color, alpha=opacity)

        if self.data.title:
            ax.set_title(self.data.title, color=self.params.text_color,
                        fontsize=self.params.title_size, fontweight="bold", pad=20, y=0.95)

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        return self._apply_opacity(self._fig_to_rgba(fig), opacity)
