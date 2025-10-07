# Format-driven Large Language Model Assessment for PRISMA 2020 guideline adherence: a study protocol

Yuki Kataoka, Ryuhei So, Masahiro Banno, Yasushi Tsujimoto, Tomohiro Takayama, Yosuke Yamagishi, Takahiro Tsuge, Norio Yamamoto, Chiaki Suda, Toshi A. Furukawa

- **Yuki Kataoka, MD, MPH, DrPH**
  - ORCID: 0000-0001-7982-5213
  - Center for Postgraduate Clinical Training and Career Development, Nagoya University Hospital, 65, Tsurumai-cho, Showa‑ku, Nagoya‑city, Aichi, Japan 
  - Center for Medical Education, Graduate School of Medicine, Nagoya University, 65, Tsurumai-cho, Showa‑ku, Nagoya‑city, Aichi, Japan
  - Scientific Research Works Peer Support Group (SRWS-PSG), Osaka, Japan
  - Department of Internal Medicine, Kyoto Min-iren Asukai Hospital, Tanaka Asukai-cho 89, Sakyo-ku, Kyoto 606-8226, Japan
  - Department of Healthcare Epidemiology, Kyoto University Graduate School of Medicine / School of Public Health, Yoshida Konoe-cho, Sakyo-ku, Kyoto 606-8501, Japan
  - Department of International and Community Oral Health, Tohoku University Graduate School of Dentistry, 4-1, Seiryo-machi, Aoba-ku, Sendai, Miyagi, 980-8575, Japan

- **Ryuhei So, MD, MPH, PhD**
  - ORCID: 0000-0002-9838-350X
  - Department of Psychiatry, Okayama Psychiatric Medical Center, Okayama, Japan
  - CureApp, Inc., Tokyo, Japan
  - Scientific Research WorkS Peer Support Group (SRWS-PSG), Osaka, Japan

- **Masahiro Banno, MD, PhD**
  - ORCID: 0002-2539-1031
  - Department of Psychiatry, Seichiryo Hospital, Nagoya, Japan
  - Department of Psychiatry, Nagoya University Graduate School of Medicine, Nagoya, Japan
  - Scientific Research WorkS Peer Support Group (SRWS-PSG), Osaka, Japan

- **Yasushi Tsujimoto, MD, MPH, PhD**
  - ORCID: 0002-7214-5589
  - Oku medical clinic, Osaka, Japan
  - Department of Health Promotion and Human Behavior, Kyoto University Graduate School of Medicine / School of Public Health, Kyoto University, Kyoto, Japan.
  - Scientific Research WorkS Peer Support Group (SRWS-PSG), Osaka, Japan

- **Tomohiro Takayama, MD**
  - ORCID: 0009-0000-3313-0619
  - Kyoto University Hospital, Kyoto, Kyoto, Japan

- **Yosuke Yamagishi, MD/MSc**
  - ORCID: 0009-0006-7688-3075
  - Division of Radiology and Biomedical Engineering, Graduate School of Medicine, The University of Tokyo

- **Takahiro Tsuge, PT, MPH**
  - ORCID: 0000-0003-0497-944X
  - Department of Rehabilitation, Kurashiki Medical Centre, Kurashiki, Okayama 710-8522, Japan
  - Department of Epidemiology, Graduate School of Medicine, Dentistry, and Pharmaceutical Sciences, Okayama University, Okayama 700-8558, Japan
  - Scientific Research WorkS Peer Support Group (SRWS-PSG), Osaka 541-0043, Japan

- **Norio Yamamoto, MD, PhD**
  - ORCID: 0000-0003-3927-399X
  - Scientific Research WorkS Peer Support Group (SRWS-PSG), Osaka 541-0043, Japan
  - Department of Orthopedic Surgery, Minato Medical Coop-Kyoritsu General Hospital, Nagoya, Aichi 456-8611, Japan

