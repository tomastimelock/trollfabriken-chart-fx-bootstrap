# G4e â€” Financial/Flow chart effects: Candlestick, Funnel, Sankey

import numpy as np

from chart_fx.base import ChartEffect, get_palette, format_number


class CandlestickEffect(ChartEffect):
    """OHLC candlestick chart with animated bar-by-bar reveal."""

    name = "candlestick"
    description = "OHLC candlestick chart with animated bar-by-bar build"
    category = "specialized"

    def render_frame(self, frame_idx: int, phase: str, progress: float) -> np.ndarray:
        import matplotlib

        matplotlib.use("Agg")
        from matplotlib.patches import Rectangle

        fig, ax = self._create_figure()
        tc = self.params.text_color

        # Expect series with values as [open, high, low, close, ...] interleaved
        # or separate series named open/high/low/close
        series_map = {s.name.lower(): s.values for s in self.data.series}
        opens = series_map.get("open", [10, 11, 10.5, 12, 11.5, 13, 12])
        highs = series_map.get("high", [12, 12, 11.5, 13, 13, 14, 13])
        lows = series_map.get("low", [9, 10, 9.5, 11, 11, 12, 11])
        closes = series_map.get("close", [11, 10.5, 11, 12.5, 12, 13.5, 12.5])
        n = min(len(opens), len(highs), len(lows), len(closes))
        labels = self.data.x_categories or [str(i + 1) for i in range(n)]

        # Animate: reveal bars progressively during enter, full during hold
        if phase == "enter":
            n_show = max(1, int(progress * n))
        else:
            n_show = n

        up_color = self.params.chart_params.get("up_color", "#26a69a")
        dn_color = self.params.chart_params.get("down_color", "#ef5350")
        bar_width = self.params.chart_params.get("bar_width", 0.6)

        for i in range(min(n_show, n)):
            o, h, lo, c = opens[i], highs[i], lows[i], closes[i]
            color = up_color if c >= o else dn_color
            # Wick
            ax.plot([i, i], [lo, h], color=color, linewidth=1.2, alpha=0.9)
            # Body
            body_h = abs(c - o) or 0.01
            body_y = min(o, c)
            rect = Rectangle(
                (i - bar_width / 2, body_y),
                bar_width,
                body_h,
                facecolor=color,
                edgecolor=color,
                alpha=0.9,
            )
            ax.add_patch(rect)

        ax.set_xlim(-0.5, n - 0.5)
        ax.set_xticks(range(n))
        ax.set_xticklabels(
            labels[:n], color=tc, fontsize=max(8, self.params.font_size - 2)
        )
        self._style_ax(ax)

        opacity = (
            progress if phase == "enter" else (progress if phase == "exit" else 1.0)
        )
        return self._apply_opacity(
            self._fig_to_rgba(fig), opacity * self.params.opacity
        )


