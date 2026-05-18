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

AGENT_02_ACT_PROMPT = """
You are AGENT 02 — Pragmatic Analyzer.

Your role is to receive the structured JSON produced by AGENT 01 and enrich each segment with a full pragmatic analysis layer. You operate exclusively within formal linguistic pragmatics: Speech Act Theory, Gricean Cooperative Principle, and Brown & Levinson Politeness Theory.

You do not interpret texts for meaning, theme, or sentiment. You classify communicative behaviour at the utterance level using established theoretical frameworks only.

---
## EPISODIC MEMORY (LEARNING FROM PAST ANALYSES)
Here are lessons from past corpora analyses. Use these to adapt your approach and avoid past mistakes:
{episodic_memory}

---
## THEORETICAL FOUNDATIONS
1. Speech Act Theory — Austin (1962) & Searle (1969) (ASSERTIVE, DIRECTIVE, COMMISSIVE, EXPRESSIVE, DECLARATION)
2. Gricean Cooperative Principle — Grice (1975) (QUANTITY, QUALITY, RELATION, MANNER)
3. Implicature — Grice (1975) (CONVENTIONAL, CONVERSATIONAL [GENERALISED/PARTICULARISED])
4. Politeness Theory — Brown & Levinson (1987) (POSITIVE/NEGATIVE FACE, FTAs, FACE-SAVING STRATEGIES)

---
## PROCESSING INSTRUCTIONS
1. Read the "text" field as the primary unit of analysis.
2. Use "sentences" sub-array for fine-grained analysis.
3. Compute one pragmatic annotation block per segment.
4. Return ONLY valid JSON adding a "pragmatics" object to each segment.

---
## OUTPUT CONTRACT (JSON Schema for "pragmatics")
"pragmatics": {
  "speech_act": { "category": "...", "directness": "...", "confidence": "...", "indirect_function": "" },
  "sentence_acts": [],
  "maxim_violations": [],
  "implicature": { "type": "...", "trigger": "", "inferred_proposition": "" },
  "politeness": { "score": 0.0, "fta_present": false, "fta_type": "...", "fta_target": "...", "strategy": "...", "strategy_evidence": "" },
  "pragmatic_ambiguity": { "flagged": false, "reason": "" }
}

Do not wrap output in markdown code fences. Return raw JSON only.
"""

AGENT_02_REFLECT_PROMPT = """
You are the Reflective Brain (Quality Assurance) for the Pragmatic Analyzer.
Your task is to review the Initial Analysis for the given text segment and identify any theoretical inconsistencies.

CHECKLIST:
1. Does the Speech Act correctly match Searle's taxonomy? (e.g., Are indirect directives misclassified as assertives?)
2. Are Gricean Maxim violations correctly identified based on the context?
3. Is the Politeness Theory application sound?

If the initial analysis is perfectly correct, return it EXACTLY as is.
If there is an error, correct the JSON values.
In either case, you MUST add a "reflection_notes" string field to the JSON explaining your verification or correction process.

Return ONLY valid JSON matching the "pragmatics" schema. Do not wrap in markdown.
"""

def run_agent2(segments: List[Dict], limit: int = 5, api_key: str = None) -> List[Dict]:
    """
    Agent 2: Pragmatic Analyzer (LLM Based with Reflective Loop and Episodic Memory)
    """
    client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
    
    target_segments = segments[:limit]
    enriched_segments = []
    
    # Retrieve Episodic Memory
    past_experiences = get_all_experiences()
    system_prompt_act = AGENT_02_ACT_PROMPT.replace("{episodic_memory}", past_experiences)

    for seg in target_segments:
        try:
            # ---------------------------------------------------------
            # STEP 1: ACT (Initial Analysis)
            # ---------------------------------------------------------
            act_response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt_act},
                    {"role": "user", "content": f"Analyze this segment JSON and add 'pragmatics' block:\n\n{json.dumps(seg)}"}
                ],
                temperature=0.2,
                response_format={ "type": "json_object" }
            )
            
            initial_result = json.loads(act_response.choices[0].message.content)
            initial_pragmatics = initial_result.get("pragmatics", initial_result)
            
            # ---------------------------------------------------------
            # STEP 2: REFLECT & CORRECT (The Brain)
            # ---------------------------------------------------------
            reflect_response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": AGENT_02_REFLECT_PROMPT},
                    {"role": "user", "content": f"Text Segment: {seg.get('text', '')}\n\nInitial Analysis:\n{json.dumps(initial_pragmatics, indent=2)}\n\nVerify and output the final corrected JSON."}
                ],
                temperature=0,
                response_format={ "type": "json_object" }
            )
            
            final_result = json.loads(reflect_response.choices[0].message.content)
            final_pragmatics = final_result.get("pragmatics", final_result)
            
            # Save the final result back to the segment
            seg["pragmatics"] = final_pragmatics
            enriched_segments.append(seg)
            
            # Save to Episodic Memory if a correction was made
            if "reflection_notes" in final_pragmatics and "corrected" in final_pragmatics["reflection_notes"].lower():
                memory_entry = {
                    "text": seg.get("text", ""),
                    "lesson": final_pragmatics["reflection_notes"]
                }
                save_to_memory("Agent2_Correction_Log", memory_entry)
                
        except Exception as e:
            seg["pragmatics"] = {"error": str(e), "skipped": True}
            enriched_segments.append(seg)

    return enriched_segments

if __name__ == "__main__":
    pass
