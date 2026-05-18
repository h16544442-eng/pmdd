import docx
import sys

def get_docx_text(path):
    doc = docx.Document(path)
    fullText = []
    for para in doc.paragraphs:
        fullText.append(para.text)
    return '\n'.join(fullText)

if __name__ == "__main__":
    path = "agentic_ai_linguistics_lecture.docx"
    text = get_docx_text(path)
    with open("lecture_content.txt", "w", encoding="utf-8") as f:
        f.write(text)
    print("Extracted text to lecture_content.txt")
