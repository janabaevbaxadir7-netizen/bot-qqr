import re
from docx import Document
import io

def parse_docx(file_bytes: bytes) -> dict:
    """
    Parse .docx file and return quiz data.
    Format:
    # QUIZ: Quiz name
    
    Q1: Question
    A) Option A
    B) Option B
    C) Option C
    D) Option D
    ANSWER: B
    """
    try:
        doc = Document(io.BytesIO(file_bytes))
        lines = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                lines.append(text)
            else:
                lines.append('')  # preserve blank lines

        quiz_name = "Quiz"
        questions = []
        current_q = None
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Quiz name
            if line.upper().startswith('# QUIZ:'):
                quiz_name = line[7:].strip()
                i += 1
                continue
            
            # Question
            q_match = re.match(r'^Q(\d+)\s*[:.)]\s*(.+)', line, re.IGNORECASE)
            if q_match:
                if current_q and all(k in current_q for k in ['question', 'a', 'b', 'c', 'd', 'answer']):
                    questions.append(current_q)
                current_q = {
                    'num': int(q_match.group(1)),
                    'question': q_match.group(2).strip()
                }
                i += 1
                continue
            
            # Options
            if current_q:
                a_match = re.match(r'^A\s*[).]\s*(.+)', line, re.IGNORECASE)
                b_match = re.match(r'^B\s*[).]\s*(.+)', line, re.IGNORECASE)
                c_match = re.match(r'^C\s*[).]\s*(.+)', line, re.IGNORECASE)
                d_match = re.match(r'^D\s*[).]\s*(.+)', line, re.IGNORECASE)
                ans_match = re.match(r'^ANSWER\s*[:)]\s*([ABCD])', line, re.IGNORECASE)
                
                if a_match:
                    current_q['a'] = a_match.group(1).strip()
                elif b_match:
                    current_q['b'] = b_match.group(1).strip()
                elif c_match:
                    current_q['c'] = c_match.group(1).strip()
                elif d_match:
                    current_q['d'] = d_match.group(1).strip()
                elif ans_match:
                    current_q['answer'] = ans_match.group(1).upper()
            
            i += 1
        
        # Add last question
        if current_q and all(k in current_q for k in ['question', 'a', 'b', 'c', 'd', 'answer']):
            questions.append(current_q)
        
        if not questions:
            return None
        
        return {
            'name': quiz_name,
            'questions': questions
        }
    except Exception as e:
        print(f"Parse error: {e}")
        return None
