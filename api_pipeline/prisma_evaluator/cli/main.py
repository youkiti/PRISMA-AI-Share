import asyncio
import csv
import json
import logging # For initial logger access if needed before setup
from pathlib import Path # Added for Path type hint
from typing import Any, Dict, List, Optional

import typer

# Relative imports from other parts of the prisma_evaluator package
from ..analysis.costs import RunCostSummary, calculate_costs_for_paths
from ..logging_config import setup_logging
from ..config import settings # To access default values for Typer options if needed
from .validate_data import validate_data_structure, print_validation_results

app = typer.Typer(help="PRISMA Evaluator CLI - Tools for evaluating systematic reviews against PRISMA guidelines.")

logger = logging.getLogger(__name__) # Get logger for this module

@app.command()
def run(
    model_id: Optional[str] = typer.Option(
        None, # Default is None, pipeline will use settings.DEFAULT_MODEL_ID
        "--model", "-m",
        help=f"LLM model ID to use. Defaults to value in settings ({settings.DEFAULT_MODEL_ID})."
    ),
    # Prompt order / arbitration options (Claude-specific but harmless to pass through)
    order_mode: str = typer.Option(
        "eande-first",
        "--order-mode", "-om",
        help="Prompt order for main evaluation: 'eande-first' (E&E then paper) or 'paper-first' (paper then E&E). Default: eande-first",
    ),
    dual_order: bool = typer.Option(
        False,
        "--dual-order",
        help="Run both prompt orders (E&E→paper and paper→E&E) and reconcile results."
    ),
    arbitrate_opus: bool = typer.Option(
        False,
        "--arbitrate-opus",
        help="For dual-order conflicts, ask Claude Native model to arbitrate using both reasons + full paper text."
    ),
    section_mode: str = typer.Option(
        "off",
        "--section-mode", "-sm",
        help="Section input mode: 'off' (full), 'minimal' (sections-only), 'hybrid' (sections-only+buffer), 'routed' (per-item routing). Default: off",
    ),
    num_papers: Optional[int] = typer.Option(
        None, # Default is None, pipeline will use settings.NUM_PAPERS_TO_EVALUATE
        "--num-papers", "-n",
        help=f"Number of papers to evaluate. Use -1 to process all papers. Defaults to value in settings ({settings.NUM_PAPERS_TO_EVALUATE}).",
        min=-1 # Allow -1 to process all papers, or at least 1 paper if specified
    ),
    format_type: Optional[str] = typer.Option(
        None, # Default is None, pipeline will use its internal default
        "--format", "-f",
        help="Format type for evaluation (currently used for output naming and metadata)."
    ),
    log_level: str = typer.Option(
        "INFO", # Default log level for CLI
        "--log-level", "-ll",
        help="Set the logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL).",
        case_sensitive=False
    ),
    # Gemini-specific parameters
    temperature: Optional[float] = typer.Option(
        None,
        "--temperature", "-t",
        help="Temperature parameter for Gemini models (0.0-2.0, default: 0.0 for deterministic)",
        min=0.0,
        max=2.0
    ),
    thinking_budget: Optional[int] = typer.Option(
        None,
        "--thinking-budget", "-tb",
        help="Thinking budget for Gemini models (-1 for unlimited, default: -1)",
        min=-1
    ),
    top_p: Optional[float] = typer.Option(
        None,
        "--top-p", "-tp",
        help="Top-p parameter for Gemini models (0.0-1.0, default: 1.0)",
        min=0.0,
        max=1.0
    ),
    # GPT-5 specific parameters
    gpt5_verbosity: Optional[str] = typer.Option(
        None,
        "--gpt5-verbosity", "-gv",
        help="Verbosity level for GPT-5 models (low, medium, high). Default: low for PRISMA yes/no responses."
    ),
    gpt5_reasoning: Optional[str] = typer.Option(
        None,
        "--gpt5-reasoning", "-gr",
        help="Reasoning effort for GPT-5 models (minimal, medium, high). Default: minimal for fast evaluation."
    ),
    disable_cfg: bool = typer.Option(
        False,
        "--disable-cfg",
        help="Disable Context-Free Grammar constraints for GPT-5 (not recommended for PRISMA evaluation)."
    ),
    disable_freeform: bool = typer.Option(
        False,
        "--disable-freeform",
        help="Disable free-form function calling for GPT-5 (not recommended for PRISMA evaluation)."
    ),
    use_openai_responses: bool = typer.Option(
        False,
        "--use-openai-responses",
        help="Use OpenAI Responses API instead of Chat Completions for OpenAI-native models."
    ),
    # Claude-specific parameters
    use_claude_native: bool = typer.Option(
        False,
        "--use-claude-native", "-cn",
        help="Force use of Claude Native API (Anthropic direct) instead of OpenRouter for Claude models."
    ),
    thinking_multiplier: Optional[str] = typer.Option(
        None,
        "--thinking-multiplier", "-tm",
        help="Claude thinking budget multiplier: '2x', '3x', '4x', 'max' for enhanced thinking. Only works with Claude native API."
    ),
    # Dataset selection options
    dataset: Optional[str] = typer.Option(
        None,
        "--dataset", "-d",
        help="Dataset to use for evaluation. Options: 'suda', 'tsuge-other', 'tsuge-prisma', 'all'. If not specified, uses default from settings."
    ),
    paper_ids: Optional[str] = typer.Option(
        None,
        "--paper-ids",
        help="Comma-separated list of specific paper IDs to evaluate (e.g., 'Suda2025_5,Suda2025_7,Suda2025_15'). Overrides num_papers if provided."
    ),
    # Best-of-∞ adaptive sampling options
    bo_mode: str = typer.Option(
        "off",
        "--bo-mode",
        help="Best-of-∞ sampling mode: off, fixed, adaptive. Default: off"
    ),
    bo_min_samples: int = typer.Option(
        3,
        "--bo-min-samples",
        help="Minimum samples before applying the stopping rule (>=1).",
        min=1
    ),
    bo_max_samples: int = typer.Option(
        15,
        "--bo-max-samples",
        help="Maximum samples to draw per item before forcing convergence.",
        min=1
    ),
    bo_agree_threshold: float = typer.Option(
        0.70,
        "--bo-agree-threshold",
        help="Agreement threshold for the leading label (0-1).",
        min=0.0,
        max=1.0
    ),
    bo_margin_threshold: float = typer.Option(
        0.15,
        "--bo-margin-threshold",
        help="Margin threshold between first and second label (0-1).",
        min=0.0,
        max=1.0
    ),
    bo_delta: float = typer.Option(
        0.02,
        "--bo-delta",
        help="Safety margin added to the Wilson lower bound (>=0).",
        min=0.0
    ),
    bo_ensemble: str = typer.Option(
        "off",
        "--bo-ensemble",
        help="Model ensemble strategy: off, static, learned. Default: off"
    ),
    bo_ensemble_models: Optional[str] = typer.Option(
        None,
        "--bo-ensemble-models",
        help="Comma-separated model IDs used for ensemble weighting."
    ),
    bo_weights: Optional[str] = typer.Option(
        None,
        "--bo-weights",
        help="Comma-separated weights for --bo-ensemble static mode (must match model count)."
    ),
    bo_train_weights: bool = typer.Option(
        False,
        "--bo-train-weights",
        help="Optimise ensemble weights on the fly using available training data."
    ),
    # Schema type selection for Function Calling
    schema_type: str = typer.Option(
        "simple",
        "--schema-type", "-st",
        help="Function calling schema type: 'simple' (baseline), 'detailed' (PRISMA-EandE), 'few-shot' (error-pattern v1), 'few-shot-v2' (enhanced English v2.0), 'few-shot-v3' (advanced 5-component v3.0), 'few-shot-v4' (sensitivity-optimized v4.0), 'eande-incontext' (E&E paper in-context learning), or 'dynamic' (load from file)."
    ),
    checklist_format: str = typer.Option(
        "md",
        "--checklist-format",
        help="How to embed the PRISMA checklist into the prompt: 'md' (headings), 'text' (plain), 'json' (JSON object), 'xml' (XML tree), or 'none' (do not embed). Default: md"
    ),
    dynamic_schema_file: Optional[str] = typer.Option(
        None,
        "--schema-file", "-sf",
        help="Path to dynamic schema JSON file when using --schema-type dynamic."
    ),
    eande_sections_file: Optional[str] = typer.Option(
        None,
        "--eande-sections-file",
        help="Path to E&E per-item sections Markdown file (for --schema-type eande-incontext)."
    )
):
    """
    Run the PRISMA evaluation pipeline for a batch of papers.
    """
    # Lazy import to avoid importing heavy LLM deps for other commands
    from ..core.pipeline import run_evaluation_pipeline
    # Setup logging as the first step.
    # log_file=None makes setup_logging use the default path from settings.
    setup_logging(log_level_str=log_level.upper(), log_file=None, log_to_console=True)

    logger.info("CLI 'run' command initiated.")
    
    # Handle dataset selection if specified
    if dataset:
        dataset_lower = dataset.lower()
        if dataset_lower == "suda":
            settings.ENABLE_SUDA = True
            settings.ENABLE_TSUGE_OTHER = False
            settings.ENABLE_TSUGE_PRISMA = False
            logger.info("Dataset selection: Suda2025 dataset enabled")
        elif dataset_lower == "tsuge-other":
            settings.ENABLE_SUDA = False
            settings.ENABLE_TSUGE_OTHER = True
            settings.ENABLE_TSUGE_PRISMA = False
            logger.info("Dataset selection: Tsuge2025-other dataset enabled")
        elif dataset_lower == "tsuge-prisma":
            settings.ENABLE_SUDA = False
            settings.ENABLE_TSUGE_OTHER = False
            settings.ENABLE_TSUGE_PRISMA = True
            logger.info("Dataset selection: Tsuge2025-PRISMA dataset enabled")
        elif dataset_lower == "all":
            settings.ENABLE_SUDA = True
            settings.ENABLE_TSUGE_OTHER = True
            settings.ENABLE_TSUGE_PRISMA = True
            logger.info("Dataset selection: All datasets enabled (Suda2025, Tsuge2025-other, Tsuge2025-PRISMA)")
        else:
            logger.error(f"Invalid dataset option: {dataset}. Valid options are: 'suda', 'tsuge-other', 'tsuge-prisma', 'all'")
            raise typer.Exit(code=1)
    else:
        logger.info(f"Using default dataset configuration: {settings.DATASET_NAME}")

    logger.info(f"Effective Model ID: {model_id or settings.DEFAULT_MODEL_ID}")
    
    # Handle paper_ids override
    specific_paper_ids = None
    if paper_ids:
        specific_paper_ids = [pid.strip() for pid in paper_ids.split(",")]
        logger.info(f"Specific Paper IDs: {specific_paper_ids} ({len(specific_paper_ids)} papers)")
        # Override num_papers when paper_ids is specified
        effective_num_papers = len(specific_paper_ids)
    else:
        effective_num_papers = num_papers or settings.NUM_PAPERS_TO_EVALUATE
        logger.info(f"Effective Number of Papers: {effective_num_papers}")
    
    if format_type:
        logger.info(f"Format Type: {format_type}")
    else:
        logger.info("Format Type: Using pipeline default.")
    
    # Log Gemini parameters if specified
    gemini_params = {}
    if temperature is not None:
        gemini_params['temperature'] = temperature
        logger.info(f"Temperature: {temperature}")
    if thinking_budget is not None:
        gemini_params['thinking_budget'] = thinking_budget
        logger.info(f"Thinking Budget: {thinking_budget}")
    if top_p is not None:
        gemini_params['top_p'] = top_p
        logger.info(f"Top-p: {top_p}")
    
    # Handle GPT-5 parameters (reuse gemini_params dict for compatibility)
    if gpt5_verbosity is not None:
        if gpt5_verbosity.lower() in ['low', 'medium', 'high']:
            gemini_params['verbosity'] = gpt5_verbosity.lower()
            logger.info(f"GPT-5 Verbosity: {gpt5_verbosity.lower()}")
        else:
            logger.error(f"Invalid GPT-5 verbosity: {gpt5_verbosity}. Valid options are: low, medium, high")
            raise typer.Exit(code=1)
    
    if gpt5_reasoning is not None:
        if gpt5_reasoning.lower() in ['minimal', 'medium', 'high']:
            gemini_params['reasoning_effort'] = gpt5_reasoning.lower()
            logger.info(f"GPT-5 Reasoning Effort: {gpt5_reasoning.lower()}")
        else:
            logger.error(f"Invalid GPT-5 reasoning effort: {gpt5_reasoning}. Valid options are: minimal, medium, high")
            raise typer.Exit(code=1)
    
    if disable_cfg:
        gemini_params['enable_cfg'] = False
        logger.info("GPT-5 Context-Free Grammar: Disabled")
    
    if disable_freeform:
        gemini_params['enable_freeform'] = False
        logger.info("GPT-5 Free-form Function Calling: Disabled")
    
    # Handle schema type for Function Calling
    valid_schema_types = ['simple', 'detailed', 'few-shot', 'few-shot-v2', 'few-shot-v3', 'few-shot-v4', 'eande-incontext', 'eande-incontext-hints', 'dynamic', 'dynamic-simple-overrides']
    if schema_type.lower() in valid_schema_types:
        gemini_params['schema_type'] = schema_type.lower()
        logger.info(f"Function Calling Schema Type: {schema_type.lower()}")
        
        # Handle dynamic schema file
        if schema_type.lower() in ('dynamic', 'dynamic-simple-overrides'):
            if not dynamic_schema_file:
                logger.error("Dynamic schema type requires --schema-file option")
                raise typer.Exit(code=1)
            if not Path(dynamic_schema_file).exists():
                logger.error(f"Dynamic schema file not found: {dynamic_schema_file}")
                raise typer.Exit(code=1)
            gemini_params['dynamic_schema_file'] = dynamic_schema_file
            logger.info(f"Dynamic schema file: {dynamic_schema_file}")
        # Handle E&E sections file override
        if schema_type.lower() == 'eande-incontext' and eande_sections_file:
            gemini_params['eande_sections_file'] = eande_sections_file
            logger.info(f"E&E sections Markdown file override: {eande_sections_file}")
    else:
        logger.error(f"Invalid schema type: {schema_type}. Valid options are: {', '.join(valid_schema_types)}")
        raise typer.Exit(code=1)

    # Checklist format selection (prompt embedding style)
    valid_checklist_formats = ['md', 'text', 'json', 'xml', 'none']
    clf_lower = (checklist_format or 'md').lower()
    if clf_lower in valid_checklist_formats:
        gemini_params['checklist_format'] = clf_lower
        logger.info(f"Checklist format: {clf_lower}")
    else:
        logger.error(f"Invalid checklist format: {checklist_format}. Valid options are: {', '.join(valid_checklist_formats)}")
        raise typer.Exit(code=1)

    if use_openai_responses:
        gemini_params['use_openai_responses'] = True
        logger.info("OpenAI evaluator configured to use Responses API.")
    
    if use_claude_native:
        gemini_params['force_claude_native'] = True
        logger.info("Claude Native API: Forced enabled")

    # Handle Claude thinking multiplier
    if thinking_multiplier is not None:
        if thinking_multiplier.lower() in ['2x', '3x', '4x', 'max']:
            gemini_params['thinking_multiplier'] = thinking_multiplier.lower()
            logger.info(f"Claude Thinking Multiplier: {thinking_multiplier.lower()}")
        else:
            logger.error(f"Invalid thinking multiplier: {thinking_multiplier}. Valid options are: 2x, 3x, 4x, max")
            raise typer.Exit(code=1)

    # Build Best-of-∞ configuration
    bo_models: List[str] = []
    if bo_ensemble_models:
        bo_models = [model.strip() for model in bo_ensemble_models.split(',') if model.strip()]
        if not bo_models:
            logger.error("--bo-ensemble-models provided but no valid model IDs were parsed.")
            raise typer.Exit(code=1)
        logger.info(f"BO∞ ensemble target models: {bo_models}")

    bo_weight_values: Optional[List[float]] = None
    if bo_weights:
        try:
            bo_weight_values = [float(weight.strip()) for weight in bo_weights.split(',') if weight.strip()]
        except ValueError:
            logger.error("--bo-weights must be a comma-separated list of numbers")
            raise typer.Exit(code=1)
        if bo_models and len(bo_weight_values) != len(bo_models):
            logger.error("Number of --bo-weights must match --bo-ensemble-models")
            raise typer.Exit(code=1)

    bo_strategy = (bo_ensemble or "off").lower()
    if bo_strategy not in {"off", "static", "learned"}:
        logger.error("Invalid --bo-ensemble value. Use 'off', 'static', or 'learned'.")
        raise typer.Exit(code=1)
    if bo_strategy == "static" and not bo_weight_values:
        logger.error("Static ensemble requires --bo-weights to be specified.")
        raise typer.Exit(code=1)

    bo_config: Optional[Dict[str, Any]] = None
    if bo_mode.lower() != "off":
        bo_config = {
            "mode": bo_mode,
            "min_samples": bo_min_samples,
            "max_samples": bo_max_samples,
            "agree_threshold": bo_agree_threshold,
            "margin_threshold": bo_margin_threshold,
            "delta": bo_delta,
            "ensemble": {
                "strategy": bo_strategy,
                "models": bo_models,
                "weights": bo_weight_values,
                "train_weights": bo_train_weights,
            },
        }
        logger.info(
            "BO∞ mode: %s (min=%d, max=%d, agree>=%.2f, margin>=%.2f, delta=%.2f)",
            bo_config["mode"],
            bo_min_samples,
            bo_max_samples,
            bo_agree_threshold,
            bo_margin_threshold,
            bo_delta,
        )
    else:
        logger.info("BO∞ sampling disabled (use --bo-mode to enable).")

    # Record order/arbitration settings (passed through; evaluators may ignore if unsupported)
    try:
        om = (order_mode or "eande-first").lower()
        if om not in ("eande-first", "paper-first"):
            logger.error(f"Invalid --order-mode: {order_mode}. Use 'eande-first' or 'paper-first'.")
            raise typer.Exit(code=1)
        gemini_params['order_mode'] = om
        if dual_order:
            gemini_params['dual_order'] = True
        if arbitrate_opus:
            gemini_params['arbitrate_opus'] = True
        if dual_order and not use_claude_native and (not model_id or 'claude' not in model_id.lower()):
            logger.warning("--dual-order/--arbitrate-opus は Claude Native 系モデル向けです。--use-claude-native と対応する Claude モデルを指定してください。")
    except Exception:
        # Non-fatal; continue with defaults
        pass
    
    try:
        asyncio.run(run_evaluation_pipeline(
            target_model_id=model_id,
            target_format_type=format_type,
            num_papers_to_process=effective_num_papers,
            specific_paper_ids=specific_paper_ids,
            gemini_params={**(gemini_params or {}), "section_mode": section_mode},
            bo_config=bo_config,
        ))
        logger.info("PRISMA evaluation pipeline completed successfully via CLI.")
    except Exception as e:
        logger.critical(f"An unhandled error occurred during the evaluation pipeline: {e}", exc_info=True)
        raise typer.Exit(code=1)

