"""A smoother ManimCE alternative to 05's JAnim shape matching experiment.

The source video is sampled at five poses.  Each ink contour retains a dense
Fourier reconstruction and becomes a smooth Bezier VMobject.  Manim's explicit
Transform then morphs the ranked contours, while color-only raster layers fade
between poses.
"""

from __future__ import annotations

import colorsys
from pathlib import Path

import cv2
import numpy as np
from manim import (
    BLACK,
    WHITE,
    Create,
    FadeIn,
    FadeOut,
    Group,
    ImageMobject,
    LaggedStart,
    Scene,
    Transform,
    VGroup,
    VMobject,
    config,
)


PROJECT = Path(__file__).resolve().parents[2]
VIDEO_PATH = PROJECT / "素材捏" / "略ndoc的软糖动画" / "某种软糖.mp4"
ARTIFACT_DIR = PROJECT / "build" / "02_video_fourier"
SAMPLE_TIMES = (0.55, 2.0, 3.45, 4.9, 6.35)
PATH_COUNT = 12
SATURATION_FACTOR = 1.28

config.pixel_width = 720
config.pixel_height = 720
config.frame_width = 8
config.frame_height = 8
config.frame_rate = 20
config.background_color = WHITE


def resample_closed(points: np.ndarray, count: int) -> np.ndarray:
    points = np.asarray(points, dtype=np.float64)
    if not np.allclose(points[0], points[-1]):
        points = np.vstack((points, points[0]))
    lengths = np.linalg.norm(np.diff(points, axis=0), axis=1)
    distance = np.r_[0.0, np.cumsum(lengths)]
    locations = np.linspace(0.0, distance[-1], count, endpoint=False)
    return np.column_stack((
        np.interp(locations, distance, points[:, 0]),
        np.interp(locations, distance, points[:, 1]),
    ))


def fourier_smooth(points: np.ndarray, samples: int = 1728, terms: int = 540) -> np.ndarray:
    """Preserve enough Fourier terms for curved hair, clothing, and face details."""
    curve = resample_closed(points, samples)
    signal = curve[:, 0] + 1j * curve[:, 1]
    spectrum = np.fft.fft(signal)
    filtered = np.zeros_like(spectrum)
    filtered[np.argsort(np.abs(spectrum))[-terms:]] = spectrum[np.argsort(np.abs(spectrum))[-terms:]]
    reconstruction = np.fft.ifft(filtered)
    return np.column_stack((reconstruction.real, reconstruction.imag))


def read_frame(capture: cv2.VideoCapture, seconds: float) -> np.ndarray:
    capture.set(cv2.CAP_PROP_POS_MSEC, seconds * 1000)
    ok, frame = capture.read()
    if not ok:
        raise RuntimeError(f"Could not sample {VIDEO_PATH.name} at {seconds:.2f}s")
    return frame


