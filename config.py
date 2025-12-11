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
    DB_PORT = os.getenv('DB_PORT', '3306') 

    # Se faltar variável, avisa no log (ajuda a descobrir o erro 500)
    if not DB_HOST or not DB_USER or not DB_PASSWORD:
        print("CRITICAL: Variáveis de ambiente faltando!")

    _pwd_safe = quote_plus(DB_PASSWORD)
    
    # --- CORREÇÃO DO CAMINHO DO CERTIFICADO ---
    # Pega o diretório onde este arquivo config.py está
    basedir = os.path.abspath(os.path.dirname(__file__))
    # Monta o caminho completo para o ca.pem
    ssl_path = os.path.join(basedir, 'ca.pem')
    
    ssl_args = {}
    # Verifica se o arquivo existe nesse caminho completo
    if os.path.exists(ssl_path):
        ssl_args = {'ssl': {'ca': ssl_path}}
        print(f"Certificado encontrado em: {ssl_path}")
    else:
        print(f"ALERTA: Certificado não encontrado em: {ssl_path}")

    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{_pwd_safe}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    
    SQLALCHEMY_ENGINE_OPTIONS = {'connect_args': ssl_args}
    SQLALCHEMY_TRACK_MODIFICATIONS = False