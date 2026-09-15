"""A compact Fourier epicycle reconstruction with a dynamic expression footer."""

from __future__ import annotations

import os
from collections import deque
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

import cv2
import numpy as np
from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Circle,
    Create,
    Dot,
    FadeIn,
    FadeOut,
    ImageMobject,
    Line,
    MathTex,
    Scene,
    ShowPassingFlash,
    Text,
    Transform,
    VGroup,
    VMobject,
    ValueTracker,
    always_redraw,
    config,
    register_font,
    smootherstep,
)


ROOT = Path(__file__).resolve().parents[2]
IMAGE_PATH = ROOT / "素材捏" / "略ndoc的软糖动画" / "midpoint.png"
FONT_FAMILY = "LXGW WenKai"
INK = "#171717"
TEAL = "#12B8A6"
LAVENDER = "#B7AEC9"
TRAIL_TAIL = "#DDD4EB"
TRAIL_HEAD = "#8872C6"
COUNTS = (1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16, 18, 20, 24, 28, 32, 36, 40, 45, 50, 56, 64, 72, 80)
MAX_VISIBLE_EPICYCLES = 25
BASE_FRAME_WIDTH = 8 * 1080 / 820
FOOTER_WORLD_HEIGHT = BASE_FRAME_WIDTH * 100 / 1080
RENDER_SCALE = int(os.environ.get("FOURIER_RENDER_SCALE", "1"))

config.pixel_width = 1080 * RENDER_SCALE
config.pixel_height = 920 * RENDER_SCALE
config.frame_width = BASE_FRAME_WIDTH
config.frame_height = 8 + FOOTER_WORLD_HEIGHT
config.frame_rate = int(os.environ.get("FOURIER_RENDER_FPS", "20"))
config.background_color = "#FFFFFF"


def font_path() -> Path:
    value = os.environ.get("LXGW_WENKAI_FONT")
    if not value:
        raise RuntimeError("Set LXGW_WENKAI_FONT to the LXGWWenKai-Medium.ttf path.")
    path = Path(value)
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def resample_closed(points: np.ndarray, count: int) -> np.ndarray:
    points = np.asarray(points, dtype=float)
    closed = np.vstack((points, points[0]))
    lengths = np.linalg.norm(np.diff(closed, axis=0), axis=1)
    distance = np.r_[0.0, np.cumsum(lengths)]
    locations = np.linspace(0.0, distance[-1], count, endpoint=False)
    return np.column_stack((
        np.interp(locations, distance, closed[:, 0]),
        np.interp(locations, distance, closed[:, 1]),
    ))


