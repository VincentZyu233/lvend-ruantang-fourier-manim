"""Render 01's nine drawing studies and its 3x3 comparison grid."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from render_support import burn_labels, create_label_overlay

SOURCE = ROOT / "src" / "01" / "create_effects.py"
EXTRACT = ROOT / "src" / "01" / "extract_geometry.py"
MEDIA = ROOT / "build" / "01_media"
OUTPUT = ROOT / "output" / "no_captioned"
SCENES = (
    ("FourierWrite", "01_02a_write"),
    ("FourierCreate", "01_02b_create"),
    ("FourierPassingFlash", "01_02c_passing_flash"),
    ("FourierLaggedCreate", "01_02d_lagged_create"),
    ("FourierBorderThenFill", "01_02e_border_then_fill"),
    ("FourierIncreasingSubsets", "01_02f_increasing_subsets"),
    ("FourierGrowFromCenter", "01_02g_grow_from_center"),
    ("FourierFadeInParts", "01_02h_fade_in_parts"),
    ("FourierPathFlash", "01_02i_path_flash"),
)
LABELS = (
    "01a Write", "01b Create", "01c PassingFlash",
    "01d LaggedCreate", "01e BorderThenFill", "01f IncreasingSubsets",
    "01g GrowFromCenter", "01h FadeInParts", "01i PathFlash",
)


def run(*command: str) -> None:
    print("+", " ".join(command))
    subprocess.run(command, check=True)


def newest_scene(scene: str) -> Path:
    matches = list(MEDIA.rglob(f"{scene}.mp4"))
    if not matches:
        raise FileNotFoundError(f"Manim did not create {scene}.mp4 under {MEDIA}")
    return max(matches, key=lambda item: item.stat().st_mtime)


def gif(video: Path) -> Path:
    target = video.with_suffix(".gif")
    run("ffmpeg", "-y", "-i", str(video), "-vf", "fps=20,scale=720:-1:flags=lanczos", "-loop", "0", str(target))
    return target


def make_grid(videos: list[Path]) -> Path:
    inputs = [part for video in videos for part in ("-i", str(video))]
    scaled = ";".join(f"[{index}:v]scale=360:360[v{index}]" for index in range(9))
    tiles = "".join(f"[v{index}]" for index in range(9))
    layout = "|".join(f"{360 * (index % 3)}_{360 * (index // 3)}" for index in range(9))
    raw_target = ROOT / "build" / "01_nine_grid_unlabeled.mp4"
    target = OUTPUT / "01_02_nine_grid.mp4"
    run(
        "ffmpeg", "-y", *inputs, "-filter_complex",
        f"{scaled};{tiles}xstack=inputs=9:layout={layout}:shortest=0,format=yuv420p[v]",
        "-map", "[v]", "-r", "20", "-c:v", "libx264", "-crf", "18", str(raw_target),
    )
    overlay = ROOT / "build" / "01_nine_grid_labels.png"
    create_label_overlay(overlay, 1080, 1080, 3, LABELS)
    burn_labels(run, raw_target, overlay, target)
    gif(target)
    return target


def main() -> None:
    OUTPUT.mkdir(exist_ok=True)
    run(sys.executable, str(EXTRACT))
    videos: list[Path] = []
    for scene, stem in SCENES:
        run(sys.executable, "-m", "manim", "--format=mp4", "--media_dir", str(MEDIA), "-r", "720,720", "--fps", "20", str(SOURCE), scene)
        target = OUTPUT / f"{stem}.mp4"
        shutil.copy2(newest_scene(scene), target)
        gif(target)
        videos.append(target)
    make_grid(videos)


if __name__ == "__main__":
    main()