def extract_contours(frame: np.ndarray) -> list[np.ndarray]:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    ink = (gray < 112).astype(np.uint8) * 255
    contours, _ = cv2.findContours(ink, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    found: list[tuple[float, np.ndarray]] = []
    for contour in contours:
        perimeter = cv2.arcLength(contour, True)
        if perimeter < 58:
            continue
        points = contour.reshape(-1, 2)
        if len(points) >= 8:
            found.append((float(perimeter), fourier_smooth(points)))
    found.sort(key=lambda entry: entry[0], reverse=True)
    if len(found) < PATH_COUNT:
        raise RuntimeError(f"Only found {len(found)} usable paths; expected at least {PATH_COUNT}")
    return [points for _, points in found[:PATH_COUNT]]


def clean_mask(mask: np.ndarray, minimum_area: int) -> np.ndarray:
    """Remove codec speckles before extracting a color region's exterior curve."""
    source = mask.astype(np.uint8) * 255
    source = cv2.morphologyEx(source, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    source = cv2.morphologyEx(source, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(source)
    result = np.zeros_like(source)
    for label in range(1, count):
        if stats[label, cv2.CC_STAT_AREA] >= minimum_area:
            result[labels == label] = 255
    return result


def polygon_from_contour(contour: np.ndarray, width: int, height: int, color: str) -> VMobject:
    points = contour.reshape(-1, 2)
    perimeter = cv2.arcLength(contour, True)
    # Dense anchors preserve the organic source contour without retaining pixel noise.
    count = min(280, max(28, int(perimeter / 4.0)))
    curve = resample_closed(points, count)
    scene_points = np.column_stack((
        (curve[:, 0] / width - 0.5) * 7.45,
        (0.5 - curve[:, 1] / height) * 7.45,
        np.zeros(len(curve)),
    ))
    block = VMobject(fill_color=boost_hex_color(color), fill_opacity=1, stroke_opacity=0)
    block.set_points_smoothly(np.vstack((scene_points, scene_points[0])))
    return block


def boost_hex_color(color: str, factor: float = SATURATION_FACTOR) -> str:
    """Apply the study-wide palette boost while leaving black and white intact."""
    red, green, blue = (int(color[index:index + 2], 16) / 255 for index in (1, 3, 5))
    hue, saturation, value = colorsys.rgb_to_hsv(red, green, blue)
    red, green, blue = colorsys.hsv_to_rgb(hue, min(1.0, saturation * factor), value)
    return "#%02X%02X%02X" % tuple(round(channel * 255) for channel in (red, green, blue))


def clean_color_rgba(frame: np.ndarray, *, include_soft_shadows: bool = True) -> np.ndarray:
    """Extract source-faithful fills as a transparent raster."""
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    saturation, value = hsv[:, :, 1], hsv[:, :, 2]
    grayscale = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

    # Preserve original flat colours plus the soft violet/grey shadow language,
    # while cutting away the white paper and pale corner watermark.
    colour_fill = (saturation >= 11) & (value < 250) & (grayscale >= 92)
    soft_shadow = (saturation >= 4) & (value < 230) & (grayscale >= 125)
    if not include_soft_shadows:
        soft_shadow = np.zeros_like(soft_shadow)

    # Keep thick black artwork (eyebrows, eyes and shoes) by measuring ink
    # thickness, instead of requiring it to be a disconnected component.  A
    # brow often touches nearby line art after H.264 compression, which made
    # the former connected-component rule incorrectly discard it.
    dark_ink = (grayscale < 70).astype(np.uint8)
    ink_thickness = cv2.distanceTransform(dark_ink, cv2.DIST_L2, 5)
    solid_core = (ink_thickness >= 3.25).astype(np.uint8) * 255
    solid_detail = cv2.dilate(
        solid_core,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)),
    ).astype(bool) & dark_ink.astype(bool)

    boosted = hsv.copy()
    boosted[:, :, 1] = np.minimum(255, boosted[:, :, 1].astype(np.float32) * 1.12).astype(np.uint8)
    return np.dstack((
        cv2.cvtColor(boosted, cv2.COLOR_HSV2RGB),
        np.where(colour_fill | soft_shadow | solid_detail, 255, 0).astype(np.uint8),
    ))


def clean_color_raster(frame: np.ndarray, *, include_soft_shadows: bool = True) -> Group:
    """Convert the transparent source-fidelity raster to a Manim colour layer."""
    rgba = clean_color_rgba(frame, include_soft_shadows=include_soft_shadows)
    return Group(ImageMobject(rgba).set_height(7.45).set_z_index(-1))


def color_polygons(frame: np.ndarray) -> VGroup:
    """Retained for geometry inspection; rendered scenes use source rasters."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hue, saturation, value = (hsv[:, :, index] for index in range(3))
    unassigned = np.ones(hue.shape, dtype=bool)

    # The first five classes map the original animation's stable flat-fill palette.
    rules = (
        ("#FDF3E7", (hue >= 11) & (hue <= 25) & (saturation >= 16) & (value >= 185), 180),  # skin
        ("#DED1F3", (hue >= 118) & (hue <= 145) & (saturation >= 25) & (value >= 205), 180),  # scarf
        ("#A497B8", (hue >= 118) & (hue <= 150) & (saturation >= 20) & (value >= 100) & (value < 205), 110),
        ("#C4C2D8", (hue >= 110) & (hue <= 175) & (saturation >= 10) & (saturation < 32) & (value >= 160), 130),
        ("#E8D5CE", (hue <= 10) & (saturation >= 12) & (saturation < 60) & (value >= 190), 35),  # blush
    )
    blocks = VGroup()
    height, width = frame.shape[:2]
    for color, rule, minimum_area in rules:
        mask = clean_mask(rule & unassigned, minimum_area)
        unassigned &= mask == 0
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        for contour in contours:
            blocks.add(polygon_from_contour(contour, width, height, color))

    # Keep small, saturated rainbow-earring accents as individual flat-color regions.
    accents = clean_mask(unassigned & (saturation >= 60) & (value >= 120), 18)
    contours, _ = cv2.findContours(accents, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    for contour in contours:
        region = np.zeros(accents.shape, dtype=np.uint8)
        cv2.drawContours(region, [contour], -1, 255, thickness=-1)
        pixels = frame[region > 0]
        if not len(pixels):
            continue
        median = np.median(pixels, axis=0).astype(np.uint8)
        accent_hsv = cv2.cvtColor(median.reshape(1, 1, 3), cv2.COLOR_BGR2HSV)
        accent_rgb = cv2.cvtColor(accent_hsv, cv2.COLOR_HSV2RGB)[0, 0]
        blocks.add(polygon_from_contour(contour, width, height, "#%02X%02X%02X" % tuple(accent_rgb)))

    # Brows, eye blocks, and shoe/sock fills are disconnected dark components.
    # Excluding the very large components keeps the existing outline paths from
    # becoming filled silhouettes while restoring the intentional solid details.
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    solid_ink = cv2.morphologyEx(
        (gray < 70).astype(np.uint8) * 255,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)),
    )
    count, labels, stats, _ = cv2.connectedComponentsWithStats(solid_ink)
    for label in range(1, count):
        area = stats[label, cv2.CC_STAT_AREA]
        if not 20 <= area <= 5000:
            continue
        component = np.zeros(gray.shape, dtype=np.uint8)
        component[labels == label] = 255
        contours, _ = cv2.findContours(component, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        for contour in contours:
            blocks.add(polygon_from_contour(contour, width, height, "#171717"))
    return blocks.set_z_index(-1)


def color_blocks(frame: np.ndarray) -> Group:
    """Use a clean masked source layer instead of fragmented colour polygons."""
    return clean_color_raster(frame)


def reorder_for_transform(previous: list[np.ndarray], current: list[np.ndarray]) -> list[np.ndarray]:
    """Assign target paths greedily by center and bounding-box area."""
    def descriptor(points: np.ndarray) -> np.ndarray:
        x, y, width, height = cv2.boundingRect(points.astype(np.float32))
        return np.array([x + width / 2, y + height / 2, width * height], dtype=float)

    pool = list(range(len(current)))
    ordered = []
    scale = np.array([1080.0, 1080.0, 1080.0 * 1080.0])
    for source in previous:
        source_descriptor = descriptor(source)
        best = min(pool, key=lambda index: np.linalg.norm((descriptor(current[index]) - source_descriptor) / scale))
        ordered.append(current[best])
        pool.remove(best)
    return ordered


def to_smooth_vmobject(points: np.ndarray, width: int, height: int) -> VMobject:
    # Nine times the initial experiment's 128 anchors, preserving fine curves.
    curve = resample_closed(points, 1152)
    scene_points = np.column_stack((
        (curve[:, 0] / width - 0.5) * 7.45,
        (0.5 - curve[:, 1] / height) * 7.45,
        np.zeros(len(curve)),
    ))
    path = VMobject(stroke_color=BLACK, stroke_width=2.15, fill_opacity=0)
    path.set_points_smoothly(np.vstack((scene_points, scene_points[0])))
    return path


def build_poses(
    *,
    sample_times: tuple[float, ...] = SAMPLE_TIMES,
    artifact_dir: Path = ARTIFACT_DIR,
) -> tuple[list[VGroup], list[VGroup]]:
    """Extract video poses with optional callers' sampling and cache locations."""
    artifact_dir.mkdir(parents=True, exist_ok=True)
    capture = cv2.VideoCapture(str(VIDEO_PATH))
    if not capture.isOpened():
        raise FileNotFoundError(VIDEO_PATH)
    frames = [read_frame(capture, seconds) for seconds in sample_times]
    capture.release()
    height, width = frames[0].shape[:2]

    contours = [extract_contours(frame) for frame in frames]
    ordered = [contours[0]]
    for pose in contours[1:]:
        ordered.append(reorder_for_transform(ordered[-1], pose))

    colors = []
    for index, frame in enumerate(frames, start=1):
        cv2.imwrite(str(artifact_dir / f"sample_{index:02d}.png"), frame)
        colors.append(color_blocks(frame))

    line_groups = [VGroup(*[
        to_smooth_vmobject(path, width, height)
        for path in pose
    ]) for pose in ordered]
    return line_groups, colors


class VideoFourierSmoothTransform(Scene):
    def construct(self) -> None:
        line_poses, color_poses = build_poses()
        self.wait(0.25)
        # Same staged drawing rhythm as 02d_lagged_create.mp4.
        self.play(
            LaggedStart(*(Create(path) for path in line_poses[0]), lag_ratio=0.11),
            run_time=1.333,
        )
        self.play(FadeIn(color_poses[0]), run_time=0.45)
        self.wait(0.25)

        current_lines = line_poses[0]
        current_color = color_poses[0]
        for target_lines, target_color in zip(line_poses[1:], color_poses[1:]):
            self.play(
                Transform(current_lines, target_lines),
                FadeOut(current_color),
                run_time=1.0,
            )
            self.play(FadeIn(target_color), run_time=0.25)
            current_color = target_color