class FunnelEffect(ChartEffect):
    """Marketing funnel chart with animated stage reveal from top."""

    name = "funnel"
    description = "Funnel chart showing conversion stages with animated reveal"
    category = "specialized"

    def render_frame(self, frame_idx: int, phase: str, progress: float) -> np.ndarray:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = self._create_figure()
        tc = self.params.text_color

        if not self.data.series:
            ax.text(
                0.5,
                0.5,
                "No data",
                color=tc,
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            return self._fig_to_rgba(fig)

        series = self.data.series[0]
        values = series.values or [100, 75, 50, 30, 15]
        stages = (
            self.data.x_categories
            or series.labels
            or [f"Stage {i+1}" for i in range(len(values))]
        )
        n = len(values)
        colors = get_palette(self.params.palette, n)

        if phase == "enter":
            n_show = max(1, int(progress * n))
        else:
            n_show = n

        max_val = max(values) if values else 1
        height = 0.9 / max(n, 1)

        for i in range(min(n_show, n)):
            w = values[i] / max_val
            alpha_i = (
                1.0
                if phase != "enter" or i < n_show - 1
                else min(1.0, max(0.0, progress * n - (n_show - 1)))
            )
            y = 1.0 - height * (i + 1)
            rect = plt.Rectangle(
                ((1 - w) / 2, y),
                w,
                height * 0.85,
                facecolor=colors[i % len(colors)],
                alpha=float(alpha_i) * 0.85,
            )
            ax.add_patch(rect)
            if self.params.show_values:
                ax.text(
                    0.5,
                    y + height * 0.42,
                    f"{stages[i]}: {format_number(values[i])}",
                    color=tc,
                    ha="center",
                    va="center",
                    fontsize=self.params.font_size,
                    fontweight="bold",
                    transform=ax.transAxes,
                )

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        if self.data.title:
            ax.set_title(
                self.data.title,
                color=tc,
                fontsize=self.params.title_size,
                fontweight="bold",
                pad=8,
            )

        opacity = (
            progress if phase == "enter" else (progress if phase == "exit" else 1.0)
        )
        return self._apply_opacity(
            self._fig_to_rgba(fig), opacity * self.params.opacity
        )


class SankeyEffect(ChartEffect):
    """Simplified Sankey flow diagram â€” source â†’ target with animated flow reveal."""

    name = "sankey"
    description = "Sankey flow diagram with animated flow reveal"
    category = "specialized"

    def render_frame(self, frame_idx: int, phase: str, progress: float) -> np.ndarray:
        import matplotlib

        matplotlib.use("Agg")

        fig, ax = self._create_figure()
        tc = self.params.text_color

        # Data format: series[i] = {name: "Aâ†’B", values: [flow_width]}
        # Build node/link list from series names "Sourceâ†’Target"
        links = []
        for s in self.data.series:
            if "â†’" in s.name or "->" in s.name:
                sep = "â†’" if "â†’" in s.name else "->"
                src, tgt = s.name.split(sep, 1)
                val = s.values[0] if s.values else 1.0
                links.append((src.strip(), tgt.strip(), val))

        if not links:
            links = [("A", "B", 50), ("A", "C", 30), ("B", "D", 40), ("C", "D", 25)]

        # Assign x positions: sources on left, targets on right
        sources = list(dict.fromkeys(lnk[0] for lnk in links))
        targets = list(dict.fromkeys(lnk[1] for lnk in links if lnk[1] not in sources))
        nodes = {
            n: (0.15, 0.1 + 0.8 * i / max(len(sources) - 1, 1))
            for i, n in enumerate(sources)
        }
        for i, n in enumerate(targets):
            nodes[n] = (0.85, 0.1 + 0.8 * i / max(len(targets) - 1, 1))

        colors = get_palette(self.params.palette, len(links))
        n_show = max(1, int(progress * len(links))) if phase == "enter" else len(links)

        for i, (src, tgt, val) in enumerate(links[:n_show]):
            if src not in nodes or tgt not in nodes:
                continue
            sx, sy = nodes[src]
            tx, ty = nodes[tgt]
            lw = max(1.0, min(20.0, val / 5.0))
            alpha_i = (
                1.0
                if phase != "enter" or i < n_show - 1
                else min(1.0, max(0.0, progress * len(links) - (n_show - 1)))
            )
            ax.annotate(
                "",
                xy=(tx, ty),
                xytext=(sx, sy),
                xycoords="axes fraction",
                textcoords="axes fraction",
                arrowprops=dict(
                    arrowstyle="-|>",
                    lw=lw,
                    color=colors[i % len(colors)],
                    alpha=float(alpha_i) * 0.8,
                    connectionstyle="arc3,rad=0.15",
                ),
            )

        # Draw node labels
        for n_name, (nx, ny) in nodes.items():
            ax.text(
                nx,
                ny,
                n_name,
                color=tc,
                ha="center",
                va="center",
                fontsize=self.params.font_size,
                fontweight="bold",
                transform=ax.transAxes,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="#333333", alpha=0.7),
            )

        ax.axis("off")
        if self.data.title:
            ax.set_title(
                self.data.title,
                color=tc,
                fontsize=self.params.title_size,
                fontweight="bold",
            )

        opacity = (
            progress if phase == "enter" else (progress if phase == "exit" else 1.0)
        )
        return self._apply_opacity(
            self._fig_to_rgba(fig), opacity * self.params.opacity
        )
