from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - fallback for older runtimes
    import tomli as tomllib  # type: ignore

from ..config.settings import BASE_DIR

PRICING_TABLE_PATH = BASE_DIR / "data/pricing/model_pricing.toml"


@dataclass
class PricingTier:
    """Represents a tier override for a pricing entry."""

    min_tokens: int = 0
    max_tokens: Optional[int] = None
    input_rate: Optional[float] = None
    output_rate: Optional[float] = None
    multiplier: Optional[float] = None
    notes: Optional[str] = None

    def matches(self, total_tokens: Optional[int]) -> bool:
        if total_tokens is None:
            return False
        if total_tokens < self.min_tokens:
            return False
        if self.max_tokens is not None and total_tokens > self.max_tokens:
            return False
        return True


@dataclass
class ModelPricing:
    """Structured pricing definition for a single model."""

    id: str
    display_name: str
    provider: str
    billing_strategy: str
    aliases: List[str] = field(default_factory=list)
    input_rate: Optional[float] = None
    output_rate: Optional[float] = None
    notes: Optional[str] = None
    tiers: List[PricingTier] = field(default_factory=list)

    def base_rates(self) -> Tuple[Optional[float], Optional[float]]:
        """Return the default input/output rate pair."""
        if self.input_rate is not None or self.output_rate is not None:
            return self.input_rate, self.output_rate

        # Fallback to first tier that explicitly defines rates
        for tier in self.tiers:
            if tier.input_rate is not None or tier.output_rate is not None:
                return tier.input_rate, tier.output_rate
        return None, None

    def effective_rates(self, total_tokens: Optional[int]) -> Tuple[Optional[float], Optional[float], Optional[PricingTier]]:
        """
        Determine the applicable rates for the provided token count.

        Returns (input_rate, output_rate, matching_tier).
        """
        base_input, base_output = self.base_rates()

        matching_tier: Optional[PricingTier] = None
        for tier in self.tiers:
            if tier.matches(total_tokens):
                matching_tier = tier
                break

        if matching_tier:
            input_rate = matching_tier.input_rate if matching_tier.input_rate is not None else base_input
            output_rate = matching_tier.output_rate if matching_tier.output_rate is not None else base_output

            if matching_tier.multiplier is not None:
                if input_rate is not None:
                    input_rate *= matching_tier.multiplier
                if output_rate is not None:
                    output_rate *= matching_tier.multiplier
        else:
            input_rate, output_rate = base_input, base_output

        return input_rate, output_rate, matching_tier


@dataclass
class PricingCatalog:
    """Convenience wrapper around the parsed pricing table."""

    currency: str
    token_rate_unit: str
    models: Dict[str, ModelPricing]

    def get(self, model_id: str) -> Optional[ModelPricing]:
        """Retrieve pricing by model id."""
        if model_id in self.models:
            return self.models[model_id]
        for model in self.models.values():
            if model_id in model.aliases:
                return model
        return None


def _parse_pricing_model(entry: Dict[str, object]) -> ModelPricing:
    tiers: List[PricingTier] = []
    for tier_entry in entry.get("tiers", []):
        tiers.append(
            PricingTier(
                min_tokens=int(tier_entry.get("min_tokens", 0)),
                max_tokens=int(tier_entry["max_tokens"]) if "max_tokens" in tier_entry else None,
                input_rate=float(tier_entry["input_rate"]) if "input_rate" in tier_entry else None,
                output_rate=float(tier_entry["output_rate"]) if "output_rate" in tier_entry else None,
                multiplier=float(tier_entry["multiplier"]) if "multiplier" in tier_entry else None,
                notes=str(tier_entry["notes"]) if "notes" in tier_entry else None,
            )
        )

    return ModelPricing(
        id=str(entry["id"]),
        display_name=str(entry.get("display_name", entry["id"])),
        provider=str(entry.get("provider", "")),
        billing_strategy=str(entry.get("billing_strategy", "simple")),
        aliases=[str(alias) for alias in entry.get("aliases", [])],
        input_rate=float(entry["input_rate"]) if "input_rate" in entry else None,
        output_rate=float(entry["output_rate"]) if "output_rate" in entry else None,
        notes=str(entry["notes"]) if "notes" in entry else None,
        tiers=tiers,
    )


@lru_cache(maxsize=1)
def load_pricing_catalog(path: Optional[Path] = None) -> PricingCatalog:
    """
    Load and cache the pricing catalog from the TOML definition.
    """
    pricing_path = path or PRICING_TABLE_PATH
    if not pricing_path.exists():
        raise FileNotFoundError(f"Pricing table not found at {pricing_path}")

    with pricing_path.open("rb") as fp:
        raw_data = tomllib.load(fp)

    models_section = raw_data.get("models")
    if not isinstance(models_section, list):
        raise ValueError("Invalid pricing table: 'models' section must be a list")

    models = [_parse_pricing_model(entry) for entry in models_section]
    return PricingCatalog(
        currency=str(raw_data.get("currency", "USD")),
        token_rate_unit=str(raw_data.get("token_rate_unit", "per_million")),
        models={model.id: model for model in models},
    )
