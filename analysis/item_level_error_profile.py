#!/usr/bin/env python3
"""
Item-level FN/FP error profile aggregation.

This script ingests unified evaluator outputs that expose `comparison_details`
and aggregates false-negative / false-positive rates per PRISMA checklist item.
It is designed to support the workflow documented in
`test/issues/2025-10-31_item_level_error_profile/README.md`.
"""

from __future__ import annotations

import argparse
import collections
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


ItemId = str


@dataclass
class ItemStats:
    tp: int = 0
    tn: int = 0
    fp: int = 0
    fn: int = 0
    fp_reasons: collections.Counter = field(default_factory=collections.Counter)
    fn_reasons: collections.Counter = field(default_factory=collections.Counter)

    def record(self, classification: str, reason: Optional[str]) -> None:
        if classification == "tp":
            self.tp += 1
        elif classification == "tn":
            self.tn += 1
        elif classification == "fp":
            self.fp += 1
            if reason:
                self.fp_reasons[reason.strip()] += 1
        elif classification == "fn":
            self.fn += 1
            if reason:
                self.fn_reasons[reason.strip()] += 1

    def fn_support(self) -> int:
        return self.tp + self.fn

    def fp_support(self) -> int:
        return self.tn + self.fp

    def fn_rate(self) -> Optional[float]:
        denominator = self.fn_support()
        if denominator <= 0:
            return None
        return self.fn / denominator

    def fp_rate(self) -> Optional[float]:
        denominator = self.fp_support()
        if denominator <= 0:
            return None
        return self.fp / denominator

    def to_dict(self) -> Dict[str, object]:
        return {
            "tp": self.tp,
            "tn": self.tn,
            "fp": self.fp,
            "fn": self.fn,
            "fn_support": self.fn_support(),
            "fp_support": self.fp_support(),
            "fn_rate": self.fn_rate(),
            "fp_rate": self.fp_rate(),
            "top_fn_reasons": format_reasons(self.fn_reasons),
            "top_fp_reasons": format_reasons(self.fp_reasons),
        }


def format_reasons(counter: collections.Counter, limit: int = 3) -> List[Dict[str, object]]:
    if not counter:
        return []
    return [{"reason": reason, "count": count} for reason, count in counter.most_common(limit)]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate item-level FN/FP error profiles from evaluator outputs."
    )
    parser.add_argument(
        "--dataset",
        action="append",
        metavar="LABEL=PATH",
        help="Dataset label and unified evaluator output path (JSON). "
        "Can be specified multiple times.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory where reports will be written.",
    )
    parser.add_argument(
        "--min-support",
        type=int,
        default=8,
        help="Minimum denominator required to report FN/FP rates (default: 8).",
    )
    parser.add_argument(
        "--topk",
        type=int,
        default=5,
        help="Number of top items to surface for each rate (default: 5).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse inputs and print summary without writing files.",
    )
    return parser.parse_args()


def load_dataset_arg(value: str) -> Tuple[str, Path]:
    if "=" not in value:
        raise ValueError(f"--dataset expects LABEL=PATH format, got '{value}'")
    label, path = value.split("=", 1)
    label = label.strip()
    if not label:
        raise ValueError(f"--dataset label missing in '{value}'")
    resolved_path = Path(path).expanduser().resolve()
    return label, resolved_path


def load_comparison_details(path: Path) -> List[Dict[str, object]]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    if isinstance(data, dict):
        if "comparison_details" in data and isinstance(data["comparison_details"], list):
            return data["comparison_details"]
        # Some unified outputs store the list under results[...]
        for key in ("results", "evaluations", "papers"):
            value = data.get(key)
            if isinstance(value, list):
                nested = _extract_from_collection(value)
                if nested:
                    return nested
    elif isinstance(data, list):
        nested = _extract_from_collection(data)
        if nested:
            return nested
    raise ValueError(f"Unable to locate comparison_details in {path}")


def _extract_from_collection(collection: Iterable[object]) -> Optional[List[Dict[str, object]]]:
    for element in collection:
        if isinstance(element, dict) and isinstance(element.get("comparison_details"), list):
            return element["comparison_details"]
    return None


