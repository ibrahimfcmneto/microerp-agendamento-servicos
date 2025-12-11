from flask import Flask
from config import Config
# Adicionamos 'Client' na importação para poder criar o usuário
from models import db, login_manager, bcrypt, Client 
from routes import init_routes

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

    # --- BLOCO DE CRIAÇÃO AUTOMÁTICA DO ADMIN ---
    # O 'with app.app_context()' permite acessar o banco antes do site ligar
    with app.app_context():
        # 1. Garante que as tabelas existem (Cria se não existirem)
        db.create_all()

        # 2. Verifica se o Admin já existe
        admin_email = "admin@barbearia.com"
        if not Client.query.filter_by(email=admin_email).first():
            print(f"⚠️ Admin não encontrado. Criando {admin_email}...")
            
            # Cria o usuário Admin
            admin = Client(name="Gestor", email="admin_email@gmail.com", phone="000000000")
            admin.set_password("admin123") # Senha definida aqui
            
            db.session.add(admin)
            db.session.commit()
            print("✅ Conta de Admin criada com sucesso!")
        else:
            print("✅ Admin já existe no banco.")

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)