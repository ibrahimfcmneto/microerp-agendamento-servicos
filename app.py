from flask import Flask
from config import Config
# Importamos agora também o login_manager e bcrypt do models
from models import db, login_manager, bcrypt 
from routes import init_routes

#email e senha adm
#admin@barbearia.com
#admin123

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializa as extensões
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    
    # Define para onde ir se alguém tentar acessar algo proibido
    login_manager.login_view = 'login' 
    login_manager.login_message = "Por favor, faça login para acessar esta página."

    # Inicializa as rotas
    init_routes(app)

    return app

if __name__ == '__main__':
    app = create_app()
    
    with app.app_context():
        db.create_all()
        print("✅ Banco e Sistema de Login conectados!")

    app.run(debug=True)