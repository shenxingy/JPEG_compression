import pytest

from jpeg_compression.utils import bits_required, int_to_binstr, uint_to_binstr, zigzag_points


def test_zigzag_visits_each_cell_once() -> None:
    points = list(zigzag_points(8, 8))
    assert points[:6] == [(0, 0), (0, 1), (1, 0), (2, 0), (1, 1), (0, 2)]
    assert len(points) == 64
    assert len(set(points)) == 64


@pytest.mark.parametrize("number", [-12, -1, 0, 1, 12])
def test_signed_amplitude_has_required_length(number: int) -> None:
    assert len(int_to_binstr(number)) == bits_required(number)


def test_unsigned_value_must_fit() -> None:
    with pytest.raises(ValueError, match="does not fit"):
        uint_to_binstr(256, 8)