@dataclass(frozen=True)
class FourierModel:
    contour: np.ndarray
    coefficients: np.ndarray
    frequencies: np.ndarray
    ranked: np.ndarray
    center: complex
    scale: float
    image_center: np.ndarray

    @classmethod
    def load(cls) -> "FourierModel":
        image = cv2.imread(str(IMAGE_PATH), cv2.IMREAD_COLOR)
        if image is None:
            raise FileNotFoundError(IMAGE_PATH)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        ink = (gray < 105).astype(np.uint8) * 255
        contours, _ = cv2.findContours(ink, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        contour = max(contours, key=cv2.contourArea).reshape(-1, 2)
        sampled = resample_closed(contour, 1024)
        signal = sampled[:, 0] + 1j * sampled[:, 1]
        coefficients = np.fft.fft(signal) / len(signal)
        frequencies = np.fft.fftfreq(len(signal), d=1 / len(signal)).astype(int)
        ranked = np.argsort(np.abs(coefficients))[::-1]
        center = signal.mean()
        scale = 5.02 / max(np.ptp(sampled[:, 0]), np.ptp(sampled[:, 1]))
        image_center = np.array([
            1.55 + (image.shape[1] / 2 - center.real) * scale,
            -(image.shape[0] / 2 - center.imag) * scale,
            0.0,
        ])
        return cls(sampled, coefficients, frequencies, ranked, center, scale, image_center)

    def reconstruct(self, count: int) -> np.ndarray:
        time = np.linspace(0.0, 1.0, len(self.contour), endpoint=False)
        indices = self.ranked[:count]
        return np.sum(
            self.coefficients[indices, None]
            * np.exp(2j * np.pi * self.frequencies[indices, None] * time),
            axis=0,
        )

    def scene_points(self, values: np.ndarray) -> np.ndarray:
        return np.column_stack((
            (values.real - self.center.real) * self.scale + 1.55,
            -(values.imag - self.center.imag) * self.scale,
            np.zeros(len(values)),
        ))


class FourierRibbonWand(Scene):
    """Build a hand-drawn contour from its strongest DFT coefficients."""

    right_shift = RIGHT * 1.02 + DOWN * 0.28
    inset_scale = 0.55

    @cached_property
    def model(self) -> FourierModel:
        return FourierModel.load()

    def text(self, value: str, size: float, color: str = INK) -> Text:
        return Text(value, font=FONT_FAMILY, font_size=size, color=color)

    def math(self, value: str, size: float, color: str = INK) -> MathTex:
        return MathTex(value, font_size=size, color=color)

    def header(self) -> None:
        title = self.text("傅里叶轮廓重建", 36).to_corner(UP + LEFT, buff=0.34)
        subtitle = self.text("00 · Ribbon Wand", 20, "#66747A").next_to(
            title, DOWN, aligned_edge=LEFT, buff=0.06
        )
        accent = Line(
            title.get_left() + DOWN * 0.22,
            title.get_left() + RIGHT * 1.1 + DOWN * 0.22,
            color=TEAL,
            stroke_width=5,
        )
        self.add(VGroup(title, subtitle, accent))

    def wave(self, y: float, frequencies: tuple[tuple[float, float], ...], color: str) -> VMobject:
        x = np.linspace(-4.9, -1.35, 260)
        values = sum(amplitude * np.sin(frequency * (x + 4.9) * 1.85) for frequency, amplitude in frequencies)
        curve = VMobject()
        curve.set_points_as_corners(np.column_stack((x, y + values, np.zeros(len(x)))))
        curve.set_stroke(color, width=3.4)
        return curve

    def trig_intro(self) -> None:
        caption = self.text("从简单的三角函数叠加开始", 26).move_to(np.array([-3.1, 2.32, 0]))
        baseline = VGroup(*[
            Line(np.array([-4.9, y, 0]), np.array([-1.35, y, 0]), color="#D8E0E2", stroke_width=1.5)
            for y in (1.35, 0.35, -0.65)
        ])
        first = self.wave(1.35, ((1, 0.38),), "#84909A")
        second = self.wave(0.35, ((3, 0.28),), LAVENDER)
        third = self.wave(-0.65, ((1, 0.38), (3, 0.28), (7, 0.16)), TEAL)
        labels = VGroup(
            self.math(r"\sin(t)", 24, "#66747A").next_to(first, LEFT, buff=0.1),
            self.math(r"\sin(3t)", 24, "#66747A").next_to(second, LEFT, buff=0.1),
            self.text("sum", 18, TEAL).next_to(third, LEFT, buff=0.1),
        )
        self.play(FadeIn(caption), Create(baseline), run_time=0.8)
        self.play(Create(first), FadeIn(labels[0]), run_time=1.15)
        self.play(Create(second), FadeIn(labels[1]), run_time=1.0)
        self.play(Create(third), FadeIn(labels[2]), run_time=1.2)
        self.wait(0.7)
        self.play(FadeOut(VGroup(caption, baseline, first, second, third, labels)), run_time=0.75)

    def epicycle_intro(self) -> None:
        origin = np.array([-3.55, -0.22, 0.0])
        phase = ValueTracker(0.0)
        caption = self.text("旋转向量的末端，留下轨迹", 26).move_to(np.array([-2.55, 2.22, 0]))
        chain = always_redraw(lambda: self.epicycle_group(phase.get_value(), 6, origin, 0.5))
        tip = always_redraw(lambda: Dot(self.endpoint(phase.get_value(), 6, origin, 0.5), radius=0.055, color=TEAL))
        trail = VMobject()
        history: deque[np.ndarray] = deque()

        def update_trace(mob: VMobject, dt: float) -> None:
            del dt
            point = self.endpoint(phase.get_value(), 6, origin, 0.5)
            if not history or np.linalg.norm(point - history[-1]) > 0.045:
                history.append(point)
            if len(history) > 150:
                history.popleft()
            if len(history) > 1:
                mob.set_points_smoothly(np.array(history)).set_stroke(TEAL, width=3.2)

        trail.add_updater(update_trace)
        self.play(FadeIn(caption), FadeIn(chain), FadeIn(tip), run_time=0.8)
        self.add(trail)
        self.play(phase.animate.set_value(1), run_time=5.2, rate_func=smootherstep)
        trail.clear_updaters()
        self.play(FadeOut(VGroup(caption, chain, tip, trail)), run_time=0.8)

    def curve(self, count: int, color: str = TEAL, width: float = 4.2, opacity: float = 1.0) -> VMobject:
        points = self.model.scene_points(self.model.reconstruct(count))
        curve = VMobject()
        curve.set_points_as_corners(np.vstack((points, points[0])))
        return curve.set_stroke(color, width=width, opacity=opacity).set_fill(opacity=0)

    def endpoint(self, time: float, active_terms: float, origin: np.ndarray, scale: float) -> np.ndarray:
        position = origin.copy()
        visible = min(MAX_VISIBLE_EPICYCLES, max(1, int(np.ceil(active_terms))))
        for index, rank in enumerate(self.model.ranked[:visible]):
            weight = float(np.clip(active_terms - index, 0.0, 1.0))
            coefficient = self.model.coefficients[rank]
            vector = coefficient * np.exp(2j * np.pi * self.model.frequencies[rank] * time) * weight
            position += np.array([vector.real * self.model.scale * scale, -vector.imag * self.model.scale * scale, 0.0])
        return position

    def epicycle_group(self, time: float, active_terms: float, origin: np.ndarray, scale: float) -> VGroup:
        position = origin.copy()
        group = VGroup()
        visible = min(MAX_VISIBLE_EPICYCLES, max(1, int(np.ceil(active_terms))))
        for index, rank in enumerate(self.model.ranked[:visible]):
            weight = float(np.clip(active_terms - index, 0.0, 1.0))
            coefficient = self.model.coefficients[rank]
            vector = coefficient * np.exp(2j * np.pi * self.model.frequencies[rank] * time) * weight
            radius = max(abs(coefficient) * self.model.scale * scale * weight, 0.001)
            next_position = position + np.array([vector.real * self.model.scale * scale, -vector.imag * self.model.scale * scale, 0.0])
            group.add(
                Circle(radius, color="#8BA2A6", stroke_width=1.25, stroke_opacity=0.76).move_to(position),
                Line(position, next_position, color=TEAL, stroke_width=2.6, stroke_opacity=0.86),
            )
            position = next_position
        return group

    def latest_term_readout(self, count: int) -> VGroup:
        rank = self.model.ranked[max(0, count - 1)]
        coefficient = self.model.coefficients[rank]
        frequency = int(self.model.frequencies[rank])
        radius = abs(coefficient) * self.model.scale * self.inset_scale
        phase_degrees = float(np.degrees(np.angle(coefficient)))
        heading = self.text("最新加入的频率项", 16, "#7A6887")
        values = self.math(
            rf"k={frequency:+03d}\quad r={radius:.2f}\quad \varphi_0={phase_degrees:+04.0f}^\circ",
            25,
            "#536067",
        )
        return VGroup(heading, values).arrange(DOWN, aligned_edge=LEFT, buff=0.04).move_to(np.array([-3.25, 2.15, 0]))

    def frequency_window(self, count: int) -> str:
        values = [int(self.model.frequencies[index]) for index in self.model.ranked[:count]]
        formatted = [f"{value:+03d}" for value in values]
        if len(formatted) > 6:
            formatted = [*formatted[:3], r"\ldots", *formatted[-3:]]
        return r",\,".join(formatted)

    def expression_footer(self, count: int) -> VGroup:
        # Keep the full truncated sum on one mathematical baseline.  Splitting
        # the coefficient window into a second row made the approximation sign
        # read as detached from the terms it qualifies.
        divider = Line(np.array([-5.25, -3.13, 0]), np.array([5.25, -3.13, 0]), color="#D8E0E2", stroke_width=1.2)
        heading = self.text("当前表达式", 17, "#7A6887").move_to(np.array([-4.35, -3.32, 0]))
        formula = self.math(
            rf"z(t)\approx\sum_k c_k e^{{i2\pi kt}}\quad K=\left\{{{self.frequency_window(count)}\right\}}\cdot\frac{{{count:02d}}}{{80}}",
            22,
            "#34454D",
        )
        formula.next_to(heading, RIGHT, buff=0.23).align_to(heading, UP)
        max_width = 8.55
        if formula.width > max_width:
            formula.scale_to_fit_width(max_width)
        return VGroup(divider, heading, formula)

    def ribbon_trail(self, phase: ValueTracker, active_terms: ValueTracker, origin: np.ndarray) -> VGroup:
        points: deque[np.ndarray] = deque()
        lengths: deque[float] = deque()
        max_length = 1.4 * 2 * np.pi * abs(self.model.coefficients[self.model.ranked[0]]) * self.model.scale * self.inset_scale
        trail = VGroup()

        def update(mob: VGroup, dt: float) -> None:
            del dt
            point = self.endpoint(phase.get_value(), active_terms.get_value(), origin, self.inset_scale)
            if not points:
                points.append(point)
                return
            distance = float(np.linalg.norm(point - points[-1]))
            if distance < 0.075:
                return
            points.append(point)
            lengths.append(distance)
            total = sum(lengths)
            while len(points) > 2 and (total > max_length or len(lengths) > 40):
                total -= lengths.popleft()
                points.popleft()
            path = VMobject()
            samples = np.array(points)
            if len(samples) >= 3:
                path.set_points_smoothly(samples)
            else:
                path.set_points_as_corners(samples)
            path.set_stroke([TRAIL_TAIL, TRAIL_HEAD], width=4.5, opacity=0.88).set_z_index(1)
            glow = path.copy().set_stroke("#C7BAE8", width=15, opacity=0.13).set_z_index(0)
            halo = Dot(point, radius=0.135, color="#D9CDF2", fill_opacity=0.20).set_stroke(width=0).set_z_index(1)
            nib = Dot(point, radius=0.050, color="#FFF9FF", fill_opacity=0.95).set_stroke(TEAL, width=1.2, opacity=0.85).set_z_index(3)
            mob.become(VGroup(glow, path, halo, nib))

        trail.add_updater(update)
        return trail

    def final_reveal(self, curve: VMobject, phase: ValueTracker) -> None:
        image = ImageMobject(IMAGE_PATH).set_height(1080 * self.model.scale).move_to(self.model.image_center + self.right_shift)
        image.set_z_index(-1)
        caption = self.text("80 个频率项，逼近一条手绘轮廓", 25).move_to(np.array([2.55, -3.18, 0]))
        self.play(phase.animate.increment_value(0.62), FadeIn(image), FadeIn(caption), run_time=2.2, rate_func=smootherstep)
        self.play(ShowPassingFlash(curve.copy().set_stroke(TEAL, width=7), time_width=0.09), run_time=1.1)
        self.wait(1.90)

    def construct(self) -> None:
        with register_font(font_path()):
            self.header()
            self.trig_intro()
            self.epicycle_intro()

            origin = np.array([-3.85, 0.04, 0.0])
            phase = ValueTracker(0.0)
            active_terms = ValueTracker(float(COUNTS[0]))
            left_title = self.text("旋转圆链 · 主频率项", 21, "#536067").move_to(np.array([-3.25, 2.78, 0]))
            rule = Line(np.array([-4.9, 2.42, 0]), np.array([-1.26, 2.42, 0]), color="#D8E0E2", stroke_width=1.4)
            visible_count = self.text("显示 01 个主频率圆", 18, "#66747A").move_to(np.array([-3.25, -3.12, 0]))
            newest = self.latest_term_readout(COUNTS[0])
            footer = self.expression_footer(COUNTS[0])
            chain = always_redraw(lambda: self.epicycle_group(phase.get_value(), active_terms.get_value(), origin, self.inset_scale))
            tip = always_redraw(lambda: Dot(self.endpoint(phase.get_value(), active_terms.get_value(), origin, self.inset_scale), radius=0.055, color=TEAL))
            trail = self.ribbon_trail(phase, active_terms, origin)
            target = self.curve(80, color="#D7E1E2", width=1.4, opacity=0.9).shift(self.right_shift).set_z_index(0)
            current = self.curve(COUNTS[0]).shift(self.right_shift).set_z_index(2)
            stage = self.math(r"01 / 80\ \mathrm{terms}", 30, "#536067").to_corner(UP + RIGHT, buff=0.28)

            self.add(target, trail)
            self.play(FadeIn(VGroup(left_title, rule, newest, chain, tip, visible_count, footer)), Create(current), FadeIn(stage), run_time=2.8)
            for count in COUNTS[1:]:
                next_curve = self.curve(count).shift(self.right_shift).set_z_index(2)
                next_stage = self.math(rf"{count:02d} / 80\ \mathrm{{terms}}", 30, "#536067").to_corner(UP + RIGHT, buff=0.28)
                visible = min(count, MAX_VISIBLE_EPICYCLES)
                suffix = "" if count <= MAX_VISIBLE_EPICYCLES else f"  +{count - MAX_VISIBLE_EPICYCLES:02d} 项"
                next_visible_count = self.text(f"显示 {visible:02d} 个主频率圆{suffix}", 18, "#66747A").move_to(np.array([-3.25, -3.12, 0]))
                self.play(
                    Transform(stage, next_stage),
                    Transform(visible_count, next_visible_count),
                    Transform(newest, self.latest_term_readout(count)),
                    Transform(footer, self.expression_footer(count)),
                    run_time=0.22,
                )
                self.play(
                    phase.animate.increment_value(1.08),
                    active_terms.animate.set_value(float(visible)),
                    Transform(current, next_curve),
                    run_time=2.30,
                    rate_func=smootherstep,
                )
            self.play(FadeOut(target), run_time=0.45)
            self.final_reveal(current, phase)
