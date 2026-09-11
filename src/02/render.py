"""Render 02's six Fourier-smoothed morph variants and a 3x2 grid."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MEDIA = ROOT / "build" / "02_media"
OUTPUT = ROOT / "output"
SCENES = (
    ("video_transform.py", "VideoFourierSmoothTransform", "02_06a_manimce_transform"),
    ("matching_shapes.py", "MatchingShapesMorph", "02_06b_manimce_transform_matching_shapes"),
    ("replacement_transform.py", "ReplacementMorph", "02_06c_manimce_replacement_transform"),
    ("transform_from_copy.py", "CopyMorph", "02_06d_manimce_transform_from_copy"),
    ("move_to_target.py", "TargetMorph", "02_06e_manimce_move_to_target"),
    ("pointwise_function.py", "PointwiseFunctionMorph", "02_06f_manimce_apply_pointwise_function"),
)


def run(*command: str) -> None:
    print("+", " ".join(command))
    subprocess.run(command, check=True)


def newest_scene(scene: str) -> Path:
    matches = list(MEDIA.rglob(f"{scene}.mp4"))
    if not matches:
        raise FileNotFoundError(f"Manim did not create {scene}.mp4 under {MEDIA}")
    return max(matches, key=lambda item: item.stat().st_mtime)


def gif(video: Path) -> None:
    run("ffmpeg", "-y", "-i", str(video), "-vf", "fps=20,scale=720:-1:flags=lanczos", "-loop", "0", str(video.with_suffix(".gif")))


def make_grid(videos: list[Path]) -> None:
    inputs = [part for video in videos for part in ("-i", str(video))]
    scaled = ";".join(f"[{index}:v]scale=360:360[v{index}]" for index in range(6))
    tiles = "".join(f"[v{index}]" for index in range(6))
    target = OUTPUT / "02_06abcdef_grid.mp4"
    run(
        "ffmpeg", "-y", *inputs, "-filter_complex",
        f"{scaled};{tiles}xstack=inputs=6:layout=0_0|360_0|720_0|0_360|360_360|720_360:shortest=0,format=yuv420p[v]",
        "-map", "[v]", "-r", "20", "-c:v", "libx264", "-crf", "18", str(target),
    )
    gif(target)


def main() -> None:
    OUTPUT.mkdir(exist_ok=True)
    videos: list[Path] = []
    for filename, scene, stem in SCENES:
        run(sys.executable, "-m", "manim", "--format=mp4", "--media_dir", str(MEDIA), "-r", "720,720", "--fps", "20", str(ROOT / "src" / "02" / filename), scene)
        target = OUTPUT / f"{stem}.mp4"
        shutil.copy2(newest_scene(scene), target)
        gif(target)
        videos.append(target)
    make_grid(videos)


if __name__ == "__main__":
    main()
