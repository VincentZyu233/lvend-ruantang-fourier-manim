"""Portable label overlays shared by the three ffmpeg grid renderers."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Sequence

from PIL import Image, ImageDraw, ImageFont


def create_label_overlay(
    target: Path,
    width: int,
    height: int,
    columns: int,
    labels: Sequence[str],
) -> None:
    """Create a system-font-independent transparent label layer for an ffmpeg grid."""
    rows = (len(labels) + columns - 1) // columns
    tile_width = width // columns
    tile_height = height // rows
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=max(16, min(tile_width, tile_height) // 19))
    for index, label in enumerate(labels):
        x = (index % columns) * tile_width + 10
        y = (index // columns) * tile_height + 8
        left, top, right, bottom = draw.textbbox((x, y), label, font=font)
        draw.rounded_rectangle((left - 5, top - 3, right + 5, bottom + 3), radius=3, fill=(255, 255, 255, 224))
        draw.text((x, y), label, font=font, fill=(20, 20, 20, 255))
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target)


def burn_labels(
    run: Callable[..., None],
    video: Path,
    overlay: Path,
    target: Path,
) -> None:
    """Burn a static Pillow overlay onto a rendered grid without platform fonts."""
    run(
        "ffmpeg", "-y", "-i", str(video), "-loop", "1", "-i", str(overlay),
        "-filter_complex", "[0:v][1:v]overlay=0:0:shortest=1,format=yuv420p[v]",
        "-map", "[v]", "-r", "20", "-c:v", "libx264", "-crf", "18", str(target),
    )
