import os
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env que criamos
load_dotenv()

class Config:
    # Pega a Secret Key do .env (ou usa uma padrão se não achar)
    SECRET_KEY = os.getenv('SECRET_KEY', 'chave_padrao_insegura_dev')
    
    # Captura as variáveis do banco
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_HOST = os.getenv('DB_HOST')
    DB_NAME = os.getenv('DB_NAME')
    
    # Monta a "String de Conexão" que o SQLAlchemy exige
    # Formato: mysql+pymysql://usuario:senha@host/banco
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False