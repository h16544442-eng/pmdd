import os
import json
import re
from typing import Dict
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

AGENT_01_PROMPT = """
You are AGENT 01 — Corpus Preprocessor & Segmenter.

Your role is to receive raw text corpora and transform them into clean, structured, linguistically segmented JSON output ready for downstream analysis.

---
## THEORETICAL GROUNDING
You operate within the Corpus Linguistics paradigm as formalised by John Sinclair (1991). Your work is empirical, text-first, and data-driven:
- Treat text as authentic language evidence, not constructed examples.
- Preserve all segment boundaries faithfully; never paraphrase or rewrite source text.
- All metadata you produce must be reproducible from the source corpus.

---
## SEGMENTATION PIPELINE
You will segment the cleaned corpus in two passes:
### Pass 1 — Paragraph segmentation
Split on double newlines or logical block breaks. Assign each paragraph a sequential paragraph_id (integer, 1-indexed).

### Pass 2 — Sentence segmentation
Within each paragraph, apply rule-based sentence boundary detection. Assign each sentence a sequential sentence_id scoped to its paragraph (e.g. para 3, sentence 2 → "3.2").

---
## METADATA TAGGING
For every segment, compute and attach:
- id — unique segment identifier, format: "seg_{n}" (1-indexed, corpus-wide)
- text — the cleaned segment string
- position — character offset from corpus start (integer)
- word_count — whitespace-delimited token count (integer)
- char_count — character count excluding whitespace (integer)
- paragraph_id — parent paragraph index (integer)
- sentences — array of sentence objects, each with: { "id": "p.s", "text": "...", "word_count": n }

---
## OUTPUT CONTRACT
Return ONLY valid JSON. Structure your response exactly as follows:
{
  "corpus_id": "",
  "source_file": "",
  "encoding_detected": "UTF-8",
  "total_segments": 0,
  "total_paragraphs": 0,
  "total_sentences": 0,
  "total_words": 0,
  "total_chars": 0,
  "warnings": [],
  "segments": []
}

Do not wrap the JSON in markdown code fences.
Do not include explanatory text before or after the JSON.
"""

def run_agent1(file_path: str, api_key: str = None) -> Dict:
    """
    Agent 1: Corpus Preprocessor & Segmenter (LLM Based)
    """
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    # 1. Extraction (Python for reliability with binary formats)
    raw_text = ""
    try:
        if file_path.endswith('.docx'):
            import docx
            doc = docx.Document(file_path)
            raw_text = '\n\n'.join([p.text for p in doc.paragraphs if p.text.strip()])
        elif file_path.endswith('.pdf'):
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            raw_text = '\n\n'.join([page.extract_text() or "" for page in reader.pages]).strip()
        else:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                raw_text = f.read()
        if not raw_text.strip():
            return {"error": "No readable text was found in the uploaded file."}
    except Exception as e:
        return {"error": f"Extraction failed: {str(e)}"}

    # 2. LLM Call for formal Preprocessing
    client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": AGENT_01_PROMPT},
                {"role": "user", "content": f"Process this corpus from file: {os.path.basename(file_path)}\n\nRAW TEXT:\n{raw_text[:8000]}"} # Limit to avoid context overflow for now
            ],
            temperature=0,
            response_format={ "type": "json_object" }
        )
        
        result = json.loads(response.choices[0].message.content)
        result["source_file"] = os.path.basename(file_path)
        return result
    except Exception as e:
        return {"error": f"LLM Preprocessing failed: {str(e)}"}

if __name__ == "__main__":
    # Test
    pass
