#!/usr/bin/env python3
"""Offline audit of the curated bibliography and its citation coverage.

This checker validates the exact BibTeX and verification ledger shipped with
this repository.  It performs no network access and does not turn persistent
identifiers into a claim that every cited theorem was independently reread.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import re
import resource
import time
from typing import Dict, Iterable, List, Tuple

ROOT = Path(__file__).resolve().parent
DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$", re.I)
ARXIV_RE = re.compile(r"^\d{4}\.\d{4,5}(?:v\d+)?$", re.I)
URL_RE = re.compile(r"^https://[^\s{}]+$", re.I)
ALLOWED_VERSION_TITLE_GROUPS = {frozenset({"kalyan1997", "kalyan2003"})}


def parse_bib(path: Path) -> List[dict]:
    text = path.read_text(encoding="utf-8")
    out: List[dict] = []
    pos = 0
    while True:
        at = text.find("@", pos)
        if at < 0:
            break
        opening = text.find("{", at)
        if opening < 0:
            raise ValueError("BibTeX entry has no opening brace")
        entry_type = text[at + 1 : opening].strip().lower()
        depth = 0
        closing = None
        for index in range(opening, len(text)):
            char = text[index]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    closing = index
                    break
        if closing is None:
            raise ValueError("Unbalanced BibTeX braces")
        payload = text[opening + 1 : closing]
        comma = payload.find(",")
        if comma < 0:
            raise ValueError("BibTeX entry has no key delimiter")
        key = payload[:comma].strip()
        body = payload[comma + 1 :]
        fields: Dict[str, str] = {}
        i = 0
        while i < len(body):
            while i < len(body) and (body[i].isspace() or body[i] == ","):
                i += 1
            if i >= len(body):
                break
            match = re.match(r"([A-Za-z][A-Za-z0-9_-]*)\s*=\s*", body[i:])
            if not match:
                raise ValueError(f"Cannot parse field in {key!r} near {body[i:i+50]!r}")
            name = match.group(1).lower()
            i += match.end()
            if i >= len(body) or body[i] != "{":
                raise ValueError(f"Field {name!r} in {key!r} is not brace-delimited")
            start = i + 1
            level = 1
            i += 1
            while i < len(body) and level:
                if body[i] == "{":
                    level += 1
                elif body[i] == "}":
                    level -= 1
                i += 1
            if level:
                raise ValueError(f"Unbalanced field {name!r} in {key!r}")
            if name in fields:
                raise ValueError(f"Duplicate field {name!r} in {key!r}")
            fields[name] = body[start : i - 1].strip()
        out.append({"key": key, "entry_type": entry_type, "fields": fields})
        pos = closing + 1
    return out


def normalize_tex(value: str) -> str:
    value = value.lower()
    value = re.sub(r"\\[a-zA-Z]+", "", value)
    value = value.replace("{", "").replace("}", "")
    return re.sub(r"[^a-z0-9]+", "", value)


def citation_keys(tex_files: Iterable[Path]) -> Tuple[set[str], int]:
    keys: set[str] = set()
    nocite_count = 0
    pattern = re.compile(
        r"\\(cite|citep|citet|citealp|citeauthor|citeyear|nocite)"
        r"(?:\s*\[[^\]]*\]){0,2}\s*\{([^}]*)\}",
        re.S,
    )
    for path in tex_files:
        text = path.read_text(encoding="utf-8")
        for command, payload in pattern.findall(text):
            if command == "nocite":
                nocite_count += 1
            for key in payload.split(","):
                key = key.strip()
                if key and key != "*":
                    keys.add(key)
    return keys, nocite_count


def isbn13_valid(value: str) -> bool:
    digits = re.sub(r"[^0-9Xx]", "", value)
    if len(digits) == 13 and digits.isdigit():
        return sum((1 if i % 2 == 0 else 3) * int(d) for i, d in enumerate(digits)) % 10 == 0
    if len(digits) == 10 and digits[:9].isdigit() and (digits[-1].isdigit() or digits[-1].upper() == "X"):
        total = sum((10 - i) * int(d) for i, d in enumerate(digits[:9]))
        total += 10 if digits[-1].upper() == "X" else int(digits[-1])
        return total % 11 == 0
    return False


def locator(entry: dict) -> Tuple[str, str, str]:
    fields = entry["fields"]
    if fields.get("doi"):
        value = fields["doi"]
        return "doi", value, "https://doi.org/" + value
    if fields.get("eprint"):
        value = fields["eprint"]
        return "arxiv", value, "https://arxiv.org/abs/" + value
    if fields.get("isbn"):
        value = re.sub(r"[^0-9Xx]", "", fields["isbn"])
        return "isbn", value, ""
    if fields.get("url"):
        value = fields["url"]
        return "official_url", value, value
    return "", "", ""


def write_summary(path: Path, rows: List[Tuple[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["metric", "value"])
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    start = time.perf_counter()
    before = resource.getrusage(resource.RUSAGE_SELF)

    bib_path = ROOT / "proofs" / "references.bib"
    entries = parse_bib(bib_path)
    keys = [entry["key"] for entry in entries]
    key_set = set(keys)
    cited, nocite_count = citation_keys(sorted((ROOT / "proofs" / "sections").glob("*.tex")))
    ledger_path = ROOT / "bibliography-verification.csv"
    with ledger_path.open(newline="", encoding="utf-8") as handle:
        ledger = list(csv.DictReader(handle))
    ledger_by_key = {row["key"]: row for row in ledger}

    errors: List[str] = []
    if len(entries) < 55:
        errors.append("bibliography has fewer than 55 entries")
    if len(entries) != 72:
        errors.append(f"expected curated 72-entry bibliography, found {len(entries)}")
    if len(key_set) != len(keys):
        errors.append("duplicate BibTeX keys")
    if nocite_count:
        errors.append("\\nocite is prohibited for coverage accounting")
    undefined = sorted(cited - key_set)
    uncited = sorted(key_set - cited)
    if undefined:
        errors.append("undefined citation keys: " + ", ".join(undefined))
    if uncited:
        errors.append("uncited bibliography keys: " + ", ".join(uncited))

    normalized_titles: Dict[str, List[str]] = {}
    persistent_ids: Dict[str, List[str]] = {}
    locator_counts: Dict[str, int] = {"doi": 0, "arxiv": 0, "isbn": 0, "official_url": 0}
    for entry in entries:
        key = entry["key"]
        fields = entry["fields"]
        for required in ("author", "title", "year"):
            if not fields.get(required):
                errors.append(f"{key}: missing {required}")
        title_norm = normalize_tex(fields.get("title", ""))
        normalized_titles.setdefault(title_norm, []).append(key)
        row = ledger_by_key.get(key)
        if row is None:
            errors.append(f"{key}: absent from bibliography-verification.csv")
            continue
        kind = row.get("persistent_id_type", "")
        ident = row.get("persistent_id", "")
        stable_url = row.get("stable_url", "")
        if kind not in locator_counts or not ident:
            errors.append(f"{key}: verification ledger has no accepted persistent locator")
            continue
        locator_counts[kind] += 1
        persistent_ids.setdefault(kind + ":" + ident.lower(), []).append(key)
        if kind == "doi" and not DOI_RE.fullmatch(ident):
            errors.append(f"{key}: malformed DOI {ident}")
        elif kind == "arxiv" and not ARXIV_RE.fullmatch(ident):
            errors.append(f"{key}: malformed arXiv identifier {ident}")
        elif kind == "isbn" and not isbn13_valid(ident):
            errors.append(f"{key}: invalid ISBN checksum {ident}")
        elif kind == "official_url" and not URL_RE.fullmatch(ident):
            errors.append(f"{key}: official URL is not an HTTPS URL")
        if stable_url and not URL_RE.fullmatch(stable_url):
            errors.append(f"{key}: stable URL is not an HTTPS URL")
        bib_kind, bib_ident, _ = locator(entry)
        if bib_kind and (bib_kind != kind or bib_ident != ident):
            errors.append(f"{key}: locator printed in BibTeX disagrees with verification ledger")

        container_value = (
            fields.get("journal", "")
            or fields.get("booktitle", "")
            or fields.get("publisher", "")
        )
        expected = {
            "entry_type": entry["entry_type"],
            "author_bibtex": fields.get("author", ""),
            "title_bibtex": fields.get("title", ""),
            "year": fields.get("year", ""),
            "container_bibtex": container_value,
            "cited_in_manuscript": "true" if key in cited else "false",
            "status": "metadata_crosschecked_locator_recorded",
        }
        for name, value in expected.items():
            if row.get(name, "") != value:
                errors.append(f"{key}: ledger field {name} disagrees with BibTeX/citation corpus")
        if row.get("verification_date") != "2026-09-16":
            errors.append(f"{key}: unexpected verification date")
        if not row.get("verification_basis") or not row.get("checked_fields"):
            errors.append(f"{key}: incomplete verification provenance")

    duplicate_titles = {title: ks for title, ks in normalized_titles.items() if title and len(ks) > 1}
    unapproved_duplicate_titles = {
        title: ks for title, ks in duplicate_titles.items()
        if frozenset(ks) not in ALLOWED_VERSION_TITLE_GROUPS
    }
    duplicate_ids = {ident: ks for ident, ks in persistent_ids.items() if len(ks) > 1}
    if unapproved_duplicate_titles:
        errors.append("unapproved duplicate normalized titles: " + repr(unapproved_duplicate_titles))
    if duplicate_ids:
        errors.append("duplicate persistent identifiers: " + repr(duplicate_ids))
    if len(ledger) != len(entries) or set(ledger_by_key) != key_set:
        errors.append("verification ledger key set or row count disagrees with bibliography")

    after = resource.getrusage(resource.RUSAGE_SELF)
    report = {
        "scope": "offline bibliographic integrity and citation-coverage audit; not a full-text theorem verification",
        "bibliography_entries": len(entries),
        "minimum_required_entries": 55,
        "unique_keys": len(key_set),
        "unique_normalized_titles": len(normalized_titles),
        "unique_cited_keys": len(cited),
        "undefined_citation_keys": undefined,
        "uncited_bibliography_keys": uncited,
        "nocite_commands": nocite_count,
        "verification_ledger_rows": len(ledger),
        "locator_counts": locator_counts,
        "duplicate_persistent_identifiers": duplicate_ids,
        "duplicate_normalized_titles": duplicate_titles,
        "approved_distinct-version_title_groups": [sorted(group) for group in sorted(ALLOWED_VERSION_TITLE_GROUPS, key=lambda item: sorted(item))],
        "verification_date": "2026-09-16",
        "network_used": False,
        "errors": errors,
        "status": "passed" if not errors else "failed",
        "wall_seconds": time.perf_counter() - start,
        "cpu_seconds": after.ru_utime + after.ru_stime - before.ru_utime - before.ru_stime,
        "peak_rss_bytes": after.ru_maxrss * 1024,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "bibliography.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    write_summary(
        args.output_dir / "bibliography-summary.csv",
        [
            ("bibliography_entries", len(entries)),
            ("minimum_required_entries", 55),
            ("unique_cited_keys", len(cited)),
            ("verification_ledger_rows", len(ledger)),
            ("doi_locators", locator_counts["doi"]),
            ("arxiv_locators", locator_counts["arxiv"]),
            ("isbn_locators", locator_counts["isbn"]),
            ("official_url_locators", locator_counts["official_url"]),
            ("undefined_citations", len(undefined)),
            ("uncited_entries", len(uncited)),
            ("nocite_commands", nocite_count),
            ("errors", len(errors)),
            ("status", report["status"]),
        ],
    )
    print(json.dumps({key: value for key, value in report.items() if key not in {"errors"}}, indent=2))
    if errors:
        for error in errors:
            print("ERROR:", error)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