@app.command()
def validate_config():
    """
    Validates the current configuration settings.
    Prints loaded settings and highlights any potential issues.
    """
    setup_logging(log_level_str="INFO", log_to_console=True) # Basic logging for this command
    logger.info("Validating configuration...")
    try:
        # Accessing settings object itself triggers its loading and validation
        logger.info("Configuration loaded successfully.")
        logger.info("Current settings:")
        for key, value in settings.model_dump().items():
            # Be careful about printing sensitive info like API keys directly
            if "API_KEY" in key.upper() and value:
                logger.info(f"  {key}: {'*' * 8}{value[-4:] if len(str(value)) > 4 else '****'}")
            else:
                logger.info(f"  {key}: {value}")
        
        # Specific checks (examples)
        if not settings.PRISMA_AI_DRIVE_PATH.exists():
            logger.warning(f"PRISMA_AI_DRIVE_PATH does not exist: {settings.PRISMA_AI_DRIVE_PATH}")
        if not settings.ANNOTATION_DATA_PATH.exists():
             logger.warning(f"ANNOTATION_DATA_PATH does not exist: {settings.ANNOTATION_DATA_PATH}")
        if not settings.STRUCTURED_DATA_DIR.exists():
            logger.warning(f"Derived STRUCTURED_DATA_DIR does not exist: {settings.STRUCTURED_DATA_DIR}")
        
        logger.info("Configuration validation finished.")

    except Exception as e: # Catch Pydantic's ValidationError or others
        logger.error(f"Configuration validation failed: {e}", exc_info=True)
        raise typer.Exit(code=1)


