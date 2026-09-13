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
    Succession,
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
read_frame = BASE["read_frame"]
VIDEO_PATH = BASE["VIDEO_PATH"]
clean_color_raster = BASE["clean_color_raster"]
clean_color_rgba = BASE["clean_color_rgba"]
resample_closed = BASE["resample_closed"]

INK = "#171717"
TEAL = "#12B8A6"
GHOST = "#84909A"
VIDEO_SAMPLE_TIMES = tuple(np.linspace(0.55, 6.35, 10))
VIDEO_ARTIFACT_DIR = PROJECT / "build" / "03_video_fourier"
# These full-video frame matches are derived from the PSD line masks. The PSD
# stores only black animation drawings, while the matching source frames retain
# the artist's face, hair, scarf, eyebrow, shoe, and shadow colours.
PSD_REFERENCE_FRAMES = (56, 112, 114, 10, 200, 56, 18, 208, 102, 212)
VIDEO_FPS = 30.0


def boost_colors(group: VGroup, saturation: float = 1.05) -> VGroup:
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


def clean_video_color_layer(frame: np.ndarray) -> Group:
    """Reuse 02's source-faithful colour mask for the redraw study."""
    return clean_color_raster(frame)


def video_color_layers(sample_times: tuple[float, ...]) -> list[Group]:
    capture = cv2.VideoCapture(str(VIDEO_PATH))
    if not capture.isOpened():
        raise FileNotFoundError(VIDEO_PATH)
    try:
        return [clean_video_color_layer(read_frame(capture, seconds)) for seconds in sample_times]
    finally:
        capture.release()


def psd_ink_mask(image: Image.Image) -> np.ndarray:
    """Extract opaque black drawing pixels from a composited PSD pose."""
    rgba = np.asarray(image)
    return ((rgba[:, :, 3] > 24) & (rgba[:, :, :3].min(axis=2) < 190)).astype(np.uint8)


def align_video_fill_to_psd(frame: np.ndarray, psd_image: Image.Image) -> np.ndarray:
    """Warp a matched colour frame into the PSD drawing's exact pixel pose.

    The animation PSD has only ink, while the video has the fills.  Their
    canvas dimensions and per-frame registration differ substantially.  A
    generic ECC fit focused on local line texture and left the source character
    too wide.  The complete ink silhouette is a more reliable registration
    reference: map its source bounding box exactly to the PSD bounding box.
    """
    target_rgba = np.asarray(psd_image)
    height, width = target_rgba.shape[:2]
    source = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)
    source_gray = cv2.cvtColor(source, cv2.COLOR_BGR2GRAY)
    source_ink = (source_gray < 112).astype(np.uint8)
    target_ink = psd_ink_mask(psd_image)

    target_points = cv2.findNonZero(target_ink)
    source_points = cv2.findNonZero(source_ink)
    if target_points is None or source_points is None:
        return clean_color_rgba(source, include_soft_shadows=False)
    target_x, target_y, target_width, target_height = cv2.boundingRect(target_points)
    source_x, source_y, source_width, source_height = cv2.boundingRect(source_points)
    scale_x = target_width / source_width
    scale_y = target_height / source_height
    # This is intentionally anisotropic: the PSD is a non-square drawing
    # canvas and its posed character is consistently narrower than the video
    # reference after the initial resize.
    warp = np.array((
        (scale_x, 0.0, target_x - source_x * scale_x),
        (0.0, scale_y, target_y - source_y * scale_y),
    ), dtype=np.float32)

    source_rgba = clean_color_rgba(source, include_soft_shadows=False)
    return cv2.warpAffine(
        source_rgba,
        warp,
        (width, height),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0, 0),
    )


