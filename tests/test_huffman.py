import pytest

from jpeg_compression.huffman import HuffmanTree


def test_single_symbol_uses_one_bit_code() -> None:
    assert HuffmanTree(["only"] * 3).value_to_bitstring_table() == {"only": "0"}


def test_empty_sequence_is_rejected() -> None:
    with pytest.raises(ValueError, match="empty"):
        HuffmanTree([])
