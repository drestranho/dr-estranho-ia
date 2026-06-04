import os
import json
import hashlib
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

def _hash_password(password: str) -> str:
    """Criptografa a senha para salvar no banco."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def get_db():
    """Inicia a conexão com o Firebase."""
    if not firebase_admin._apps:
        # Se estiver rodando na Nuvem (Streamlit Cloud), lê da variável de ambiente invisível
        env_cred = os.getenv("FIREBASE_KEY_JSON")
        if env_cred:
            cred_dict = json.loads(env_cred)
            cred = credentials.Certificate(cred_dict)
        else:
            # Se estiver rodando no computador, lê do arquivo local
            cred_path = "firebase_key.json"
            if not os.path.exists(cred_path):
                raise FileNotFoundError("Arquivo firebase_key.json ou variável FIREBASE_KEY_JSON não configurados.")
            cred = credentials.Certificate(cred_path)
            
        firebase_admin.initialize_app(cred)
    return firestore.client()

def verify_login(username, password):
    """Verifica se o usuário existe e a senha está correta."""
    # Como fallback caso a internet caia ou firebase não conecte, o ADMIN MASTER definido no .env sempre funciona
    if username == os.getenv("APP_USERNAME", "admin") and password == os.getenv("APP_PASSWORD", "123456"):
        return {"username": username, "role": "admin"}
        
    try:
        db = get_db()
        user_ref = db.collection('users').document(username)
        doc = user_ref.get()
        if doc.exists:
            data = doc.to_dict()
            if data.get('password_hash') == _hash_password(password):
                return {"username": username, "role": data.get('role', 'user')}
    except Exception as e:
        print(f"Erro ao acessar Firebase: {e}")
        pass
    
    return None

def create_user(username, password, role="user"):
    """Cria um novo usuário no Firebase."""
    db = get_db()
    user_ref = db.collection('users').document(username)
    if user_ref.get().exists:
        raise ValueError("Usuário já existe!")
        
    user_ref.set({
        "password_hash": _hash_password(password),
        "role": role
    })

def delete_user(username):
    """Deleta um usuário do Firebase."""
    # Impede de deletar a si mesmo ou o admin master
    if username == os.getenv("APP_USERNAME", "admin"):
        raise ValueError("Não é possível deletar o Administrador Master.")
        
    db = get_db()
    db.collection('users').document(username).delete()

def list_users():
    """Retorna a lista de usuários cadastrados."""
    db = get_db()
    users = db.collection('users').stream()
    return [{"username": u.id, "role": u.to_dict().get("role")} for u in users]
