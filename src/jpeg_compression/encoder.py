"""Encoder for the project's educational JPEG-like bitstream format."""

from __future__ import annotations

from pathlib import Path
from typing import TextIO

import numpy as np
from PIL import Image
from scipy import fftpack

from .huffman import HuffmanTree
from .utils import (
    bits_required,
    flatten,
    int_to_binstr,
    load_quantization_table,
    uint_to_binstr,
    zigzag_points,
)

FORMAT_MAGIC = "JPC1"
DIMENSION_BITS = 32
BLOCK_SIZE = 8


def quantize(block: np.ndarray, component: str) -> np.ndarray:
    """Quantize one DCT block using the luminance or chrominance table."""
    table = load_quantization_table(component)
    return (block / table).round().astype(np.int32)


def block_to_zigzag(block: np.ndarray) -> np.ndarray:
    """Flatten a two-dimensional block in JPEG zigzag order."""
    return np.array([block[point] for point in zigzag_points(*block.shape)])


def dct_2d(image: np.ndarray) -> np.ndarray:
    """Apply an orthonormal two-dimensional discrete cosine transform."""
    return fftpack.dct(fftpack.dct(image.T, norm="ortho").T, norm="ortho")


def run_length_encode(arr: np.ndarray) -> tuple[list[tuple[int, int]], list[str]]:
    """Encode AC coefficients as JPEG-style ``(zero run, bit size)`` symbols."""
    nonzero_indices = np.flatnonzero(arr)
    last_nonzero = int(nonzero_indices[-1]) if nonzero_indices.size else -1

    symbols: list[tuple[int, int]] = []
    values: list[str] = []
    run_length = 0

    for index, element in enumerate(arr):
        value = int(element)
        if index > last_nonzero:
            symbols.append((0, 0))
            values.append("")
            break
        if value == 0 and run_length < 15:
            run_length += 1
            continue

        size = bits_required(value)
        symbols.append((run_length, size))
        values.append(int_to_binstr(value))
        run_length = 0

    return symbols, values


def _write_huffman_tables(stream: TextIO, tables: dict[str, dict]) -> None:
    for table_name in ("dc_y", "ac_y", "dc_c", "ac_c"):
        table = tables[table_name]
        stream.write(uint_to_binstr(len(table), 16))

        for key, code in table.items():
            if table_name.startswith("dc"):
                stream.write(uint_to_binstr(int(key), 4))
                stream.write(uint_to_binstr(len(code), 4))
            else:
                run_length, size = key
                stream.write(uint_to_binstr(int(run_length), 4))
                stream.write(uint_to_binstr(int(size), 4))
                stream.write(uint_to_binstr(len(code), 8))
            stream.write(code)


def write_encoded_file(
    filepath: str | Path,
    dc: np.ndarray,
    ac: np.ndarray,
    tables: dict[str, dict],
    width: int,
    height: int,
) -> None:
    """Serialize coefficients and Huffman tables to a JPC1 text bitstream."""
    output_path = Path(filepath)
    try:
        stream = output_path.open("w", encoding="ascii")
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Output directory does not exist: {output_path.parent}") from exc

    with stream:
        stream.write(FORMAT_MAGIC)
        stream.write(uint_to_binstr(width, DIMENSION_BITS))
        stream.write(uint_to_binstr(height, DIMENSION_BITS))
        _write_huffman_tables(stream, tables)
        stream.write(uint_to_binstr(len(dc), 32))

        for block_index in range(len(dc)):
            for component in range(3):
                category = bits_required(int(dc[block_index, component]))
                symbols, values = run_length_encode(ac[block_index, :, component])
                dc_table = tables["dc_y"] if component == 0 else tables["dc_c"]
                ac_table = tables["ac_y"] if component == 0 else tables["ac_c"]

                stream.write(dc_table[category])
                stream.write(int_to_binstr(int(dc[block_index, component])))
                for symbol, value in zip(symbols, values):
                    stream.write(ac_table[symbol])
                    stream.write(value)


def encode_image(input_path: str | Path, output_path: str | Path) -> None:
    """Encode an image to the custom JPC1 educational bitstream."""
    with Image.open(input_path) as source:
        ycbcr = source.convert("YCbCr")
        pixels = np.asarray(ycbcr, dtype=np.uint8)

    height, width = pixels.shape[:2]
    padded_height = ((height + BLOCK_SIZE - 1) // BLOCK_SIZE) * BLOCK_SIZE
    padded_width = ((width + BLOCK_SIZE - 1) // BLOCK_SIZE) * BLOCK_SIZE
    pixels = np.pad(
        pixels,
        ((0, padded_height - height), (0, padded_width - width), (0, 0)),
        mode="edge",
    )

    blocks_count = (padded_height // BLOCK_SIZE) * (padded_width // BLOCK_SIZE)
    dc = np.empty((blocks_count, 3), dtype=np.int32)
    ac = np.empty((blocks_count, 63, 3), dtype=np.int32)

    block_index = 0
    for row in range(0, padded_height, BLOCK_SIZE):
        for column in range(0, padded_width, BLOCK_SIZE):
            for component in range(3):
                block = (
                    pixels[
                        row : row + BLOCK_SIZE,
                        column : column + BLOCK_SIZE,
                        component,
                    ].astype(np.int32)
                    - 128
                )
                quantized = quantize(dct_2d(block), "lum" if component == 0 else "chrom")
                zigzag = block_to_zigzag(quantized)
                dc[block_index, component] = zigzag[0]
                ac[block_index, :, component] = zigzag[1:]
            block_index += 1

    tables = {
        "dc_y": HuffmanTree(np.vectorize(bits_required)(dc[:, 0])).value_to_bitstring_table(),
        "ac_y": HuffmanTree(
            flatten(run_length_encode(ac[index, :, 0])[0] for index in range(blocks_count))
        ).value_to_bitstring_table(),
        "dc_c": HuffmanTree(np.vectorize(bits_required)(dc[:, 1:].flat)).value_to_bitstring_table(),
        "ac_c": HuffmanTree(
            flatten(
                run_length_encode(ac[index, :, component])[0]
                for index in range(blocks_count)
                for component in (1, 2)
            )
        ).value_to_bitstring_table(),
    }

    write_encoded_file(output_path, dc, ac, tables, width, height)