- **Chiaki Suda, MD**
  - ORCID: 0000-0001-8642-1559
  - Department of Public Health, Gunma University Graduate School of Medicine · Gunma, JPN
  - Scientific Research WorkS Peer Support Group (SRWS-PSG), Osaka 541-0043, Japan

- **Toshi A. Furukawa, MD, PhD**
  - ORCID: 0000-0003-2159-3776
  - Department of Health Promotion and Human Behavior, Kyoto University Graduate School of Medicine/School of Public Health, Kyoto, Japan

Correspondence:
Yuki Kataoka, MD, MPH, DrPH
youkiti　at　gmail.com

## 1. Background

Transparent reporting is foundational to trustworthy evidence synthesis. The Preferred Reporting Items for Systematic reviews and Meta-Analyses (PRISMA) 2020 statement was developed to improve the reporting quality of systematic reviews (SRs) [@Page2021-vy]. Yet recent assessments indicate that adherence remains suboptimal across fields [@Ivaldi2024-jl;@Suda2025-nd;@Tsuge2025-ev]. In practice, checking adherence is performed manually by peer reviewers and editors adding to the peer-review workload. This burden is exacerbated by increasing demands on the global peer‑review workforce [@Kovanis2016-zy;@Aczel2021-hm].

Recent advances in large language models (LLMs) have demonstrated potential for improving the efficiency of this process. Prior studies have explored adherence to reporting guidelines, including the STROBE statement for observational studies [@Sanmarchi2023-fu], and CONSORT and SPIRIT statements for randomized controlled trials [@Alharbi2024-ar;@Chen2025-vc;@Wrightson2025-pd;@Srinivasan2025-gr], while studies addressing PRISMA 2020 statement have remained limited to small samples and abstracts [@Alharbi2024-ar;@Forero2025-ra]. 

Two barriers limit the efficiency. First, the field lacks a robust, publicly shareable, copyright‑conscious benchmark with item‑level labels on full‑text systematic reviews [Ni2025-em]. Second, the influence of input representation on LLM performance remains unexamined. Although recent evidence suggests that prompt formatting [@He2024-do] substantially affects performance, no study has systematically evaluated input formats for medical literature analysis using current-generation LLMs.

To address these gaps, this study addresses two objectives. We will first develop a robust, copyright-conscious benchmark for PRISMA 2020 adherence, comprising license‑compatible full texts with item‑level human annotations. Second, we will systematically compare various input formats to determine the optimal approach for automating assessment. Our research aims to provide an evidence-based insights for the efficient and accurate integration of LLMs into systematic review quality assurance.

## 2. Methods

### 2.1 Data Sources

This study will obtain data from the following two studies:

1. **Suda C, et al. (2025)** - Study on PRISMA 2020 usage in emergency medicine journals
   - PRISMA 2020 compliance evaluation data for systematic reviews in emergency medicine

2. **Tsuge T, et al. (2025)** - Systematic review evaluation study in rehabilitation journals
   - PRISMA 2020 compliance evaluation data for 120 papers in the rehabilitation field

### 2.2 Experimental Design

```{.mermaid format=png}
flowchart TD
    A[Data Preparation] --> B[Input Format Conversion]
    B --> C[LLM Evaluation Execution]
    C --> D[Comparison with Human Evaluation]
```

#### 2.2.1 Data Preparation
1. Extract lists of evaluated systematic reviews from the two papers.
2. Retrieve target systematic review papers for evaluation when they are publicly accessible through creative commons license.
3. Convert each manuscript's PDF file, including supplementary materials, into a structured JSON file using the Adobe PDF Extract API [@adobeextract-ya].
4. Prepare original PRISMA 2020 evaluation results (by humans) as the reference standard.

#### 2.2.2 Input Format Conversion
Convert the PRISMA 2020 checklist (27 items) into the following 5 formats. These format choices are based on the methodology for verifying processing accuracy differences between formats demonstrated in the prior study [@He2024-do]:

1. **Plain Text Format**
   - Express PRISMA 2020 items directly as text
   - Example: "Item 1: Identify the report as a systematic review."

