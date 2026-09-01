#!/usr/bin/env python3
"""Template for the sparse logo-traveller layer used by the animated banner.

The master specification separates the dense portrait from a sparse traveller
layer. This file provides the matching primitive and a small SVG transform
builder; it intentionally does not guess the three logo shapes, which should
come from supplied reference artwork.

Input arrays should contain N x 2 points normalized to the same coordinate
space. For larger point sets, replace the full Hungarian assignment with an
approximate optimal-transport implementation.
"""

from __future__ import annotations

from pathlib import Path
import argparse

import numpy as np
from scipy.optimize import linear_sum_assignment


def match_points(source: np.ndarray, target: np.ndarray) -> np.ndarray:
    """Return target points assigned to each source point by minimum cost."""
    if source.ndim != 2 or target.ndim != 2 or source.shape[1] != 2 or target.shape[1] != 2:
        raise ValueError("source and target must have shape N x 2")
    if len(source) != len(target):
        raise ValueError("source and target must contain the same number of points")

    diff = source[:, None, :] - target[None, :, :]
    cost = np.sum(diff * diff, axis=2)
    rows, cols = linear_sum_assignment(cost)
    ordered = np.empty_like(target)
    ordered[rows] = target[cols]
    return ordered


def emit_keyframes(points_a: np.ndarray, points_b: np.ndarray, duration: float = 1.3) -> str:
    """Emit a compact SVG <g> block using SMIL values for point motion.

    This is a template helper. In the final generator, split the traveller
    points into individual <path> elements or small batches for the desired
    opacity and motion profile.
    """
    matched = match_points(points_a, points_b)
    fragments = []
    for i, (start, end) in enumerate(zip(points_a, matched)):
        dx = float(end[0] - start[0])
        dy = float(end[1] - start[1])
        fragments.append(
            f'<circle cx="{start[0]:.3f}" cy="{start[1]:.3f}" r="1">'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="0 0;{dx:.3f} {dy:.3f};0 0" '
            f'keyTimes="0;0.5;1" dur="{duration:.2f}s" repeatCount="indefinite" />'
            f'</circle>'
        )
    return '<g class="travellers" opacity="0">' + ''.join(fragments) + '</g>'


def load_points(path: Path) -> np.ndarray:
    points = np.load(path)
    if points.ndim != 2 or points.shape[1] != 2:
        raise ValueError(f"{path} must contain an N x 2 NumPy array")
    return points.astype(np.float64, copy=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="N x 2 source points (.npy)")
    parser.add_argument("target", type=Path, help="N x 2 target/logo points (.npy)")
    parser.add_argument("--duration", type=float, default=1.3)
    parser.add_argument("--out", type=Path, default=Path("travellers.svgfrag"))
    args = parser.parse_args()

    source = load_points(args.source)
    target = load_points(args.target)
    svg = emit_keyframes(source, target, args.duration)
    args.out.write_text(svg, encoding="utf-8")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
