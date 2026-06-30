from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

from chart_fx.base import ChartData, ChartEffect, ChartParams

_REGISTRY: Dict[str, type] = {}


def _register_all() -> None:
    if _REGISTRY:
        return
    from chart_fx.charts.bar_charts import BarChartEffect, StackedBarEffect, GroupedBarEffect, HorizontalBarEffect
    from chart_fx.charts.line_charts import LineChartEffect, AreaChartEffect, MultiLineEffect, SparklineEffect
    from chart_fx.charts.circle_charts import PieChartEffect, DonutChartEffect, GaugeChartEffect
    from chart_fx.charts.scatter_charts import ScatterChartEffect, BubbleChartEffect
    from chart_fx.matrices.heatmap_charts import HeatmapEffect, HourYearHeatmapEffect
    from chart_fx.matrices.correlation_matrix import CorrelationMatrixEffect
    from chart_fx.matrices.dot_matrix import DotMatrixEffect
    from chart_fx.matrices.quadrant_matrix import QuadrantMatrixEffect
    from chart_fx.specialized.compass_chart import CompassChartEffect
    from chart_fx.specialized.financial_charts import CandlestickEffect, FunnelEffect, SankeyEffect
    from chart_fx.specialized.radar_chart import RadarChartEffect
    from chart_fx.specialized.statistical_charts import BoxplotEffect, ViolinEffect
    from chart_fx.specialized.treemap_chart import TreemapEffect
    from chart_fx.specialized.waterfall_chart import WaterfallEffect
    from chart_fx.specialized.wind_rose import WindRoseEffect

    for cls in [
        BarChartEffect, StackedBarEffect, GroupedBarEffect, HorizontalBarEffect,
        LineChartEffect, AreaChartEffect, MultiLineEffect, SparklineEffect,
        PieChartEffect, DonutChartEffect, GaugeChartEffect,
        ScatterChartEffect, BubbleChartEffect,
        HeatmapEffect, HourYearHeatmapEffect,
        CorrelationMatrixEffect, DotMatrixEffect, QuadrantMatrixEffect,
        CompassChartEffect, CandlestickEffect, FunnelEffect, SankeyEffect,
        RadarChartEffect, BoxplotEffect, ViolinEffect,
        TreemapEffect, WaterfallEffect, WindRoseEffect,
    ]:
        _REGISTRY[cls.name] = cls


def list_effects() -> list[str]:
    _register_all()
    return sorted(_REGISTRY.keys())


def render_chart(
    chart_type: str,
    data: Dict[str, Any] | ChartData,
    params: Optional[Dict[str, Any] | ChartParams] = None,
    width: int = 1920,
    height: int = 1080,
    fps: int = 30,
    output: Optional[Path | str] = None,
) -> list[np.ndarray]:
    """Render a chart effect and return list of RGBA frames.

    If `output` is provided, frames are also written as a video via ffmpeg.
    """
    _register_all()

    cls = _REGISTRY.get(chart_type)
    if cls is None:
        available = ", ".join(sorted(_REGISTRY.keys()))
        raise ValueError(f"Unknown chart type {chart_type!r}. Available: {available}")

    if isinstance(data, dict):
        data = ChartData.from_dict(data)

    if params is None:
        params = ChartParams(chart_type=chart_type)
    elif isinstance(params, dict):
        params = ChartParams.from_spec({"chart_type": chart_type, **params})

    effect: ChartEffect = cls(params=params, data=data, width=width, height=height, fps=fps)
    frames = effect.render_all_frames()

    if output is not None:
        _write_video(frames, Path(output), fps=fps)

    return frames


def _write_video(frames: list[np.ndarray], output: Path, fps: int = 30) -> None:
    import subprocess, tempfile, os
    with tempfile.TemporaryDirectory() as td:
        for i, frame in enumerate(frames):
            from PIL import Image
            img = Image.fromarray(frame, "RGBA")
            img.save(os.path.join(td, f"frame_{i:05d}.png"))
        cmd = [
            "ffmpeg", "-y", "-framerate", str(fps),
            "-i", os.path.join(td, "frame_%05d.png"),
            "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p",
            str(output),
        ]
        subprocess.run(cmd, check=True)
