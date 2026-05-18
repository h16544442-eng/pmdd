from agents.agent1_preprocessor import run_agent1
from agents.agent2_pragmatic import run_agent2
from agents.agent3_semantic import run_agent3
from agents.agent4_statistics import run_agent4
from agents.agent5_orchestrator import run_agent5
import os

def test_full_pipeline():
    print("Starting Full Pipeline Integration Test...")
    
    # 0. Ensure directories exist
    os.makedirs("data", exist_ok=True)
    os.makedirs("outputs", exist_ok=True)
    
    # 1. Create a mini corpus
    corpus_name = "Integration Test Corpus"
    corpus_file = "data/integration_test.txt"
    with open(corpus_file, "w", encoding="utf-8") as f:
        f.write("The community must reclaim its power. Power is often misunderstood in political discourse. We are building a stronger community through collective action.")
    
    # 2. Run Agents
    print("\n[Step 1] Preprocessing...")
    a1 = run_agent1(corpus_file)
    
    print("\n[Step 2] Pragmatic Analysis (Reflective)...")
    a2 = run_agent2(a1['segments'], limit=3)
    
    print("\n[Step 3] Semantic Analysis (Reflective)...")
    a3 = run_agent3(a1['segments'], limit=3)
    
    print("\n[Step 4] Statistical Analysis...")
    a4 = run_agent4(a1['segments'])
    
    print("\n[Step 5] Orchestration & PDF Generation...")
    report_text, pdf_path = run_agent5(corpus_name, a1, a2, a3, a4)
    
    print(f"\nSUCCESS! Test complete.")
    print(f"Final Report Path: {pdf_path}")
    
    # Optional: Display a snippet of the report
    print("\nReport Snippet:")
    print("-" * 30)
    print(report_text[:300] + "...")
    print("-" * 30)

if __name__ == "__main__":
    test_full_pipeline()
