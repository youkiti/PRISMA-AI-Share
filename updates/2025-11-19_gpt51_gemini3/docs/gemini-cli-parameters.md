# Gemini CLI Parameters Configuration

This document describes the CLI parameter support for Google Gemini models in PRISMA-AI.

## Overview

The PRISMA-AI CLI now supports configurable parameters for Google Gemini models, allowing fine-tuning of evaluation behavior through command-line arguments.

## New CLI Parameters

### Gemini Model (`--gemini-model`, `-gm`)
- **Type**: String
- **Default**: `gemini-2.5-pro` (from settings)
- **Purpose**: Select which Gemini model to use for evaluation
- **Usage**: `--gemini-model gemini-3-pro-preview`

**Available Models**:
- `gemini-2.5-pro`: Current stable model (default)
- `gemini-3-pro-preview`: New preview model

### Temperature (`--temperature`, `-t`)
- **Type**: Float (0.0-2.0)
- **Default**: Model-dependent
  - `gemini-2.5-pro`: 0.0 (deterministic)
  - `gemini-3-pro-preview`: 1.0 (recommended by Google)
- **Purpose**: Controls randomness in model output
- **Usage**: `--temperature 0.1`

**Important**: For Gemini 3, Google strongly recommends keeping temperature at the default value of 1.0. Changing it (especially to values below 1.0) may cause unexpected behavior such as loops or performance degradation on complex reasoning tasks.

**Recommendations for Gemini 2.5**:
- `0.0`: Completely deterministic (best for consistent evaluations)
- `0.1-0.3`: Low randomness (good for structured tasks like PRISMA evaluation)

### Thinking Budget (`--thinking-budget`, `-tb`)
- **Type**: Integer (-1 or positive)
- **Default**: -1 (unlimited)
- **Purpose**: Controls the amount of internal reasoning tokens (for Gemini 2.5)
- **Usage**: `--thinking-budget 4096`
- **Note**: Cannot be used together with `--thinking-level`

**Recommendations for Gemini 2.5**:
- `-1`: Unlimited thinking (best quality, highest cost)
- `4096`: High-quality reasoning (good balance)
- `2048`: Moderate reasoning (faster, lower cost)
- `1024`: Basic reasoning (fastest, lowest cost)

### Thinking Level (`--thinking-level`, `-tl`)
- **Type**: String (low, medium, high)
- **Default**: `high` for Gemini 3 models
- **Purpose**: Controls the depth of internal reasoning (for Gemini 3)
- **Usage**: `--thinking-level low`
- **Note**: Cannot be used together with `--thinking-budget`

**Options**:
- `low`: Minimizes latency and cost. Best for simple instruction following, chat, and high-throughput applications
- `medium`: (Coming soon) Not supported at release
- `high` (default): Maximizes reasoning depth. Model may take longer to reach first token, but outputs are more carefully reasoned

### Top-p (`--top-p`, `-tp`)
- **Type**: Float (0.0-1.0)
- **Default**: 1.0 (consider all tokens)
- **Purpose**: Controls nucleus sampling for token selection
- **Usage**: `--top-p 0.4`

**Recommendations**:
- `0.4-0.6`: More focused responses (good for structured evaluation)
- `0.7-0.9`: Balanced responses
- `1.0`: Consider all possible tokens (most diverse)

## Usage Examples

### Basic Evaluation with Default Parameters
```bash
python -m prisma_evaluator.cli.main run \
  --model gemini-2.5-pro \
  --num-papers 3
```

### Using Gemini 3 (with default settings: temp=1.0, thinking_level=high)
```bash
python -m prisma_evaluator.cli.main run \
  --model gemini-2.5-pro \
  --gemini-model gemini-3-pro-preview \
  --num-papers 3
```

### Gemini 3 with Low Latency Mode
```bash
python -m prisma_evaluator.cli.main run \
  --model gemini-2.5-pro \
  --gemini-model gemini-3-pro-preview \
  --thinking-level low \
  --num-papers 3
```