2. **YAML Format**
   ```yaml
   - item: "1"
     section: "Title"
     description: "Identify the report as a systematic review."
   ```

3. **JSON Format**
   ```json
   {
     "item": "1",
     "section": "Title",
     "description": "Identify the report as a systematic review.",
   }
   ```

4. **Markdown Format**
   ```markdown
   # PRISMA 2020 Checklist
   
   ## TITLE - Title
   ### Item 1: Identify the report as a systematic review.
   ```

5. **Structured XML Format**
   ```xml
   <PRISMA 2020_item id="1">
     <section>Title</section>
     <description>Identify the report as a systematic review.</description>
   </PRISMA 2020_item>
   ```

#### 2.2.3 LLM Evaluation Execution
We will conduct an initial experiment on 10 articles randomly sampled from Suda et al’s dataset. If the results are favorable, we will then test for reproducibility using 10 articles randomly sampled from Tsuge et al’s dataset.

We will use a unified prompt optimized for model characteristics:

```
You are an expert in evaluating systematic reviews based on PRISMA 2020 guidelines.
Please evaluate the provided systematic review paper against the following PRISMA 2020 items.
For each item, respond with "Yes", "No" and provide a brief rationale.

# paper
[Insert the paper]

# PRISMA 2020 checklist
[Insert PRISMA 2020 items in each format here]

```

To improve evaluation metrics, we will adopt other prompting techniques as necessary.


### 2.3 Evaluation Metrics

#### 2.3.1 Primary Evaluation Metrics
- **Accuracy** – proportion of correct item-level judgements (Yes/No).
- **Sensitivity** – proportion of true positives in all human positives.
- **Specificity** – proportion of true negatives in all human negatives.

#### 2.3.2 Secondary Evaluation Metrics
- **Token size** - The amount of data the API processed per paper
- **Cost** – API usage cost per paper
- **Time** – Latency to receive the API response per paper



### 2.4 Statistical Analysis
We will use descriptive statistics to summarize the data. We will first use the Suda et al.'s dataset to identify the most effective combinations of LLM models and input formats. Subsequently, we will assess the reproducibility of these top-performing combinations using the Tsuge et al.’s dataset.

## 2.5 Technical Implementation

### 2.5.1 System Architecture

```{.mermaid format=png}
flowchart LR
    A[Data Management Module] --> B[Format Conversion Module]
    B --> C[LLM Integration Module]
    C --> D[Evaluation Collection Module]
    D --> E[Analysis Module]
```

### 2.5.2 Required Technologies and Tools
- **Languages/Libraries**: Python (pydantic, typer, pandas, numpy, scikit-learn, pyyaml, httpx)
- **AI APIs / Providers**: Claude Opus 4.1 (Anthropic), GPT-5 & GPT-4o (OpenAI), Gemini 2.5 Pro (Google), Grok-4 (xAI via OpenRouter), Qwen3-235B & GPT-OSS variants (OpenRouter)

## 3. Discussion

### 3.1 Novel Contributions
This study represents the first systematic investigation of input format effects on LLM performance for PRISMA 2020 guideline adherence assessment. Building on the methodological framework presented in Section 2, we will establish a standardized benchmark. Our multi-format experimental design-comparing plain text,  YAML, JSON, Markdown, and XML inputs-provides empirical evidence that format selection materially affects evaluation accuracy.

### 3.2 Limitations
This study has two primary limitations related to our datasets. First, the evaluation scope is restricted to systematic reviews from two datasets in emergency medicine and rehabilitation, which might limit generalizability to other medical specialties. Second, the human reference annotations from these datasets may contain residual inconsistencies.

### 3.3 Conclusion
By addressing the critical gap in format-driven LLM assessment for PRISMA 2020 adherence, this study provides actionable guidance for integrating assistance into quality assuarance of SR. The results will also encourage researchers and publishers to use LLMs for evaluating PRISMA 2020 adherence. In addition, reporting guideline researchers to release LLM-ready checklist formats alongside human-readable documentation.

## References

