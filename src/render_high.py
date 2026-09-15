"""Build the 2160x1840@60 FPS release assets without touching standard media."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(*command: str) -> None:
    print("+", " ".join(command))
    subprocess.run(command, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--font", type=Path, required=True, help="Path to LXGWWenKai-Medium.ttf")
    args = parser.parse_args()
    if not args.font.is_file():
        parser.error(f"Font file not found: {args.font}")

    for chapter in ("01", "02", "03"):
        run(sys.executable, str(ROOT / "src" / chapter / "render.py"), "--profile", "high")
    run(sys.executable, str(ROOT / "src" / "captioned" / "render.py"), "--font", str(args.font), "--profile", "high", "--bili")
    run(sys.executable, str(ROOT / "src" / "00" / "render.py"), "--font", str(args.font), "--profile", "high", "--bili")


if __name__ == "__main__":
    main()
