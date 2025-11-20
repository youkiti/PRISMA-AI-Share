"""
Google Gemini Direct API Evaluator

OpenRouterを経由せず、Google Direct APIでGemini 2.5 Proを使用
Function Callingで42項目の一括評価を実現

Created: 2025-06-30
Purpose: OpenRouterの制限を回避し、Geminiの真の能力を活用
"""
import asyncio
import json
import logging
import time
from collections.abc import Mapping
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Literal

from pydantic import ValidationError

from .base_evaluator import BaseEvaluator
from ..schemas import AIEvaluation, ProcessingMetadata, PrismaChecklist, PrismaChecklistItem
from ..resources.prisma_eande_loader import get_item_details_for_schema
from .utils import render_checklist_content

logger = logging.getLogger(__name__)

class GeminiDirectEvaluator(BaseEvaluator):
    """
    Google Gemini Direct API Evaluator
    
    OpenRouterを経由せず、Google Direct APIでGemini 2.5 Proを直接使用。
    42項目のPRISMAチェックリストを一括でFunction Callingにより評価。
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.5-pro",
        retry_count: int = 3,
        retry_delay: int = 5,
        temperature: Optional[float] = None,
        thinking_budget: Optional[int] = None,
        thinking_level: Optional[str] = None,
        top_p: float = 1.0,
        schema_type: str = "simple",
        checklist_format: str = "md",
        dynamic_schema_file: Optional[str] = None,
        max_retries: int = 3
    ):
        """
        Args:
            api_key: Google Gemini API キー
            model: 使用するGeminiモデル（デフォルト: gemini-2.5-pro）
            retry_count: リトライ回数（Legacy）
            retry_delay: リトライ間隔（秒）（Legacy）
            temperature: 温度パラメータ（0.0-2.0）。Noneの場合はモデル別デフォルトを使用
            thinking_budget: 思考トークン予算（-1で無制限）。Gemini 2.5用
            thinking_level: 思考レベル（low, medium, high）。Gemini 3用
            top_p: Top-pサンプリング（0.0-1.0、デフォルト: 1.0）
            max_retries: 新しいリトライシステムでの最大リトライ回数
        """
        super().__init__(max_retries=max_retries)
        self.api_key = api_key
        self.model = model
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.thinking_budget = thinking_budget
        self.thinking_level = thinking_level
        self.top_p = top_p
        self.schema_type = schema_type
        clf = (checklist_format or "md").lower()
        self.checklist_format = clf if clf in ("md", "text", "json", "xml", "none") else "md"
        self.dynamic_schema_file = dynamic_schema_file

        # モデル別デフォルト値の設定
        is_gemini3 = "gemini-3" in model.lower()
        if temperature is None:
            self.temperature = 1.0 if is_gemini3 else 0.0
        else:
            self.temperature = temperature

        # Gemini 3のデフォルトthinking_level
        if is_gemini3 and thinking_level is None and thinking_budget is None:
            self.thinking_level = "high"

        logger.info(f"Model: {model}, Temperature: {self.temperature}, "
                    f"Thinking Level: {self.thinking_level}, Thinking Budget: {self.thinking_budget}")
        
        # Google Gemini APIクライアントの初期化（google-genai SDK）
        try:
            from google import genai
        except ImportError as exc:
            raise ImportError("google-genai パッケージが必要です: pip install google-genai") from exc

        self.genai = genai
        self.client = genai.Client(api_key=api_key)
        self.types = genai.types
        logger.info(f"Google Gemini Direct API client initialized with model: {model}")
        self._thinking_config_cls = getattr(self.types, "ThinkingConfig", None)
        self._thinking_config_warning_emitted = False
        if self.thinking_level or self.thinking_budget:
            if not self._thinking_config_cls:
                logger.warning(
                    "Installed Gemini SDK does not expose ThinkingConfig; "
                    "falling back to provider defaults for thinking parameters."
                )

    def build_prompt(
        self, 
        paper_text_content: str, 
        prisma_checklist: Optional[PrismaChecklist], 
        prisma_abstract_checklist: Optional[PrismaChecklist], 
        evaluation_type: Literal["main", "abstract"]
    ) -> List[Dict[str, str]]:
        """Gemini用のプロンプトを構築"""
        
        if evaluation_type == "main" and prisma_checklist:
            checklist_name = prisma_checklist.name or "PRISMA 2020 checklist"
            checklist_for_prompt = ""
            if self.checklist_format != "none":
                items_struct: List[Dict[str, str]] = []
                for item in prisma_checklist.items:
                    if self.schema_type in [
                        "detailed",
                        "few-shot",
                        "few-shot-v2",
                        "few-shot-v3",
                        "few-shot-v4",
                        "few-shot-v5",
                        "few-shot-v6",
                        "eande-incontext",
                        "dynamic",
                    ]:
                        eande_details = get_item_details_for_schema(
                            item.item_id,
                            self.schema_type,
                            self.dynamic_schema_file,
                        )
                        desc = eande_details.get('description', item.description) if eande_details else item.description
                        title = eande_details.get('name', item.description) if eande_details else item.description
                    else:
                        desc = item.description
                        title = item.description
                    items_struct.append({
                        "item_id": item.item_id,
                        "category": item.category,
                        "section": item.section,
                        "title": title,
                        "description": desc,
                    })

                checklist_for_prompt = render_checklist_content(
                    self.checklist_format,
                    checklist_name,
                    items_struct,
                )
            else:
                checklist_for_prompt = ""

            prompt_content = f"""
