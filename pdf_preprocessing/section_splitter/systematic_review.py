import re
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple


@dataclass
class SectionSplitResult:
    sections: Dict[str, str]
    subsections: Dict[str, str]
    evaluation_sets: Dict[str, str]
    metadata: Dict[str, Any]
    prisma_coverage_hints: Dict[str, str]


class SystematicReviewSectionSplitter:
    """システマティックレビュー論文専用のセクション分割（軽量版）"""

    def __init__(self) -> None:
        # Abstract抽出の最大長（文字数）
        self.max_abstract_length = 4000
        common_prefix = r"^\s*(\d+\.?\s*)?"
        # 見出しの後ろにサブ見出しや説明語が同一行で続くケースを許容
        # 例: "MATERIALS AND METHODS Study Design"
        common_suffix = r"(?:\s*[:\-–—]\s*)?.*$"

        self.sr_section_patterns: Dict[str, Dict[str, Any]] = {
            "abstract": {
                "patterns": [
                    common_prefix + r"(abstract|structured\s+abstract|summary)" + common_suffix,
                ],
                "subsections": ["background", "objectives", "methods", "results", "conclusions"],
                "prisma_items": ["1", "2"],
            },
            "introduction": {
                "patterns": [
                    # 背景(Background:)は構造化抄録用の小見出しと衝突するためコロン付きは除外
                    common_prefix + r"(introduction|background(?!\s*:)|rationale)" + common_suffix,
                ],
                "keywords": ["rationale", "objectives", "research question", "PICO"],
                "prisma_items": ["3", "4"],
            },
            "methods": {
                "patterns": [
                    common_prefix + r"(methods?|materials\s+and\s+methods?|patients\s+and\s+methods?|methodology|methods?\s+and\s+analysis)" + common_suffix,
                ],
                "subsections": [
                    "eligibility_criteria",
                    "information_sources",
                    "search_strategy",
                    "selection_process",
                    "data_collection",
                    "data_items",
                    "risk_of_bias",
                    "synthesis_methods",
                ],
                "prisma_items": ["5", "6", "7", "8", "9", "10a", "10b", "11", "12", "13a-f", "14", "15"],
            },
            "results": {
                "patterns": [
                    common_prefix + r"(results?|findings?)" + common_suffix,
                ],
                "subsections": [
                    "study_selection",
                    "study_characteristics",
                    "risk_of_bias_results",
                    "individual_results",
                    "synthesis_results",
                    "reporting_bias",
                    "certainty_evidence",
                ],
                "prisma_items": ["16a-b", "17", "18", "19", "20a-d", "21", "22"],
                "expected_elements": ["flow_diagram", "forest_plot", "table"],
            },
            "discussion": {
                "patterns": [
                    common_prefix + r"(discussion|discussion\s+and\s+conclusion|conclusion|conclusions)" + common_suffix,
                ],
                "subsections": ["summary_evidence", "limitations", "implications"],
                "prisma_items": ["23a", "23b", "23c"],
            },
            "other_information": {
                "patterns": [
                    common_prefix + r"(other\s+information|acknowledg(e)?ments?|funding|conflicts?\s+of\s+interest|competing\s+interests?|registration|protocol)" + common_suffix,
                ],
                "subsections": ["registration", "protocol", "funding", "conflicts_of_interest"],
                "prisma_items": ["24a-c", "25", "26"],
            },
        }

        self.figure_caption_pattern = re.compile(r"^(figure|fig\.)\s*\d+\s*[:\.]\s*(.+)$", re.IGNORECASE | re.MULTILINE)
        self.forest_plot_kw = re.compile(r"forest\s+plot", re.IGNORECASE)
        self.flow_kw = re.compile(r"prisma\s+flow|flow\s+(diagram|chart)", re.IGNORECASE)

    def split_paper(self, text: str) -> SectionSplitResult:
        full_text = self._normalize_text(text)
        main_sections = self._detect_main_sections(full_text)
        # Abstract補完: ラベルがあれば Abstract〜(本編)Introduction/Background直前で抽出
        abs_span = self._extract_abstract_by_labels(full_text)
        if abs_span:
            candidate_abs = full_text[abs_span[0]:abs_span[1]].strip()
            existing_abs = main_sections.get("abstract", "")
            # 既存より長ければ置き換え（構造化抄録ラベルを優先）
            if len(candidate_abs) > len(existing_abs):
                main_sections["abstract"] = candidate_abs
        elif "abstract" not in main_sections:
            # ラベルが見つからない場合のみフォールバック: 先頭〜(本編)Introduction直前
            intro_pos = self._first_intro_heading(full_text)
            if intro_pos is not None and intro_pos > 0:
                fallback_abs = full_text[:intro_pos].strip()
                if fallback_abs:
                    main_sections["abstract"] = fallback_abs

        # Abstractをラベルで抽出できた場合、誤ってAbstract領域を巻き込んだother_informationを除去
        if abs_span and "other_information" in main_sections:
            oi = main_sections.get("other_information", "")
            if isinstance(oi, str) and "abstract" in oi.lower():
                # 前付けの Funding information などがAbstract付近を誤検出していると判断
                del main_sections["other_information"]
        methods_subsections = self._extract_methods_subsections(main_sections.get("methods", ""), full_text)
        results_subsections = self._extract_results_subsections(main_sections.get("results", ""), full_text)
        sr_metadata = self._detect_sr_elements(full_text)
        return self._structure_for_two_phase_evaluation(
            main_sections,
            {**methods_subsections, **results_subsections},
            full_text,
            sr_metadata,
        )

    # --- helpers ---
    def _normalize_text(self, text: str) -> str:
        return re.sub(r"\r\n?|\u00A0", "\n", text)

    def _detect_main_sections(self, text: str) -> Dict[str, str]:
        # 章の開始インデックスを見出しで収集し、範囲で切り出し
        indices: List[Tuple[int, str]] = []
        for name, conf in self.sr_section_patterns.items():
            for pat in conf.get("patterns", []):
                for m in re.finditer(pat, text, re.IGNORECASE | re.MULTILINE):
                    # 見出し行の先頭位置を記録
                    indices.append((m.start(), name))
        if not indices:
            return {}
        indices = sorted(indices, key=lambda x: x[0])
        # 近接する同一セクションの重複を粗く除去
        dedup: List[Tuple[int, str]] = []
        last_name = None
        for pos, name in indices:
            if name == last_name:
                continue
            dedup.append((pos, name))
            last_name = name

        dedup.append((len(text), "__END__"))
        sections: Dict[str, str] = {}
        for i in range(len(dedup) - 1):
            start_pos, name = dedup[i]
            end_pos, _ = dedup[i + 1]
            chunk = text[start_pos:end_pos].strip()
            # 見出し行を取り除く（先頭行）
            chunk = re.sub(r"^.*$\n?", "", chunk, count=1)
            if name not in sections or len(chunk) > len(sections[name]):
                sections[name] = chunk.strip()
        return sections

    def _first_section_start(self, name: str, text: str) -> int | None:
        conf = self.sr_section_patterns.get(name)
        if not conf:
            return None
        first = None
        for pat in conf.get("patterns", []):
            m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
            if m:
                pos = m.start()
                if first is None or pos < first:
                    first = pos
        return first

    def _first_intro_heading(self, text: str) -> int | None:
        """本編のIntroduction/Background見出し開始位置（構造化抄録の Background: は除外）。"""
        patterns = [
            r"(?m)^\s*(\d+\.?\s*)?introduction\s*(?!:)\s*$",
            r"(?m)^\s*(\d+\.?\s*)?background\s*(?!:)\s*$",
        ]
        pos = None
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                p = m.start()
                if pos is None or p < pos:
                    pos = p
        return pos

    def _extract_abstract_by_labels(self, text: str) -> Tuple[int, int] | None:
        """“Abstract”系ラベルからAbstract本文を抽出（終端は本編Intro/Background見出し）。"""
        # 開始: Abstract/Structured abstract/Abstract Background
        start_patterns = [
            r"abstract\s+background",  # e.g., "Abstract Background:"
            r"structured\s+abstract",
            r"abstract",
        ]
        start = None
        tl = text.lower()
        for sp in start_patterns:
            m = re.search(sp, tl, re.IGNORECASE)
            if m:
                start = m.start()
                break
        if start is None:
            return None
        end = self._first_intro_heading(text)
        if end is None or end <= start:
            end = len(text)
        # 上限キャップ
        end = min(end, start + self.max_abstract_length)
        return (start, end)

    def _find_subsection(self, text: str, patterns: List[str], keywords: List[str]) -> str:
        window = ""
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                # 見つかった箇所の前後をウィンドウ抽出
                start = max(0, m.start() - 1000)
                end = min(len(text), m.end() + 3000)
                window = text[start:end]
                break
        if not window:
            return ""
        # キーワードで拡張
        score = sum(1 for k in keywords if re.search(re.escape(k), window, re.IGNORECASE))
        return window if score >= 1 else ""

    def _extract_methods_subsections(self, methods_text: str, full_text: str) -> Dict[str, str]:
        subsections: Dict[str, str] = {}
        if not methods_text:
            return subsections
        # 検索戦略
        s = self._find_subsection(
            methods_text,
            patterns=[r"search\s+strategy", r"literature\s+search", r"database\s+search"],
            keywords=["AND", "OR", "MeSH", "Boolean"],
        )
        if s:
            subsections["search_strategy"] = s
        # 適格基準
        s = self._find_subsection(
            methods_text,
            patterns=[r"eligibility\s+criteria", r"inclusion.*criteria", r"selection\s+criteria"],
            keywords=["included", "excluded", "PICO"],
        )
        if s:
            subsections["eligibility_criteria"] = s
        # リスクオブバイアス
        s = self._find_subsection(
            methods_text,
            patterns=[r"risk\s+of\s+bias", r"quality\s+assessment", r"bias\s+assessment"],
            keywords=["Cochrane", "GRADE", "blinding", "random"],
        )
        if s:
            subsections["risk_of_bias"] = s
        # 統合方法
        s = self._find_subsection(
            methods_text,
            patterns=[r"synthesis\s+methods?", r"data\s+synthesis", r"meta-analysis"],
            keywords=["pooled", "random effects", "fixed effects", "heterogeneity"],
        )
        if s:
            subsections["synthesis_methods"] = s
        return subsections

    def _extract_results_subsections(self, results_text: str, full_text: str) -> Dict[str, str]:
        subs: Dict[str, str] = {}
        if not results_text:
            return subs
        # 簡易: フローやフォレストの近傍を提示
        flow_hit = self.flow_kw.search(results_text)
        if flow_hit:
            start = max(0, flow_hit.start() - 800)
            end = min(len(results_text), flow_hit.end() + 1200)
            subs["study_selection"] = results_text[start:end]
        forest_hit = self.forest_plot_kw.search(results_text)
        if forest_hit:
            start = max(0, forest_hit.start() - 800)
            end = min(len(results_text), forest_hit.end() + 1200)
            subs["synthesis_results"] = results_text[start:end]
        return subs

    def _detect_sr_elements(self, text: str) -> Dict[str, Any]:
        md: Dict[str, Any] = {}
        # captions
        captions = [m.group(0) for m in self.figure_caption_pattern.finditer(text)]
        md["has_flow_diagram"] = bool(self.flow_kw.search("\n".join(captions)) or self.flow_kw.search(text))
        md["has_forest_plot"] = bool(self.forest_plot_kw.search("\n".join(captions)) or self.forest_plot_kw.search(text))
        # databases
        db_list = [
            "PubMed", "MEDLINE", "Ovid MEDLINE", "Cochrane", "CENTRAL", "Embase", "Web of Science",
            "Scopus", "CINAHL", "PsycINFO", "ClinicalTrials.gov", "ICTRP", "IEEE Xplore",
        ]
        detected: List[str] = []
        tl = text.lower()
        for db in db_list:
            if db.lower() in tl:
                detected.append(db)
        md["detected_databases"] = sorted(set(detected))
        md["has_meta_analysis"] = bool(re.search(r"meta[-\s]?analysis|pooled\s+(estimate|effect)", text, re.IGNORECASE))
        return md

    def _structure_for_two_phase_evaluation(
        self,
        main_sections: Dict[str, str],
        subsections: Dict[str, str],
        full_text: str,
        metadata: Dict[str, Any],
    ) -> SectionSplitResult:
        sections_only = "\n\n".join(
            [f"=== {name.upper()} ===\n{content}" for name, content in main_sections.items() if content]
        )
        if subsections:
            subsections_text = "\n\n".join(
                [f"--- {name.replace('_', ' ').title()} ---\n{content}" for name, content in subsections.items() if content]
            )
            sections_only += f"\n\n=== DETAILED SUBSECTIONS ===\n{subsections_text}"
        return SectionSplitResult(
            sections=main_sections,
            subsections=subsections,
            evaluation_sets={"partial": sections_only, "full": full_text},
            metadata=metadata,
            prisma_coverage_hints=self._generate_prisma_hints(main_sections, subsections),
        )

    def _generate_prisma_hints(self, sections: Dict[str, str], subsections: Dict[str, str]) -> Dict[str, str]:
        hints: Dict[str, str] = {}
        if "search_strategy" in subsections:
            hints["7"] = "Found in Methods > Search Strategy"
        if "eligibility_criteria" in subsections:
            hints["5"] = "Found in Methods > Eligibility Criteria"
        if "results" in sections:
            hints["16a"] = "Look for flow diagram in Results"
            hints["20a"] = "Look for synthesis results in Results"
        return hints
