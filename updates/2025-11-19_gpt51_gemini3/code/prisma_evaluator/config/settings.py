from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional, Literal
import os

# BASE_DIR はプロジェクトルートを指すように調整が必要な場合があります。
# ここでは、この settings.py ファイルの親の親の親をプロジェクトルートと仮定します。
# 例: prisma_evaluator/config/settings.py -> prisma_evaluator/ -> project_root/
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = Path(__file__).resolve().parent # Directory of this config file

class Settings(BaseSettings):
    # API Keys (expected from .env or environment)
    OPENROUTER_API_KEY: str
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # Paths (expected from .env, environment, or default_settings.toml)
    # PRISMA_AI_DRIVE_PATH: External data directory path (e.g., /path/to/prisma-ai-data)
    PRISMA_AI_DRIVE_PATH: Path
    ANNOTATION_DATA_PATH: Path

    # Evaluation Parameters (defaults from default_settings.toml, overridable by .env/environment)
    NUM_PAPERS_TO_EVALUATE: int = 5 # Default here acts as ultimate fallback
    DEFAULT_MODEL_ID: str = "openai/gpt-4o"
    RETRY_COUNT: int = 3
    RETRY_DELAY_SECONDS: int = 5
    MAX_CONCURRENT_PAPERS: int = 3
    TREAT_FAILED_AS_INCORRECT: bool = True
    MAX_EVALUATION_RETRIES: int = 3

    # Section-based evaluation settings
    ENABLE_SECTION_BASED_EVALUATION: bool = True
    MAX_ITEMS_PER_SECTION: int = 12
    ENABLE_JSON_REPAIR: bool = True
    
    # Gemini Direct API settings
    ENABLE_GEMINI_DIRECT: bool = True
    GEMINI_DIRECT_MODEL: str = "gemini-2.5-pro"
    
    # GPT-5 specific settings (optimized for PRISMA evaluation)
    GPT5_VERBOSITY: Literal["low", "medium", "high"] = "low"  # Default low for yes/no responses
    GPT5_REASONING_EFFORT: Literal["none", "minimal", "medium", "high"] = "minimal"  # Fast evaluation (gpt-5.1 defaults to none unless overridden)
    ENABLE_GPT5_CFG: bool = True  # Context-Free Grammar constraints
    ENABLE_GPT5_FREEFORM: bool = True  # Free-form function calling
    
    # OpenRouter model specific settings
    OPENROUTER_MAX_TOKENS: int = 4096  # Default for most models
    GPT_OSS_MAX_TOKENS: int = 60000  # GPT-OSS specific limit (reduced for context safety)
    GPT_OSS_REASONING_EFFORT: Literal["low", "minimal", "medium", "high"] = "high"
    
    # Qwen thinking model specific settings
    QWEN_THINKING_MAX_TOKENS: int = 60000  # Qwen thinking model output limit
    QWEN_THINKING_REASONING_MAX_TOKENS: int = 20000  # Reasoning dedicated tokens
    QWEN_THINKING_REASONING_EFFORT: Literal["low", "minimal", "medium", "high"] = "medium"
    # Note: temperature cannot be set when using reasoning parameter

    # Qwen Max model specific settings
    QWEN_MAX_MAX_TOKENS: int = 32768  # Conservative cap matching OpenRouter guidance (32k output tokens)
    QWEN_MAX_SUPPORTS_REASONING: bool = False  # OpenRouter Qwen Max currently lacks reasoning mode

    # Dataset Selection Flags (from toml, overridable by .env)
    ENABLE_SUDA: bool = False
    ENABLE_TSUGE_OTHER: bool = False
    ENABLE_TSUGE_PRISMA: bool = True  # Default to Tsuge PRISMA dataset
    
    # Directory Names (dynamically set based on dataset flags)
    # Note: STRUCTURED_DATA_SUBDIR is relative to PRISMA_AI_DRIVE_PATH
    
    LOGS_DIR_NAME: str = "logs"
    RESULTS_DIR_NAME: str = "results/evaluator_output"

    # Checklist Files (from toml, overridable by .env)
    PRISMA_CHECKLIST_FILE: str = "PRISMA_2020_checklist.md"
    PRISMA_ABSTRACT_CHECKLIST_FILE: str = "PRISMA_2020_abstract_checklist.md"

    # --- Derived Paths (computed properties) ---
    def _validate_dataset_flags(self) -> None:
        """Validate dataset flags configuration."""
        enabled_flags = sum([self.ENABLE_SUDA, self.ENABLE_TSUGE_OTHER, self.ENABLE_TSUGE_PRISMA])
        if enabled_flags == 0:
            raise ValueError(
                "At least one dataset flag must be enabled. "
                "Please set one of: ENABLE_SUDA, ENABLE_TSUGE_OTHER, or ENABLE_TSUGE_PRISMA to True."
            )

    @property
    def ALL_DATASETS_ENABLED(self) -> bool:
        """Check if all three datasets are enabled."""
        return self.ENABLE_SUDA and self.ENABLE_TSUGE_OTHER and self.ENABLE_TSUGE_PRISMA

    @property
    def ENABLED_DATASETS(self) -> list[str]:
        """Get list of enabled dataset names."""
        datasets = []
        if self.ENABLE_SUDA:
            datasets.append("suda2025")
        if self.ENABLE_TSUGE_OTHER:
            datasets.append("tsuge2025_other")
        if self.ENABLE_TSUGE_PRISMA:
            datasets.append("tsuge2025_prisma")
        return datasets

    @property
    def DATASET_NAME(self) -> str:
        """Get the name of the currently active dataset(s)."""
        self._validate_dataset_flags()
        if self.ALL_DATASETS_ENABLED:
            return "all"
        elif self.ENABLE_SUDA and not (self.ENABLE_TSUGE_OTHER or self.ENABLE_TSUGE_PRISMA):
            return "suda2025"
        elif self.ENABLE_TSUGE_OTHER and not (self.ENABLE_SUDA or self.ENABLE_TSUGE_PRISMA):
            return "tsuge2025_other"
        elif self.ENABLE_TSUGE_PRISMA and not (self.ENABLE_SUDA or self.ENABLE_TSUGE_OTHER):
            return "tsuge2025_prisma"
        else:
            # Multiple datasets enabled but not all - return combined name
            return "_".join(self.ENABLED_DATASETS)

    @property
    def STRUCTURED_DATA_SUBDIRS(self) -> list[str]:
        """Get list of all enabled structured data subdirectories."""
        self._validate_dataset_flags()
        subdirs = []
        if self.ENABLE_SUDA:
            subdirs.append("Suda2025-SR文献")
        if self.ENABLE_TSUGE_OTHER:
            subdirs.append("Tsuge2025-other")
        if self.ENABLE_TSUGE_PRISMA:
            subdirs.append("Tsuge2025-PRISMA")
        return subdirs

    @property
    def STRUCTURED_DATA_SUBDIR(self) -> str:
        """Dynamically determine the structured data subdirectory based on dataset flags.
        Returns first subdirectory for backward compatibility when only one dataset is enabled.
        """
        subdirs = self.STRUCTURED_DATA_SUBDIRS
        if len(subdirs) == 1:
            return subdirs[0]
        else:
            # Multiple datasets - return first one for backward compatibility
            # The new pipeline logic should use STRUCTURED_DATA_SUBDIRS instead
            return subdirs[0] if subdirs else "Tsuge2025-PRISMA"
    
    @property
    def ANNOTATION_FILE_NAMES(self) -> list[str]:
        """Get list of all enabled annotation file names."""
        self._validate_dataset_flags()
        files = []
        if self.ENABLE_SUDA:
            files.append("suda2025_merged.json")
        if self.ENABLE_TSUGE_OTHER or self.ENABLE_TSUGE_PRISMA:
            # Both tsuge datasets use the same annotation file
            if "tsuge2025_merged.json" not in files:
                files.append("tsuge2025_merged.json")
        return files

    @property
    def ANNOTATION_FILE_NAME(self) -> str:
        """Dynamically determine the annotation file name based on dataset flags.
        Returns first file for backward compatibility when only one dataset is enabled.
        """
        files = self.ANNOTATION_FILE_NAMES
        if len(files) == 1:
            return files[0]
        else:
            # Multiple annotation files - return first one for backward compatibility
            # The new pipeline logic should use ANNOTATION_FILE_NAMES instead
            return files[0] if files else "tsuge2025_merged.json"

    @property
    def STRUCTURED_DATA_DIRS(self) -> list[Path]:
        """Get list of all enabled structured data directories."""
        return [self.PRISMA_AI_DRIVE_PATH / subdir for subdir in self.STRUCTURED_DATA_SUBDIRS]

    @property
    def STRUCTURED_DATA_DIR(self) -> Path:
        """Return first structured data directory for backward compatibility."""
        return self.PRISMA_AI_DRIVE_PATH / self.STRUCTURED_DATA_SUBDIR

    @property
    def ANNOTATION_FILE_PATHS(self) -> list[Path]:
        """Get list of all enabled annotation file paths."""
        return [self.ANNOTATION_DATA_PATH / filename for filename in self.ANNOTATION_FILE_NAMES]

    @property
    def ANNOTATION_FILE_PATH(self) -> Path:
        """Return first annotation file path for backward compatibility."""
        return self.ANNOTATION_DATA_PATH / self.ANNOTATION_FILE_NAME
    
    @property
    def PACKAGE_RESOURCES_DIR(self) -> Path:
        # prisma_evaluator パッケージ内の resources ディレクトリを想定
        return Path(__file__).resolve().parent.parent / "resources"

    @property
    def PRISMA_CHECKLIST_PATH(self) -> Path:
        return self.PACKAGE_RESOURCES_DIR / "formats" / self.PRISMA_CHECKLIST_FILE

    @property
    def PRISMA_ABSTRACT_CHECKLIST_PATH(self) -> Path:
        return self.PACKAGE_RESOURCES_DIR / "formats" / self.PRISMA_ABSTRACT_CHECKLIST_FILE

    @property
    def LOG_DIR(self) -> Path:
        # プロジェクトルート直下の logs ディレクトリを想定
        return BASE_DIR / self.LOGS_DIR_NAME

    @property
    def RESULTS_DIR(self) -> Path:
        # プロジェクトルート直下の results ディレクトリを想定
        return BASE_DIR / self.RESULTS_DIR_NAME
    
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding='utf-8',
        toml_file=CONFIG_DIR / "default_settings.toml", # Load TOML for defaults
        extra='ignore'
    )

# The Settings class will now attempt to load values in the following priority:
# 1. Environment variables.
# 2. Variables from .env file.
# 3. Variables from default_settings.toml.
# 4. Default values defined in the Settings class fields themselves.

settings = Settings()

# .envファイルが存在しない場合の警告
if not (BASE_DIR / ".env").exists():
    print(f"警告: .envファイル ({BASE_DIR / '.env'}) が見つかりません。"
          " APIキーやパス設定は環境変数または default_settings.toml から読み込まれます。"
          " 重要な設定が不足している場合、アプリケーションは起動時にエラーとなる可能性があります。")

# PRISMA_AI_DRIVE_PATH と ANNOTATION_DATA_PATH は Settings モデルで必須フィールドとして定義されており、
# default_settings.toml または .env ファイル、環境変数のいずれかで設定される必要があります。
# 設定されていない場合、Settings() のインスタンス化時に Pydantic が ValidationError を発生させます。
