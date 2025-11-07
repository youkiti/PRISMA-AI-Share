#!/usr/bin/env python3
"""Enrich merged annotation JSON files with Creative Commons license metadata."""

import json
import pathlib
from typing import Dict, Optional

LICENSE_JSON = pathlib.Path("results/license_filter/cc_paper_licenses.json")
ANNOTATION_ROOT = pathlib.Path("/home/prisma-ai-data/annotation")
OUTPUT_DIR = pathlib.Path("results/license_filter/enriched")

LICENSE_ATTRS: Dict[str, Dict[str, Optional[bool]]] = {
    "cc-by": {"allows_commercial_use": True, "allows_derivatives": True, "share_alike": False},
    "cc-by-sa": {"allows_commercial_use": True, "allows_derivatives": True, "share_alike": True},
    "cc-by-nc": {"allows_commercial_use": False, "allows_derivatives": True, "share_alike": False},
    "cc-by-nc-nd": {"allows_commercial_use": False, "allows_derivatives": False, "share_alike": False},
    "cc0": {"allows_commercial_use": True, "allows_derivatives": True, "share_alike": False},
}


def load_license_map() -> Dict[str, str]:
    if not LICENSE_JSON.exists():
        raise SystemExit(f"License map not found: {LICENSE_JSON}")
    data = json.loads(LICENSE_JSON.read_text())
    return data.get("paper_license", {})


def to_structured_key(paper_id: str) -> Optional[str]:
    if paper_id.startswith("Suda2025_"):
        return f"Suda2025-SR文献_{paper_id.split('_')[-1]}"
    if paper_id.startswith("Tsuge2025_PRISMA2020_"):
        return f"Tsuge2025-PRISMA_{paper_id.split('_')[-1]}"
    if paper_id.startswith("Tsuge2025_others_"):
        return f"Tsuge2025-other_{paper_id.split('_')[-1]}"
    return None


def enrich_annotation(path: pathlib.Path, license_map: Dict[str, str]) -> None:
    data = json.loads(path.read_text())
    for entry in data:
        metadata = entry.get("metadata", {})
        paper_id = metadata.get("ID")
        if not paper_id:
            continue
        structured_key = to_structured_key(paper_id)
        license_label = license_map.get(structured_key or "", "")
        metadata["creative_commons_license"] = license_label
        attrs = LICENSE_ATTRS.get(license_label)
        if attrs:
            metadata["cc_allows_commercial_use"] = attrs["allows_commercial_use"]
            metadata["cc_allows_derivatives"] = attrs["allows_derivatives"]
            metadata["cc_requires_share_alike"] = attrs["share_alike"]
        else:
            metadata["cc_allows_commercial_use"] = None
            metadata["cc_allows_derivatives"] = None
            metadata["cc_requires_share_alike"] = None
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / path.name.replace("_merged", "_merged_with_cc")
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"Enriched annotation written to {out_path}")


def main() -> None:
    license_map = load_license_map()
    for annotation_path in ANNOTATION_ROOT.glob("*_merged.json"):
        enrich_annotation(annotation_path, license_map)


if __name__ == "__main__":
    main()
