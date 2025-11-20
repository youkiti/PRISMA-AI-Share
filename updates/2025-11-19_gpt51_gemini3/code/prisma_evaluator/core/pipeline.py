import asyncio
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from ..config.settings import settings
from ..schemas import PaperEvaluation, AnnotationFile, PrismaChecklist # Added PrismaChecklist
from .tasks import evaluate_single_paper_processing_task
from ..data_io import loaders, savers
from ..metrics import calculators
from ..llm.base_evaluator import BaseEvaluator
from ..llm.openai_evaluator import OpenAIEvaluator 
from ..llm.openrouter_evaluator import OpenRouterEvaluator # Specific evaluator for now
from ..llm.section_based_evaluator import SectionBasedEvaluator
from ..llm.gemini_direct_evaluator import GeminiDirectEvaluator
from ..llm.gpt5_evaluator import GPT5Evaluator
logger = logging.getLogger(__name__)

async def run_evaluation_pipeline(
    target_model_id: Optional[str] = None, # If None, use default from settings
    target_format_type: Optional[str] = None, # If None, use a default
    num_papers_to_process: Optional[int] = None, # If None, use default from settings
    gemini_params: Optional[Dict[str, Any]] = None, # Gemini-specific parameters
    paper_ids: Optional[List[str]] = None, # Explicit paper selection
) -> None:
    """
    Main evaluation pipeline orchestrator.
    Processes a specified number of papers using a given LLM model and format type.
    """
    # Resolve effective settings
    model_id_to_use = target_model_id or settings.DEFAULT_MODEL_ID
    format_type_to_use = target_format_type or "refactored_pipeline_default" # Default if not specified
    num_papers = num_papers_to_process if num_papers_to_process is not None else settings.NUM_PAPERS_TO_EVALUATE
    
    # ★★★ デバッグログ追加 ★★★
    logger.info(f"DEBUG PIPELINE: Effective output_base_dir from settings: {settings.RESULTS_DIR}")
    # Note: settings.RESULTS_DIR is likely what's used as output_base_dir, 
    # or it's derived from settings.paths.output_base_dir if that exists.
    # Based on default_settings.toml, RESULTS_DIR = "results/evaluator_output"
    # We need to confirm if this is the value being overridden by the wrapper script.

    logger.info(
        f"Starting evaluation pipeline for {num_papers} papers. "
        f"Model: '{model_id_to_use}', Format Type: '{format_type_to_use}'."
    )

    # 1. Ensure output directories exist
    try:
        settings.RESULTS_DIR.mkdir(exist_ok=True, parents=True)
        # Log directory creation is handled by logging_config.py typically
        logger.info(f"Results will be saved to: {settings.RESULTS_DIR}")
    except Exception as e:
        logger.error(f"Failed to create results directory {settings.RESULTS_DIR}: {e}", exc_info=True)
        return


    # 2. Load PRISMA checklists (common resources)
    prisma_main_checklist: Optional[PrismaChecklist] = loaders.load_checklist_file(settings.PRISMA_CHECKLIST_PATH)
    prisma_abstract_checklist: Optional[PrismaChecklist] = loaders.load_checklist_file(settings.PRISMA_ABSTRACT_CHECKLIST_PATH)

    if not prisma_main_checklist:
        logger.error(f"Could not load PRISMA main checklist from: {settings.PRISMA_CHECKLIST_PATH}. Pipeline cannot continue.")
        return
    if not prisma_abstract_checklist:
        logger.error(f"Could not load PRISMA abstract checklist from: {settings.PRISMA_ABSTRACT_CHECKLIST_PATH}. Pipeline cannot continue.")
        return
    logger.info("PRISMA checklists loaded successfully.")

    # 3. Load human annotations (for abstract text input and accuracy calculation)
    human_annotations_dict = {}
    if settings.ALL_DATASETS_ENABLED or len(settings.ANNOTATION_FILE_PATHS) > 1:
        # Multiple datasets enabled - load all annotation files
        logger.info("Multiple datasets enabled - loading annotations from multiple files")
        human_annotations_dict = loaders.load_annotations_from_multiple_files(settings.ANNOTATION_FILE_PATHS)
        if not human_annotations_dict:
            logger.warning("Could not load any human annotations from multiple files. Abstract evaluation input may be affected.")
        else:
            logger.info(f"Human annotations loaded from {len(human_annotations_dict)} files: {list(human_annotations_dict.keys())}")
    else:
        # Single dataset - use existing logic for backward compatibility
        human_annotations: Optional[AnnotationFile] = loaders.load_annotations(settings.ANNOTATION_FILE_PATH)
        if not human_annotations:
            logger.warning(
                f"Could not load human annotations from {settings.ANNOTATION_FILE_PATH}. "
                "Abstract evaluation input may be affected, and accuracy calculation will be skipped."
            )
        else:
            logger.info("Human annotations loaded successfully.")
            # Store in dict for consistent interface
            human_annotations_dict[settings.ANNOTATION_FILE_PATH.stem] = human_annotations

    # 4. Get list of structured data files to process
    dataset_source_name = settings.DATASET_NAME
    structured_data_dirs = settings.STRUCTURED_DATA_DIRS

    override_dirs = os.environ.get("STRUCTURED_DATA_SUBDIRS_OVERRIDE")
    if override_dirs:
        override_paths: List[Path] = []
        project_root = Path(__file__).resolve().parents[2]
        for raw_path in override_dirs.split(","):
            raw_path = raw_path.strip()
            if not raw_path:
                continue
            candidate = Path(raw_path)
            candidates_to_try = []
            if candidate.is_absolute():
                candidates_to_try.append(candidate)
            else:
                candidates_to_try.append(settings.PRISMA_AI_DRIVE_PATH / raw_path)
                candidates_to_try.append(project_root / raw_path)
                candidates_to_try.append(candidate.resolve())
            resolved = next((c for c in candidates_to_try if c.exists()), None)
            if resolved:
                override_paths.append(resolved)
            else:
                logger.warning(f"Structured data override path not found: {raw_path}")
        if override_paths:
            structured_data_dirs = override_paths
            logger.info("Using structured data override directories: %s", structured_data_dirs)

    if paper_ids:
        structured_data_files = loaders.get_structured_data_files_by_paper_ids(structured_data_dirs, paper_ids)
        logger.info(
            "Paper ID filter active: requested %d paper(s), located %d file(s).",
            len(paper_ids),
            len(structured_data_files),
        )
    elif settings.ALL_DATASETS_ENABLED or len(structured_data_dirs) > 1:
        # Multiple datasets enabled - load files from all directories
        logger.info(f"Multiple datasets enabled - loading files from {len(structured_data_dirs)} directories")
        for i, data_dir in enumerate(structured_data_dirs):
            logger.info(f"  Directory {i+1}: {data_dir}")
        
        structured_data_files = loaders.get_structured_data_files_from_multiple_dirs(structured_data_dirs, num_papers)
    else:
        # Single dataset - use existing logic for backward compatibility
        logger.info(f"Single dataset: {dataset_source_name} from dir: {structured_data_dirs[0]}")
        structured_data_files = loaders.get_structured_data_files(structured_data_dirs[0], num_papers)
    
    if not structured_data_files:
        logger.error(f"No structured data files found in specified directories. Pipeline cannot continue.")
        return
    logger.info(f"Found {len(structured_data_files)} structured data files to process (limit was {num_papers}).")
    
    # 5. Initialize LLM Evaluator
    # Priority: Gemini Direct > Section-Based > Standard OpenRouter
    try:
        # GPT-5 Direct API (最優先 - PRISMA評価最適化)
        if (settings.OPENAI_API_KEY and 
            model_id_to_use and "gpt-5" in model_id_to_use.lower()):
            
            gpt5_reasoning_default = settings.GPT5_REASONING_EFFORT

            evaluator_kwargs = {
                'api_key': settings.OPENAI_API_KEY,
                'retry_count': settings.RETRY_COUNT,
                'retry_delay': settings.RETRY_DELAY_SECONDS,
                'verbosity': settings.GPT5_VERBOSITY,
                'reasoning_effort': gpt5_reasoning_default,
                'enable_cfg': settings.ENABLE_GPT5_CFG,
                'enable_freeform': settings.ENABLE_GPT5_FREEFORM,
                'max_completion_tokens': 128000,  # GPT-5の最大出力トークン数
                'max_retries': settings.MAX_EVALUATION_RETRIES
            }

            # GPT-5.1用のデフォルト値を適用（高速レスポンス）
            autodetect_gpt51 = "gpt-5.1" in model_id_to_use.lower()
            cli_overrides_reasoning = bool(gemini_params and 'reasoning_effort' in gemini_params)
            if autodetect_gpt51 and not cli_overrides_reasoning and gpt5_reasoning_default == "minimal":
                evaluator_kwargs['reasoning_effort'] = 'none'
                logger.info("GPT-5.1モデルを検出: CLI未指定かつ設定値がデフォルトのため reasoning effort を 'none' に設定")

            # GPT-5特有のパラメータのCLI上書き対応
            if gemini_params:  # 将来的にgpt5_paramsに変更
                if 'verbosity' in gemini_params:
                    evaluator_kwargs['verbosity'] = gemini_params['verbosity']
                    logger.info(f"Using CLI verbosity: {gemini_params['verbosity']}")
                if 'reasoning_effort' in gemini_params:
                    evaluator_kwargs['reasoning_effort'] = gemini_params['reasoning_effort']
                    logger.info(f"Using CLI reasoning effort: {gemini_params['reasoning_effort']}")
                if 'schema_type' in gemini_params:
                    evaluator_kwargs['schema_type'] = gemini_params['schema_type']
                    logger.info(f"Using CLI schema type: {gemini_params['schema_type']}")
                if 'checklist_format' in gemini_params:
                    evaluator_kwargs['checklist_format'] = gemini_params['checklist_format']
                    logger.info(f"Using checklist format: {gemini_params['checklist_format']}")
                if 'dynamic_schema_file' in gemini_params:
                    evaluator_kwargs['dynamic_schema_file'] = gemini_params['dynamic_schema_file']
                    logger.info(f"Using dynamic schema file: {gemini_params['dynamic_schema_file']}")
            
            evaluator: BaseEvaluator = GPT5Evaluator(**evaluator_kwargs)
            logger.info(f"Initialized GPT-5 Evaluator for model: {model_id_to_use}")
        
        # OpenAI Native API (GPT-5の次、Claudeの前)
        elif (settings.OPENAI_API_KEY and 
            model_id_to_use and 
            ("openai/" in model_id_to_use.lower() or model_id_to_use.lower().startswith("gpt-4o")) and 
            "gpt-oss" not in model_id_to_use.lower()):  # GPT-OSSはOpenRouterで処理
            
            evaluator_kwargs = {
                'api_key': settings.OPENAI_API_KEY,
                'retry_count': settings.RETRY_COUNT,
                'retry_delay': settings.RETRY_DELAY_SECONDS,
                'max_retries': settings.MAX_EVALUATION_RETRIES
            }
            # Pass optional schema/checklist format if provided
            if gemini_params:
                if 'schema_type' in gemini_params:
                    evaluator_kwargs['schema_type'] = gemini_params['schema_type']
                    logger.info(f"Using CLI schema type for OpenAI: {gemini_params['schema_type']}")
                if 'checklist_format' in gemini_params:
                    evaluator_kwargs['checklist_format'] = gemini_params['checklist_format']
                    logger.info(f"Using checklist format for OpenAI: {gemini_params['checklist_format']}")
                if gemini_params.get('use_openai_responses'):
                    evaluator_kwargs['use_responses_api'] = True
                    logger.info("OpenAI evaluator will use Responses API.")

            evaluator: BaseEvaluator = OpenAIEvaluator(**evaluator_kwargs)
            logger.info(f"Initialized OpenAI Native Evaluator for model: {model_id_to_use}")
        
        # Claude Native API (OpenAIの次)
        elif (settings.ANTHROPIC_API_KEY and 
            ((model_id_to_use and "claude" in model_id_to_use.lower()) or 
             (gemini_params and gemini_params.get('force_claude_native', False)))):
            from ..llm.claude_evaluator import ClaudeEvaluator
            
            evaluator_kwargs = {
                'api_key': settings.ANTHROPIC_API_KEY,
                'retry_count': settings.RETRY_COUNT,
                'retry_delay': settings.RETRY_DELAY_SECONDS,
                'max_retries': settings.MAX_EVALUATION_RETRIES
            }

            # Add thinking multiplier and schema_type if specified
            if gemini_params:
                if 'thinking_multiplier' in gemini_params:
                    evaluator_kwargs['thinking_multiplier'] = gemini_params['thinking_multiplier']
                    logger.info(f"Using CLI thinking multiplier: {gemini_params['thinking_multiplier']}")
                if 'schema_type' in gemini_params:
                    evaluator_kwargs['schema_type'] = gemini_params['schema_type']
                    logger.info(f"Using CLI schema type for Claude: {gemini_params['schema_type']}")
                if 'checklist_format' in gemini_params:
                    evaluator_kwargs['checklist_format'] = gemini_params['checklist_format']
                    logger.info(f"Using checklist format for Claude: {gemini_params['checklist_format']}")
                if 'dynamic_schema_file' in gemini_params:
                    evaluator_kwargs['dynamic_schema_file'] = gemini_params['dynamic_schema_file']
                    logger.info(f"Using dynamic schema file for Claude: {gemini_params['dynamic_schema_file']}")
                # New: prompt order / arbitration
                if 'order_mode' in gemini_params:
                    evaluator_kwargs['order_mode'] = gemini_params['order_mode']
                    logger.info(f"Using prompt order mode: {gemini_params['order_mode']}")
                if 'dual_order' in gemini_params:
                    evaluator_kwargs['dual_order'] = bool(gemini_params['dual_order'])
                    if evaluator_kwargs['dual_order']:
                        logger.info("Dual-order prompting enabled for Claude")
                if 'arbitrate_opus' in gemini_params:
                    evaluator_kwargs['arbitrate_opus'] = bool(gemini_params['arbitrate_opus'])
                    if evaluator_kwargs['arbitrate_opus']:
                        logger.info("Opus arbitration for conflicts enabled")
                if 'eande_sections_file' in gemini_params:
                    try:
                        from ..resources import prisma_eande_loader as eande
                        eande.set_eande_sections_md_path(gemini_params['eande_sections_file'])
                        logger.info(f"Overriding E&E sections Markdown path: {gemini_params['eande_sections_file']}")
                    except Exception as e:
                        logger.warning(f"Failed to set E&E sections path: {e}")

            if model_id_to_use:
                evaluator_kwargs['model_id'] = model_id_to_use

            evaluator: BaseEvaluator = ClaudeEvaluator(**evaluator_kwargs)
            logger.info(f"Initialized Claude Native Evaluator for model: {model_id_to_use}")
        
        # Gemini Direct API (Claude の次)
        elif (settings.ENABLE_GEMINI_DIRECT and 
            settings.GEMINI_API_KEY and 
            model_id_to_use and "gemini" in model_id_to_use.lower()):
            
            # Extract Gemini parameters from CLI or use defaults
            # Determine which Gemini model to use: CLI override > settings default
            gemini_model_to_use = settings.GEMINI_DIRECT_MODEL
            if gemini_params and 'gemini_model' in gemini_params:
                gemini_model_to_use = gemini_params['gemini_model']
                logger.info(f"Using CLI-specified Gemini model: {gemini_model_to_use}")

            evaluator_kwargs = {
                'api_key': settings.GEMINI_API_KEY,
                'model': gemini_model_to_use,
                'retry_count': settings.RETRY_COUNT,
                'retry_delay': settings.RETRY_DELAY_SECONDS
            }

            # Apply CLI-provided Gemini parameters if available
            if gemini_params:
                if 'temperature' in gemini_params:
                    evaluator_kwargs['temperature'] = gemini_params['temperature']
                    logger.info(f"Using CLI temperature: {gemini_params['temperature']}")
                if 'thinking_budget' in gemini_params:
                    evaluator_kwargs['thinking_budget'] = gemini_params['thinking_budget']
                    logger.info(f"Using CLI thinking budget: {gemini_params['thinking_budget']}")
                if 'thinking_level' in gemini_params:
                    evaluator_kwargs['thinking_level'] = gemini_params['thinking_level']
                    logger.info(f"Using CLI thinking level: {gemini_params['thinking_level']}")
                if 'top_p' in gemini_params:
                    evaluator_kwargs['top_p'] = gemini_params['top_p']
                    logger.info(f"Using CLI top_p: {gemini_params['top_p']}")
            
            evaluator: BaseEvaluator = GeminiDirectEvaluator(**evaluator_kwargs)
            logger.info(f"Initialized Gemini Direct Evaluator: {gemini_model_to_use}")
        
        # Section-Based Evaluator (OpenRouter経由のGemini用フォールバック)
        elif (settings.ENABLE_SECTION_BASED_EVALUATION and 
              model_id_to_use and "gemini" in model_id_to_use.lower()):
            evaluator: BaseEvaluator = SectionBasedEvaluator(
                api_key=settings.OPENROUTER_API_KEY,
                base_url="https://openrouter.ai/api/v1",
                retry_count=settings.RETRY_COUNT,
                retry_delay=settings.RETRY_DELAY_SECONDS,
                max_items_per_section=settings.MAX_ITEMS_PER_SECTION,
                enable_json_repair=settings.ENABLE_JSON_REPAIR
            )
            logger.info(f"Initialized Section-Based Evaluator (fallback) for Gemini: {model_id_to_use}")
        
        # Standard OpenRouter Evaluator (その他のモデル)
        else:
            evaluator: BaseEvaluator = OpenRouterEvaluator(
                api_key=settings.OPENROUTER_API_KEY,
                base_url="https://openrouter.ai/api/v1",
                retry_count=settings.RETRY_COUNT,
                retry_delay=settings.RETRY_DELAY_SECONDS
            )
            logger.info(f"Initialized Standard OpenRouter Evaluator for model: {model_id_to_use}")
            
    except Exception as e:
        logger.error(f"Failed to initialize LLM Evaluator: {e}", exc_info=True)
        return

    # 6. Create and run evaluation tasks concurrently
    max_concurrent_papers = max(1, getattr(settings, "MAX_CONCURRENT_PAPERS", 1))
    if max_concurrent_papers > 1:
        logger.info("Paper-level concurrency limit: %d", max_concurrent_papers)
    semaphore = asyncio.Semaphore(max_concurrent_papers)

    async def run_with_semaphore(coro):
        async with semaphore:
            return await coro

    evaluation_tasks = []
    for paper_file_path in structured_data_files:
        # Determine which annotation file to use for this paper
        annotation_file_to_use = None
        if human_annotations_dict:
            # For single dataset mode, we have only one annotation file
            if len(human_annotations_dict) == 1:
                annotation_file_to_use = list(human_annotations_dict.values())[0]
            else:
                # For multiple datasets, determine based on paper file path
                # Match based on which dataset directory contains this file
                paper_parent_dir = paper_file_path.parent.name
                for annotation_key, annotation_file in human_annotations_dict.items():
                    # Map annotation keys to expected directory names
                    if ("suda" in annotation_key.lower() and "suda" in paper_parent_dir.lower()) or \
                       ("tsuge" in annotation_key.lower() and "tsuge" in paper_parent_dir.lower()):
                        annotation_file_to_use = annotation_file
                        break
                
                # If no specific match found, use the first available annotation file
                if not annotation_file_to_use and human_annotations_dict:
                    annotation_file_to_use = list(human_annotations_dict.values())[0]
                    logger.debug(f"Using default annotation file for paper {paper_file_path.name}")
        
        task = evaluate_single_paper_processing_task(
            paper_file_path=paper_file_path,
            evaluator=evaluator,
            prisma_checklist=prisma_main_checklist, # Pass PrismaChecklist object
            prisma_abstract_checklist=prisma_abstract_checklist, # Pass PrismaChecklist object
            human_annotations_file=annotation_file_to_use,
            model_id=model_id_to_use, # Specific model for the evaluator to use
            format_type=format_type_to_use,
            dataset_source_name=dataset_source_name
        )
        evaluation_tasks.append(run_with_semaphore(task))
    
    logger.info(f"Dispatching {len(evaluation_tasks)} paper evaluation tasks.")
    ai_paper_evaluations_results: List[Optional[PaperEvaluation]] = await asyncio.gather(*evaluation_tasks, return_exceptions=True)
    
    # Filter out None results (failed tasks) and handle exceptions
    ai_paper_evaluations: List[PaperEvaluation] = []
    for i, result in enumerate(ai_paper_evaluations_results):
        if isinstance(result, PaperEvaluation):
            ai_paper_evaluations.append(result)
        elif isinstance(result, Exception):
            logger.error(f"Task for paper {structured_data_files[i].name} failed with exception: {result}", exc_info=result)
        else: # Should be None if task returned None without exception
            logger.warning(f"Task for paper {structured_data_files[i].name} returned no result (None).")


    if not ai_paper_evaluations:
        logger.warning("No AI evaluations were successfully completed after running all tasks.")
        # Consider saving an indicator file for no results
        savers.save_general_json_output(
            data_to_save={"message": "No AI evaluations completed successfully."},
            base_filename="NO_AI_EVALUATIONS",
            results_dir=settings.RESULTS_DIR,
            model_id=model_id_to_use,
            format_type=format_type_to_use
        )
        return
    logger.info(f"Successfully completed {len(ai_paper_evaluations)} AI paper evaluations.")

    # 7. Calculate accuracy metrics
    accuracy_results: Optional[Dict[str, Any]] = None
    if human_annotations_dict:
        logger.info("Calculating accuracy metrics...")
        try:
            # For multiple datasets, we need to combine all annotation files
            # The calculator expects a single AnnotationFile, so we'll combine them
            if len(human_annotations_dict) == 1:
                # Single annotation file - use directly
                combined_annotations = list(human_annotations_dict.values())[0]
            else:
                # Multiple annotation files - combine into one
                from ..schemas import AnnotationFile, AnnotationEntry
                combined_entries = []
                for annotation_file in human_annotations_dict.values():
                    if annotation_file.root:
                        combined_entries.extend(annotation_file.root)
                combined_annotations = AnnotationFile(root=combined_entries)
                logger.info(f"Combined {len(combined_entries)} annotation entries from {len(human_annotations_dict)} files")
            
            accuracy_results = calculators.calculate_overall_accuracy_metrics(
                ai_paper_evaluations, # Note: This list is modified in-place by the calculator
                combined_annotations
            )
            logger.info("Accuracy metrics calculated.")
        except Exception as e:
            logger.error(f"Error during accuracy calculation: {e}", exc_info=True)
            accuracy_results = {"error": str(e)} # Store error in results if needed
    else:
        logger.warning("Skipping accuracy calculation as human annotations were not loaded or available.")

    # 8. Save all results
    logger.info("Saving all processed results...")
    saved_eval_path = savers.save_ai_evaluations(
        ai_paper_evaluations, settings.RESULTS_DIR, model_id_to_use, format_type_to_use
    )
    if saved_eval_path:
        logger.info(f"AI evaluations saved to: {saved_eval_path}")

    if accuracy_results and "error" not in accuracy_results :
        saved_summary_path = savers.save_accuracy_summary(
            accuracy_results, settings.RESULTS_DIR, model_id_to_use, format_type_to_use
        )
        if saved_summary_path:
            logger.info(f"Accuracy summary saved to: {saved_summary_path}")

        comparison_details = accuracy_results.get("comparison_details", [])
        if comparison_details:
            saved_details_path = savers.save_comparison_details(
                comparison_details, settings.RESULTS_DIR, model_id_to_use, format_type_to_use
            )
            if saved_details_path:
                logger.info(f"Comparison details saved to: {saved_details_path}")
    elif accuracy_results and "error" in accuracy_results:
        logger.error(f"Accuracy calculation failed, not saving summary. Error: {accuracy_results['error']}")


    logger.info(f"Evaluation pipeline finished for model '{model_id_to_use}', format '{format_type_to_use}'.")
