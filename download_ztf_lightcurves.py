#!/usr/bin/env python3
"""Bulk download ZTF DR2 light-curve tables and save them as text files.

This script logs into IRSA, obtains a list of ZTF object identifiers, fetches
their light curves from the DR2 archive, and writes each result as an
``astropy.table.Table`` in text form on the user's Desktop.

The output directory will be created automatically at
``~/Desktop/ztf_lightcurves``. Each object is saved as ``<objectid>.ecsv``
(Astropy's ASCII ECSV format, which preserves table metadata and can be read
directly back into an ``astropy.table.Table`` instance).

Example usage::

    python download_ztf_lightcurves.py targets.txt --username <IRSA_ID>

The ``targets.txt`` file should contain one ZTF ``objectid`` per line.
If you omit ``--username`` the script prompts for it, and the password is
always requested securely at runtime.

Alternatively, you can supply ``--sn-type-ia`` (or the more general
``--classification`` option) to have the script query IRSA for all objects
whose catalogue classification matches a desired pattern before downloading
their light curves.
"""

from __future__ import annotations

import argparse
import getpass
import sys
import time
import warnings
from pathlib import Path
from typing import Iterable

from astroquery.exceptions import NoResultsWarning
from astroquery.irsa import Irsa
from astropy.table import Table


def _read_object_ids(path: Path) -> list[str]:
    """Read ZTF object identifiers from a text file.

    Blank lines and lines starting with ``#`` are ignored.
    """

    object_ids: list[str] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            object_ids.append(stripped)
    return object_ids


def _iter_object_ids(
    args: argparse.Namespace, classification_pattern: str | None
) -> Iterable[str]:
    if classification_pattern:
        return _query_object_ids_by_classification(classification_pattern, args.limit)
    if args.object_ids:
        return args.object_ids
    if args.input:
        return _read_object_ids(args.input)
    raise SystemExit("No object IDs supplied. Use --input or positional IDs.")


def _login(username: str | None) -> None:
    if not username:
        username = input("IRSA username: ")
    password = getpass.getpass("IRSA password: ")
    Irsa.login(username, password)


def _save_table(table: Table, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    table.write(destination, format="ascii.ecsv", overwrite=True)


def _escape_like(pattern: str) -> str:
    """Escape a string for use inside a SQL ``LIKE`` literal."""

    return pattern.replace("'", "''")


def _query_object_ids_by_classification(
    classification_pattern: str, limit: int | None
) -> Iterable[str]:
    """Return object IDs matching a classification pattern.

    The pattern should follow SQL ``LIKE`` syntax. For convenience, callers can
    use ``%`` as a wildcard (e.g. ``SN Ia%`` will also match ``SN Ia-91bg`` and
    similar sub-types).
    """

    escaped = _escape_like(classification_pattern)
    select = "SELECT objectid"
    if limit is not None:
        select = f"SELECT TOP {int(limit)} objectid"
    query = (
        f"{select} FROM ztf_objects_dr2 "
        f"WHERE classification LIKE '{escaped}'"
    )

    print(
        "Fetching object list from IRSA with classification pattern:",
        classification_pattern,
    )
    try:
        table = Irsa.query_tap(query)
    except Exception as exc:  # noqa: BLE001 - surface all failures
        raise SystemExit(f"Failed to query classification list: {exc}") from exc

    if table is None or len(table) == 0:
        raise SystemExit(
            "No objects matched the requested classification pattern."
        )

    return [row["objectid"] for row in table]


def download_light_curves(
    object_ids: Iterable[str],
    output_dir: Path,
    delay: float,
    max_attempts: int,
) -> None:
    Irsa.ROW_LIMIT = -1
    Irsa.TIMEOUT = 180

    warnings.simplefilter("ignore", NoResultsWarning)

    for object_id in object_ids:
        object_id = object_id.strip()
        if not object_id:
            continue

        destination = output_dir / f"{object_id}.ecsv"
        print(f"Fetching {object_id} …", flush=True)

        for attempt in range(1, max_attempts + 1):
            try:
                table = Irsa.query_object(object_id, catalog="ztf_lightcurves_dr2")
            except Exception as exc:  # noqa: BLE001 - surface all failures
                print(f"  Attempt {attempt}/{max_attempts} failed: {exc}")
                if attempt == max_attempts:
                    print("  Giving up on", object_id)
                else:
                    time.sleep(delay)
                continue

            if table is None or len(table) == 0:
                print(f"  No data returned for {object_id}")
                break

            _save_table(table, destination)
            print(f"  Saved to {destination}")
            break

        time.sleep(delay)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "object_ids",
        metavar="OBJECT_ID",
        nargs="*",
        help="ZTF object IDs to download (ignored when --input is used)",
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        help="Path to a text file containing one object ID per line",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path.home() / "Desktop" / "ztf_lightcurves",
        help="Directory where light curves will be stored (default: Desktop/ztf_lightcurves)",
    )
    parser.add_argument(
        "-u",
        "--username",
        help="IRSA username (will prompt if omitted)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Seconds to wait between requests (default: 1.0)",
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=3,
        help="Number of times to retry a failed download (default: 3)",
    )
    parser.add_argument(
        "--sn-type-ia",
        action="store_true",
        help=(
            "Convenience flag equivalent to --classification 'SN Ia%%' to "
            "download all Type Ia supernova objects (including sub-types)."
        ),
    )
    parser.add_argument(
        "--classification",
        help=(
            "SQL LIKE pattern applied to ztf_objects_dr2.classification to "
            "determine which object IDs to download (e.g. 'SN Ia%%')."
        ),
    )
    parser.add_argument(
        "--limit",
        type=int,
        help=(
            "Optional upper bound on the number of objects to download when "
            "using --classification or --sn-type-ia."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])

    classification_pattern = args.classification
    if args.sn_type_ia:
        if classification_pattern and classification_pattern != "SN Ia%":
            raise SystemExit(
                "--sn-type-ia cannot be combined with a different --classification"
            )
        classification_pattern = "SN Ia%"

    _login(args.username)

    object_ids = list(_iter_object_ids(args, classification_pattern))
    if not object_ids:
        print("No object IDs to process.")
        return 1

    download_light_curves(object_ids, args.output, args.delay, args.max_attempts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
