Pending the ingestion of unified evaluator outputs for the Suda and Tsuge cohorts, the item-level error profile cannot yet report checklist-specific FN or FP rates; once the datasets are available, rerun the aggregation script to update these metrics.
<!--
canonical: results/evaluator_output/
finalized: test/issues/2025-10-31_item_level_error_profile/reports/
regen: .venv/bin/python analysis/item_level_error_profile.py --dataset Suda=<path_to_unified_json> --dataset Tsuge=<path_to_unified_json> --output-dir test/issues/2025-10-31_item_level_error_profile/reports
consistency: Ensure each dataset supplies comparison_details with TREAT_FAILED_AS_INCORRECT=true; verify fnfp_item_support.json totals before manuscript insertion.
notes: Replace placeholder sentence with quantitative findings immediately after regenerating the reports.
-->
