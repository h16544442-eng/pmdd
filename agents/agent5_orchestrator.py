import json
import os
from typing import Dict, List, Tuple
from openai import OpenAI
from dotenv import load_dotenv
from generate_report_pdf import PMDD_Report, clean_text

load_dotenv()

AGENT_05_PROMPT = """
You are AGENT 05 — Orchestrator & Evidence Synthesizer.

Your role is to produce a unified, research-grade linguistic report. 

---
## CORE MISSION
1. **Quality Audit (MANDATORY)**: You MUST include a section called "PIPELINE HEALTH REPORT". 
   - Explicitly list which agents (1-4) provided full data, partial data, or no data.
   - Summarize any self-corrections made by the Reflective Brains (Agent 2 and 3).
2. **Triangulated Synthesis**: Combine pragmatic, semantic, and statistical findings into a coherent narrative using Fairclough's CDA framework.
3. **Strict 30/70 Ratio**: You MUST maintain a 30% Quantitative (Statistics) and 70% Qualitative (Corpus Segments) evidence ratio.
4. **Meaning Drift Score**: Assign a score (0-100) based on the intensity of change detected across all layers.

---
## FORMATTING INSTRUCTIONS FOR PDF PARSER
- Use `#` or `##` for all section titles.
- Use `>` blockquotes ONLY when citing raw qualitative evidence (segments) from the text.
- Do not wrap the entire output in markdown code fences.

---
## REPORT SECTIONS
1. EXECUTIVE SUMMARY
2. PIPELINE HEALTH REPORT & REFLECTIVE AUDIT
3. PRAGMATIC DRIFT ANALYSIS
4. SEMANTIC SHIFT & REGISTER COHERENCE
5. CORPUS STATISTICAL VALIDATION
6. FINAL DISCOURSE CRITIQUE
7. MEANING DRIFT SCORE
"""

def run_agent5(corpus_name: str, a1: Dict, a2: List[Dict], a3: Dict, a4: Dict, api_key: str = None) -> Tuple[str, str, Dict]:
    """
    Agent 5: Orchestrator & Synthesizer (LLM Based)
    """
    client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
    
    # Prepare data for synthesis
    synthesis_data = {
        "corpus_name": corpus_name,
        "agent1_preprocessor": a1.get("corpus_stats", {}),
        "agent2_pragmatic": a2[:10], # Sample for LLM synthesis
        "agent3_semantic": {
            "drift_map": a3.get("semantic_drift_map", [])[:5],
            "register_summary": a3.get("register_summary", {})
        },
        "agent4_corpus_stats": a4.get("report_markdown", "")
    }

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": AGENT_05_PROMPT},
                {"role": "user", "content": f"Synthesize these findings into a final report:\n\n{json.dumps(synthesis_data)}"}
            ],
            temperature=0.3
        )
        
        full_output = response.choices[0].message.content
        report_md = full_output
        
        # Create PDF from the report markdown
        os.makedirs("outputs", exist_ok=True)
        pdf = PMDD_Report()
        pdf.add_page()
        pdf.set_font('Helvetica', 'B', 16)
        pdf.cell(0, 10, clean_text(f"Linguistic Analysis: {corpus_name}"), 0, 1, 'C')
        pdf.ln(10)
        
        # Enhanced markdown to PDF conversion for the sections
        for line in report_md.split('\n'):
            line = line.strip()
            if not line:
                continue
            if line.startswith('#'):
                clean_title = line.replace('#', '').strip()
                pdf.chapter_title(clean_title)
            elif line.startswith('>'):
                clean_evidence = line.replace('>', '').strip()
                pdf.evidence_box("CITED", clean_evidence, "Qualitative Evidence")
            else:
                pdf.chapter_body(line)
        
        pdf_path = f"outputs/{corpus_name.replace(' ', '_')}_Final_Report.pdf"
        pdf.output(pdf_path)
        
        return report_md, pdf_path, synthesis_data
    except Exception as e:
        return f"Synthesis failed: {str(e)}", "", {}

if __name__ == "__main__":
    pass
