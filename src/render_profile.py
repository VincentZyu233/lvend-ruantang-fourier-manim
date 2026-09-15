"""Shared render profiles for the standard and high-fidelity video pipelines."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RenderProfile:
    name: str
    scale: int
    fps: int
    high_fidelity: bool

    @property
    def scene_side(self) -> int:
        return 720 * self.scale

    @property
    def chapter00_size(self) -> tuple[int, int]:
        return 1080 * self.scale, 920 * self.scale

    @property
    def final_size(self) -> tuple[int, int]:
        return 1080 * self.scale, 920 * self.scale

    @property
    def footer_height(self) -> int:
        return 100 * self.scale

    @property
    def grid_tile(self) -> int:
        return 360 * self.scale

    @property
    def gif_fps(self) -> int:
        return 20

    def environment(self) -> dict[str, str]:
        return {
            "FOURIER_RENDER_SCALE": str(self.scale),
            "FOURIER_RENDER_FPS": str(self.fps),
        }


STANDARD = RenderProfile("standard", scale=1, fps=20, high_fidelity=False)
HIGH = RenderProfile("high", scale=2, fps=60, high_fidelity=True)


def get_profile(name: str) -> RenderProfile:
    if name == STANDARD.name:
        return STANDARD
    if name == HIGH.name:
        return HIGH
    raise ValueError(f"Unknown render profile: {name}")


def profile_output(root: Path, profile: RenderProfile, standard_name: str) -> Path:
    """Keep existing standard output locations stable and isolate high assets."""
    if profile.high_fidelity:
        return root / "output" / "high" / standard_name
    return root / "output" / standard_name