You are an expert reviewer for the PRISMA (Preferred Reporting Items for Systematic Reviews and Meta-Analyses) guideline.
Evaluate the provided systematic review against the PRISMA 2020 checklist ({len(prisma_checklist.items)} items).

For each item:
- result: decide strictly between "yes" and "no".
- reason: provide a concise justification (50 words or fewer).

Use the exact item IDs shown (e.g., "1", "3a") as dictionary keys when returning data.

PRISMA 2020 checklist items:
{checklist_for_prompt}

Evaluate all {len(prisma_checklist.items)} items. When information is missing or unclear, answer "no".
Call the function submit_prisma_evaluation to return your output.

=== Target review ===
{paper_text_content}
"""
        
        elif evaluation_type == "abstract" and prisma_abstract_checklist:
            checklist_name = prisma_abstract_checklist.name or "PRISMA abstract checklist"
            checklist_for_prompt = ""
            if self.checklist_format != "none":
                items_struct: List[Dict[str, str]] = []
                for item in prisma_abstract_checklist.items:
                    if self.schema_type in [
                        "detailed",
                        "few-shot",
                        "few-shot-v2",
                        "few-shot-v3",
                        "few-shot-v4",
                        "few-shot-v5",
                        "few-shot-v6",
                        "eande-incontext",
                        "dynamic",
                    ]:
                        eande_details = get_item_details_for_schema(
                            item.item_id,
                            self.schema_type,
                            self.dynamic_schema_file,
                        )
                        desc = eande_details.get('description', item.description) if eande_details else item.description
                        title = eande_details.get('name', item.description) if eande_details else item.description
                    else:
                        desc = item.description
                        title = item.description
                    items_struct.append({
                        "item_id": item.item_id,
                        "category": item.category,
                        "section": item.section,
                        "title": title,
                        "description": desc,
                    })

                checklist_for_prompt = render_checklist_content(
                    self.checklist_format,
                    checklist_name,
                    items_struct,
                )
            else:
                checklist_for_prompt = ""

            prompt_content = f"""
You are an expert reviewer for the PRISMA guideline.
Evaluate the abstract of the provided paper against the PRISMA abstract checklist ({len(prisma_abstract_checklist.items)} items).

For each item:
- result: decide strictly between "yes" and "no".
- reason: provide a concise justification (50 words or fewer).

Use the exact item IDs shown (e.g., "item_1") as dictionary keys when returning data.

PRISMA abstract checklist items:
{checklist_for_prompt}

Call the function submit_prisma_evaluation to return the results.

