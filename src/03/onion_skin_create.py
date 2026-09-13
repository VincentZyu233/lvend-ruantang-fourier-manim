"""10: flipbook onion skins redraw each pose with native Manim Create."""

from __future__ import annotations

from manim import FadeOut, Scene

from common import GHOST, configure_canvas, flood_colors, native_create, psd_assets, video_assets


configure_canvas()

MODES = {
    "single": ("cascade", 0.16),
    "layered": ("chapters", 0.22),
    "longtail": ("outline_first", 0.12),
}
DRAW_DURATIONS = {
    # Both sources now use ten poses.  PSD has more independent paths, but its
    # former per-pose Create duration is deliberately cut in half.
    "video": 0.72,
    "psd": 0.82,
}
GHOST_DURATION = 0.18
COLOR_FADE_DURATION = 0.28
COLOR_HOLD_DURATION = 0.25


class OnionSkinFlow(Scene):
    source = "video"
    mode = "single"

    def construct(self) -> None:
        video_lines, video_colors = video_assets()
        if self.source == "video":
            line_poses, color_poses = video_lines, video_colors
        else:
            line_poses, color_poses = psd_assets()
        style, ghost_opacity = MODES[self.mode]
        draw_time = DRAW_DURATIONS[self.source]

        self.wait(0.18)
        current = line_poses[0].copy()
        native_create(self, current, style, draw_time)
        current_color = color_poses[0].copy()
        flood_colors(self, current_color, run_time=COLOR_FADE_DURATION)
        self.wait(COLOR_HOLD_DURATION)

        for target, target_color in zip(line_poses[1:], color_poses[1:]):
            transitions = [current.animate.set_stroke(GHOST, width=1.2, opacity=ghost_opacity)]
            if current_color.submobjects:
                transitions.append(FadeOut(current_color))
            self.play(*transitions, run_time=GHOST_DURATION)
            next_pose = target.copy()
            native_create(self, next_pose, style, draw_time)
            self.remove(current)
            current = next_pose
            current_color = target_color.copy()
            flood_colors(self, current_color, run_time=COLOR_FADE_DURATION)
            self.wait(COLOR_HOLD_DURATION)
        self.wait(0.85)


class Flow10aVideoSingle(OnionSkinFlow):
    source, mode = "video", "single"


class Flow10bVideoLayered(OnionSkinFlow):
    source, mode = "video", "layered"


class Flow10cVideoLongTail(OnionSkinFlow):
    source, mode = "video", "longtail"


class Flow10dPsdSingle(OnionSkinFlow):
    source, mode = "psd", "single"


class Flow10ePsdLayered(OnionSkinFlow):
    source, mode = "psd", "layered"


class Flow10fPsdLongTail(OnionSkinFlow):
    source, mode = "psd", "longtail"
