"""Render 01's nine drawing studies and its 3x3 comparison grid."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from render_support import burn_labels, create_label_overlay
from render_profile import get_profile, profile_output

SOURCE = ROOT / "src" / "01" / "create_effects.py"
EXTRACT = ROOT / "src" / "01" / "extract_geometry.py"
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


def run(*command: str, env: dict[str, str] | None = None) -> None:
    print("+", " ".join(command))
    subprocess.run(command, check=True, env=env)


def newest_scene(media: Path, scene: str) -> Path:
    matches = list(media.rglob(f"{scene}.mp4"))
    if not matches:
        raise FileNotFoundError(f"Manim did not create {scene}.mp4 under {media}")
    return max(matches, key=lambda item: item.stat().st_mtime)


def gif(video: Path) -> Path:
    target = video.with_suffix(".gif")
    run("ffmpeg", "-y", "-i", str(video), "-vf", "fps=20,scale=720:-1:flags=lanczos", "-loop", "0", str(target))
    return target


def make_grid(videos: list[Path], output: Path, build: Path, profile) -> Path:
    inputs = [part for video in videos for part in ("-i", str(video))]
    tile = profile.grid_tile
    scaled = ";".join(f"[{index}:v]scale={tile}:{tile}[v{index}]" for index in range(9))
    tiles = "".join(f"[v{index}]" for index in range(9))
    layout = "|".join(f"{tile * (index % 3)}_{tile * (index // 3)}" for index in range(9))
    raw_target = build / "01_nine_grid_unlabeled.mp4"
    target = output / "01_02_nine_grid.mp4"
    run(
        "ffmpeg", "-y", *inputs, "-filter_complex",
        f"{scaled};{tiles}xstack=inputs=9:layout={layout}:shortest=0,format=yuv420p[v]",
        "-map", "[v]", "-r", str(profile.fps), "-c:v", "libx264", "-crf", "18", str(raw_target),
    )
    overlay = build / "01_nine_grid_labels.png"
    create_label_overlay(overlay, tile * 3, tile * 3, 3, LABELS)
    burn_labels(run, raw_target, overlay, target, profile.fps)
    if not profile.high_fidelity:
        gif(target)
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("standard", "high"), default="standard")
    args = parser.parse_args()
    profile = get_profile(args.profile)
    output = profile_output(ROOT, profile, "no_captioned")
    media = ROOT / "build" / f"01_media_{profile.name}"
    build = ROOT / "build" / profile.name
    output.mkdir(parents=True, exist_ok=True)
    build.mkdir(parents=True, exist_ok=True)
    run(sys.executable, str(EXTRACT))
    videos: list[Path] = []
    for scene, stem in SCENES:
        environment = os.environ | profile.environment()
        run(sys.executable, "-m", "manim", "--format=mp4", "--media_dir", str(media), "-r", f"{profile.scene_side},{profile.scene_side}", "--fps", str(profile.fps), str(SOURCE), scene, env=environment)
        target = output / f"{stem}.mp4"
        shutil.copy2(newest_scene(media, scene), target)
        if not profile.high_fidelity:
            gif(target)
        videos.append(target)
    make_grid(videos, output, build, profile)


if __name__ == "__main__":
    main()