def normalize_item_id(raw_id: str) -> ItemId:
    if not raw_id:
        return "unknown"
    if raw_id.startswith("main_"):
        return raw_id[len("main_") :]
    if raw_id.startswith("abstract_item_"):
        suffix = raw_id[len("abstract_item_") :]
        return f"A{suffix}"
    if raw_id.startswith("abstract_"):
        suffix = raw_id[len("abstract_") :]
        suffix = suffix.replace("item_", "")
        return f"A{suffix}"
    return raw_id


def aggregate_dataset(comparison_details: List[Dict[str, object]]) -> Dict[ItemId, ItemStats]:
    stats_map: Dict[ItemId, ItemStats] = collections.defaultdict(ItemStats)
    for paper in comparison_details:
        items = paper.get("items", [])
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            classification = item.get("classification")
            if classification not in {"tp", "tn", "fp", "fn"}:
                continue
            normalized_id = normalize_item_id(str(item.get("item_id", "")))
            reason = item.get("ai_reason")
            stats_map[normalized_id].record(classification, reason)
    return stats_map


def build_rankings(
    stats: Dict[ItemId, ItemStats],
    min_support: int,
    topk: int,
) -> Dict[str, List[Dict[str, object]]]:
    fn_candidates = []
    fp_candidates = []
    for item_id, item_stats in stats.items():
        fn_support = item_stats.fn_support()
        fp_support = item_stats.fp_support()
        fn_rate = item_stats.fn_rate()
        fp_rate = item_stats.fp_rate()

        if fn_rate is not None and fn_support >= min_support:
            fn_candidates.append(
                (
                    fn_rate,
                    {
                        "item_id": item_id,
                        "fn_rate": fn_rate,
                        "fn_count": item_stats.fn,
                        "fn_support": fn_support,
                        "top_fn_reasons": format_reasons(item_stats.fn_reasons),
                    },
                )
            )
        if fp_rate is not None and fp_support >= min_support:
            fp_candidates.append(
                (
                    fp_rate,
                    {
                        "item_id": item_id,
                        "fp_rate": fp_rate,
                        "fp_count": item_stats.fp,
                        "fp_support": fp_support,
                        "top_fp_reasons": format_reasons(item_stats.fp_reasons),
                    },
                )
            )

    fn_top = [entry for _, entry in sorted(fn_candidates, key=lambda x: x[0], reverse=True)[:topk]]
    fp_top = [entry for _, entry in sorted(fp_candidates, key=lambda x: x[0], reverse=True)[:topk]]

    return {
        "fn_top": fn_top,
        "fp_top": fp_top,
    }


def render_markdown(
    dataset_results: Dict[str, Dict[str, List[Dict[str, object]]]],
    intersection: Dict[str, List[Dict[str, object]]],
    min_support: int,
    topk: int,
) -> str:
    lines: List[str] = []
    if not dataset_results:
        lines.append(
            "No datasets met the reporting criteria. Provide evaluator outputs and rerun the script."
        )
        return "\n".join(lines)

    intro = (
        f"The item-level error profile aggregates false-negative and false-positive rates "
        f"per PRISMA 2020 checklist entry using a minimum support of {min_support} "
        f"and highlights the top {topk} items per dataset."
    )
    lines.append(intro)

    for label, rankings in dataset_results.items():
        fn_items = rankings.get("fn_top", [])
        fp_items = rankings.get("fp_top", [])
        if not fn_items and not fp_items:
            lines.append(
                f"{label}: No checklist items satisfied the minimum support requirement."
            )
            continue
        if fn_items:
            entries = [
                f"{item['item_id']} shows an FN rate of {item['fn_rate']:.1%} "
                f"across {item['fn_support']} comparable human positives."
                for item in fn_items
            ]
            lines.append(f"{label} FN focus: " + " ".join(entries))
        if fp_items:
            entries = [
                f"{item['item_id']} exhibits an FP rate of {item['fp_rate']:.1%} "
                f"over {item['fp_support']} comparable human negatives."
                for item in fp_items
            ]
            lines.append(f"{label} FP focus: " + " ".join(entries))

    intersect_fn = intersection.get("fn_top", [])
    intersect_fp = intersection.get("fp_top", [])
    if intersect_fn or intersect_fp:
        lines.append(
            "Cross-dataset overlap isolates checklist entries that remain problematic across inputs."
        )
        if intersect_fn:
            entries = [
                f"{item['item_id']} recurring FN rate {item['fn_rate']:.1%}"
                for item in intersect_fn
            ]
            lines.append("Shared FN pressures: " + ", ".join(entries))
        if intersect_fp:
            entries = [
                f"{item['item_id']} recurring FP rate {item['fp_rate']:.1%}"
                for item in intersect_fp
            ]
            lines.append("Shared FP pressures: " + ", ".join(entries))

    return "\n".join(lines)


