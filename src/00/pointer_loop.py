"""A compact, always-coloured 02a-style pose loop for the Bili timeline."""

from __future__ import annotations

import runpy
import os
from pathlib import Path

from manim import FadeIn, FadeOut, Scene, Transform, config


ROOT = Path(__file__).resolve().parents[2]
BASE = runpy.run_path(str(ROOT / "src" / "02" / "video_transform.py"))
build_poses = BASE["build_poses"]

# This asset is composited with FFmpeg's white key, so it deliberately keeps
# the same white canvas as the established 02a render.
RENDER_SCALE = int(os.environ.get("FOURIER_RENDER_SCALE", "1"))
config.pixel_width = 720 * RENDER_SCALE
config.pixel_height = 720 * RENDER_SCALE
config.frame_width = 8
config.frame_height = 8
config.frame_rate = int(os.environ.get("FOURIER_RENDER_FPS", "20"))
config.background_color = "#FFFFFF"


class TimelinePoseLoop(Scene):
    """Loop the five 02a video poses without replaying its Create intro."""

    def construct(self) -> None:
        lines, colors = build_poses(artifact_dir=ROOT / "build" / "00_pointer_samples")
        for pose in lines:
            for path in pose:
                path.set_stroke(width=5.2)
        current_lines = lines[0]
        current_color = colors[0]
        self.add(current_color, current_lines)

        # Keep the exact 02a relationship: the visible colour always belongs
        # to the current line pose, fades out during its Transform, then the
        # next pose's colour fades in only after its outline settles.
        for target_lines, target_color in zip(lines[1:] + lines[:1], colors[1:] + colors[:1]):
            self.play(
                Transform(current_lines, target_lines),
                FadeOut(current_color),
                run_time=0.25,
            )
            current_color = target_color.copy()
            self.play(FadeIn(current_color), run_time=0.25)
