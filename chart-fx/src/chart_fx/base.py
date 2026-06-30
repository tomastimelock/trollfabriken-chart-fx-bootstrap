from __future__ import annotations

import math
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np


def _ease_linear(t): return t
def _ease_in_quad(t): return t * t
def _ease_out_quad(t): return t * (2 - t)
def _ease_in_out_quad(t): return 2*t*t if t < 0.5 else -1 + (4 - 2*t)*t
def _ease_in_cubic(t): return t**3
def _ease_out_cubic(t): return (t - 1)**3 + 1
def _ease_in_out_cubic(t): return 4*t**3 if t < 0.5 else (t-1)*(2*t-2)**2 + 1
def _ease_out_elastic(t):
    if t in (0, 1): return t
    return math.pow(2, -10*t) * math.sin((t - 0.075) * (2*math.pi) / 0.3) + 1
def _ease_out_bounce(t):
    if t < 1/2.75: return 7.5625*t*t
    elif t < 2/2.75: t -= 1.5/2.75; return 7.5625*t*t + 0.75
    elif t < 2.5/2.75: t -= 2.25/2.75; return 7.5625*t*t + 0.9375
    else: t -= 2.625/2.75; return 7.5625*t*t + 0.984375

EASING_MAP: Dict[str, Callable] = {
    "linear": _ease_linear, "ease_in": _ease_in_quad, "ease_out": _ease_out_quad,
    "ease_in_out": _ease_in_out_quad, "ease_in_cubic": _ease_in_cubic,
    "ease_out_cubic": _ease_out_cubic, "ease_in_out_cubic": _ease_in_out_cubic,
    "elastic": _ease_out_elastic, "bounce": _ease_out_bounce,
}

def get_easing(name: str) -> Callable:
    return EASING_MAP.get(name, _ease_linear)


PALETTES: Dict[str, List[str]] = {
    "default":     ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f",
                    "#edc948", "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac"],
    "neon":        ["#00ffcc", "#ff00ff", "#00aaff", "#ffaa00", "#ff3366",
                    "#33ff99", "#cc66ff", "#ffcc00", "#00ccff", "#ff6633"],
    "pastel":      ["#aec7e8", "#ffbb78", "#98df8a", "#ff9896", "#c5b0d5",
                    "#c49c94", "#f7b6d2", "#c7c7c7", "#dbdb8d", "#9edae5"],
    "corporate":   ["#003f5c", "#2f4b7c", "#665191", "#a05195", "#d45087",
                    "#f95d6a", "#ff7c43", "#ffa600", "#488f31", "#1a9850"],
    "warm":        ["#fee08b", "#fdae61", "#f46d43", "#d73027", "#a50026",
                    "#ff6b6b", "#ffa07a", "#ffcc5c", "#ff8a65", "#ef5350"],
    "cool":        ["#313695", "#4575b4", "#74add1", "#abd9e9", "#e0f3f8",
                    "#00bcd4", "#0097a7", "#00838f", "#006064", "#004d40"],
    "monochrome":  ["#ffffff", "#e0e0e0", "#bdbdbd", "#9e9e9e", "#757575",
                    "#616161", "#424242", "#303030", "#212121", "#111111"],
    "diverging":   ["#d73027", "#f46d43", "#fdae61", "#fee08b", "#ffffbf",
                    "#d9ef8b", "#a6d96a", "#66bd63", "#1a9850", "#006837"],
    "sequential":  ["#f7fbff", "#deebf7", "#c6dbef", "#9ecae1", "#6baed6",
                    "#4292c6", "#2171b5", "#08519c", "#08306b", "#041f4a"],
}

def get_palette(name: str, n: int = 10) -> List[str]:
    pal = PALETTES.get(name, PALETTES["default"])
    return [pal[i % len(pal)] for i in range(n)]

def hex_to_rgba(h: str) -> Tuple[int, int, int, int]:
    h = h.lstrip("#")
    if len(h) == 6: return (int(h[0:2],16), int(h[2:4],16), int(h[4:6],16), 255)
    if len(h) == 8: return (int(h[0:2],16), int(h[2:4],16), int(h[4:6],16), int(h[6:8],16))
    return (255, 255, 255, 255)

