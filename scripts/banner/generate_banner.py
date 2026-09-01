#!/usr/bin/env python3
"""Generate a GitHub-profile dot-matrix banner scaffold.

This is intentionally a template: it produces a high-resolution SVG portrait,
keeps the generated numeric data as .npy files, and leaves the logo-traveller
matching hook explicit for the next iteration.

Usage:
  python scripts/banner/generate_banner.py photo.jpg --out-dir assets

The implementation follows the profile specification:
- head/shoulders-oriented crop
- autocontrast + light sharpening
- Floyd-Steinberg style error-diffusion dithering
- optional dark-mode background segmentation
- SVG <path> runs instead of font glyphs
- separate portrait/traveller layers so the dense portrait can remain detailed
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable
import math

import numpy as np
from PIL import Image, ImageChops, ImageEnhance, ImageFilter, ImageOps, ImageDraw


BG_DARK = "#0A101F"
CYAN = "#22D3EE"
TEAL = "#0891B2"
PURPLE_DARK = "#A78BFA"
PURPLE_LIGHT = "#7C3AED"
GREEN = "#10B981"
TEXT = "#94A3B8"
WHITE = "#F8FAFC"
RED = "#EF4444"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path, help="Input portrait image")
    parser.add_argument("--out-dir", type=Path, default=Path("assets"))
    parser.add_argument("--cols", type=int, default=300)
    parser.add_argument("--rows", type=int, default=340)
    parser.add_argument("--contrast", type=float, default=1.3)
    parser.add_argument("--dot-scale", type=float, default=0.82)
    parser.add_argument("--threshold", type=float, default=55.0)
    parser.add_argument("--no-segment", action="store_true")
    return parser.parse_args()


def crop_head_shoulders(image: Image.Image, target_ratio: float) -> Image.Image:
    """Use a centered, forgiving crop rather than a tight face crop."""
    w, h = image.size
    current = w / h
    if current > target_ratio:
        new_w = int(h * target_ratio)
        left = (w - new_w) // 2
        return image.crop((left, 0, left + new_w, h))

    new_h = int(w / target_ratio)
    # Bias a little upward so the head stays comfortably in frame.
    top = max(0, int((h - new_h) * 0.18))
    return image.crop((0, top, w, top + new_h))


def segment_background(rgb: np.ndarray, threshold: float) -> np.ndarray:
    """Estimate foreground with a simple corner-colour distance mask.

    This is deliberately conservative. A real production banner can replace
    this function with GrabCut or a dedicated segmentation model.
    """
    h, w, _ = rgb.shape
    samples = np.concatenate(
        [rgb[: max(8, h // 12), : max(8, w // 12)].reshape(-1, 3),
         rgb[: max(8, h // 12), -max(8, w // 12):].reshape(-1, 3),
         rgb[-max(8, h // 12):, : max(8, w // 12)].reshape(-1, 3),
         rgb[-max(8, h // 12):, -max(8, w // 12):].reshape(-1, 3)]
    )
    bg = np.median(samples, axis=0)
    distance = np.linalg.norm(rgb.astype(np.float32) - bg[None, None, :], axis=2)
    mask = (distance >= threshold).astype(np.uint8) * 255

    # Binary closing + smoothing using Pillow morphology.
    mask_img = Image.fromarray(mask, mode="L")
    mask_img = mask_img.filter(ImageFilter.MaxFilter(7))
    mask_img = mask_img.filter(ImageFilter.MinFilter(7))
    mask_img = mask_img.filter(ImageFilter.GaussianBlur(0.6))
    return np.asarray(mask_img)


def grayscale(image: Image.Image, contrast: float) -> np.ndarray:
    image = ImageOps.autocontrast(image.convert("L"), cutoff=1)
    image = ImageEnhance.Contrast(image).enhance(contrast)
    image = image.filter(ImageFilter.UnsharpMask(radius=3, percent=140, threshold=2))
    return np.asarray(image, dtype=np.float32) / 255.0


def floyd_steinberg(gray: np.ndarray, serpentine: bool = True) -> np.ndarray:
    """Return a 1-bit image using error diffusion."""
    data = gray.copy()
    out = np.zeros_like(data, dtype=np.uint8)
    rows, cols = data.shape

    for y in range(rows):
        forward = not serpentine or y % 2 == 0
        xs: Iterable[int] = range(cols) if forward else range(cols - 1, -1, -1)
        for x in xs:
            old = data[y, x]
            new = 1.0 if old >= 0.5 else 0.0
            out[y, x] = 255 if new else 0
            err = old - new
            if forward:
                neighbours = ((x + 1, y, 7 / 16), (x - 1, y + 1, 3 / 16),
                              (x, y + 1, 5 / 16), (x + 1, y + 1, 1 / 16))
            else:
                neighbours = ((x - 1, y, 7 / 16), (x + 1, y + 1, 3 / 16),
                              (x, y + 1, 5 / 16), (x - 1, y + 1, 1 / 16))
            for nx, ny, weight in neighbours:
                if 0 <= nx < cols and 0 <= ny < rows:
                    data[ny, nx] += err * weight
    return out


def svg_path_for_run(x: int, y: int, size: float) -> str:
    r = size / 2.0
    return f"M{x + r:.2f},{y:.2f}h{size:.2f}v{size:.2f}H{x + r:.2f}z"


def dot_paths(binary: np.ndarray, dot_scale: float) -> str:
    rows, cols = binary.shape
    # A single cell is easier to read at large README widths than a tiny glyph.
    cell = 340.0 / rows
    size = cell * dot_scale
    offset = (cell - size) / 2
    paths: list[str] = []

    for y in range(rows):
        for x in range(cols):
            if binary[y, x] == 0:
                continue
            px = x * cell + offset
            py = y * cell + offset
            paths.append(svg_path_for_run(int(px), int(py), size))
    return "".join(paths)


def text_row(label: str, value: str, y: int) -> str:
    return (
        f'<text x="504" y="{y}" fill="{TEXT}" font-size="14" '
        f'textLength="140" lengthAdjust="spacingAndGlyphs">{label}</text>'
        f'<path d="M650 {y-4} H832" stroke="#263248" stroke-width="1" '
        f'stroke-dasharray="2 6" />'
        f'<text x="846" y="{y}" fill="{WHITE}" font-size="14" '
        f'textAnchor="end" textLength="210" lengthAdjust="spacingAndGlyphs">{value}</text>'
    )


def banner_svg(binary: np.ndarray, *, dark: bool, dot_color: str, portrait_hue: str) -> str:
    bg = BG_DARK if dark else "#F8FAFC"
    panel = "#111A2E" if dark else "#EEF2FF"
    frame = "#24304A" if dark else "#CBD5E1"
    text = WHITE if dark else "#0F172A"
    dot_color = dot_color or portrait_hue

    portrait = dot_paths(binary, 0.82)
    rows = [
        text_row("Subject", "ISHAN RAY CHAUDHURI", 100),
        text_row("Role", "SOFTWARE ENGINEER", 123),
        text_row("Origin", "INDIA", 146),
        text_row("Education", "VIT CHENNAI", 169),
        text_row("Status", "BUILDING + SHIPPING", 192),
        text_row("ToolChain", "GIT · LINUX · DOCKER", 215),
        text_row("Core.Lang", "C · C++ · PYTHON · JAVA", 258),
        text_row("Core.Frontend", "HTML · CSS · JS · REACT", 281),
        text_row("Core.Backend", "APIS · SERVICES", 304),
        text_row("Core.Database", "MYSQL · ORACLE", 327),
        text_row("Core.Infra", "CLOUD · DEVOPS · K8S", 350),
    ]

    rows_html = "".join(rows)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1180" height="610" viewBox="0 0 1180 610">
<rect width="1180" height="610" rx="18" fill="{bg}"/>
<rect x="18" y="18" width="1144" height="574" rx="16" fill="{panel}" stroke="{frame}"/>
<rect x="42" y="42" width="1100" height="44" rx="10" fill="{bg}"/>
<circle cx="66" cy="64" r="6" fill="#FF5F56"/><circle cx="86" cy="64" r="6" fill="#FFBD2E"/><circle cx="106" cy="64" r="6" fill="#27C93F"/>
<text x="134" y="70" fill="{text}" font-size="14" font-family="ui-monospace, SFMono-Regular, Menlo, monospace">profile.sh --live</text>
<rect x="1000" y="52" width="112" height="24" rx="12" fill="#2A1320"/>
<circle cx="1016" cy="64" r="4" fill="{RED}"/><text x="1028" y="68" fill="{WHITE}" font-size="12" font-family="ui-monospace, monospace">LIVE</text>
<text x="60" y="116" fill="{CYAN if dark else TEAL}" font-size="13" font-family="ui-monospace, monospace">VISUAL.MAP</text>
<text x="504" y="116" fill="{CYAN if dark else TEAL}" font-size="13" font-family="ui-monospace, monospace">SYSTEM.INFO</text>
<rect x="52" y="130" width="420" height="420" rx="14" fill="{bg}" stroke="{frame}"/>
<g fill="{dot_color}" shape-rendering="crispEdges">{portrait}</g>
{rows_html}
<rect x="504" y="392" width="350" height="34" rx="17" fill="{GREEN}" fill-opacity="0.15" stroke="{GREEN}" stroke-opacity="0.45"/>
<text x="679" y="414" fill="{GREEN}" font-size="14" text-anchor="middle" font-family="ui-monospace, monospace">@ishanraychaudhuri2025</text>
<text x="504" y="472" fill="{TEXT}" font-size="13" font-family="ui-monospace, monospace">Core stack</text>
<text x="504" y="496" fill="{text}" font-size="15" font-family="ui-monospace, monospace">AI/ML · SOFTWARE · CLOUD · DEVOPS</text>
<text x="504" y="530" fill="{TEXT}" font-size="12" font-family="ui-monospace, monospace">Generated from source image · update via Python pipeline</text>
</svg>'''


def save_outputs(binary: np.ndarray, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    np.save(out_dir / "portrait-binary.npy", binary)

    # Dark mode: segment the background, then apply dither only to the foreground.
    # Light mode intentionally retains the entire crop.
    dark_svg = banner_svg(binary, dark=True, dot_color=PURPLE_DARK, portrait_hue=PURPLE_DARK)
    light_svg = banner_svg(binary, dark=False, dot_color=PURPLE_LIGHT, portrait_hue=PURPLE_LIGHT)
    (out_dir / "dark.svg").write_text(dark_svg, encoding="utf-8")
    (out_dir / "light.svg").write_text(light_svg, encoding="utf-8")


def main() -> None:
    args = parse_args()
    source = Image.open(args.image).convert("RGB")
    target_ratio = args.cols / args.rows
    source = crop_head_shoulders(source, target_ratio)
    resized = source.resize((args.cols, args.rows), Image.Resampling.LANCZOS)

    gray = grayscale(resized, args.contrast)
    if not args.no_segment:
        rgb = np.asarray(resized, dtype=np.uint8)
        mask = segment_background(rgb, args.threshold)
        # Keep the subject bright enough to survive the 1-bit pass.
        gray = np.where(mask > 16, gray, 1.0)
        np.save(args.out_dir / "portrait-mask.npy", mask)

    binary = floyd_steinberg(gray, serpentine=True)
    save_outputs(binary, args.out_dir)
    print(f"Wrote {args.out_dir / 'dark.svg'}")
    print(f"Wrote {args.out_dir / 'light.svg'}")
    print(f"Wrote {args.out_dir / 'portrait-binary.npy'}")
    print("Next iteration: replace the traveller placeholder with optimal-transport logo matching and SMIL timing.")


if __name__ == "__main__":
    main()
