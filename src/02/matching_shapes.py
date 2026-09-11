"""ManimCE TransformMatchingShapes without mismatch fades."""

from __future__ import annotations

import runpy
from pathlib import Path

from manim import Create, FadeIn, FadeOut, LaggedStart, Scene, TransformMatchingShapes

BASE = runpy.run_path(str(Path(__file__).with_name("video_transform.py")))
build_poses = BASE["build_poses"]


class MatchingShapesMorph(Scene):
    def construct(self) -> None:
        poses, colors = build_poses()
        for color in colors:
            color.set_z_index(-1)
        current = poses[0]
        current_color = colors[0]
        self.wait(0.3)
        self.play(LaggedStart(*(Create(path) for path in current), lag_ratio=0.11), run_time=1.333)
        self.play(FadeIn(current_color), run_time=0.45)
        for target, target_color in zip(poses[1:], colors[1:]):
            # transform_mismatches makes every unmatched contour interpolate,
            # so this variant never falls back to a fade.
            self.play(
                TransformMatchingShapes(current, target, transform_mismatches=True),
                FadeOut(current_color),
                run_time=1.35,
            )
            self.play(FadeIn(target_color), run_time=0.25)
            current = target
            current_color = target_color
        self.wait(11.117)
