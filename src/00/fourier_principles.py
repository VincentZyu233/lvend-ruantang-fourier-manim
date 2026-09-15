"""Four short, high-school-level scenes that introduce Fourier contours."""

from __future__ import annotations

from collections import deque
import re

import numpy as np
from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Arrow,
    Circle,
    Create,
    DashedLine,
    Dot,
    FadeIn,
    FadeOut,
    Line,
    MathTex,
    Rectangle,
    ShowPassingFlash,
    Transform,
    VGroup,
    VMobject,
    ValueTracker,
    always_redraw,
    register_font,
    smootherstep,
)

from fourier_ribbon_wand import FourierRibbonWand, INK, LAVENDER, TEAL, font_path


GRAY = "#66747A"
GRID = "#D8E0E2"
PURPLE = "#7A6887"
CONTENT_RISE = 0.34
NOTE_CENTER_Y = -2.62


class PrinciplesScene(FourierRibbonWand):
    """Shared typography and transitions for the four explanatory chapters."""

    chapter = "00"
    heading = "傅里叶轮廓"
    subtitle = ""

    def setup_scene(self) -> None:
        title = self.text(self.heading, 35).to_corner(UP + LEFT, buff=0.34)
        subtitle = self.text(f"{self.chapter} · {self.subtitle}", 19, GRAY).next_to(
            title, DOWN, aligned_edge=LEFT, buff=0.05
        )
        accent = Line(
            title.get_left() + DOWN * 0.22,
            title.get_left() + RIGHT * 1.15 + DOWN * 0.22,
            color=TEAL,
            stroke_width=5,
        )
        self.add(VGroup(title, subtitle, accent))

    def formula(self, expression: str, size: float = 34, color: str = INK) -> MathTex:
        return MathTex(expression, font_size=size, color=color)

    def curve(self, *args: object, **kwargs: object) -> VMobject:
        """Keep the teaching diagrams above the larger timeline safe area."""
        return super().curve(*args, **kwargs).shift(UP * CONTENT_RISE)

    def wrapped_text(self, value: str, size: float, color: str, max_width: float) -> VGroup:
        """Wrap CJK copy by its rendered width instead of letting it leave the frame."""
        lines: list[str] = []
        for paragraph in value.splitlines() or [""]:
            line = ""
            tokens = re.findall(r"[A-Za-z0-9_+\-./=\[\]|]+|.", paragraph)
            for token in tokens:
                candidate = line + token
                if line and self.text(candidate, size, color).width > max_width:
                    lines.append(line)
                    line = token
                else:
                    line = candidate
            if line:
                lines.append(line)
        return VGroup(*[self.text(line, size, color) for line in lines]).arrange(
            DOWN, aligned_edge=LEFT, buff=0.06
        )

    def note(self, title: str, detail: str, y: float = NOTE_CENTER_Y) -> VGroup:
        heading = self.wrapped_text(title, 24, "#34454D", 9.35)
        body = self.wrapped_text(detail, 18, GRAY, 9.35)
        return VGroup(heading, body).arrange(DOWN, aligned_edge=LEFT, buff=0.08).move_to(
            np.array([0.0, y, 0])
        )

    def clear_stage(self, *mobjects: VGroup, duration: float = 0.55) -> None:
        self.play(FadeOut(VGroup(*mobjects)), run_time=duration)


