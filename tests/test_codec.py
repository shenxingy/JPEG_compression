from pathlib import Path

import numpy as np
from PIL import Image

from jpeg_compression import decode_image, encode_image


def test_round_trip_preserves_non_aligned_rectangular_dimensions(tmp_path: Path) -> None:
    height, width = 10, 13
    rows, columns = np.mgrid[:height, :width]
    pixels = np.stack(
        (
            columns * 255 // (width - 1),
            rows * 255 // (height - 1),
            (rows + columns) * 255 // (height + width - 2),
        ),
        axis=-1,
    ).astype(np.uint8)

    source = tmp_path / "source.png"
    encoded = tmp_path / "image.jpc"
    restored = tmp_path / "restored.png"
    Image.fromarray(pixels, "RGB").save(source)

    encode_image(source, encoded)
    decode_image(encoded, restored)

    with Image.open(restored) as result:
        reconstructed = np.asarray(result.convert("RGB"), dtype=np.int16)
        assert result.size == (width, height)

    mean_absolute_error = np.abs(reconstructed - pixels.astype(np.int16)).mean()
    assert mean_absolute_error < 12


def test_uniform_image_uses_single_symbol_huffman_tables(tmp_path: Path) -> None:
    source = tmp_path / "uniform.png"
    encoded = tmp_path / "uniform.jpc"
    restored = tmp_path / "restored.png"
    Image.new("RGB", (8, 8), (120, 120, 120)).save(source)

    encode_image(source, encoded)
    decode_image(encoded, restored)

    assert encoded.read_text(encoding="ascii").startswith("JPC1")
    assert Image.open(restored).size == (8, 8)
