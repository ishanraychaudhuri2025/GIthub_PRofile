#!/usr/bin/env python3
"""Generate a GitHub-profile dot-matrix banner scaffold.

The script creates a theme-ready SVG portrait plus .npy source data. It is a
working foundation for the animated banner; the sparse logo-traveller layer
and SMIL choreography are kept as an explicit extension point instead of
pretending a static scaffold is the finished animation.

Usage:
  python scripts/banner/generate_banner.py photo.jpg --out-dir assets
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

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
    parser.add_argument("--threshold", type=float, default=55.0)
    parser.add_argument("--dot-scale", type=float, default=0.82)
    parser.add_argument("--no-segment", action="store_true")
    return parser.parse_args()


def crop_head_shoulders(image: Image.Image, target_ratio: float) -> Image.Image:
    """Use a forgiving crop rather than an over-zoomed face crop."""
    w, h = image.size
    current = w / h
    if current > target_ratio:
        new_w = int(h * target_ratio)
        left = (w - new_w) // 2
        return image.crop((left, 0, left + new_w, h))

    new_h = int(w / target_ratio)
    top = max(0, int((h - new_h) * 0.18))
    return image.crop((0, top, w, top + new_h))


def segment_background(rgb: np.ndarray, threshold: float) -> np.ndarray:
    """Estimate foreground using corner-colour distance.

    Replace this function with a stronger segmentation method for a production
    banner if the source photo has shadows, gradients, or a busy background.
    """
    h, w, _ = rgb.shape
    hh, ww = max(8, h // 12), max(8, w // 12)
    samples = np.concatenate(
        [rgb[:hh, :ww].reshape(-1, 3),
         rgb[:hh, -ww:].reshape(-1, 3),
         rgb[-hh:, :ww].reshape(-1, 3),
         rgb[-hh:, -ww:].reshape(-1, 3)]
    )
    bg = np.median(samples, axis=0)
    distance = np.linalg.norm(rgb.astype(np.float32) - bg[None, None, :], axis=2)
    mask = (distance >= threshold).astype(np.uint8) * 255

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
            neighbours = (
                ((x + 1, y, 7 / 16), (x - 1, y + 1, 3 / 16),
                 (x, y + 1, 5 / 16), (x + 1, y + 1, 1 / 16))
                if forward else
                ((x - 1, y, 7 / 16), (x + 1, y + 1, 3 / 16),
                 (x, y + 1, 5 / 16), (x - 1, y + 1, 1 / 16))
            )
            for nx, ny, weight in neighbours:
                if 0 <= nx < cols and 0 <= ny < rows:
                    data[ny, nx] += err * weight
    return out


def svg_path_for_dot(x: float, y: float, size: float) -> str:
    return f"M{x:.2f},{y:.2f}h{size:.2f}v{size:.2f}h-{size:.2f}z"


def dot_paths(binary: np.ndarray, dot_scale: float, offset_x: float = 52, offset_y: float = 130) -> str:
    rows, _ = binary.shape
    cell = 420.0 / rows
    size = cell * dot_scale
    inset = (cell - size) / 2
    parts: list[str] = []

    for y, row in enumerate(binary):
        for x, value in enumerate(row):
            if value == 0:
                continue
            px = offset_x + x * cell + inset
            py = offset_y + y * cell + inset
            parts.append(svg_path_for_dot(px, py, size))
    return "".join(parts)


def text_row(label: str, value: str, y: int, value_fill: str) -> str:
    return (
        f'<text x="504" y="{y}" fill="{TEXT}" font-size="14" '
        f'textLength="140" lengthAdjust="spacingAndGlyphs">{label}</text>'
        f'<path d="M650 {y-4} H832" stroke="#263248" stroke-width="1" stroke-dasharray="2 6" />'
        f'<text x="846" y="{y}" fill="{value_fill}" font-size="14" text-anchor="end" '
        f'textLength="210" lengthAdjust="spacingAndGlyphs">{value}</text>'
    )


def banner_svg(binary: np.ndarray, *, dark: bool, dot_color: str) -> str:
    bg = BG_DARK if dark else "#F8FAFC"
    panel = "#111A2E" if dark else "#EEF2FF"
    frame = "#24304A" if dark else "#CBD5E1"
    text = WHITE if dark else "#0F172A"
    portrait = dot_paths(binary, 0.82)

    rows = [
        text_row("Subject", "ISHAN RAY CHAUDHURI", 100, text),
        text_row("Role", "SOFTWARE ENGINEER", 123, text),
        text_row("Origin", "INDIA", 146, text),
        text_row("Education", "VIT CHENNAI", 169, text),
        text_row("Status", "BUILDING + SHIPPING", 192, text),
        text_row("ToolChain", "GIT · LINUX · DOCKER", 215, text),
        text_row("Core.Lang", "C · C++ · PYTHON · JAVA", 258, text),
        text_row("Core.Frontend", "HTML · CSS · JS · REACT", 281, text),
        text_row("Core.Backend", "APIS · SERVICES", 304, text),
        text_row("Core.Database", "MYSQL · ORACLE", 327, text),
        text_row("Core.Infra", "CLOUD · DEVOPS · K8S", 350, text),
    ]

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
{''.join(rows)}
<rect x="504" y="392" width="350" height="34" rx="17" fill="{GREEN}" fill-opacity="0.15" stroke="{GREEN}" stroke-opacity="0.45"/>
<text x="679" y="414" fill="{GREEN}" font-size="14" text-anchor="middle" font-family="ui-monospace, monospace">@ishanraychaudhuri2025</text>
<text x="504" y="472" fill="{TEXT}" font-size="13" font-family="ui-monospace, monospace">Core stack</text>
<text x="504" y="496" fill="{text}" font-size="15" font-family="ui-monospace, monospace">AI/ML · SOFTWARE · CLOUD · DEVOPS</text>
<text x="504" y="530" fill="{TEXT}" font-size="12" font-family="ui-monospace, monospace">Generated from source image · update via Python pipeline</text>
</svg>'''


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    source = Image.open(args.image).convert("RGB")
    source = crop_head_shoulders(source, args.cols / args.rows)
    resized = source.resize((args.cols, args.rows), Image.Resampling.LANCZOS)
    gray = grayscale(resized, args.contrast)

    mask = None
    if not args.no_segment:
        rgb = np.asarray(resized, dtype=np.uint8)
        mask = segment_background(rgb, args.threshold)
        np.save(args.out_dir / "portrait-mask.npy", mask)

    # Dark mode: background is removed, so only the lit subject is retained.
    dark_gray = np.where(mask > 16, gray, 0.0) if mask is not None else gray
    # Light mode: invert so darker photo regions become visible dots on light UI.
    light_gray = 1.0 - gray

    dark_binary = floyd_steinberg(dark_gray, serpentine=True)
    light_binary = floyd_steinberg(light_gray, serpentine=True)
    np.save(args.out_dir / "portrait-dark.npy", dark_binary)
    np.save(args.out_dir / "portrait-light.npy", light_binary)

    (args.out_dir / "dark.svg").write_text(
        banner_svg(dark_binary, dark=True, dot_color=PURPLE_DARK), encoding="utf-8"
    )
    (args.out_dir / "light.svg").write_text(
        banner_svg(light_binary, dark=False, dot_color=PURPLE_LIGHT), encoding="utf-8"
    )

    print(f"Wrote {args.out_dir / 'dark.svg'}")
    print(f"Wrote {args.out_dir / 'light.svg'}")
    print(f"Wrote {args.out_dir / 'portrait-dark.npy'} and portrait-light.npy")
    print("Extension point: add the ~900-dot optimal-transport traveller layer and SMIL timeline.")


if __name__ == "__main__":
    main()
