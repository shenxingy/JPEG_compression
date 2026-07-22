# JPEG Compression in Python

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)

A compact, readable implementation of the main ideas behind JPEG compression. The project is
designed for learning: it exposes color conversion, 8×8 block transforms, quantization, zigzag
scanning, run-length encoding, and Huffman coding as ordinary Python code.

> **Important:** this project writes its own `.jpc` learning format. It demonstrates the JPEG
> pipeline, but it does **not** produce a standards-compliant `.jpg` bitstream and should not be
> used as a production image codec.

## How it works

```mermaid
flowchart LR
    A[RGB image] --> B[YCbCr conversion]
    B --> C[8×8 blocks]
    C --> D[2D DCT]
    D --> E[Quantization]
    E --> F[Zigzag scan]
    F --> G[Run-length encoding]
    G --> H[Huffman coding]
    H --> I[.jpc bitstream]
```

The decoder reverses these stages, applies the inverse DCT, clips all reconstructed channels to
the valid 8-bit range, and converts the image back to RGB.

## Highlights

- Supports rectangular images and dimensions that are not multiples of 8.
- Preserves the original image dimensions in the `JPC1` stream header.
- Includes a command-line interface and a small public Python API.
- Handles one-symbol Huffman tables correctly, including uniform images.
- Detects truncated or malformed streams instead of reading forever.
- Can still decode the repository's original square legacy bitstream.
- Includes tests for the codec, Huffman edge cases, and numeric helpers.

## Quick start

Clone the repository and install it in a virtual environment:

```bash
git clone https://github.com/shenxingy/JPEG_compression.git
cd JPEG_compression
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Encode any image format supported by Pillow:

```bash
jpeg-compression encode examples/input/astronaut.webp astronaut.jpc
```

Decode it to a regular image:

```bash
jpeg-compression decode astronaut.jpc reconstructed.png
```

The module entry point is equivalent if you prefer not to use the installed command:

```bash
python -m jpeg_compression encode input.png output.jpc
python -m jpeg_compression decode output.jpc restored.png
```

## Python API

```python
from jpeg_compression import decode_image, encode_image

encode_image("input.png", "output.jpc")
decode_image("output.jpc", "restored.png")
```

## Example

| Original crop | Reconstructed image |
| --- | --- |
| ![Original astronaut](examples/output/astronaut_crop.png) | ![Reconstructed astronaut](examples/output/reconstructed.jpg) |

The transform is intentionally lossy. Exact output depends on the fixed luminance and chrominance
quantization tables in `src/jpeg_compression/utils.py`.

## Repository layout

```text
JPEG_compression/
├── src/jpeg_compression/       # Installable encoder, decoder, CLI, and helpers
├── tests/                      # Unit and end-to-end tests
├── examples/
│   ├── input/                  # Source image
│   └── output/                 # Reconstruction and channel visualizations
├── scripts/
│   └── generate_channel_examples.py
├── pyproject.toml              # Package metadata and tool configuration
└── README.md
```

## Development

Install the development dependencies and run the checks:

```bash
python -m pip install -e ".[dev]"
pytest
ruff check .
```

To regenerate the Y, Cb, and Cr channel examples:

```bash
python scripts/generate_channel_examples.py
```

## Stream format and limitations

The current stream begins with the ASCII marker `JPC1`, followed by 32-bit width and height
fields, serialized Huffman tables, a block count, and the encoded coefficients. Bits are stored as
the characters `0` and `1` to keep the format inspectable. This is useful for teaching, but it adds
substantial storage overhead compared with packed binary data.

The implementation also deliberately omits several parts of the JPEG standard, including marker
segments, configurable quality levels, chroma subsampling, DC differential coding, byte stuffing,
and optimized binary I/O.

## Acknowledgements

This implementation was originally adapted from:

- [ghallak/jpeg-python](https://github.com/ghallak/jpeg-python)
- [zhangqizky/jpeg-compression](https://github.com/zhangqizky/jpeg-compression)

The current version reorganizes the project, documents the custom format, preserves image
dimensions, validates malformed input, and fixes channel overflow artifacts during reconstruction.
