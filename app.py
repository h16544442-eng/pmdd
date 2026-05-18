import gradio as gr
import os
import json
from dotenv import load_dotenv
from agents.agent1_preprocessor import run_agent1
from agents.agent2_pragmatic import run_agent2
from agents.agent3_semantic import run_agent3
from agents.agent4_statistics import run_agent4
from agents.agent5_orchestrator import run_agent5

load_dotenv()

def process_corpus(file_obj, corpus_name, analysis_limit):
    """
    The main pipeline connecting all 5 agents.
    """
    if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "your_api_key_here":
        return "ERROR: OpenAI API Key not found. Please update the .env file.", None, None

    logs = []
    
    # --- AGENT 1 ---
    logs.append(">>> Starting Agent 1: Preprocessing...")
    a1_result = run_agent1(file_obj.name)
    if a1_result.get("status") == "error":
        return f"Error in Preprocessing: {a1_result['error']}", None, None
    segments = a1_result["segments"]
    logs.append(f"Agent 1 Complete. Segments found: {len(segments)}")
    
    # --- AGENT 2 ---
    logs.append(">>> Starting Agent 2: Pragmatic Analysis (Reflective Brain)...")
    a2_result = run_agent2(segments, limit=int(analysis_limit))
    logs.append("Agent 2 Complete.")
    
    # --- AGENT 3 ---
    logs.append(">>> Starting Agent 3: Semantic & Register Detection...")
    a3_result = run_agent3(segments, limit=int(analysis_limit))
    logs.append("Agent 3 Complete.")
    
    # --- AGENT 4 ---
    logs.append(">>> Starting Agent 4: Statistical Analysis...")
    a4_result = run_agent4(segments)
    logs.append("Agent 4 Complete.")
    
    # --- AGENT 5 ---
    logs.append(">>> Starting Agent 5: Orchestration & Report Synthesis...")
    report_text, pdf_path = run_agent5(corpus_name, a1_result, a2_result, a3_result, a4_result)
    logs.append(f"Agent 5 Complete. PDF generated: {pdf_path}")
    
    return "\n".join(logs), report_text, pdf_path

# --- GRADIO UI DESIGN ---
# Custom CSS for Glassmorphism and Professional Styling
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=JetBrains+Mono:wght@500;700&display=swap');

:root {
    --primary-color: #6366f1;
    --bg-color: #0b1326;
    --card-bg: rgba(23, 31, 51, 0.6);
    --border-color: rgba(99, 102, 241, 0.2);
}

body {
    background-color: var(--bg-color) !important;
    font-family: 'Inter', sans-serif !important;
}

.gradio-container {
    background-color: var(--bg-color) !important;
    max-width: 1200px !important;
    margin: 0 auto !important;
}

/* Glassmorphism Cards */
.glass-card {
    background: var(--card-bg) !important;
    backdrop-filter: blur(12px) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 12px !important;
    padding: 24px !important;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37) !important;
}

/* Header Styling */
.header-text {
    text-align: center;
    margin-bottom: 40px;
    background: linear-gradient(135deg, #fff 0%, #6366f1 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Terminal/Log area */
.terminal-log textarea {
    background: #060e20 !important;
    color: #c0c1ff !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13px !important;
    border: 1px solid #1e293b !important;
    border-radius: 8px !important;
}

/* Primary Button */
.primary-btn {
    background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
    border: none !important;
    border-radius: 8px !important;
    color: white !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 14px 0 rgba(99, 102, 241, 0.39) !important;
}

.primary-btn:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5) !important;
}

/* Input Fields */
.input-field input, .input-field textarea {
    background: rgba(30, 41, 59, 0.5) !important;
    border: 1px solid rgba(148, 163, 184, 0.2) !important;
    border-radius: 8px !important;
    color: white !important;
}

.input-field input:focus {
    border-color: var(--primary-color) !important;
    box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2) !important;
}
"""

with gr.Blocks() as demo:
    with gr.Row(elem_classes=["header-text"]):
        gr.Markdown("# PMDD: Pragmatic Meaning Drift Detector")
        gr.Markdown("### Agentic AI Framework for Deep Linguistic & Semantic Analysis")
    
    with gr.Row():
        with gr.Column(scale=1, elem_classes=["glass-card"]):
            gr.Markdown("#### 🛠️ Analysis Configuration")
            file_input = gr.File(label="Upload Corpus", file_types=[".txt", ".csv"], elem_classes=["input-field"])
            name_input = gr.Textbox(label="Corpus Name", value="Political Speech Corpus", elem_classes=["input-field"])
            limit_input = gr.Slider(minimum=1, maximum=50, step=1, label="LLM Analysis Limit (Segments)", value=5, elem_classes=["input-field"])
            run_btn = gr.Button("RUN MULTI-AGENT ANALYSIS", variant="primary", elem_classes=["primary-btn"])
            
        with gr.Column(scale=2, elem_classes=["glass-card"]):
            gr.Markdown("#### 🛰️ Real-time Agent Pipeline")
            log_output = gr.Textbox(label="Pipeline Activity", lines=12, elem_classes=["terminal-log"])
            
    with gr.Row(elem_classes=["glass-card"]):
        with gr.Column():
            gr.Markdown("#### 📜 Linguistic Insights Summary")
            report_output = gr.Markdown(elem_id="report-summary")
            pdf_output = gr.File(label="📄 Download Scientific Report (PDF)")

    run_btn.click(
        fn=process_corpus,
        inputs=[file_input, name_input, limit_input],
        outputs=[log_output, report_output, pdf_output]
    )

if __name__ == "__main__":
    print("Launching PMDD Professional Dashboard on http://127.0.0.1:7860")
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        theme=gr.themes.Default(),
        css=custom_css
    )