# Placeholder for other commands like 'metrics'
@app.command()
def validate_data(
    log_level: str = typer.Option(
        "INFO",
        "--log-level", "-ll",
        help="Set the logging level.",
        case_sensitive=False
    )
):
    """
    Validate the external data directory structure.
    Checks that all required directories and files exist.
    """
    setup_logging(log_level_str=log_level.upper(), log_to_console=True)
    logger.info("Validating data structure...")
    
    try:
        results = validate_data_structure()
        print_validation_results(results)
        
        if results['valid']:
            logger.info("Data structure validation passed.")
        else:
            logger.error("Data structure validation failed.")
            raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"Error during data validation: {e}", exc_info=True)
        raise typer.Exit(code=1)

@app.command()
def show_metrics(
    results_file: Optional[Path] = typer.Option(None, "--results-file", "-rf", help="Path to a unified evaluation JSON (results/evaluator_output/yyyymmdd_HHMMSS.json)")
):
    """
    (Placeholder) Calculate and display metrics from previous evaluation results.
    If --results-file is provided, it analyzes that. Otherwise, it might look for latest.
    """
    setup_logging(log_level_str="INFO")
    logger.info("Executing 'show-metrics' command...")
    from ..data_io import loaders
    from ..metrics import calculators
    from ..schemas import PaperEvaluation
    import json

    if not results_file:
        logger.error("--results-file is required. Pass a unified evaluation JSON path.")
        raise typer.Exit(code=1)
    if not results_file.exists():
        logger.error(f"Results file not found: {results_file}")
        raise typer.Exit(code=1)

    logger.info(f"Analyzing unified results: {results_file}")
    data = json.loads(results_file.read_text(encoding="utf-8"))
    pe_list = data.get("paper_evaluations", [])
    if not pe_list:
        logger.error("No paper_evaluations in the results file.")
        raise typer.Exit(code=1)

    # Parse into Pydantic objects
    ai_papers = []
    for pe in pe_list:
        try:
            ai_papers.append(PaperEvaluation(**pe))
        except Exception as e:
            logger.error(f"Failed to parse PaperEvaluation: {e}")
            raise typer.Exit(code=1)

    # Load human annotations (robust): try both SUDA and TSUGE files if available
    from ..schemas import AnnotationFile
    candidate_paths = []
    # Preferred configured paths
    candidate_paths.extend(settings.ANNOTATION_FILE_PATHS)
    # Also probe common filenames under repo data/annotation
    from pathlib import Path as _P
    probe_dir = _P("data/annotation")
    for name in ["suda2025_merged.json", "tsuge2025_merged.json"]:
        p = probe_dir / name
        if p.exists() and p not in candidate_paths:
            candidate_paths.append(p)

    anns = loaders.load_annotations_from_multiple_files(candidate_paths)
    if not anns:
        logger.error("Failed to load any human annotations from candidates.")
        raise typer.Exit(code=1)
    # Merge for calculator
    entries = []
    for a in anns.values():
        if a and a.root:
            entries.extend(a.root)
    ann_for_calc = AnnotationFile(root=entries)

    if not ann_for_calc:
        logger.error("Failed to load human annotations. Check settings.ANNOTATION_FILE_PATH(S).")
        raise typer.Exit(code=1)

    metrics = calculators.calculate_overall_accuracy_metrics(ai_papers, ann_for_calc)
    # Print concise summary
    om = metrics.get("overall_metrics", {})
    print("Overall:", {k: round(v,2) if isinstance(v,float) else v for k,v in om.items() if k!="counts"})
    print("Counts:", om.get("counts"))

    # Save timestamped summaries under results/evaluator_output
    from ..data_io import savers
    saved_summary = savers.save_accuracy_summary(metrics, settings.RESULTS_DIR, model_id="metrics_only", format_type="from_file")
    saved_details = savers.save_comparison_details(metrics.get("comparison_details", []), settings.RESULTS_DIR, model_id="metrics_only", format_type="from_file")
    if saved_summary:
        logger.info(f"Saved accuracy summary: {saved_summary}")
    if saved_details:
        logger.info(f"Saved comparison details: {saved_details}")


