"""Extractor de ENZYME con un servidor simulado: ninguna prueba usa la red.

Las entradas de muestra solo imitan el formato de enzclass.txt y enzyme.dat; sus
números EC y nombres son ficticios y no se usan como datos.
"""

import pytest
from conftest import FakeFtp

from metabo.errors import SourceFormatError
from metabo.sources import enzyme

CLASS = b"""Description: Definition of enzyme classes, subclasses and sub-subclasses
Name:        enzclass.txt
Release:     02-Sep-2026

9. -. -.-  Clase ficticia.
1. 9. 9.-    Sub-subclase ficticia.
"""
DAT = b"""CC   -----------------------------------------------------------------------
CC   Release of 02-Sep-2026
CC   -----------------------------------------------------------------------
//
ID   1.9.9.9
DE   enzima ficticia.
CA   A = B.
//
"""


def files(**overrides: bytes) -> dict[str, bytes]:
    served = {enzyme.CLASS_URL: CLASS, enzyme.DAT_URL: DAT}
    for name, body in overrides.items():
        served[f"{enzyme.BASE_URL}/{name}"] = body
    return served


def test_releases_are_read_as_iso_dates():
    assert enzyme.class_release(CLASS.decode()) == "2026-09-02"
    assert enzyme.dat_release(DAT.decode()) == "2026-09-02"


def test_extract_downloads_into_release_folder(run_extractor):
    raw_dir, (version, records) = run_extractor(enzyme.extract, FakeFtp(files()))
    assert version == "2026-09-02"
    assert [r.archivo for r in records] == [
        "enzyme/2026-09-02/enzclass.txt",
        "enzyme/2026-09-02/enzyme.dat",
    ]
    assert (raw_dir / "enzyme/2026-09-02/enzyme.dat").read_bytes() == DAT
    assert all(r.licencia == "CC BY 4.0" for r in records)


def test_mismatched_releases_stop_the_extraction(run_extractor):
    newer = DAT.replace(b"02-Sep-2026", b"07-Oct-2026")
    with pytest.raises(SourceFormatError, match="2026-10-07"):
        run_extractor(enzyme.extract, FakeFtp(files(**{"enzyme.dat": newer})))


@pytest.mark.parametrize(
    "name, body",
    [
        ("enzclass.txt", CLASS.replace(b"Release:", b"Version:")),
        ("enzclass.txt", CLASS.replace(b"02-Sep-2026", b"2026-09-02")),
        ("enzclass.txt", CLASS.split(b"\n\n")[0] + b"\n"),
        ("enzyme.dat", DAT.replace(b"DE   ", b"XX   ")),
        ("enzyme.dat", DAT.replace(b"Release of", b"Version")),
    ],
)
def test_changed_format_stops_the_extraction(run_extractor, name, body):
    with pytest.raises(SourceFormatError):
        run_extractor(enzyme.extract, FakeFtp(files(**{name: body})))


def test_only_official_enzyme_urls_are_requested(run_extractor):
    server = FakeFtp(files())
    run_extractor(enzyme.extract, server)
    assert all(
        url.startswith("https://ftp.expasy.org/databases/enzyme/") for url in server.requests
    )


ENTRIES = """CC   Release of 02-Sep-2026
//
ID   7.99.99.1
DE   enzima ficticia de
DE   nombre largo.
//
ID   7.99.99.2
DE   Transferred entry: 7.99.99.1 and 7.99.99.3.
//
ID   7.99.99.3
DE   Deleted entry.
//
ID   7.99.99.n4
DE   enzima ficticia preliminar.
//
"""


def test_parse_entries_marks_transferred_and_deleted_numbers():
    entries = enzyme.parse_entries(ENTRIES)
    assert set(entries) == {"EC:7.99.99.1", "EC:7.99.99.2", "EC:7.99.99.3", "EC:7.99.99.n4"}
    assert entries["EC:7.99.99.1"].nombre == "enzima ficticia de nombre largo"
    assert entries["EC:7.99.99.1"].vigente
    assert entries["EC:7.99.99.2"].transferida_a == ("EC:7.99.99.1", "EC:7.99.99.3")
    assert not entries["EC:7.99.99.2"].vigente
    assert entries["EC:7.99.99.3"].eliminada
    assert not entries["EC:7.99.99.3"].vigente


def test_parse_entries_rejects_entries_without_description():
    with pytest.raises(SourceFormatError, match=r"7\.99\.99\.1"):
        enzyme.parse_entries("ID   7.99.99.1\n//\n")
