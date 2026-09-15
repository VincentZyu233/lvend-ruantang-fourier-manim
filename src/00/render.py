"""Render chapter 00 and assemble the extended 20260915 Bili cut."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from render_profile import RenderProfile, STANDARD, get_profile, profile_output


ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "src" / "00"
CAPTIONED = ROOT / "output" / "captioned"
BILI = ROOT / "output" / "bili"
BUILD = ROOT / "build"
POINTER_SOURCE = BUILD / "00_02a_timeline_pointer.mp4"
POINTER_SCENE = SOURCE_DIR / "pointer_loop.py"
POINTER_MEDIA = BUILD / "00_pointer_media"
TIMELINE_OVERLAY = BUILD / "00_timeline_overlay_20260915.mp4"
ASSEMBLED = BUILD / "00_bili_assembled_20260915.mp4"
GROUP_A = BUILD / "00_science_segment.mp4"
GROUP_B = BUILD / "00_hanataba_segment.mp4"

SCIENCE = ROOT / "素材捏" / "music" / "科学-サイエンス-mimi.flac"
HANATABA = ROOT / "素材捏" / "music" / "花束-ハナタバ-mimi.flac"
SORROW = ROOT / "素材捏" / "music" / "悲伤的间隙-哀の隙間-mimi.flac"
LEGACY_VIDEO = BILI / "bili-video-20260913.mp4"
SCIENCE_DURATION = 188.0
HANATABA_DURATION = 150.362336
LEGACY_SOURCE_DURATION = 219.118
MUSIC_CROSSFADE = 0.8
PLAYBACK_RATE = 1.09090909
FIRST_GROUP_TARGET = SCIENCE_DURATION
SECOND_GROUP_TARGET = HANATABA_DURATION - MUSIC_CROSSFADE
LEGACY_TARGET = LEGACY_SOURCE_DURATION - MUSIC_CROSSFADE
TIMELINE_LEFT = 32
TIMELINE_WIDTH = 1016
TIMELINE_RIGHT = TIMELINE_LEFT + TIMELINE_WIDTH
PROFILE = STANDARD
FRAME_WIDTH, FRAME_HEIGHT = PROFILE.final_size


@dataclass(frozen=True)
class RenderStage:
    stem: str
    source: Path
    scene: str
    media: Path


@dataclass(frozen=True)
class StageWindow:
    chapter: str
    index: int
    count: int
    start: float
    duration: float


STAGES = (
    RenderStage("00_16g_ribbon_wand", SOURCE_DIR / "fourier_ribbon_wand.py", "FourierRibbonWand", BUILD / "00_media"),
    RenderStage("00_00b_closed_loop", SOURCE_DIR / "fourier_principles.py", "ClosedLoopCoordinates", BUILD / "00_principles_media"),
    RenderStage("00_00c_complex_vectors", SOURCE_DIR / "fourier_principles.py", "ComplexRotatingVectors", BUILD / "00_principles_media"),
    RenderStage("00_00d_sampling_derotation", SOURCE_DIR / "fourier_principles.py", "SamplingAndDeRotation", BUILD / "00_principles_media"),
    RenderStage("00_00e_reconstruction", SOURCE_DIR / "fourier_principles.py", "Reconstruction", BUILD / "00_principles_media"),
)

LEGACY_CHAPTERS = (
    ("01", ("01_02_nine_grid.mp4", "01_02a_write.mp4", "01_02b_create.mp4", "01_02c_passing_flash.mp4", "01_02d_lagged_create.mp4", "01_02e_border_then_fill.mp4", "01_02f_increasing_subsets.mp4", "01_02g_grow_from_center.mp4", "01_02h_fade_in_parts.mp4", "01_02i_path_flash.mp4")),
    ("02", ("02_06abcdef_grid.mp4", "02_06a_manimce_transform.mp4", "02_06b_manimce_transform_matching_shapes.mp4", "02_06c_manimce_replacement_transform.mp4", "02_06d_manimce_transform_from_copy.mp4", "02_06e_manimce_move_to_target.mp4", "02_06f_manimce_apply_pointwise_function.mp4")),
    ("03", ("03_10abcdef_onionskin_grid.mp4", "03_10a_video_single.mp4", "03_10b_video_layered.mp4", "03_10c_video_longtail.mp4", "03_10d_psd_single.mp4", "03_10e_psd_layered.mp4", "03_10f_psd_longtail.mp4")),
)


def run(*command: str, env: dict[str, str] | None = None) -> None:
    print("+", " ".join(command))
    subprocess.run(command, check=True, env=env)


def configure_profile(profile: RenderProfile) -> None:
    """Redirect every generated asset while keeping the standard pipeline stable."""
    global PROFILE, FRAME_WIDTH, FRAME_HEIGHT
    global CAPTIONED, BUILD, POINTER_SOURCE, POINTER_MEDIA, TIMELINE_OVERLAY
    global ASSEMBLED, GROUP_A, GROUP_B, LEGACY_VIDEO, STAGES
    PROFILE = profile
    FRAME_WIDTH, FRAME_HEIGHT = profile.final_size
    BUILD = ROOT / "build" / profile.name if profile.high_fidelity else ROOT / "build"
    CAPTIONED = profile_output(ROOT, profile, "captioned")
    POINTER_SOURCE = BUILD / "00_02a_timeline_pointer.mp4"
    POINTER_MEDIA = BUILD / "00_pointer_media"
    TIMELINE_OVERLAY = BUILD / "00_timeline_overlay_20260915.mp4"
    ASSEMBLED = BUILD / "00_bili_assembled_20260915.mp4"
    GROUP_A = BUILD / "00_science_segment.mp4"
    GROUP_B = BUILD / "00_hanataba_segment.mp4"
    LEGACY_VIDEO = (
        ROOT / "build" / "captioned" / profile.name / "legacy-01-03-high.mp4"
        if profile.high_fidelity
        else BILI / "bili-video-20260913.mp4"
    )
    STAGES = tuple(
        RenderStage(
            stage.stem,
            stage.source,
            stage.scene,
            BUILD / ("00_media" if stage.stem == "00_16g_ribbon_wand" else "00_principles_media"),
        )
        for stage in STAGES
    )


def probe_duration(path: Path) -> float:
    result = subprocess.run(("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)), check=True, capture_output=True, text=True)
    return float(result.stdout.strip())


def probe_video_duration(path: Path) -> float:
    """Read the visual timeline instead of a potentially longer audio stream."""
    result = subprocess.run(
        (
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ),
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def video_encoder_args() -> tuple[str, ...]:
    """Use the available GPU encoder for the high-resolution delivery path."""
    if PROFILE.high_fidelity:
        return (
            "-c:v", "h264_nvenc", "-preset", "p5", "-tune", "hq",
            "-rc", "vbr", "-cq", "18", "-b:v", "0",
            "-profile:v", "high", "-level:v", "5.1",
        )
    return ("-c:v", "libx264", "-preset", "medium", "-crf", "18")


def make_gif(video: Path) -> None:
    if PROFILE.high_fidelity:
        return
    run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(video), "-vf", "fps=20,scale=720:-1:flags=lanczos", "-loop", "0", str(video.with_suffix(".gif")))


def newest_scene(media: Path, scene: str) -> Path:
    matches = list(media.rglob(f"{scene}.mp4"))
    if not matches:
        raise FileNotFoundError(f"Manim did not create {scene}.mp4 under {media}")
    return max(matches, key=lambda item: item.stat().st_mtime)


def render_stage(stage: RenderStage, font: Path) -> Path:
    environment = os.environ | {"LXGW_WENKAI_FONT": str(font)} | PROFILE.environment()
    run(sys.executable, "-m", "manim", "--disable_caching", "--format=mp4", "--media_dir", str(stage.media), "-r", f"{FRAME_WIDTH},{FRAME_HEIGHT}", "--fps", str(PROFILE.fps), str(stage.source), stage.scene, env=environment)
    CAPTIONED.mkdir(parents=True, exist_ok=True)
    target = CAPTIONED / f"{stage.stem}.mp4"
    shutil.copy2(newest_scene(stage.media, stage.scene), target)
    make_gif(target)
    return target


def render_all(font: Path, stages: tuple[RenderStage, ...] = STAGES) -> dict[str, Path]:
    if not font.is_file():
        raise FileNotFoundError(f"LXGW WenKai font not found: {font}")
    return {stage.stem: render_stage(stage, font) for stage in stages}


def rendered_stages() -> dict[str, Path]:
    result = {stage.stem: CAPTIONED / f"{stage.stem}.mp4" for stage in STAGES}
    missing = [path for path in result.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing rendered chapter-00 clips:\n" + "\n".join(map(str, missing)))
    return result


def concat_to_duration(inputs: tuple[Path, ...], target: float, output: Path) -> tuple[float, ...]:
    durations = tuple(probe_duration(path) for path in inputs)
    actual = sum(durations)
    if actual <= 0:
        raise RuntimeError("Cannot retime an empty clip group.")
    factor = target / actual
    graph = "".join(f"[{index}:v]setpts=(PTS-STARTPTS)*{factor:.12f}[v{index}];" for index in range(len(inputs)))
    graph += "".join(f"[v{index}]" for index in range(len(inputs))) + f"concat=n={len(inputs)}:v=1:a=0,format=yuv420p[v]"
    output.parent.mkdir(parents=True, exist_ok=True)
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
    for path in inputs:
        command += ["-i", str(path)]
    command += ["-filter_complex", graph, "-map", "[v]", "-r", str(PROFILE.fps), *video_encoder_args(), "-movflags", "+faststart", str(output)]
    run(*command)
    return tuple(duration * factor for duration in durations)


def scaled_durations(inputs: tuple[Path, ...], target: float) -> tuple[float, ...]:
    durations = tuple(probe_duration(path) for path in inputs)
    total = sum(durations)
    if total <= 0:
        raise RuntimeError("Cannot scale an empty clip group.")
    return tuple(duration * target / total for duration in durations)


def render_pointer_loop() -> Path:
    environment = os.environ | PROFILE.environment()
    run(sys.executable, "-m", "manim", "--disable_caching", "--format=mp4", "--media_dir", str(POINTER_MEDIA), "-r", f"{PROFILE.scene_side},{PROFILE.scene_side}", "--fps", str(PROFILE.fps), str(POINTER_SCENE), "TimelinePoseLoop", env=environment)
    POINTER_SOURCE.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(newest_scene(POINTER_MEDIA, "TimelinePoseLoop"), POINTER_SOURCE)
    return POINTER_SOURCE


def read_pointer_frames() -> tuple[np.ndarray, ...]:
    if not POINTER_SOURCE.is_file():
        render_pointer_loop()
    capture = cv2.VideoCapture(str(POINTER_SOURCE))
    frames: list[np.ndarray] = []
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            scale = PROFILE.scale
            pointer = cv2.resize(
                frame[16 * scale:656 * scale, 90 * scale:630 * scale],
                (96 * scale, 114 * scale),
                interpolation=cv2.INTER_AREA,
            )
            hsv = cv2.cvtColor(pointer, cv2.COLOR_BGR2HSV)
            hsv[:, :, 1] = np.minimum(255, hsv[:, :, 1].astype(np.float32) * 2.35).astype(np.uint8)
            frames.append(cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR))
    finally:
        capture.release()
    if not frames:
        raise RuntimeError("The rendered 02a timeline pointer contains no frames.")
    return tuple(frames)


def timeline_color(value: str) -> tuple[int, int, int]:
    red, green, blue = (int(value[index:index + 2], 16) for index in (1, 3, 5))
    return blue, green, red


def stage_windows(first_group: tuple[float, ...], second_group: tuple[float, ...]) -> tuple[StageWindow, ...]:
    windows: list[StageWindow] = []
    start = 0.0
    for index, duration in enumerate((*first_group, *second_group)):
        windows.append(StageWindow("00", index, 5, start, duration))
        start += duration
    raw_legacy: list[tuple[str, tuple[str, ...], tuple[float, ...]]] = []
    total = 0.0
    for chapter, filenames in LEGACY_CHAPTERS:
        durations = tuple(probe_duration(CAPTIONED / filename) / PLAYBACK_RATE for filename in filenames)
        raw_legacy.append((chapter, filenames, durations))
        total += sum(durations)
    if total <= 0:
        raise RuntimeError("No captioned 01–03 clip durations were found for the timeline.")
    scale = LEGACY_TARGET / total
    for chapter, filenames, durations in raw_legacy:
        for index, duration in enumerate(durations):
            duration *= scale
            windows.append(StageWindow(chapter, index, len(filenames), start, duration))
            start += duration
    return tuple(windows)


def active_window(windows: tuple[StageWindow, ...], timestamp: float) -> StageWindow:
    for window in windows:
        if timestamp < window.start + window.duration:
            return window
    return windows[-1]


def chapter_boundaries(windows: tuple[StageWindow, ...]) -> tuple[float, ...]:
    boundaries: list[float] = []
    current = windows[0].chapter
    for window in windows[1:]:
        if window.chapter != current:
            boundaries.append(window.start)
            current = window.chapter
    return tuple(boundaries)


def render_timeline_overlay(total_duration: float, windows: tuple[StageWindow, ...]) -> Path:
    """Build dynamic rails in OpenCV; FFmpeg only keys the white canvas."""
    TIMELINE_OVERLAY.parent.mkdir(parents=True, exist_ok=True)
    fps = PROFILE.fps
    if PROFILE.high_fidelity and TIMELINE_OVERLAY.is_file():
        try:
            if abs(probe_video_duration(TIMELINE_OVERLAY) - total_duration) <= 1 / fps:
                return TIMELINE_OVERLAY
        except (subprocess.CalledProcessError, ValueError):
            pass
    frames = max(1, int(np.ceil(total_duration * fps)))
    writer = cv2.VideoWriter(str(TIMELINE_OVERLAY), cv2.VideoWriter_fourcc(*"mp4v"), fps, (FRAME_WIDTH, FRAME_HEIGHT))
    if not writer.isOpened():
        raise RuntimeError("OpenCV could not open the timeline overlay writer.")
    pointer_frames = read_pointer_frames()
    gray, teal, coral, purple = (timeline_color(value) for value in ("#D8DDE0", "#12B8A6", "#F07D5A", "#8B6BB7"))
    try:
        boundaries = chapter_boundaries(windows)
        scale = PROFILE.scale
        left, width, right = TIMELINE_LEFT * scale, TIMELINE_WIDTH * scale, TIMELINE_RIGHT * scale
        for index in range(frames):
            timestamp = min(total_duration, index / fps)
            progress = min(1.0, timestamp / total_duration)
            frame = np.full((FRAME_HEIGHT, FRAME_WIDTH, 3), 255, dtype=np.uint8)
            cv2.rectangle(frame, (left, 8 * scale), (right, 16 * scale), gray, thickness=-1)
            cv2.rectangle(frame, (left, 8 * scale), (left + round(width * progress), 16 * scale), teal, thickness=-1)
            for boundary in boundaries:
                x = left + round(width * boundary / total_duration)
                cv2.rectangle(frame, (x, 8 * scale), (x + scale, 16 * scale), (255, 255, 255), thickness=-1)
            window = active_window(windows, timestamp)
            cell_width = width / window.count
            local = np.clip((timestamp - window.start) / window.duration, 0.0, 1.0)
            cv2.rectangle(frame, (left, 25 * scale), (right, 32 * scale), gray, thickness=-1)
            stage_end = left + round(cell_width * (window.index + local))
            cv2.rectangle(frame, (left, 25 * scale), (stage_end, 32 * scale), coral, thickness=-1)
            for separator in range(1, window.count):
                x = left + round(cell_width * separator)
                cv2.rectangle(frame, (x, 25 * scale), (x + scale, 32 * scale), (255, 255, 255), thickness=-1)
            pointer = pointer_frames[index % len(pointer_frames)]
            pointer_x = left + round((width - pointer.shape[1]) * progress)
            pointer_y = 800 * scale
            alpha = np.clip((248 - pointer.min(axis=2)) * 5, 0, 255).astype(np.float32) / 255.0
            visible = min(pointer.shape[0], frame.shape[0] - pointer_y)
            region = frame[pointer_y:pointer_y + visible, pointer_x:pointer_x + pointer.shape[1]]
            region[:] = (region * (1 - alpha[:visible, :, None]) + pointer[:visible] * alpha[:visible, :, None]).astype(np.uint8)
            cv2.rectangle(frame, (left, 900 * scale), (right, 916 * scale), gray, thickness=-1)
            cv2.rectangle(frame, (left, 900 * scale), (left + round(width * progress), 916 * scale), purple, thickness=-1)
            writer.write(frame)
    finally:
        writer.release()
    return TIMELINE_OVERLAY


def add_progress_overlay(source: Path, target: Path, windows: tuple[StageWindow, ...]) -> Path:
    overlay = render_timeline_overlay(probe_duration(source), windows)
    target.parent.mkdir(parents=True, exist_ok=True)
    run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(source), "-i", str(overlay), "-filter_complex", "[1:v]format=rgba,colorkey=0xFFFFFF:0.08:0.12[timeline];[0:v][timeline]overlay=0:0:shortest=1,format=yuv420p[v]", "-map", "[v]", "-map", "0:a", "-r", str(PROFILE.fps), *video_encoder_args(), "-c:a", "copy", "-movflags", "+faststart", str(target))
    return target


def audio_graph() -> str:
    science_fade = SCIENCE_DURATION - MUSIC_CROSSFADE
    hanataba_start = SCIENCE_DURATION - MUSIC_CROSSFADE
    sorrow_start = SCIENCE_DURATION + SECOND_GROUP_TARGET - MUSIC_CROSSFADE
    return ";".join((
        f"[3:a]atrim=0:{SCIENCE_DURATION:.6f},asetpts=PTS-STARTPTS,afade=t=out:st={science_fade:.6f}:d={MUSIC_CROSSFADE}[science]",
        f"[4:a]atrim=0:{HANATABA_DURATION:.6f},asetpts=PTS-STARTPTS,afade=t=in:st=0:d={MUSIC_CROSSFADE},adelay={round(hanataba_start * 1000)}:all=1[hanataba]",
        f"[5:a]atrim=0:{LEGACY_SOURCE_DURATION:.6f},asetpts=PTS-STARTPTS,afade=t=in:st=0:d={MUSIC_CROSSFADE},adelay={round(sorrow_start * 1000)}:all=1[sorrow]",
        "[science][hanataba][sorrow]amix=inputs=3:duration=longest:normalize=0,aresample=48000[a]",
    ))


def assemble(clips: dict[str, Path]) -> Path:
    for path in (SCIENCE, HANATABA, SORROW, LEGACY_VIDEO):
        if not path.is_file():
            raise FileNotFoundError(path)
    first = concat_to_duration((clips[STAGES[0].stem], clips[STAGES[1].stem], clips[STAGES[2].stem]), FIRST_GROUP_TARGET, GROUP_A)
    second = concat_to_duration((clips[STAGES[3].stem], clips[STAGES[4].stem]), SECOND_GROUP_TARGET, GROUP_B)
    legacy_factor = LEGACY_TARGET / probe_video_duration(LEGACY_VIDEO)
    graph = ";".join(("[0:v]setsar=1,setpts=PTS-STARTPTS[a]", "[1:v]setsar=1,setpts=PTS-STARTPTS[b]", f"[2:v]pad={FRAME_WIDTH}:{FRAME_HEIGHT}:0:{50 * PROFILE.scale}:color=white,setsar=1,setpts=(PTS-STARTPTS)*{legacy_factor:.12f}[legacy]", "[a][b][legacy]concat=n=3:v=1:a=0[v]", audio_graph()))
    run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(GROUP_A), "-i", str(GROUP_B), "-i", str(LEGACY_VIDEO), "-i", str(SCIENCE), "-i", str(HANATABA), "-i", str(SORROW), "-filter_complex", graph, "-map", "[v]", "-map", "[a]", "-r", str(PROFILE.fps), *video_encoder_args(), "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(ASSEMBLED))
    suffix = "-high" if PROFILE.high_fidelity else ""
    return add_progress_overlay(ASSEMBLED, BILI / f"bili-video-20260915{suffix}.mp4", stage_windows(first, second))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--font", type=Path, help="Path to LXGWWenKai-Medium.ttf")
    parser.add_argument("--bili", action="store_true", help="Assemble output/bili/bili-video-20260915.mp4")
    parser.add_argument("--profile", choices=("standard", "high"), default="standard")
    parser.add_argument("--pointer-loop", action="store_true", help="Render only the 02a-style timeline pointer loop")
    parser.add_argument("--assemble-only", action="store_true", help="Reuse existing captioned 00 clips")
    parser.add_argument("--skip-cold-open", action="store_true", help="Reuse the existing 00a Ribbon Wand while rendering 00b–00e")
    parser.add_argument("--render-principles", action="store_true", help="Render only 00b–00d, then reuse 00a and 00e")
    parser.add_argument("--render-tail", action="store_true", help="Render only 00d–00e, then reuse 00a–00c")
    parser.add_argument("--render-cold-open", action="store_true", help="Render only 00a, then reuse existing 00b–00e")
    parser.add_argument("--overlay-only", action="store_true", help="Add the 20260915 timeline to an existing assembled video")
    args = parser.parse_args()
    configure_profile(get_profile(args.profile))
    if args.pointer_loop:
        print(render_pointer_loop())
        return
    if args.overlay_only:
        clips = rendered_stages()
        first = scaled_durations(tuple(clips[stage.stem] for stage in STAGES[:3]), FIRST_GROUP_TARGET)
        second = scaled_durations(tuple(clips[stage.stem] for stage in STAGES[3:]), SECOND_GROUP_TARGET)
        if not ASSEMBLED.is_file():
            parser.error(f"Missing assembled video: {ASSEMBLED}")
        print(add_progress_overlay(ASSEMBLED, BILI / "bili-video-20260915.mp4", stage_windows(first, second)))
        return
    if args.assemble_only:
        clips = rendered_stages()
    else:
        if args.font is None:
            parser.error("--font is required unless --assemble-only is used")
        if args.render_cold_open:
            selected = STAGES[:1]
        elif args.render_principles:
            selected = STAGES[1:4]
        elif args.render_tail:
            selected = STAGES[3:]
        elif args.skip_cold_open:
            selected = STAGES[1:]
        else:
            selected = STAGES
        render_all(args.font, selected)
        clips = rendered_stages()
    if args.bili:
        print(assemble(clips))


if __name__ == "__main__":
    main()
