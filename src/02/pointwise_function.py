"""Continuous geometric warps with ManimCE ApplyPointwiseFunction."""

from __future__ import annotations

import runpy
from pathlib import Path

import numpy as np
from manim import ApplyPointwiseFunction, Create, FadeIn, LaggedStart, Restore, Scene

BASE = runpy.run_path(str(Path(__file__).with_name("video_transform.py")))
build_poses = BASE["build_poses"]


class PointwiseFunctionMorph(Scene):
    def construct(self) -> None:
        poses, colors = build_poses()
        colors[0].set_z_index(-1)
        drawing = poses[0]
        self.wait(0.3)
        self.play(LaggedStart(*(Create(path) for path in drawing), lag_ratio=0.11), run_time=1.333)
        self.play(FadeIn(colors[0]), run_time=0.45)

        for phase in (0.0, 1.1, 2.2):
            drawing.save_state()

            def ripple(point, phase=phase):
                x, y, z = point
                return np.array((
                    x + 0.16 * np.sin(1.65 * y + phase),
                    y + 0.12 * np.sin(1.35 * x - phase),
                    z,
                ))

            self.play(ApplyPointwiseFunction(ripple, drawing), run_time=0.85)
            self.play(Restore(drawing), run_time=0.75)
