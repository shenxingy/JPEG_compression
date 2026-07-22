"""Generate the Y, Cb, and Cr channel visualizations used by the README."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


def generate_examples(input_path: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    with Image.open(input_path) as source:
        image = source.convert("RGB").crop((0, 0, 1024, 1024))

    image.save(output_dir / "astronaut_crop.png")
    ycbcr = image.convert("YCbCr")
    y, cb, cr = ycbcr.split()
    neutral = Image.new("L", ycbcr.size, 128)

    Image.merge("YCbCr", (neutral, cb, cr)).convert("RGB").save(
        output_dir / "astronaut_without_y.png"
    )
    Image.merge("YCbCr", (y, neutral, neutral)).convert("RGB").save(
        output_dir / "astronaut_brightness.png"
    )
    Image.merge("YCbCr", (neutral, neutral, cr)).convert("RGB").save(
        output_dir / "cr_only_image.jpg"
    )
    Image.merge("YCbCr", (neutral, cb, neutral)).convert("RGB").save(
        output_dir / "cb_only_image.jpg"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("examples/input/astronaut.webp"),
        help="source image (default: examples/input/astronaut.webp)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("examples/output"),
        help="output directory (default: examples/output)",
    )
    args = parser.parse_args()
    generate_examples(args.input, args.output_dir)


if __name__ == "__main__":
    main()