def parse_color(c) -> Tuple[int, int, int, int]:
    if c is None: return (255, 255, 255, 255)
    if isinstance(c, (list, tuple)):
        c = list(c); [c.append(255) for _ in range(4 - len(c))]
        return tuple(c[:4])
    c = str(c).strip().lower()
    names = {"white":(255,255,255,255),"black":(0,0,0,255),"red":(255,0,0,255),
             "green":(0,128,0,255),"blue":(0,0,255,255),"transparent":(0,0,0,0)}
    if c in names: return names[c]
    if c.startswith("#"): return hex_to_rgba(c)
    m = re.match(r"rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)", c)
    if m:
        a = int(float(m.group(4))*255) if m.group(4) else 255
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)), a)
    return (255, 255, 255, 255)

def interpolate_color(c1: str, c2: str, t: float) -> Tuple[int, int, int, int]:
    r1 = hex_to_rgba(c1); r2 = hex_to_rgba(c2)
    return tuple(int(a + (b - a) * t) for a, b in zip(r1, r2))

def format_number(val: float, fmt: str = "auto") -> str:
    if fmt == "auto":
        if abs(val) >= 1_000_000: return f"{val/1_000_000:.1f}M"
        if abs(val) >= 1_000: return f"{val/1_000:.1f}K"
        if abs(val) == int(val): return str(int(val))
        return f"{val:.1f}"
    return f"{val:{fmt}}"


@dataclass
class ChartSeries:
    name: str = ""
    values: List[float] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    color: Optional[str] = None
    x: Optional[List[float]] = None
    y: Optional[List[float]] = None
    sizes: Optional[List[float]] = None
    color_values: Optional[List[float]] = None
    matrix: Optional[List[List[float]]] = None
    row_labels: Optional[List[str]] = None
    col_labels: Optional[List[str]] = None

    @classmethod
    def from_dict(cls, d: Dict) -> "ChartSeries":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class ChartData:
    series: List[ChartSeries] = field(default_factory=list)
    title: str = ""
    subtitle: str = ""
    x_label: str = ""
    y_label: str = ""
    x_categories: List[str] = field(default_factory=list)
    matrix: Optional[np.ndarray] = None
    row_labels: List[str] = field(default_factory=list)
    col_labels: List[str] = field(default_factory=list)
    value_label: str = ""
    source: str = ""
    unit: str = ""

    @classmethod
    def from_dict(cls, d: Dict) -> "ChartData":
        series = [ChartSeries.from_dict(s) for s in d.get("series", [])]
        matrix = np.array(d["matrix"]) if "matrix" in d else None
        return cls(
            series=series, title=d.get("title", ""), subtitle=d.get("subtitle", ""),
            x_label=d.get("x_label", ""), y_label=d.get("y_label", ""),
            x_categories=d.get("x_categories", []), matrix=matrix,
            row_labels=d.get("row_labels", []), col_labels=d.get("col_labels", []),
            value_label=d.get("value_label", ""), source=d.get("source", ""),
            unit=d.get("unit", ""),
        )


@dataclass
class ChartParams:
    chart_type: str = "bar"
    animation_style: str = "build_up"
    data: Optional[Dict] = None
    data_prompt: Optional[str] = None
    enter_duration: float = 1.5
    hold_duration: float = 3.0
    exit_duration: float = 0.5
    enter_easing: str = "ease_out_cubic"
    exit_easing: str = "ease_in_quad"
    palette: str = "default"
    background_color: str = "transparent"
    text_color: str = "#ffffff"
    grid_color: str = "#333333"
    font_size: int = 14
    title_size: int = 20
    show_grid: bool = True
    show_legend: bool = True
    show_values: bool = False
    show_axes: bool = True
    position: str = "center"
    scale: float = 0.85
    opacity: float = 1.0
    padding: float = 0.08
    chart_params: Dict[str, Any] = field(default_factory=dict)
    ai_model: str = "claude-sonnet-4-6"
    ai_temperature: float = 0.5

    @classmethod
    def from_spec(cls, spec: Dict[str, Any]) -> "ChartParams":
        effect = spec.get("effect", {})
        return cls(
            chart_type=spec.get("chart_type", effect.get("type", "bar")),
            animation_style=effect.get("animation_style", "build_up"),
            data=spec.get("data"),
            data_prompt=spec.get("data_prompt"),
            enter_duration=effect.get("enter_duration", 1.5),
            hold_duration=effect.get("hold_duration", 3.0),
            exit_duration=effect.get("exit_duration", 0.5),
            enter_easing=effect.get("enter_easing", "ease_out_cubic"),
            exit_easing=effect.get("exit_easing", "ease_in_quad"),
            palette=spec.get("palette", "default"),
            background_color=spec.get("background_color", "transparent"),
            text_color=spec.get("text_color", "#ffffff"),
            grid_color=spec.get("grid_color", "#333333"),
            font_size=spec.get("font_size", 14),
            title_size=spec.get("title_size", 20),
            show_grid=spec.get("show_grid", True),
            show_legend=spec.get("show_legend", True),
            show_values=spec.get("show_values", False),
            show_axes=spec.get("show_axes", True),
            position=spec.get("position", "center"),
            scale=spec.get("scale", 0.85),
            opacity=spec.get("opacity", 1.0),
            padding=spec.get("padding", 0.08),
            chart_params=effect.get("params", {}),
            ai_model=effect.get("ai_model", "claude-sonnet-4-6"),
            ai_temperature=effect.get("ai_temperature", 0.5),
        )