def intersect_rankings(
    dataset_rankings: Dict[str, Dict[str, List[Dict[str, object]]]],
) -> Dict[str, List[Dict[str, object]]]:
    if not dataset_rankings:
        return {"fn_top": [], "fp_top": []}

    fn_sets: List[Dict[str, Dict[str, object]]] = []
    fp_sets: List[Dict[str, Dict[str, object]]] = []
    for rankings in dataset_rankings.values():
        fn_map = {item["item_id"]: item for item in rankings.get("fn_top", [])}
        fp_map = {item["item_id"]: item for item in rankings.get("fp_top", [])}
        if fn_map:
            fn_sets.append(fn_map)
        if fp_map:
            fp_sets.append(fp_map)

    fn_overlap = intersect_item_maps(fn_sets)
    fp_overlap = intersect_item_maps(fp_sets)

    return {
        "fn_top": list(fn_overlap.values()),
        "fp_top": list(fp_overlap.values()),
    }


def intersect_item_maps(
    item_maps: List[Dict[str, Dict[str, object]]]
) -> Dict[str, Dict[str, object]]:
    if not item_maps:
        return {}
    common_ids = set(item_maps[0].keys())
    for mapping in item_maps[1:]:
        common_ids &= set(mapping.keys())
    if not common_ids:
        return {}
    result: Dict[str, Dict[str, object]] = {}
    for item_id in sorted(common_ids):
        # prefer the statistics from the first dataset for deterministic output
        for mapping in item_maps:
            if item_id in mapping:
                result[item_id] = mapping[item_id]
                break
    return result


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def main() -> None:
    args = parse_args()

    datasets = {}
    if args.dataset:
        for dataset_arg in args.dataset:
            label, path = load_dataset_arg(dataset_arg)
            datasets[label] = path

    dataset_stats: Dict[str, Dict[ItemId, ItemStats]] = {}
    dataset_rankings: Dict[str, Dict[str, List[Dict[str, object]]]] = {}
    dataset_errors: Dict[str, str] = {}

    for label, path in datasets.items():
        if not path.exists():
            dataset_errors[label] = f"Input file not found: {path}"
            continue
        try:
            details = load_comparison_details(path)
        except Exception as exc:  # noqa: BLE001
            dataset_errors[label] = str(exc)
            continue
        stats = aggregate_dataset(details)
        dataset_stats[label] = stats
        dataset_rankings[label] = build_rankings(stats, args.min_support, args.topk)

    intersection = intersect_rankings(dataset_rankings)

    outputs = {
        "parameters": {
            "min_support": args.min_support,
            "topk": args.topk,
        },
        "datasets": {
            label: {
                "rankings": dataset_rankings.get(label, {"fn_top": [], "fp_top": []}),
                "errors": dataset_errors.get(label),
            }
            for label in datasets.keys()
        },
        "intersection": intersection,
    }

    support_snapshot = {
        label: {
            item_id: stats.to_dict()
            for item_id, stats in sorted(item_stats.items())
        }
        for label, item_stats in dataset_stats.items()
    }

    markdown_text = render_markdown(dataset_rankings, intersection, args.min_support, args.topk)

    if args.dry_run:
        print(json.dumps(outputs, indent=2, ensure_ascii=False))
        print("\n---\n")
        print(markdown_text)
        return

    ensure_directory(args.output_dir)
    top_items_path = args.output_dir / "fnfp_top_items.json"
    support_path = args.output_dir / "fnfp_item_support.json"
    markdown_path = args.output_dir / "fnfp_top_items.md"

    top_items_path.write_text(json.dumps(outputs, indent=2, ensure_ascii=False), encoding="utf-8")
    support_path.write_text(json.dumps(support_snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
    markdown_path.write_text(markdown_text, encoding="utf-8")


if __name__ == "__main__":
    main()

