import pytest

from app.money import format_yen, with_tax


def test_with_tax() -> None:
    assert with_tax(100000) == 110000
    assert with_tax(999) == 1098  # 1098.9 → 切り捨て


@pytest.mark.parametrize("bad", [-1, 1.5, True])
def test_with_tax_rejects_invalid(bad: object) -> None:
    with pytest.raises(ValueError):
        with_tax(bad)  # type: ignore[arg-type]


def test_format_yen() -> None:
    assert format_yen(147000) == "147,000円"
