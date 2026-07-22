"""Small Huffman tree implementation used by the educational codec."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
import heapq
from itertools import count
from typing import Generic, Hashable, Iterable, TypeVar

Symbol = TypeVar("Symbol", bound=Hashable)


@dataclass(order=True)
class _Node(Generic[Symbol]):
    frequency: int
    order: int
    value: Symbol | None = field(compare=False, default=None)
    left: "_Node[Symbol] | None" = field(compare=False, default=None)
    right: "_Node[Symbol] | None" = field(compare=False, default=None)

    @property
    def is_leaf(self) -> bool:
        return self.value is not None


class HuffmanTree(Generic[Symbol]):
    """Build a deterministic Huffman code table for a non-empty symbol stream."""

    def __init__(self, values: Iterable[Symbol]):
        frequencies = Counter(values)
        if not frequencies:
            raise ValueError("Cannot build a Huffman tree from an empty sequence")

        sequence = count()
        queue = [
            _Node(frequency, next(sequence), value=value)
            for value, frequency in frequencies.items()
        ]
        heapq.heapify(queue)

        while len(queue) > 1:
            left = heapq.heappop(queue)
            right = heapq.heappop(queue)
            heapq.heappush(
                queue,
                _Node(
                    left.frequency + right.frequency,
                    next(sequence),
                    left=left,
                    right=right,
                ),
            )

        self._root = queue[0]
        self._table: dict[Symbol, str] = {}

    def value_to_bitstring_table(self) -> dict[Symbol, str]:
        """Return a symbol-to-prefix-code mapping."""
        if not self._table:
            self._build_table(self._root, "")
        return self._table.copy()

    def _build_table(self, node: _Node[Symbol], prefix: str) -> None:
        if node.is_leaf:
            # A one-symbol alphabet still needs one bit so the decoder can make progress.
            self._table[node.value] = prefix or "0"  # type: ignore[index]
            return
        if node.left is not None:
            self._build_table(node.left, prefix + "0")
        if node.right is not None:
            self._build_table(node.right, prefix + "1")
