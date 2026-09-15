"""Create readable lower-third variants of the committed Manim studies."""

from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from render_profile import get_profile, profile_output
OUTPUT = ROOT / "output"
RAW = OUTPUT / "no_captioned"
CAPTIONED = OUTPUT / "captioned"
BUILD = ROOT / "build" / "captioned"
BILI = OUTPUT / "bili"
FOOTER_HEIGHT = 100
PLAYBACK_RATE = "1.09090909"


@dataclass(frozen=True)
class Clip:
    filename: str
    chapter: str
    method: str


CLIPS = (
    Clip("01_02_nine_grid.mp4", "01 / 单帧傅里叶描线", "9 Methods / Grid"),
    Clip("01_02a_write.mp4", "01a / 单帧傅里叶描线", "Write"),
    Clip("01_02b_create.mp4", "01b / 单帧傅里叶描线", "Create"),
    Clip("01_02c_passing_flash.mp4", "01c / 单帧傅里叶描线", "Passing Flash"),
    Clip("01_02d_lagged_create.mp4", "01d / 单帧傅里叶描线", "Lagged Create"),
    Clip("01_02e_border_then_fill.mp4", "01e / 单帧傅里叶描线", "Border Then Fill"),
    Clip("01_02f_increasing_subsets.mp4", "01f / 单帧傅里叶描线", "Increasing Subsets"),
    Clip("01_02g_grow_from_center.mp4", "01g / 单帧傅里叶描线", "Grow From Center"),
    Clip("01_02h_fade_in_parts.mp4", "01h / 单帧傅里叶描线", "Fade In Parts"),
    Clip("01_02i_path_flash.mp4", "01i / 单帧傅里叶描线", "Path Flash"),
    Clip("02_06abcdef_grid.mp4", "02 / 视频傅里叶轮廓变换", "6 Methods / Grid"),
    Clip("02_06a_manimce_transform.mp4", "02a / 视频傅里叶轮廓变换", "Transform"),
    Clip("02_06b_manimce_transform_matching_shapes.mp4", "02b / 视频傅里叶轮廓变换", "TransformMatchingShapes"),
    Clip("02_06c_manimce_replacement_transform.mp4", "02c / 视频傅里叶轮廓变换", "ReplacementTransform"),
    Clip("02_06d_manimce_transform_from_copy.mp4", "02d / 视频傅里叶轮廓变换", "Transform From Copy"),
    Clip("02_06e_manimce_move_to_target.mp4", "02e / 视频傅里叶轮廓变换", "Move To Target"),
    Clip("02_06f_manimce_apply_pointwise_function.mp4", "02f / 视频傅里叶轮廓变换", "ApplyPointwiseFunction"),
    Clip("03_10abcdef_onionskin_grid.mp4", "03 / 视频与 PSD 原生描线", "6 Methods / Grid"),
    Clip("03_10a_video_single.mp4", "03a / 视频与 PSD 原生描线", "Video Cascade"),
    Clip("03_10b_video_layered.mp4", "03b / 视频与 PSD 原生描线", "Video Chapters"),
    Clip("03_10c_video_longtail.mp4", "03c / 视频与 PSD 原生描线", "Video Outline First"),
    Clip("03_10d_psd_single.mp4", "03d / 视频与 PSD 原生描线", "PSD Cascade"),
    Clip("03_10e_psd_layered.mp4", "03e / 视频与 PSD 原生描线", "PSD Chapters"),
    Clip("03_10f_psd_longtail.mp4", "03f / 视频与 PSD 原生描线", "PSD Outline First"),
)


def run(*command: str) -> None:
    if command[0] == "ffmpeg":
        command = ("ffmpeg", "-hide_banner", "-loglevel", "error", *command[1:])
    print("+", " ".join(command))
    subprocess.run(command, check=True)


def video_size(path: Path) -> tuple[int, int]:
    result = subprocess.run(
        (
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height", "-of", "csv=p=0", str(path),
        ),
        check=True,
        capture_output=True,
        text=True,
    )
    width, height = result.stdout.strip().split(",")
    return int(width), int(height)