=== Target abstract ===
{paper_text_content}
"""
        else:
            raise ValueError(f"Invalid evaluation_type: {evaluation_type} or missing checklist")
        
        return [{"role": "user", "content": prompt_content}]

    def _build_generation_config(
        self,
        tools: Optional[List[Any]] = None,
        max_output_tokens: Optional[int] = None,
    ):
        config_kwargs: Dict[str, Any] = {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_output_tokens": max_output_tokens,
        }
        if tools is not None:
            config_kwargs["tools"] = tools

        # thinking_levelまたはthinking_budgetを設定（両方は使用不可）
        thinking_config_cls = self._thinking_config_cls
        if self.thinking_level is not None:
            # Gemini 3用: thinking_levelを使用（google-genai: ThinkingConfig.thinkingLevel）
            thinking_level_map = {
                "low": "LOW",
                "medium": "HIGH",  # SDKはLOW/HIGHのみサポート（mediumはHIGHに丸める）
                "high": "HIGH",
            }
            level = thinking_level_map.get(self.thinking_level, "HIGH")
            if thinking_config_cls:
                config_kwargs["thinking_config"] = thinking_config_cls(
                    thinkingLevel=level,
                    includeThoughts=False,
                )
                logger.debug(f"Using thinking_level: {level}")
            else:
                self._log_missing_thinking_config_once("thinking_level")
        elif self.thinking_budget is not None:
            # Gemini 2.5用: thinking_budgetを使用
            if thinking_config_cls:
                config_kwargs["thinking_config"] = thinking_config_cls(
                    thinkingBudget=self.thinking_budget,
                    includeThoughts=False,
                )
                logger.debug(f"Using thinking_budget: {self.thinking_budget}")
            else:
                self._log_missing_thinking_config_once("thinking_budget")

        return self.types.GenerateContentConfig(**config_kwargs)

    def _log_missing_thinking_config_once(self, param_name: str) -> None:
        if self._thinking_config_warning_emitted:
            return
        logger.warning(
            "Gemini SDK missing ThinkingConfig; ignoring %s override and using API defaults.",
            param_name,
        )
        self._thinking_config_warning_emitted = True

    async def _generate_with_function(
        self,
        prompt: str,
        function_declaration: Any,
        max_output_tokens: Optional[int] = None,
    ) -> Any:
        def _run():
            tools = [self.types.Tool(function_declarations=[function_declaration])]
            contents = [
                self.types.Content(
                    role="user",
                    parts=[self.types.Part.from_text(text=prompt)],
                )
            ]
            generate_content_config = self._build_generation_config(
                tools=tools,
                max_output_tokens=max_output_tokens,
            )
            return self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=generate_content_config,
            )

        return await asyncio.to_thread(_run)

    def _parse_function_response(self, response: Any, function_name: str) -> Dict[str, AIEvaluation]:
        evaluations: Dict[str, AIEvaluation] = {}
        candidates = getattr(response, "candidates", []) or []
        if not candidates:
            logger.warning("Gemini response contained no candidates for function '%s'", function_name)
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            parts = getattr(content, "parts", []) if content else []
            for part in parts:
                func_call = getattr(part, "function_call", None)
                if not func_call or getattr(func_call, "name", "") != function_name:
                    continue
                args = getattr(func_call, "args", {}) or {}
                if hasattr(args, "to_dict"):
                    try:
                        args = args.to_dict()
                    except Exception:
                        args = dict(args) if isinstance(args, Mapping) else args
                elif isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        logger.warning("Gemini function_call args JSON decode failed; skipping candidate")
                        continue
                elif isinstance(args, Mapping):
                    args = dict(args)

                if not isinstance(args, dict):
                    logger.warning("Gemini function_call args unexpected type: %s", type(args))
                    continue

                raw_evaluations = args.get("evaluations", {})
                if hasattr(raw_evaluations, "to_dict"):
                    try:
                        raw_evaluations = raw_evaluations.to_dict()
                    except Exception:
                        raw_evaluations = dict(raw_evaluations) if isinstance(raw_evaluations, Mapping) else raw_evaluations
                elif isinstance(raw_evaluations, str):
                    try:
                        raw_evaluations = json.loads(raw_evaluations)
                    except json.JSONDecodeError:
                        logger.warning("Gemini evaluations payload JSON decode failed; skipping candidate")
                        continue
                elif isinstance(raw_evaluations, Mapping):
                    raw_evaluations = dict(raw_evaluations)

                if not isinstance(raw_evaluations, dict):
                    logger.warning("Gemini evaluations payload unexpected type: %s", type(raw_evaluations))
                    continue
                for item_id, eval_data in raw_evaluations.items():
                    if hasattr(eval_data, "to_dict"):
                        try:
                            eval_data = eval_data.to_dict()
                        except Exception:
                            eval_data = dict(eval_data) if isinstance(eval_data, Mapping) else eval_data
                    elif isinstance(eval_data, Mapping):
                        eval_data = dict(eval_data)
                    if isinstance(eval_data, dict) and "result" in eval_data and "reason" in eval_data:
                        result_value = eval_data.get("result")
                        if isinstance(result_value, str):
                            result_value = result_value.strip().lower()
                        try:
                            evaluations[item_id] = AIEvaluation(
                                result=result_value,
                                reason=eval_data.get("reason"),
                                raw_response="",
                            )
                        except ValidationError:
                            continue
        return evaluations

    def _log_response_diagnostics(self, response: Any, context: str) -> None:
        """Function Callingレスポンスの概要をログ出力"""
        try:
            candidates = getattr(response, "candidates", []) or []
            logger.warning("Gemini diagnostics (%s): %d candidates", context, len(candidates))
            for idx, candidate in enumerate(candidates):
                content = getattr(candidate, "content", None)
                parts = getattr(content, "parts", []) if content else []
                finish_reason = getattr(candidate, "finish_reason", None)
                logger.debug(
                    "Gemini candidate[%d] finish_reason=%s parts=%d",
                    idx,
                    finish_reason,
                    len(parts),
                )
                for p_idx, part in enumerate(parts):
                    func_call = getattr(part, "function_call", None)
                    if func_call:
                        name = getattr(func_call, "name", None)
                        args = getattr(func_call, "args", None)
                        args_type = type(args).__name__
                        if hasattr(args, "to_dict"):
                            try:
                                args_payload = args.to_dict()
                            except Exception:
                                args_payload = repr(args)
                            args_repr = json.dumps(args_payload, ensure_ascii=False)[:1000]
                            args_type = "to_dict"
                        elif isinstance(args, dict):
                            args_repr = json.dumps(args, ensure_ascii=False)[:1000]
                        elif isinstance(args, Mapping):
                            try:
                                args_repr = json.dumps(dict(args), ensure_ascii=False)[:1000]
                            except Exception:
                                args_repr = repr(args)[:500]
                        elif isinstance(args, str):
                            args_repr = args[:1000]
                        else:
                            args_repr = repr(args)[:500]
                        logger.warning(
                            "Gemini candidate[%d] part[%d] function_call name=%s args_type=%s preview=%s",
                            idx,
                            p_idx,
                            name,
                            args_type,
                            args_repr,
                        )
                    elif hasattr(part, "text"):
                        text_preview = getattr(part, "text", "")[:500]
                        logger.warning(
                            "Gemini candidate[%d] part[%d] text preview=%s",
                            idx,
                            p_idx,
                            text_preview,
                        )
                    else:
                        attrs = list(vars(part).keys()) if hasattr(part, "__dict__") else type(part).__name__
                        logger.warning(
                            "Gemini candidate[%d] part[%d] unknown structure: %s",
                            idx,
                            p_idx,
                            attrs,
                        )
        except Exception:
            logger.exception("Failed to log Gemini diagnostics for %s", context)

    def _extract_usage_metadata(self, response: Any) -> Dict[str, int]:
        token_usage: Dict[str, int] = {}
        usage = getattr(response, "usage_metadata", None)
        if not usage:
            return token_usage

        def capture(value: Any, *keys: str) -> None:
            if isinstance(value, (int, float)):
                for key in keys:
                    if key not in token_usage:
                        token_usage[key] = int(value)

        prompt_tokens = getattr(usage, "prompt_token_count", None)
        capture(prompt_tokens, "prompt_token_count", "prompt_tokens", "input_tokens")

        completion_tokens = getattr(usage, "candidates_token_count", None)
        capture(completion_tokens, "candidates_token_count", "completion_tokens", "output_tokens")

        cached_tokens = getattr(usage, "cached_content_token_count", None)
        capture(cached_tokens, "cached_content_token_count", "cached_tokens")

        total_tokens = getattr(usage, "total_token_count", None)
        capture(total_tokens, "total_token_count", "total_tokens")

        if "total_tokens" not in token_usage:
            combined = 0
            has_any = False
            for key in ("input_tokens", "prompt_tokens", "output_tokens", "completion_tokens"):
                if key in token_usage:
                    combined += token_usage[key]
                    has_any = True
            if has_any:
                token_usage["total_tokens"] = int(combined)

        return token_usage
    
    def get_tool_schema(self, evaluation_type: Literal["main", "abstract"]) -> List[Dict[str, str]]:
        """Gemini用のツールスキーマは使用しない（Function Declarationで直接定義）"""
        return []

    async def evaluate_failed_items(
        self,
        failed_item_ids: List[str],
        paper_id: str,
        paper_text_content: str,
        prisma_checklist: Optional[PrismaChecklist],
        prisma_abstract_checklist: Optional[PrismaChecklist],
        evaluation_type: Literal["main", "abstract"],
        model_id: str,
        format_type: str
    ) -> Optional[Tuple[Dict[str, AIEvaluation], ProcessingMetadata]]:
        """
        失敗した項目のみを再評価するGemini実装
        """
        start_time = time.time()
        self.logger.info(f"Gemini: Evaluating {len(failed_item_ids)} failed items for {paper_id} ({evaluation_type})")
        
        # 評価対象のチェックリストを決定
        target_checklist = prisma_abstract_checklist if evaluation_type == "abstract" else prisma_checklist
        if not target_checklist:
            self.logger.error(f"No checklist available for {evaluation_type} evaluation")
            return None
        
        # 失敗項目のみのFunction Declarationを作成
        partial_function_declaration = self._create_partial_function_declaration(
            checklist=target_checklist,
            evaluation_type=evaluation_type,
            failed_item_ids=failed_item_ids
        )
        
        # プロンプト作成
        prompt = self._build_partial_prompt(
            paper_text_content=paper_text_content,
            target_checklist=target_checklist,
            evaluation_type=evaluation_type,
            failed_item_ids=failed_item_ids
        )
        
        try:
            response = await self._generate_with_function(prompt, partial_function_declaration, max_output_tokens=8192)
            evaluations = self._parse_function_response(response, "prisma_evaluation_partial")
            filtered_evaluations = {
                item_id: evaluation
                for item_id, evaluation in evaluations.items()
                if item_id in failed_item_ids
            }

            if not filtered_evaluations:
                self._log_response_diagnostics(response, f"retry_{evaluation_type}_{len(failed_item_ids)}items")

            processing_time = time.time() - start_time
            token_usage = self._extract_usage_metadata(response)
            token_count = token_usage.get("total_token_count", 0)

            metadata = ProcessingMetadata(
                model_id=model_id,
                model_version=self.model,
                max_tokens=8192,
                format_type=format_type,
                prompt_version="gemini_partial_retry_v2",
                token_count=token_count,
                token_usage=token_usage,
                processing_time=processing_time,
                timestamp=datetime.now()
            )

            self.logger.info(
                f"Gemini partial retry success: {len(filtered_evaluations)} items evaluated in {processing_time:.2f}s"
            )
            return filtered_evaluations, metadata

        except Exception as e:
            self.logger.error(f"Gemini partial evaluation failed: {e}")
            return None

    def _create_partial_function_declaration(
        self, 
        checklist: PrismaChecklist, 
        evaluation_type: Literal["main", "abstract"],
        failed_item_ids: List[str]
    ) -> Any:
        """失敗項目のみのFunction Declarationを作成"""
        
        # 失敗した項目のみを含むプロパティを生成
        properties = {}
        required_items = []
        
        for item in checklist.items:
            item_key = f"item_{item.item_id}" if evaluation_type == "abstract" else str(item.item_id)
            if item_key not in failed_item_ids:
                continue
            properties[item_key] = {
                "type": "OBJECT",
                "properties": {
                    "result": {
                        "type": "STRING",
                        "enum": ["yes", "no"],
                        "description": "PRISMA項目に対する評価結果（yes/no）",
                    },
                    "reason": {
                        "type": "STRING",
                        "description": f"評価理由: {item.description[:100]}...",
                    },
                },
                "required": ["result", "reason"],
            }
            required_items.append(item_key)

        return self.types.FunctionDeclaration(
            name="prisma_evaluation_partial",
            description=f"失敗した{len(failed_item_ids)}項目のPRISMA評価を実行",
            parameters={
                "type": "OBJECT",
                "properties": properties,
                "required": required_items,
            },
        )

    def _build_partial_prompt(
        self,
        paper_text_content: str,
        target_checklist: PrismaChecklist,
        evaluation_type: Literal["main", "abstract"],
        failed_item_ids: List[str]
    ) -> str:
        """失敗項目のみのプロンプトを構築"""
        
        evaluation_target = "抄録" if evaluation_type == "abstract" else "本文"
        
        # 失敗項目のみのチェックリストを作成
        failed_items_text = ""
        for item in target_checklist.items:
            item_key = f"item_{item.item_id}" if evaluation_type == "abstract" else str(item.item_id)
            if item_key in failed_item_ids:
                failed_items_text += f"\n{item_key}: [{item.category}] {item.description}"
        
        prompt = f"""
