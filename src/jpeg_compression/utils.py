"""Shared numeric helpers for the encoder and decoder."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import TypeVar

import numpy as np

T = TypeVar("T")


def load_quantization_table(component: str) -> np.ndarray:
    """Return the fixed 8x8 luminance or chrominance quantization table."""
    if component == "lum":
        return np.array(
            [
                [2, 2, 2, 2, 3, 4, 5, 6],
                [2, 2, 2, 2, 3, 4, 5, 6],
                [2, 2, 2, 2, 4, 5, 7, 9],
                [2, 2, 2, 4, 5, 7, 9, 12],
                [3, 3, 4, 5, 8, 10, 12, 12],
                [4, 4, 5, 7, 10, 12, 12, 12],
                [5, 5, 7, 9, 12, 12, 12, 12],
                [6, 6, 9, 12, 12, 12, 12, 12],
            ]
        )
    if component == "chrom":
        return np.array(
            [
                [3, 3, 5, 9, 13, 15, 15, 15],
                [3, 4, 6, 11, 14, 12, 12, 12],
                [5, 6, 9, 14, 12, 12, 12, 12],
                [9, 11, 14, 12, 12, 12, 12, 12],
                [13, 14, 12, 12, 12, 12, 12, 12],
                [15, 12, 12, 12, 12, 12, 12, 12],
                [15, 12, 12, 12, 12, 12, 12, 12],
                [15, 12, 12, 12, 12, 12, 12, 12],
            ]
        )
    raise ValueError(f"Component must be 'lum' or 'chrom', got {component!r}")


def zigzag_points(rows: int, columns: int) -> Iterator[tuple[int, int]]:
    """Yield matrix coordinates in JPEG zigzag order."""
    if rows <= 0 or columns <= 0:
        raise ValueError("Zigzag dimensions must be positive")

    row = column = 0
    moving_up = True
    for _ in range(rows * columns):
        yield row, column
        if moving_up:
            if column == columns - 1:
                row += 1
                moving_up = False
            elif row == 0:
                column += 1
                moving_up = False
            else:
                row -= 1
                column += 1
        else:
            if row == rows - 1:
                column += 1
                moving_up = True
            elif column == 0:
                row += 1
                moving_up = True
            else:
                row += 1
                column -= 1


def bits_required(number: int) -> int:
    """Return the number of magnitude bits required for a signed integer."""
    return abs(int(number)).bit_length()


def binstr_flip(bits: str) -> str:
    """Invert every bit in a binary string."""
    if not set(bits).issubset({"0", "1"}):
        raise ValueError("Binary string may contain only '0' and '1'")
    return "".join("0" if char == "1" else "1" for char in bits)


def uint_to_binstr(number: int, size: int) -> str:
    """Render an unsigned integer using exactly ``size`` bits."""
    number = int(number)
    if size <= 0 or number < 0 or number >= 1 << size:
        raise ValueError(f"{number} does not fit in {size} unsigned bits")
    return format(number, f"0{size}b")


def int_to_binstr(number: int) -> str:
    """Render a signed value using the JPEG amplitude convention."""
    number = int(number)
    if number == 0:
        return ""
    magnitude = format(abs(number), "b")
    return magnitude if number > 0 else binstr_flip(magnitude)


def flatten(groups: Iterable[Iterable[T]]) -> list[T]:
    return [item for group in groups for item in group]
