import pytest
from geneweb_py.models import CDate


@pytest.mark.parametrize(
    "s,expected",
    [
        ("ABT 1900", (1900, None, None, "approx")),
        ("BEF 1900", (1900, None, None, "before")),
        ("AFT 1900", (1900, None, None, "after")),
        ("BET 1900 AND 1910", (1900, None, None, "between_1910")),
        ("FROM 1890 TO 1900", (1890, None, None, "range_1900")),
        ("12 JAN 1900", (1900, 1, 12, "day")),
        ("JAN 1900", (1900, 1, None, "month")),
        ("1900-05-03", (1900, 5, 3, "day")),
        ("1900-05", (1900, 5, None, "month")),
        ("1900", (1900, None, None, "year")),
    ],
)
def test_cdate_from_string(s, expected):
    cd = CDate.from_string(s)
    assert cd is not None
    y, m, d, prec = expected
    assert cd.year == y
    assert cd.month == m
    assert cd.day == d
    assert cd.precision == prec


def test_cdate_fallback_year():
    cd = CDate.from_string("around 1875 or so")
    assert cd is not None
    assert cd.year == 1875
    assert cd.precision == "unknown"