以下のシステマティックレビュー論文の{evaluation_target}を、指定されたPRISMAガイドライン項目について再評価してください。

これらの項目は初回評価で失敗したため、慎重に再評価をお願いします。

【評価対象の{evaluation_target}】
{paper_text_content}

【再評価が必要なPRISMA項目】
{failed_items_text}

【評価指示】
- 各項目について、{evaluation_target}にその要素が含まれているかを「yes」または「no」で厳密に判定
- 判定理由を簡潔に記載
- 少しでも曖昧な場合は「no」と判定
- Function Callingで構造化された結果を返してください

prisma_evaluation_partial関数を呼び出して評価結果を返してください。
"""
        return prompt
    
    def _create_function_declaration(self, checklist: PrismaChecklist, evaluation_type: Literal["main", "abstract"]) -> Any:
        """Gemini用のFunction Declarationを作成"""
        
        # 各項目のスキーマを動的生成
        properties = {}
        required_items = []
        
        for item in checklist.items:
            item_key = f"item_{item.item_id}" if evaluation_type == "abstract" else str(item.item_id)
            properties[item_key] = {
                "type": "OBJECT",
                "properties": {
                    "result": {"type": "STRING", "enum": ["yes", "no"]},
                    "reason": {"type": "STRING"},
                },
                "required": ["result", "reason"],
            }
            required_items.append(item_key)

        return self.types.FunctionDeclaration(
            name="submit_prisma_evaluation",
            description=f"PRISMA評価結果（{len(checklist.items)}項目）を提出",
            parameters={
                "type": "OBJECT",
                "properties": {
                    "evaluations": {
                        "type": "OBJECT",
                        "properties": properties,
                        "required": required_items,
                    }
                },
                "required": ["evaluations"],
            },
        )
    
    async def evaluate_paper_content(
        self,
        paper_id: str,
        paper_text_content: str,
        prisma_checklist: Optional[PrismaChecklist],
        prisma_abstract_checklist: Optional[PrismaChecklist],
        evaluation_type: Literal["main", "abstract"],
        model_id: str,
        format_type: str
    ) -> Optional[Tuple[Dict[str, AIEvaluation], ProcessingMetadata]]:
        if evaluation_type == "main" and not prisma_checklist:
            logger.error("main evaluation requires prisma_checklist")
            return None
        if evaluation_type == "abstract" and not prisma_abstract_checklist:
            logger.error("abstract evaluation requires prisma_abstract_checklist")
            return None

        checklist = prisma_checklist if evaluation_type == "main" else prisma_abstract_checklist
        prompt = self.build_prompt(paper_text_content, prisma_checklist, prisma_abstract_checklist, evaluation_type)[0]["content"]
        function_declaration = self._create_function_declaration(checklist, evaluation_type)

        logger.info(f"Starting Gemini Direct evaluation for {paper_id}: {len(checklist.items)}項目")

        for attempt in range(self.retry_count):
            try:
                start_time = time.time()
                response = await self._generate_with_function(prompt, function_declaration)
                processing_time = time.time() - start_time

                evaluations = self._parse_function_response(response, "submit_prisma_evaluation")
                token_usage = self._extract_usage_metadata(response)
                token_count = token_usage.get("total_token_count", 0)

                metadata = ProcessingMetadata(
                    model_id=self.model,
                    model_version=self.model,
                    temperature=self.temperature,
                    max_tokens=None,
                    format_type=format_type,
                    prompt_version="gemini_direct_v2",
                    token_count=token_count,
                    token_usage=token_usage,
                    processing_time=processing_time,
                    timestamp=datetime.now()
                )

                if evaluations:
                    logger.info(
                        f"Gemini Direct evaluation completed: {len(evaluations)}/{len(checklist.items)} items in {processing_time:.2f}s"
                    )
                    return evaluations, metadata

                logger.warning(
                    f"Gemini evaluation returned no items for '{paper_id}' (attempt {attempt + 1}/{self.retry_count})."
                )
                self._log_response_diagnostics(response, f"main_attempt_{attempt + 1}")
                if attempt < self.retry_count - 1:
                    await asyncio.sleep(self.retry_delay)
            except Exception as exc:
                logger.error(
                    f"Gemini Direct API error (attempt {attempt + 1}/{self.retry_count}) for {paper_id}: {exc}",
                    exc_info=True,
                )
                if attempt < self.retry_count - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    logger.error(f"All retry attempts failed for {paper_id}")
                    return None

        return None
