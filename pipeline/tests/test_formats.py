import gzip

import pytest

from metabo.errors import SourceFormatError
from metabo.sources.formats import check_header, english_date_to_iso


def test_check_header_reads_plain_and_gzip_files(tmp_path):
    plain = tmp_path / "a.tsv"
    plain.write_text("x\ty\n1\t2\n", encoding="utf-8")
    packed = tmp_path / "b.tsv.gz"
    packed.write_bytes(gzip.compress(b"x\ty\n1\t2\n"))
    check_header(plain, ("x", "y"))
    check_header(packed, ("x", "y"))
    with pytest.raises(SourceFormatError, match=r"a\.tsv"):
        check_header(plain, ("x", "y", "z"))


@pytest.mark.parametrize(
    "value, expected", [("02-Sep-2026", "2026-09-02"), ("29-Feb-2028", "2028-02-29")]
)
def test_english_date_to_iso(value, expected):
    assert english_date_to_iso(value, "prueba") == expected


@pytest.mark.parametrize("value", ["2026-09-02", "02-Sept-2026", "31-Feb-2026", "02-sep-2026"])
def test_english_date_to_iso_rejects_other_formats(value):
    with pytest.raises(SourceFormatError):
        english_date_to_iso(value, "prueba")
