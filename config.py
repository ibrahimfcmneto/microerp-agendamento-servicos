import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv(verbose=True)

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'chave_secreta_padrao')
    
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_HOST = os.getenv('DB_HOST')
    DB_NAME = os.getenv('DB_NAME')
    # Adicionamos suporte à porta personalizada do Aiven
    DB_PORT = os.getenv('DB_PORT', '3306') 

    if not DB_HOST or not DB_USER or not DB_PASSWORD:
        raise ValueError("ERRO: Variáveis do .env não encontradas.")

    _pwd_safe = quote_plus(DB_PASSWORD)
    
    # --- CONFIGURAÇÃO SSL PARA AIVEN ---
    ssl_args = {}
    # Se o arquivo ca.pem estiver na pasta, usamos ele para conectar com segurança
    if os.path.exists('ca.pem'):
        ssl_args = {'ssl': {'ca': 'ca.pem'}}

    # Montamos a URL com a PORTA correta
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{_pwd_safe}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    
    SQLALCHEMY_ENGINE_OPTIONS = {'connect_args': ssl_args}
    SQLALCHEMY_TRACK_MODIFICATIONS = False