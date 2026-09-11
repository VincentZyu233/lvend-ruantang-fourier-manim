"""Nine Manim drawing effects using the same extracted Fourier image geometry."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from manim import BLACK, WHITE, Create, DrawBorderThenFill, FadeIn, Group, GrowFromCenter, ImageMobject, LaggedStart, Scene, ShowIncreasingSubsets, ShowPassingFlash, VGroup, VMobject, Write, config


PROJECT = Path(__file__).resolve().parents[2]
ASSETS = PROJECT / "build" / "01_geometry"
SOURCE = PROJECT / "素材捏" / "略ndoc的软糖动画" / "midpoint.png"
config.pixel_width = 720
config.pixel_height = 720
config.frame_width = 8
config.frame_height = 8
config.frame_rate = 20
config.background_color = WHITE


def pixel_path_to_vmobject(points: list[list[float]], width: int, height: int, color: str = BLACK, stroke_width: float = 2.8) -> VMobject:
    pixels = np.asarray(points, dtype=float)
    scene_points = np.column_stack([
        (pixels[:, 0] / width - 0.5) * config.frame_width,
        (0.5 - pixels[:, 1] / height) * config.frame_height,
        np.zeros(len(pixels)),
    ])
    path = VMobject(stroke_color=color, stroke_width=stroke_width, fill_opacity=0)
    path.set_points_as_corners(np.vstack([scene_points, scene_points[0]]))
    return path


class FourierBase(Scene):
    def setup_assets(self) -> None:
        data = json.loads((ASSETS / "geometry.json").read_text(encoding="utf-8"))
        width, height = data["width"], data["height"]
        self.color_mobjects = Group(*[
            ImageMobject(ASSETS / filename).set_height(config.frame_height)
            for filename in data["color_layers"]
        ])
        self.line_art = VGroup(*[
            pixel_path_to_vmobject(path, width, height)
            for path in data["paths"]
        ])
        self.fourier_curve = pixel_path_to_vmobject(
            data["fourier_curve"], width, height, color="#009A9A", stroke_width=5.5
        )

    def show_colors(self) -> None:
        self.play(
            LaggedStart(*(FadeIn(layer, scale=0.985) for layer in self.color_mobjects), lag_ratio=0.08),
            run_time=1.5,
        )

    def show_fourier_accent(self) -> None:
        self.play(ShowPassingFlash(self.fourier_curve, time_width=0.16), run_time=1.2)

    def finish(self) -> None:
        self.play(FadeIn(ImageMobject(SOURCE).set_height(config.frame_height)), run_time=0.45)
        self.wait(0.5)


class FourierWrite(FourierBase):
    def construct(self) -> None:
        self.setup_assets()
        self.show_fourier_accent()
        self.play(Write(self.line_art, lag_ratio=0.012), run_time=4.2)
        self.show_colors()
        self.finish()


class FourierCreate(FourierBase):
    def construct(self) -> None:
        self.setup_assets()
        self.show_fourier_accent()
        self.play(Create(self.line_art, lag_ratio=0.012), run_time=4.2)
        self.show_colors()
        self.finish()


class FourierPassingFlash(FourierBase):
    def construct(self) -> None:
        self.setup_assets()
        self.show_fourier_accent()
        flashing_lines = self.line_art.copy().set_stroke("#111111", width=5.0)
        self.play(ShowPassingFlash(flashing_lines, time_width=0.1), run_time=3.4)
        self.add(self.line_art)
        self.wait(0.8)
        self.show_colors()
        self.finish()


class FourierLaggedCreate(FourierBase):
    def construct(self) -> None:
        self.setup_assets()
        self.show_fourier_accent()
        self.play(LaggedStart(*(Create(path) for path in self.line_art), lag_ratio=0.11), run_time=4.2)
        self.show_colors()
        self.finish()


class FourierBorderThenFill(FourierBase):
    def construct(self) -> None:
        self.setup_assets()
        self.show_fourier_accent()
        self.play(DrawBorderThenFill(self.line_art, lag_ratio=0.012), run_time=4.2)
        self.show_colors()
        self.finish()


class FourierIncreasingSubsets(FourierBase):
    def construct(self) -> None:
        self.setup_assets()
        self.show_fourier_accent()
        self.play(ShowIncreasingSubsets(self.line_art), run_time=4.2)
        self.show_colors()
        self.finish()


class FourierGrowFromCenter(FourierBase):
    def construct(self) -> None:
        self.setup_assets()
        self.show_fourier_accent()
        self.play(LaggedStart(*(GrowFromCenter(path) for path in self.line_art), lag_ratio=0.11), run_time=4.2)
        self.show_colors()
        self.finish()


class FourierFadeInParts(FourierBase):
    def construct(self) -> None:
        self.setup_assets()
        self.show_fourier_accent()
        self.play(LaggedStart(*(FadeIn(path, scale=0.45) for path in self.line_art), lag_ratio=0.11), run_time=4.2)
        self.show_colors()
        self.finish()


class FourierPathFlash(FourierBase):
    def construct(self) -> None:
        self.setup_assets()
        self.show_fourier_accent()
        flashes = [ShowPassingFlash(path.copy(), time_width=0.22) for path in self.line_art]
        self.play(LaggedStart(*flashes, lag_ratio=0.11), run_time=4.2)
        self.add(self.line_art)
        self.show_colors()
        self.finish()
