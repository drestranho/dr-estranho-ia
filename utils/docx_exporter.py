import io
import re
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

def create_legal_docx(markdown_text: str) -> io.BytesIO:
    """
    Converte texto Markdown gerado pela IA em um arquivo DOCX
    com formatação padrão para peças jurídicas (Times New Roman, 12, justificado).
    """
    doc = Document()
    
    # Configurações de margem (padrão forense)
    sections = doc.sections
    for section in sections:
        section.top_margin = Cm(3)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(3)
        section.right_margin = Cm(2)

    # Estilo padrão
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)

    lines = markdown_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            # Linha em branco
            doc.add_paragraph()
            continue

        # Verifica se é um cabeçalho (ex: # Título)
        header_match = re.match(r'^(#{1,6})\s+(.*)', line)
        if header_match:
            level = len(header_match.group(1))
            text = header_match.group(2)
            
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if level == 1 else WD_ALIGN_PARAGRAPH.LEFT
            
            # Espaçamento antes/depois do título
            p.paragraph_format.space_before = Pt(18)
            p.paragraph_format.space_after = Pt(12)
            
            run = p.add_run(text)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(14 if level == 1 else 12)
            run.bold = True
            if level <= 2:
                run.all_caps = True
            continue

        # Parágrafo normal
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        
        # Espaçamento entre linhas (1.5)
        p.paragraph_format.line_spacing = 1.5
        
        # Recuo da primeira linha do parágrafo (2.5cm)
        # Se a linha não começar com * ou - (lista)
        if not line.startswith(('* ', '- ', '> ')):
            p.paragraph_format.first_line_indent = Cm(2.5)
        else:
            # É um item de lista ou citação
            p.paragraph_format.left_indent = Cm(2.5)
            if line.startswith(('- ', '* ')):
                line = line[2:] # Remove marcador
            elif line.startswith('> '):
                # Citação jurisprudencial (recuo de 4cm)
                p.paragraph_format.left_indent = Cm(4)
                p.paragraph_format.first_line_indent = Cm(0)
                font.size = Pt(10) # Jurisprudência costuma ser fonte 10
                line = line[2:]
        
        # Processa negrito no texto (ex: **texto**)
        parts = re.split(r'(\*\*.*?\*\*)', line)
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                run = p.add_run(part[2:-2])
                run.bold = True
                run.font.name = 'Times New Roman'
            else:
                run = p.add_run(part)
                run.font.name = 'Times New Roman'

    # Salva no buffer de memória
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer
