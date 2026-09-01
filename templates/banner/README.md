# Animated Banner Template

The source specification treats the banner as the main creative part of the profile. It calls for a 1180×610 terminal-style window with a portrait panel, a `SYSTEM.INFO` panel, a pulsing `LIVE` badge, a handle pill, and a theme-aware dark/light SVG pair. fileciteturn0file1L53-L67

## Generate the portrait scaffold

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
pip install -r scripts/banner/requirements.txt
python scripts/banner/generate_banner.py /path/to/portrait.jpg --out-dir assets
```

Outputs:

```text
assets/
├── dark.svg
├── light.svg
├── portrait-binary.npy
└── portrait-mask.npy
```

## What the scaffold already covers

- head-and-shoulders crop rather than a tight face crop
- 300×340 default portrait grid
- autocontrast and restrained 1.3× contrast boost
- UnsharpMask sharpening
- serpentine Floyd–Steinberg error diffusion
- optional background-distance segmentation for dark mode
- crisp SVG path geometry instead of font glyphs
- persisted `.npy` source data so the SVG is not the only source of truth

These choices mirror the master prompt's specified portrait pipeline. fileciteturn0file1L57-L67

## Animation extension point

The specification separates the dense portrait from a sparse traveller layer: roughly 17k portrait dots and roughly 900 travelling dots matched between logo shapes. It explicitly warns that trying to make every portrait dot travel destroys the portrait's resolution. fileciteturn0file1L76-L85

The current Python file therefore keeps the traveller/SMIL stage as the next extension rather than pretending that a static template is already the final animation.

## Quality rule

Do visual validation in a browser. The master prompt warns that CairoSVG is useful for rendering but does not accurately reproduce every SMIL/transform behavior used by the animated SVG. fileciteturn0file1L152-L159
