from fpdf import FPDF

def clean_text(text):
    """
    Clean text for FPDF compatibility (standard fonts only support latin-1).
    """
    if not text:
        return ""
    # Replace smart quotes and other common unicode characters
    replacements = {
        "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "-",
        "\u2026": "...", "\u00a0": " ",
        "\u2022": "*", "\u20ac": "EUR",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    
    # Last resort: encode as latin-1 and ignore what doesn't fit
    return text.encode("latin-1", "ignore").decode("latin-1")

class PMDD_Report(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 12)
        self.cell(0, 10, 'PMDD - Scientific Linguistic Analysis Report', 0, 1, 'C')
        self.ln(5)

    def chapter_title(self, title):
        self.set_font('Helvetica', 'B', 14)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 10, clean_text(title), 0, 1, 'L', 1)
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Helvetica', '', 11)
        self.multi_cell(0, 7, clean_text(body))
        self.ln()

    def evidence_box(self, segment_id, text, analysis):
        self.set_font('Helvetica', 'I', 10)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 5, clean_text(f"Segment #{segment_id}: \"{text}\""))
        self.set_font('Helvetica', 'B', 10)
        self.cell(0, 5, clean_text(f"Analysis: {analysis}"), 0, 1)
        self.set_text_color(0, 0, 0)
        self.ln(3)

def generate_sample_report():
    pdf = PMDD_Report()
    pdf.add_page()
    
    # Title Section
    pdf.set_font('Helvetica', 'B', 20)
    pdf.cell(0, 20, 'Linguistic Drift Analysis Report', 0, 1, 'C')
    pdf.set_font('Helvetica', '', 12)
    pdf.cell(0, 10, 'Target Corpus: Political Speeches', 0, 1, 'C')
    pdf.ln(10)

    pdf.output('PMDD_Sample_Report.pdf')
