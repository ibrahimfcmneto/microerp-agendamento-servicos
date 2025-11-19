import os
from dotenv import load_dotenv

# Tenta carregar o arquivo .env explicitamente
# O verbose=True ajuda a ver se ele encontrou o arquivo
load_dotenv(verbose=True)

class Config:
    # Vamos imprimir no terminal o que ele está encontrando (para Debug)
    print("--- DEBUG CONFIG ---")
    print(f"DB_HOST lido: {os.getenv('DB_HOST')}")
    print(f"DB_USER lido: {os.getenv('DB_USER')}")
    print("--------------------")

    SECRET_KEY = os.getenv('SECRET_KEY', 'chave_padrao_insegura_dev')
    
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_HOST = os.getenv('DB_HOST')
    DB_NAME = os.getenv('DB_NAME')
    
    # Verifica se as variáveis essenciais existem antes de montar a URL
    if not DB_HOST or not DB_USER:
        raise ValueError("ERRO: As variáveis do .env não foram carregadas! Verifique o arquivo.")

    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False