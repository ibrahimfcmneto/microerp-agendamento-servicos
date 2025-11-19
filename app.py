from flask import Flask
from config import Config
from models import db
from routes import init_routes  # <--- IMPORTANTE: Importa as rotas

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializa o banco de dados
    db.init_app(app)

    # Inicializa as rotas
    init_routes(app)  # <--- IMPORTANTE: Ativa as rotas

    return app

if __name__ == '__main__':
    app = create_app()
    
    with app.app_context():
        db.create_all()
        print("✅ Banco de dados conectado e tabelas verificadas/criadas!")

    app.run(debug=True)