def create_footer(target: Path, width: int, height: int, clip: Clip, font_path: Path) -> None:
    image = Image.new("RGB", (width, height), "#FFFFFF")
    draw = ImageDraw.Draw(image)
    scale = width / 720
    chapter_size = round(35 * scale)
    method_size = round(26 * scale)
    left = round(50 * scale)
    right = width - round(28 * scale)
    gap = round(24 * scale)
    while True:
        chapter_font = ImageFont.truetype(font_path, size=chapter_size)
        method_font = ImageFont.truetype(font_path, size=method_size)
        occupied = left + draw.textlength(clip.chapter, font=chapter_font) + gap
        if occupied <= right - draw.textlength(clip.method, font=method_font):
            break
        if method_size > round(19 * scale):
            method_size -= 1
        elif chapter_size > round(26 * scale):
            chapter_size -= 1
        else:
            raise ValueError(f"Caption is too wide for {width}px footer: {clip}")
    draw.line((0, 0, width, 0), fill="#D8DDE0", width=1)
    draw.rectangle((round(28 * scale), round(18 * scale), round(34 * scale), height - round(18 * scale)), fill="#12B8A6")
    draw.text((left, height // 2), clip.chapter, anchor="lm", font=chapter_font, fill="#1B2428")
    draw.text((right, height // 2), clip.method, anchor="rm", font=method_font, fill="#536067")
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target)


def make_gif(video: Path) -> None:
    run(
        "ffmpeg", "-y", "-i", str(video),
        "-vf", "fps=20,scale=720:-1:flags=lanczos",
        "-loop", "0", str(video.with_suffix(".gif")),
    )


def caption_clip(clip: Clip, font_path: Path, raw: Path, captioned: Path, profile) -> Path:
    source = raw / clip.filename
    if not source.is_file():
        raise FileNotFoundError(f"Missing source video: {source}")
    width, _ = video_size(source)
    build = BUILD / profile.name
    footer = build / f"{source.stem}_footer.png"
    target = captioned / clip.filename
    create_footer(footer, width, profile.footer_height, clip, font_path)
    captioned.mkdir(parents=True, exist_ok=True)
    run(
        "ffmpeg", "-y", "-i", str(source), "-loop", "1", "-framerate", str(profile.fps), "-i", str(footer),
        "-filter_complex", "[0:v][1:v]vstack=inputs=2:shortest=1,format=yuv420p[v]",
        "-map", "[v]", "-an", "-r", str(profile.fps), "-c:v", "libx264", "-crf", "18", "-movflags", "+faststart",
        "-shortest", str(target),
    )
    if not profile.high_fidelity:
        make_gif(target)
    return target


def assemble_bili(videos: list[Path], music: Path, profile) -> Path:
    if not music.is_file():
        raise FileNotFoundError(f"Missing background music: {music}")
    BILI.mkdir(parents=True, exist_ok=True)
    if profile.high_fidelity:
        # A 24-input scale/concat graph holds every 2160p frame in memory at once.
        # All captioned clips already share dimensions, fps, and codec settings, so
        # concatenate their bitstreams first and process one video stream afterward.
        build = BUILD / profile.name
        build.mkdir(parents=True, exist_ok=True)
        manifest = build / "legacy-01-03-high.concat.txt"
        manifest.write_text(
            "".join(f"file '{video.resolve().as_posix()}'\n" for video in videos),
            encoding="utf-8",
        )
        joined = build / "legacy-01-03-high-joined.mp4"
        run(
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(manifest),
            "-map", "0:v:0", "-an", "-c", "copy", "-movflags", "+faststart", str(joined),
        )
        target = build / "legacy-01-03-high.mp4"
        final_width, final_height = profile.final_size
        content_height = final_height - profile.footer_height
        graph = (
            f"[0:v]scale={final_width}:{content_height}:force_original_aspect_ratio=decrease:force_divisible_by=2,"
            f"pad={final_width}:{content_height}:(ow-iw)/2:(oh-ih)/2:color=white,"
            f"setpts=PTS/{PLAYBACK_RATE}[video]"
        )
        run(
            "ffmpeg", "-y", "-i", str(joined), "-i", str(music),
            "-filter_complex", graph, "-map", "[video]", "-map", "1:a:0",
            "-r", str(profile.fps), "-c:v", "libx264", "-preset", "slow", "-profile:v", "high", "-level:v", "5.1", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(target),
        )
        return target
    input_arguments = [argument for video in videos for argument in ("-i", str(video))]
    chains = []
    for index in range(len(videos)):
        chains.append(
            f"[{index}:v]scale={profile.final_size[0]}:{profile.final_size[1] - profile.footer_height}:force_original_aspect_ratio=decrease:force_divisible_by=2,"
            f"pad={profile.final_size[0]}:{profile.final_size[1] - profile.footer_height}:(ow-iw)/2:(oh-ih)/2:color=white,setpts=PTS/{PLAYBACK_RATE}[v{index}]"
        )
    inputs = "".join(f"[v{index}]" for index in range(len(videos)))
    graph = ";".join((*chains, f"{inputs}concat=n={len(videos)}:v=1:a=0[video]"))
    target = (BUILD / "high" / "legacy-01-03-high.mp4") if profile.high_fidelity else BILI / "bili-video-20260913.mp4"
    target.parent.mkdir(parents=True, exist_ok=True)
    run(
        "ffmpeg", "-y", *input_arguments, "-i", str(music),
        "-filter_complex", graph, "-map", "[video]", "-map", f"{len(videos)}:a:0",
        "-r", str(profile.fps), "-c:v", "libx264", "-preset", "slow", "-profile:v", "high", "-level:v", "5.1", "-crf", "18", "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart", str(target),
    )
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--font", type=Path, required=True, help="Path to LXGWWenKai-Medium.ttf")
    parser.add_argument("--bili", action="store_true", help="Also concatenate the captioned videos with background music")
    parser.add_argument("--assemble-only", action="store_true", help="Reuse existing captioned clips without regenerating their footers")
    parser.add_argument("--profile", choices=("standard", "high"), default="standard")
    parser.add_argument(
        "--music", type=Path,
        default=ROOT / "素材捏" / "music" / "悲伤的间隙-哀の隙間-mimi.flac",
        help="Background FLAC used with --bili",
    )
    args = parser.parse_args()
    if not args.font.is_file():
        parser.error(f"Font file not found: {args.font}")
    profile = get_profile(args.profile)
    raw = profile_output(ROOT, profile, "no_captioned")
    captioned = profile_output(ROOT, profile, "captioned")
    if args.assemble_only:
        videos = [captioned / clip.filename for clip in CLIPS]
        missing = [video for video in videos if not video.is_file()]
        if missing:
            parser.error("Missing captioned clips:\n" + "\n".join(map(str, missing)))
    else:
        videos = [caption_clip(clip, args.font, raw, captioned, profile) for clip in CLIPS]
    if args.bili:
        print(assemble_bili(videos, args.music, profile))


if __name__ == "__main__":
    main()
