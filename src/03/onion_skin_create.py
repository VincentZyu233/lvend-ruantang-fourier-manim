"""10: flipbook onion skins redraw each pose with native Manim Create."""

from __future__ import annotations

from manim import FadeOut, Scene

from common import GHOST, configure_canvas, flood_colors, native_create, psd_assets, video_assets


configure_canvas()

MODES = {
    "single": ("cascade", 1.18, 0.16),
    "layered": ("chapters", 1.28, 0.22),
    "longtail": ("outline_first", 1.38, 0.12),
}


class OnionSkinFlow(Scene):
    source = "video"
    mode = "single"

    def construct(self) -> None:
        video_lines, video_colors = video_assets()
        if self.source == "video":
            line_poses, color_poses = video_lines, video_colors
        else:
            line_poses, color_poses = psd_assets(video_colors)
        style, draw_time, ghost_opacity = MODES[self.mode]

        self.wait(0.18)
        current = line_poses[0].copy()
        native_create(self, current, style, draw_time)

        for target in line_poses[1:]:
            self.play(current.animate.set_stroke(GHOST, width=1.2, opacity=ghost_opacity), run_time=0.18)
            next_pose = target.copy()
            native_create(self, next_pose, style, draw_time)
            self.remove(current)
            current = next_pose
        self.wait(0.24)
        flood_colors(self, color_poses[-1], run_time=0.8)
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
