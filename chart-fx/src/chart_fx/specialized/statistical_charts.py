# G4e â€” Statistical chart effects: Boxplot, Violin

import numpy as np

from chart_fx.base import ChartEffect, get_palette


class BoxplotEffect(ChartEffect):
    """Animated box-and-whisker plot with per-group reveal."""

    name = "boxplot"
    description = "Box-and-whisker plot with animated group-by-group reveal"
    category = "specialized"

    def render_frame(self, frame_idx: int, phase: str, progress: float) -> np.ndarray:
        import matplotlib

        matplotlib.use("Agg")

        fig, ax = self._create_figure()
        tc = self.params.text_color
        colors = get_palette(self.params.palette, max(1, len(self.data.series)))

        groups = []
        labels = []
        for s in self.data.series:
            if s.values:
                groups.append(s.values)
                labels.append(s.name or s.labels[0] if s.labels else "")

        if not groups:
            groups = [
                np.random.normal(0, 1, 50).tolist(),
                np.random.normal(1, 1.5, 50).tolist(),
                np.random.normal(2, 0.8, 50).tolist(),
            ]
            labels = ["Group A", "Group B", "Group C"]

        n = len(groups)
        n_show = max(1, int(progress * n)) if phase == "enter" else n

        bp = ax.boxplot(groups[:n_show], patch_artist=True, notch=False, widths=0.5)
        for i, patch in enumerate(bp["boxes"]):
            patch.set_facecolor(colors[i % len(colors)])
            patch.set_alpha(0.75)
        for element in ["whiskers", "caps", "medians", "fliers"]:
            for item in bp[element]:
                item.set_color(tc)
                item.set_alpha(0.8)

        ax.set_xticklabels(labels[:n_show], color=tc, fontsize=self.params.font_size)
        self._style_ax(ax)

        opacity = (
            progress if phase == "enter" else (progress if phase == "exit" else 1.0)
        )
        return self._apply_opacity(
            self._fig_to_rgba(fig), opacity * self.params.opacity
        )


class ViolinEffect(ChartEffect):
    """Animated violin plot â€” distribution shapes sweep in from the centre axis."""

    name = "violin"
    description = "Violin plot showing distribution shapes with animated reveal"
    category = "specialized"

    def render_frame(self, frame_idx: int, phase: str, progress: float) -> np.ndarray:
        import matplotlib

        matplotlib.use("Agg")

        fig, ax = self._create_figure()
        tc = self.params.text_color
        colors = get_palette(self.params.palette, max(1, len(self.data.series)))

        groups = []
        labels = []
        for s in self.data.series:
            if s.values and len(s.values) >= 4:
                groups.append(s.values)
                labels.append(s.name or "")

        if not groups:
            rng = np.random.RandomState(42)
            groups = [
                rng.normal(0, 1, 80).tolist(),
                rng.normal(1, 1.2, 80).tolist(),
                rng.normal(-0.5, 0.7, 80).tolist(),
            ]
            labels = ["Dist A", "Dist B", "Dist C"]

        n = len(groups)
        n_show = max(1, int(progress * n)) if phase == "enter" else n
        show_groups = groups[:n_show]

        parts = ax.violinplot(
            show_groups,
            positions=list(range(1, n_show + 1)),
            showmedians=True,
            showextrema=True,
        )

        # Colour each violin
        for i, body in enumerate(parts.get("bodies", [])):
            body.set_facecolor(colors[i % len(colors)])
            body.set_alpha(0.7 * (progress if phase == "enter" else 1.0))
            body.set_edgecolor(tc)
            body.set_linewidth(0.8)

        for key in ("cmedians", "cmaxes", "cmins", "cbars"):
            if key in parts:
                parts[key].set_color(tc)
                parts[key].set_linewidth(1.2)
                parts[key].set_alpha(0.9)

        ax.set_xticks(range(1, n_show + 1))
        ax.set_xticklabels(labels[:n_show], color=tc, fontsize=self.params.font_size)
        self._style_ax(ax)

        opacity = (
            progress if phase == "enter" else (progress if phase == "exit" else 1.0)
        )
        return self._apply_opacity(
            self._fig_to_rgba(fig), opacity * self.params.opacity
        )
