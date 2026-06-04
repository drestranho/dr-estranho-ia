import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def configure_ai(api_key: str = None):
    """Configura a chave da API do Gemini. Tenta pegar do .env se não for passada."""
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("Chave de API do Gemini não encontrada. Adicione ao .env ou insira na interface.")
    genai.configure(api_key=key)

def generate_legal_document(system_instruction: str, user_prompt: str, context_docs: str) -> str:
    """
    Chama o modelo Gemini 1.5 Pro para redigir a peça com base nos documentos e no prompt.
    """
    try:
        model_name = "gemini-1.5-flash"
        print(f"===========================================================", flush=True)
        print(f"CHAMANDO API COM O MODELO: {model_name}", flush=True)
        print(f"===========================================================", flush=True)
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_instruction,
            generation_config={"temperature": 0.3} # Temperatura baixa para tom formal e factual
        )
        
        # Monta a query completa
        full_prompt = f"PEDIDO DO ADVOGADO:\n{user_prompt}\n\nDOCUMENTOS DE REFERÊNCIA:\n{context_docs}"
        
        # Faz a chamada
        response = model.generate_content(full_prompt)
        
        return response.text
    except Exception as e:
        raise RuntimeError(f"Erro ao comunicar com a IA: {e}")

def refine_document(system_instruction: str, history: list, new_request: str) -> tuple:
    """
    Aplica alterações a uma peça gerada anteriormente mantendo o histórico.
    history deve ser uma lista de mensagens (formato suportado pela API ou montado manualmente).
    Para simplificar no Streamlit, recriamos o contexto.
    """
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system_instruction,
        generation_config={"temperature": 0.3}
    )
    
    # Inicia chat com o histórico
    chat = model.start_chat(history=history)
    response = chat.send_message(f"O usuário solicitou uma alteração: {new_request}. Reescreva a peça completa com essa alteração.")
    
    return response.text, chat.history
