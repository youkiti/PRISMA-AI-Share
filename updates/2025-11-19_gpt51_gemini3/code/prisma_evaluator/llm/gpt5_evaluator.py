import asyncio
import inspect
import json
import time
import logging
from collections.abc import Mapping
from typing import Optional, Dict, Any, Tuple, Literal, List
from datetime import datetime

from openai import OpenAI, APIError, APITimeoutError, RateLimitError
from pydantic import ValidationError, BaseModel

from .base_evaluator import BaseEvaluator
from ..schemas import AIEvaluation, ProcessingMetadata, PrismaChecklist
from ..exceptions import LLMAPIError, EvaluationError, ConfigurationError
from ..resources.gpt5_grammars import get_prisma_tool_definition
from ..resources.prisma_eande_loader import get_item_details_for_schema
from .utils import render_checklist_content

# GPT-5専用のメタデータスキーマ
class GPT5ProcessingMetadata(BaseModel):
    """GPT-5専用の処理メタデータ"""
    model_id: str
    model_version: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    format_type: Optional[str] = None
    prompt_version: Optional[str] = None
    token_count: Optional[int] = 0
    processing_time: Optional[float] = 0.0
    processing_time_seconds: Optional[float] = 0.0  # GPT-5互換
    timestamp: datetime
    model_usage: Optional[Dict[str, Any]] = None  # GPT-5 API usage info
    evaluation_attempt: Optional[int] = None
    evaluation_parameters: Optional[Dict[str, Any]] = None

# GPT-5専用の評価結果スキーマ
class GPT5Evaluation(BaseModel):
    """GPT-5 APIからの評価結果"""
    model_id: str
    evaluation_type: Literal["main", "abstract"]
    response_json: Dict[str, Any]
    processing_metadata: GPT5ProcessingMetadata

logger = logging.getLogger(__name__)