def psd_regions(image: Image.Image) -> list[np.ndarray]:
    """Return closed, inset cells bounded by the PSD's own ink."""
    ink = psd_ink_mask(image) * 255
    barriers = cv2.dilate(ink, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(255 - barriers)
    height, width = ink.shape
    regions = []
    for label in range(1, count):
        x, y, cell_width, cell_height, area = stats[label]
        if x == 0 or y == 0 or x + cell_width >= width or y + cell_height >= height:
            continue
        if 65 <= area <= width * height * 0.18:
            regions.append(labels == label)
    return regions


def psd_boundary_fill(frame: np.ndarray, psd_image: Image.Image) -> np.ndarray:
    """Keep source semantic fills, but let PSD cells lock scarf and ink edges."""
    aligned = align_video_fill_to_psd(frame, psd_image)
    filled = aligned.copy()
    support = aligned[:, :, 3] > 0
    for region in psd_regions(psd_image):
        samples = region & support
        # A little overlap is enough after hand-drawn-frame registration; the
        # final alpha comes exclusively from the PSD cell, never the video.
        if samples.sum() < max(20, int(region.sum() * 0.045)):
            continue
        color = np.median(aligned[:, :, :3][samples], axis=0).astype(np.uint8)
        if color.min() > 246:
            continue
        hue, saturation, value = cv2.cvtColor(color.reshape(1, 1, 3), cv2.COLOR_RGB2HSV)[0, 0]
        is_black_detail = value < 82
        is_scarf_purple = 118 <= hue <= 156 and saturation >= 28 and value >= 95
        # Face and hair contours are not reliably closed in this PSD.  The
        # source raster preserves their white-hair/skin separation, while the
        # closed scarf and dark-detail cells can safely own their exact edges.
        if not (is_black_detail or is_scarf_purple):
            continue
        filled[region, :3] = color
        filled[region, 3] = 255
    return filled


def psd_reference_color_layers(images: list[Image.Image]) -> list[Group]:
    """Align original video fills to every PSD black-line pose."""
    capture = cv2.VideoCapture(str(VIDEO_PATH))
    if not capture.isOpened():
        raise FileNotFoundError(VIDEO_PATH)
    try:
        layers = []
        for frame_index, psd_image in zip(PSD_REFERENCE_FRAMES, images):
            rgba = psd_boundary_fill(
                read_frame(capture, frame_index / VIDEO_FPS),
                psd_image,
            )
            image = (
                ImageMobject(rgba)
                .stretch_to_fit_width(7.45)
                .stretch_to_fit_height(7.45)
                .set_z_index(-1)
            )
            layers.append(Group(image))
        return layers
    finally:
        capture.release()


def video_assets() -> tuple[list[VGroup], list[Group]]:
    """Build ten Fourier line poses with source-faithful masked fill layers."""
    lines, colors = build_video_poses(
        sample_times=VIDEO_SAMPLE_TIMES,
        artifact_dir=VIDEO_ARTIFACT_DIR,
    )
    del colors
    return lines, video_color_layers(VIDEO_SAMPLE_TIMES)


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
    """Paint only reliable PSD regions, keeping line-art-only areas uncoloured.

    The PSD contains black ink but no source fills. Broad vertical-band rules
    made sleeves and coat panels purple, so the conservative pass below limits
    purple to the central scarf. Shoe colour uses each pose's lower ink bound,
    rather than a canvas-wide region that could colour the trousers.
    """
    rgba = np.asarray(image)
    height, width = rgba.shape[:2]
    ink = ((rgba[:, :, 3] > 24) & (rgba[:, :, :3].min(axis=2) < 190)).astype(np.uint8) * 255
    barriers = cv2.dilate(ink, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    count, labels, stats, centroids = cv2.connectedComponentsWithStats(255 - barriers)
    painted = np.zeros((height, width, 4), dtype=np.uint8)
    ink_y = np.where(ink > 0)[0]
    character_top, character_bottom = int(ink_y.min()), int(ink_y.max())
    # The original reference has dark shoes at the very base of each pose. The
    # crop prevents a connected trouser-and-shoe cell being painted all black.
    shoe_top = character_bottom - int((character_bottom - character_top) * 0.10)
    row_indices = np.arange(height)[:, None]
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
        component = labels == label
        if y + region_height >= shoe_top and center_y >= shoe_top - region_height * 0.35:
            painted[component & (row_indices >= shoe_top)] = (28, 26, 33, 255)
        elif 0.34 <= relative_y < 0.57 and 0.23 <= relative_x <= 0.77:
            color = (255, 224, 202, 245)  # face and blush-family regions
            painted[component] = color
        elif 0.54 <= relative_y < 0.74 and 0.20 <= relative_x <= 0.80:
            color = (211, 181, 255, 245)  # scarf and its central shadow
            painted[component] = color
        else:
            continue  # hair, coat, and ambiguous cells stay source-white
    return Group(ImageMobject(painted).set_height(7.45).set_z_index(-1))


def psd_assets() -> tuple[list[VGroup], list[Group]]:
    """Use the PSD as its honest source form: ten black line-art poses only."""
    psd = PSDImage.open(PSD_PATH)
    source_groups = psd_pose_groups(psd)
    selected_indices = tuple(range(len(source_groups)))
    images = [composite_group(source_groups[index], psd.size) for index in selected_indices]
    raw_poses = [extract_psd_contours(image) for image in images]
    ordered = [raw_poses[0]]
    for pose in raw_poses[1:]:
        ordered.append(reorder_for_transform(ordered[-1], pose))
    line_poses = [VGroup(*[points_to_path(points, *psd.size) for points in pose]) for pose in ordered]
    # This PSD does not contain colour layers.  Do not fabricate colour from
    # video reference frames in the PSD comparison row.
    return line_poses, [Group() for _ in images]


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
    if not colors.submobjects:
        return
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
    chapters = [
        LaggedStart(*(Create(path) for path in group), lag_ratio=0.12, run_time=duration * weight)
        for group, weight in zip(groups, weights)
    ]
    # Keep chapter order while Scene controls one shared duration.  Calling play
    # separately for each sub-frame rounds every chapter up at 20 fps.
    scene.play(Succession(*chapters), run_time=duration)
