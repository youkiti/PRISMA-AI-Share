#!/usr/bin/env python3
"""Extract Creative Commons license mentions from structured paper JSON files."""

import csv
import json
import pathlib
import re
from collections import Counter, defaultdict
from typing import Dict, Iterable, Iterator, List, Tuple

ROOT = pathlib.Path("/home/prisma-ai-data")
OUT_DIR = pathlib.Path("results/license_filter")
CSV_PATH = OUT_DIR / "cc_paper_licenses.csv"
JSON_PATH = OUT_DIR / "cc_paper_licenses.json"

CC_TRIGGER_RE = re.compile(r"creative\s*commons", re.IGNORECASE)
TERMS: List[Tuple[re.Pattern[str], str]] = [
    (re.compile(r"noncommercial[- ]?(?:no[- ]?derivs|no[- ]?derivatives|nd)", re.IGNORECASE), "cc-by-nc-nd"),
    (re.compile(r"non-commercial[- ]?(?:no[- ]?derivs|no[- ]?derivatives|nd)", re.IGNORECASE), "cc-by-nc-nd"),
    (re.compile(r"share\s*alike|sharealike", re.IGNORECASE), "cc-by-sa"),
    (re.compile(r"no[- ]?derivs", re.IGNORECASE), "cc-by-nd"),
    (re.compile(r"no[- ]?derivatives", re.IGNORECASE), "cc-by-nd"),
    (re.compile(r"noncommercial", re.IGNORECASE), "cc-by-nc"),
    (re.compile(r"non-commercial", re.IGNORECASE), "cc-by-nc"),
    (re.compile(r"cc\s*-?by\s*-?nc\s*-?nd", re.IGNORECASE), "cc-by-nc-nd"),
    (re.compile(r"cc\s*-?by\s*-?sa", re.IGNORECASE), "cc-by-sa"),
    (re.compile(r"cc\s*-?by\s*-?nc", re.IGNORECASE), "cc-by-nc"),
    (re.compile(r"cc\s*-?by\s*-?nd", re.IGNORECASE), "cc-by-nd"),
    (re.compile(r"cc\s*-?by", re.IGNORECASE), "cc-by"),
    (re.compile(r"attribution", re.IGNORECASE), "cc-by"),
    (re.compile(r"cc0", re.IGNORECASE), "cc0"),
]
PRIORITY = ["cc-by-nc-nd", "cc-by-nc", "cc-by-sa", "cc-by-nd", "cc-by", "cc0"]


def iter_structured_papers() -> Iterator[Tuple[str, str, pathlib.Path]]:
    for json_path in ROOT.rglob("*.json"):
        try:
            data = json.loads(json_path.read_text())
        except Exception:
            continue
        if isinstance(data, dict):
            for paper_id, payload in data.items():
                if isinstance(payload, dict):
                    text = payload.get("text")
                    if isinstance(text, str):
                        yield paper_id, text, json_path
        elif isinstance(data, list):
            for entry in data:
                if isinstance(entry, dict):
                    paper_id = entry.get("paper_id") or entry.get("ID") or entry.get("id") or entry.get("title")
                    text = entry.get("text")
                    if paper_id and isinstance(text, str):
                        yield paper_id, text, json_path


def classify_snippet(snippet: str) -> str:
    for pattern, label in TERMS:
        if pattern.search(snippet):
            return label
    return "cc-by-nc-nd"


def main() -> None:
    paper_license: Dict[str, str] = {}
    match_records: List[Dict[str, str]] = []

    for paper_id, text, path in iter_structured_papers():
        for match in CC_TRIGGER_RE.finditer(text):
            start, end = match.span()
            snippet = text[max(0, start - 150) : end + 150]
            label = classify_snippet(snippet)
            match_records.append(
                {
                    "paper_id": paper_id,
                    "dataset": path.parent.name,
                    "file_path": str(path),
                    "license_label": label,
                    "context": snippet.replace("\n", " "),
                }
            )
            current = paper_license.get(paper_id)
            if current is None or PRIORITY.index(label) < PRIORITY.index(current):
                paper_license[paper_id] = label

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["paper_id", "license_label", "dataset", "file_path", "context"]
        )
        writer.writeheader()
        for row in match_records:
            writer.writerow(row)

    with JSON_PATH.open("w") as fh:
        json.dump(
            {"paper_license": paper_license, "match_records": match_records},
            fh,
            ensure_ascii=False,
            indent=2,
        )

    counts = Counter(paper_license.values())
    print(f"Unique papers classified: {len(paper_license)}")
    for label, count in counts.most_common():
        print(f"  {label}: {count}")
    print(f"\nCSV output:  {CSV_PATH}")
    print(f"JSON output: {JSON_PATH}")


if __name__ == "__main__":
    main()
