import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

CURRENT_API_KEY = None

def configure_ai(api_key: str = None):
    """Configura a chave da API do Gemini. Tenta pegar do .env se não for passada."""
    global CURRENT_API_KEY
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("Chave de API do Gemini não encontrada. Adicione ao .env ou insira na interface.")
    genai.configure(api_key=key, transport="rest")
    # Salva no ambiente para o nosso cliente HTTP REST customizado conseguir ler
    os.environ["GEMINI_API_KEY"] = key
    CURRENT_API_KEY = key

import requests
import json

def get_best_model(api_key: str) -> str:
    """Usa o modelo que o usuário solicitou."""
    return "gemini-3-flash-preview"

def generate_legal_document(system_instruction: str, user_prompt: str, context_docs: str) -> str:
    """
    Chama o modelo Gemini via REST API (requests).
    """
    global CURRENT_API_KEY
    try:
        api_key = CURRENT_API_KEY or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Chave de API não encontrada no momento da requisição.")
        api_key = api_key.strip()

        model_name = get_best_model(api_key)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        
        full_prompt = f"PEDIDO DO ADVOGADO:\n{user_prompt}\n\nDOCUMENTOS DE REFERÊNCIA:\n{context_docs}"
        if len(full_prompt) > 2000000:
            full_prompt = full_prompt[:2000000] + "\n[TEXTO CORTADO DEVIDO AO TAMANHO]"
        
        headers = {"Content-Type": "application/json"}
        payload = {
            "system_instruction": {
                "parts": {"text": system_instruction}
            },
            "contents": [{
                "role": "user",
                "parts": [{"text": full_prompt}]
            }],
            "generationConfig": {
                "temperature": 0.3
            }
        }
        
        import time
        
        max_retries = 3
        response = None
        for attempt in range(max_retries):
            response = requests.post(
                url, 
                headers=headers, 
                data=json.dumps(payload),
                proxies={"http": None, "https": None},
                verify=False 
            )
            
            if response.status_code == 503:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt) # Espera 1s, depois 2s, e tenta de novo
                    continue
                else:
                    raise RuntimeError("Os servidores do Google estão temporariamente sobrecarregados (Erro 503). Por favor, aguarde alguns segundos e clique em 'Gerar Peça' novamente.")
            break
            
        if response.status_code != 200:
            raise RuntimeError(f"Erro da API (HTTP {response.status_code}): {response.text}")
            
        result_json = response.json()
        if "candidates" in result_json and len(result_json["candidates"]) > 0:
            return result_json["candidates"][0]["content"]["parts"][0]["text"]
        else:
            raise RuntimeError("A API não retornou texto válido. Resposta: " + str(result_json))
            
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        raise RuntimeError(f"Detalhes do erro: {e}\n\nTraceback:\n{error_details}")

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
