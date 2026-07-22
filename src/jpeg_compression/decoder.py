"""Decoder for current JPC1 and legacy project bitstreams."""

from __future__ import annotations

import math
from pathlib import Path
from typing import TextIO

import numpy as np
from PIL import Image
from scipy import fftpack

from .encoder import BLOCK_SIZE, DIMENSION_BITS, FORMAT_MAGIC
from .utils import binstr_flip, load_quantization_table, zigzag_points


class BitstreamReader:
    """Read integers and Huffman symbols from the ASCII bitstream."""

    TABLE_SIZE_BITS = 16
    BLOCKS_COUNT_BITS = 32
    DC_CODE_LENGTH_BITS = 4
    CATEGORY_BITS = 4
    AC_CODE_LENGTH_BITS = 8
    RUN_LENGTH_BITS = 4
    SIZE_BITS = 4

    def __init__(self, filepath: str | Path):
        self._stream: TextIO = Path(filepath).open("r", encoding="ascii")

    def __enter__(self) -> "BitstreamReader":
        return self

    def __exit__(self, *_: object) -> None:
        self._stream.close()

    def read_dimensions(self) -> tuple[int, int] | None:
        """Read a JPC1 header, or rewind when opening a legacy bitstream."""
        prefix = self._stream.read(len(FORMAT_MAGIC))
        if prefix != FORMAT_MAGIC:
            self._stream.seek(0)
            return None
        width = self._read_uint(DIMENSION_BITS)
        height = self._read_uint(DIMENSION_BITS)
        if width <= 0 or height <= 0:
            raise ValueError("Invalid image dimensions in bitstream header")
        return width, height

    def read_int(self, size: int) -> int:
        if size == 0:
            return 0
        bits = self._read_str(size)
        return self._to_int(bits) if bits[0] == "1" else -self._to_int(binstr_flip(bits))

    def read_dc_table(self) -> dict[str, int]:
        table: dict[str, int] = {}
        for _ in range(self._read_uint(self.TABLE_SIZE_BITS)):
            category = self._read_uint(self.CATEGORY_BITS)
            code_length = self._read_uint(self.DC_CODE_LENGTH_BITS)
            table[self._read_str(code_length)] = category
        return table

    def read_ac_table(self) -> dict[str, tuple[int, int]]:
        table: dict[str, tuple[int, int]] = {}
        for _ in range(self._read_uint(self.TABLE_SIZE_BITS)):
            run_length = self._read_uint(self.RUN_LENGTH_BITS)
            size = self._read_uint(self.SIZE_BITS)
            code_length = self._read_uint(self.AC_CODE_LENGTH_BITS)
            table[self._read_str(code_length)] = (run_length, size)
        return table

    def read_blocks_count(self) -> int:
        return self._read_uint(self.BLOCKS_COUNT_BITS)

    def read_huffman_code(self, table: dict[str, object]) -> object:
        prefix = ""
        while prefix not in table:
            prefix += self._read_str(1)
        return table[prefix]

    def _read_uint(self, size: int) -> int:
        if size <= 0:
            raise ValueError("Unsigned integer size must be greater than zero")
        return self._to_int(self._read_str(size))

    def _read_str(self, length: int) -> str:
        value = self._stream.read(length)
        if len(value) != length or not set(value).issubset({"0", "1"}):
            raise ValueError("Unexpected end of file or invalid bitstream data")
        return value

    @staticmethod
    def _to_int(bits: str) -> int:
        return int(bits, 2)


def read_encoded_file(
    filepath: str | Path,
) -> tuple[np.ndarray, np.ndarray, int, int]:
    """Read coefficients and return them with padded output dimensions."""
    with BitstreamReader(filepath) as reader:
        dimensions = reader.read_dimensions()
        tables: dict[str, dict] = {}
        for table_name in ("dc_y", "ac_y", "dc_c", "ac_c"):
            tables[table_name] = (
                reader.read_dc_table() if table_name.startswith("dc") else reader.read_ac_table()
            )

        blocks_count = reader.read_blocks_count()
        if blocks_count <= 0:
            raise ValueError("Bitstream contains no image blocks")

        dc = np.empty((blocks_count, 3), dtype=np.int32)
        ac = np.empty((blocks_count, 63, 3), dtype=np.int32)

        for block_index in range(blocks_count):
            for component in range(3):
                dc_table = tables["dc_y"] if component == 0 else tables["dc_c"]
                ac_table = tables["ac_y"] if component == 0 else tables["ac_c"]
                category = int(reader.read_huffman_code(dc_table))
                dc[block_index, component] = reader.read_int(category)

                cell = 0
                while cell < 63:
                    run_length, size = reader.read_huffman_code(ac_table)
                    if (run_length, size) == (0, 0):
                        ac[block_index, cell:, component] = 0
                        break
                    if cell + run_length >= 63:
                        raise ValueError("Invalid AC run length in bitstream")
                    ac[block_index, cell : cell + run_length, component] = 0
                    cell += run_length
                    ac[block_index, cell, component] = reader.read_int(size)
                    cell += 1

    if dimensions is None:
        blocks_per_side = math.isqrt(blocks_count)
        if blocks_per_side * blocks_per_side != blocks_count:
            raise ValueError("Legacy bitstreams must contain a square number of blocks")
        width = height = blocks_per_side * BLOCK_SIZE
    else:
        width, height = dimensions
        expected_blocks = math.ceil(width / BLOCK_SIZE) * math.ceil(height / BLOCK_SIZE)
        if blocks_count != expected_blocks:
            raise ValueError(
                f"Header dimensions require {expected_blocks} blocks, found {blocks_count}"
            )

    return dc, ac, width, height


def zigzag_to_block(zigzag: list[int]) -> np.ndarray:
    """Restore a square coefficient block from zigzag order."""
    side = math.isqrt(len(zigzag))
    if side * side != len(zigzag):
        raise ValueError("Zigzag length must be a perfect square")
    block = np.empty((side, side), dtype=np.int32)
    for index, point in enumerate(zigzag_points(side, side)):
        block[point] = zigzag[index]
    return block


def dequantize(block: np.ndarray, component: str) -> np.ndarray:
    return block * load_quantization_table(component)


def idct_2d(image: np.ndarray) -> np.ndarray:
    return fftpack.idct(fftpack.idct(image.T, norm="ortho").T, norm="ortho")


def decode_image(input_path: str | Path, output_path: str | Path) -> None:
    """Decode a project bitstream and save the reconstructed RGB image."""
    dc, ac, width, height = read_encoded_file(input_path)
    blocks_per_row = math.ceil(width / BLOCK_SIZE)
    padded_width = blocks_per_row * BLOCK_SIZE
    padded_height = math.ceil(height / BLOCK_SIZE) * BLOCK_SIZE
    pixels = np.empty((padded_height, padded_width, 3), dtype=np.uint8)

    for block_index in range(len(dc)):
        row = (block_index // blocks_per_row) * BLOCK_SIZE
        column = (block_index % blocks_per_row) * BLOCK_SIZE
        for component in range(3):
            zigzag = [int(dc[block_index, component]), *ac[block_index, :, component]]
            quantized = zigzag_to_block(zigzag)
            dct_block = dequantize(quantized, "lum" if component == 0 else "chrom")
            block = np.clip(np.rint(idct_2d(dct_block) + 128), 0, 255).astype(np.uint8)
            pixels[
                row : row + BLOCK_SIZE,
                column : column + BLOCK_SIZE,
                component,
            ] = block

    image = Image.fromarray(pixels[:height, :width], "YCbCr").convert("RGB")
    image.save(output_path)
