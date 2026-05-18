import os
import json
import math
import pandas as pd
from collections import Counter
from typing import List, Dict
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class CorpusStatistician:
    def __init__(self, segments: List[Dict], api_key: str = None):
        self.segments = segments
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.total_tokens = []
        for s in segments:
            # Simple whitespace tokenization for stats as per framework
            self.total_tokens.extend(s['text'].lower().split())
        self.corpus_size = len(self.total_tokens)
        self.vocab = Counter(self.total_tokens)

    def calculate_ttr(self):
        types = len(self.vocab)
        tokens = self.corpus_size
        ttr = (types / tokens) * 100 if tokens > 0 else 0
        return {"tokens": tokens, "types": types, "ttr": round(ttr, 2)}

    def calculate_frequencies(self, top_n=50):
        # Exclude common stopwords
        stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "is", "was", "of", "that", "it", "this", "as"}
        content_freq = {w: f for w, f in self.vocab.items() if w not in stopwords and len(w) > 1}
        sorted_freq = sorted(content_freq.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        table = []
        for rank, (word, freq) in enumerate(sorted_freq, 1):
            rel_freq = round((freq / self.corpus_size) * 1000, 2)
            table.append({"Rank": rank, "Word": word, "Raw Freq": freq, "Rel. Freq (per 1k)": rel_freq})
        return table

    def calculate_mi_score(self, target_word, span=5):
        # MI = log2(observed / expected)
        target_word = target_word.lower()
        if target_word not in self.vocab: return []
        
        target_freq = self.vocab[target_word]
        collocates = Counter()
        
        for i, token in enumerate(self.total_tokens):
            if token == target_word:
                start = max(0, i - span)
                end = min(len(self.total_tokens), i + span + 1)
                for j in range(start, end):
                    if i != j:
                        collocates[self.total_tokens[j]] += 1
        
        results = []
        for coll, obs in collocates.items():
            if obs < 2: continue 
            coll_freq = self.vocab[coll]
            expected = (target_freq * coll_freq * (span * 2)) / self.corpus_size
            if expected == 0: continue
            mi = math.log2(obs / expected)
            if mi >= 3.0: 
                results.append({"Collocate": coll, "Co-occurrences": obs, "Expected": round(expected, 3), "MI Score": round(mi, 2)})
        
        return sorted(results, key=lambda x: x["MI Score"], reverse=True)[:10]

    def generate_markdown_report(self, limit=5, api_key=None):
        freq_table = self.calculate_frequencies()
        ttr_data = self.calculate_ttr()
        
        top_keyword = freq_table[0]["Word"] if freq_table else "data"
        collocates = self.calculate_mi_score(top_keyword)

        report = f"## 1. Word Frequency List\n\n"
        df_freq = pd.DataFrame(freq_table[:20])
        report += df_freq.to_markdown(index=False) + "\n\n"
        
        report += f"## 2. Type-Token Ratio\n\n"
        report += f"| Tokens | Types | TTR (%) |\n|---|---|---|\n| {ttr_data['tokens']} | {ttr_data['types']} | {ttr_data['ttr']}% |\n\n"
        
        report += f"## 3. Top Collocates for '{top_keyword}'\n\n"
        if collocates:
            df_coll = pd.DataFrame(collocates)
            report += df_coll.to_markdown(index=False) + "\n\n"
        else:
            report += "No significant collocates detected.\n\n"

        client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        try:
            interp_response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a quantitative corpus linguist. Interpret the following statistical tables scientifically using Sinclair (1991) and Scott (1997) frameworks."},
                    {"role": "user", "content": f"Statistical Data:\n{report}"}
                ],
                temperature=0.3
            )
            report += "\n### Linguistic Interpretation\n" + interp_response.choices[0].message.content
        except:
            report += "\n(Interpretation unavailable)"

        return report

def run_agent4(segments: List[Dict], limit: int = 5, api_key: str = None) -> Dict:
    """
    Agent 4: Corpus Statistician
    """
    stats = CorpusStatistician(segments, api_key=api_key)
    report_md = stats.generate_markdown_report(limit=limit, api_key=api_key)
    return {"status": "success", "report_markdown": report_md, "tokens_processed": stats.corpus_size}

if __name__ == "__main__":
    pass
