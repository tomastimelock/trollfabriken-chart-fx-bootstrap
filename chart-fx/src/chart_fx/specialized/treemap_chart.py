# Filepath: core/post/charts_fx/specialized/treemap_chart.py
# Condensed Description: Animated treemap â€” squarified rectangular tiles proportional to
#   values, with labels and color-coding. Tiles grow from center during enter.
# Architecture Layer: Post-Production
# Environment: Both

from __future__ import annotations
import numpy as np

from chart_fx.base import ChartEffect, ChartParams, ChartData, get_palette, format_number

__all__ = ["TreemapEffect"]


def _squarify(values, x, y, w, h):
    """Simple squarified treemap layout. Returns list of (x, y, w, h, value_index)."""
    if not values:
        return []
    if len(values) == 1:
        return [(x, y, w, h, 0)]

    total = sum(values)
    if total <= 0:
        return [(x, y, w, h, i) for i in range(len(values))]

    rects = []
    remaining = list(enumerate(values))
    rx, ry, rw, rh = x, y, w, h

    while remaining:
        if len(remaining) == 1:
            idx, _ = remaining[0]
            rects.append((rx, ry, rw, rh, idx))
            break

        rem_total = sum(v for _, v in remaining)
        is_wide = rw >= rh

        # Take items until aspect ratio worsens
        row = []
        row_total = 0
        for i, (idx, val) in enumerate(remaining):
            row.append((idx, val))
            row_total += val
            if i < len(remaining) - 1:
                frac = row_total / rem_total
                if is_wide:
                    row_w = rw * frac
                    worst_ar = max(
                        max((rh * v / row_total) / row_w, row_w / (rh * v / row_total))
                        for _, v in row if v > 0
                    ) if row_w > 0 else float("inf")
                else:
                    row_h = rh * frac
                    worst_ar = max(
                        max((rw * v / row_total) / row_h, row_h / (rw * v / row_total))
                        for _, v in row if v > 0
                    ) if row_h > 0 else float("inf")
                if worst_ar > 4:
                    break

        # Layout row
        frac = row_total / rem_total if rem_total > 0 else 1
        if is_wide:
            row_w = rw * frac
            cy = ry
            for idx, val in row:
                cell_h = rh * (val / row_total) if row_total > 0 else rh / len(row)
                rects.append((rx, cy, row_w, cell_h, idx))
                cy += cell_h
            rx += row_w
            rw -= row_w
        else:
            row_h = rh * frac
            cx = rx
            for idx, val in row:
                cell_w = rw * (val / row_total) if row_total > 0 else rw / len(row)
                rects.append((cx, ry, cell_w, row_h, idx))
                cx += cell_w
            ry += row_h
            rh -= row_h

        remaining = remaining[len(row):]

    return rects


class TreemapEffect(ChartEffect):
    """Animated treemap â€” proportional rectangles.

    Data: series[0].values = sizes, series[0].labels = tile labels

    chart_params:
        border_width: float (default 2)
        border_color: str (default "white")
        text_threshold: float (default 0.03) â€” min fraction to show text
    """
    name = "treemap"
    description = "Animated proportional treemap"
    category = "specialized"

    def render_frame(self, frame_idx: int, phase: str, progress: float) -> np.ndarray:
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches

        fig, ax = self._create_figure()
        ax.axis("off")

        if not self.data.series or not self.data.series[0].values:
            return self._fig_to_rgba(fig)

        s = self.data.series[0]
        values = list(s.values)
        labels = s.labels or [f"Item {i+1}" for i in range(len(values))]
        n = len(values)
        colors = get_palette(self.params.palette, n)
        total = sum(values)

        border_w = self.params.chart_params.get("border_width", 2)
        border_c = self.params.chart_params.get("border_color", "white")
        text_thresh = self.params.chart_params.get("text_threshold", 0.03)

        opacity = progress if phase != "hold" else 1.0

        # Sort descending for better layout
        sorted_idx = sorted(range(n), key=lambda i: values[i], reverse=True)
        sorted_vals = [values[i] for i in sorted_idx]

        rects = _squarify(sorted_vals, 0, 0, 1, 1)

        for rx, ry, rw, rh, local_i in rects:
            orig_i = sorted_idx[local_i]
            color = colors[orig_i % len(colors)]

            if phase == "enter":
                # Tiles grow from center
                cx_center, cy_center = rx + rw/2, ry + rh/2
                scale = progress
                draw_x = cx_center - rw * scale / 2
                draw_y = cy_center - rh * scale / 2
                draw_w = rw * scale
                draw_h = rh * scale
            else:
                draw_x, draw_y, draw_w, draw_h = rx, ry, rw, rh

            rect = mpatches.FancyBboxPatch(
                (draw_x, draw_y), draw_w, draw_h,
                boxstyle=mpatches.BoxStyle.Round(pad=0.005),
                facecolor=color, edgecolor=border_c, linewidth=border_w,
                alpha=0.85 * opacity, transform=ax.transAxes
            )
            ax.add_patch(rect)

            # Label if tile is large enough
            frac = values[orig_i] / total if total > 0 else 0
            if frac >= text_thresh and (phase != "enter" or progress > 0.5):
                label_text = labels[orig_i]
                value_text = format_number(values[orig_i])
                pct_text = f"({frac*100:.1f}%)"
                tx = draw_x + draw_w / 2
                ty = draw_y + draw_h / 2

                fs = max(7, min(self.params.font_size, int(draw_h * 80)))
                ax.text(tx, ty + draw_h * 0.08, label_text, transform=ax.transAxes,
                       ha="center", va="center", fontsize=fs, fontweight="bold",
                       color="white", alpha=opacity * 0.95)
                ax.text(tx, ty - draw_h * 0.08, f"{value_text} {pct_text}",
                       transform=ax.transAxes, ha="center", va="center",
                       fontsize=max(6, fs - 3), color="white", alpha=opacity * 0.7)

        if self.data.title:
            ax.set_title(self.data.title, color=self.params.text_color,
                        fontsize=self.params.title_size, fontweight="bold", pad=10)

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        return self._apply_opacity(self._fig_to_rgba(fig), opacity)
