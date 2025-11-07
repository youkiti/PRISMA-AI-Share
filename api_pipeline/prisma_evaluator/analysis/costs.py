from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from ..data_io.pricing_loader import ModelPricing, PricingCatalog, load_pricing_catalog

TokenDict = Dict[str, Any]


def _safe_int(value: Any) -> int:
    """Safely coerce numeric fields to integers."""
    if value is None:
        return 0
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return 0
        try:
            if "." in value:
                return int(float(value))
            return int(value)
        except ValueError:
            return 0
    return 0


def _extract_first(dct: Dict[str, Any], keys: Sequence[str]) -> Tuple[int, bool]:
    """Return the first present integer value for the given keys."""
    for key in keys:
        if key in dct and dct[key] is not None:
            return _safe_int(dct[key]), True
    return 0, False


@dataclass
class UsageBreakdown:
    prompt_tokens: int
    completion_tokens: int
    cached_tokens: int
    total_tokens: int
    source: str
    notes: List[str] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PaperCostResult:
    paper_id: str
    model_id: Optional[str]
    pricing_model_id: Optional[str]
    prompt_tokens: int
    completion_tokens: int
    cached_tokens: int
    total_tokens: int
    input_cost: Optional[float]
    output_cost: Optional[float]
    total_cost: Optional[float]
    notes: List[str] = field(default_factory=list)


@dataclass
class RunCostSummary:
    run_id: str
    file_path: Path
    pricing_model_id: Optional[str]
    pricing_display_name: Optional[str]
    currency: str
    token_rate_unit: str
    papers: List[PaperCostResult] = field(default_factory=list)
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_cached_tokens: int = 0
    total_tokens: int = 0
    total_input_cost: Optional[float] = None
    total_output_cost: Optional[float] = None
    total_cost: Optional[float] = None
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["file_path"] = str(self.file_path)
        return payload


def extract_usage(metadata: Dict[str, Any]) -> UsageBreakdown:
    """Pull token usage from a paper metadata block with sensible fallbacks."""
    notes: List[str] = []
    token_usage = metadata.get("token_usage")

    if isinstance(token_usage, dict):
        prompt_tokens, prompt_found = _extract_first(
            token_usage,
            ("prompt_tokens", "prompt_token_count", "input_tokens", "input_token_count"),
        )
        completion_tokens, completion_found = _extract_first(
            token_usage,
            ("completion_tokens", "candidates_token_count", "output_tokens", "output_token_count"),
        )
        cached_tokens, _ = _extract_first(
            token_usage,
            ("cached_tokens", "cached_content_token_count"),
        )
        total_tokens, total_found = _extract_first(
            token_usage,
            ("total_tokens", "total_token_count"),
        )

        if not total_found:
            total_tokens = prompt_tokens + completion_tokens

        if not completion_found and completion_tokens == 0 and prompt_tokens and total_tokens > prompt_tokens:
            completion_tokens = max(total_tokens - prompt_tokens, 0)
            notes.append("completion_tokens_inferred_from_total")

        if total_tokens < prompt_tokens + completion_tokens:
            total_tokens = prompt_tokens + completion_tokens
            notes.append("total_tokens_adjusted_to_sum")

        return UsageBreakdown(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cached_tokens=cached_tokens,
            total_tokens=total_tokens,
            source="token_usage",
            notes=notes,
            raw=token_usage,
        )

    # Fallback path for legacy runs without token_usage
    prompt_tokens, prompt_found = _extract_first(
        metadata,
        ("prompt_tokens", "prompt_token_count", "input_tokens", "input_token_count"),
    )
    completion_tokens, completion_found = _extract_first(
        metadata,
        ("completion_tokens", "output_tokens", "output_token_count"),
    )
    total_tokens, total_found = _extract_first(metadata, ("total_tokens", "total_token_count", "token_count"))

    if not total_found:
        total_tokens = prompt_tokens + completion_tokens
    if total_tokens == 0 and metadata.get("token_count"):
        total_tokens = _safe_int(metadata["token_count"])

    if not prompt_found and total_tokens and completion_tokens:
        prompt_tokens = max(total_tokens - completion_tokens, 0)
        notes.append("prompt_tokens_inferred_from_total")
    if not completion_found and total_tokens and prompt_tokens:
        completion_tokens = max(total_tokens - prompt_tokens, 0)
        notes.append("completion_tokens_inferred_from_total")
    if completion_tokens == 0 and prompt_tokens == 0 and total_tokens:
        prompt_tokens = total_tokens
        notes.append("fallback_assumed_all_tokens_prompt")

    cached_tokens, _ = _extract_first(
        metadata,
        ("cached_tokens", "cached_content_token_count"),
    )

    if total_tokens < prompt_tokens + completion_tokens:
        total_tokens = prompt_tokens + completion_tokens
        notes.append("total_tokens_adjusted_to_sum")

    notes.append("usage_fallback_to_overall_metadata")

    return UsageBreakdown(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cached_tokens=cached_tokens,
        total_tokens=total_tokens,
        source="overall_metadata",
        notes=notes,
        raw={},
    )


