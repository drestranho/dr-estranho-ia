import io
import fitz  # PyMuPDF
from docx import Document

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extrai texto de um arquivo PDF carregado em memória."""
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text("text") + "\n\n"
        return text
    except Exception as e:
        raise ValueError(f"Erro ao extrair PDF: {e}")

def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extrai texto de um arquivo DOCX carregado em memória."""
    try:
        doc = Document(io.BytesIO(file_bytes))
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        raise ValueError(f"Erro ao extrair DOCX: {e}")

def extract_text(file_obj, file_name: str) -> str:
    """Função genérica para extrair texto baseado na extensão."""
    file_bytes = file_obj.read()
    if file_name.lower().endswith('.pdf'):
        return extract_text_from_pdf(file_bytes)
    elif file_name.lower().endswith('.docx'):
        return extract_text_from_docx(file_bytes)
    elif file_name.lower().endswith('.txt'):
        return file_bytes.decode('utf-8', errors='replace')
    else:
        raise ValueError(f"Formato de arquivo não suportado: {file_name}")
