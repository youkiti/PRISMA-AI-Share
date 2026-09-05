"""Validate the shape of a unified Tsuge MD validation JSON.

Checks that the file produced by ``build_unified_validation_json.py`` has:

* ``experiment_metadata.cli_parameters.target_model_id`` /
  ``experiment_metadata.actual_execution.model_id_to_use`` /
  every ``paper_evaluations[].overall_metadata.model_id`` pointing to the same
  final model ID.
* ``overall_metrics.counts.total_comparable`` equal to the expected value
  (default: 53 for a single-paper smoke test, 530 for the full 10 papers).
* ``main_body_metrics.counts.total_comparable`` equal to 41 (smoke) or 410.
* ``abstract_metrics.counts.total_comparable`` equal to 12 (smoke) or 120.

Exits with a non-zero status if any assertion fails.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


def _load(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def _get(data: Dict[str, Any], dotted: str, default: Any = None) -> Any:
    current: Any = data
    for key in dotted.split("."):
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def check_counts(data: Dict[str, Any], expected: Dict[str, int]) -> List[str]:
    errors: List[str] = []
    for label, expected_value in expected.items():
        dotted = f"{label}.counts.total_comparable"
        actual = _get(data, dotted)
        if actual != expected_value:
            errors.append(
                f"{dotted}: expected {expected_value}, got {actual!r}"
            )
    return errors


def check_model_ids(data: Dict[str, Any]) -> Tuple[List[str], Dict[str, Any]]:
    errors: List[str] = []
    observed = {
        "cli_target_model_id": _get(data, "experiment_metadata.cli_parameters.target_model_id"),
        "actual_model_id_to_use": _get(data, "experiment_metadata.actual_execution.model_id_to_use"),
    }
    paper_model_ids = sorted({
        (p.get("overall_metadata") or {}).get("model_id")
        for p in data.get("paper_evaluations", [])
        if isinstance(p, dict)
    })
    observed["paper_model_ids"] = paper_model_ids

    unique = {observed["cli_target_model_id"], observed["actual_model_id_to_use"], *paper_model_ids}
    unique.discard(None)
    if len(unique) > 1:
        errors.append(
            "model_id inconsistency across metadata layers: " + repr(observed)
        )
    return errors, observed


def check_pricing_flags(data: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    for paper in data.get("paper_evaluations", []):
        meta = paper.get("overall_metadata") or {}
        flags: List[str] = []
        flags.extend(meta.get("notes") or [])
        if isinstance(meta.get("cost_breakdown"), dict):
            flags.extend(meta["cost_breakdown"].get("notes") or [])
        for flag in flags:
            if not isinstance(flag, str):
                continue
            if flag.startswith("pricing_not_found") or "cost_not_calculated_missing_pricing" in flag:
                errors.append(
                    f"paper {paper.get('paper_id')!r}: pricing flag '{flag}' detected"
                )
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("unified_json", type=Path)
    parser.add_argument(
        "--expected-size",
        choices=("smoke", "full"),
        default="full",
        help="smoke=1 paper (53/41/12), full=10 papers (530/410/120).",
    )
    parser.add_argument(
        "--skip-pricing-check",
        action="store_true",
        help="Skip pricing_not_found / cost_not_calculated_missing_pricing check.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data = _load(args.unified_json)

    if args.expected_size == "smoke":
        expected_counts = {
            "overall_metrics": 53,
            "main_body_metrics": 41,
            "abstract_metrics": 12,
        }
    else:
        expected_counts = {
            "overall_metrics": 530,
            "main_body_metrics": 410,
            "abstract_metrics": 120,
        }

    all_errors: List[str] = []
    all_errors.extend(check_counts(data, expected_counts))
    model_errors, observed = check_model_ids(data)
    all_errors.extend(model_errors)
    if not args.skip_pricing_check:
        all_errors.extend(check_pricing_flags(data))

    print(f"file={args.unified_json}")
    print(f"expected_counts={expected_counts}")
    print(f"observed_model_ids={observed}")
    for label in ("overall_metrics", "main_body_metrics", "abstract_metrics"):
        counts = _get(data, f"{label}.counts")
        print(f"{label}.counts={counts}")

    if all_errors:
        print("FAIL")
        for err in all_errors:
            print(f"  - {err}")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
