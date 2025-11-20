import typer
import asyncio
import logging # For initial logger access if needed before setup
from typing import Optional, List
from pathlib import Path # Added for Path type hint

# Relative imports from other parts of the prisma_evaluator package
from ..logging_config import setup_logging
from ..core.pipeline import run_evaluation_pipeline
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
    checklist_format: Optional[str] = typer.Option(
        None,
        "--checklist-format", "-cf",
        help="Checklist-specific format identifier (e.g., md, json, xml, none). Overrides --format when provided."
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
    gemini_model: Optional[str] = typer.Option(
        None,
        "--gemini-model", "-gm",
        help="Gemini model to use (e.g., gemini-2.5-pro, gemini-3-pro-preview). Overrides default from settings."
    ),
    thinking_level: Optional[str] = typer.Option(
        None,
        "--thinking-level", "-tl",
        help="Thinking level for Gemini 3 models (low, medium, high). Cannot be used with --thinking-budget."
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
        help="Comma-separated list of specific paper IDs to evaluate (e.g., Tsuge2025_PRISMA2020_5,Tsuge2025_PRISMA2020_6).",
    )
):
    """
    Run the PRISMA evaluation pipeline for a batch of papers.
    """
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
    logger.info(f"Effective Number of Papers: {num_papers or settings.NUM_PAPERS_TO_EVALUATE}")
    effective_format = checklist_format or format_type
    if checklist_format:
        logger.info(f"Checklist format override: {checklist_format}")
    if format_type and not checklist_format:
        logger.info(f"Format Type: {format_type}")
    if not effective_format:
        logger.info("Format Type: Using pipeline default.")

    parsed_paper_ids: Optional[List[str]] = None
    if paper_ids:
        parsed_paper_ids = [pid.strip() for pid in paper_ids.split(",") if pid.strip()]
        if not parsed_paper_ids:
            logger.warning("No valid paper IDs found in --paper-ids input; falling back to auto-selection.")
        else:
            logger.info(f"Restricting evaluation to {len(parsed_paper_ids)} paper IDs.")
    
    # Log Gemini parameters if specified
    gemini_params = {}
    if gemini_model is not None:
        gemini_params['gemini_model'] = gemini_model
        logger.info(f"Gemini Model: {gemini_model}")
    if temperature is not None:
        gemini_params['temperature'] = temperature
        logger.info(f"Temperature: {temperature}")

    # Validate thinking_budget and thinking_level are not both specified
    if thinking_budget is not None and thinking_level is not None:
        logger.error("Cannot specify both --thinking-budget and --thinking-level. Use one or the other.")
        raise typer.Exit(code=1)

    if thinking_budget is not None:
        gemini_params['thinking_budget'] = thinking_budget
        logger.info(f"Thinking Budget: {thinking_budget}")
    if thinking_level is not None:
        # Validate thinking_level value
        valid_levels = ['low', 'medium', 'high']
        if thinking_level.lower() not in valid_levels:
            logger.error(f"Invalid thinking level: {thinking_level}. Valid options: {', '.join(valid_levels)}")
            raise typer.Exit(code=1)
        gemini_params['thinking_level'] = thinking_level.lower()
        logger.info(f"Thinking Level: {thinking_level}")
    if top_p is not None:
        gemini_params['top_p'] = top_p
        logger.info(f"Top-p: {top_p}")
    
    try:
        asyncio.run(run_evaluation_pipeline(
            target_model_id=model_id,
            target_format_type=effective_format,
            num_papers_to_process=num_papers,
            gemini_params=gemini_params if gemini_params else None,
            paper_ids=parsed_paper_ids
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
    results_file: Optional[Path] = typer.Option(None, "--results-file", "-rf", help="Path to a specific AI evaluations JSON results file to analyze.")
):
    """
    (Placeholder) Calculate and display metrics from previous evaluation results.
    If --results-file is provided, it analyzes that. Otherwise, it might look for latest.
    """
    setup_logging(log_level_str="INFO")
    logger.info("Executing 'show-metrics' command...")
    if results_file:
        logger.info(f"Analyzing results from: {results_file}")
        if not results_file.exists():
            logger.error(f"Results file not found: {results_file}")
            raise typer.Exit(code=1)
        # TODO: Add logic to load the results file, load annotations, and calculate/display metrics.
        logger.warning("Metrics display logic from a specific file is not yet implemented.")
    else:
        # TODO: Add logic to find latest results or a summary.
        logger.warning("General metrics display (e.g., from latest run) is not yet implemented.")
    print("Metrics calculation/display logic would be here.")


if __name__ == "__main__":
    # This allows running `python -m prisma_evaluator.cli.main`
    # For proper CLI usage, users should install the package and use the registered entry point.
    app()
