import os
from dotenv import load_dotenv
from urllib.parse import quote_plus # Importação vital para corrigir o erro da senha

load_dotenv(verbose=True)

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'chave_padrao_insegura_dev')
    
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_HOST = os.getenv('DB_HOST')
    DB_NAME = os.getenv('DB_NAME')
    
    # Verifica se as credenciais foram carregadas
    if not DB_HOST or not DB_USER or not DB_PASSWORD:
        raise ValueError("ERRO: Variáveis do .env não encontradas.")

    # --- A MÁGICA ACONTECE AQUI ---
    # Transformamos caracteres perigosos (como @) em código seguro (ex: %40)
    _pwd_safe = quote_plus(DB_PASSWORD)
    
    # Montamos a URL usando a senha segura (_pwd_safe)
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{_pwd_safe}@{DB_HOST}/{DB_NAME}'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False