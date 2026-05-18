import os
import json
from typing import List, Dict
from openai import OpenAI
from dotenv import load_dotenv
import sys

# Add the parent directory to the system path so we can import utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.memory import get_all_experiences, save_to_memory

load_dotenv()

AGENT_03_ACT_PROMPT = """
You are AGENT 03 — Semantic Field & Register Detector.

Your mission is to perform deep lexical analysis on pragmatically enriched segments. You must identify semantic clustering, track field drift, and classify the register using Hallidayan linguistics.

---
## EPISODIC MEMORY (LEARNING FROM PAST ANALYSES)
Here are lessons from past corpora analyses. Use these to adapt your approach and avoid past mistakes:
{episodic_memory}

---
## CORE TASKS
1. **Semantic Field Indexing**: Map every significant content word to a domain-specific field (e.g., 'trust' -> 'MORALITY', 'market' -> 'ECONOMY').
2. **Semantic Drift Mapping**: Crucial task. Identify at least 3-5 keywords that show a change in semantic field or intensity across the provided segments. If no drift is found, identify the most stable high-frequency fields.
3. **Register Summary**: Use Halliday's Field (Topic), Tenor (Relationship), and Mode (Channel) to define the dominant register.

---
## REQUIRED OUTPUT STRUCTURE (STRICT)
You must return a JSON object with these EXACT keys:
{
  "agent": "AGENT_03",
  "semantic_field_index": { 
    "word": { "field": "...", "pos": "...", "frequency": 0 }
  },
  "semantic_drift_map": [
    { "lemma": "...", "original_field": "...", "emergent_field": "...", "drift_severity": "HIGH/MEDIUM/LOW", "evidence": "..." }
  ],
  "register_summary": {
    "dominant_register": "...",
    "field": "...",
    "tenor": "...",
    "mode": "...",
    "mean_lexical_density": 0.0,
    "register_shift_count": 0
  },
  "segments": [
    {
      "text": "...",
      "semantics": {
        "content_words": [],
        "primary_field": "...",
        "register_elevation": "STABLE/ELEVATED/INTRUSIVE"
      }
    }
  ]
}

Ensure 'semantic_drift_map' is ALWAYS populated with at least 2 entries. If you cannot find drift, use the most prominent stable field entries.
"""

AGENT_03_REFLECT_PROMPT = """
You are the Reflective Brain (Quality Assurance) for the Semantic Field & Register Detector.
Your task is to review the Initial Analysis and identify any theoretical inconsistencies.

CHECKLIST:
1. Does the Semantic Drift Map accurately reflect Lyons' Theory? (Are the fields logical or hallucinatory?)
2. Are the Register parameters (Field, Tenor, Mode) correctly identified under Halliday's framework?
3. Ensure there are no contradictions between the 'semantic_field_index' and 'segments' data.

If the initial analysis is perfectly correct, return it EXACTLY as is.
If there is an error, correct the JSON values.
In either case, you MUST add a "reflection_notes" string field at the root level of the JSON explaining your verification or correction process.

Return ONLY valid JSON matching the exact schema provided in the initial task. Do not wrap in markdown.
"""

def run_agent3(segments: List[Dict], limit: int = 5, api_key: str = None) -> Dict:
    """
    Agent 3: Semantic Field & Register Detector (LLM Based with Reflective Loop and Episodic Memory)
    """
    client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
    
    # Retrieve Episodic Memory
    past_experiences = get_all_experiences()
    system_prompt_act = AGENT_03_ACT_PROMPT.replace("{episodic_memory}", past_experiences)

    try:
        # ---------------------------------------------------------
        # STEP 1: ACT (Initial Analysis)
        # ---------------------------------------------------------
        act_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt_act},
                {"role": "user", "content": f"Analyze these pragmatically enriched segments:\n\n{json.dumps(segments[:limit])}"}
            ],
            temperature=0.2,
            response_format={ "type": "json_object" }
        )
        
        initial_result = json.loads(act_response.choices[0].message.content)
        
        # ---------------------------------------------------------
        # STEP 2: REFLECT & CORRECT (The Brain)
        # ---------------------------------------------------------
        reflect_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": AGENT_03_REFLECT_PROMPT},
                {"role": "user", "content": f"Initial Analysis:\n{json.dumps(initial_result, indent=2)}\n\nVerify and output the final corrected JSON."}
            ],
            temperature=0,
            response_format={ "type": "json_object" }
        )
        
        final_result = json.loads(reflect_response.choices[0].message.content)
        
        # Save to Episodic Memory if a correction was made
        if "reflection_notes" in final_result and "corrected" in final_result["reflection_notes"].lower():
            memory_entry = {
                "task": "Semantic & Register Detection",
                "lesson": final_result["reflection_notes"]
            }
            save_to_memory("Agent3_Correction_Log", memory_entry)
            
        return final_result
        
    except Exception as e:
        return {"error": str(e), "agent": "AGENT_03"}

if __name__ == "__main__":
    pass
