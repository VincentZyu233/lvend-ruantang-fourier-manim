"""Render 03's native-Create video/PSD pose studies and a 3x2 grid."""

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

SOURCE = ROOT / "src" / "03" / "onion_skin_create.py"
SCENES = (
    ("Flow10aVideoSingle", "03_10a_video_single"),
    ("Flow10bVideoLayered", "03_10b_video_layered"),
    ("Flow10cVideoLongTail", "03_10c_video_longtail"),
    ("Flow10dPsdSingle", "03_10d_psd_single"),
    ("Flow10ePsdLayered", "03_10e_psd_layered"),
    ("Flow10fPsdLongTail", "03_10f_psd_longtail"),
)
LABELS = (
    "03a Video Cascade", "03b Video Chapters", "03c Video OutlineFirst",
    "03d PSD Cascade", "03e PSD Chapters", "03f PSD OutlineFirst",
)


def run(*command: str, env: dict[str, str] | None = None) -> None:
    print("+", " ".join(command))
    subprocess.run(command, check=True, env=env)


def newest_scene(media: Path, scene: str) -> Path:
    matches = list(media.rglob(f"{scene}.mp4"))
    if not matches:
        raise FileNotFoundError(f"Manim did not create {scene}.mp4 under {media}")
    return max(matches, key=lambda item: item.stat().st_mtime)


def gif(video: Path) -> None:
    run("ffmpeg", "-y", "-i", str(video), "-vf", "fps=20,scale=720:-1:flags=lanczos", "-loop", "0", str(video.with_suffix(".gif")))


def make_grid(videos: list[Path], output: Path, build: Path, profile) -> None:
    inputs = [part for video in videos for part in ("-i", str(video))]
    tile = profile.grid_tile
    scaled = ";".join(f"[{index}:v]scale={tile}:{tile}[v{index}]" for index in range(6))
    tiles = "".join(f"[v{index}]" for index in range(6))
    raw_target = build / "03_grid_unlabeled.mp4"
    target = output / "03_10abcdef_onionskin_grid.mp4"
    run(
        "ffmpeg", "-y", *inputs, "-filter_complex",
        f"{scaled};{tiles}xstack=inputs=6:layout=0_0|{tile}_0|{tile * 2}_0|0_{tile}|{tile}_{tile}|{tile * 2}_{tile}:shortest=0,format=yuv420p[v]",
        "-map", "[v]", "-r", str(profile.fps), "-c:v", "libx264", "-crf", "18", str(raw_target),
    )
    overlay = build / "03_grid_labels.png"
    create_label_overlay(overlay, tile * 3, tile * 2, 3, LABELS)
    burn_labels(run, raw_target, overlay, target, profile.fps)
    if not profile.high_fidelity:
        gif(target)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("standard", "high"), default="standard")
    args = parser.parse_args()
    profile = get_profile(args.profile)
    output = profile_output(ROOT, profile, "no_captioned")
    media = ROOT / "build" / f"03_media_{profile.name}"
    build = ROOT / "build" / profile.name
    output.mkdir(parents=True, exist_ok=True)
    build.mkdir(parents=True, exist_ok=True)
    videos: list[Path] = []
    for scene, stem in SCENES:
        # The source-video raster and PSD registration are computed at runtime;
        # bypass Manim's partial-movie cache so an invocation always reflects
        # the current extraction and alignment code.
        environment = os.environ | profile.environment()
        run(sys.executable, "-m", "manim", "--disable_caching", "--format=mp4", "--media_dir", str(media), "-r", f"{profile.scene_side},{profile.scene_side}", "--fps", str(profile.fps), str(SOURCE), scene, env=environment)
        target = output / f"{stem}.mp4"
        shutil.copy2(newest_scene(media, scene), target)
        if not profile.high_fidelity:
            gif(target)
        videos.append(target)
    make_grid(videos, output, build, profile)


if __name__ == "__main__":
    main()
