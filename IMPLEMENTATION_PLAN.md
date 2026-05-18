# IMPLEMENTATION PLAN: Pragmatic Meaning Drift Detector (PMDD)

## 1. Project Overview
The **Pragmatic Meaning Drift Detector (PMDD)** is an agentic AI application designed for large-scale linguistic corpus analysis. It uses a 5-agent architecture to detect shifts in pragmatic meaning, semantic fields, and social registers across different sections or time periods of a text.

---

## 2. Architecture & Memory Design
The system implements four types of memory as defined in the theoretical framework:
*   **In-Context Memory**: LLM conversation history for individual agent reasoning.
*   **External Memory**: Persistent storage (JSON/Database) for sharing data between agents.
*   **Episodic Memory**: A "Long-Term Experience Log" that allows agents to learn from past corpus analyses. This enables the system to recognize recurring linguistic patterns and avoid repeating previous analytical errors.
*   **Semantic Memory**: Vector embeddings of keywords to track conceptual movement.

### The "Agent Brain" (Self-Correction Loop)
Every agent implements a **Reflective Loop**:
1. **Act**: The agent performs the initial linguistic analysis.
2. **Reflect**: The agent reviews its own output against the core linguistic theory.
3. **Correct**: If a discrepancy is found (e.g., a speech act misclassification), the agent updates its output before passing it to the next stage.

---

## 3. Detailed Agent Implementation Plan

### Phase 1: Agent 1 - Corpus Preprocessor & Segmenter
*   **Responsibility**: Clean raw data and prepare linguistic segments.
*   **Framework**: Sinclair’s Corpus Methodology.
*   **Tasks**:
    1. Read `.txt`, `.csv`, `.json`, or `.pdf`.
    2. Segment text into sentences using `spaCy`.
    3. Tag segments with metadata (`id`, `word_count`, `relative_position`).
*   **Output**: `segments.json`

### Phase 2: Agent 2 - Pragmatic Analyzer
*   **Responsibility**: Identify speech acts and maxim violations.
*   **Framework**: Searle (Speech Act Theory) & Grice (Cooperative Principle).
*   **Tasks**:
    1. Apply the user-provided "Linguistic Framework Prompt".
    2. Classify dominant Speech Acts (Assertive, Directive, etc.).
    3. Identify violations of Gricean Maxims (Quantity, Quality, Relation, Manner).
*   **Output**: `pragmatic_analysis.json`

### Phase 3: Agent 3 - Semantic Field & Register Detector
*   **Responsibility**: Map vocabulary drift and social context shifts.
*   **Framework**: Lyons (Semantic Field Theory) & Halliday (Register Analysis).
*   **Tasks**:
    1. Extract content words and cluster into semantic fields using GPT-4o.
    2. Detect register shifts (Formal vs. Informal) across sections.
    3. Identify "Register Borrowing".
*   **Output**: `semantic_drift_map.json`

### Phase 4: Agent 4 - Corpus Statistician
*   **Responsibility**: Quantitative validation of linguistic patterns.
*   **Framework**: Sinclair (Frequency & Collocation) & Scott (Keyness).
*   **Tasks**:
    1. Compute word frequencies and Type-Token Ratio (TTR).
    2. Calculate Mutual Information (MI) scores for collocations.
    3. Identify statistically significant "Keywords" per section.
*   **Output**: `statistical_tables.csv`

### Phase 5: Agent 5 - Orchestrator & Evidence Synthesizer
*   **Responsibility**: Final report generation and quality assurance.
*   **Framework**: Fairclough (Critical Discourse Analysis).
*   **Tasks**:
    1. Review all agent outputs for consistency using the **Reflective Brain**.
    2. Trigger feedback loops if coverage is below 50%.
    3. Synthesize findings into a formal scientific report.
    4. **PDF Generation**: Automatically generate a research-grade PDF using the `fpdf2` library, incorporating quantitative tables and qualitative evidence citations (30/70 ratio).
*   **Output**: `final_linguistic_report.pdf` & `dashboard_metrics.json`

---

## 4. Technical Implementation Roadmap

### Step 1: Project Scaffolding
*   Create directory structure.
*   Install dependencies: `openai`, `spacy`, `pandas`, `gradio`.
*   Download `en_core_web_sm` model.

### Step 2: Agent Development
*   Implement agents sequentially as standalone Python modules.
*   Test each agent with a 10-segment "Mini-Corpus".

### Step 3: Application Integration
*   Build the main `app.py` using Gradio.
*   Implement the sequential pipeline logic with Agent 5 as the controller.

### Step 4: Validation
*   Run the system on the "Political Speech Corpus" (2000-2024).
*   Verify the **Overall Meaning Drift Score** calculation logic.

---

## 5. Success Criteria
1. **Theoretical Grounding**: Every finding must be linked to one of the six theoretical frameworks.
2. **Evidence-Based**: Every claim in the final report must cite a specific Segment ID.
3. **Modularity**: Each agent must function independently if needed.
4. **Interpretability**: The results must be defensible by a human linguist.
