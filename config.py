import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

# --- FORÇAR CARREGAMENTO DO .ENV NO CAMINHO CORRETO ---
# Isso garante que o Python encontre o arquivo .env mesmo que você rode o app de pastas diferentes
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'), override=True)

class Config:
    # --- Chaves de Segurança ---
    SECRET_KEY = os.getenv('SECRET_KEY', '04092006')
    
    # --- Dados do Administrador (Puxando do .env) ---
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

    # --- Configurações do Banco de Dados ---
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_HOST = os.getenv('DB_HOST')
    DB_NAME = os.getenv('DB_NAME')
    DB_PORT = os.getenv('DB_PORT', '3306') 

    # Validação básica para avisar no terminal se algo faltar
    if not all([DB_HOST, DB_USER, DB_PASSWORD, ADMIN_EMAIL, ADMIN_PASSWORD]):
        print("❌ CRITICAL: Variáveis de ambiente faltando no arquivo .env!")
        print(f"DEBUG - ADMIN_EMAIL: {ADMIN_EMAIL}") # Ajuda a identificar se o erro é leitura
    else:
        print("✅ Variáveis de ambiente carregadas com sucesso!")

    # Tratamento da senha para a URL do banco
    _pwd_safe = quote_plus(DB_PASSWORD) if DB_PASSWORD else ""
    
    # --- Caminho do Certificado SSL ---
    ssl_path = os.path.join(basedir, 'ca.pem')
    
    ssl_args = {}
    if os.path.exists(ssl_path):
        ssl_args = {'ssl': {'ca': ssl_path}}
        print(f"✅ Certificado encontrado em: {ssl_path}")
    else:
        print(f"⚠️ ALERTA: Certificado não encontrado em: {ssl_path}")

    # --- SQLAlchemy Config ---
    # Monta a string de conexão para MySQL/Aiven
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{_pwd_safe}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    SQLALCHEMY_ENGINE_OPTIONS = {'connect_args': ssl_args}
    SQLALCHEMY_TRACK_MODIFICATIONS = False