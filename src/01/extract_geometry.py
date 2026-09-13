"""Extract color layers, line paths, and one Fourier-reconstructed contour."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np


PROJECT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = PROJECT / "素材捏" / "略ndoc的软糖动画" / "midpoint.png"
DEFAULT_OUTPUT = PROJECT / "build" / "01_geometry"
SATURATION_FACTOR = 1.28


def boost_saturation_bgr(image: np.ndarray, factor: float = SATURATION_FACTOR) -> np.ndarray:
    """Increase painted colours without changing luminance or alpha masks."""
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    hsv[:, :, 1] = np.uint8(np.clip(hsv[:, :, 1].astype(np.float32) * factor, 0, 255))
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


def resample_closed_curve(points: np.ndarray, count: int) -> np.ndarray:
    points = np.asarray(points, dtype=np.float64)
    if not np.allclose(points[0], points[-1]):
        points = np.vstack([points, points[0]])
    lengths = np.linalg.norm(np.diff(points, axis=0), axis=1)
    distance = np.r_[0.0, np.cumsum(lengths)]
    samples = np.linspace(0.0, distance[-1], count, endpoint=False)
    return np.column_stack([
        np.interp(samples, distance, points[:, 0]),
        np.interp(samples, distance, points[:, 1]),
    ])


def fourier_reconstruction(points: np.ndarray, samples: int = 512, terms: int = 80) -> tuple[np.ndarray, list[dict[str, float]]]:
    curve = resample_closed_curve(points, samples)
    signal = curve[:, 0] + 1j * curve[:, 1]
    coefficients = np.fft.fft(signal) / samples
    frequencies = np.fft.fftfreq(samples, d=1 / samples).astype(int)
    selected = np.argsort(np.abs(coefficients))[::-1][:terms]
    t = np.linspace(0.0, 1.0, samples, endpoint=False)
    reconstruction = np.zeros(samples, dtype=np.complex128)
    terms_data: list[dict[str, float]] = []
    for index in selected:
        coefficient = coefficients[index]
        frequency = int(frequencies[index])
        reconstruction += coefficient * np.exp(2j * np.pi * frequency * t)
        terms_data.append({
            "frequency": frequency,
            "real": float(coefficient.real),
            "imag": float(coefficient.imag),
        })
    return np.column_stack([reconstruction.real, reconstruction.imag]), terms_data


def save_color_layers(image: np.ndarray, ink: np.ndarray, output: Path, clusters: int) -> list[str]:
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    maximum = rgb.max(axis=2)
    minimum = rgb.min(axis=2)
    chroma = maximum.astype(np.int16) - minimum.astype(np.int16)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    near_white = (minimum > 242) & (chroma < 14)
    eligible = ~(near_white | ink.astype(bool))
    coordinates = np.flatnonzero(eligible)
    if len(coordinates) < clusters:
        return []

    pixels = rgb.reshape(-1, 3)[coordinates].astype(np.float32)
    cv2.setRNGSeed(7)
    _, labels, _ = cv2.kmeans(
        pixels,
        clusters,
        None,
        (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.8),
        3,
        cv2.KMEANS_PP_CENTERS,
    )
    paths: list[str] = []
    for cluster in range(clusters):
        cluster_mask = np.zeros(image.shape[:2], dtype=bool)
        cluster_mask.reshape(-1)[coordinates[labels.ravel() == cluster]] = True
        rgba = cv2.cvtColor(boost_saturation_bgr(image), cv2.COLOR_BGR2BGRA)
        rgba[:, :, 3] = np.where(cluster_mask, 255, 0).astype(np.uint8)
        filename = f"color_{cluster:02d}.png"
        cv2.imwrite(str(output / filename), rgba)
        paths.append(filename)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--max-paths", type=int, default=180)
    parser.add_argument("--clusters", type=int, default=6)
    arguments = parser.parse_args()

    image = cv2.imread(str(arguments.input), cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(arguments.input)
    output = arguments.output
    output.mkdir(parents=True, exist_ok=True)
    height, width = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    ink = (gray < 105).astype(np.uint8) * 255
    contours, _ = cv2.findContours(ink, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

    paths: list[tuple[float, list[list[float]]]] = []
    for contour in contours:
        perimeter = cv2.arcLength(contour, True)
        if perimeter < 26:
            continue
        simplified = cv2.approxPolyDP(contour, 0.9, True).reshape(-1, 2)
        if len(simplified) < 3:
            continue
        paths.append((float(perimeter), simplified.astype(float).tolist()))
    paths.sort(key=lambda item: item[0], reverse=True)
    paths = paths[: arguments.max_paths]
    if not paths:
        raise RuntimeError("No drawable ink paths were detected.")

    line_preview = np.full_like(image, 255)
    for _, points in paths:
        cv2.polylines(line_preview, [np.asarray(points, dtype=np.int32)], True, (0, 0, 0), 2, cv2.LINE_AA)
    cv2.imwrite(str(output / "line_preview.png"), line_preview)

    hero_points = np.asarray(paths[0][1], dtype=np.float64)
    reconstructed, coefficients = fourier_reconstruction(hero_points)
    reconstruction_preview = line_preview.copy()
    cv2.polylines(reconstruction_preview, [np.asarray(reconstructed, dtype=np.int32)], True, (100, 150, 0), 3, cv2.LINE_AA)
    cv2.imwrite(str(output / "fourier_preview.png"), reconstruction_preview)
    color_layers = save_color_layers(image, ink, output, arguments.clusters)

    payload = {
        "source": str(arguments.input),
        "width": width,
        "height": height,
        "paths": [points for _, points in paths],
        "fourier_curve": reconstructed.tolist(),
        "fourier_coefficients": coefficients,
        "color_layers": color_layers,
    }
    (output / "geometry.json").write_text(json.dumps(payload), encoding="utf-8")
    print(f"Saved {len(paths)} ink paths, {len(color_layers)} color layers, and {len(coefficients)} Fourier terms to {output}")


if __name__ == "__main__":
    main()