class GPT5Evaluator(BaseEvaluator):
    """
    GPT-5専用のEvaluator（PRISMA評価最適化版）
    
    GPT-5の新機能を活用:
    - Verbosity Parameter: lowデフォルトで簡潔な出力
    - Minimal Reasoning: 高速評価
    - Context-Free Grammar: yes/no出力制約
    - Free-form Function Calling: 直接JSON出力
    """
    
    def __init__(
        self, 
        api_key: str, 
        base_url: Optional[str] = None,
        retry_count: int = 3, 
        retry_delay: int = 5,
        verbosity: Literal["low", "medium", "high"] = "low",  # lowで簡潔な出力
        reasoning_effort: Literal["none", "minimal", "medium", "high"] = "minimal",
        enable_cfg: bool = True,
        enable_freeform: bool = True,
        schema_type: str = "simple",  # "simple" or "detailed"
        checklist_format: str = "md",  # 'md' | 'text' | 'json' | 'xml' | 'none'
        dynamic_schema_file: Optional[str] = None,  # 動的スキーマファイル
        max_completion_tokens: int = 128000,  # GPT-5の最大出力トークン数
        max_retries: int = 3
    ):
        super().__init__(max_retries=max_retries)
        
        if not api_key:
            msg = "OpenAI API key is required for GPT-5 evaluator."
            logger.error(msg)
            raise ConfigurationError(msg)
        
        client_args: Dict[str, Any] = {"api_key": api_key}
        if base_url:
            client_args["base_url"] = base_url
        
        self.client = OpenAI(**client_args)
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.verbosity = verbosity
        self.reasoning_effort = reasoning_effort
        self.enable_cfg = enable_cfg
        self.enable_freeform = enable_freeform
        self.schema_type = schema_type
        clf = (checklist_format or "md").lower()
        self.checklist_format = clf if clf in ("md", "text", "json", "xml", "none") else "md"
        self.dynamic_schema_file = dynamic_schema_file
        self.max_completion_tokens = max_completion_tokens

        # OpenAI Python SDK compatibility: detect whether responses.create accepts response_format
        responses_create_sig = inspect.signature(self.client.responses.create)
        self._supports_response_format = "response_format" in responses_create_sig.parameters
        
        logger.info(
            f"GPT5Evaluator initialized. "
            f"Verbosity: {verbosity}, Reasoning: {reasoning_effort}, "
            f"CFG: {enable_cfg}, Freeform: {enable_freeform}, "
            f"Schema: {schema_type}"
        )

    @staticmethod
    def _normalize_usage(usage: Any) -> Dict[str, int]:
        normalized: Dict[str, int] = {}
        if not usage:
            return normalized

        if isinstance(usage, Mapping):
            getter = usage.get
        else:
            getter = lambda key, default=None: getattr(usage, key, default)

        for key in (
            "input_tokens",
            "prompt_tokens",
            "output_tokens",
            "completion_tokens",
            "total_tokens",
        ):
            value = getter(key, None)
            if isinstance(value, (int, float)):
                normalized[key] = int(value)

        input_details = getter("input_tokens_details", None)
        if input_details:
            if isinstance(input_details, Mapping):
                cached = input_details.get("cached_tokens")
            else:
                cached = getattr(input_details, "cached_tokens", None)
            if isinstance(cached, (int, float)):
                normalized["cached_tokens"] = int(cached)

        for detail_key in ("output_tokens_details", "completion_tokens_details"):
            details = getter(detail_key, None)
            if isinstance(details, Mapping):
                reasoning = details.get("reasoning_tokens")
            else:
                reasoning = getattr(details, "reasoning_tokens", None) if details else None
            if isinstance(reasoning, (int, float)):
                normalized["reasoning_tokens"] = int(reasoning)

        return normalized

    @staticmethod
    def _resolve_total_tokens(token_usage: Dict[str, int]) -> int:
        if "total_tokens" in token_usage:
            return int(token_usage["total_tokens"])

        input_total = None
        for key in ("input_tokens", "prompt_tokens"):
            if key in token_usage:
                input_total = token_usage[key]
                break

        output_total = None
        for key in ("output_tokens", "completion_tokens"):
            if key in token_usage:
                output_total = token_usage[key]
                break

        if input_total is not None and output_total is not None:
            return int(input_total + output_total)

        # If we only have one side, fall back to whichever is available
        if input_total is not None:
            return int(input_total)
        if output_total is not None:
            return int(output_total)

        return 0

    def build_prompt(
        self,
        paper_text_content: str,
        prisma_checklist: Optional[PrismaChecklist],
        prisma_abstract_checklist: Optional[PrismaChecklist],
        evaluation_type: Literal["main", "abstract"]
    ) -> List[Dict[str, str]]:
        """
        GPT-5用のプロンプトを構築（OpenRouter準拠で統一、CFG制約活用）
        """
        system_prompt_template = """
You are an expert reviewer for the PRISMA (Preferred Reporting Items for Systematic Reviews and Meta-Analyses) guideline.
Evaluate the **{evaluation_target_text}** of the provided systematic review against the following {checklist_name_text} items.

Evaluation rules:
1. Decide strictly between "yes" or "no" for each item.
2. Do not use labels such as "partial" or "not applicable."
3. Provide a concise, specific rationale (50 words or fewer) for every decision.
4. Respond "no" whenever the paper does not explicitly report the required information.
5. Avoid speculation or assumptions.

The {checklist_name_text} is listed below:
{checklist_content_for_prompt}

Return the result strictly in the following JSON format:
{example_json_output_text}

Note: Any output other than valid JSON will be rejected. Follow the schema exactly and use the designated tool output.
"""
        active_checklist_obj: Optional[PrismaChecklist] = None
        evaluation_target = ""
        checklist_name = ""
        example_json_output = ""

        if evaluation_type == "main":
            active_checklist_obj = prisma_checklist
            evaluation_target = "full text"
            checklist_name = "PRISMA main checklist"
            example_json_output = """{
  "evaluations": {
    "1": {"result": "yes", "reason": "Title explicitly states the review is systematic"},
    "2": {"result": "yes", "reason": "Structured abstract is provided"},
    "3": {"result": "no", "reason": "Objectives are not clearly described"}
  }
}"""
        elif evaluation_type == "abstract":
            active_checklist_obj = prisma_abstract_checklist
            evaluation_target = "abstract"
            checklist_name = "PRISMA abstract checklist"
            example_json_output = """{
  "evaluations": {
    "item_1": {"result": "yes", "reason": "Title identifies this as a systematic review"},
    "item_2": {"result": "no", "reason": "Background description is insufficient"}
  }
}"""
        else:
            msg = f"Invalid evaluation type for prompt building: {evaluation_type}"
            logger.error(msg)
            raise EvaluationError(msg)

        checklist_for_prompt = ""
        if self.checklist_format != "none":
            if active_checklist_obj and active_checklist_obj.items:
                checklist_name_to_display = active_checklist_obj.name or checklist_name
                items_struct = []
                for item in active_checklist_obj.items:
                    # schema_typeに基づいて詳細情報を追加
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
                        "dynamic-simple-overrides",
                    ]:
                        eande_details = get_item_details_for_schema(
                            item.item_id,
                            self.schema_type,
                            self.dynamic_schema_file,
                        )
                        desc = eande_details.get('description', item.description) if eande_details else item.description
                        title = eande_details.get('name', item.description) if eande_details else item.description
                    else:
                        # simple schema - 基本説明のみ
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
                    checklist_name_to_display,
                    items_struct,
                )
            else:
                logger.warning(f"Checklist data is missing or empty for {evaluation_type} evaluation. Prompt will be incomplete.")
                checklist_for_prompt = f"Error: {checklist_name} data was not found."

        system_prompt = system_prompt_template.format(
            evaluation_target_text=evaluation_target,
            checklist_name_text=checklist_name,
            checklist_content_for_prompt=checklist_for_prompt,
            example_json_output_text=example_json_output
        )

        return [
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": f"Please evaluate the following paper content:\n\n{paper_text_content}"}
        ]

    async def _call_gpt5_api(
        self, 
        messages: List[Dict[str, str]], 
        model_id: str,
        evaluation_type: Literal["main", "abstract"],
        prisma_checklist: Optional[PrismaChecklist] = None,
        prisma_abstract_checklist: Optional[PrismaChecklist] = None
    ) -> Dict[str, Any]:
        """
        GPT-5 APIを呼び出し（新機能活用）
        """
        try:
            # 動的スキーマ生成を使用したJSON Schema定義
            json_schema = self.get_json_schema(evaluation_type, prisma_checklist, prisma_abstract_checklist)

            # GPT-5 Responses APIを使用
            api_params = {
                "model": model_id,
                "input": messages,  # messagesをinputに変更
                "reasoning": {
                    "effort": self.reasoning_effort,  # GPT-5固有パラメータ
                    "summary": "auto"
                },
                "store": False
            }

            if json_schema:
                if self._supports_response_format:
                    # 最新SDK: response_formatパラメータを使用
                    api_params["response_format"] = {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "prisma_evaluation",
                            "schema": json_schema,
                            "strict": True
                        }
                    }
                    api_params["text"] = {
                        "verbosity": self.verbosity
                    }
                else:
                    # 旧SDK: text.format 経由でStructured Outputsを指定
                    api_params["text"] = {
                        "format": {
                            "type": "json_schema",
                            "name": "prisma_evaluation",
                            "schema": json_schema,
                            "strict": True
                        },
                        "verbosity": self.verbosity
                    }
            else:
                api_params["text"] = {
                    "verbosity": self.verbosity
                }
            
            completion = await asyncio.to_thread(
                self.client.responses.create,
                **api_params
            )
            
            # GPT-5 Structured Outputs レスポンスの処理
            logger.debug(f"GPT-5 response structure: {type(completion)}")
            logger.debug(f"GPT-5 response attributes: {dir(completion)}")

            # 共通: usage 抽出
            usage_info: Dict[str, Any] = {}
            usage_obj = getattr(completion, "usage", None)
            if usage_obj:
                for key in ("input_tokens", "output_tokens", "total_tokens"):
                    value = getattr(usage_obj, key, None)
                    if isinstance(value, (int, float)):
                        usage_info[key] = int(value)

                details = getattr(usage_obj, "output_tokens_details", None)
                if details and hasattr(details, "reasoning_tokens"):
                    reasoning_tokens = getattr(details, "reasoning_tokens")
                    if isinstance(reasoning_tokens, (int, float)):
                        usage_info["reasoning_tokens"] = int(reasoning_tokens)

            # Structured Outputsの場合はJSONが直接返される
            if json_schema:
                # 1) 最優先: parsed / output_parsed が dict であればそのまま返す
                parsed = getattr(completion, 'parsed', None)
                if not parsed:
                    parsed = getattr(completion, 'output_parsed', None)
                if isinstance(parsed, dict) and parsed:
                    logger.debug("Using parsed structured output")
                    return {
                        "content": json.dumps(parsed, ensure_ascii=False),
                        "parsed": parsed,
                        "usage": usage_info,
                        "finish_reason": "structured_output"
                    }

                # 2) 次善: output_text があればテキストを利用
                output_text = getattr(completion, 'output_text', None)
                if isinstance(output_text, str) and output_text.strip():
                    logger.debug("Using completion.output_text for structured output")
                    return {
                        "content": output_text,
                        "usage": usage_info,
                        "finish_reason": "structured_output"
                    }

                # 3) output配列を解析（最新Responses APIフォーマット）
                json_content = None
                try:
                    completion_dict = completion.model_dump()  # type: ignore[attr-defined]
                except Exception:
                    completion_dict = None

                if completion_dict:
                    output_list = completion_dict.get("output") or []
                    collected: List[str] = []
                    for item in output_list:
                        if not isinstance(item, dict):
                            continue
                        parts = item.get("content") or []
                        if not isinstance(parts, list):
                            continue
                        for part in parts:
                            if isinstance(part, dict):
                                text_val = part.get("text")
                                if isinstance(text_val, str) and text_val.strip():
                                    collected.append(text_val.strip())
                    if collected:
                        json_content = "\n".join(collected)

                if json_content is None:
                    logger.debug("Structured Output fallback: using stringified completion.output")
                    raw_output = getattr(completion, "output", "")
                    if isinstance(raw_output, list):
                        json_content = json.dumps(raw_output, ensure_ascii=False)
                    else:
                        json_content = str(raw_output)

                logger.debug(f"Structured Output (fallback path), length: {len(str(json_content))}")
                return {
                    "content": str(json_content),
                    "usage": usage_info,
                    "finish_reason": "structured_output"
                }
            else:
                # プレーンテキスト応答
                if hasattr(completion, 'output') and hasattr(completion.output, 'content'):
                    content_item = completion.output.content[0]
                    content = getattr(content_item, 'text', str(content_item))
                else:
                    content = getattr(completion, 'output', '') or getattr(completion, 'text', '')
                
                return {
                    "content": str(content),
                    "usage": usage_info,
                    "finish_reason": getattr(completion, 'finish_reason', 'stop')
                }
                
        except Exception as e:
            logger.error(f"GPT-5 API call failed: {e}")
            raise LLMAPIError(f"GPT-5 API error: {str(e)}")

    def _extract_json_from_response(self, content: str) -> Optional[Dict[str, Any]]:
        """
        GPT-5応答からJSONを抽出（空JSON検出時の処理追加）
        """
        content = content.strip()
        
        # 空JSONの検出
        if content == "{}" or content == "":
            logger.warning("Empty JSON detected in GPT-5 response, likely due to output token limit")
            return None
        
        # CFG制約により既にJSONの場合
        if content.startswith("{") and content.endswith("}"):
            try:
                parsed = json.loads(content)
                # 空のJSONオブジェクトをチェック
                if not parsed or (isinstance(parsed, dict) and len(parsed) == 0):
                    logger.warning("Parsed JSON is empty, likely incomplete response")
                    return None
                return parsed
            except json.JSONDecodeError:
                pass
        
        # フォールバック: 従来の抽出方法
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            if end != -1:
                json_str = content[start:end].strip()
            else:
                json_str = content[start:].strip()
        elif "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            if end != -1:
                json_str = content[start:end].strip()
            else:
                json_str = content[start:].strip()
        else:
            start = content.find("{")
            if start != -1:
                brace_count = 0
                end = start
                for i, char in enumerate(content[start:], start):
                    if char == "{":
                        brace_count += 1
                    elif char == "}":
                        brace_count -= 1
                        if brace_count == 0:
                            end = i + 1
                            break
                json_str = content[start:end]
            else:
                return None

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON: {e}")
            return None

    async def evaluate_paper(
        self,
        paper_id: str,
        paper_text_content: str,
        prisma_checklist: Optional[PrismaChecklist],
        prisma_abstract_checklist: Optional[PrismaChecklist],
        evaluation_type: Literal["main", "abstract"],
        model_id: str
    ) -> GPT5Evaluation:
        """
        GPT-5を使用してPRISMA評価を実行
        """
        logger.info(f"Starting GPT-5 evaluation for paper '{paper_id}', type '{evaluation_type}', model '{model_id}'.")
        
        # プロンプト構築
        messages = self.build_prompt(
            paper_text_content, 
            prisma_checklist, 
            prisma_abstract_checklist, 
            evaluation_type
        )

        # リトライ機構付きAPI呼び出し
        for attempt in range(1, self.retry_count + 1):
            try:
                start_time = time.time()
                api_response = await self._call_gpt5_api(
                    messages, model_id, evaluation_type, 
                    prisma_checklist, prisma_abstract_checklist
                )
                elapsed_time = time.time() - start_time

                usage_normalized = self._normalize_usage(api_response.get("usage"))
                total_tokens = self._resolve_total_tokens(usage_normalized)

                logger.debug(
                    f"GPT-5 API success for '{paper_id}', type '{evaluation_type}'. "
                    f"Finish: {api_response.get('finish_reason')}, "
                    f"Tokens: {total_tokens or usage_normalized.get('output_tokens', 'unknown')}, "
                    f"Attempt: {attempt}, Time: {elapsed_time:.2f}s"
                )

                # JSON解析（output_parsed があれば最優先で使用）
                parsed_direct = api_response.get("parsed")
                if isinstance(parsed_direct, dict) and parsed_direct:
                    json_data = parsed_direct
                    logger.debug("Parsed JSON obtained from API (output_parsed)")
                else:
                    response_content = api_response.get("content", "")
                    json_data = self._extract_json_from_response(response_content)

                if not json_data:
                    # 空JSONの場合、特別なログを出力してリトライ
                    if response_content == "{}" or response_content == "":
                        logger.warning(
                            f"Empty JSON detected for '{paper_id}', type '{evaluation_type}'. "
                            f"Output tokens used: {api_response.get('usage', {}).get('output_tokens', 'unknown')}. "
                            f"This suggests the output was truncated. Attempt: {attempt}/{self.retry_count}"
                        )
                        if attempt < self.retry_count:
                            logger.info(f"Retrying with same max_completion_tokens (128000)...")
                            await asyncio.sleep(self.retry_delay)
                            continue  # 次の試行へ
                    raise EvaluationError(f"Could not parse JSON from GPT-5 response: {response_content}")

                logger.info(
                    f"Successfully parsed GPT-5 response for '{paper_id}', type '{evaluation_type}'. "
                    f"Items: {len(json_data)}"
                )

                # GPT5Evaluation構築
                return GPT5Evaluation(
                    model_id=model_id,
                    evaluation_type=evaluation_type,
                    response_json=json_data,
                    processing_metadata=GPT5ProcessingMetadata(
                        model_id=model_id,
                        model_version=model_id,
                        temperature=None,  # GPT-5はtemperatureをサポートしない
                        max_tokens=self.max_completion_tokens,  # 実際のパラメータ値を使用
                        format_type="gpt5_optimized",
                        prompt_version="gpt5_v1",
                        token_count=total_tokens,
                        processing_time=elapsed_time,
                        processing_time_seconds=elapsed_time,  # 互換性
                        timestamp=datetime.now(),
                        model_usage=usage_normalized,
                        evaluation_attempt=attempt,
                        evaluation_parameters={
                            "verbosity": self.verbosity,
                            "reasoning_effort": self.reasoning_effort,
                            "cfg_enabled": self.enable_cfg,
                            "freeform_enabled": self.enable_freeform,
                            "max_completion_tokens": self.max_completion_tokens
                        }
                    )
                )

            except (APIError, APITimeoutError, RateLimitError) as api_error:
                logger.warning(
                    f"GPT-5 API error on attempt {attempt}/{self.retry_count} for '{paper_id}': {api_error}"
                )
                if attempt < self.retry_count:
                    await asyncio.sleep(self.retry_delay)
                else:
                    raise LLMAPIError(f"GPT-5 API failed after {self.retry_count} attempts: {str(api_error)}")
            
            except (ValidationError, EvaluationError) as eval_error:
                logger.error(f"GPT-5 evaluation error for '{paper_id}': {eval_error}")
                raise eval_error
            
            except Exception as unexpected_error:
                logger.error(f"Unexpected GPT-5 error for '{paper_id}': {unexpected_error}", exc_info=True)
                if attempt < self.retry_count:
                    await asyncio.sleep(self.retry_delay)
                else:
                    raise EvaluationError(f"GPT-5 evaluation failed: {str(unexpected_error)}")

        raise EvaluationError(f"GPT-5 evaluation failed after all retry attempts for paper '{paper_id}'")

    def get_tool_schema(
        self,
        evaluation_type: Literal["main", "abstract"],
        prisma_checklist: Optional[PrismaChecklist] = None,
        prisma_abstract_checklist: Optional[PrismaChecklist] = None
    ) -> List[Dict[str, Any]]:
        """
        BaseEvaluator抽象メソッドの実装（GPT-5では使用しない）
        """
        return []

    def get_json_schema(
        self,
        evaluation_type: Literal["main", "abstract"],
        prisma_checklist: Optional[PrismaChecklist] = None,
        prisma_abstract_checklist: Optional[PrismaChecklist] = None
    ) -> Optional[Dict[str, Any]]:
        """
        GPT-5用のJSON Schemaを返す（動的チェックリストベース）
        schema_typeに応じてシンプル版または詳細版を生成
        """
        if not (self.enable_cfg and self.enable_freeform):
            return None
        
        if self.schema_type == "detailed":
            return self._get_detailed_json_schema(evaluation_type, prisma_checklist, prisma_abstract_checklist)
        else:
            return self._get_simple_json_schema(evaluation_type, prisma_checklist, prisma_abstract_checklist)
    
    def _get_simple_json_schema(
        self,
        evaluation_type: Literal["main", "abstract"],
        prisma_checklist: Optional[PrismaChecklist] = None,
        prisma_abstract_checklist: Optional[PrismaChecklist] = None
    ) -> Dict[str, Any]:
        """シンプルなJSON Schema生成（Structured Outputs用）"""
        
        properties: Dict[str, Any]
        required_outer: List[str] = ["evaluations"]

        if evaluation_type == "main":
            item_props: Dict[str, Any] = {}
            required_inner: List[str] = []
            
            # 実際のチェックリスト項目を使用
            if prisma_checklist and prisma_checklist.items:
                for item in prisma_checklist.items:
                    # Main評価のitem_idをそのまま使用（"1", "2", "3a"など）
                    item_key = str(item.item_id)
                    item_props[item_key] = {
                        "type": "object",
                        "properties": {
                            "result": {"type": "string", "enum": ["yes", "no"]},
                            "reason": {"type": "string"}
                        },
                        "required": ["result", "reason"],
                        "additionalProperties": False
                    }
                    required_inner.append(item_key)
            else:
                # フォールバック: additionalPropertiesを使用
                properties = {
                    "evaluations": {
                        "type": "object",
                        "description": "Evaluation for each item in the PRISMA main checklist.",
                        "additionalProperties": {
                            "type": "object",
                            "properties": {
                                "result": {"type": "string", "enum": ["yes", "no"]},
                                "reason": {"type": "string"}
                            },
                            "required": ["result", "reason"],
                            "additionalProperties": False
                        }
                    }
                }
            
            # チェックリスト項目がある場合は具体的なスキーマを設定
            if prisma_checklist and prisma_checklist.items:
                properties = {"evaluations": {"type": "object", "properties": item_props, "required": required_inner, "additionalProperties": False}}
        elif evaluation_type == "abstract":
            item_props: Dict[str, Any] = {}
            required_inner: List[str] = []
            
            # 実際のチェックリスト項目を使用、なければフォールバック
            if prisma_abstract_checklist and prisma_abstract_checklist.items:
                for item in prisma_abstract_checklist.items:
                    item_key = f"item_{item.item_id}"
                    item_props[item_key] = {
                        "type": "object",
                        "properties": {
                            "result": {"type": "string", "enum": ["yes", "no"]},
                            "reason": {"type": "string"}
                        },
                        "required": ["result", "reason"],
                        "additionalProperties": False
                    }
                    required_inner.append(item_key)
            else:
                logger.warning("No abstract checklist provided, using fallback range 1-12")
                for i in range(1, 13):
                    item_key = f"item_{i}"
                    item_props[item_key] = {
                        "type": "object",
                        "properties": {
                            "result": {"type": "string", "enum": ["yes", "no"]},
                            "reason": {"type": "string"}
                        },
                        "required": ["result", "reason"],
                        "additionalProperties": False
                    }
                    required_inner.append(item_key)
            
            properties = {"evaluations": {"type": "object", "properties": item_props, "required": required_inner, "additionalProperties": False}}
        else:
            msg = f"Invalid evaluation type for JSON schema: {evaluation_type}"
            logger.error(msg)
            raise EvaluationError(msg)

        return {
            "type": "object",
            "properties": properties,
            "required": required_outer,
            "additionalProperties": False
        }
    
    def _get_detailed_json_schema(
        self,
        evaluation_type: Literal["main", "abstract"],
        prisma_checklist: Optional[PrismaChecklist] = None,
        prisma_abstract_checklist: Optional[PrismaChecklist] = None
    ) -> Dict[str, Any]:
        """詳細なJSON Schema生成（PRISMA-EandE情報を含む）"""
        
        properties: Dict[str, Any]
        required_outer: List[str] = ["evaluations"]

        if evaluation_type == "main":
            item_props: Dict[str, Any] = {}
            required_inner: List[str] = []
            
            # 実際のチェックリスト項目を使用してPRISMA-EandE詳細を追加
            if prisma_checklist and prisma_checklist.items:
                for item in prisma_checklist.items:
                    item_key = str(item.item_id)
                    
                    # PRISMA-EandEから詳細情報を取得
                    eande_details = get_item_details_for_schema(
                        item.item_id, 
                        self.schema_type, 
                        self.dynamic_schema_file
                    )
                    
                    # 基本スキーマ
                    item_schema = {
                        "type": "object",
                        "title": f"PRISMA Item {item.item_id}: {item.description[:50]}...",
                        "properties": {
                            "result": {"type": "string", "enum": ["yes", "no"]},
                            "reason": {"type": "string", "description": "評価の具体的理由（50字以内）"}
                        },
                        "required": ["result", "reason"],
                        "additionalProperties": False
                    }
                    
                    # PRISMA-EandE詳細情報を追加
                    if eande_details:
                        item_schema["description"] = f"""
{eande_details.get('title', f'PRISMA Item {item.item_id}')}

【評価基準】
{eande_details.get('description', 'No detailed description available')}

【受け入れ条件】
{eande_details.get('accept_criteria', 'No specific accept criteria')}

【拒否条件】
{eande_details.get('reject_criteria', 'No specific reject criteria')}

【確認ポイント】
{eande_details.get('evidence_hints', 'No specific evidence hints')}
"""
                    else:
                        item_schema["description"] = f"PRISMA Item {item.item_id}: {item.description}"
                    
                    item_props[item_key] = item_schema
                    required_inner.append(item_key)
            else:
                # フォールバック: シンプル版を使用
                logger.warning("No main checklist provided for detailed schema, falling back to simple schema")
                return self._get_simple_json_schema(evaluation_type, prisma_checklist, prisma_abstract_checklist)
            
            properties = {"evaluations": {"type": "object", "properties": item_props, "required": required_inner, "additionalProperties": False}}
            
        elif evaluation_type == "abstract":
            item_props: Dict[str, Any] = {}
            required_inner: List[str] = []
            
            # Abstract評価用の詳細スキーマ
            if prisma_abstract_checklist and prisma_abstract_checklist.items:
                for item in prisma_abstract_checklist.items:
                    item_key = f"item_{item.item_id}"
                    
                    # 基本スキーマ（Abstract用）
                    item_schema = {
                        "type": "object",
                        "title": f"PRISMA Abstract Item {item.item_id}: {item.description[:50]}...",
                        "description": f"PRISMA Abstract Item {item.item_id}: {item.description}",
                        "properties": {
                            "result": {"type": "string", "enum": ["yes", "no"]},
                            "reason": {"type": "string", "description": "評価の具体的理由（50字以内）"}
                        },
                        "required": ["result", "reason"],
                        "additionalProperties": False
                    }
                    
                    item_props[item_key] = item_schema
                    required_inner.append(item_key)
            else:
                logger.warning("No abstract checklist provided for detailed schema, falling back to simple schema")
                return self._get_simple_json_schema(evaluation_type, prisma_checklist, prisma_abstract_checklist)
            
            properties = {"evaluations": {"type": "object", "properties": item_props, "required": required_inner, "additionalProperties": False}}
        else:
            msg = f"Invalid evaluation type for tool schema: {evaluation_type}"
            logger.error(msg)
            raise EvaluationError(msg)

        return {
            "type": "object",
            "properties": properties,
            "required": required_outer,
            "additionalProperties": False
        }

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
        """
        BaseEvaluator互換のevaluate_paper_contentメソッド
        """
        try:
            # GPT-5固有のevaluate_paperメソッドを呼び出し
            ai_evaluation = await self.evaluate_paper(
                paper_id, paper_text_content, prisma_checklist, 
                prisma_abstract_checklist, evaluation_type, model_id
            )
            
            # 結果をBaseEvaluator形式に変換
            evaluations_dict = {}
            if ai_evaluation.response_json and "evaluations" in ai_evaluation.response_json:
                evaluations_data = ai_evaluation.response_json["evaluations"]
                for item_id, item_data in evaluations_data.items():
                    if isinstance(item_data, dict) and "result" in item_data and "reason" in item_data:
                        evaluations_dict[item_id] = AIEvaluation(
                            result=item_data["result"],
                            reason=item_data["reason"],
                            raw_response=""
                        )
                    else:
                        logger.warning(f"Skipping malformed item '{item_id}' in GPT-5 response for '{paper_id}': {item_data}")
            else:
                logger.warning(f"No 'evaluations' field found in GPT-5 response for '{paper_id}': {ai_evaluation.response_json}")
            
            usage_dict = self._normalize_usage(getattr(ai_evaluation.processing_metadata, "model_usage", {}))
            resolved_token_count = self._resolve_total_tokens(usage_dict)
            if not resolved_token_count:
                resolved_token_count = getattr(ai_evaluation.processing_metadata, "token_count", 0) or 0

            # ProcessingMetadataを更新（BaseEvaluator互換形式）
            metadata = ProcessingMetadata(
                model_id=ai_evaluation.model_id,
                model_version=ai_evaluation.model_id,
                temperature=None,  # GPT-5はtemperatureをサポートしない
                max_tokens=self.max_completion_tokens,  # 実際のパラメータ値を使用
                format_type=format_type,
                prompt_version="gpt5_v1",
                token_count=resolved_token_count,
                token_usage=usage_dict,
                processing_time=getattr(ai_evaluation.processing_metadata, 'processing_time', 0.0),
                timestamp=ai_evaluation.processing_metadata.timestamp
            )

            return evaluations_dict, metadata
            
        except Exception as e:
            logger.error(f"GPT-5 evaluate_paper_content failed for '{paper_id}': {e}")
            return None

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
        失敗した項目のみを再評価するGPT-5実装
        """
        start_time = time.time()
        self.logger.info(f"GPT-5: Evaluating {len(failed_item_ids)} failed items for {paper_id} ({evaluation_type})")
        
        try:
            # 失敗項目のみの動的JSON Schemaを生成
            partial_schema = self._create_partial_json_schema(evaluation_type, failed_item_ids)
            
            # プロンプト構築
            prompt = self._build_partial_prompt(
                paper_text_content, 
                prisma_checklist, 
                prisma_abstract_checklist, 
                evaluation_type,
                failed_item_ids
            )
            
            # GPT-5 Structured Outputs API呼び出し
            response = self.client.responses.create(
                text={
                    "format": {
                        "name": f"prisma_partial_{evaluation_type}_evaluation",
                        "schema": partial_schema
                    },
                    "prompt": prompt,
                    "max_completion_tokens": self.max_completion_tokens
                },
                verbosity=self.verbosity,
                reasoning_effort=self.reasoning_effort
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # レスポンス処理
            response_data = json.loads(response.text)
            evaluations = self._parse_gpt5_partial_response(response_data, evaluation_type, failed_item_ids)

            # メタデータ作成
            usage_dict = self._normalize_usage(getattr(response, "usage", None))
            token_count = self._resolve_total_tokens(usage_dict)
            if not token_count:
                token_count = len(prompt.split()) * 2  # フォールバック（推定）
            metadata = ProcessingMetadata(
                model_id=model_id,
                model_version="gpt-5",
                max_tokens=self.max_completion_tokens,
                format_type=format_type,
                prompt_version="gpt5_partial_retry_v1",
                token_count=token_count,
                token_usage=usage_dict,
                processing_time=processing_time,
                timestamp=datetime.now()
            )
            
            self.logger.info(f"GPT-5 partial retry success: {len(evaluations)} items evaluated in {processing_time:.2f}s")
            return evaluations, metadata
            
        except Exception as e:
            self.logger.error(f"GPT-5 partial evaluation failed: {e}")
            return None

    def _create_partial_json_schema(self, evaluation_type: Literal["main", "abstract"], failed_item_ids: List[str]) -> Dict[str, Any]:
        """失敗項目のみのJSON Schemaを生成"""
        
        properties = {}
        required = []
        
        for item_id in failed_item_ids:
            properties[item_id] = {
                "type": "object",
                "properties": {
                    "result": {
                        "type": "string",
                        "enum": ["yes", "no"],
                        "description": "Evaluation results for PRISMA items"
                    },
                    "reason": {
                        "type": "string",
                        "description": "評価の理由"
                    }
                },
                "required": ["result", "reason"],
                "additionalProperties": False
            }
            required.append(item_id)
        
        schema = {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False
        }
        
        return schema

    def _build_partial_prompt(
        self, 
        paper_text_content: str,
        prisma_checklist: Optional[PrismaChecklist],
        prisma_abstract_checklist: Optional[PrismaChecklist],
        evaluation_type: Literal["main", "abstract"],
        failed_item_ids: List[str]
    ) -> str:
        """失敗項目のみのプロンプトを構築"""
        
        target_checklist = prisma_abstract_checklist if evaluation_type == "abstract" else prisma_checklist
        evaluation_target = "抄録" if evaluation_type == "abstract" else "本文"
        
        # 失敗項目のみのチェックリスト作成
        failed_items_text = ""
        if target_checklist:
            for item in target_checklist.items:
                item_key = f"item_{item.item_id}" if evaluation_type == "abstract" else str(item.item_id)
                if item_key in failed_item_ids:
                    item_title = getattr(item, "title", None) or item.description
                    failed_items_text += f"\n{item_key}. {item_title}: {item.description}"
        
        prompt = f"""以下のシステマティックレビュー論文の{evaluation_target}を、失敗したPRISMAガイドライン項目について再評価してください。

【評価対象の{evaluation_target}】
{paper_text_content}

【再評価が必要なPRISMA項目】
{failed_items_text}

【評価指示】
- 各項目について、{evaluation_target}にその要素が記載されているかを「yes」または「no」で厳密に判定
- 判定理由を簡潔に記載
- 曖昧な場合は「no」と判定
- JSON形式で構造化された結果を返してください"""
        
        return prompt

    def _parse_gpt5_partial_response(self, response_data: Dict[str, Any], evaluation_type: str, failed_item_ids: List[str]) -> Dict[str, AIEvaluation]:
        """GPT-5の部分評価レスポンスをパース"""
        
        evaluations = {}
        
        for item_id in failed_item_ids:
            if item_id in response_data:
                item_data = response_data[item_id]
                result = item_data.get("result")
                reason = item_data.get("reason", "")
                
                if result in ["yes", "no"]:
                    evaluations[item_id] = AIEvaluation(result=result, reason=reason)
                else:
                    self.logger.warning(f"Invalid result for {item_id}: {result}")
                    evaluations[item_id] = AIEvaluation(result=None, reason="Invalid response format")
        
        return evaluations