### Gemini 2.5 High-Precision Evaluation
```bash
python -m prisma_evaluator.cli.main run \
  --model gemini-2.5-pro \
  --temperature 0.0 \
  --thinking-budget 4096 \
  --top-p 0.4 \
  --num-papers 3
```

### Balanced Evaluation (Recommended)
```bash
python -m prisma_evaluator.cli.main run \
  --model gemini-2.5-pro \
  --temperature 0.1 \
  --thinking-budget 2048 \
  --top-p 0.6 \
  --num-papers 3
```

### Fast Evaluation
```bash
python -m prisma_evaluator.cli.main run \
  --model gemini-2.5-pro \
  --temperature 0.2 \
  --thinking-budget 1024 \
  --top-p 0.8 \
  --num-papers 3
```

## Parameter Combinations for Different Use Cases

### Research/Publication (Highest Quality)
- `--temperature 0.0`
- `--thinking-budget -1` (unlimited)
- `--top-p 0.4`
- **Trade-off**: Highest accuracy, highest cost, slowest

### Production Evaluation (Balanced)
- `--temperature 0.1`
- `--thinking-budget 2048`
- `--top-p 0.6`
- **Trade-off**: Good accuracy, moderate cost, reasonable speed

### Rapid Prototyping (Fastest)
- `--temperature 0.2`
- `--thinking-budget 1024`
- `--top-p 0.8`
- **Trade-off**: Acceptable accuracy, lowest cost, fastest

## Implementation Details

### Code Changes
1. **CLI Interface** (`prisma_evaluator/cli/main.py`):
   - Added three new optional parameters to the `run` command
   - Parameters are validated and passed to the evaluation pipeline

2. **Pipeline Integration** (`prisma_evaluator/core/pipeline.py`):
   - Updated `run_evaluation_pipeline()` to accept `gemini_params`
   - Parameters are passed to GeminiDirectEvaluator during initialization

3. **Evaluator Enhancement** (`prisma_evaluator/llm/gemini_direct_evaluator.py`):
   - Constructor now accepts temperature, thinking_budget, and top_p parameters
   - Parameters are used in the actual API calls
   - Metadata includes the actual parameters used for traceability

### Parameter Validation
- All parameters have appropriate min/max constraints
- Invalid values are rejected at the CLI level
- Parameters are only applied to Gemini models (ignored for other models)

## Monitoring and Results

### Parameter Tracking
- All used parameters are logged during evaluation
- Parameters are included in the evaluation metadata
- Results files contain the exact configuration used

### Performance Comparison
To compare different parameter configurations:

1. Run evaluations with different parameters
2. Compare results in the `logs/results/` directory
3. Look for accuracy and processing time differences

## Troubleshooting

### Common Issues
1. **Parameters ignored**: Ensure you're using a Gemini model (`gemini-2.5-pro`)
2. **Invalid parameter values**: Check the allowed ranges for each parameter
3. **No effect observed**: Some parameters have subtle effects - compare with extreme values

### Debugging
Enable debug logging to see parameter usage:
```bash
python -m prisma_evaluator.cli.main run \
  --log-level DEBUG \
  --model gemini-2.5-pro \
  --temperature 0.1
```

## Best Practices

1. **Start with defaults**: Use default parameters first to establish baseline
2. **Systematic testing**: Change one parameter at a time to understand effects
3. **Document configuration**: Keep track of which parameters work best for your use case
4. **Consider cost**: Higher thinking budgets and unlimited thinking increase costs
5. **Validate results**: Always compare accuracy against human annotations

## Future Enhancements

Potential future additions:
- Parameter presets (e.g., `--preset research`, `--preset fast`)
- Automatic parameter optimization based on target accuracy
- Parameter recommendations based on paper characteristics
- Batch evaluation with parameter sweeps