def _format_currency(value: Optional[float], currency: str) -> str:
    if value is None:
        return "n/a"
    symbol = "$" if currency.upper() == "USD" else f"{currency} "
    return f"{symbol}{value:,.6f}"


def _format_tokens(value: int) -> str:
    return f"{value:,}"


def _print_cost_summary(summary: RunCostSummary, verbose: bool) -> None:
    typer.echo(f"Run {summary.run_id} ({summary.file_path.name})")
    if summary.pricing_display_name:
        typer.echo(f"  Model: {summary.pricing_display_name} [{summary.pricing_model_id}]")
    elif summary.papers:
        fallback_model = summary.papers[0].model_id or "unknown"
        typer.echo(f"  Model: {fallback_model}")

    typer.echo(
        "  Tokens (prompt/output/total): "
        f"{_format_tokens(summary.total_prompt_tokens)} / "
        f"{_format_tokens(summary.total_completion_tokens)} / "
        f"{_format_tokens(summary.total_tokens)}"
    )
    if summary.total_cached_tokens:
        typer.echo(f"  Cached tokens: {_format_tokens(summary.total_cached_tokens)}")

    typer.echo(
        "  Cost (input/output/total): "
        f"{_format_currency(summary.total_input_cost, summary.currency)} / "
        f"{_format_currency(summary.total_output_cost, summary.currency)} / "
        f"{_format_currency(summary.total_cost, summary.currency)}"
    )

    if summary.warnings:
        for warning in sorted(set(summary.warnings)):
            typer.echo(f"  Warning: {warning}")

    if verbose:
        typer.echo("  Papers:")
        for paper in summary.papers:
            line = (
                f"    - {paper.paper_id}: "
                f"tokens {_format_tokens(paper.prompt_tokens)}/"
                f"{_format_tokens(paper.completion_tokens)}/"
                f"{_format_tokens(paper.total_tokens)}; "
                f"cost {_format_currency(paper.total_cost, summary.currency)}"
            )
            if paper.notes:
                line += " | notes: " + ", ".join(sorted(set(paper.notes)))
            typer.echo(line)


