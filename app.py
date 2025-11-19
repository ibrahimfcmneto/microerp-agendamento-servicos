from flask import Flask
from config import Config
from models import db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializa o banco de dados com a configuração do app
    db.init_app(app)

    return app

if __name__ == '__main__':
    app = create_app()
    
    # Cria as tabelas no banco de dados se elas não existirem
    with app.app_context():
        db.create_all()
        print("✅ Banco de dados conectado e tabelas verificadas/criadas!")

    app.run(debug=True)