"""Render 03's native-Create video/PSD pose studies and a 3x2 grid."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from render_support import burn_labels, create_label_overlay

SOURCE = ROOT / "src" / "03" / "onion_skin_create.py"
MEDIA = ROOT / "build" / "03_media"
OUTPUT = ROOT / "output"
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
    raw_target = ROOT / "build" / "03_grid_unlabeled.mp4"
    target = OUTPUT / "03_10abcdef_onionskin_grid.mp4"
    run(
        "ffmpeg", "-y", *inputs, "-filter_complex",
        f"{scaled};{tiles}xstack=inputs=6:layout=0_0|360_0|720_0|0_360|360_360|720_360:shortest=0,format=yuv420p[v]",
        "-map", "[v]", "-r", "20", "-c:v", "libx264", "-crf", "18", str(raw_target),
    )
    overlay = ROOT / "build" / "03_grid_labels.png"
    create_label_overlay(overlay, 1080, 720, 3, LABELS)
    burn_labels(run, raw_target, overlay, target)
    gif(target)


def main() -> None:
    OUTPUT.mkdir(exist_ok=True)
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