def _calculate_cost_for_usage(
    model_pricing: Optional[ModelPricing],
    usage: UsageBreakdown,
    token_rate_unit: str,
) -> Tuple[Optional[float], Optional[float], Optional[float], List[str]]:
    notes: List[str] = []
    if not model_pricing:
        return None, None, None, notes

    divisor = 1_000_000 if token_rate_unit == "per_million" else 1_000

    total_tokens = usage.total_tokens if usage.total_tokens > 0 else None
    input_rate, output_rate, tier = model_pricing.effective_rates(total_tokens)

    if tier and tier.notes:
        notes.append(f"pricing_tier:{tier.notes}")

    if model_pricing.billing_strategy == "variable":
        notes.append("pricing_flag:variable_rate")

    input_cost = (
        usage.prompt_tokens / divisor * input_rate if input_rate is not None else None
    )
    output_cost = (
        usage.completion_tokens / divisor * output_rate if output_rate is not None else None
    )

    total_cost = None
    if input_cost is not None or output_cost is not None:
        total_cost = (input_cost or 0.0) + (output_cost or 0.0)

    return input_cost, output_cost, total_cost, notes


def calculate_run_cost(
    result_path: Path,
    pricing_catalog: Optional[PricingCatalog] = None,
) -> RunCostSummary:
    """Compute the cost summary for a single evaluator result JSON."""
    catalog = pricing_catalog or load_pricing_catalog()
    with result_path.open("r", encoding="utf-8") as fp:
        data = json.load(fp)

    experiment_meta = data.get("experiment_metadata", {})
    run_id = experiment_meta.get("experiment_id") or result_path.stem

    papers: List[PaperCostResult] = []
    aggregate_prompt = 0
    aggregate_completion = 0
    aggregate_cached = 0
    aggregate_total = 0
    aggregate_input_cost = 0.0
    aggregate_output_cost = 0.0

    any_input_cost = False
    any_output_cost = False

    warnings: List[str] = []
    pricing_model_id: Optional[str] = None
    pricing_model_display: Optional[str] = None

    for paper in data.get("paper_evaluations", []):
        overall_metadata = paper.get("overall_metadata", {})
        paper_id = paper.get("paper_id") or overall_metadata.get("paper_id") or "unknown"
        model_id = overall_metadata.get("model_id")

        usage = extract_usage(overall_metadata)

        pricing = catalog.get(model_id) if model_id else None
        if pricing:
            pricing_model_id = pricing.id
            pricing_model_display = pricing.display_name
        else:
            if model_id:
                warnings.append(f"pricing_not_found:{model_id}")

        input_cost, output_cost, total_cost, cost_notes = _calculate_cost_for_usage(
            pricing,
            usage,
            catalog.token_rate_unit,
        )

        paper_notes = usage.notes + cost_notes
        if not pricing:
            paper_notes.append("cost_not_calculated_missing_pricing")

        papers.append(
            PaperCostResult(
                paper_id=paper_id,
                model_id=model_id,
                pricing_model_id=pricing.id if pricing else None,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                cached_tokens=usage.cached_tokens,
                total_tokens=usage.total_tokens,
                input_cost=input_cost,
                output_cost=output_cost,
                total_cost=total_cost,
                notes=paper_notes,
            )
        )

        aggregate_prompt += usage.prompt_tokens
        aggregate_completion += usage.completion_tokens
        aggregate_cached += usage.cached_tokens
        aggregate_total += usage.total_tokens

        if input_cost is not None:
            aggregate_input_cost += input_cost
            any_input_cost = True
        if output_cost is not None:
            aggregate_output_cost += output_cost
            any_output_cost = True

    total_input_cost = aggregate_input_cost if any_input_cost else None
    total_output_cost = aggregate_output_cost if any_output_cost else None
    total_cost = None
    if total_input_cost is not None or total_output_cost is not None:
        total_cost = (total_input_cost or 0.0) + (total_output_cost or 0.0)

    return RunCostSummary(
        run_id=run_id,
        file_path=result_path,
        pricing_model_id=pricing_model_id,
        pricing_display_name=pricing_model_display,
        currency=catalog.currency,
        token_rate_unit=catalog.token_rate_unit,
        papers=papers,
        total_prompt_tokens=aggregate_prompt,
        total_completion_tokens=aggregate_completion,
        total_cached_tokens=aggregate_cached,
        total_tokens=aggregate_total,
        total_input_cost=total_input_cost,
        total_output_cost=total_output_cost,
        total_cost=total_cost,
        warnings=warnings,
    )


def calculate_costs_for_paths(
    paths: Iterable[Path],
    pricing_catalog: Optional[PricingCatalog] = None,
) -> List[RunCostSummary]:
    catalog = pricing_catalog or load_pricing_catalog()
    summaries: List[RunCostSummary] = []
    for path in paths:
        if path.is_dir():
            for child in sorted(path.glob("*.json")):
                summaries.append(calculate_run_cost(child, catalog))
        else:
            summaries.append(calculate_run_cost(path, catalog))
    return summaries
