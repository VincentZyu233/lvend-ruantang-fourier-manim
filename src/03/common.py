"""Shared geometry and live-ink helpers for the 09/10 experiments."""

from __future__ import annotations

import colorsys
import runpy
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from psd_tools import PSDImage
from manim import (
    BLACK,
    Create,
    FadeIn,
    Group,
    ImageMobject,
    LaggedStart,
    Scene,
    VGroup,
    VMobject,
    ValueTracker,
    config,
)
from manim.utils.color import color_to_rgb, rgb_to_color


PROJECT = Path(__file__).resolve().parents[2]
PSD_PATH = PROJECT / "素材捏" / "略ndoc的软糖动画" / "1775818328351.psd"
BASE = runpy.run_path(str(PROJECT / "src" / "02" / "video_transform.py"))
build_video_poses = BASE["build_poses"]
resample_closed = BASE["resample_closed"]

INK = "#171717"
TEAL = "#12B8A6"
GHOST = "#84909A"


def boost_colors(group: VGroup, saturation: float = 1.3) -> VGroup:
    """Keep 06's clean polygon masks while making the fills more present."""
    result = group.copy()
    for item in result.get_family():
        if not isinstance(item, VMobject) or item.get_fill_opacity() <= 0:
            continue
        red, green, blue = color_to_rgb(item.get_fill_color())
        hue, value_saturation, value = colorsys.rgb_to_hsv(red, green, blue)
        if value_saturation < 0.035:
            continue
        item.set_fill(rgb_to_color(colorsys.hsv_to_rgb(hue, min(1.0, value_saturation * saturation), value)))
    return result.set_z_index(-1)


def video_assets() -> tuple[list[VGroup], list[VGroup]]:
    lines, colors = build_video_poses()
    return lines, [boost_colors(group) for group in colors]


def leaf_layers(layer) -> list:
    if getattr(layer, "is_group", lambda: False)():
        leaves = []
        for child in layer:
            leaves.extend(leaf_layers(child))
        return leaves
    return [layer]


def psd_pose_groups(psd: PSDImage) -> list:
    found = {}

    def walk(layer) -> None:
        name = getattr(layer, "name", "")
        if name.startswith("图层组") and name[3:].isdigit():
            found[int(name[3:])] = layer
        if getattr(layer, "is_group", lambda: False)():
            for child in layer:
                walk(child)

    for top_level in psd:
        walk(top_level)
    if len(found) != 10:
        raise RuntimeError(f"Expected ten PSD pose groups, found {sorted(found)}")
    return [found[index] for index in range(10, 0, -1)]


def composite_group(group, size: tuple[int, int]) -> Image.Image:
    canvas = Image.new("RGBA", size, (255, 255, 255, 0))
    for layer in reversed(leaf_layers(group)):
        canvas.alpha_composite(layer.topil().convert("RGBA"))
    return canvas


