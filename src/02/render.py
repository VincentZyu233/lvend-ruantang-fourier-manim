"""Render 02's six Fourier-smoothed morph variants and a 3x2 grid."""

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

SCENES = (
    ("video_transform.py", "VideoFourierSmoothTransform", "02_06a_manimce_transform"),
    ("matching_shapes.py", "MatchingShapesMorph", "02_06b_manimce_transform_matching_shapes"),
    ("replacement_transform.py", "ReplacementMorph", "02_06c_manimce_replacement_transform"),
    ("transform_from_copy.py", "CopyMorph", "02_06d_manimce_transform_from_copy"),
    ("move_to_target.py", "TargetMorph", "02_06e_manimce_move_to_target"),
    ("pointwise_function.py", "PointwiseFunctionMorph", "02_06f_manimce_apply_pointwise_function"),
)
LABELS = (
    "02a Transform", "02b MatchingShapes", "02c Replacement",
    "02d FromCopy", "02e MoveToTarget", "02f Pointwise",
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
    raw_target = build / "02_grid_unlabeled.mp4"
    target = output / "02_06abcdef_grid.mp4"
    run(
        "ffmpeg", "-y", *inputs, "-filter_complex",
        f"{scaled};{tiles}xstack=inputs=6:layout=0_0|{tile}_0|{tile * 2}_0|0_{tile}|{tile}_{tile}|{tile * 2}_{tile}:shortest=0,format=yuv420p[v]",
        "-map", "[v]", "-r", str(profile.fps), "-c:v", "libx264", "-crf", "18", str(raw_target),
    )
    overlay = build / "02_grid_labels.png"
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
    media = ROOT / "build" / f"02_media_{profile.name}"
    build = ROOT / "build" / profile.name
    output.mkdir(parents=True, exist_ok=True)
    build.mkdir(parents=True, exist_ok=True)
    videos: list[Path] = []
    for filename, scene, stem in SCENES:
        # Rebuild all partial movies so the output reflects the current timing.
        environment = os.environ | profile.environment()
        run(sys.executable, "-m", "manim", "--disable_caching", "--format=mp4", "--media_dir", str(media), "-r", f"{profile.scene_side},{profile.scene_side}", "--fps", str(profile.fps), str(ROOT / "src" / "02" / filename), scene, env=environment)
        target = output / f"{stem}.mp4"
        shutil.copy2(newest_scene(media, scene), target)
        if not profile.high_fidelity:
            gif(target)
        videos.append(target)
    make_grid(videos, output, build, profile)


if __name__ == "__main__":
    main()