@app.command()
def cost(
    result_paths: List[Path] = typer.Argument(
        ...,
        help="Evaluator result JSON files or directories (directories are scanned for *.json).",
    ),
    save_json: Optional[Path] = typer.Option(
        None,
        "--save-json",
        help="Optional path to save the aggregated cost summary as JSON.",
    ),
    save_csv: Optional[Path] = typer.Option(
        None,
        "--save-csv",
        help="Optional path to save the per-paper breakdown as CSV.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Print per-paper breakdown to the console.",
    ),
    log_level: str = typer.Option(
        "INFO",
        "--log-level",
        "-ll",
        help="Set the logging level.",
        case_sensitive=False,
    ),
) -> None:
    """
    Estimate API costs for evaluator result JSON files.
    """
    setup_logging(log_level_str=log_level.upper(), log_to_console=True)

    resolved_paths: List[Path] = []
    for path in result_paths:
        if not path.exists():
            typer.echo(f"Path not found: {path}", err=True)
            raise typer.Exit(code=1)
        resolved_paths.append(path)

    summaries = calculate_costs_for_paths(resolved_paths)
    if not summaries:
        typer.echo("No evaluator result files found.", err=True)
        raise typer.Exit(code=1)

    for idx, summary in enumerate(summaries):
        if idx:
            typer.echo("")  # Spacer between runs
        _print_cost_summary(summary, verbose=verbose)

    if save_json:
        save_json.parent.mkdir(parents=True, exist_ok=True)
        with save_json.open("w", encoding="utf-8") as fp:
            json.dump([summary.to_dict() for summary in summaries], fp, indent=2, ensure_ascii=False)
        typer.echo(f"\nSaved JSON summary to {save_json}")

    if save_csv:
        save_csv.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = [
            "run_id",
            "file_path",
            "paper_id",
            "model_id",
            "pricing_model_id",
            "prompt_tokens",
            "completion_tokens",
            "cached_tokens",
            "total_tokens",
            "input_cost",
            "output_cost",
            "total_cost",
            "notes",
        ]
        with save_csv.open("w", encoding="utf-8", newline="") as fp:
            writer = csv.DictWriter(fp, fieldnames=fieldnames)
            writer.writeheader()
            for summary in summaries:
                for paper in summary.papers:
                    writer.writerow(
                        {
                            "run_id": summary.run_id,
                            "file_path": str(summary.file_path),
                            "paper_id": paper.paper_id,
                            "model_id": paper.model_id or "",
                            "pricing_model_id": paper.pricing_model_id or "",
                            "prompt_tokens": paper.prompt_tokens,
                            "completion_tokens": paper.completion_tokens,
                            "cached_tokens": paper.cached_tokens,
                            "total_tokens": paper.total_tokens,
                            "input_cost": f"{paper.input_cost:.8f}" if paper.input_cost is not None else "",
                            "output_cost": f"{paper.output_cost:.8f}" if paper.output_cost is not None else "",
                            "total_cost": f"{paper.total_cost:.8f}" if paper.total_cost is not None else "",
                            "notes": ";".join(sorted(set(paper.notes))),
                        }
                    )
        typer.echo(f"Saved CSV breakdown to {save_csv}")

if __name__ == "__main__":
    # This allows running `python -m prisma_evaluator.cli.main`
    # For proper CLI usage, users should install the package and use the registered entry point.
    app()