def extract_psd_contours(image: Image.Image, maximum: int = 18) -> list[np.ndarray]:
    rgba = np.asarray(image)
    alpha, rgb = rgba[:, :, 3], rgba[:, :, :3]
    ink = ((alpha > 24) & (rgb.min(axis=2) < 190)).astype(np.uint8) * 255
    contours, _ = cv2.findContours(ink, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    selected = []
    for contour in contours:
        perimeter = cv2.arcLength(contour, True)
        if perimeter >= 38 and len(contour) >= 8:
            selected.append((float(perimeter), contour.reshape(-1, 2)))
    selected.sort(key=lambda item: item[0], reverse=True)
    return [points for _, points in selected[:maximum]]


def reorder_for_transform(previous: list[np.ndarray], current: list[np.ndarray]) -> list[np.ndarray]:
    def descriptor(points: np.ndarray) -> np.ndarray:
        x, y, width, height = cv2.boundingRect(points.astype(np.float32))
        return np.array([x + width / 2, y + height / 2, width * height], dtype=float)

    available = list(range(len(current)))
    ordered: list[np.ndarray] = []
    scale = np.array([1080.0, 1080.0, 1080.0 * 1080.0])
    for source in previous[: len(current)]:
        index = min(available, key=lambda item: np.linalg.norm((descriptor(current[item]) - descriptor(source)) / scale))
        ordered.append(current[index])
        available.remove(index)
    ordered.extend(current[index] for index in available)
    return ordered


def points_to_path(points: np.ndarray, width: int, height: int) -> VMobject:
    # Fewer anchors than 06 keep the twelve short experiments responsive.
    curve = resample_closed(points, min(480, max(96, len(points))))
    scene_points = np.column_stack((
        (curve[:, 0] / width - 0.5) * 7.45,
        (0.5 - curve[:, 1] / height) * 7.45,
        np.zeros(len(curve)),
    ))
    path = VMobject(stroke_color=INK, stroke_width=2.15, fill_opacity=0)
    path.set_points_smoothly(np.vstack((scene_points, scene_points[0])))
    return path


def psd_paint_layer(image: Image.Image) -> Group:
    """Paint closed PSD ink regions with the video palette, without pose mismatch."""
    rgba = np.asarray(image)
    height, width = rgba.shape[:2]
    ink = ((rgba[:, :, 3] > 24) & (rgba[:, :, :3].min(axis=2) < 190)).astype(np.uint8) * 255
    barriers = cv2.dilate(ink, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    count, labels, stats, centroids = cv2.connectedComponentsWithStats(255 - barriers)
    painted = np.zeros((height, width, 4), dtype=np.uint8)
    for label in range(1, count):
        x, y, region_width, region_height, area = stats[label]
        center_x, center_y = centroids[label]
        # The outside paper region is the only component touching a canvas edge.
        if x == 0 or y == 0 or x + region_width >= width or y + region_height >= height:
            continue
        if not 90 <= area <= width * height * 0.14:
            continue
        relative_y = center_y / height
        relative_x = center_x / width
        if relative_y < 0.34:
            continue  # hair stays white
        if relative_y < 0.55 and 0.25 < relative_x < 0.75:
            color = (255, 223, 202, 225)  # face and blush-family regions
        elif relative_y < 0.67:
            color = (215, 194, 255, 235)  # scarf
        elif relative_y < 0.86:
            color = (184, 166, 225, 225)  # coat/shadow
        else:
            color = (147, 124, 192, 225)
        painted[labels == label] = color
    return Group(ImageMobject(painted).set_height(7.45).set_z_index(-1))


def psd_assets(video_colors: list[VGroup]) -> tuple[list[VGroup], list[Group]]:
    """Select five PSD groups and build pose-aligned paint from the video palette."""
    psd = PSDImage.open(PSD_PATH)
    source_groups = psd_pose_groups(psd)
    selected_indices = (0, 2, 4, 6, 8)
    images = [composite_group(source_groups[index], psd.size) for index in selected_indices]
    raw_poses = [extract_psd_contours(image) for image in images]
    ordered = [raw_poses[0]]
    for pose in raw_poses[1:]:
        ordered.append(reorder_for_transform(ordered[-1], pose))
    line_poses = [VGroup(*[points_to_path(points, *psd.size) for points in pose]) for pose in ordered]
    return line_poses, [psd_paint_layer(image) for image in images]


def _partial(target: VMobject, source: VMobject, start: float, end: float) -> None:
    if end <= start:
        target.set_opacity(0)
        return
    target.set_opacity(1)
    target.pointwise_become_partial(source, max(0.0, start), min(1.0, end))


def live_write(scene: Scene, paths: VGroup, run_time: float, tail: float, stagger: float) -> VGroup:
    """A cyan cursor writes permanent black ink along every contour."""
    permanent = VGroup()
    cursor = VGroup()
    records: list[tuple[VMobject, VMobject, VMobject, float]] = []
    total = max(1, len(paths))
    for index, source in enumerate(paths):
        ink = source.copy().set_stroke(INK, width=2.15, opacity=1).set_z_index(0)
        ink.pointwise_become_partial(source, 0, 0)
        glow = source.copy().set_stroke(TEAL, width=5.1, opacity=0.95).set_z_index(2)
        glow.pointwise_become_partial(source, 0, 0)
        permanent.add(ink)
        cursor.add(glow)
        records.append((source, ink, glow, stagger * (index / max(1, total - 1))))

    progress = ValueTracker(0.0)

    def update(_group: VGroup) -> None:
        value = progress.get_value()
        for source, ink, glow, delay in records:
            local = np.clip((value - delay) / max(0.001, 1.0 - delay), 0.0, 1.0)
            _partial(ink, source, 0.0, local)
            _partial(glow, source, max(0.0, local - tail), local)

    cursor.add_updater(update)
    scene.add(permanent, cursor)
    scene.play(progress.animate.set_value(1.0), run_time=run_time)
    cursor.remove_updater(update)
    scene.remove(cursor)
    return permanent


def ambient_cursor(scene: Scene, paths: VGroup, duration: float, tail: float, lanes: int = 1) -> None:
    """Keep one or more short cyan highlights travelling after the drawing settles."""
    strips = VGroup()
    records = []
    for index, source in enumerate(paths):
        for lane in range(lanes):
            first = source.copy().set_stroke(TEAL, width=4.3, opacity=0).set_z_index(2)
            second = source.copy().set_stroke(TEAL, width=4.3, opacity=0).set_z_index(2)
            strips.add(first, second)
            records.append((source, first, second, (index / max(1, len(paths)) + lane / lanes) % 1.0))
    clock = ValueTracker(0.0)

    def update(_group: VGroup) -> None:
        time = clock.get_value()
        for source, first, second, offset in records:
            end = (time * 1.35 + offset) % 1.0
            start = end - tail
            if start >= 0:
                _partial(first, source, start, end)
                second.set_opacity(0)
            else:
                _partial(first, source, 0, end)
                _partial(second, source, 1 + start, 1)

    strips.add_updater(update)
    scene.add(strips)
    scene.play(clock.animate.set_value(1.0), run_time=duration)
    strips.remove_updater(update)
    scene.remove(strips)


def flood_colors(scene: Scene, colors: VGroup, run_time: float = 0.9) -> None:
    scene.play(
        LaggedStart(*(FadeIn(block, scale=0.975) for block in colors), lag_ratio=0.035),
        run_time=run_time,
    )


def configure_canvas() -> None:
    config.pixel_width = 720
    config.pixel_height = 720
    config.frame_width = 8
    config.frame_height = 8
    config.frame_rate = 20
    config.background_color = "#FFFFFF"


def native_create(scene: Scene, paths: VGroup, style: str, duration: float) -> None:
    """Use Manim's own elegant path growth, grouped only for drawing rhythm."""
    if style == "cascade":
        scene.play(LaggedStart(*(Create(path) for path in paths), lag_ratio=0.085), run_time=duration)
        return
    sections = 4
    chunk_size = max(1, int(np.ceil(len(paths) / sections)))
    groups = [VGroup(*paths[index:index + chunk_size]) for index in range(0, len(paths), chunk_size)]
    if style == "outline_first":
        weights = [0.34] + [(1 - 0.34) / max(1, len(groups) - 1)] * max(0, len(groups) - 1)
    else:
        weights = [1 / len(groups)] * len(groups)
    for group, weight in zip(groups, weights):
        scene.play(LaggedStart(*(Create(path) for path in group), lag_ratio=0.12), run_time=duration * weight)