class ChartEffect(ABC):
    name: str = "base"
    description: str = ""
    category: str = "chart"

    def __init__(self, params: ChartParams, data: ChartData,
                 width: int = 1920, height: int = 1080, fps: int = 30):
        self.params = params
        self.data = data
        self.width = width
        self.height = height
        self.fps = fps
        self._colors = get_palette(params.palette, max(10, len(data.series)))

    @property
    def total_duration(self) -> float:
        return self.params.enter_duration + self.params.hold_duration + self.params.exit_duration

    @property
    def total_frames(self) -> int:
        return max(1, int(self.total_duration * self.fps))

    def get_phase(self, frame_idx: int) -> Tuple[str, float]:
        t = frame_idx / self.fps
        enter_end = self.params.enter_duration
        hold_end = enter_end + self.params.hold_duration
        total = self.total_duration
        if t <= enter_end and enter_end > 0:
            raw = t / enter_end
            return ("enter", get_easing(self.params.enter_easing)(raw))
        elif t <= hold_end:
            return ("hold", 1.0)
        elif t <= total and self.params.exit_duration > 0:
            raw = (t - hold_end) / self.params.exit_duration
            return ("exit", 1.0 - get_easing(self.params.exit_easing)(min(raw, 1.0)))
        return ("done", 0.0)

    def _create_figure(self) -> Tuple:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        dpi = 100
        fig, ax = plt.subplots(figsize=(self.width / dpi, self.height / dpi), dpi=dpi)
        fig.patch.set_alpha(0)
        ax.set_facecolor("none")
        fig.subplots_adjust(
            left=self.params.padding, right=1-self.params.padding,
            top=1-self.params.padding, bottom=self.params.padding,
        )
        return fig, ax

    def _fig_to_rgba(self, fig) -> np.ndarray:
        import matplotlib.pyplot as plt
        fig.canvas.draw()
        frame = np.asarray(fig.canvas.buffer_rgba()).copy()
        plt.close(fig)
        return frame

    def _apply_opacity(self, frame: np.ndarray, opacity: float) -> np.ndarray:
        if opacity >= 1.0:
            return frame
        result = frame.copy()
        result[:, :, 3] = (result[:, :, 3].astype(float) * opacity).astype(np.uint8)
        return result

    def _style_ax(self, ax, show_title: bool = True):
        tc = self.params.text_color
        gc = self.params.grid_color
        if show_title and self.data.title:
            ax.set_title(self.data.title, color=tc, fontsize=self.params.title_size,
                        fontweight="bold", pad=12)
        if self.data.x_label:
            ax.set_xlabel(self.data.x_label, color=tc, fontsize=self.params.font_size)
        if self.data.y_label:
            ax.set_ylabel(self.data.y_label, color=tc, fontsize=self.params.font_size)
        ax.tick_params(colors=tc, labelsize=self.params.font_size - 2)
        for spine in ax.spines.values():
            spine.set_color(gc); spine.set_linewidth(0.5)
        if self.params.show_grid:
            ax.grid(True, alpha=0.2, color=gc, linestyle="--", linewidth=0.5)
        else:
            ax.grid(False)
        if not self.params.show_axes:
            ax.axis("off")

    @abstractmethod
    def render_frame(self, frame_idx: int, phase: str, progress: float) -> np.ndarray: ...

    def render_all_frames(self) -> List[np.ndarray]:
        frames = []
        for i in range(self.total_frames):
            phase, progress = self.get_phase(i)
            if phase == "done":
                break
            frames.append(self.render_frame(i, phase, progress))
        return frames