class ClosedLoopCoordinates(PrinciplesScene):
    """00b: define a loop, t, coordinates, and a circle before using DFT."""

    chapter = "00b"
    heading = "先把一条线变成一个运动"
    subtitle = "闭合曲线、进度 t 与坐标 z(t)"

    def loop_progress(self) -> None:
        curve = self.curve(80, TEAL, 4.8).shift(RIGHT * 1.0 + DOWN * 0.1)
        dot = Dot(curve.get_start(), radius=0.07, color=LAVENDER)
        phase = ValueTracker(0.0)
        dot.add_updater(lambda mob: mob.move_to(curve.point_from_proportion(phase.get_value())))
        title = self.text("让一个点沿闭合轮廓走一圈", 27).move_to(np.array([-0.9, 2.50, 0]))
        first = self.text("像赛车绕跑道：回到起点后，下一圈可以重复。", 19, GRAY).next_to(
            title, DOWN, aligned_edge=LEFT, buff=0.12
        )
        ticks = VGroup()
        for value in (0.0, 0.3, 0.8, 1.0):
            marker = Dot(curve.point_from_proportion(value), radius=0.036, color="#8BA2A6")
            label = self.formula(rf"t={value:g}", 22, PURPLE).next_to(marker, UP, buff=0.08)
            ticks.add(marker, label)
        note = self.note(
            "t 不是现实秒数，而是跑完一圈的进度。",
            "规定 t=0 刚出发，t=0.3 是 30%，t=1 回到起点；之后 t+1 又是一圈。",
        )
        self.play(FadeIn(title), FadeIn(first), Create(curve), FadeIn(ticks), FadeIn(dot), run_time=1.9)
        self.play(phase.animate.set_value(1.0), run_time=5.2, rate_func=smootherstep)
        dot.clear_updaters()
        self.play(FadeIn(note), run_time=0.8)
        self.wait(1.4)
        self.clear_stage(title, first, curve, ticks, dot, note)

    def coordinate_example(self) -> None:
        origin = np.array([-3.2, -0.10, 0])
        horizontal = Arrow(origin + LEFT * 1.55, origin + RIGHT * 1.65, buff=0, color="#8BA2A6", stroke_width=2)
        vertical = Arrow(origin + DOWN * 1.4, origin + UP * 1.5, buff=0, color="#8BA2A6", stroke_width=2)
        point = Dot(origin + np.array([1.04, 0.78, 0]), color=TEAL, radius=0.07)
        x_line = DashedLine(point.get_center(), np.array([point.get_x(), origin[1], 0]), color=LAVENDER, stroke_width=1.6)
        y_line = DashedLine(point.get_center(), np.array([origin[0], point.get_y(), 0]), color=LAVENDER, stroke_width=1.6)
        coordinate = self.formula(r"z(t)=(x(t),y(t))", 36).move_to(np.array([2.55, 1.18, 0]))
        explain = self.text("输入一个进度 t，输出此刻的横、纵坐标。", 20, GRAY).next_to(
            coordinate, DOWN, buff=0.16
        )
        z_values = VGroup(
            self.formula(r"t=0.3", 24, PURPLE),
            self.formula(r"z(0.3)=(1.04,0.78)", 26, TEAL),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.12).move_to(np.array([2.55, -0.02, 0]))
        note = self.note(
            "把轮廓看成函数：进度决定位置。",
            "图像上的点是静态坐标；z(t) 让它随着 t 改变，成为一条可以重复播放的路径。",
        )
        group = VGroup(horizontal, vertical, point, x_line, y_line, coordinate, explain, z_values)
        self.play(FadeIn(group), run_time=1.3)
        self.play(ShowPassingFlash(VGroup(x_line, y_line).copy().set_stroke(TEAL, width=5), time_width=0.18), run_time=1.2)
        self.play(FadeIn(note), run_time=0.7)
        self.wait(1.4)
        self.clear_stage(group, note)

    def circle_example(self) -> None:
        center = np.array([-2.55, -0.05, 0])
        phase = ValueTracker(0.0)
        circle = Circle(1.23, color="#8BA2A6", stroke_width=2).move_to(center)
        vector = always_redraw(lambda: Line(
            center,
            center + 1.23 * np.array([np.cos(2 * np.pi * phase.get_value()), np.sin(2 * np.pi * phase.get_value()), 0]),
            color=TEAL,
            stroke_width=4,
        ))
        tip = always_redraw(lambda: Dot(vector.get_end(), radius=0.065, color=TEAL))
        formula = self.formula(r"z(t)=(\cos(2\pi t),\sin(2\pi t))", 33).move_to(np.array([2.05, 1.15, 0]))
        lines = VGroup(
            self.text("t 从 0 走到 1：正好绕圆一圈", 21, GRAY),
            self.text("cos 管左右，sin 管上下", 21, PURPLE),
            self.text("这就是最简单的闭合、可重复运动", 21, "#34454D"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.16).move_to(np.array([2.05, -0.08, 0]))
        note = self.note(
            "后面所有复杂轮廓，都会由许多个这样的圆周运动相加。",
            "这一刻只需记住：t 在 [0,1] 内前进，2π 让它恰好转完一圈。",
        )
        self.play(FadeIn(circle), FadeIn(vector), FadeIn(tip), FadeIn(formula), FadeIn(lines), run_time=1.3)
        self.play(phase.animate.set_value(1.0), run_time=4.8, rate_func=smootherstep)
        self.play(FadeIn(note), run_time=0.75)
        self.wait(1.3)
        self.clear_stage(circle, vector, tip, formula, lines, note)

    def discrete_and_continuous(self) -> None:
        line = Line(np.array([-4.25, 0.35, 0]), np.array([4.25, 0.35, 0]), color=GRID, stroke_width=3)
        title = self.text("t 可以连续取值；程序记录时再把它切成编号", 26).move_to(np.array([0.0, 2.48, 0]))
        values = (0, 0.25, 0.5, 0.75, 1.0)
        ticks = VGroup(*[
            VGroup(
                Line(np.array([-4.25 + 8.5 * value, 0.20, 0]), np.array([-4.25 + 8.5 * value, 0.50, 0]), color=LAVENDER, stroke_width=2),
                self.formula(rf"t={value:g}", 21, PURPLE).next_to(np.array([-4.25 + 8.5 * value, 0.20, 0]), DOWN, buff=0.14),
                self.formula(rf"n={round(value * 4)}", 18, GRAY).next_to(np.array([-4.25 + 8.5 * value, 0.50, 0]), UP, buff=0.14),
            )
            for value in values
        ])
        slider = Dot(line.get_left(), color=TEAL, radius=0.075)
        formula = self.formula(r"t_n=\frac{n}{N}\qquad n=0,1,\ldots,N-1", 34).move_to(np.array([0.0, -1.02, 0]))
        note = self.note(
            "动画里 t 可以是 0.372 这样的连续进度。",
            "真正输入 DFT 时，程序选 N 个位置，写成 n=0,1,…,N-1；第 n 个位置的进度就是 n/N。",
        )
        self.play(FadeIn(title), Create(line), FadeIn(ticks), FadeIn(slider), run_time=1.25)
        self.play(slider.animate.move_to(line.get_right()), run_time=3.1, rate_func=smootherstep)
        self.play(FadeIn(formula), FadeIn(note), run_time=0.8)
        self.wait(1.45)
        self.clear_stage(title, line, ticks, slider, formula, note)

    def sine_cosine_projections(self) -> None:
        center = np.array([-2.95, 0.0, 0])
        phase = ValueTracker(0.0)
        circle = Circle(1.12, color="#8BA2A6", stroke_width=2).move_to(center)
        axes = VGroup(
            Line(center + LEFT * 1.38, center + RIGHT * 1.38, color=GRID, stroke_width=1.4),
            Line(center + DOWN * 1.38, center + UP * 1.38, color=GRID, stroke_width=1.4),
        )
        vector = always_redraw(lambda: Arrow(
            center,
            center + 1.12 * np.array([np.cos(2 * np.pi * phase.get_value()), np.sin(2 * np.pi * phase.get_value()), 0]),
            buff=0, color=TEAL, stroke_width=4,
        ))
        dot = always_redraw(lambda: Dot(vector.get_end(), radius=0.055, color=TEAL))
        vertical = always_redraw(lambda: DashedLine(vector.get_end(), np.array([vector.get_end()[0], center[1], 0]), color=LAVENDER, stroke_width=1.5))
        horizontal = always_redraw(lambda: DashedLine(vector.get_end(), np.array([center[0], vector.get_end()[1], 0]), color=LAVENDER, stroke_width=1.5))
        formula = self.formula(r"x(t)=\cos(2\pi t)\qquad y(t)=\sin(2\pi t)", 32).move_to(np.array([2.05, 1.20, 0]))
        prose = VGroup(
            self.text("圆上点的横向投影是 cos", 21, PURPLE),
            self.text("纵向投影是 sin", 21, TEAL),
            self.text("两个投影合在一起，就是一个匀速转圈的点", 20, GRAY),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.16).move_to(np.array([2.05, -0.02, 0]))
        note = self.note(
            "三角函数不是额外的魔法：它们就是圆周运动在两条坐标轴上的影子。",
            "因此用正弦、余弦的组合来描述路径，本质上是在组合不同速度的圆周运动。",
        )
        self.play(FadeIn(circle), FadeIn(axes), FadeIn(vector), FadeIn(dot), FadeIn(vertical), FadeIn(horizontal), FadeIn(formula), FadeIn(prose), run_time=1.35)
        self.play(phase.animate.set_value(1.18), run_time=5.0, rate_func=smootherstep)
        self.play(FadeIn(note), run_time=0.8)
        self.wait(1.5)
        self.clear_stage(circle, axes, vector, dot, vertical, horizontal, formula, prose, note)

    def periodic_rule(self) -> None:
        left = self.formula(r"z(0)=z(1)=z(2)=\cdots", 38, TEAL).move_to(np.array([0.0, 0.80, 0]))
        right = self.formula(r"z(t+1)=z(t)", 39, PURPLE).move_to(np.array([0.0, -0.28, 0]))
        title = self.text("闭合轮廓的约定：走完一圈，下一圈从同一点接上", 26).move_to(np.array([0.0, 2.47, 0]))
        note = self.note(
            "傅里叶并不要求真实动画永远循环；这里是我们把一条封闭轮廓当作周期为 1 的信号。",
            "有了这个约定，所有整数 k 的圆周运动都会在 t=0 与 t=1 无缝对上。",
        )
        self.play(FadeIn(title), FadeIn(left), run_time=1.0)
        self.play(Transform(left, right), run_time=1.35, rate_func=smootherstep)
        self.play(FadeIn(note), run_time=0.75)
        self.wait(2.1)
        self.clear_stage(title, left, note)

    def construct(self) -> None:
        with register_font(font_path()):
            self.setup_scene()
            self.loop_progress()
            self.coordinate_example()
            self.circle_example()
            self.discrete_and_continuous()
            self.sine_cosine_projections()
            self.periodic_rule()


class ComplexRotatingVectors(PrinciplesScene):
    """00c: bridge familiar 2D vectors and the compact complex notation."""

    chapter = "00c"
    heading = "复平面只是把二维坐标写短"
    subtitle = "i、exp 与一个旋转向量"

    def complex_plane(self) -> None:
        origin = np.array([-2.45, -0.18, 0])
        horizontal = Arrow(origin + LEFT * 1.7, origin + RIGHT * 1.7, buff=0, color="#8BA2A6", stroke_width=2)
        vertical = Arrow(origin + DOWN * 1.55, origin + UP * 1.55, buff=0, color="#8BA2A6", stroke_width=2)
        real = self.text("实轴", 18, GRAY).next_to(horizontal.get_end(), DOWN, buff=0.08)
        imaginary = self.text("虚轴", 18, GRAY).next_to(vertical.get_end(), LEFT, buff=0.08)
        point = Dot(origin + np.array([-0.8, 1.18, 0]), color=TEAL, radius=0.075)
        vector = Arrow(origin, point.get_center(), buff=0, color=TEAL, stroke_width=4)
        coordinate = self.formula(r"-2+3i\ \longleftrightarrow\ (-2,3)", 34).move_to(np.array([2.25, 1.16, 0]))
        copy = VGroup(
            self.text("横坐标写在前面；纵坐标的系数写在 i 前面。", 20, GRAY),
            self.text("地点没变，只是从直角坐标换成一种紧凑记号。", 20, PURPLE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.16).move_to(np.array([2.25, 0.16, 0]))
        note = self.note(
            "把 x+iy 当成一个二维向量即可。",
            "它不是凭空多出一条维度：横轴仍是实数，纵轴仍是 i 的系数。",
        )
        group = VGroup(horizontal, vertical, real, imaginary, point, vector, coordinate, copy)
        self.play(FadeIn(group), run_time=1.25)
        self.play(ShowPassingFlash(vector.copy().set_stroke(LAVENDER, width=7), time_width=0.16), run_time=1.25)
        self.play(FadeIn(note), run_time=0.7)
        self.wait(1.4)
        self.clear_stage(group, note)

    def multiplication_by_i(self) -> None:
        origin = np.array([-2.55, -0.18, 0])
        axes = VGroup(
            Arrow(origin + LEFT * 1.65, origin + RIGHT * 1.65, buff=0, color="#8BA2A6", stroke_width=2),
            Arrow(origin + DOWN * 1.55, origin + UP * 1.55, buff=0, color="#8BA2A6", stroke_width=2),
        )
        before_end = origin + np.array([1.05, 0.55, 0])
        before = Arrow(origin, before_end, buff=0, color=TEAL, stroke_width=4)
        after = Arrow(origin, origin + np.array([-0.55, 1.05, 0]), buff=0, color=LAVENDER, stroke_width=4)
        label_before = self.formula(r"(x,y)", 27, TEAL).next_to(before_end, RIGHT, buff=0.08)
        label_after = self.formula(r"(-y,x)", 27, LAVENDER).next_to(after.get_end(), LEFT, buff=0.08)
        formula = self.formula(r"(x+iy)\cdot i=-y+ix", 34).move_to(np.array([2.20, 1.1, 0]))
        prose = VGroup(
            self.text("乘一次 i：向量逆时针转 90°。", 21, GRAY),
            self.text("再乘一次 i：再转 90°；连续使用就能描述旋转。", 20, PURPLE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to(np.array([2.2, -0.01, 0]))
        note = self.note(
            "这是复数在这里最有用的几何意义。",
            "它让“向量转角度”从两行坐标运算，压缩为一次乘法。",
        )
        self.play(FadeIn(axes), FadeIn(before), FadeIn(label_before), FadeIn(formula), FadeIn(prose), run_time=1.2)
        self.play(Transform(before, after), Transform(label_before, label_after), run_time=1.45, rate_func=smootherstep)
        self.play(FadeIn(note), run_time=0.7)
        self.wait(1.4)
        self.clear_stage(axes, before, label_before, formula, prose, note)

    def rotating_term(self) -> None:
        center = np.array([-2.62, -0.10, 0])
        phase = ValueTracker(0.0)
        circle = Circle(1.26, color="#8BA2A6", stroke_width=2).move_to(center)
        vector = always_redraw(lambda: Arrow(
            center,
            center + 1.26 * np.array([
                np.cos(2 * np.pi * 2 * phase.get_value() + 0.62),
                np.sin(2 * np.pi * 2 * phase.get_value() + 0.62),
                0,
            ]),
            buff=0,
            color=TEAL,
            stroke_width=4,
        ))
        tip = always_redraw(lambda: Dot(vector.get_end(), radius=0.06, color=TEAL))
        formula = self.formula(r"c[k]\,e^{i2\pi kt}", 40).move_to(np.array([2.05, 1.22, 0]))
        labels = VGroup(
            self.text("|c[k]|：半径有多大", 22, TEAL),
            self.text("arg(c[k])：从哪个方向出发", 21, PURPLE),
            self.text("k：一圈里转几圈，正负表示转向", 21, GRAY),
            self.text("exp(...) = e 的幂：程序写“持续转动”的简写", 19, "#34454D"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.14).move_to(np.array([2.05, -0.09, 0]))
        note = self.note(
            "欧拉公式 e^{iθ}=cosθ+i sinθ 把圆周运动压成一行。",
            "所以 c[k]e^{i2πkt} 就是一根指定大小、初相位和转速的旋转向量。",
        )
        self.play(FadeIn(circle), FadeIn(vector), FadeIn(tip), FadeIn(formula), FadeIn(labels), run_time=1.25)
        self.play(phase.animate.set_value(1.15), run_time=4.9, rate_func=smootherstep)
        self.play(FadeIn(note), run_time=0.7)
        self.wait(1.35)
        self.clear_stage(circle, vector, tip, formula, labels, note)

    def euler_identity(self) -> None:
        left = self.formula(r"e^{i\theta}=\cos\theta+i\sin\theta", 42, TEAL).move_to(np.array([0.0, 0.72, 0]))
        pieces = VGroup(
            self.text("e 是自然常数；exp(…) 就是 e 的幂。", 21, GRAY),
            self.text("把 θ 放进 i 的倍数里，结果恰好落在单位圆上。", 21, PURPLE),
            self.text("所以 exp(iθ) 可直接当成“转到 θ 角度的单位向量”。", 21, "#34454D"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.16).move_to(np.array([0.0, -0.86, 0]))
        title = self.text("欧拉公式把 sin、cos 两个坐标压成一个复数", 26).move_to(np.array([0.0, 2.47, 0]))
        note = self.note(
            "这里的 exp 不是某个新物理量，也不是缩写；它来自 exponential，指数函数。",
            "复数写法只是在同一行中同时保存“横坐标 + 纵坐标”。",
        )
        self.play(FadeIn(title), FadeIn(left), run_time=1.0)
        self.play(ShowPassingFlash(left.copy().set_stroke(LAVENDER, width=6), time_width=0.14), FadeIn(pieces), run_time=1.7)
        self.play(FadeIn(note), run_time=0.75)
        self.wait(2.0)
        self.clear_stage(title, left, pieces, note)

    def exponent_adds_angles(self) -> None:
        center = np.array([-2.85, -0.22, 0])
        first = Arrow(center, center + 1.05 * np.array([np.cos(0.55), np.sin(0.55), 0]), buff=0, color=TEAL, stroke_width=4)
        second = Arrow(center, center + 1.05 * np.array([np.cos(1.65), np.sin(1.65), 0]), buff=0, color=LAVENDER, stroke_width=4)
        arc = Circle(1.12, color=GRID, stroke_width=1.5).move_to(center)
        formula = self.formula(r"e^{ia}\cdot e^{ib}=e^{i(a+b)}", 37).move_to(np.array([2.0, 0.92, 0]))
        detail = VGroup(
            self.text("复数相乘：长度相乘，角度相加。", 21, GRAY),
            self.text("因此“原来转 +3 圈”再乘“反向转 −3 圈”，", 20, PURPLE),
            self.text("总转角就是 0。", 20, PURPLE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.11).move_to(np.array([2.28, -0.01, 0]))
        title = self.text("为什么解旋时能把两个转速抵消？", 26).move_to(np.array([0.0, 2.47, 0]))
        note = self.note(
            "这条指数运算规则就是后面“测对后静下来”的代数原因。",
            "不是向量点积：它是把两个旋转先后执行，旋转角自然相加。",
        )
        self.play(FadeIn(title), FadeIn(arc), FadeIn(first), FadeIn(formula), FadeIn(detail), run_time=1.2)
        self.play(Transform(first, second), run_time=1.55, rate_func=smootherstep)
        self.play(FadeIn(note), run_time=0.75)
        self.wait(1.75)
        self.clear_stage(title, arc, first, formula, detail, note)

    def positive_and_negative(self) -> None:
        phase = ValueTracker(0.0)
        centers = (np.array([-2.45, -0.18, 0]), np.array([2.45, -0.18, 0]))
        circles = VGroup(*[Circle(0.92, color="#8BA2A6", stroke_width=2).move_to(center) for center in centers])
        vectors = VGroup(*[
            always_redraw(lambda center=center, sign=sign: Arrow(center, center + 0.82 * np.array([np.cos(sign * 2 * np.pi * 2 * phase.get_value()), np.sin(sign * 2 * np.pi * 2 * phase.get_value()), 0]), buff=0, color=TEAL if sign > 0 else LAVENDER, stroke_width=4))
            for center, sign in zip(centers, (1, -1))
        ])
        labels = VGroup(
            self.formula(r"k=+2", 29, TEAL).next_to(circles[0], DOWN, buff=0.2),
            self.formula(r"k=-2", 29, LAVENDER).next_to(circles[1], DOWN, buff=0.2),
        )
        title = self.text("k 的正负只表示转向，绝对值表示一圈里转几圈", 25).move_to(np.array([0.0, 2.47, 0]))
        note = self.note(
            "k=+2 与 k=−2 在 t 从 0 到 1 时都转两圈，只是方向相反。",
            "这也是傅里叶会同时检查慢转、快转、正转和反转的原因。",
        )
        self.play(FadeIn(title), FadeIn(circles), FadeIn(vectors), FadeIn(labels), run_time=1.15)
        self.play(phase.animate.set_value(1.3), run_time=4.6, rate_func=smootherstep)
        self.play(FadeIn(note), run_time=0.75)
        self.wait(1.35)
        self.clear_stage(title, circles, vectors, labels, note)

    def vector_sum(self) -> None:
        origin = np.array([-3.6, -0.42, 0])
        phase = ValueTracker(0.0)
        first = always_redraw(lambda: Arrow(origin, origin + 1.14 * np.array([np.cos(2 * np.pi * phase.get_value()), np.sin(2 * np.pi * phase.get_value()), 0]), buff=0, color=TEAL, stroke_width=4))
        second = always_redraw(lambda: Arrow(first.get_end(), first.get_end() + 0.62 * np.array([np.cos(-4 * np.pi * phase.get_value() + 0.8), np.sin(-4 * np.pi * phase.get_value() + 0.8), 0]), buff=0, color=LAVENDER, stroke_width=4))
        tip = always_redraw(lambda: Dot(second.get_end(), radius=0.06, color=TEAL))
        trail = VMobject()
        history: deque[np.ndarray] = deque()

        def update_trace(mob: VMobject, dt: float) -> None:
            del dt
            point = second.get_end()
            if not history or np.linalg.norm(point - history[-1]) > 0.035:
                history.append(point)
            if len(history) > 170:
                history.popleft()
            if len(history) > 2:
                mob.set_points_smoothly(np.array(history)).set_stroke(TEAL, width=3.5)

        trail.add_updater(update_trace)
        title = self.text("先转一个圆，再从它的末端接第二个圆", 26).move_to(np.array([0.0, 2.47, 0]))
        formula = self.formula(r"z(t)=c[1]e^{i2\pi t}+c[-2]e^{-i4\pi t}", 30).move_to(np.array([1.60, -1.38, 0]))
        note = self.note(
            "两个圆的末端相加，已经不再是圆；更多不同圆相加，就能得到复杂闭合轮廓。",
            "接下来要解决的只剩一件事：怎样从原轮廓测出每个 c[k]。",
        )
        self.play(FadeIn(title), FadeIn(first), FadeIn(second), FadeIn(tip), FadeIn(formula), run_time=1.25)
        self.add(trail)
        self.play(phase.animate.set_value(1.15), run_time=5.4, rate_func=smootherstep)
        trail.clear_updaters()
        self.play(FadeIn(note), run_time=0.75)
        self.wait(1.4)
        self.clear_stage(title, first, second, tip, trail, formula, note)

    def construct(self) -> None:
        with register_font(font_path()):
            self.setup_scene()
            self.complex_plane()
            self.multiplication_by_i()
            self.euler_identity()
            self.exponent_adds_angles()
            self.rotating_term()
            self.positive_and_negative()
            self.vector_sum()


class SamplingAndDeRotation(PrinciplesScene):
    """00d: show how a DFT measures a frequency without iterative fitting."""

    chapter = "00d"
    heading = "程序怎样找出每个旋转圆？"
    subtitle = "等距采样、解旋与平均"

    def sampling(self) -> None:
        curve = self.curve(80, TEAL, 4.5).shift(RIGHT * 1.40)
        dots = VGroup(*[
            Dot(curve.point_from_proportion(index / 48), radius=0.028, color=LAVENDER)
            for index in range(48)
        ])
        title = self.text("第一步：沿轮廓按弧长尽量等距取 N 个点", 26).move_to(np.array([-1.2, 2.50, 0]))
        line_a = self.formula(r"z[0],\ z[1],\ \ldots,\ z[N-1]", 31, PURPLE).move_to(np.array([-2.52, -1.26, 0]))
        line_b = self.text("每个 z[n] 就是第 n 个样本点的二维坐标。", 20, GRAY).next_to(line_a, DOWN, buff=0.16)
        side = VGroup(
            self.text("画面展示 48 点", 20, GRAY),
            self.text("实际本项目用 N=1024", 20, PURPLE),
            self.text("采样更密：程序看得更细", 20, "#34454D"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.16).move_to(np.array([-2.50, 0.79, 0]))
        note = self.note(
            "采样是把连续轮廓交给程序的方式。",
            "n 是样本编号；n/N 是它沿整圈走过的比例，和前面的 t 对应。",
        )
        self.play(Create(curve), FadeIn(title), FadeIn(side), run_time=1.4)
        self.play(FadeIn(dots, lag_ratio=0.018), run_time=1.7)
        self.play(FadeIn(line_a), FadeIn(line_b), FadeIn(note), run_time=0.9)
        self.wait(1.3)
        self.clear_stage(curve, dots, title, line_a, line_b, side, note)

    def derotate(self) -> None:
        left_center = np.array([-2.75, 0.06, 0])
        right_center = np.array([2.05, 0.06, 0])
        phase = ValueTracker(0.0)
        left_circle = Circle(1.18, color="#8BA2A6", stroke_width=2).move_to(left_center)
        right_circle = Circle(1.18, color="#8BA2A6", stroke_width=2).move_to(right_center)
        original = always_redraw(lambda: Arrow(
            left_center,
            left_center + 1.05 * np.array([np.cos(2 * np.pi * 3 * phase.get_value()), np.sin(2 * np.pi * 3 * phase.get_value()), 0]),
            buff=0, color=TEAL, stroke_width=4,
        ))
        reference = always_redraw(lambda: Arrow(
            right_center,
            right_center + 1.05 * np.array([np.cos(-2 * np.pi * 3 * phase.get_value()), np.sin(-2 * np.pi * 3 * phase.get_value()), 0]),
            buff=0, color=LAVENDER, stroke_width=4,
        ))
        result = always_redraw(lambda: Arrow(
            right_center,
            right_center + 0.78 * np.array([1.0, 0.0, 0]),
            buff=0, color=TEAL, stroke_width=5,
        ))
        heading = self.text("第二步：拿一个反方向的参考圆去“解旋”", 26).move_to(np.array([0.0, 2.50, 0]))
        labels = VGroup(
            self.text("z[n] 含有 +3 速成分", 21, TEAL).next_to(left_circle, DOWN, buff=0.22),
            self.formula(r"e^{-i2\pi\cdot3\cdot n/N}", 25, LAVENDER).next_to(right_circle, DOWN, buff=0.22),
        )
        formula = self.formula(r"z[n]\cdot e^{-i2\pi kn/N}", 34, INK).move_to(np.array([0.0, -1.82, 0]))
        note = self.note(
            "若 k 测对，原来的 +3 圈和参考的 -3 圈相抵，结果不再转。",
            "这叫解旋：不是点积，而是复数相乘；几何上就是再旋转一个相反角度。",
        )
        self.play(FadeIn(VGroup(left_circle, right_circle, heading, labels, formula)), FadeIn(original), FadeIn(reference), FadeIn(result), run_time=1.4)
        self.play(phase.animate.set_value(1.0), run_time=4.6, rate_func=smootherstep)
        self.play(FadeIn(note), run_time=0.75)
        self.wait(1.3)
        self.clear_stage(left_circle, right_circle, original, reference, result, heading, labels, formula, note)

    def average_and_cancel(self) -> None:
        title = self.text("第三步：把一圈的解旋结果做平均", 26).move_to(np.array([0.0, 2.50, 0]))
        matched = VGroup(*[
            Arrow(np.array([-3.85, 0.78 - row * 0.50, 0]), np.array([-2.80, 0.78 - row * 0.50, 0]), buff=0, color=TEAL, stroke_width=4)
            for row in range(4)
        ])
        mismatched = VGroup(*[
            Arrow(np.array([1.55, -0.18, 0]), np.array([1.55, -0.18, 0]) + 0.78 * np.array([np.cos(angle), np.sin(angle), 0]), buff=0, color=LAVENDER, stroke_width=4)
            for angle in (0, np.pi / 2, np.pi, 3 * np.pi / 2)
        ])
        matched_label = self.text("测对：都朝近似同一方向", 21, TEAL).move_to(np.array([-3.0, -1.62, 0]))
        mismatch_label = self.text("测错：方向绕一圈，彼此抵消", 21, PURPLE).move_to(np.array([2.15, -1.62, 0]))
        formula = self.formula(r"c[k]=\frac{1}{N}\sum_{n=0}^{N-1}z[n]e^{-i2\pi kn/N}", 31).move_to(np.array([0.0, -1.52, 0]))
        note = self.note(
            "平均后留下的向量 c[k]：长度 |c[k]| 是这一转速有多重要，角度是它的初相位。",
            "DFT = Discrete Fourier Transform，离散傅里叶变换：N 固定时一次算完，不是训练迭代。",
        )
        matched.shift(UP * 0.22)
        mismatched.shift(UP * 0.22)
        matched_label.shift(UP * 0.30)
        mismatch_label.shift(UP * 0.30)
        group = VGroup(title, matched, mismatched, matched_label, mismatch_label, formula)
        self.play(FadeIn(title), FadeIn(matched, lag_ratio=0.13), FadeIn(mismatched, lag_ratio=0.13), run_time=1.45)
        self.play(ShowPassingFlash(matched.copy().set_stroke(TEAL, width=7), time_width=0.17), run_time=1.4)
        self.play(FadeIn(VGroup(matched_label, mismatch_label, formula, note)), run_time=0.9)
        self.wait(2.0)
        self.clear_stage(group, note)

    def frequency_grid(self) -> None:
        title = self.text("程序会对每个整数 k 都做一次这台“测速仪”", 26).move_to(np.array([0.0, 2.50, 0]))
        values = (-4, -3, -2, -1, 0, 1, 2, 3, 4)
        cards = VGroup()
        for index, value in enumerate(values):
            card = Rectangle(width=0.85, height=1.08, stroke_color=GRID, stroke_width=1.5)
            card.move_to(np.array([-4.0 + index, 0.66, 0]))
            weight = 0.92 if value in (-3, 1, 4) else 0.22
            bar = Rectangle(width=0.13, height=0.68 * weight, fill_color=TEAL if weight > 0.5 else LAVENDER, fill_opacity=1, stroke_width=0)
            bar.move_to(card.get_bottom() + UP * (0.16 + bar.height / 2))
            label = self.formula(rf"{value:+d}", 22, PURPLE).next_to(card, DOWN, buff=0.14)
            cards.add(card, bar, label)
        labels = VGroup(
            self.text("转慢", 19, GRAY).move_to(np.array([-3.0, -1.14, 0])),
            self.text("不转", 19, GRAY).move_to(np.array([0.0, -1.14, 0])),
            self.text("转快", 19, GRAY).move_to(np.array([3.0, -1.14, 0])),
        )
        note = self.note(
            "为什么只测整数 k？因为 t 从 0 到 1 恰好是一圈，整数圈能在边界自然接上。",
            "得到全部 c[k] 后，按 |c[k]| 排序；保留多少项是重建阶段的选择，不是 DFT 的迭代。",
        )
        self.play(FadeIn(title), FadeIn(cards, lag_ratio=0.05), FadeIn(labels), run_time=1.45)
        self.play(FadeIn(note), run_time=0.8)
        self.wait(1.8)
        self.clear_stage(title, cards, labels, note)

    def angle_rule(self) -> None:
        center = np.array([-2.72, 0.44, 0])
        circle = Circle(1.22, color="#8BA2A6", stroke_width=2).move_to(center)
        spokes = VGroup(*[
            Line(center, center + 1.08 * np.array([np.cos(2 * np.pi * n / 8), np.sin(2 * np.pi * n / 8), 0]), color=GRID, stroke_width=1.1)
            for n in range(8)
        ])
        reference = Arrow(center, center + 1.05 * np.array([np.cos(-2 * np.pi * 3 * 5 / 8), np.sin(-2 * np.pi * 3 * 5 / 8), 0]), buff=0, color=LAVENDER, stroke_width=4)
        marker = Dot(center + 1.26 * np.array([np.cos(2 * np.pi * 5 / 8), np.sin(2 * np.pi * 5 / 8), 0]), radius=0.06, color=TEAL)
        title = self.text("为什么参考角度写成 2πkn/N？", 27).move_to(np.array([0.0, 2.48, 0]))
        formula = self.formula(r"\theta_{k,n}=2\pi\cdot k\cdot\frac{n}{N}", 39, TEAL).move_to(np.array([2.0, 1.18, 0]))
        prose = VGroup(
            self.text("n/N：第 n 个样本已走完一圈的几分之几", 20, GRAY),
            self.text("乘 k：参考圆在这段进度里要转 k 圈", 20, PURPLE),
            self.text("乘 2π：把“一圈”换成弧度", 20, "#34454D"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.11).move_to(np.array([2.0, 0.09, 0]))
        note = self.note(
            "这里的 n 不是原图点相对原点的角度，而是“沿轮廓走到第几个采样点”的编号。",
            "因此每个样本都乘一个对应进度的参考旋转，才能检查第 k 种转速。",
        )
        self.play(FadeIn(title), FadeIn(circle), FadeIn(spokes), FadeIn(reference), FadeIn(marker), FadeIn(formula), FadeIn(prose), run_time=1.35)
        self.play(ShowPassingFlash(circle.copy().set_stroke(TEAL, width=6), time_width=0.12), run_time=1.5)
        self.play(FadeIn(note), run_time=0.75)
        self.wait(1.9)
        self.clear_stage(title, circle, spokes, reference, marker, formula, prose, note)

    def matched_number_example(self) -> None:
        title = self.text("测对时：四个解旋后的向量都指向右边", 26).move_to(np.array([0.0, 2.48, 0]))
        rows = VGroup(*[
            VGroup(
                self.formula(rf"w_3[{n}]", 24, PURPLE),
                Arrow(np.array([-0.75, 1.12 - n * 0.58, 0]), np.array([0.75, 1.12 - n * 0.58, 0]), buff=0, color=TEAL, stroke_width=4),
            )
            for n in range(4)
        ])
        average = self.formula(r"c[3]=\frac{(2,0)+(2,0)+(2,0)+(2,0)}{4}=(2,0)", 32, TEAL).move_to(np.array([0.0, -1.42, 0]))
        note = self.note(
            "每个 w_k[n] 是第 n 个点乘上反向参考圆后的临时向量。",
            "方向没有被平均掉，长度 2 留了下来：这说明 k=3 这类转速在原轨迹里很明显。",
        )
        self.play(FadeIn(title), FadeIn(rows, lag_ratio=0.12), run_time=1.3)
        self.play(ShowPassingFlash(rows.copy().set_stroke(LAVENDER, width=6), time_width=0.15), FadeIn(average), run_time=1.45)
        self.play(FadeIn(note), run_time=0.75)
        self.wait(2.1)
        self.clear_stage(title, rows, average, note)

    def mismatched_number_example(self) -> None:
        center = np.array([-2.72, 0.42, 0])
        circle = Circle(1.15, color="#8BA2A6", stroke_width=2).move_to(center)
        arrows = VGroup(*[
            Arrow(center, center + 0.92 * np.array([np.cos(angle), np.sin(angle), 0]), buff=0, color=LAVENDER, stroke_width=4)
            for angle in (0, np.pi / 2, np.pi, 3 * np.pi / 2)
        ])
        title = self.text("测错时：原本 +5 速，却用 −3 速去解旋", 26).move_to(np.array([0.0, 2.48, 0]))
        formula = self.formula(r"e^{i2\pi\cdot5t}\cdot e^{-i2\pi\cdot3t}=e^{i2\pi(5-3)t}=e^{i2\pi\cdot2t}", 30, TEAL).move_to(np.array([1.60, 0.96, 0]))
        prose = VGroup(
            self.text("剩下 +2 速，仍会绕圈。", 22, PURPLE),
            self.text("一圈内平均时，四个方向互相抵消。", 21, GRAY),
            self.formula(r"c[3]\approx0", 31, "#34454D"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.11).move_to(np.array([1.60, -0.38, 0]))
        note = self.note(
            "“静下来多少”通过平均后的 |c[k]| 定量判断：越接近 0，说明这个 k 越不像原轨迹的组成部分。",
            "这就是 DFT 的核心：对每个整数速度做一次同样的测量，再得到全部系数。",
        )
        self.play(FadeIn(title), FadeIn(circle), FadeIn(arrows, lag_ratio=0.13), FadeIn(formula), FadeIn(prose), run_time=1.35)
        self.play(ShowPassingFlash(circle.copy().set_stroke(TEAL, width=6), time_width=0.14), run_time=1.55)
        self.play(FadeIn(note), run_time=0.8)
        self.wait(2.0)
        self.clear_stage(title, circle, arrows, formula, prose, note)

    def dft_flow(self) -> None:
        title = self.text("把 DFT 看成一条固定的计算流水线", 27).move_to(np.array([0.0, 2.48, 0]))
        labels = ("1. 沿轮廓取 N 点", "2. 选一个整数 k", "3. 乘反向参考圆", "4. 对 N 个结果平均")
        boxes = VGroup(*[
            Rectangle(width=2.12, height=0.74, stroke_color=TEAL if index in (0, 3) else LAVENDER, stroke_width=2).move_to(np.array([-3.55 + index * 2.36, 0.82, 0]))
            for index in range(4)
        ])
        copy = VGroup(*[
            self.text(label, 18, "#34454D").move_to(box)
            for label, box in zip(labels, boxes)
        ])
        arrows = VGroup(*[
            Arrow(boxes[index].get_right() + RIGHT * 0.05, boxes[index + 1].get_left() + LEFT * 0.05, buff=0.04, color=GRID, stroke_width=2)
            for index in range(3)
        ])
        formula = self.formula(r"X[k]=\sum_{n=0}^{N-1}x[n]e^{-i2\pi kn/N}", 33, INK).move_to(np.array([0.0, -0.86, 0]))
        note = self.note(
            "DFT 的全称是 Discrete Fourier Transform：对离散的 N 个输入点，给出 N 个频率结果 X[k]。",
            "N 一旦选定，程序不需要猜测或反复训练；只是依次检查每个 k，并用同一条公式求和。",
        )
        self.play(FadeIn(title), FadeIn(boxes, lag_ratio=0.12), FadeIn(copy, lag_ratio=0.12), FadeIn(arrows), run_time=1.45)
        self.play(FadeIn(formula), FadeIn(note), run_time=0.85)
        self.wait(2.6)
        self.clear_stage(title, boxes, copy, arrows, formula, note)

    def choosing_resolution(self) -> None:
        title = self.text("人真正要决定的，是观察精度，而不是让程序猜答案", 26).move_to(np.array([0.0, 2.48, 0]))
        values = VGroup(
            self.formula(r"N=256", 34, PURPLE),
            self.formula(r"N=1024", 34, TEAL),
            self.formula(r"N=4096", 34, LAVENDER),
        ).arrange(RIGHT, buff=1.0).move_to(np.array([0.0, 0.86, 0]))
        captions = VGroup(
            self.text("轮廓较粗", 20, GRAY),
            self.text("本项目的采样数", 20, TEAL),
            self.text("更多细节，也更耗计算", 20, GRAY),
        )
        for caption, value in zip(captions, values):
            caption.next_to(value, DOWN, buff=0.24)
        rule = Line(np.array([-4.0, -1.12, 0]), np.array([4.0, -1.12, 0]), color=GRID, stroke_width=2)
        note = self.note(
            "若轮廓太粗糙，就提高 N 后重新采样、重新计算；这是一轮新的固定计算，不是 DFT 在内部迭代到收敛。",
            "之后仍可独立选择保留多少个 c[k] 来画图，别把“采样数 N”和“保留项数”混为一谈。",
        )
        self.play(FadeIn(title), FadeIn(values, lag_ratio=0.12), FadeIn(captions, lag_ratio=0.12), Create(rule), run_time=1.35)
        self.play(ShowPassingFlash(rule.copy().set_stroke(TEAL, width=6), time_width=0.14), run_time=1.25)
        self.play(FadeIn(note), run_time=0.8)
        self.wait(2.35)
        self.clear_stage(title, values, captions, rule, note)

    def construct(self) -> None:
        with register_font(font_path()):
            self.setup_scene()
            self.sampling()
            self.derotate()
            self.angle_rule()
            self.average_and_cancel()
            self.matched_number_example()
            self.mismatched_number_example()
            self.frequency_grid()
            self.dft_flow()
            self.choosing_resolution()


class Reconstruction(PrinciplesScene):
    """00e: sort the measured coefficients and reconstruct the contour."""

    chapter = "00e"
    heading = "最后，把测到的圆按重要程度放回来"
    subtitle = "从 1 项到 80 项的重建"

    def spectrum_sort(self) -> None:
        heading = self.text("DFT 已经一次算出了所有 c[k]", 27).move_to(np.array([0.0, 2.50, 0]))
        bars = VGroup()
        heights = (0.30, 0.52, 1.52, 0.44, 0.28, 1.16, 0.67, 0.22, 0.93, 0.38, 0.17)
        for index, height in enumerate(heights):
            x = -4.5 + index * 0.9
            bar = Rectangle(width=0.42, height=height, fill_color=TEAL if height > 0.8 else LAVENDER, fill_opacity=1, stroke_width=0)
            bar.move_to(np.array([x, -0.11 + height / 2, 0]))
            bars.add(bar)
        baseline = Line(np.array([-4.85, -0.11, 0]), np.array([4.85, -0.11, 0]), color=GRID, stroke_width=2)
        formula = VGroup(
            self.formula(r"|c[k]|", 32, INK),
            self.text("越大，说明第 k 种转速越重要", 21, INK),
        ).arrange(RIGHT, buff=0.18).move_to(np.array([0.0, -1.08, 0]))
        note = self.note(
            "我们不必按 k 的数字顺序画圆，而是先放回影响最大的项。",
            "大的慢转项先决定整体姿态；较小的快转项再补头发、鞋子和局部转折。",
        )
        self.play(FadeIn(heading), FadeIn(baseline), FadeIn(bars, lag_ratio=0.055), run_time=1.5)
        self.play(FadeIn(formula), FadeIn(note), run_time=0.9)
        self.wait(1.6)
        self.clear_stage(heading, bars, baseline, formula, note)

    def progressive_reconstruction(self) -> None:
        counts = (1, 5, 25, 80)
        target = self.curve(80, "#D7E1E2", 1.5, 0.96).shift(RIGHT * 1.42 + UP * 0.25)
        current = self.curve(counts[0], TEAL, 4.8).shift(RIGHT * 1.42 + UP * 0.25)
        title = self.text("同一批 c[k]，只改变“保留多少项”", 27).move_to(np.array([-0.6, 2.50, 0]))
        count_label = self.text("1 项：先抓住最粗的大形状", 23, PURPLE).move_to(np.array([-1.7, -1.48, 0]))
        track = Rectangle(width=4.55, height=0.21, stroke_color=GRID, stroke_width=1.4).move_to(np.array([-2.55, -2.04, 0]))
        fill = Rectangle(width=0.10, height=0.13, fill_color=TEAL, fill_opacity=1, stroke_width=0).align_to(track, LEFT).move_to(np.array([-4.78, -2.04, 0]), aligned_edge=LEFT)
        note = self.note(
            "这不是重新计算，也不是不断试错。",
            "系数早已算好；我们只是从排序结果中拿 1、5、25、80 项来相加。",
        )
        self.play(FadeIn(target), FadeIn(title), FadeIn(count_label), FadeIn(track), FadeIn(fill), Create(current), run_time=1.65)
        descriptions = {
            5: "5 项：身体、头部开始成形",
            25: "25 项：主要弯曲和姿态出现",
            80: "80 项：补上较小的轮廓细节",
        }
        for count in counts[1:]:
            next_curve = self.curve(count, TEAL, 4.8).shift(RIGHT * 1.42 + UP * 0.25)
            next_label = self.text(descriptions[count], 23, PURPLE).move_to(count_label)
            ratio = count / 80
            next_fill = Rectangle(width=max(0.10, 4.35 * ratio), height=0.13, fill_color=TEAL, fill_opacity=1, stroke_width=0)
            next_fill.align_to(track, LEFT).move_to(np.array([-4.78 + 2.17 * ratio, -2.04, 0]))
            self.play(Transform(count_label, next_label), run_time=0.38, rate_func=smootherstep)
            self.play(Transform(fill, next_fill), Transform(current, next_curve), run_time=1.25, rate_func=smootherstep)
            self.wait(1.17)
        self.play(FadeIn(note), run_time=0.75)
        self.wait(1.65)
        self.clear_stage(target, current, title, count_label, track, fill, note)

    def low_and_high_frequency(self) -> None:
        baseline = VGroup(
            Line(np.array([-4.75, 0.82, 0]), np.array([4.75, 0.82, 0]), color=GRID, stroke_width=1.4),
            Line(np.array([-4.75, -0.80, 0]), np.array([4.75, -0.80, 0]), color=GRID, stroke_width=1.4),
        )
        slow = self.wave(0.82, ((1, 0.46),), TEAL)
        detailed = self.wave(-0.80, ((1, 0.46), (8, 0.14)), LAVENDER)
        title = self.text("慢转先决定大形状，快转再补局部细节", 27).move_to(np.array([0.0, 2.48, 0]))
        labels = VGroup(
            self.text("低频：整体起伏、身体大轮廓", 21, TEAL).move_to(np.array([-2.90, 1.79, 0])),
            self.text("高频：头发、鞋子、细小转折", 21, PURPLE).move_to(np.array([-2.90, -1.52, 0])),
        )
        note = self.note(
            "所以按 |c[k]| 从大到小加入时，人物会先有姿态，再逐渐出现细节。",
            "这不是硬性规定圆要由大到小：只是这个轮廓的主要低频项通常比较强。",
        )
        self.play(FadeIn(title), FadeIn(baseline), FadeIn(labels), Create(slow), run_time=1.35)
        self.play(Create(detailed), run_time=2.3)
        self.play(ShowPassingFlash(detailed.copy().set_stroke(TEAL, width=6), time_width=0.12), run_time=1.4)
        self.play(FadeIn(note), run_time=0.75)
        self.wait(1.8)
        self.clear_stage(title, baseline, slow, detailed, labels, note)

    def sample_count_and_term_count(self) -> None:
        left_curve = self.curve(80, TEAL, 3.6).scale(0.48).move_to(np.array([-2.65, 0.66, 0]))
        right_curve = self.curve(80, TEAL, 3.6).scale(0.48).move_to(np.array([2.65, 0.66, 0]))
        samples = VGroup(*[Dot(left_curve.point_from_proportion(index / 20), radius=0.03, color=LAVENDER) for index in range(20)])
        rings = VGroup(*[Circle(0.20 + index * 0.07, color=TEAL if index < 2 else LAVENDER, stroke_width=1.3).move_to(np.array([2.65, 0.46, 0])) for index in range(4)])
        title = self.text("不要混淆两个数量", 27).move_to(np.array([0.0, 2.48, 0]))
        labels = VGroup(
            self.text("N=1024：先从原线取多少样本", 21, PURPLE).move_to(np.array([-2.65, -1.12, 0])),
            self.text("80 项：重画时放回多少个圆", 21, TEAL).move_to(np.array([2.65, -1.12, 0])),
        )
        note = self.note(
            "提高 N 是让程序更细地观察原线；增加保留项数是让重建结果放回更多已算出的频率。",
            "N 固定后 DFT 的计算流程固定；觉得细节不够时，人可以选择更大的 N 再重新计算。",
        )
        self.play(FadeIn(title), FadeIn(left_curve), FadeIn(right_curve), FadeIn(labels), run_time=1.1)
        self.play(FadeIn(samples, lag_ratio=0.04), FadeIn(rings, lag_ratio=0.16), run_time=1.65)
        self.play(FadeIn(note), run_time=0.75)
        self.wait(2.2)
        self.clear_stage(title, left_curve, right_curve, samples, rings, labels, note)

    def why_a_basis_works(self) -> None:
        title = self.text("为什么许多圆周运动能逼近任意闭合轮廓？", 27).move_to(np.array([0.0, 2.48, 0]))
        left = self.wave(0.80, ((1, 0.34),), "#84909A")
        middle = self.wave(0.08, ((3, 0.25),), LAVENDER)
        right = self.wave(-0.64, ((1, 0.34), (3, 0.25), (7, 0.12)), TEAL)
        guides = VGroup(*[
            Line(np.array([-4.8, y, 0]), np.array([-1.35, y, 0]), color=GRID, stroke_width=1.3)
            for y in (0.80, 0.08, -0.64)
        ])
        labels = VGroup(
            self.text("低频波", 19, GRAY).move_to(np.array([-4.14, 1.34, 0])),
            self.text("中频波", 19, PURPLE).move_to(np.array([-4.14, 0.62, 0])),
            self.text("叠加形状", 19, TEAL).move_to(np.array([-4.02, -0.08, 0])),
        )
        formula = self.formula(r"z(t)\approx\sum_k c[k]e^{i2\pi kt}", 34, INK).move_to(np.array([2.05, 1.06, 0]))
        note = self.note(
            "这些不同整数速度的转动，像一套“拼形状的基础积木”：每块互不混淆，DFT 能分别测出它的权重。",
            "对普通、足够平滑的闭合曲线，保留的项越多，叠加结果就越接近原线；这是傅里叶级数的结论。",
        )
        self.play(FadeIn(title), FadeIn(guides), Create(left), FadeIn(labels[0]), run_time=1.35)
        self.play(Create(middle), FadeIn(labels[1]), run_time=1.3)
        self.play(Create(right), FadeIn(labels[2]), FadeIn(formula), run_time=1.5)
        self.play(FadeIn(note), run_time=0.8)
        self.wait(2.2)
        self.clear_stage(title, guides, left, middle, right, labels, formula, note)

    def coefficient_geometry(self) -> None:
        center = np.array([-2.72, 0.19, 0])
        circle = Circle(1.16, color="#8BA2A6", stroke_width=2).move_to(center)
        vector = Arrow(center, center + 0.92 * np.array([np.cos(0.78), np.sin(0.78), 0]), buff=0, color=TEAL, stroke_width=4)
        radius = DashedLine(center, vector.get_end(), color=LAVENDER, stroke_width=1.7)
        title = self.text("一个系数 c[k] 同时装下半径和初始方向", 26).move_to(np.array([0.0, 2.48, 0]))
        formula = self.formula(r"c[k]=r_k e^{i\varphi_k}", 40, TEAL).move_to(np.array([2.02, 0.86, 0]))
        prose = VGroup(
            self.text("rₖ = |c[k]|：这根箭头有多长", 21, PURPLE),
            self.text("φₖ = arg(c[k])：它从哪个角度出发", 21, GRAY),
            self.text("k：之后每圈里转几圈、往哪个方向转", 21, "#34454D"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.16).move_to(np.array([2.02, -0.38, 0]))
        note = self.note(
            "因此 c[k] 不是单纯的“权重数字”：它是二维向量，长度决定影响强弱，角度决定初相位。",
            "把所有 c[k] 配上自己的 k 后，就得到了完整的旋转圆清单。",
        )
        self.play(FadeIn(title), FadeIn(circle), FadeIn(vector), FadeIn(radius), FadeIn(formula), FadeIn(prose), run_time=1.25)
        self.play(ShowPassingFlash(vector.copy().set_stroke(LAVENDER, width=7), time_width=0.15), run_time=1.25)
        self.play(FadeIn(note), run_time=0.75)
        self.wait(2.25)
        self.clear_stage(title, circle, vector, radius, formula, prose, note)

    def reconstruction_tradeoff(self) -> None:
        target = self.curve(80, "#D7E1E2", 1.4, 0.9).shift(RIGHT * 1.35 + UP * 0.28)
        few = self.curve(5, LAVENDER, 3.5).shift(RIGHT * 1.35 + UP * 0.28)
        many = self.curve(80, TEAL, 4.4).shift(RIGHT * 1.35 + UP * 0.28)
        title = self.text("保留多少项，是“形状精度”和“微小抖动”的取舍", 26).move_to(np.array([0.0, 2.48, 0]))
        label = self.text("5 项：姿态可见，但局部还很粗", 21, PURPLE).move_to(np.array([-2.30, -1.42, 0]))
        note = self.note(
            "少量项像画速写：保留大形状，主动忽略细枝末节；更多项会还原更多细节，也可能保留原图的噪声。",
            "本项目展示 80 项，不是唯一正确答案，而是观察效果后选择的平衡点。",
        )
        self.play(FadeIn(title), FadeIn(target), Create(few), FadeIn(label), run_time=1.45)
        next_label = self.text("80 项：轮廓更接近原线，也更忠实地保留细节", 21, TEAL).move_to(label)
        self.play(Transform(few, many), Transform(label, next_label), run_time=2.5, rate_func=smootherstep)
        self.play(FadeIn(note), run_time=0.8)
        self.wait(2.3)
        self.clear_stage(title, target, few, label, note)

    def epicycle_return(self) -> None:
        origin = np.array([-3.76, -0.31, 0])
        phase = ValueTracker(0.0)
        chain = always_redraw(lambda: self.epicycle_group(phase.get_value(), 10, origin, 0.73))
        tip = always_redraw(lambda: Dot(self.endpoint(phase.get_value(), 10, origin, 0.73), radius=0.06, color=TEAL))
        trace = VMobject()
        history: deque[np.ndarray] = deque()

        def update_trace(mob: VMobject, dt: float) -> None:
            del dt
            point = self.endpoint(phase.get_value(), 10, origin, 0.73)
            if not history or np.linalg.norm(point - history[-1]) > 0.035:
                history.append(point)
            if len(history) > 245:
                history.popleft()
            if len(history) > 2:
                mob.set_points_smoothly(np.array(history)).set_stroke(TEAL, width=3.7, opacity=0.94)

        trace.add_updater(update_trace)
        title = self.text("每个圆的末端接下一个圆的圆心", 26).move_to(np.array([0.0, 2.50, 0]))
        copy = VGroup(
            self.text("所有旋转向量相加", 22, PURPLE),
            self.text("最后一个末端留下轨迹", 22, TEAL),
            self.text("轨迹逐步接近原来的闭合轮廓", 20, GRAY),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.16).move_to(np.array([2.25, 0.72, 0]))
        formula = self.formula(r"z(t)\approx\sum_k c[k]e^{i2\pi kt}", 33, INK).move_to(np.array([1.85, -1.28, 0]))
        finish = self.note(
            "一条轮廓不是神秘地“变成圆”：它被记录为一组不同速度、半径和初相位的旋转向量。",
            "接下来看到的 01–03，就是把这一计算结果变成不同的描线、色块与姿态动画。",
        )
        self.play(FadeIn(title), FadeIn(chain), FadeIn(tip), FadeIn(copy), FadeIn(formula), run_time=1.4)
        self.add(trace)
        self.play(phase.animate.set_value(1.2), run_time=6.0, rate_func=smootherstep)
        trace.clear_updaters()
        self.play(FadeIn(finish), run_time=0.8)
        self.wait(2.2)
        self.clear_stage(title, chain, tip, trace, copy, formula, finish, duration=0.85)

    def construct(self) -> None:
        with register_font(font_path()):
            self.setup_scene()
            self.spectrum_sort()
            self.low_and_high_frequency()
            self.sample_count_and_term_count()
            self.why_a_basis_works()
            self.coefficient_geometry()
            self.progressive_reconstruction()
            self.reconstruction_tradeoff()
            self.epicycle_return()
